#!/usr/bin/env python3
"""Capture a new dated orbital snapshot from a profile without changing history.

Fetch each configured CelesTrak URL once, stop on errors, and publish a
directory only after validation. Successful downloads are cached for two
hours so resuming a failed capture does not repeat large requests. An
optional historical NASA reference remains explicitly dated if its current
query fails; it is not presented as a current position validation.
"""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import tempfile
from urllib.request import Request, urlopen


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url, cache):
    key = digest(url.encode())
    payload = cache / (key + ".data")
    receipt = cache / (key + ".json")
    if payload.is_file() and receipt.is_file():
        note = json.loads(receipt.read_text())
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(note["retrieved_at"])).total_seconds()
        data = payload.read_bytes()
        if 0 <= age < 7200 and note["sha256"] == digest(data):
            return data, note
    request = Request(url, headers={"User-Agent": "cartofreako-orbital-technosphere/2.0 (+https://github.com/bdekoz/cartofreako)",
                                   "Accept": "application/json,text/csv,*/*"})
    with urlopen(request, timeout=45) as response:
        data = response.read()
    note = {"url": url, "retrieved_at": utcnow(), "sha256": digest(data), "bytes": len(data)}
    payload.write_bytes(data)
    receipt.write_text(json.dumps(note, indent=2) + "\n")
    return data, note


def validate_csv(data, name):
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    required = {"OBJECT_NAME", "OBJECT_ID", "EPOCH", "NORAD_CAT_ID", "MEAN_MOTION",
                "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER",
                "MEAN_ANOMALY", "CLASSIFICATION_TYPE", "ELEMENT_SET_NO", "REV_AT_EPOCH",
                "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"{name}: empty or invalid OMM CSV")
    ids = set()
    for row in rows:
        ident = row["NORAD_CAT_ID"]
        if not ident.isdigit() or ident in ids or not row["OBJECT_NAME"]:
            raise ValueError(f"{name}: invalid/duplicate ID or missing name: {ident}")
        ids.add(ident)
        datetime.fromisoformat(row["EPOCH"])
        for field in required - {"OBJECT_NAME", "OBJECT_ID", "EPOCH", "NORAD_CAT_ID", "CLASSIFICATION_TYPE"}:
            if not math.isfinite(float(row[field])):
                raise ValueError(f"{name}: non-finite {field}")
        if float(row["MEAN_MOTION"]) <= 0 or not 0 <= float(row["ECCENTRICITY"]) < 1:
            raise ValueError(f"{name}: invalid orbital elements")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--historical-reference-profile", type=Path)
    parser.add_argument("--timestamp", help="explicit UTC calculation instant; defaults to the template timestamp")
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError(f"destination already exists; choose a new snapshot directory: {args.output}")
        profile = json.loads(args.template.read_text())
        if args.timestamp:
            profile["timestamp"] = args.timestamp
            center = datetime.fromisoformat(args.timestamp)
            interval = (center - timedelta(minutes=5)).strftime("%Y%m%dT%H%M%SZ") + "," \
                + (center + timedelta(minutes=5)).strftime("%Y%m%dT%H%M%SZ")
            nasa = profile["catalogs"]["nasa_ssc_reference"]
            nasa["query_url"] = re.sub(r"\d{8}T\d{6}Z,\d{8}T\d{6}Z", interval, nasa["query_url"])
        instant = datetime.fromisoformat(profile["timestamp"])
        if instant.utcoffset() != timedelta(0):
            raise ValueError("profile timestamp must use UTC timezone")
        args.cache.mkdir(parents=True, exist_ok=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        started = utcnow()
        sources = []
        with tempfile.TemporaryDirectory(dir=args.output.parent, prefix=".orbital-refresh-") as temporary:
            stage = Path(temporary) / "snapshot"
            stage.mkdir()
            for group in [profile["catalogs"]["primary"]] + profile["catalogs"]["groups"]:
                filename = group["file"]
                if Path(filename).name != filename:
                    raise ValueError(f"catalog filename must be local: {filename}")
                print(f"Fetching {group['id']}", flush=True)
                data, note = fetch(group["source_url"], args.cache)
                rows = validate_csv(data, group["id"])
                if group["id"] == "active" and len(rows) < 10000:
                    raise ValueError("active catalog is unexpectedly small")
                if group["id"] == "active" and len(rows) > profile["display"]["maximum_active_objects"]:
                    raise ValueError("active catalog exceeds the display budget; review the profile")
                epochs = [datetime.fromisoformat(r["EPOCH"]).replace(tzinfo=timezone.utc) for r in rows]
                admissible = sum(-profile["propagation"]["maximum_future_epoch_hours"] * 3600
                                 <= (instant - epoch).total_seconds()
                                 <= profile["propagation"]["maximum_element_age_days"] * 86400
                                 for epoch in epochs)
                if group["id"] == "active" and admissible < len(rows) * 0.9:
                    raise ValueError("fewer than 90% of active elements are fresh at the profile instant")
                (stage / filename).write_bytes(data)
                sources.append(dict(note, id=group["id"], file=filename, records=len(rows),
                                    admissible_epochs=admissible, oldest_epoch=min(epochs).isoformat(),
                                    newest_epoch=max(epochs).isoformat()))
            nasa = profile["catalogs"]["nasa_ssc_reference"]
            try:
                print("Fetching NASA SSC reference", flush=True)
                data, note = fetch(nasa["query_url"], args.cache)
                response = json.loads(data)
                if response[1]["Result"][1]["StatusCode"] != "SUCCESS":
                    raise ValueError("NASA reference query did not report SUCCESS")
                nasa["reference_timestamp"] = profile["timestamp"]
                nasa["reference_status"] = "current-query; independent comparison not yet performed"
                nasa.pop("refresh_error", None)
            except Exception as error:
                if args.historical_reference_profile is None:
                    raise
                historical = json.loads(args.historical_reference_profile.read_text())
                nasa = dict(historical["catalogs"]["nasa_ssc_reference"])
                data = (args.historical_reference_profile.parent / nasa["file"]).read_bytes()
                nasa["reference_timestamp"] = historical["timestamp"]
                nasa["reference_status"] = "historical-validation-only"
                nasa["refresh_error"] = str(error)
                profile["catalogs"]["nasa_ssc_reference"] = nasa
                note = {"url": nasa["query_url"], "sha256": digest(data), "bytes": len(data),
                        "retrieved_at": historical["snapshot"]["collection_completed_at"]}
                print(f"WARNING (nonfatal): NASA current reference unavailable: {error}. "
                      f"Continuing with NASA reference dated {nasa['reference_timestamp']} "
                      "for historical validation only; current CelesTrak catalogs are retained.", flush=True)
            (stage / nasa["file"]).write_bytes(data)
            sources.append(dict(note, id="nasa-ssc-reference", file=nasa["file"],
                                reference_status=nasa["reference_status"], reference_timestamp=nasa["reference_timestamp"]))
            profile["snapshot"] = {"collection_started_at": started, "collection_completed_at": utcnow(),
                                   "checksum_file": "SHA256SUMS", "receipt_file": "acquisition.json"}
            (stage / "orbital-technosphere-profile.json").write_text(json.dumps(profile, indent=2) + "\n")
            (stage / "acquisition.json").write_text(json.dumps({"schema": "cartofreako-orbital-acquisition-v1",
                "timestamp": profile["timestamp"], "sources": sources}, indent=2) + "\n")
            files = sorted(p for p in stage.iterdir() if p.is_file())
            (stage / "SHA256SUMS").write_text("".join(f"{digest(p.read_bytes())}  {p.name}\n" for p in files))
            stage.rename(args.output)
        print(f"Created {args.output}: {len(sources) - 1} OMM catalogs; profile {profile['timestamp']}")
        return 0
    except Exception as error:
        print(f"refresh-orbiting-snapshot: {error}; no snapshot installed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

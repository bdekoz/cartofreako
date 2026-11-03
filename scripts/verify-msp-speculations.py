#!/usr/bin/env python3
"""Audit the delivered MSP sheets, sources, framing, symbols and physical sizes."""

import argparse
import csv
import gzip
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"
VERIFY = importlib.import_module("verify-orbiting-layers")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"output/msp-speculations-20261103")
    parser.add_argument("--profile", type=Path, default=ROOT/"assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json")
    args = parser.parse_args()
    manifest = json.loads((args.output/"manifest.json").read_text())
    config = manifest["configuration"]
    assert manifest["recipe_sha256"] == digest(ROOT/"config/msp-speculations-20261103.json")
    assert manifest["builder_sha256"] == digest(ROOT/"scripts/build-msp-speculations.py")
    expected = {(r["id"], subject, kind) for r in config["studies"]
                for subject in config["subjects"] for kind in ("map", "legend")}
    records = manifest["records"]
    assert len(records) == 18 and {(r["study"], r["subject"], r["kind"]) for r in records} == expected
    profile = json.loads(args.profile.read_text())
    names = {}
    for group in [profile["catalogs"]["primary"], *profile["catalogs"]["groups"]]:
        with (args.profile.parent/group["file"]).open(newline="") as stream:
            for row in csv.DictReader(stream):
                names.setdefault(row["NORAD_CAT_ID"], row["OBJECT_NAME"])
    report = {"sheets": 18, "maps": 9, "legends": 9, "verified_files": 0, "orbital": []}
    with tempfile.TemporaryDirectory(prefix="cartofreako-msp-audit-") as temporary:
        maps = []
        for record in records:
            recipe = next(r for r in config["studies"] if r["id"] == record["study"])
            framing = record["framing"]
            assert math.isclose(framing["cyclic_move_on_sheet_inches"], 4.35)
            assert framing["image_inches"] == [43.5, 19.052559*(43.5/44)]
            assert framing["antarctica_adjustment"]["present"] == (record["subject"] != "orbital-technosphere-observer")
            for item in record["outputs"]:
                path = args.output/item["path"]
                assert path.is_file() and digest(path) == item["sha256"] and path.stat().st_size == item["bytes"]
                report["verified_files"] += 1
                if path.suffix == ".pdf":
                    info = subprocess.check_output(["pdfinfo", str(path)], text=True)
                    assert re.search(r"Pages:\s+1\b", info)
                    size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
                    assert size and math.isclose(float(size[1]), 44*72, abs_tol=.02)
                    assert math.isclose(float(size[2]), 19.052559*72, abs_tol=.02)
                elif path.name.endswith(".svg.gz"):
                    data = gzip.decompress(path.read_bytes())
                    assert hashlib.sha256(data).hexdigest() == record["svg_sha256"]
                    target = Path(temporary)/record["study"]/path.name.removesuffix(".gz")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    root = ET.fromstring(data)
                    assert root.get("data-color-study") == recipe["title"]
                    elements = list(root.iter())
                    by_id = {e.get("id"): e for e in elements if e.get("id")}
                    ids = [e.get("id") for e in elements if e.get("id")]
                    assert len(ids) == len(set(ids))
                    if record["kind"] == "map":
                        assert root.get("data-sheet-kind") == "map"
                        assert float(root.get("data-cyclic-shift-in")) == 4.4
                        uses = [e.get("transform") for e in by_id["st2-image-window"] if e.tag == SVG+"use"]
                        assert uses == [f"translate({n} 0)" for n in (4.4-44, 4.4, 4.4+44)]
                        assert not any(e.get("id") in ("constellation-legend", "groundstation-legend") for e in elements)
                        if record["subject"].startswith("orbital"):
                            maps.append(target)
                        else:
                            metadata = by_id["network-groundstations-metadata"]
                            assert metadata.get("data-datestamp") == "20261103"
                            assert sum(e.get("data-groundstation") == "true" for e in elements) == 780
                            assert metadata.get("data-source-gateways-sha256") == digest(ROOT/"assets.static/network-groundstations/starlink-global-gateways-pops.20261103.geojson")
                            assert metadata.get("data-source-kml-sha256") == digest(ROOT/"assets.static/network-groundstations/starlink-global-gateways-pops.20261103.kml")
                    else:
                        assert "plate-source-bibliography" in by_id and "msp-print-note" in by_id
                    paper = by_id["st2-sheet-paper" if record["kind"] == "map" else "legend-paper"]
                    styles = dict(s.strip().split(":", 1) for s in paper.get("style").split(";") if ":" in s)
                    assert styles["fill"] == recipe["background"]
        report["orbital"] = [VERIFY.verify(path, profile, names) for path in maps]
        for item in report["orbital"]:
            item["file"] = str(Path(item["file"]).relative_to(temporary))
    (args.output/"validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print(f"Verified {report['sheets']} sheets, {report['verified_files']} delivered files, Setouchi framing, source counts, symbols and 9 pt Starlink IDs")


if __name__ == "__main__":
    main()

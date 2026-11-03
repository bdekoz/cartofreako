"""Source-preserving antenna inventory interpretation for the Starlink studies.

The proxy is the largest complete *listed* bank aperture, not site throughput.
Bands are never added: one antenna can serve more than one band. All source
claims, including contradictory and incomplete fields, remain in the receipt.
"""

from collections import Counter, defaultdict
import math
import re


CAPABILITIES = {
    "ka": ("Ka", 3, 1),
    "ka-e": ("Ka + E", 6, 2),
    "e": ("E only", 4, 2),
    "qv": ("Q/V", 5, 3),
    "quad": ("Ka + E + Q/V + W", 12, 4),
    "community": ("Community gateway", 8, 3),
    "ttc": ("Tracking / telemetry / control", 2, 2),
    "ku": ("Ku", 7, 1),
    "unknown": ("Unspecified / conflicting band", 0, 0),
}
BANKS = ("Ka", "E", "Ka/E", "Q/V", "W")


def positive_number(value, integral=False):
    """Reject composites, non-finite values, negative/zero counts and fractions."""
    value = value.strip()
    if not re.fullmatch(r"\d+(?:\.\d*)?", value):
        return None
    result = float(value)
    if not math.isfinite(result) or result <= 0 or (integral and not result.is_integer()):
        return None
    return int(result) if integral else result


def interpret(feature):
    props = feature["properties"]
    fields = defaultdict(list)
    for entry in props.get("extended_data", []):
        fields[entry["name"]].append(entry.get("value", ""))
    raw, resolutions, issues = {}, [], []
    for name, values in fields.items():
        populated = list(dict.fromkeys(v.strip() for v in values if v.strip()))
        numeric = [positive_number(v) for v in populated]
        equivalent = bool(numeric) and None not in numeric and len(set(numeric)) == 1
        if len(populated) <= 1 or equivalent:
            raw[name] = populated[0] if populated else ""
            if len(values) > 1:
                resolutions.append({"field": name, "values": values, "chosen": raw[name],
                                    "rule": "equivalent-numbers" if len(populated) > 1 else
                                            "one-populated-value" if populated else "all-empty"})
        else:
            raw[name] = ""
            issues.append({"code": "conflicting-repeated-field", "field": name, "values": values})
    geometry = feature["geometry"]
    point = geometry["type"] == "Point"
    pop = point and props["folder_path"] == ["PoPs & Backbone"]
    kind = "pop" if pop else "antenna-site" if point else "link"
    result = {
        "id": feature["id"], "name": props["Name"], "kind": kind,
        "folder_path": props["folder_path"], "geometry": geometry,
        "raw_extended_data": props.get("extended_data", []),
        "field_resolutions": resolutions,
        "description_html": props.get("description", ""),
    }
    if kind != "antenna-site":
        return result
    banks = []
    for band in BANKS:
        size_raw, count_raw = raw.get(band+" Antenna Size", ""), raw.get(band+" Antenna Count", "")
        if not (size_raw or count_raw):
            continue
        diameter, count = positive_number(size_raw), positive_number(count_raw, True)
        if size_raw and diameter is None:
            issues.append({"code": "invalid-or-composite-diameter", "field": band+" Antenna Size", "value": size_raw})
        if count_raw and count is None:
            issues.append({"code": "invalid-count", "field": band+" Antenna Count", "value": count_raw})
        banks.append({"band": band, "diameter_m": diameter, "count": count,
                      "diameter_raw": size_raw, "count_raw": count_raw,
                      "aperture_m2": count*math.pi*diameter**2/4 if count and diameter else None})
    complete = [b for b in banks if b["aperture_m2"] is not None]
    selected = max(complete, key=lambda b: b["aperture_m2"], default=None)
    incomplete = any(b["aperture_m2"] is None for b in banks)
    if incomplete:
        issues.append({"code": "incomplete-bank-inventory"})

    # Frequency is a source claim. Do not silently repair Ku/Ka or Ka+# typos
    # from operational booleans, dish size, or location.
    freq = re.sub(r"\s+", "", raw.get("Freq", "")).upper()
    capability = {"KA": "ka", "KA+E": "ka-e", "E": "e", "V/Q": "qv",
                  "KA+V/Q+E+W": "quad", "TTC": "ttc", "KU": "ku"}.get(freq, "unknown")
    if props["folder_path"] == ["Community Gateways"]:
        capability = "community"
    if freq and freq not in ("KA", "KA+E", "E", "V/Q", "KA+V/Q+E+W", "TTC", "KU"):
        issues.append({"code": "unrecognized-frequency", "value": raw.get("Freq", "")})
    operations = {b: raw.get(b+" Operational", "").strip().lower()
                  for b in ("Ka", "E", "V/Q", "W")}
    status_raw = raw.get("Status", "")
    status = status_raw.lower()
    retired = bool(re.search(r"demolish|decommission|withdrawn|abandon|cancel|dismantl|terminated", status))
    reported = any(v == "true" for v in operations.values())
    negative = bool(re.search(r"not (?:yet )?(?:built|live|operational)|never built", status))
    status_class = "retired" if retired else "reported-operational" if reported and not negative else "unconfirmed"
    if reported and (retired or negative):
        issues.append({"code": "operational-status-conflict"})
    if freq in ("KU", "KU+E", "E") and operations["Ka"] == "true":
        issues.append({"code": "frequency-operational-conflict"})
    if re.search(r"\b\d+\s+of\s+\d+", status):
        issues.append({"code": "partial-build-status"})
    result.update({
        "capability": capability, "frequency_raw": raw.get("Freq", ""),
        "status": status_class, "status_raw": status_raw,
        "operational_flags_raw": operations, "source_date": raw.get("Date", ""),
        "application": raw.get("Application", ""), "banks": banks,
        "aperture_proxy_m2": selected["aperture_m2"] if selected else None,
        "selected_bank": selected["band"] if selected else None,
        "incomplete_inventory": incomplete, "issues": issues,
    })
    return result


def normalize(document):
    records = [interpret(feature) for feature in document["features"]]
    ids = [r["id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate source feature IDs")
    sites = [r for r in records if r["kind"] == "antenna-site"]
    coordinates = defaultdict(list)
    for r in sites:
        coordinates[tuple(r["geometry"]["coordinates"][:2])].append(r["id"])
    duplicates = [v for v in coordinates.values() if len(v) > 1]
    for group in duplicates:
        for r in sites:
            if r["id"] in group:
                r["issues"].append({"code": "shared-source-coordinate", "records": group})
    return records, {
        "source_records": len(records),
        "kinds": dict(Counter(r["kind"] for r in records)),
        "capabilities": dict(Counter(r["capability"] for r in sites)),
        "statuses": dict(Counter(r["status"] for r in sites)),
        "sized_sites": sum(r["aperture_proxy_m2"] is not None for r in sites),
        "unknown_size_sites": sum(r["aperture_proxy_m2"] is None for r in sites),
        "incomplete_inventories": sum(r["incomplete_inventory"] for r in sites),
        "issue_counts": dict(Counter(i["code"] for r in sites for i in r["issues"])),
        "coincident_record_groups": duplicates,
        "blank_source_dates": sum(not r["source_date"] for r in sites),
        "resolved_repeated_fields": sum(len(r["field_resolutions"]) for r in sites),
    }

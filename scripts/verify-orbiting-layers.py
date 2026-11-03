#!/usr/bin/env python3
"""Verify named SVG layers, one-to-one name/dot associations and source names."""

import argparse
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

SVG = "{http://www.w3.org/2000/svg}"
INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}"


def verify(path, profile, names):
    root = ET.parse(path).getroot()
    elements = list(root.iter())
    ids = [e.get("id") for e in elements if e.get("id")]
    assert len(ids) == len(set(ids)), f"{path}: duplicate XML IDs"
    by_id = {e.get("id"): e for e in elements if e.get("id")}
    metadata = by_id["orbital-technosphere-metadata"]
    assert metadata.get("data-timestamp") == profile["timestamp"]
    dots = [e for e in elements if e.get("data-object-kind") == "locpoint"]
    labels = [e for e in elements if e.get("data-object-kind") == "name"]
    assert len(dots) == len(labels) == int(metadata.get("data-visible-records"))
    dot_ids = {e.get("data-norad-id"): e for e in dots}
    label_ids = {e.get("data-norad-id"): e for e in labels}
    assert len(dot_ids) == len(dots) and dot_ids.keys() == label_ids.keys()
    for ident, dot in dot_ids.items():
        label = label_ids[ident]
        assert label.tag == SVG + "text" and dot.tag == SVG + "circle"
        assert label.get("data-locpoint-id") == dot.get("id")
        assert label.get("data-display-group") == dot.get("data-display-group")
        assert "".join(label.itertext()).strip() == names[ident].strip()
        assert dot.get("data-name") == names[ident]
    counts = {}
    for group in [e for e in root if e.get("data-object-count") is not None]:
        ident = group.get("id")
        children = {e.get("id"): e for e in group if e.tag == SVG + "g"}
        assert set(children) == {ident + "-name", ident + "-locpoint"}
        for suffix in ("name", "locpoint"):
            layer = children[ident + "-" + suffix]
            assert layer.get(INKSCAPE + "label") == suffix
            assert layer.get(INKSCAPE + "groupmode") == "layer"
            expected_tag = SVG + ("text" if suffix == "name" else "circle")
            assert all(e.tag == expected_tag for e in layer)
            assert all(e.get("data-display-group") == ident for e in layer)
            assert len(layer) == int(group.get("data-object-count"))
        if not profile["display"].get("show_satellite_names", False):
            assert children[ident + "-name"].get("style") == "display:none"
        counts[ident] = len(children[ident + "-locpoint"])
    named = {g["constellation"]["id"] for g in profile["catalogs"]["groups"] if "constellation" in g}
    assert named.issubset(counts)
    assert sum(counts.values()) == len(dots)
    assert "constellation-legend" in by_id
    print(f"{path.name}: {len(dots)} dots and paired names, {len(named)} named groups verified")
    return {"file": str(path), "timestamp": profile["timestamp"], "objects": len(dots),
            "groups": counts, "skipped_stale": int(metadata.get("data-skipped-stale")),
            "failed_propagation": int(metadata.get("data-failed-propagation"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("svg", type=Path, nargs="+")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text())
    names = {}
    for group in [profile["catalogs"]["primary"]] + profile["catalogs"]["groups"]:
        with (args.profile.parent / group["file"]).open(newline="") as stream:
            for row in csv.DictReader(stream):
                names.setdefault(row["NORAD_CAT_ID"], row["OBJECT_NAME"])
    reports = [verify(path, profile, names) for path in args.svg]
    if args.report:
        args.report.write_text(json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()

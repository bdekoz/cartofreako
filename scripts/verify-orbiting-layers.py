#!/usr/bin/env python3
"""Verify orbital map/legend pairs, source names, symbols and Starlink IDs."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

SVG = "{http://www.w3.org/2000/svg}"
INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}"


def expected_shape(role, group):
    if role == "debris":
        return "x"
    if group == "starlink":
        return "sunburst"
    if group == "intelsat":
        return "square"
    if role == "earth-observation":
        return "triangle"
    return "circle"


def verify_marker(marker):
    shape = expected_shape(marker.get("data-role"), marker.get("data-display-group"))
    assert marker.get("data-marker-shape") == shape
    if shape == "circle":
        assert marker.tag == SVG + "circle"
        return
    assert marker.tag == SVG + "path"
    tokens = marker.get("d", "").split()
    size = {"x": 4, "triangle": 3, "square": 4, "sunburst": 16}[shape]
    commands = ["M", "L", "M", "L"] if shape == "x" else ["M"] + ["L"]*(size-1) + ["Z"]
    assert len(tokens) == size*3 + (shape != "x") and tokens[::3] == commands
    vertices = [(float(tokens[i]), float(tokens[i+1])) for i in range(1, size*3, 3)]
    assert all(math.isfinite(value) for point in vertices for value in point)
    assert len(set(vertices)) == size
    if shape == "x":
        (ax, ay), (bx, by), (cx, cy), (dx, dy) = vertices
        assert ax < bx and ay < by and cx < dx and cy > dy
        assert math.isclose(ax+bx, cx+dx) and math.isclose(ay+by, cy+dy)
        style = dict(part.strip().split(":", 1) for part in marker.get("style", "").split(";") if part.strip())
        assert style["stroke"] == "rgb(0,0,0)" and float(style["stroke-opacity"]) == 1
        assert float(style["fill-opacity"]) == 0 and float(style["stroke-width"]) > 0
    elif shape == "triangle":
        (ax, ay), (bx, by), (cx, cy) = vertices
        assert (bx-ax)*(cy-ay) - (by-ay)*(cx-ax) > 0
        assert ay < by and ay < cy
    elif shape == "square":
        widths = [math.dist(vertices[i], vertices[(i+1)%4]) for i in range(4)]
        assert min(widths) > 0 and math.isclose(min(widths), max(widths), rel_tol=1e-5)
    else:
        center = tuple(sum(p[axis] for p in vertices)/size for axis in (0, 1))
        radii = [math.dist(p, center) for p in vertices]
        assert all(radii[i] > 2*radii[i+1] for i in range(0, size, 2))


def verify(path, profile, names):
    root = ET.parse(path).getroot()
    elements = list(root.iter())
    ids = [e.get("id") for e in elements if e.get("id")]
    assert len(ids) == len(set(ids)), f"{path}: duplicate XML IDs"
    by_id = {e.get("id"): e for e in elements if e.get("id")}
    metadata = by_id["orbital-technosphere-metadata"]
    assert metadata.get("data-timestamp") == profile["timestamp"]
    product = metadata.get("data-product")
    assert root.get("data-sheet-kind") == "map"
    assert "constellation-legend" not in by_id
    dots = [e for e in elements if e.get("data-object-kind") == "locpoint"]
    labels = [e for e in elements if e.get("data-object-kind") == "name"]
    assert len(dots) == len(labels) == int(metadata.get("data-visible-records"))
    dot_ids = {e.get("data-norad-id"): e for e in dots}
    label_ids = {e.get("data-norad-id"): e for e in labels}
    assert len(dot_ids) == len(dots) and dot_ids.keys() == label_ids.keys()
    for ident, dot in dot_ids.items():
        label = label_ids[ident]
        assert label.tag == SVG + "text"
        verify_marker(dot)
        assert label.get("data-locpoint-id") == dot.get("id")
        assert label.get("data-display-group") == dot.get("data-display-group")
        assert "".join(label.itertext()).strip() == names[ident].strip()
        assert dot.get("data-name") == names[ident]
    counts = {}
    for group in [e for e in elements if e.get("data-object-count") is not None]:
        ident = group.get("id")
        children = {e.get("id"): e for e in group if e.tag == SVG + "g"}
        suffixes = ["name", "locpoint"]
        if product == "global" and ident == "starlink":
            suffixes.append("id")
        assert set(children) == {ident + "-" + suffix for suffix in suffixes}
        for suffix in ("name", "locpoint"):
            layer = children[ident + "-" + suffix]
            assert layer.get(INKSCAPE + "label") == suffix
            assert layer.get(INKSCAPE + "groupmode") == "layer"
            assert all(e.get("data-object-kind") == suffix for e in layer)
            assert all(e.get("data-display-group") == ident for e in layer)
            assert len(layer) == int(group.get("data-object-count"))
        if not profile["display"].get("show_satellite_names", False):
            assert children[ident + "-name"].get("style") == "display:none"
        counts[ident] = len(children[ident + "-locpoint"])
    ids = [e for e in elements if e.get("data-object-kind") == "id"]
    expected_ids = {ident for ident, dot in dot_ids.items()
                    if product == "global" and dot.get("data-display-group") == "starlink"}
    assert {e.get("data-norad-id") for e in ids} == expected_ids
    assert len(ids) == len(expected_ids)
    if ids:
        layer = by_id["starlink-id"]
        assert layer.get(INKSCAPE + "label") == "id" and layer.get("style") != "display:none"
        scale = float(root.get("data-image-scale"))
        for label in ids:
            assert label.tag == SVG + "text" and label.text == label.get("data-norad-id")
            assert label.get("data-display-group") == "starlink"
            assert label.get("data-locpoint-id") == dot_ids[label.text].get("id")
            assert math.isclose(float(label.get("font-size"))*scale*72, 10)
    named = {g["constellation"]["id"] for g in profile["catalogs"]["groups"] if "constellation" in g}
    assert named.issubset(counts)
    assert sum(counts.values()) == len(dots)
    legend_path = path.with_name(path.stem + "-legend.svg")
    assert root.get("data-legend-companion") == legend_path.name
    legend = ET.parse(legend_path).getroot()
    assert legend.get("data-sheet-kind") == "legend"
    assert legend.get("data-map-companion") == path.name
    assert legend.get("viewBox") == root.get("viewBox") or list(map(float, legend.get("viewBox").split())) == list(map(float, root.get("viewBox").split()))
    legend_ids = {e.get("id"): e for e in legend.iter() if e.get("id")}
    assert "constellation-legend" in legend_ids and "plate-source-bibliography" in legend_ids
    ledger = json.loads(legend_ids["orbital-source-ledger"].text)
    assert ledger["calculation_timestamp"] == profile["timestamp"]
    catalog_ids = {g["id"] for g in [profile["catalogs"]["primary"], *profile["catalogs"]["groups"]]}
    assert catalog_ids == {g["id"] for g in ledger["acquisition"]["sources"] if g.get("file", "").endswith(".csv")}
    root_dir = Path(__file__).resolve().parents[1]
    assert ledger["profile_sha256"] == hashlib.sha256((root_dir / ledger["profile"]).read_bytes()).hexdigest()
    assert not any(e.get("data-object-kind") for e in legend.iter())
    assert legend_ids["orbital-technosphere-metadata"].attrib == metadata.attrib
    for ident, count in counts.items():
        if count or ident in named:
            verify_marker(legend_ids["legend-" + ident])
    print(f"{path.name}: {len(dots)} markers and paired names, {len(named)} named groups, "
          f"{len(ids)} Starlink IDs at 10 pt; symbols and separate attribution legend verified")
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
    reports = [verify(path, profile, names) for path in args.svg if not path.stem.endswith("-legend")]
    if args.report:
        args.report.write_text(json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()

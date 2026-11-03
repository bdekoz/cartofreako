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

from print_palette_validation import verify_palette, verify_land_order, paint

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"
VERIFY = importlib.import_module("verify-orbiting-layers")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vertices(marker):
    tokens = marker.get("d").split()
    return [(float(tokens[i]), float(tokens[i+1])) for i in range(1, 48, 3)]


def group_colors(root, vendor_colors):
    colors = {}
    assert root.get("data-marker-color-policy") == "preserve-source-groups"
    for marker in root.iter():
        group = marker.get("data-display-group")
        if not group or not marker.get("data-marker-shape"):
            continue
        color = paint(marker, "stroke" if marker.get("data-marker-shape") == "x" else "fill")
        if group in vendor_colors:
            assert color == vendor_colors[group], (group, color, vendor_colors[group])
        assert colors.setdefault(group, color) == color
    return colors


def compare_orbital_variant(original, variant, global_plate):
    base = ET.parse(original).getroot()
    changed = ET.parse(variant).getroot()
    base_marks = {n.get("data-norad-id"): n for n in base.iter() if n.get("data-object-kind") == "locpoint"}
    variant_marks = {n.get("data-norad-id"): n for n in changed.iter() if n.get("data-object-kind") == "locpoint"}
    assert base_marks.keys() == variant_marks.keys()
    scaled = 0
    for identifier, a in base_marks.items():
        b = variant_marks[identifier]
        if a.get("data-display-group") == "starlink":
            assert b.get("data-marker-shape") == "sunburst"
            av, bv = vertices(a), vertices(b)
            center = [sum(p[axis] for p in av)/16 for axis in (0, 1)]
            actual_center = [sum(p[axis] for p in bv)/16 for axis in (0, 1)]
            assert all(math.isclose(x, y, abs_tol=1e-8) for x, y in zip(center, actual_center))
            for p, q in zip(av, bv):
                assert all(math.isclose(c+1.5*(v-c), w, abs_tol=1e-8) for c, v, w in zip(center, p, q))
            scaled += 1
        else:
            for key in ("d", "cx", "cy", "r", "transform"):
                assert a.get(key) == b.get(key), (identifier, key)
    # Text coordinates and source identity stay fixed while only Starlink size changes.
    labels = {n.get("id"): n for n in base.iter() if n.get("data-object-kind") in ("name", "id")}
    for label in changed.iter():
        if label.get("id") in labels:
            a = labels[label.get("id")]
            for key in ("x", "y", "transform", "data-norad-id"):
                assert label.get(key) == a.get(key)
            if not global_plate or label.get("data-display-group") != "starlink":
                assert label.get("font-size") == a.get("font-size")
    if global_plate:
        elements = list(changed.iter())
        text_order = [i for i, n in enumerate(elements) if n.get("data-display-group") == "starlink" and n.get("data-object-kind") in ("name", "id")]
        marker_order = [i for i, n in enumerate(elements) if n.get("data-object-kind") == "locpoint"]
        assert max(text_order) < min(marker_order)
    baseline_legend = original.with_name(original.stem+"-legend.svg")
    variant_legend = variant.with_name(variant.stem+"-legend.svg")
    a = next(n for n in ET.parse(baseline_legend).getroot().iter() if n.get("id") == "legend-starlink")
    b = next(n for n in ET.parse(variant_legend).getroot().iter() if n.get("id") == "legend-starlink")
    av, bv = vertices(a), vertices(b)
    center = [sum(p[axis] for p in av)/16 for axis in (0, 1)]
    assert all(math.isclose(c+1.5*(v-c), w, abs_tol=1e-8) for p, q in zip(av, bv) for c, v, w in zip(center, p, q))
    return scaled


def capability_geometry(root):
    keys = ("id", "d", "points", "transform", "cx", "cy", "r", "x", "y", "width", "height",
            "font-size", "clip-path", "data-record-id", "data-capability", "data-status", "data-pattern", "data-aperture-m2")
    def walk(node, skip=False):
        skip = skip or node.get("data-presentation-only") == "true"
        if skip:
            return
        if node.tag.split("}")[-1] in ("g", "path", "circle", "rect", "text", "line", "use", "polygon"):
            yield (node.tag, tuple(node.get(k) for k in keys), node.text if node.tag.endswith("}text") else None)
        for child in node:
            yield from walk(child, skip)
    return list(walk(root))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"output/msp-speculations-20261103")
    parser.add_argument("--profile", type=Path, default=ROOT/"assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json")
    args = parser.parse_args()
    manifest = json.loads((args.output/"manifest.json").read_text())
    config = manifest["configuration"]
    assert manifest["recipe_sha256"] == digest(ROOT/"config/msp-speculations-20261103.json")
    assert manifest["builder_sha256"] == digest(ROOT/"scripts/build-msp-speculations.py")
    assert manifest["framing_sha256"] == digest(ROOT/"scripts/setouchi_world_framing.py")
    provenance_path = ROOT/config["palette_provenance"]
    assert manifest["palette_provenance_sha256"] == digest(provenance_path) == digest(args.output/"palette-sources.json")
    provenance = json.loads(provenance_path.read_text())
    capability = manifest["capability_input"]
    assert digest(ROOT/capability["manifest_path"]) == capability["manifest_sha256"]
    assert digest(ROOT/capability["evidence_path"]) == capability["evidence_sha256"]
    cap_manifest = json.loads((ROOT/capability["manifest_path"]).read_text())
    expected = {(r["id"], subject, kind) for r in config["studies"]
                for subject in config["subjects"] for kind in ("map", "legend")}
    records = manifest["records"]
    assert len(records) == len(expected) == 42 and {(r["study"], r["subject"], r["kind"]) for r in records} == expected
    fourth_studies = [r for r in config["studies"] if r.get("family") == "msp-speculation-4"]
    assert len(fourth_studies) == 4 and {r["randoma11y_pair"] for r in fourth_studies} == {p["id"] for p in provenance["pairs"]}
    assert all(r["variant"]["global_starlink_font_size_pt"] == 6 for r in fourth_studies)
    profile = json.loads(args.profile.read_text())
    vendor_colors = {g["constellation"]["id"]: "rgb("+",".join(map(str, g["constellation"]["color_rgb"]))+")"
                     for g in profile["catalogs"]["groups"] if "constellation" in g}
    assert len(vendor_colors) == len(set(vendor_colors.values())) == 18
    names = {}
    for group in [profile["catalogs"]["primary"], *profile["catalogs"]["groups"]]:
        with (args.profile.parent/group["file"]).open(newline="") as stream:
            for row in csv.DictReader(stream):
                names.setdefault(row["NORAD_CAT_ID"], row["OBJECT_NAME"])
    report = {"sheets": len(expected), "maps": len(expected)//2, "legends": len(expected)//2,
              "verified_files": 0, "orbital": [], "vendor_colors": vendor_colors,
              "checks": ["source Randoma11y pairs and actual SVG paint", "Antarctic inset below source data",
                         "all four color pairs delivered for the complete MSP 4 set",
                         "MSP 4 Starlink centroids fixed, sunburst linear size 1.5x", "all global markers above 6 pt Starlink text",
                         "18 original vendor colors and matching map/legend keys on both orbital subjects",
                         "groundstation fiber links use pair foreground at full opacity",
                         "MSP 4 groundstation geometry identical to option-3-petals"]}
    with tempfile.TemporaryDirectory(prefix="cartofreako-msp-audit-") as temporary:
        maps = []
        colors_by_sheet = {}
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
                            font = recipe.get("variant", {}).get("global_starlink_font_size_pt", 9)
                            maps.append((target, font))
                        else:
                            metadata = by_id["network-groundstations-metadata"]
                            assert metadata.get("data-datestamp") == "20261103"
                            petal_study = recipe.get("variant", {}).get("groundstation_study")
                            assert sum(e.get("data-groundstation") == "true" for e in elements) == (590 if petal_study else 780)
                            if petal_study:
                                marks = [e for e in elements if e.get("data-groundstation") == "true"]
                                assert all(e.get("data-pattern") == "petals" and e.get("data-marker-shape") == "equilateral-triangle" for e in marks)
                                assert sum(e.get("data-kind") == "pop" for e in elements) == 66
                                assert sum(e.get("data-gateway-link") == "true" for e in elements) == 124
                            assert metadata.get("data-source-gateways-sha256") == digest(ROOT/"assets.static/network-groundstations/starlink-global-gateways-pops.20261103.geojson")
                            assert metadata.get("data-source-kml-sha256") == digest(ROOT/"assets.static/network-groundstations/starlink-global-gateways-pops.20261103.kml")
                    else:
                        assert "msp-print-note" in by_id
                        assert "plate-source-bibliography" in by_id or "capability-legend-ledger" in by_id
                    verify_palette(root, recipe, provenance)
                    if record["subject"].startswith("orbital"):
                        assert record["marker_color_policy"] == config["orbital_marker_colors"] == "preserve-source-groups"
                        colors_by_sheet[(record["study"], record["subject"], record["kind"])] = group_colors(root, vendor_colors)
                    if record["kind"] == "map":
                        verify_land_order(root)
                    if record.get("capability_study"):
                        reference = next(r for r in cap_manifest["records"] if r["study"] == "option-3-petals" and r["kind"] == record["kind"])
                        archive = next(f for f in reference["outputs"] if f["path"].endswith(".svg.gz"))
                        cap_source = (ROOT/capability["manifest_path"]).parent/archive["path"]
                        original = ET.fromstring(gzip.decompress(cap_source.read_bytes()))
                        assert capability_geometry(root) == capability_geometry(original)
        report["orbital"] = [VERIFY.verify(path, profile, names, font) for path, font in maps]
        report["scaled_starlink_markers"] = {}
        for recipe in config["studies"]:
            for subject in ("orbital-technosphere-global", "orbital-technosphere-observer"):
                map_colors = colors_by_sheet[(recipe["id"], subject, "map")]
                legend_colors = colors_by_sheet[(recipe["id"], subject, "legend")]
                assert set(vendor_colors).issubset(legend_colors)
                assert all(color == legend_colors[group] for group, color in map_colors.items())
        for recipe in fourth_studies:
            report["scaled_starlink_markers"][recipe["id"]] = {}
            for subject in ("global", "observer"):
                stem = "orbital-technosphere-"+subject+"-authagraph-44-19.052559.svg"
                report["scaled_starlink_markers"][recipe["id"]][subject] = compare_orbital_variant(
                    Path(temporary)/"msp-speculation-1"/stem,
                    Path(temporary)/recipe["id"]/stem, subject == "global")
        for item in report["orbital"]:
            item["file"] = str(Path(item["file"]).relative_to(temporary))
    assert report["verified_files"] == len(expected)*3
    (args.output/"validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print(f"Verified {report['sheets']} sheets, {report['verified_files']} files, all four MSP 4 palettes, 18 vendor colors, bright fiber links, 6/9 pt IDs, layer order and 1.5x sunbursts")


if __name__ == "__main__":
    main()

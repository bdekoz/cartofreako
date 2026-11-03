#!/usr/bin/env python3
"""Verify source accounting, physical symbol sizes, tiling and delivered PDFs."""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from lxml import etree as E
from PIL import Image
from cartofreako_style import STYLE, hexoffsets
from groundstation_capabilities import normalize, CAPABILITIES
from legend_informatics import ROOT, NS, WIDTH, HEIGHT, digest
from setouchi_world_framing import SCALE, SHIFT
from print_palette_validation import verify_palette, verify_land_order


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"output/groundstation-capabilities-20261103")
    args = parser.parse_args()
    evidence_path = args.output/"capability-evidence.json"
    evidence = json.loads(evidence_path.read_text())
    manifest = json.loads((args.output/"manifest.json").read_text())
    config = json.loads((ROOT/"config/groundstation-capabilities-20261103.json").read_text())
    assert manifest["configuration"] == evidence["configuration"] == config
    assert manifest["evidence_sha256"] == digest(evidence_path)
    palette_source = ROOT/"config/randoma11y-pairs-20261103.json"
    assert manifest["palette_provenance_sha256"] == digest(palette_source)
    provenance = json.loads(palette_source.read_text())
    recipes = {r["id"]: r for r in json.loads((ROOT/"config/msp-speculations-20261103.json").read_text())["studies"]}
    assert manifest["palettes"] == {s["id"]: recipes[s["palette"]] for s in config["studies"]}
    for path, sha in manifest["scripts"].items():
        assert digest(ROOT/path) == sha, path
    assert digest(ROOT/"assets/fonts/atkinson-hyperlegible/provenance.json") == manifest["font_sha256"]
    source = ROOT/evidence["source"]
    assert digest(source) == evidence["source_sha256"]
    assert digest(source.with_name(evidence["source_kml"])) == evidence["source_kml_sha256"]
    normalized, summary = normalize(json.loads(source.read_text()))
    assert evidence["summary"] == summary
    rows = {r["id"]: r for r in evidence["records"]}
    assert len(rows) == len(normalized) == 780
    for raw in normalized:
        assert all(rows[raw["id"]][k] == v for k, v in raw.items())
    sites = {k: r for k, r in rows.items() if r["kind"] == "antenna-site"}
    pops = {k: r for k, r in rows.items() if r["kind"] == "pop"}
    links = {k: r for k, r in rows.items() if r["kind"] == "link"}
    assert (len(sites), len(pops), len(links)) == (590, 66, 124)
    assert (summary["sized_sites"], summary["unknown_size_sites"]) == (538, 52)
    assert summary["issue_counts"]["invalid-count"] == 3
    assert summary["resolved_repeated_fields"] == 294
    # Independent source sample: 8 x 1.85 m, not the sum of Ka and E.
    assert math.isclose(rows["placemark-000180"]["aperture_proxy_m2"], 8*math.pi*1.85**2/4)
    # Blank second diameter must not erase the populated first diameter.
    assert rows["placemark-000309"]["aperture_proxy_m2"] is not None
    assert rows["placemark-000592"]["aperture_proxy_m2"] is None
    placement = evidence["placement"]
    assert placement["group_grid_inches"] == STYLE["cdn"]["group_grid_in"]
    membership = []
    for group in placement["groups"]:
        cell = group["cell_radius_inches"]
        expected_offsets = hexoffsets(len(group["records"]), cell)
        for identifier, offset in zip(group["records"], expected_offsets):
            membership.append(identifier)
            row = rows[identifier]
            assert row["cell_offset"] == list(offset)
            assert row["display_xy"] == [a+b for a, b in zip(group["display_anchor"], offset)]
            assert row["group"] == group["id"]
            sx, sy = row["source_xy"]
            assert group["key"] == ["starlink", row["kind"], round(sx/placement["group_grid_inches"]), round(sy/placement["group_grid_inches"])]
    assert sorted(membership) == sorted([*sites, *pops])
    points = [r for r in rows.values() if r["kind"] != "link"]
    for i, row in enumerate(points):
        x, y = row["display_xy"]
        rr = row["radius_inches"]
        assert 0 <= x-rr and x+rr <= WIDTH and 0 <= y-rr and y+rr <= HEIGHT
        for other in points[:i]:
            assert math.dist(row["display_xy"], other["display_xy"]) >= rr+other["radius_inches"]-1e-9
    expected = {(s["id"], k) for s in config["studies"] for k in ("map", "legend")}
    assert len(manifest["records"]) == 6
    assert {(r["study"], r["kind"]) for r in manifest["records"]} == expected
    geometry_by_study = []
    report = {"sheets": 6, "files": 0, "summary": summary, "groups": len(placement["groups"]),
              "equilateral_centered_triangles": 590, "overlapping_mark_bounds": 0,
              "checks": ["source identity and raw field preservation", "blank duplicate reconciliation", "no summed bands",
                         "CDN grid membership and shared hex lattice", "proportional radius with explicit floor and unknown size",
                         "triangle geometry and cell containment", "separate map and attribution sheets", "single-page physical PDF dimensions",
                         "distinct Randoma11y pairs and actual SVG colors", "Antarctic land below source data"]}
    for record in manifest["records"]:
        root = None
        for output in record["outputs"]:
            path = args.output/output["path"]
            assert digest(path) == output["sha256"] and path.stat().st_size == output["bytes"]
            report["files"] += 1
            if path.suffix == ".pdf":
                info = subprocess.check_output(["pdfinfo", str(path)], text=True)
                assert re.search(r"Pages:\s+1\b", info)
                size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
                assert size and math.isclose(float(size[1]), WIDTH*72, abs_tol=.02)
                assert math.isclose(float(size[2]), HEIGHT*72, abs_tol=.02)
            elif path.name.endswith(".svg.gz"):
                data = gzip.decompress(path.read_bytes())
                assert hashlib.sha256(data).hexdigest() == record["svg_sha256"]
                root = E.fromstring(data)
            else:
                with Image.open(path) as image:
                    assert image.width == 3840 and abs(image.height-3840*HEIGHT/WIDTH) < 1
        assert root is not None
        identifiers = root.xpath("//*[@id]/@id")
        assert len(identifiers) == len(set(identifiers))
        assert root.get("data-sheet-kind") == record["kind"]
        verify_palette(root, manifest["palettes"][record["study"]], provenance)
        if record["kind"] == "legend":
            assert root.xpath('//*[@id="capability-legend-ledger"]')[0].get("data-receipt-sha256") == digest(evidence_path)
            assert set(root.xpath('//*[@data-marker-shape="equilateral-triangle"]/@data-capability')) == set(CAPABILITIES)
            content = " ".join(root.xpath('//*[local-name()="text"]/text()'))
            for phrase in ("52 unknown sizes", "538 sized records", "Natural Earth", "Ofcom", "FCC", "not throughput"):
                assert phrase in content, phrase
            continue
        assert float(root.get("data-cyclic-shift-in")) == SHIFT
        assert root.xpath('//*[@id="antarctica-consolidated-inset"]')
        verify_land_order(root)
        frame = root.xpath('//*[@id="st2-image-frame"]')[0]
        assert f"scale({SCALE})" in frame.get("transform")
        assert len(root.xpath('//*[@id="st2-image-window"]/*[local-name()="use"]')) == 3
        assert not root.xpath('//*[@id="network-groundstations-legend-and-provenance"]')
        meta = root.xpath('//*[@id="groundstation-capability-metadata"]')[0]
        assert meta.get("data-receipt-sha256") == digest(evidence_path)
        marks = root.xpath('//*[@data-groundstation="true"]')
        assert len(marks) == 590 and {m.get("data-record-id") for m in marks} == set(sites)
        assert set(root.xpath('//*[@data-kind="pop"]/@data-record-id')) == set(pops)
        assert set(root.xpath('//*[@data-gateway-link="true"]/@data-record-id')) == set(links)
        geometry = []
        for mark in marks:
            row = sites[mark.get("data-record-id")]
            assert mark.get("data-capability") == row["capability"]
            assert mark.get("data-status") == row["status"]
            assert mark.get("data-pattern") == next(s["pattern"] for s in config["studies"] if s["id"] == record["study"])
            rr = float(mark.get("data-radius-inches"))
            area = row["aperture_proxy_m2"]
            size = config["size"]
            expected_r = (max(size["minimum_radius_inches"], size["reference_radius_inches"]*math.sqrt(area/size["reference_aperture_m2"]))
                          if area is not None else size["unknown_radius_inches"])
            assert math.isclose(rr, expected_r)
            unknown = mark.xpath('./*[@data-role="unknown-size"]')
            assert len(unknown) == (1 if area is None else 0)
            if unknown:
                assert E.QName(unknown[0]).localname == "rect"
            polygon = mark.xpath('./*[@data-role="triangle-boundary"]')[0]
            vertices = [tuple(map(float, pair.split(","))) for pair in polygon.get("points").split()]
            assert len(vertices) == 3
            assert abs(sum(x for x, y in vertices)) < 1e-8 and abs(sum(y for x, y in vertices)) < 1e-8
            sides = [math.dist(vertices[i], vertices[(i+1)%3]) for i in range(3)]
            assert max(sides)-min(sides) < 1e-8 and vertices[0][1] < vertices[1][1]
            fill = mark.xpath('./*[@data-role="radial-fill"]')[0]
            assert fill.get("clip-path") == f'url(#{mark.get("id")}-clip)'
            clip = root.xpath(f'//*[@id="{mark.get("id")}-clip"]')[0]
            assert clip[0].get("points") == polygon.get("points")
            pattern = mark.get("data-pattern")
            units = fill.xpath('./*[@data-radial-unit]')
            count = CAPABILITIES[row["capability"]][2 if pattern == "rings" else 1]
            assert len(units) == count
            for unit in units:
                assert unit.get("data-radial-unit") == {"rings": "ring", "spokes": "spoke", "petals": "petal"}[pattern]
                if pattern == "rings":
                    assert E.QName(unit).localname == "circle" and float(unit.get("r")) < rr/2
                else:
                    assert E.QName(unit).localname == "path" and unit.get("d").startswith("M 0 0")
                    assert (" Q " in unit.get("d")) == (pattern == "petals")
            # Flat-top hex inequalities, with its triangle centered at origin.
            for x, y in vertices:
                cell = row["cell_radius_inches"]
                assert abs(y) <= math.sqrt(3)*cell/2+1e-8
                assert math.sqrt(3)*abs(x)+abs(y) <= math.sqrt(3)*cell+1e-8
            center = [float(v) for v in re.findall(r"[-\d.]+", mark.get("transform"))]
            assert all(math.isclose(a, b, abs_tol=1e-9) for a, b in zip(center, row["display_xy"]))
            names = root.xpath(f'//*[local-name()="text" and @data-locpoint="{mark.get("id")}"]')
            assert len(names) == 1 and names[0].text == row["name"]
            assert names[0].getparent().get("style") == "display:none"
            assert math.isclose(float(names[0].get("font-size"))*72*SCALE, 9)
            geometry.append((row["id"], center, vertices, rr))
        geometry_by_study.append(geometry)
    assert geometry_by_study[0] == geometry_by_study[1] == geometry_by_study[2]
    assert report["files"] == 18
    (args.output/"validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print("Verified 3 map/legend pairs, 590 centered triangles, 66 PoPs, 124 links; 538 sized / 52 unknown; identical study geometry")


if __name__ == "__main__":
    main()

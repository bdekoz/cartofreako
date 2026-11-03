#!/usr/bin/env python3
"""Render three antenna-capability studies using CDN grouping and Setouchi sheets."""

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import copy
import gzip
import html
import importlib
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image
from cartofreako_style import Projection, STYLE, hexoffsets, hexpoints
from groundstation_capabilities import CAPABILITIES, normalize
from legend_informatics import E, ROOT, NS, WIDTH, HEIGHT, digest, el, text, save, register_fonts, font_environment
from setouchi_world_framing import make_plate, SCALE

MSP = importlib.import_module("build-msp-speculations")
CONFIG = ROOT/"config/groundstation-capabilities-20261103.json"
STEM = "network-groundstations-authagraph-44-19.052559"
INK = "http://www.inkscape.org/namespaces/inkscape"


def layer(parent, identifier, label, hidden=False):
    node = el("g", parent, id=identifier)
    node.set("{"+INK+"}groupmode", "layer")
    node.set("{"+INK+"}label", label)
    if hidden:
        node.set("style", "display:none")
    return node


def radius(record, config):
    size = config["size"]
    if record["kind"] == "pop":
        return .032
    area = record["aperture_proxy_m2"]
    if area is None:
        return size["unknown_radius_inches"]
    return max(size["minimum_radius_inches"],
               size["reference_radius_inches"]*math.sqrt(area/size["reference_aperture_m2"]))


def layout(records, projection, config):
    """CDN's source-family/grid grouping and hexoffsets, with a collision pass.

    Larger triangles require a wider hex lattice than tiny CDN record cells.
    Retain CDN grid memberships; move whole groups to the nearest clear lattice
    position rather than merging, dropping records or changing their weights.
    """
    points = [r for r in records if r["kind"] != "link"]
    groups = {}
    for r, (x, y) in zip(points, projection.project([r["geometry"]["coordinates"][:2] for r in points])):
        r["source_xy"] = [x, y]
        r["radius_inches"] = radius(r, config)
        key = ("starlink", r["kind"], round(x/STYLE["cdn"]["group_grid_in"]), round(y/STYLE["cdn"]["group_grid_in"]))
        groups.setdefault(key, {"key": list(key), "anchor": [x, y], "records": []})["records"].append(r)
    placed = []
    result = []
    # Place large clusters first. The source IDs are the deterministic tiebreaker.
    for group in sorted(groups.values(), key=lambda g: (-len(g["records"]), -max(r["radius_inches"] for r in g["records"]), g["records"][0]["id"])):
        members = sorted(group["records"], key=lambda r: (-r["radius_inches"], r["id"]))
        cell = max(config["layout"]["cell_radius_min_inches"],
                   max(r["radius_inches"] for r in members)*config["layout"]["cell_radius_to_maximum_triangle_radius"])
        candidates = hexoffsets(512, cell)
        offsets = hexoffsets(len(members), cell)
        ax, ay = group["anchor"]
        for mx, my in candidates:
            positions = [(ax+mx+dx, ay+my+dy, r["radius_inches"]) for r, (dx, dy) in zip(members, offsets)]
            if any(x-r < .02 or x+r > WIDTH-.02 or y-r < .02 or y+r > HEIGHT-.02 for x, y, r in positions):
                continue
            pad = config["layout"]["collision_padding_inches"]
            if any(math.hypot(x-px, y-py) < r+pr+pad for x, y, r in positions for px, py, pr in placed):
                continue
            break
        else:
            raise ValueError("No clear honeycomb location for " + members[0]["id"])
        gid = "cluster-"+members[0]["id"]
        for r, (x, y, rr), offset in zip(members, positions, offsets):
            r.update(display_xy=[x, y], group=gid, group_size=len(members), cell_offset=list(offset), cell_radius_inches=cell)
        placed.extend(positions)
        result.append({"id": gid, "key": group["key"], "source_anchor": [ax, ay],
                       "display_anchor": [ax+mx, ay+my], "cell_radius_inches": cell, "records": [r["id"] for r in members]})
    return {"group_grid_inches": STYLE["cdn"]["group_grid_in"],
            "cell_radius_range_inches": [min(g["cell_radius_inches"] for g in result), max(g["cell_radius_inches"] for g in result)],
            "largest_group": max(len(g["records"]) for g in result), "groups": result,
            "maximum_displacement_inches": max(math.dist(r["source_xy"], r["display_xy"]) for r in points)}


def triangle_points(r):
    return [(0, -r), (math.sqrt(3)*r/2, r/2), (-math.sqrt(3)*r/2, r/2)]


def points_string(points):
    return " ".join(f"{x:.10f},{y:.10f}" for x, y in points)


def symbol(parent, defs, record, pattern, recipe, identifier, x, y, r, example=False):
    known = record.get("aperture_proxy_m2") is not None
    capability = record.get("capability", "unknown")
    status = record.get("status", "unconfirmed")
    color = recipe["neutral"] if status == "retired" else MSP.adjusted("#ff1d10", recipe)
    node = el("g", parent, id=identifier, transform=f"translate({x:.10f} {y:.10f})",
              data_marker_shape="equilateral-triangle", data_capability=capability,
              data_status=status, data_pattern=pattern, data_radius_inches=r,
              data_size_known=str(known).lower(), data_aperture_m2=record["aperture_proxy_m2"] if known else "")
    if not example:
        node.set("data-record-id", record["id"])
        node.set("data-groundstation", "true")
        node.set("data-name", record["name"])
        node.set("data-source-x", str(record["source_xy"][0]))
        node.set("data-source-y", str(record["source_xy"][1]))
        node.set("data-group", record["group"])
        node.set("data-longitude", str(record["geometry"]["coordinates"][0]))
        node.set("data-latitude", str(record["geometry"]["coordinates"][1]))
    area_text = f"{record['aperture_proxy_m2']:.2f} m²" if known else "unknown"
    el("title", node).text = (record.get("name", CAPABILITIES[capability][0])+" | "+CAPABILITIES[capability][0]
        +f" | listed aperture proxy: {area_text} | "+record.get("status_raw", status)
        +" | " + ("incomplete inventory" if record.get("incomplete_inventory") else "")
        +" | not measured throughput")
    pts = points_string(triangle_points(r))
    clip = el("clipPath", defs, id=identifier+"-clip", clipPathUnits="userSpaceOnUse")
    el("polygon", clip, points=pts)
    # Light field and categorical radial ink, all inside the triangle.
    el("polygon", node, points=pts, fill=recipe["background"], stroke="none")
    el("polygon", node, points=pts, fill=color, fill_opacity=.13 if known else .035, stroke="none")
    fill = el("g", node, clip_path=f"url(#{identifier}-clip)", data_role="radial-fill")
    rays, rings = CAPABILITIES[capability][1:]
    width = max(.006, r*.05)
    pattern_color = recipe["text"]
    for i in range(rays if pattern != "rings" else rings):
        if pattern == "rings":
            # Keep the rings within the triangle's incircle. Rings beyond
            # r/2 reduce to corner fragments and make adjacent classes alike.
            rr = r*(.25 if rings == 1 else .12+.34*i/(rings-1))
            attributes = {"stroke_dasharray": f"{r*.18} {r*.13}"} if capability in ("e", "qv", "ku") else {}
            el("circle", fill, cx=0, cy=0, r=rr, fill="none", stroke=pattern_color,
               stroke_width=width, data_radial_unit="ring", **attributes)
        else:
            angle = -math.pi/2+2*math.pi*i/rays
            if pattern == "spokes":
                el("path", fill, d=f"M 0 0 L {r*1.5*math.cos(angle)} {r*1.5*math.sin(angle)}",
                   fill="none", stroke=pattern_color, stroke_width=width, data_radial_unit="spoke")
            else:
                left, right = angle-.23, angle+.23
                d = (f"M 0 0 Q {r*.7*math.cos(left)} {r*.7*math.sin(left)} {r*1.35*math.cos(angle)} {r*1.35*math.sin(angle)} "
                     f"Q {r*.7*math.cos(right)} {r*.7*math.sin(right)} 0 0 Z")
                el("path", fill, d=d, fill=pattern_color, stroke=pattern_color,
                   stroke_width=width*.35, data_radial_unit="petal")
    if capability == "ttc":
        el("circle", fill, cx=0, cy=0, r=r*.07, fill="none", stroke=pattern_color, stroke_width=width)
        el("path", fill, d=f"M {-r} 0 L {r} 0", fill="none", stroke=pattern_color, stroke_width=width)
    if capability == "unknown":
        t = text(node, 0, r*.19 if known else -r*.46, "?", r*.80 if known else r*.5, text_anchor="middle")
        t.set("fill", color)
    if not known:
        # Unknown hardware size is explicit, independent of capability/status.
        # A square cannot be mistaken for one of the concentric-ring fills.
        el("rect", node, x=-r*.19, y=-r*.19, width=r*.38, height=r*.38,
           fill=recipe["background"], stroke=recipe["text"], stroke_width=.006,
           data_role="unknown-size")
    attrs = {"stroke_dasharray": ".024 .014"} if status == "unconfirmed" else ({"stroke_dasharray": ".004 .012"} if status == "retired" else {})
    el("polygon", node, points=pts, fill="none", stroke=color, stroke_width=.010,
       stroke_linejoin="round", data_role="triangle-boundary", **attrs)
    return node


def map_source(source, records, placement, config, study, recipe, receipt_hash):
    root = MSP.read_svg(source)
    for child in list(root):
        if child.get("id", "").startswith("starlink-gateways-") or "legend" in child.get("id", ""):
            root.remove(child)
    # Retain original projected link geometry; lines never acquire antenna marks.
    links = root.xpath('//*[@data-gateway-link="true"]')
    link_records = [r for r in records if r["kind"] == "link"]
    if len(links) != len(link_records):
        raise ValueError("Projected link accounting differs from the source")
    for node, record in zip(links, link_records):
        node.set("data-record-id", record["id"])
        MSP.set_style(node, stroke=recipe["neutral"], stroke_opacity=.22, stroke_width=.008)
    for node in root.xpath('//*[@id="network-groundstations-ocean"]'):
        MSP.set_style(node, fill=recipe["background"])
    for node in root.xpath('//*[@id="terrestrial-land"]//*[local-name()="path"]'):
        MSP.set_style(node, fill=recipe["land"], stroke="none")
    defs = el("defs", root)
    meta = el("metadata", root, id="groundstation-capability-metadata",
              data_source_records=len(records), data_site_records=sum(r["kind"] == "antenna-site" for r in records),
              data_pop_records=sum(r["kind"] == "pop" for r in records), data_link_records=len(link_records),
              data_receipt_sha256=receipt_hash, data_pattern=study["pattern"], data_config_sha256=digest(CONFIG))
    meta.text = json.dumps({"size": config["size"], "layout": config["layout"], "palette": recipe}, sort_keys=True)
    tethers = layer(root, "groundstation-location-tethers", "Source positions / displacement tethers")
    vendor = layer(root, "groundstations-starlink", "Starlink / antenna capabilities")
    groups = {}
    for capability, (label, _, _) in CAPABILITIES.items():
        group = layer(vendor, "groundstations-"+capability, label)
        groups[capability] = (layer(group, "groundstations-"+capability+"-locpoint", label+" / locpoint"),
                              layer(group, "groundstations-"+capability+"-name", label+" / name", True))
    pops = layer(root, "groundstation-pops", "Starlink / PoPs (unscaled)")
    cells = layer(root, "groundstation-cell-guides", "Hex cell construction guides", True)
    for r in records:
        if r["kind"] == "link":
            continue
        x, y = r["display_xy"]
        sx, sy = r["source_xy"]
        if math.hypot(x-sx, y-sy) > .015:
            el("path", tethers, d=f"M {sx} {sy} L {x} {y}", fill="none", stroke=recipe["neutral"],
               stroke_opacity=.45, stroke_width=.004, data_record_id=r["id"])
            el("circle", tethers, cx=sx, cy=sy, r=.009, fill=recipe["neutral"])
        el("polygon", cells, points=hexpoints(x, y, r["cell_radius_inches"]), fill="none",
           stroke=recipe["neutral"], stroke_width=.003, data_record_id=r["id"])
        if r["kind"] == "pop":
            p = el("circle", pops, cx=x, cy=y, r=r["radius_inches"], fill=recipe["background"],
                   stroke=recipe["text"], stroke_width=.009, data_record_id=r["id"], data_kind="pop")
            el("title", p).text = r["name"]+" / PoP; no antenna-size inference"
            continue
        locpoint, names = groups[r["capability"]]
        symbol(locpoint, defs, r, study["pattern"], recipe, "site-"+r["id"], x, y, r["radius_inches"])
        text(names, x, y-r["radius_inches"]-.03, r["name"], 9/72/SCALE,
             text_anchor="middle", data_record_id=r["id"], data_locpoint="site-"+r["id"]).set("fill", recipe["text"])
    return root


def legend(config, study, recipe, summary, placement, receipt_hash):
    root = el("svg", width="44in", height=f"{HEIGHT}in", viewBox=f"0 0 44 {HEIGHT}",
              data_sheet_kind="legend", data_legend_style="setouchi-st2", data_map_companion=STEM+".svg")
    el("title", root).text = "Groundstation capability study / "+study["name"]+" / legend and attribution"
    el("rect", root, id="legend-paper", width=44, height=HEIGHT, fill=recipe["background"])
    defs = el("defs", root)
    el("metadata", root, id="capability-legend-ledger", data_receipt_sha256=receipt_hash).text = json.dumps(config, sort_keys=True)
    def tx(x, y, value, size=18/72, **attrs):
        n = text(root, x, y, value, size, **attrs)
        n.set("fill", recipe["text"])
        return n
    for i, title in enumerate(("Groundstation capabilities", study["name"]+" / Starlink")):
        tx(.4, -43.42+i*.63, title, 48/72, font_weight="700", transform="rotate(90)")
    tx(.8, .8, "Listed antenna hardware / 3 November 2026 source", 28/72, font_weight="700")
    tx(.8, 1.4, "590 antenna records · 66 PoPs · 124 links", 23/72)
    tx(.8, 1.95, f"{summary['sized_sites']} sized records · {summary['unknown_size_sites']} unknown sizes · {summary['incomplete_inventories']} incomplete inventories", 19/72)
    y = 2.8
    blocks = [
        ("Read the map", [
            "Triangle area scales with the largest complete listed antenna bank: max(N × π × D² / 4). Size uses antenna count and diameter; bands are never added together.",
            "This is an aperture proxy for listed hardware, including planned and licensed installations. It is not throughput, antenna gain, installed capacity or a claim of current operation.",
            "A hollow central square means size unknown. Small known triangles have a 0.04-inch source radius floor. Capability patterns are categorical: their rings, rays and petals are not antenna counts or RF beam diagrams.",
            "Solid outline: at least one source operational flag is TRUE. Dashed: unconfirmed or planned. Dotted, muted outline: source says retired/withdrawn. Flags are not independently verified; raw status remains in the evidence receipt.",
            "One point record per hex cell; triangles are centered inside the invisible cells. CDN grouping uses the same 0.0625-inch projected grid and hexoffsets routine. Cells fit the largest triangle in each group; a collision pass moves groups when needed. Tethers end at source positions.",
            "PoPs remain small open circles. Lines retain supplied geometry and have no antenna symbol. Repeated coordinates are retained as distinct source records, including upgrade proposals; no record is counted twice as a line endpoint.",
        ]),
        ("Sources / attribution", [
            "Unofficial Starlink Global Gateways & PoPs: user-supplied starlink-global-gateways-pops.20261103.kml and lossless-metadata GeoJSON conversion. The supplied file specifies neither author nor license. Antenna counts, bands and statuses come from its ExtendedData.",
            "Diameter is interpreted in metres, consistent with FCC SpaceX 1.47 m and 1.85 m listings (DOC-374641A1; DOC-395259A1). This does not verify each site. Composite sizes and invalid fractional counts remain unresolved.",
            "Starlink submission to Ofcom, 19 March 2025, pp. 4–5: existing V4 antennas support both Ka and E. This supports keeping band inventories separate; it does not validate the 2026 collection.",
            "Natural Earth 1:10m land, public domain. Cartography and processing: Cartofreako. Atkinson Hyperlegible. Source URLs, raw fields, exceptions, formulas and hashes accompany the plates in capability-evidence.json and manifest.json.",
            "Setouchi AuthaGraph: 43.5-inch image, +4.35-inch printed horizontal move, Antarctic terrestrial inset at lower left. Infrastructure keeps its geographic reference; display displacement is recorded separately.",
        ]),
    ]
    for title, paragraphs in blocks:
        tx(.8, y, title, 22/72, font_weight="700"); y += .47
        for paragraph in paragraphs:
            for line in MSP.ORBITAL.wrapped(paragraph, 17/72, 26):
                tx(.8, y, line, 17/72); y += .32
            y += .14
        y += .25
    if y > 16.6:
        raise ValueError(f"Legend bibliography exceeds its panel: {y}")
    tx(.8, 17.0, "MSP speculation 1 / Charcoal green", 22/72, font_weight="700")
    for i, line in enumerate(("Epson Stylus Pro 9000 · metallic glossy paper · cyan and light magenta reported low.",
                              "Dark, green-biased ground responds to reported violet grays. This is an unmeasured print hypothesis.",
                              "All three capability studies use the same palette, records, size mapping and placement.")):
        tx(.8, 17.55+i*.35, line, 16/72)
    tx(42.1, .85, "Capability pattern / source record count", 21/72, text_anchor="end", font_weight="700")
    for i, (capability, (label, _, _)) in enumerate(CAPABILITIES.items()):
        yy = 1.55+i*.74
        example = {"capability": capability, "status": "reported-operational", "aperture_proxy_m2": 50}
        symbol(root, defs, example, study["pattern"], recipe, "key-"+capability, 41.75, yy, .25, True)
        tx(41.2, yy+.06, label+" / "+str(summary["capabilities"].get(capability, 0)), 18/72, text_anchor="end")
    tx(42.1, 8.7, "Aperture proxy / square metres", 21/72, text_anchor="end", font_weight="700")
    for i, area in enumerate((config["size"]["reference_aperture_m2"], 50, 100, 200)):
        example = {"kind": "antenna-site", "capability": "ka", "status": "reported-operational", "aperture_proxy_m2": area}
        rr = radius(example, config)*SCALE
        xx = 31.6+i*3.05
        symbol(root, defs, example, study["pattern"], recipe, "size-key-"+str(i), xx, 9.6, rr, True)
        tx(xx, 10.15, f"{area:.1f}" if i == 0 else str(area), 16/72, text_anchor="middle")
    tx(42.1, 10.75, "Size samples print at the actual map scale.", 15/72, text_anchor="end")
    for i, status in enumerate(("reported-operational", "unconfirmed", "retired")):
        yy = 11.65+i*.65
        example = {"capability": "ka-e", "status": status, "aperture_proxy_m2": 50}
        symbol(root, defs, example, study["pattern"], recipe, "status-key-"+status, 41.75, yy, .22, True)
        label = {"reported-operational": "Source flag TRUE", "unconfirmed": "Unconfirmed / planned", "retired": "Retired / withdrawn"}[status]
        tx(41.2, yy+.05, label+" / "+str(summary["statuses"][status]), 17/72, text_anchor="end")
    example = {"capability": "community", "status": "unconfirmed", "aperture_proxy_m2": None}
    symbol(root, defs, example, study["pattern"], recipe, "unknown-size-key", 41.75, 14.0, .22, True)
    tx(41.2, 14.05, f"Unknown size / central square / {summary['unknown_size_sites']}", 17/72, text_anchor="end")
    el("circle", root, cx=41.75, cy=14.7, r=.10, fill=recipe["background"], stroke=recipe["text"], stroke_width=.012)
    tx(41.2, 14.75, "PoP / fixed-size open circle / 66", 17/72, text_anchor="end")
    tx(42.1, 15.55, f"{len(placement['groups'])} projected source groups", 17/72, text_anchor="end")
    tx(42.1, 16.0, "Patterns enlarged above for comparison.", 15/72, text_anchor="end")
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, default=ROOT/"build/orbital-technosphere-20261103")
    parser.add_argument("--output", type=Path, default=ROOT/"output/groundstation-capabilities-20261103")
    parser.add_argument("--work", type=Path, default=ROOT/"build/groundstation-capabilities-20261103")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    register_fonts()
    config = json.loads(CONFIG.read_text())
    source = ROOT/config["source"]
    profile = json.loads((ROOT/config["source_profile"]).read_text())
    if digest(source) != profile["source"]["gateways_sha256"]:
        raise ValueError("Groundstation source checksum mismatch")
    records, summary = normalize(json.loads(source.read_text()))
    placement = layout(records, Projection("authagraph", args.work/"projection"), config)
    recipe = next(s for s in json.loads(MSP.CONFIG.read_text())["studies"] if s["id"] == config["palette"])
    args.output.mkdir(parents=True, exist_ok=True)
    evidence = {"schema": "cartofreako-groundstation-capability-evidence-v1", "source": config["source"],
                "source_sha256": digest(source), "source_kml": profile["source"]["kml"],
                "source_kml_sha256": profile["source"]["kml_sha256"], "configuration": config,
                "summary": summary, "placement": placement, "records": records}
    evidence_path = args.output/"capability-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False)+"\n")
    receipt_hash = digest(evidence_path)
    original = args.build_root/"authagraph/svg"/(STEM+".svg")
    jobs, framings = [], {}
    for study in config["studies"]:
        unframed = args.work/study["id"]/(STEM+"-source.svg")
        save(map_source(original, records, placement, config, study, recipe, receipt_hash), unframed)
        svg = args.work/study["id"]/(STEM+".svg")
        framings[study["id"]] = make_plate(unframed, svg, STEM+"-legend.svg")
        root = MSP.read_svg(svg)
        root.set("data-sheet-kind", "map")
        root.set("data-study", study["id"])
        for node in root.xpath('//*[@id="st2-sheet-paper" or @id="st2-image-background"]'):
            node.set("fill", recipe["background"])
        save(root, svg)
        leg = svg.with_name(STEM+"-legend.svg")
        save(legend(config, study, recipe, summary, placement, receipt_hash), leg)
        jobs.extend((study, kind, path) for kind, path in (("map", svg), ("legend", leg)))
    env = font_environment()
    def export(job):
        study, kind, svg = job
        destination = args.output/study["id"]
        destination.mkdir(parents=True, exist_ok=True)
        pdf, webp, archive = [destination/(svg.stem+ext) for ext in (".pdf", ".webp", ".svg.gz")]
        png = svg.with_suffix(".png")
        with svg.with_suffix(".log").open("w") as log:
            for command in (["inkscape", str(svg), "--export-area-page", "--export-filename="+str(pdf)],
                            ["inkscape", str(svg), "--export-area-page", "--export-width=3840", "--export-filename="+str(png)]):
                subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        with Image.open(png) as image:
            image.convert("RGB").save(webp, "WEBP", quality=94, method=6)
        with archive.open("wb") as stream, gzip.GzipFile(fileobj=stream, mode="wb", mtime=0, filename="") as compressed:
            compressed.write(svg.read_bytes())
        print("Exported", study["id"], kind, flush=True)
        return {"study": study["id"], "kind": kind, "svg_sha256": digest(svg),
                "outputs": [{"path": str(p.relative_to(args.output)), "bytes": p.stat().st_size, "sha256": digest(p)} for p in (pdf, webp, archive)]}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        outputs = list(pool.map(export, jobs))
    manifest = {"schema": "cartofreako-groundstation-capability-delivery-v1", "configuration": config,
                "evidence_sha256": receipt_hash, "source_svg_sha256": digest(original), "palette": recipe,
                "scripts": {str(p.relative_to(ROOT)): digest(p) for p in [Path(__file__), ROOT/"scripts/groundstation_capabilities.py", ROOT/"scripts/cartofreako_style.py", ROOT/"scripts/setouchi_world_framing.py"]},
                "font_sha256": digest(ROOT/"assets/fonts/atkinson-hyperlegible/provenance.json"),
                "framing": framings, "records": outputs}
    (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    cards = []
    for study in config["studies"]:
        stem = study["id"]+"/"+STEM
        key = []
        for capability, (label, _, _) in CAPABILITIES.items():
            svg = el("svg", viewBox="-.32 -.34 .64 .60", role="img", aria_label=label)
            defs = el("defs", svg)
            example = {"capability": capability, "status": "reported-operational", "aperture_proxy_m2": 50}
            symbol(svg, defs, example, study["pattern"], recipe, "web-"+study["id"]+"-"+capability, 0, 0, .27, True)
            key.append('<figure>'+E.tostring(svg, encoding="unicode")+'<figcaption>'+html.escape(label)+'</figcaption></figure>')
        cards.append(f'<section id="{study["id"]}"><h2>{html.escape(study["name"])}</h2><p>{html.escape(study["note"])}</p>'
                     +'<p>Enlarged pattern key, uniform example size:</p><div class="symbols">'+''.join(key)+'</div><div class="pair">'
                     f'<article><a href="{stem}.webp"><img src="{stem}.webp" alt="{study["name"]} map"></a><p><a href="{stem}.pdf">Map PDF</a> · <a href="{stem}.svg.gz">Editable map SVG</a></p></article>'
                     f'<article><a href="{stem}-legend.webp"><img src="{stem}-legend.webp" alt="{study["name"]} legend and attribution"></a><p><a href="{stem}-legend.pdf">Legend PDF</a> · <a href="{stem}-legend.svg.gz">Editable legend SVG</a></p></article></div></section>')
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Groundstation capability studies</title>'
    page += '<style>body{font:18px system-ui;background:#26382f;color:#e4ecd3;max-width:1800px;margin:auto;padding:32px}a{color:#d6e5a7}p{max-width:100ch;line-height:1.5}h1{font-size:40px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}img{width:100%;height:auto}section{margin:48px 0}nav{display:flex;gap:24px;flex-wrap:wrap}.symbols{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:14px;margin:24px 0 40px}.symbols figure{margin:0;text-align:center;font-size:14px}.symbols svg{width:100%;height:110px}@media(max-width:800px){.pair{grid-template-columns:1fr}body{padding:16px}}</style>'
    page += '<h1>Groundstation capability studies</h1><p>Three radial fills on the same Setouchi AuthaGraph map. Triangles sit at the centers of hexagonal cells; their areas scale with the largest complete listed antenna bank’s aperture. All three use MSP speculation 1’s dark palette.</p>'
    page += f'<p><strong>{summary["sized_sites"]} antenna records can be sized; {summary["unknown_size_sites"]} have unknown sizes.</strong> The 590 antenna records include planned and retired installations. The 66 PoPs and 124 supplied lines remain separate. This is a hardware proxy, not measured throughput or a verified census of operating sites.</p>'
    page += '<p>Solid, dashed and dotted triangle outlines distinguish source-reported operation, unconfirmed/planned status and retirement. A hollow central square marks unknown size. The categorical patterns are not antenna counts or radiation diagrams. Open the vector PDFs to inspect fine patterns at print size.</p>'
    page += '<nav>'+''.join(f'<a href="#{s["id"]}">{s["name"]}</a>' for s in config["studies"])+'</nav>'
    page += '<p><a href="capability-evidence.json">Source fields, calculations and placement</a> · <a href="manifest.json">Delivery checksums</a> · <a href="../msp-speculations-20261103/index.html">Original MSP color proofs</a></p>'+''.join(cards)+'</html>'
    (args.output/"index.html").write_text(page)
    print(json.dumps(summary, indent=2))
    print("Completed six map/legend sheets:", args.output/"index.html")


if __name__ == "__main__":
    main()

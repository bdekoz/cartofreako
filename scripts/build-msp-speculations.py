#!/usr/bin/env python3
"""Build documented metallic-paper color and layout studies in the Setouchi frame."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import gzip
import importlib
import json
from pathlib import Path
import posixpath
import re
import shutil
import subprocess

from PIL import Image
from legend_informatics import E, ROOT, NS, WIDTH, HEIGHT, digest, el, font_environment, register_fonts, save, text
from setouchi_world_framing import make_plate, SCALE, SHIFT

ORBITAL = importlib.import_module("split-orbiting-plates")
SUFFIX = "-authagraph-44-19.052559"
CONFIG = ROOT / "config/msp-speculations-20261103.json"


def read_svg(path):
    return E.parse(str(path), E.XMLParser(huge_tree=True)).getroot()


def style(node):
    return dict(p.strip().split(":", 1) for p in node.get("style", "").split(";") if ":" in p)


def set_style(node, **values):
    current = style(node)
    current.update({k.replace("_", "-"): str(v) for k, v in values.items()})
    node.set("style", ";".join(k+":"+v for k, v in current.items()))


def ground_legend(source, map_name):
    metadata = source.find(f"{{{NS}}}metadata")
    root = el("svg", width="44in", height=f"{HEIGHT}in", viewBox=f"0 0 44 {HEIGHT}",
              role="img", data_sheet_kind="legend", data_legend_style="setouchi-st2", data_map_companion=map_name)
    el("title", root).text = "Network groundstations / legend and attribution"
    root.append(copy.deepcopy(metadata))
    el("rect", root, id="legend-paper", width=44, height=HEIGHT, fill="white")
    key = el("g", root, id="groundstation-legend")
    for i, title in enumerate(("Network groundstations", "Starlink / AuthaGraph")):
        text(key, .4, -43.42+i*.63, title, 56/72, font_weight="700", transform="rotate(90)")
    text(key, 42.38, .65, "Starlink gateways and PoPs / 3 November 2026", 24/72, text_anchor="end", font_weight="700")
    text(key, 42.38, 1.2, "780 source placemarks / 656 points and 124 lines", 16/72, text_anchor="end")
    symbols = source.xpath('//*[@data-groundstation="true"]')
    symbol = copy.deepcopy(symbols[0])
    for attr in list(symbol.attrib):
        if attr.startswith("data-"):
            del symbol.attrib[attr]
    x0, y0, x1, y1 = ORBITAL.LAYOUT.shape_bounds(symbol)
    icon = el("g", key, transform=f"translate(42.14 2.1) scale(4) translate({-(x0+x1)/2} {-(y0+y1)/2})")
    icon.append(symbol)
    text(key, 41.7, 2.1, "Gateway / PoP record position", 18/72, text_anchor="end")
    el("path", key, d="M 41.96 2.65 L 42.32 2.65", data_role="gateway-link-key",
       style="fill:none;stroke:rgb(255,29,16);stroke-width:0.0115;stroke-opacity:1")
    text(key, 41.7, 2.65, "Supplied link geometry", 18/72, text_anchor="end")
    y = 3.5
    for note in ["Source line placemarks also retain their representative position marker.",
                 "The source is an unofficial infrastructure collection. Feature descriptions, folders, styles and original KML are preserved in the conversion.",
                 "AuthaGraph cyclic move: +4.35 printed inches. Antarctic land is deliberately displaced to the lower left; infrastructure retains source coordinates."]:
        for line in ORBITAL.wrapped(note, 14/72, 11.8):
            text(key, 42.38, y, line, 14/72, text_anchor="end")
            y += .29
        y += .12
    panel = el("g", root, id="plate-source-bibliography")
    text(panel, .8, .8, "Data bibliography / attribution", 28/72, font_weight="700")
    blocks = [
        ("Unofficial Starlink Global Gateways & PoPs", [
            "User-supplied KML: starlink-global-gateways-pops.20261103.kml.",
            "780 features: 656 points and 124 line strings. The durable KML-to-GeoJSON conversion retains source metadata and geometry.",
            "The supplied file does not specify a license or author. Its title is credited without attributing it to SpaceX.",
            "https://github.com/bdekoz/cartofreako/tree/main/assets.static/network-groundstations",
        ]),
        ("Natural Earth / terrestrial context", [
            "Natural Earth 1:10m physical land. Public-domain cartographic data.",
            "https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-land/",
        ]),
        ("Cartography and processing / Cartofreako", [
            "Setouchi ST2 separate sheets, proportional 43.5-inch image and cyclic AuthaGraph frame. Atkinson Hyperlegible typography.",
            "https://bdekoz.github.io/cartofreako/docs/pages/projections/authagraph/bibliography.html",
        ]),
    ]
    y = 1.8
    for title, paragraphs in blocks:
        text(panel, .8, y, title, 20/72, font_weight="700")
        y += .45
        for paragraph in paragraphs:
            for line in ORBITAL.wrapped(paragraph, 18/72, 25):
                text(panel, .8, y, line, 18/72)
                y += .34
        y += .45
    el("metadata", root, id="groundstation-source-ledger").text = json.dumps(dict(metadata.attrib), sort_keys=True)
    return root


def prepare_sources(build, work):
    sources = {}
    for subject in json.loads(CONFIG.read_text())["subjects"]:
        filename = subject+SUFFIX+".svg"
        current = build/"authagraph/svg"/filename
        if subject.startswith("orbital"):
            original = build/"authagraph/composition"/filename
            source = read_svg(original)
            if subject.endswith("global"):
                starlink = source.find(f"{{{NS}}}g[@id='starlink']")
                current_starlink = read_svg(current).xpath('//*[@id="starlink"]')[0]
                starlink.remove(starlink.find(f"{{{NS}}}g[@id='starlink-name']"))
                for suffix in ("name", "id"):
                    starlink.append(copy.deepcopy(current_starlink.find(f"{{{NS}}}g[@id='starlink-{suffix}']")))
            legend = read_svg(current.with_name(current.stem+"-legend.svg"))
            for label in legend.xpath('//*[local-name()="text"]'):
                if label.text:
                    label.text = label.text.replace("white margins", "sheet margins")
            note = el("g", legend, id="setouchi-framing-note")
            for i, line in enumerate(ORBITAL.wrapped(
                    "Setouchi AuthaGraph: +4.35-inch printed horizontal move on a 43.5-inch image. "
                    + ("Antarctic land is deliberately displaced to the lower left; object coordinates retain source registration."
                       if subject.endswith("global") else "Celestial directions retain source registration in the same cyclic frame."), 14/72, 26)):
                text(note, .8, 16.05+i*.27, line, 14/72)
        else:
            source = read_svg(current)
            legend = ground_legend(source, filename)
        unframed = work/"sources"/filename
        save(source, unframed)
        target = work/"standard/authagraph/svg"/filename
        framing = make_plate(unframed, target, target.stem+"-legend.svg")
        framed = read_svg(target)
        framed.set("data-sheet-kind", "map")
        framed.set("data-image-scale", str(SCALE))
        save(framed, target)
        legend_path = target.with_name(target.stem+"-legend.svg")
        save(legend, legend_path)
        sources[subject] = {"map": target, "legend": legend_path, "input": current,
                            "framing": framing}
    return sources


def study_subjects(config, recipe):
    return config["subjects"] + recipe.get("additional_subjects", [])


def study_directory(recipe):
    return recipe.get("directory", recipe["id"])


def astronomy_sources(directory, work, label_font_size_pt):
    """Reuse the pinned ST2 sky and bibliography without reframing the sky twice."""
    receipt_path = directory/"provenance.json"
    receipt = json.loads(receipt_path.read_text())
    result = {"input": receipt_path, "framing": receipt["framing"]}
    filename = "astro-all-sky"+SUFFIX
    for kind in ("map", "legend"):
        record = receipt["files"][kind]
        archive = directory/record["file"]
        assert digest(archive) == record["sha256"]
        target = work/"astronomy-sources"/(filename+("-legend" if kind == "legend" else "")+".svg")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.decompress(archive.read_bytes()))
        assert digest(target) == record["svg_sha256"]
        root = read_svg(target)
        root.set("data-sheet-kind", kind)
        if kind == "map":
            root.set("data-image-scale", str(SCALE))
            root.set("data-legend-companion", filename+"-legend.svg")
            labels = root.xpath('//*[@id="labels"]')[0]
            labels.set("data-font-size-pt", str(label_font_size_pt))
            for label in labels:
                label.set("font-size", str(label_font_size_pt/72/SCALE))
        else:
            root.set("data-map-companion", filename+".svg")
            root.append(copy.deepcopy(read_svg(result["map"]).xpath('//*[@id="astro-metadata"]')[0]))
            paper = el("rect", id="legend-paper", width=44, height=HEIGHT, fill="white")
            root.insert(0, paper)
            note = el("g", root, id="astronomy-type-note", data_presentation_only="true")
            text(note, 42.38, 4.3, f"Sky object labels: {label_font_size_pt} pt on the full-size sheet.",
                 14/72, text_anchor="end")
        root.set("data-marker-color-policy", "preserve-source-astronomy")
        save(root, target)
        result[kind] = target
    return result


def capability_sources(directory, work, study):
    """Reuse the audited, framed capability map and its complete companion legend."""
    manifest = json.loads((directory/"manifest.json").read_text())
    evidence = directory/"capability-evidence.json"
    assert digest(evidence) == manifest["evidence_sha256"]
    result = {"input": evidence, "framing": manifest["framing"][study],
              "capability_study": study, "capability_manifest_sha256": digest(directory/"manifest.json")}
    for kind in ("map", "legend"):
        record = next(r for r in manifest["records"] if r["study"] == study and r["kind"] == kind)
        archive = next(f for f in record["outputs"] if f["path"].endswith(".svg.gz"))
        source = directory/archive["path"]
        assert digest(source) == archive["sha256"]
        target = work/"capability-sources"/source.name.removesuffix(".gz")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.decompress(source.read_bytes()))
        assert digest(target) == record["svg_sha256"]
        result[kind] = target
    return result


def scale_sunburst(marker, factor):
    """Scale vertices about their centroid without moving the satellite position."""
    assert marker.get("data-marker-shape") == "sunburst"
    tokens = marker.get("d").split()
    vertices = [(float(tokens[i]), float(tokens[i+1])) for i in range(1, 48, 3)]
    assert len(tokens) == 49 and tokens[::3] == ["M"]+["L"]*15+["Z"]
    center = [sum(v[axis] for v in vertices)/16 for axis in (0, 1)]
    for i, vertex in enumerate(vertices):
        tokens[1+3*i:3+3*i] = [f"{c+factor*(v-c):.12g}" for v, c in zip(vertex, center)]
    marker.set("d", " ".join(tokens))
    marker.set("data-marker-linear-scale", str(factor))


def apply_variant(root, recipe, subject, kind):
    variant = recipe.get("variant", {})
    if not variant or not subject.startswith("orbital"):
        return {}
    factor = variant["starlink_marker_linear_scale"]
    for marker in root.xpath('//*[@data-display-group="starlink" and @data-marker-shape]'):
        scale_sunburst(marker, factor)
    global_plate = subject.endswith("global")
    if global_plate and kind == "map":
        if "global_track_width_scale" in variant:
            tracks = root.xpath('//*[@id="representative-ground-tracks"]')[0]
            for path in tracks:
                if E.QName(path).localname == "path":
                    set_style(path, stroke_width=float(style(path)["stroke-width"])*variant["global_track_width_scale"])
        starlink = root.xpath('//*[@id="starlink"]')[0]
        for suffix in ("name", "id"):
            layer = starlink.find(f"{{{NS}}}g[@id='starlink-{suffix}']")
            layer.set("data-font-size-pt", str(variant["global_starlink_font_size_pt"]))
            for label in layer:
                label.set("font-size", str(variant["global_starlink_font_size_pt"]/72/SCALE))
        # Paint Starlink text before its own symbols and every other foreground group.
        locpoints = starlink.find(f"{{{NS}}}g[@id='starlink-locpoint']")
        starlink.remove(locpoints)
        starlink.append(locpoints)
        parent = starlink.getparent()
        parent.remove(starlink)
        land = parent.find(f"{{{NS}}}g[@id='terrestrial-land']")
        assert land is not None
        parent.insert(parent.index(land)+1, starlink)
    elif kind == "map" and variant.get("observer_starlink_names"):
        starlink = root.xpath('//*[@id="starlink"]')[0]
        names = starlink.find(f"{{{NS}}}g[@id='starlink-name']")
        size = variant["observer_starlink_font_size_pt"]
        set_style(names, display="inline")
        names.set("data-font-size-pt", str(size))
        for label in names:
            label.set("font-size", str(size/72/SCALE))
        # Put every marker above the now-visible Starlink names.
        starlink.remove(names)
        starlink.insert(0, names)
        parent = starlink.getparent()
        parent.remove(starlink)
        first_group = next(n for n in parent if n.get("data-object-count") is not None)
        parent.insert(parent.index(first_group), starlink)
        root.set("data-satellite-name-display", "starlink-only")
    if kind == "legend":
        if global_plate:
            for label in root.xpath('//*[local-name()="text"]'):
                if label.text:
                    label.text = label.text.replace("9 pt", f"{variant['global_starlink_font_size_pt']} pt")
        elif variant.get("observer_starlink_names"):
            for label in root.xpath('//*[local-name()="text"]'):
                if label.text == "Name and locpoint sublayers are independent. Names are hidden by default.":
                    label.text = "Starlink names are visible; all other satellite name layers are hidden."
        note = el("g", root, id="msp-variant-note", data_presentation_only="true")
        lines = ["Starlink sunbursts: 1.5× linear size on both orbital maps."]
        if global_plate:
            lines += [f"Starlink text: {variant['global_starlink_font_size_pt']} pt; all satellite markers paint above it.",
                      "All terrestrial land, including Antarctica, paints below the data."]
            if "global_track_width_scale" in variant:
                lines.append(f"Representative ground tracks: {variant['global_track_width_scale']}× stroke width.")
        elif variant.get("observer_starlink_names"):
            lines.append(f"Starlink names: {variant['observer_starlink_font_size_pt']} pt in the separate name layer, beneath satellite markers.")
        for i, line in enumerate(lines):
            text(note, 42.38, 12.15+i*.32, line, 14/72, text_anchor="end")
    el("metadata", root, id="msp-layout-variant").text = json.dumps(variant, sort_keys=True)
    return variant


def rgb(value):
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))
    match = re.fullmatch(r"rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)", value)
    return tuple(map(int, match.groups())) if match else None


def adjusted(value, recipe):
    original = rgb(value)
    if original is None or max(original) < 5:
        return value
    return recipe["text"]


def palette_metadata(root, recipe):
    for node in root.xpath('//*[@id="msp-color-recipe"]'):
        node.getparent().remove(node)
    root.set("data-color-study", recipe["title"])
    el("metadata", root, id="msp-color-recipe").text = json.dumps(recipe, sort_keys=True)


def print_note(root, recipe):
    for node in root.xpath('//*[@id="msp-print-note"]'):
        node.getparent().remove(node)
    note = el("g", root, id="msp-print-note", data_presentation_only="true")
    text(note, .8, 17.0, recipe["title"]+" / "+recipe["palette"], 22/72,
         font_weight="700").set("fill", recipe["text"])
    orbital = bool(root.xpath('//*[@id="orbital-technosphere-metadata"]'))
    astronomy = bool(root.xpath('//*[@id="astro-metadata"]'))
    foreground_role = "type" if orbital or astronomy else "marks/type/fiber links"
    detail = (" Vendor markers retain source colors." if orbital else
              " Astronomy symbols retain source colors." if astronomy else " Fiber links use full opacity.")
    lines = [f'Randoma11y: ground {recipe["background"]}; {foreground_role} {recipe["text"]}. sRGB contrast {recipe["srgb_contrast_ratio"]:.2f}:1 (screen only).'+detail,
             recipe["source_url"],
             "Epson Stylus Pro 9000 / metallic glossy paper / cyan and light magenta reported low; grays reportedly print violet.",
             "Intended RGB hues; final printed hue is unmeasured. No green correction, ink separation or metallic reflection simulation."]
    y = 17.45
    for line in lines:
        for row in ORBITAL.wrapped(line, 14/72, 27):
            text(note, .8, y, row, 14/72).set("fill", recipe["text"])
            y += .27


def apply_palette(root, recipe, kind, preserve_orbital_colors=True):
    translations = {}
    astronomy = bool(root.xpath('//*[@id="astro-metadata"]'))
    backgrounds = ("st2-sheet-paper", "st2-image-background", "legend-paper")
    # Capability sheets already have semantic ground/land/foreground colors.
    # Preserve those roles when adopting the petal study in a different pair.
    original_recipe = root.xpath('//*[@id="msp-color-recipe"]')
    roles = {}
    if original_recipe:
        previous = json.loads(original_recipe[0].text)
        roles = {previous[key]: recipe[key] for key in ("background", "land", "text", "neutral", "halo")}
    def paint(value):
        return roles.get(value, adjusted(value, recipe))
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        tag = E.QName(node).localname
        if tag not in ("g", "path", "circle", "rect", "text", "line", "polygon", "polyline", "ellipse"):
            continue
        if astronomy and tag != "text" and node.get("id") not in backgrounds:
            continue
        # Categorical marker colors are data encoding. Keep their source RGB
        # values, including the companion legend keys, while recoloring type
        # and the ground. The debris pass below retains its black x and halo.
        if preserve_orbital_colors and node.get("data-display-group") and node.get("data-marker-shape"):
            continue
        current = style(node)
        for attr in ("fill", "stroke"):
            if node.get(attr):
                old = node.get(attr)
                node.set(attr, paint(old))
                translations[old] = node.get(attr)
            if attr in current:
                old = current[attr]
                current[attr] = paint(old)
                translations[old] = current[attr]
        if current:
            node.set("style", ";".join(k+":"+v for k, v in current.items()))
        if tag == "text":
            set_style(node, fill=recipe["text"], stroke="none", stroke_opacity=0)
        if node.get("id") in backgrounds:
            set_style(node, fill=recipe["background"], fill_opacity=1, stroke_opacity=0)
        if tag == "path" and any(a.get("id", "").startswith("terrestrial-land") for a in node.iterancestors()):
            set_style(node, fill=recipe["land"])
        if node.get("data-gateway-link") == "true" or node.get("data-role") == "gateway-link-key":
            set_style(node, stroke=recipe["text"], stroke_opacity=1)
    # Keep the requested black x visible against a dark field without recoloring it.
    debris = root.xpath('//*[@data-role="debris" and @data-marker-shape="x"]')
    halos = None
    for marker in debris:
        halo = copy.deepcopy(marker)
        halo.attrib.clear()
        halo.set("d", marker.get("d"))
        halo.set("data-presentation-only", "true")
        set_style(halo, fill="none", stroke=recipe["halo"], stroke_opacity=.95,
                  stroke_width=float(style(marker)["stroke-width"])*2.7)
        if kind == "map":
            if halos is None:
                outer = marker.getparent().getparent()
                halos = el("g", id="msp-debris-contrast", data_presentation_only="true")
                outer.getparent().insert(outer.getparent().index(outer), halos)
            halos.append(halo)
        else:
            marker.addprevious(halo)
        set_style(marker, fill_opacity=0, stroke="rgb(0,0,0)", stroke_opacity=1)
    palette_metadata(root, recipe)
    if preserve_orbital_colors and root.xpath('//*[@id="orbital-technosphere-metadata"]'):
        root.set("data-marker-color-policy", "preserve-source-groups")
    for metadata in root.xpath('//*[@id="groundstation-capability-metadata"]'):
        content = json.loads(metadata.text)
        content["palette"] = recipe
        metadata.text = json.dumps(content, sort_keys=True)
    if kind == "legend":
        print_note(root, recipe)
    return translations


def payload(root):
    records = []
    for node in root.iter():
        if not isinstance(node.tag, str) or node.get("data-presentation-only") == "true" or any(a.get("data-presentation-only") == "true" for a in node.iterancestors()):
            continue
        if E.QName(node).localname not in ("g", "path", "circle", "rect", "text", "line", "use", "polygon", "polyline", "ellipse"):
            continue
        attrs = {k: v for k, v in node.attrib.items() if k not in ("style", "fill", "stroke", "fill-opacity", "stroke-opacity", "stroke-width", "opacity")}
        records.append((node.tag, attrs, node.text if E.QName(node).localname == "text" else None))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT/"output/msp-speculations-20261103")
    parser.add_argument("--work", type=Path, default=ROOT/"build/msp-speculations-20261103")
    parser.add_argument("--capability-root", type=Path, default=ROOT/"output/groundstation-capabilities-20261103")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    register_fonts()
    config = json.loads(CONFIG.read_text())
    sources = prepare_sources(args.build_root, args.work)
    if any("astro-all-sky" in study_subjects(config, recipe) for recipe in config["studies"]):
        sources["astro-all-sky"] = astronomy_sources(
            ROOT/config["astronomy_source"], args.work, config["astronomy_label_font_size_pt"])
    capability = capability_sources(args.capability_root, args.work, "option-3-petals")
    env = font_environment()
    manifest_path = args.output/"manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    font_sha256 = digest(ROOT/"assets/fonts/atkinson-hyperlegible/provenance.json")
    cached = {(r["study"], r["subject"], r["kind"]): r for r in previous.get("records", [])}
    records = []
    jobs = []
    for recipe in config["studies"]:
        for subject in study_subjects(config, recipe):
            baseline = sources[subject]
            inputs = (capability if subject == "network-groundstations" and
                      recipe.get("variant", {}).get("groundstation_study") == "option-3-petals" else baseline)
            for kind in ("map", "legend"):
                source = inputs[kind]
                root = read_svg(source)
                variant = apply_variant(root, recipe, subject, kind)
                before = payload(root)
                translations = apply_palette(root, recipe, kind,
                                             config["orbital_marker_colors"] == "preserve-source-groups")
                assert payload(root) == before, "Color study changed source geometry, IDs, names or type"
                svg = args.work/recipe["id"]/"authagraph/svg"/source.name
                save(root, svg)
                jobs.append((recipe, subject, kind, svg, source, inputs, variant, translations))

    def export(job):
        recipe, subject, kind, svg, source, inputs, variant, translations = job
        result = {"study": recipe["id"], "subject": subject, "kind": kind,
                  "source_svg_sha256": digest(source), "svg_sha256": digest(svg),
                  "framing": inputs["framing"], "color_replacements": translations,
                  "layout_variant": variant, "capability_study": inputs.get("capability_study"),
                  "marker_color_policy": (config["orbital_marker_colors"] if subject.startswith("orbital") else
                                          config["astronomy_marker_colors"] if subject == "astro-all-sky" else "randoma11y-foreground"),
                  "palette_preserves_geometry_ids_names_and_type": True}
        prior = cached.get((recipe["id"], subject, kind))
        if (prior and prior["svg_sha256"] == digest(svg)
                and previous.get("font_sha256") == font_sha256
                and all((args.output/f["path"]).is_file()
                        and digest(args.output/f["path"]) == f["sha256"] for f in prior["outputs"])):
            print("Cached", recipe["id"], subject, kind, flush=True)
            return {**result, "outputs": prior["outputs"]}
        directory = args.output/study_directory(recipe)
        directory.mkdir(parents=True, exist_ok=True)
        pdf = directory/(svg.stem+".pdf")
        webp = directory/(svg.stem+".webp")
        compressed = directory/(svg.name+".gz")
        png = svg.with_suffix(".png")
        log = svg.with_suffix(".log")
        with log.open("w") as stream:
            for command in [
                ["inkscape", str(svg), "--export-area-page", "--export-filename="+str(pdf)],
                ["inkscape", str(svg), "--export-area-page", "--export-width=3840", "--export-filename="+str(png)],
            ]:
                subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
        with Image.open(png) as rendered:
            rendered.convert("RGB").save(webp, "WEBP", quality=92, method=6)
        with svg.open("rb") as stream, compressed.open("wb") as output:
            with gzip.GzipFile(fileobj=output, mode="wb", mtime=0, filename="") as archive:
                shutil.copyfileobj(stream, archive)
        outputs = [{"path": str(p.relative_to(args.output)), "sha256": digest(p), "bytes": p.stat().st_size} for p in (pdf, webp, compressed)]
        result["outputs"] = outputs
        print("Exported", recipe["id"], subject, kind, flush=True)
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(export, jobs))
    manifest = {"schema": "cartofreako-msp-delivery-v1", "configuration": config,
                "recipe_sha256": digest(CONFIG), "builder_sha256": digest(Path(__file__)),
                "framing_sha256": digest(ROOT/"scripts/setouchi_world_framing.py"),
                "palette_provenance_sha256": digest(ROOT/config["palette_provenance"]),
                "font_sha256": font_sha256,
                "inputs": {subject: {"path": str(v["input"].resolve().relative_to(ROOT)), "sha256": digest(v["input"])} for subject, v in sources.items()},
                "capability_input": {"study": capability["capability_study"],
                                     "manifest_path": str((args.capability_root/"manifest.json").resolve().relative_to(ROOT)),
                                     "manifest_sha256": capability["capability_manifest_sha256"],
                                     "evidence_path": str(capability["input"].resolve().relative_to(ROOT)),
                                     "evidence_sha256": digest(capability["input"])},
                "records": records}
    (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    (args.output/"color-recipes.json").write_text(json.dumps(config, indent=2)+"\n")
    (args.output/"palette-sources.json").write_bytes((ROOT/config["palette_provenance"]).read_bytes())
    (args.output/"index.html").write_text(review_page(config, config["studies"]))
    family = "msp-speculation-5"
    (args.output/family/"index.html").write_text(review_page(
        config, [r for r in config["studies"] if r.get("family") == family], family))
    print(f"Completed {len(records)} map/legend sheets: {args.output/family/'index.html'}")


def review_page(config, recipes, directory="."):
    """Render both the full comparison and a self-contained nested revision index."""
    root_link = posixpath.relpath(".", directory)+"/"
    cards = []
    for recipe in recipes:
        cards.append(f'<section id="{recipe["id"]}" style="--ground:{recipe["background"]};--ink:{recipe["text"]}"><h2>{recipe["title"]} · {recipe["palette"]}</h2>'
                     f'<p><a href="{recipe["source_url"]}">Randoma11y pair</a>: ground {recipe["background"]}, type and groundstation fiber lines {recipe["text"]}. '
                     'Orbital markers retain their vendor colors. '
                     f'Source sRGB contrast {recipe["srgb_contrast_ratio"]:.2f}:1; printed contrast and hue remain unmeasured.</p>')
        if recipe.get("variant"):
            cards.append('<p>Petal capability triangles on the groundstation map. Both orbital maps use 1.5× Starlink sunbursts; '
                         f'global Starlink IDs use {recipe["variant"]["global_starlink_font_size_pt"]} pt type beneath all satellite markers. '
                         'Antarctic land paints below labels and marks.</p>')
            if recipe["variant"].get("observer_starlink_names"):
                cards.append(f'<p>Observer Starlink names use {recipe["variant"]["observer_starlink_font_size_pt"]} pt type; other satellite names stay hidden. '
                             f'Global ground tracks use {recipe["variant"]["global_track_width_scale"]}× their original line width.</p>')
        if "astro-all-sky" in study_subjects(config, recipe):
            cards.append('<p>Astronomy all sky retains its 29 October 2026, 20:00 UTC source positions, symbol colors and 35 labels. '
                         f'Sky labels use {config["astronomy_label_font_size_pt"]} pt type on the full-size sheet. '
                         'Its background follows this color set, with light typography and a separate source legend.</p>')
        cards.append('<div class="plates">')
        for subject in study_subjects(config, recipe):
            stem = posixpath.relpath(study_directory(recipe), directory)+"/"+subject+SUFFIX
            title = "Astronomy / all sky" if subject == "astro-all-sky" else subject.replace("-", " ").title()
            cards.append(f'<article><h3>{title}</h3><a href="{stem}.webp"><img src="{stem}.webp" alt="{title} map" loading="lazy"></a>'
                         f'<p><a href="{stem}.pdf">Map PDF</a> · <a href="{stem}.svg.gz">Editable SVG (gzip)</a></p>'
                         f'<a href="{stem}-legend.webp"><img src="{stem}-legend.webp" alt="{title} legend and attribution" loading="lazy"></a>'
                         f'<p><a href="{stem}-legend.pdf">Legend PDF</a> · <a href="{stem}-legend.svg.gz">Legend SVG (gzip)</a></p></article>')
        cards.append('</div></section>')
    title = "MSP speculation 5" if directory != "." else "MSP print speculations"
    page = f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>'
    page += '<style>body{font:17px system-ui;background:#121119;color:#f5eae7;max-width:1600px;margin:auto;padding:32px}a{color:inherit}h1{font-size:40px}p{max-width:90ch;line-height:1.5}.plates{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px}article{border:1px solid currentColor;padding:16px}img{width:100%;height:auto}section{margin:48px 0;padding:24px;background:var(--ground);color:var(--ink)}nav{display:flex;gap:24px;flex-wrap:wrap}</style>'
    page += f'<h1>{title}</h1><p>MSP speculation 5 is available in all four Randoma11y pairs, each with groundstation, orbital global, orbital observer and astronomy all-sky map/legend companions. Orbital vendors and astronomy symbols retain their distinct source colors; the pairs control backgrounds, type and bright groundstation fiber lines.</p>'
    page += ('<p><a href="msp-speculation-5/index.html">Open MSP speculation 5 — all four nested color variations</a>. '
             'Studies 1–4 remain available below as the previous revisions.</p>' if directory == "." else
             '<p><a href="../index.html">All MSP studies, including the previous revisions</a>.</p>')
    page += '<p>Epson Stylus Pro 9000 on metallic glossy paper: cyan and light magenta are reported low, grays print violet, and dark backgrounds work better. These are intended RGB design choices, without a measured prediction of the printed hue.</p>'
    fourth_size = next(r["variant"]["global_starlink_font_size_pt"] for r in config["studies"] if r.get("family") == "msp-speculation-4")
    page += f'<p>Setouchi AuthaGraph framing: 43.5-inch image on a 44-inch sheet, +4.35-inch printed horizontal move and lower-left Antarctic land inset beneath terrestrial data. Each map has a separate legend with attribution. Global Starlink NORAD IDs print at {ORBITAL.STARLINK_LABEL_SIZE_PT} pt in studies 1–3 and {fourth_size} pt in every MSP 4 and MSP 5 palette.</p>'
    page += '<nav>'+''.join(f'<a href="#{r["id"]}">{r["title"]}</a>' for r in recipes)+'</nav>'
    page += f'<p><a href="{root_link}color-recipes.json">Color recipes</a> · <a href="{root_link}palette-sources.json">Randoma11y provenance</a> · <a href="{root_link}manifest.json">Sources and output checksums</a> · <a href="{root_link}../groundstation-capabilities-20261103/capability-evidence.json">Capability source fields and placement</a> · <a href="{root_link}../../assets.static/astronomy/msp-setouchi-20261029/provenance.json">Astronomy source receipt</a></p>'+''.join(cards)+'</html>'
    return page


if __name__ == "__main__":
    main()

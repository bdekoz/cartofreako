#!/usr/bin/env python3
"""Build three documented metallic-paper color studies in the Setouchi frame."""

import argparse
import colorsys
from concurrent.futures import ThreadPoolExecutor
import copy
import gzip
import importlib
import json
from pathlib import Path
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
    el("path", key, d="M 41.96 2.65 L 42.32 2.65", style="fill:none;stroke:rgb(255,29,16);stroke-width:0.0115;stroke-opacity:0.45")
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


def rgb(value):
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))
    match = re.fullmatch(r"rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)", value)
    return tuple(map(int, match.groups())) if match else None


def adjusted(value, recipe):
    original = rgb(value)
    if original is None or max(original) < 5:
        return value
    if max(original)-min(original) < 15:
        return recipe["neutral"]
    c, m, y = (1-v/255 for v in original)
    k = min(c, m, y)
    c = min(1, k+(c-k)*(1+recipe["cyan_emphasis"]))
    m = k+(m-k)*(1-recipe["magenta_reduction"])
    hue, light, saturation = colorsys.rgb_to_hls(1-c, 1-m, 1-y)
    result = colorsys.hls_to_rgb(hue, max(light, recipe["foreground_lightness_floor"]),
                                saturation*recipe["saturation_factor"])
    return "#"+"".join(f"{round(channel*255):02x}" for channel in result)


def apply_palette(root, recipe, kind):
    translations = {}
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        tag = E.QName(node).localname
        if tag not in ("g", "path", "circle", "rect", "text", "line", "polygon", "polyline", "ellipse"):
            continue
        current = style(node)
        for attr in ("fill", "stroke"):
            if node.get(attr):
                old = node.get(attr)
                node.set(attr, adjusted(old, recipe))
                translations[old] = node.get(attr)
            if attr in current:
                old = current[attr]
                current[attr] = adjusted(old, recipe)
                translations[old] = current[attr]
        if current:
            node.set("style", ";".join(k+":"+v for k, v in current.items()))
        if tag == "text":
            set_style(node, fill=recipe["text"], stroke="none", stroke_opacity=0)
        if node.get("id") in ("st2-sheet-paper", "st2-image-background", "legend-paper"):
            set_style(node, fill=recipe["background"], fill_opacity=1, stroke_opacity=0)
        if tag == "path" and any(a.get("id", "").startswith("terrestrial-land") for a in node.iterancestors()):
            set_style(node, fill=recipe["land"])
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
    root.set("data-color-study", recipe["title"])
    el("metadata", root, id="msp-color-recipe").text = json.dumps(recipe, sort_keys=True)
    if kind == "legend":
        note = el("g", root, id="msp-print-note", data_presentation_only="true")
        text(note, .8, 17.0, recipe["title"]+" / "+recipe["palette"], 22/72, font_weight="700").set("fill", recipe["text"])
        lines = ["Metallic glossy paper / Epson Stylus Pro 9000 / cyan and light magenta reported low.",
                 "Green-biased neutrals respond to the reported violet gray cast. Dark backgrounds follow the supplied print observation.",
                 "Unmeasured color study. The saved recipe does not predict ink-channel output or simulate metallic reflection."]
        y = 17.45
        for line in lines:
            for row in ORBITAL.wrapped(line, 14/72, 27):
                text(note, .8, y, row, 14/72).set("fill", recipe["text"])
                y += .27
    return translations


def payload(root):
    records = []
    for node in root.iter():
        if not isinstance(node.tag, str) or node.get("data-presentation-only") == "true" or any(a.get("data-presentation-only") == "true" for a in node.iterancestors()):
            continue
        if E.QName(node).localname not in ("g", "path", "circle", "rect", "text", "line", "use"):
            continue
        attrs = {k: v for k, v in node.attrib.items() if k not in ("style", "fill", "stroke", "fill-opacity", "stroke-opacity", "stroke-width", "opacity")}
        records.append((node.tag, attrs, node.text if E.QName(node).localname == "text" else None))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT/"output/msp-speculations-20261103")
    parser.add_argument("--work", type=Path, default=ROOT/"build/msp-speculations-20261103")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    register_fonts()
    config = json.loads(CONFIG.read_text())
    sources = prepare_sources(args.build_root, args.work)
    env = font_environment()
    manifest_path = args.output/"manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    font_sha256 = digest(ROOT/"assets/fonts/atkinson-hyperlegible/provenance.json")
    cached = {(r["study"], r["subject"], r["kind"]): r for r in previous.get("records", [])}
    records = []
    jobs = []
    for recipe in config["studies"]:
        for subject, inputs in sources.items():
            for kind in ("map", "legend"):
                source = inputs[kind]
                root = read_svg(source)
                before = payload(root)
                translations = apply_palette(root, recipe, kind)
                assert payload(root) == before, "Color study changed source geometry, IDs, names or type"
                svg = args.work/recipe["id"]/"authagraph/svg"/source.name
                save(root, svg)
                jobs.append((recipe, subject, kind, svg, source, translations))

    def export(job):
        recipe, subject, kind, svg, source, translations = job
        prior = cached.get((recipe["id"], subject, kind))
        if (prior and prior["svg_sha256"] == digest(svg)
                and previous.get("font_sha256") == font_sha256
                and all((args.output/f["path"]).is_file()
                        and digest(args.output/f["path"]) == f["sha256"] for f in prior["outputs"])):
            print("Cached", recipe["id"], subject, kind, flush=True)
            return prior
        directory = args.output/recipe["id"]
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
        result = {"study": recipe["id"], "subject": subject, "kind": kind,
                  "source_svg_sha256": digest(source), "svg_sha256": digest(svg),
                  "framing": sources[subject]["framing"], "color_replacements": translations,
                  "geometry_ids_names_and_type_preserved": True, "outputs": outputs}
        print("Exported", recipe["id"], subject, kind, flush=True)
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(export, jobs))
    manifest = {"schema": "cartofreako-msp-delivery-v1", "configuration": config,
                "recipe_sha256": digest(CONFIG), "builder_sha256": digest(Path(__file__)),
                "font_sha256": font_sha256,
                "inputs": {subject: {"path": str(v["input"].resolve().relative_to(ROOT)), "sha256": digest(v["input"])} for subject, v in sources.items()},
                "records": records}
    (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    (args.output/"color-recipes.json").write_text(json.dumps(config, indent=2)+"\n")
    cards = []
    for recipe in config["studies"]:
        cards.append(f'<section id="{recipe["id"]}"><h2>{recipe["title"]} · {recipe["palette"]}</h2><div class="plates">')
        for subject in config["subjects"]:
            stem = recipe["id"]+"/"+subject+SUFFIX
            title = subject.replace("-", " ").title()
            cards.append(f'<article><h3>{title}</h3><a href="{stem}.webp"><img src="{stem}.webp" alt="{title} map" loading="lazy"></a>'
                         f'<p><a href="{stem}.pdf">Map PDF</a> · <a href="{stem}.svg.gz">Editable SVG (gzip)</a></p>'
                         f'<a href="{stem}-legend.webp"><img src="{stem}-legend.webp" alt="{title} legend and attribution" loading="lazy"></a>'
                         f'<p><a href="{stem}-legend.pdf">Legend PDF</a> · <a href="{stem}-legend.svg.gz">Legend SVG (gzip)</a></p></article>')
        cards.append('</div></section>')
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MSP print speculations</title>'
    page += '<style>body{font:17px system-ui;background:#17231c;color:#e5eadc;max-width:1600px;margin:auto;padding:32px}a{color:#c5d99a}h1{font-size:40px}p{max-width:90ch;line-height:1.5}.plates{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px}article{border:1px solid #71816a;padding:16px}img{width:100%;height:auto}section{margin:48px 0}nav{display:flex;gap:24px;flex-wrap:wrap}</style>'
    page += '<h1>MSP print speculations</h1><p>Three studies for the Epson Stylus Pro 9000 on metallic glossy paper, responding to reported low cyan/light magenta, a violet cast in grays, and stronger results with dark backgrounds. These are unmeasured color hypotheses.</p>'
    page += f'<p>Setouchi AuthaGraph framing: 43.5-inch image on a 44-inch sheet, +4.35-inch printed horizontal move and lower-left Antarctic land inset. Each map has a separate legend with attribution. Global Starlink NORAD IDs print at {ORBITAL.STARLINK_LABEL_SIZE_PT} pt.</p>'
    page += '<nav>'+''.join(f'<a href="#{r["id"]}">{r["title"]}</a>' for r in config['studies'])+'</nav>'
    page += '<p><a href="color-recipes.json">Color recipes</a> · <a href="manifest.json">Sources and output checksums</a></p>'+''.join(cards)+'</html>'
    (args.output/"index.html").write_text(page)
    print(f"Completed {len(records)} map/legend sheets: {args.output/'index.html'}")


if __name__ == "__main__":
    main()

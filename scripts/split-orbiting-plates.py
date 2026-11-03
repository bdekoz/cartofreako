#!/usr/bin/env python3
"""Compose paired orbital map and Setouchi-style legend/attribution plates."""

import argparse
import copy
import importlib
import json
from pathlib import Path

from cartofreako_style import STYLE
from legend_informatics import E, NS, ROOT, XL, digest, el, register_fonts, save, text

LAYOUT = importlib.import_module("revise-setouchi-plates")
SITE = "https://bdekoz.github.io/cartofreako"
REPO = "https://github.com/bdekoz/cartofreako/blob/main/"
INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"
STARLINK_LABEL_SIZE_PT = 9


def wrapped(value, size, width, role="Regular"):
    # Provider and receipt URLs must fit as well as ordinary prose.
    words = []
    for word in value.split():
        while LAYOUT.width_in(word, size, role) > width:
            cut = 1
            while cut < len(word) and LAYOUT.width_in(word[:cut+1], size, role) <= width:
                cut += 1
            words.append(word[:cut])
            word = word[cut:]
        if word:
            words.append(word)
    return LAYOUT.wrap(" ".join(words), size, width, role)


def source_blocks(profile, metadata, projection):
    catalogs = [profile["catalogs"]["primary"], *profile["catalogs"]["groups"]]
    nasa = profile["catalogs"]["nasa_ssc_reference"]
    blocks = [
        ("01  CelesTrak / orbital elements and memberships", [
            f"{len(catalogs)} OMM CSV catalogs. Collected "
            f"{profile['snapshot']['collection_started_at']} to "
            f"{profile['snapshot']['collection_completed_at']}.",
            "Active catalog supplies the satellite population; membership catalogs "
            "identify named fleets. Three bounded debris catalogs supplement it.",
            "Catalogs: " + ", ".join(g["id"] for g in catalogs) + ".",
            "Attribution: CelesTrak. Exact feed URLs, element epochs and hashes are retained in the source ledger.",
        ], "https://celestrak.org/NORAD/documentation/gp-data-formats.php"),
        ("02  SGP4 / Vallado, Crawford, Hujsak and Kelso", [
            "Positions propagated from the pinned elements using the reference SGP4 implementation, WGS-72 and AFSPC mode.",
            f"Calculation instant: {profile['timestamp']}. "
            f"{metadata['data-skipped-stale']} records excluded by epoch; "
            f"{metadata['data-failed-propagation']} propagation failures.",
            "Public element uncertainty and approximate Earth rotation limit these visualization positions.",
        ], "https://celestrak.org/publications/AIAA/2006-6753/"),
    ]
    if metadata["data-product"] == "global":
        blocks.append(("03  Natural Earth / terrestrial context", [
            "Natural Earth 1:10m physical land provides the subdued geographic background.",
            "Attribution: Natural Earth. Public-domain cartographic data.",
        ], "https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-land/"))
    blocks.extend([
        ("Historical validation / NASA SSCWeb", [
            "Reference instant: " + nasa.get("reference_timestamp", "historical snapshot") + ".",
            "Historical regression reference only. The November refresh was unreachable; "
            "this response does not provide an independent comparison of the plotted November positions.",
        ], nasa["source_url"]),
        ("Cartography / Cartofreako", [
            "Projection: " + projection.replace("-", " ").title() + ". "
            "The projection bibliography credits its mathematical and design sources.",
            "Separate map and legend composition follows the Setouchi ST2 layout. "
            "Typography: Atkinson Hyperlegible; bundled fonts under the SIL Open Font License.",
        ], SITE + f"/docs/pages/projections/{projection}/bibliography.html"),
    ])
    return blocks


def legend_plate(source, profile, profile_path, map_path, projection):
    width, height = map(float, source.get("viewBox").split()[2:])
    metadata_node = source.find(f"{{{NS}}}metadata[@id='orbital-technosphere-metadata']")
    metadata = dict(metadata_node.attrib)
    product = metadata["data-product"]
    root = el("svg", width=f"{width}in", height=f"{height}in",
              viewBox=f"0 0 {width} {height}", role="img", data_sheet_kind="legend",
              data_legend_style="setouchi-st2", data_map_companion=map_path.name)
    el("title", root).text = f"Orbital Technosphere / {product} / {projection} / legend and attribution"
    root.append(copy.deepcopy(metadata_node))
    acquisition = profile_path.parent / profile["snapshot"]["receipt_file"]
    ledger = {
        "profile": str(profile_path.resolve().relative_to(ROOT)),
        "profile_sha256": digest(profile_path),
        "acquisition_sha256": digest(acquisition),
        "snapshot_sha256": digest(profile_path.parent / profile["snapshot"]["checksum_file"]),
        "generation_style_sha256": digest(ROOT / "generation-style.json"),
        "calculation_timestamp": profile["timestamp"],
        "acquisition": json.loads(acquisition.read_text()),
    }
    el("metadata", root, id="orbital-source-ledger").text = json.dumps(ledger, sort_keys=True)
    el("rect", root, id="legend-paper", width=width, height=height, fill="white")
    key = el("g", root, id="constellation-legend", data_legend_style="setouchi-st2")
    titles = ["Orbital technosphere", product.title() + " / " + projection.replace("-", " ").title()]
    title_size = min(56/72, (height-1) / max(LAYOUT.width_in(s, 1, "Bold") for s in titles))
    for index, line in enumerate(titles):
        text(key, .4, -(width-.58)+index*.63, line, title_size,
             font_weight="700", transform="rotate(90)", dominant_baseline="central")
    right = width-1.62
    y = .5
    for value, size, role in [
        ("SGP4 positions / " + profile["timestamp"], 24/72, "Bold"),
        (f"{int(metadata['data-visible-records']):,} plotted objects / named fleets and residual roles", 16/72, "Regular"),
        ("Seven-day element age; six-hour future tolerance.", 12/72, "Italic"),
    ]:
        for line in wrapped(value, size, 12.2, role):
            text(key, right, y, line, size, text_anchor="end",
                 font_weight="700" if role == "Bold" else "400",
                 font_style="italic" if role == "Italic" else "normal")
            y += size*1.6
    y = max(y+.3, 2.0)
    original = source.find(f"{{{NS}}}g[@id='constellation-legend']")
    if original is None:
        raise ValueError("A named-profile constellation legend is required")
    children = list(original)
    for index, symbol in enumerate(children):
        if not symbol.get("data-marker-shape"):
            continue
        label = "".join(children[index+1].itertext()).strip()
        text(key, right-.68, y, label, 18/72, text_anchor="end", dominant_baseline="central")
        x0, y0, x1, y1 = LAYOUT.shape_bounds(symbol)
        scale = min(.4/max(x1-x0, .001), .24/max(y1-y0, .001))
        icon = el("g", key, transform=f"translate({right-.24} {y}) scale({scale}) translate({-(x0+x1)/2} {-(y0+y1)/2})")
        icon.append(copy.deepcopy(symbol))
        y += .32
    y += .35
    notes = [
        "One object per NORAD ID. Overlapping named memberships use profile order.",
        (f"Starlink NORAD IDs are visible at {STARLINK_LABEL_SIZE_PT} pt in a separate id layer. All name layers are hidden."
         if product == "global" else "Name and locpoint sublayers are independent. Names are hidden by default."),
        "Black x: debris. Sunburst: Starlink. Square: Intelsat. Triangle: remaining Earth observation.",
        "Active-marker opacity records illumination. Debris remains solid black.",
        ("Terrestrial subpoints; bounded representative ground tracks; reference site marked."
         if product == "global" else
         "Topocentric celestial directions above the San Francisco horizon. Equator and horizon are reference lines."),
    ]
    for note in notes:
        for line in wrapped(note, 14/72, 11.8):
            text(key, right, y, line, 14/72, text_anchor="end")
            y += .28
        y += .1
    if y > height-.8:
        raise ValueError("Orbital legend exceeds the sheet")
    number = STYLE["atlas"]["plate_number"]
    footer = text(key, right, height-.5, "01" if product == "global" else "02",
                  number["size_pt"]/72, id="plate-number", text_anchor="end",
                  font_weight=number["weight"], stroke=number["stroke"],
                  stroke_width=number["stroke_width_pt"]/72, opacity=number["opacity"])
    footer.set("fill", number["fill"])
    panel = el("g", root, id="plate-source-bibliography")
    text(panel, .8, .8, "Data bibliography / attribution", 28/72, font_weight="700")
    text(panel, .8, 1.3, f"Orbital Technosphere / {product.title()}", 22/72, font_weight="700")
    left_width = width-15.4
    column_width = (left_width-1.2)/2
    columns = [.8, .8+column_width+.6]
    column, y = 0, 2.0
    blocks = source_blocks(profile, metadata, projection)
    profile_url = REPO + str(profile_path.resolve().relative_to(ROOT))
    blocks.append(("Pinned inputs / source ledger", [
        "The profile records the calculation time, observer, filters and every catalog URL. "
        "Adjacent acquisition.json and SHA256SUMS record retrievals and original input bytes.",
        "Map and legend carry the same timestamp and counts; the complete acquisition ledger is embedded in this SVG.",
        f"Map image scaled to {STYLE['atlas']['image_width_inches']/44*100:.6f}% with proportional white margins.",
    ], profile_url))
    for title, paragraphs, url in blocks:
        rows = [(line, 20/72, "700") for line in wrapped(title, 20/72, column_width, "Bold")]
        for paragraph in [*paragraphs, url]:
            rows += [(line, 18/72, "400") for line in wrapped(paragraph, 18/72, column_width)]
        if y + len(rows)*.34 + .4 > height-.8:
            column += 1
            y = 2.0
        if column >= len(columns):
            raise ValueError("Orbital bibliography exceeds the sheet")
        block = el("g", panel)
        for line, size, weight in rows:
            text(block, columns[column], y, line, size, font_weight=weight)
            y += .34
        # A clickable source area includes its exact printed URL.
        link = el("a", block)
        link.set("{"+XL+"}href", url)
        for child in list(block)[:-1]:
            link.append(child)
        y += .4
    return root


def split(source_path, map_path, profile_path):
    profile = json.loads(profile_path.read_text())
    parser = E.XMLParser(remove_blank_text=False, huge_tree=True)
    source = E.parse(str(source_path), parser).getroot()
    projection = map_path.parent.parent.name
    legend_path = map_path.with_name(map_path.stem+"-legend.svg")
    legend = legend_plate(source, profile, profile_path, map_path, projection)
    width, height = map(float, source.get("viewBox").split()[2:])
    source.set("data-sheet-kind", "map")
    source.set("data-legend-style", "separate-sheet")
    source.set("data-legend-companion", legend_path.name)
    scale = STYLE["atlas"]["image_width_inches"]/44
    source.set("data-image-scale", str(scale))
    metadata = source.find(f"{{{NS}}}metadata[@id='orbital-technosphere-metadata']")
    if metadata.get("data-product") == "global":
        starlink = source.find(f"{{{NS}}}g[@id='starlink']")
        ids = el("g", starlink, id="starlink-id", data_font_size_pt=STARLINK_LABEL_SIZE_PT)
        ids.set("{"+INKSCAPE+"}groupmode", "layer")
        ids.set("{"+INKSCAPE+"}label", "id")
        for name in starlink.find(f"{{{NS}}}g[@id='starlink-name']"):
            name.set("font-size", str(STARLINK_LABEL_SIZE_PT/72/scale))
            label = copy.deepcopy(name)
            label.set("id", "id-norad-"+label.get("data-norad-id"))
            label.set("data-object-kind", "id")
            # Unitless SVG size is in sheet inches; compensate for map framing.
            label.set("font-size", str(STARLINK_LABEL_SIZE_PT/72/scale))
            label.text = label.get("data-norad-id")
            ids.append(label)
    frame = el("g", id="orbital-image-frame",
               transform=f"translate({width*(1-scale)/2} {height*(1-scale)/2}) scale({scale})")
    for child in list(source):
        if child.get("id") == "constellation-legend":
            source.remove(child)
        elif E.QName(child).localname not in ("title", "desc", "metadata", "defs"):
            frame.append(child)
    paper = el("rect", id="orbital-sheet-paper", width=width, height=height, fill="white")
    source.append(paper)
    source.append(frame)
    save(legend, legend_path)
    save(source, map_path)
    print(f"Separated {map_path.name} and {legend_path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    register_fonts()
    split(args.source, args.map, args.profile)


if __name__ == "__main__":
    main()

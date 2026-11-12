#!/usr/bin/env python3
"""Compose fresh dataset-bound cartography with the reviewed atlas framing."""
from copy import deepcopy
import csv
import gzip
from html import escape
import importlib
import io
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import xml.sax
from xml.sax.saxutils import XMLGenerator

from lxml import etree as E

from dataset import ROOT, DatasetError, atomic_json, binding, context, digest, output
from atlas_presentation import settings, Theme
from atlas_presentation import css, paint
import atlas_groundstations as GROUNDSTATIONS
import atlas_world as WORLD
from cartofreako_style import STYLE, Projection
from legend_informatics import WIDTH, HEIGHT, SUFFIX, font_environment, legend_group, register_fonts
from atlas_review_sheets import el, legend, save

FRAMING = importlib.import_module("setouchi_world_framing")
REVISED = importlib.import_module("revise-setouchi-plates")
MSP = importlib.import_module('build-msp-speculations')


class CurrentAtlasTheme(Theme):
    def startElement(self, name, attrs):
        if name == 'rect' and attrs.get('id') == 'resource-legend-panel':
            attrs = dict(attrs)
            paint(attrs, fill=self.recipe['background'], fill_opacity=1, stroke_opacity=0)
        super().startElement(name, attrs)


def current_theme(source, destination, recipe, kind, subject=None, attributes=None):
    """Theme current sheets without recoloring resource data swatches."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w') as stream:
        xml.sax.parse(str(source), CurrentAtlasTheme(stream, recipe, kind, subject, attributes))


class JapanDefinitions(xml.sax.ContentHandler):
    """Expose the streamed geographic viewport to the H3 tile renderer."""
    def __init__(self, stream):
        self.writer = XMLGenerator(stream, encoding="utf-8")
        self.stack = []
        self.wrapped = None

    def startDocument(self):
        self.writer.startDocument()

    def startElement(self, name, attrs):
        attrs = dict(attrs)
        if not self.stack:
            attrs["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
        self.writer.startElement(name, attrs)
        if name == "g" and self.stack and self.stack[-1].get("clip-path") == "url(#japan-detail-viewport)":
            self.wrapped = len(self.stack)
            self.writer.startElement("defs", {})
            self.writer.startElement("g", {"id": "source-content"})
        self.stack.append(attrs)

    def endElement(self, name):
        self.stack.pop()
        if self.wrapped is not None and len(self.stack) == self.wrapped:
            self.writer.endElement("g")
            self.writer.endElement("defs")
            self.writer.startElement("use", {"xlink:href": "#source-content"})
            self.writer.endElement("use")
            self.wrapped = None
        self.writer.endElement(name)

    def characters(self, text):
        self.writer.characters(text)


def resolve_catalog_sources(catalog, resource_profile=None):
    """Resolve dated resource filenames from the selected metric definitions."""
    requested = [p for p in catalog if p['source_stem'].startswith('resources-')
                 and p['id'] != 'resources-mineral-mine-production-comparison']
    if requested and resource_profile is None:
        resource_profile = binding('RESOURCES_DATA_DIR')/'resources-profile.json'
    profile = json.loads(resource_profile.read_text()) if requested else None
    resolved = []
    for original in catalog:
        plate = dict(original)
        if original in requested:
            stem = original['source_stem']
            exact, compatible = [], []
            for family in profile['families']:
                for metric in family['metrics']:
                    tag = metric.get('output_tag')
                    if not tag or metric.get('status') not in ('default', 'released'):
                        continue
                    canonical = ('anthropocene' if metric['id'] == 'coral-reef-threat'
                                 else family['id']) + '-' + tag
                    if stem in (canonical, family['id']+'-'+tag):
                        exact.append((canonical, metric))
                    elif stem.startswith(family['id']+'-'+metric['id']+'-'):
                        compatible.append((canonical, metric))
            candidates = exact or compatible
            if len(candidates) != 1:
                raise DatasetError('Atlas resource source is missing or ambiguous in the selected profile: ' + stem)
            canonical, metric = candidates[0]
            plate.update(catalog_source_stem=stem, source_stem=canonical,
                         source_reference_period=metric['reference_period'])
        resolved.append(plate)
    return resolved


def native_source(native, plate):
    stem = plate["source_stem"]
    stem = stem.replace("anthropocene-temperature-", "anthropocene-land-temperature-")
    if stem == "network-swarm-ge-1080p":
        stem = "network-swarm"
    matches = list((native / "authagraph/svg").glob(stem + SUFFIX + ".svg*"))
    matches = [p for p in matches if p.name.endswith((".svg", ".svg.gz"))]
    if not matches:
        raise DatasetError("No fresh native source for atlas product: " + plate["id"])
    return matches[0]


def native_path(native, plate):
    path = native_source(native, plate)
    if path.suffix == ".gz":
        target = native / "atlas-sources" / path.stem
        target.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "rb") as source, target.open("wb") as stream:
            shutil.copyfileobj(source, stream)
        return target
    return path


def standalone_legend(plate, source, destination, dataset, scope, all_sources):
    special = special_legend(plate, dataset, scope)
    if special is not None:
        special.set("data-dataset-id", dataset["dataset_id"])
        save(special, destination)
        return
    group = REVISED.old_legend(source)
    companion = source.with_name(source.stem + "-legend.svg")
    if group is None and companion.is_file():
        group = REVISED.old_legend(companion)
    if group is not None:
        # Preserve native units and class intervals. The source note is
        # regenerated from the selected manifest rather than an old legend.
        sheet = el("svg", width="44in", height=f"{HEIGHT}in", viewBox=f"0 0 44 {HEIGHT}",
                   data_canonical_plate_id=plate["id"], data_sheet_kind="legend")
        el("rect", sheet, width=44, height=HEIGHT, fill="#240413")
        group=deepcopy(group)
        sheet.append(group)
        sheet.set("data-dataset-id", dataset["dataset_id"])
        # Native legends can use projection coordinates; query the group
        # bounds once and fit it to the separate sheet without changing keys.
        group.set("id", "current-source-legend")
        temporary = destination.with_name(destination.stem + ".source.svg")
        save(sheet, temporary)
        result = subprocess.run(["bash", str(ROOT / "scripts/run-inkscape.sh"), "inkscape", str(temporary),
                                 "--query-id=current-source-legend", "--query-x", "--query-y",
                                 "--query-width", "--query-height"], capture_output=True, text=True, check=True)
        # Activated desktop services can print environment assignments to the
        # isolated D-Bus session's stdout. Only complete numeric query lines
        # belong to Inkscape's four-value geometry protocol.
        numbers=[float(line.strip())/96 for line in result.stdout.splitlines()
                 if re.fullmatch(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',line.strip())]
        if len(numbers) != 4:
            raise DatasetError('Inkscape did not return four legend bounds')
        x,y,width,height=numbers
        scale = min(41 / max(width, .001), 13.5 / max(height, .001))
        sheet.remove(sheet[-1])
        wrapper = el("g", sheet, transform=f"translate(1.3 2.5) scale({scale}) translate({-x} {-y})")
        wrapper.append(group)
        title = el("text", sheet, x="1", y="1.2", fill="#fcc553", font_size=".45", font_family="Atkinson Hyperlegible")
        title.text = plate["title"] + " / " + scope
        note = el("text", sheet, x="1", y="17.2", fill="#fcc553", font_size=".24", font_family="Atkinson Hyperlegible")
        note.text = "Dataset " + dataset["dataset_id"] + "; exact source periods and hashes: sources/dataset.json"
        themed = destination.with_name(destination.stem + ".theme.svg")
        save(sheet, themed)
        _, recipe = settings(STYLE)
        current_theme(themed, destination, recipe, "legend")
        themed.unlink()
        temporary.unlink()
    else:
        sheet = legend(plate["id"], plate["title"], scope.title() + " / dataset " + dataset["dataset_id"], [],
                       ["See the accompanying dataset manifest for source-specific observation periods and pinned local input versions.",
                        "Missing observations remain missing. A dataset update does not make pinned historical inputs current observations."],
                       ["Dataset manifest: sources/dataset.json"])
        sheet.set("data-dataset-id", dataset["dataset_id"])
        save(sheet, destination)


def special_legend(plate, dataset, scope):
    stem = plate["source_stem"]
    if stem == "cloud-atmosphere":
        profile = json.loads(binding("ATLAS_CLOUD_PROFILE").read_text())
        snapshot = json.loads(binding("ATLAS_CLOUD_GEOJSON").read_text())["metadata"]
        return legend(plate["id"], plate["title"], "H3 resolution 5 / " + scope.title(), [
            {"title": "Cloud fraction", "keys": list(zip(STYLE["atmosphere"]["cloud_colors"],
                ["0 to <1/6", "1/6 to <2/6", "2/6 to <3/6", "3/6 to <4/6", "4/6 to <5/6", "5/6 to 1"])),
             "notes": ["An observed zero has no cloud paint. Missing retrievals are not clear sky."]},
            {"title": "Shortwave radiation / W m-2", "notes": [
                "100 nearest linear opacity levels from 0 to 400 W m-2, with opacity from 0 to 1. Values outside that domain are clamped.",
                "Actual H3 cell boundaries; no interpolation or source-pixel footprint filling."]},
            {"title": "Other layer scales", "notes": [
                f"{layer['title']}: {layer['scale_min']:g} to {layer['scale_max']:g} {layer['unit']}; six source bins."
                for layer in profile["layers"] if layer.get("enabled") and layer["id"] not in ("cloud-fraction", "surface-shortwave-radiation")]}],
            ["Maximum 720 samples per raster axis; quality masks and source-specific observation intervals remain in the input ledger.",
             "White outlines show terrestrial context above observations. Amber background is presentation; it is not an observation."],
            ["JAXA source definitions and actual observation periods: sources/dataset.json",
             "Prepared snapshot SHA-256: " + digest(binding("ATLAS_CLOUD_GEOJSON"))])
    if stem.startswith("petroleum-"):
        if "coverage" in stem:
            keys = [("#865a3d", "Country figures indexed"), ("#d6d6d2", "No separate country figure"),
                    ("#f0ece6", "Not matched to report register")]
            units = "Country source coverage / World Oil Outlook 2026"
            notes = ["Coverage categories, not production quantities. Regional totals are not allocated to countries."]
        else:
            keys = list(zip(["#fff0c8", "#c59225", "#ca6924", "#865a3d", "#7d4e2d", "#800505", "#51372a"],
                            ["≤0.1", ">0.1 to 0.5", ">0.5 to 1", ">1 to 2", ">2 to 5", ">5 to 10", ">10 to 25"]))
            keys.append(("#d6d6d2", "No separate reported value; not zero"))
            units = "Million barrels/day / " + ("2030 projection" if "projection" in stem else "2025 historical/estimate")
            notes = ["Fixed upper-inclusive thresholds; values above 25 use the highest class.",
                     "Total liquids include NGLs, other liquids and processing gain; not crude-only production or refinery throughput."]
        return legend(plate["id"], plate["title"], units + " / " + scope.title(),
                      [{"title": units, "keys": keys}], notes,
                      ["US EIA October 2026 STEO / https://www.eia.gov/outlooks/steo/data.php?type=tables" if "eia" in stem
                       else "OPEC World Oil Outlook 2026 / https://publications.opec.org/woo",
                       "Pinned audited releases; input hashes and source register: sources/dataset.json"])
    if plate["id"] == "resources-mineral-mine-production-comparison":
        resources = binding("RESOURCES_DATA_DIR")
        profile = json.loads((resources / "resources-profile.json").read_text())
        rows = json.loads((resources / "resources-values.json").read_text())["records"]
        metrics = {m["id"]: m for f in profile["families"] for m in f["metrics"]}
        sections = []
        for metric, kind in (("rare-earth-mine-production", "rare-earth"), ("lithium-mine-production", "lithium"),
                             ("uranium-mine-production", "uranium")):
            selected = [r for r in rows if r["metric"] == metric]
            style = STYLE["resources"]["mineral_types"][kind]
            m = metrics[metric]
            sections.append({"title": kind.title() + " / " + m["reference_period"],
                             "keys": [(style["color"], style["shape"].title(), style["shape"])],
                             "notes": [m["unit"], f"Largest symbol: {max(r['value'] for r in selected):,}.", m["notes"]]})
        return legend(plate["id"], plate["title"], "Independent commodity scales / " + scope.title(), sections,
                      ["Symbol area is proportional to production within each mineral, independently normalized. Do not compare areas across mineral types.",
                       "Country representative points are not mine locations. Missing or withheld values remain missing; reference years and source units differ."],
                      [s["title"] + " / " + s["url"] for s in profile["sources"] if s["id"] in
                       {i for key in ("rare-earth-mine-production", "lithium-mine-production", "uranium-mine-production") for i in metrics[key]["source_ids"]}])
    return None


def petroleum_native(plate, work):
    """Render audited tabular releases; never substitute a retained SVG."""
    import numpy as np
    from shapely.geometry import shape
    projection = Projection("authagraph", work / "projection")
    root = projection.base(plate["title"], "Audited petroleum source release; observations and projections remain separate")
    data = binding("PETROLEUM_DATA") / "normalized"
    stem = plate["source_stem"]
    filename = "eia-series.csv" if "eia" in stem else "opec-country-coverage.csv" if "coverage" in stem else "opec-liquids-supply.csv"
    with (data / filename).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if "coverage" in stem:
        values = {r["iso3"]: int(r["numeric_country_cells"]) for r in rows}
    elif "eia" in stem:
        values = {r["iso3"]: float(r["value"]) for r in rows if r["iso3"] and r["period"] == "2025"
                  and r["table"] in ("3b", "3c") and r["value"] and r["metric"] == "petroleum-and-other-liquid-fuels-production"}
    else:
        values = {r["iso3"]: float(r["value"]) for r in rows if r["period"] == "2030"}
    geometry = json.loads((binding("RESOURCES_DATA_DIR") / "countries-110m.geojson").read_text())
    # Retain the audited petroleum scale; unlike resource choropleths these
    # are seven fixed production classes, never edition-relative log bins.
    bounds = [.1, .5, 1, 2, 5, 10, 25]
    colors = ["#fff0c8", "#c59225", "#ca6924", "#865a3d", "#7d4e2d", "#800505", "#51372a"]
    if not values or any(not math.isfinite(v) or v < 0 for v in values.values()):
        raise DatasetError("Invalid audited petroleum values")
    layer = el("g", root, id="petroleum-country-geometry")
    mapped=set()
    for feature in geometry["features"]:
        code = feature["properties"]["RESOURCE_A3"]
        mapped.add(code)
        value = values.get(code)
        index = min(6, int(np.searchsorted(bounds, value, side="left"))) if value is not None else None
        color = colors[index] if value is not None else "#d6d6d2"
        if "coverage" in stem:
            color = "#865a3d" if value else "#d6d6d2" if value is not None else "#f0ece6"
        polygons = feature["geometry"]["coordinates"]
        if feature["geometry"]["type"] == "Polygon":
            polygons = [polygons]
        for polygon in polygons:
            rings = [projection.project(ring) for ring in polygon]
            path_data = " ".join("M " + " L ".join(f"{x} {y}" for x, y in coordinates) + " Z" for coordinates in rings)
            node = el("path", layer, d=path_data, fill_rule="evenodd",
                      fill=color, stroke="#fcc553", stroke_width=".004", data_iso3=code,
                      data_value="missing" if value is None else value)
            el("title", node).text = code + ": " + ("missing" if value is None else str(value))
    locators=json.loads((ROOT/'config/petroleum-point-locators.json').read_text())['points']
    for code in sorted(set(values)-mapped):
        if code not in locators:
            if 'coverage' in stem:
                continue  # The source register includes unmapped small territories.
            raise DatasetError('Petroleum quantity has no country geometry or approved locator: '+code)
        value=values[code];x,y=locators[code]
        color=('#865a3d' if value else '#d6d6d2') if 'coverage' in stem else colors[min(6,int(np.searchsorted(bounds,value,side='left')))]
        el('circle',root,cx=x,cy=y,r='.045',fill=color,stroke='#333333',stroke_width='.008',data_iso3=code,data_value=value)
    metadata = el("metadata", root, id="petroleum-source")
    metadata.text = json.dumps({"file": str(data / filename), "sha256": digest(data / filename),
                                "units": "indexed source cells" if "coverage" in stem else "million barrels/day",
                                "basis": "projection" if "2030" in stem else "source register" if "coverage" in stem else "historical/estimate"})
    target = work / (plate["id"] + SUFFIX + ".svg")
    save(root, target)
    return target


def observer_source(source, plate, scope, work):
    if scope != "japan" or plate["id"] not in ("astro-observer-ground-multiband", "orbital-technosphere-observer"):
        return source
    orbit = plate["id"].startswith("orbital")
    profile_path = binding("ORBITING_PROFILE") if orbit else binding("ASTRO_DATA_DIR") / "astro-profile.json"
    profile = json.loads(profile_path.read_text())
    point = profile["reference_point"] if orbit else profile["observer"]
    point.update(name="Setouchi, Japan", latitude_deg=34.45, longitude_deg_east=133.99)
    # Relative input references are anchored to the immutable source profile,
    # not to this derived observer profile's output work directory.
    def paths(node):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if isinstance(value, str) and key in ("file", "omm_catalog", "gaia_dr3", "nasa_exoplanets", "curated_sky"):
                    candidate = profile_path.parent / value
                    if candidate.is_file():
                        node[key] = str(candidate)
                elif key == "small_bodies":
                    node[key] = [str(profile_path.parent / p) for p in value]
                else:
                    paths(value)
        elif isinstance(node, list):
            for child in node:
                paths(child)
    paths(profile)
    derived = work / (plate["id"] + "-japan-profile.json")
    atomic_json(derived, profile)
    binary = ROOT / "src.generate" / ("generate-orbiting" if orbit else "generate-astro")
    command = [str(binary), "authagraph", "observer", str(derived)]
    subprocess.run(command, cwd=work, check=True, env=os.environ.copy())
    matches = list(work.glob(plate["id"] + SUFFIX + ".svg"))
    if not matches:
        raise DatasetError("Observer renderer did not produce the selected Japan view")
    return matches[0]


def celestial_presentation(path,plate,recipe):
    """Apply reviewed type/marker sizes to newly calculated celestial data."""
    root=E.parse(str(path),E.XMLParser(huge_tree=True)).getroot()
    scale=STYLE['atlas']['image_width_inches']/WIDTH
    uses=root.xpath('//*[local-name()="use" and @*[local-name()="href"]="#source-content"]')
    if len(uses)==1:
        scale=1
        for node in [uses[0],*uses[0].iterancestors()]:
            for value in re.findall(r'scale\(([^)]+)\)',node.get('transform','')):
                scale*=float(value.split()[0])
    ident=plate['id']
    if ident.startswith('orbital-'):
        variant=recipe['variant']
        for marker in root.xpath('//*[@data-display-group="starlink" and @data-marker-shape="sunburst"]'):
            MSP.scale_sunburst(marker,variant['starlink_marker_linear_scale'])
        global_view=ident.endswith('global')
        points=variant['global_starlink_font_size_pt' if global_view else 'observer_starlink_font_size_pt']
        for group in root.xpath('//*[@data-display-group and @data-object-count]'):
            for names in group.xpath('./*[local-name()="g" and substring(@id,string-length(@id)-4)="-name"]'):
                paint(names.attrib,display='inline' if group.get('data-display-group')=='starlink' else 'none')
                names.set('data-font-size-pt',str(points))
                for label in names.xpath('.//*[local-name()="text"]'):
                    label.set('font-size',str(points/72/scale))
                group.remove(names);group.insert(0,names)
        if global_view:
            for track in root.xpath('//*[@id="representative-ground-tracks"]/*[local-name()="path"]'):
                paint(track.attrib,stroke_width=float(css(track.attrib)['stroke-width'])*variant['global_track_width_scale'])
        root.set('data-satellite-name-display','starlink-only')
    else:
        config,_=settings(STYLE)
        for label in root.xpath('//*[@id="labels"]//*[local-name()="text"]'):
            label.set('font-size',str(config['astronomy_label_font_size_pt']/72/scale))
    save(root,path)


def japan_sky(source,destination,earth):
    """Place a freshly calculated sky beside the reviewed geographic locator."""
    doc=el('svg',width='44in',height=f'{HEIGHT}in',viewBox=f'0 0 44 {HEIGHT}',role='img')
    el('rect',doc,id='st2-sheet-paper',width=44,height=HEIGHT,fill='white')
    defs=el('defs',doc)
    defs.append(E.Comment('CURRENT-SKY'))
    for ident,bounds in (('japan-sky-clip',STYLE['japan']['viewport_inches']),('japan-locator-clip',(30,10.7,12.5,5.8))):
        clip=el('clipPath',defs,id=ident)
        el('rect',clip,**dict(zip(('x','y','width','height'),bounds)))
    frame=el('g',doc,id='st2-image-frame',transform=f'translate({FRAMING.DX} {FRAMING.DY}) scale({FRAMING.SCALE})')
    x,y,w,h=STYLE['japan']['viewport_inches'];scale=min(w/44,h/HEIGHT)
    clipped=el('g',frame,clip_path='url(#japan-sky-clip)')
    view=el('g',clipped,transform=f'translate({x+(w-44*scale)/2} {y+(h-HEIGHT*scale)/2}) scale({scale})')
    el('use',view).set('{http://www.w3.org/1999/xlink}href','#source-content')
    # Locator geometry comes from the selected basemap and the checked Japan
    # boundary, never from a retained observational SVG.
    projection=Projection('authagraph',destination.parent/'locator-projection')
    boundary=json.loads((ROOT/'config/regions/japan-10m.geojson').read_text())['geometry']
    rings=[ring for polygon in boundary['coordinates'] for ring in polygon]
    points=projection.project([point for ring in rings for point in ring])
    xs,ys=zip(*points);bx,by=min(xs)-.2,min(ys)-.2;bw,bh=max(xs)-bx+.2,max(ys)-by+.2
    lx,ly,lw,lh=30,10.7,12.5,5.8;zoom=min(lw/bw,lh/bh)
    locator=el('g',defs,id='japan-earth-context')
    land=E.parse(str(earth),E.XMLParser(huge_tree=True))
    for group in land.xpath('/*/*[@id="land" or @id="ocean" or @id="coastline" or @id="terrestrial-coastline"]'):
        group=deepcopy(group)
        group.set('id','locator-'+('land' if group.get('id')=='land' else 'ocean' if group.get('id')=='ocean' else 'coastline'))
        locator.append(group)
    px,py=projection.project([(133.99,34.45)])[0]
    el('circle',locator,cx=px,cy=py,r=.045,fill='#fcc553',data_reference='Setouchi conceptual reference; venue unconfirmed')
    clipped=el('g',frame,clip_path='url(#japan-locator-clip)')
    view=el('g',clipped,transform=f'translate({lx+(lw-bw*zoom)/2-bx*zoom} {ly+(lh-bh*zoom)/2-by*zoom}) scale({zoom})')
    el('use',view).set('{http://www.w3.org/1999/xlink}href','#japan-earth-context')
    label=el('text',frame,x=30,y=10.3,font_size='.25',fill='#fcc553');label.text='Japan / geographic locator'
    prefix,suffix=E.tostring(doc,encoding='unicode').split('<!--CURRENT-SKY-->')
    with destination.open('w') as stream:
        stream.write(prefix+'<g id="source-content">')
        xml.sax.parse(str(source),FRAMING.Body(stream,{}))
        stream.write('</g>'+suffix)


def build(catalog=None, scopes=('world','japan')):
    manifest_path, manifest = context()
    destination = output("atlas")
    work = destination / "sources/current-build"
    work.mkdir(parents=True, exist_ok=True)
    register_fonts()
    _, recipe = settings(STYLE)
    native = output("native")
    catalog = resolve_catalog_sources(catalog if catalog is not None else
                                      [p for p in manifest['products']['plates'] if p['default']])
    selections = []
    missing = []
    for plate in catalog:
        if (plate['source_stem'].startswith('petroleum-')
                or plate['id'] in ('cloud-atmosphere', 'resources-mineral-mine-production-comparison')):
            continue  # These atlas-only products are generated below.
        try:
            source = native_source(native, plate)
        except DatasetError as error:
            missing.append(str(error))
            continue
        selections.append({'id': plate['id'], 'source': str(source), 'source_sha256': digest(source),
                           'catalog_source_stem': plate.get('catalog_source_stem', plate['source_stem']),
                           'source_stem': plate['source_stem'],
                           'reference_period': plate.get('source_reference_period')})
    if missing:
        raise DatasetError('Atlas native-source preflight failed: ' + '; '.join(missing))
    atomic_json(destination/'sources/native-source-selection.json',
                {'dataset_id': manifest['dataset_id'], 'manifest_sha256': digest(manifest_path),
                 'resources_profile_sha256': digest(binding('RESOURCES_DATA_DIR')/'resources-profile.json')
                    if any('source_reference_period' in p for p in catalog) else None,
                 'selections': selections})
    # Framing's editorial ocean backing needs the fresh earth source beside
    # decompressed mineral/source inputs, not a retained historical source.
    earth = native / "authagraph/svg" / ("earth" + SUFFIX + ".svg")
    if earth.is_file():
        shutil.copyfile(earth, work / earth.name)
        (native / "atlas-sources").mkdir(exist_ok=True)
        shutil.copyfile(earth, native / "atlas-sources" / earth.name)
    records = []
    for plate in catalog:
        ident = plate["id"]
        if plate["source_stem"].startswith("petroleum-"):
            source = petroleum_native(plate, work)
        elif ident == "resources-mineral-mine-production-comparison":
            source = mineral_comparison(work)
        elif ident == "cloud-atmosphere":
            subprocess.run([str(ROOT / "src.generate/generate-cloud-atmosphere"), "authagraph",
                            str(binding("ATLAS_CLOUD_PROFILE")), str(binding("ATLAS_CLOUD_GEOJSON"))],
                           cwd=work, check=True)
            source = work / ("cloud-atmosphere" + SUFFIX + ".svg")
        else:
            source = native_path(native, plate)
        groundstation_evidence = None
        if ident == 'network-groundstations':
            source, groundstation_evidence = GROUNDSTATIONS.prepare(source, work, recipe,
                profile_path=binding('NETWORK_GROUNDSTATIONS_PROFILE'))
        for scope in scopes:
            selected = observer_source(source, plate, scope, work)
            if scope=='world' and ident in WORLD.PLATES:
                world_map,world_legend,_=WORLD.compose(ident,selected,work,recipe,
                    orbital_profile=binding('ORBITING_PROFILE') if ident.startswith('orbital-') else None,
                    groundstation_profile=binding('NETWORK_GROUNDSTATIONS_PROFILE') if ident=='network-groundstations' else None)
                for kind,tree in (('map',world_map),('legend',world_legend)):
                    path=destination/('maps' if kind=='map' else 'legends')/scope/'svg'/(ident+('-legend' if kind=='legend' else '')+'.svg')
                    tree.set('data-dataset-id',manifest['dataset_id'])
                    tree.set('data-dataset-manifest-sha256',digest(manifest_path))
                    if 'source_reference_period' in plate:
                        tree.set('data-source-reference-period',plate['source_reference_period'])
                    companion=f'../../../{"legends" if kind=="map" else "maps"}/{scope}/svg/{ident}{"-legend" if kind=="map" else ""}.svg'
                    tree.set('data-legend-companion' if kind=='map' else 'data-map-companion',companion)
                    save(tree,path)
                    records.append({'kind':kind,'scope':scope,'stem':ident,'source_stem':plate['source_stem'],
                        'svg':path.relative_to(destination).as_posix(),'svg_sha256':digest(path),
                        'source':str(selected),'source_sha256':digest(selected),
                        'sheet_background':'#fcc553' if kind=='legend' else recipe['background'],
                        'dataset_id':manifest['dataset_id'],'manifest_sha256':digest(manifest_path)})
                continue
            target = destination / "maps" / scope / "svg" / (ident + ".svg")
            target.parent.mkdir(parents=True, exist_ok=True)
            intermediate = work / f"{scope}-{ident}.svg"
            celestial = ident.startswith("astro-") or ident == "orbital-technosphere-observer"
            if scope == 'japan' and celestial:
                japan_sky(selected,intermediate,earth)
            elif scope == "world":
                FRAMING.make_plate(selected, intermediate, ident + "-legend.svg")
            else:
                unwrapped = intermediate.with_suffix(".detail.svg")
                subprocess.run([sys.executable, str(ROOT / "scripts/generate-japan-detail.py"), str(selected),
                                "--output", str(unwrapped)], check=True)
                with intermediate.open("w") as stream:
                    xml.sax.parse(str(unwrapped), JapanDefinitions(stream))
            current_theme(intermediate, target, recipe, "map", subject=ident, attributes={
                "data-dataset-id": manifest["dataset_id"], "data-dataset-manifest-sha256": digest(manifest_path),
                "data-canonical-plate-id": ident, "data-sheet-kind": "map",
                "data-legend-companion": f"../../../legends/{scope}/svg/{ident}-legend.svg",
                **({'data-source-reference-period':plate['source_reference_period']}
                   if 'source_reference_period' in plate else {})})
            if celestial or ident.startswith('orbital-'):
                celestial_presentation(target,plate,recipe)
            legend_path = destination / "legends" / scope / "svg" / (ident + "-legend.svg")
            legend_path.parent.mkdir(parents=True, exist_ok=True)
            if groundstation_evidence is not None:
                companion = GROUNDSTATIONS.legend(scope, groundstation_evidence, recipe)
                companion.set('data-dataset-id', manifest['dataset_id'])
                save(companion, legend_path)
            else:
                standalone_legend(plate, selected, legend_path, manifest, scope, manifest["sources"])
            for kind, path in (("map", target), ("legend", legend_path)):
                records.append({"kind": kind, "scope": scope, "stem": ident, "source_stem": plate["source_stem"],
                                "svg": path.relative_to(destination).as_posix(), "svg_sha256": digest(path),
                                "source": str(selected), "source_sha256": digest(selected),
                                "sheet_background": recipe["background"],
                                "dataset_id": manifest["dataset_id"], "manifest_sha256": digest(manifest_path)})
        if ident == "cloud-atmosphere":
            cloud_presentation(destination, manifest)
            for record in records:
                if record['stem'] == ident and record['kind'] == 'map':
                    record['svg_sha256'] = digest(destination / record['svg'])
                    record['sheet_background'] = '#fcc553'
                    tree = E.parse(str(destination / record['svg']))
                    record['linked_inputs'] = [{"path": str(((destination / record['svg']).parent / node.get('{http://www.w3.org/1999/xlink}href')).resolve()),
                                               "sha256": digest((destination / record['svg']).parent / node.get('{http://www.w3.org/1999/xlink}href'))}
                                              for node in tree.xpath('//*[local-name()="image"]')]
        print("Composed current atlas: " + ident, flush=True)
    atomic_json(destination / "sources/dataset.json", manifest)
    by_id = {p['id']: p for p in catalog}
    for record in records:
        plate = by_id[record['stem']]
        if 'source_reference_period' in plate:
            record['source_reference_period'] = plate['source_reference_period']
            record['catalog_source_stem'] = plate['catalog_source_stem']
    atomic_json(destination / "sources/current-atlas.json", {"schema": "cartofreako-current-atlas-v1",
                "dataset_id": manifest["dataset_id"], "manifest_sha256": digest(manifest_path),
                "records": records, "expected_sheets": 2 * len(scopes) * len(catalog)})
    atomic_json(destination / "sources/separate-sheets.json", {"schema": "cartofreako-current-atlas-v1", "records": records})
    return records


def cloud_annotation_contrast(tree):
    """Keep captions legible on the cloud sheet's amber background."""
    for node in tree.xpath('//*[local-name()="text" or local-name()="tspan"]'):
        attrs = dict(node.attrib)
        paint(attrs, fill='#240413', stroke='none')
        node.attrib.update(attrs)


def cloud_presentation(destination, manifest):
    """Render current atmospheric cells with the selected H3/opacity recipe."""
    from setouchi_h3_trials import settings_for, map_tree
    work = destination / 'sources/current-build/cloud-tiles'
    work.mkdir(parents=True, exist_ok=True)
    config = settings_for(destination, 'cloud-atmosphere', 300)
    atomic_json(work / 'settings.json', config)
    helper = ROOT / 'build/setouchi-h3-tools/render-cells'
    subprocess.run([str(helper), 'atmosphere', str(binding('ATLAS_CLOUD_PROFILE')),
                    str(binding('ATLAS_CLOUD_GEOJSON')), str(work/'settings.json'), str(work)], check=True)
    rendered = json.loads((work/'render.json').read_text())
    if rendered['h3_resolution'] != 5:
        raise DatasetError('Atmospheric atlas renderer used the wrong spatial support')
    meta = json.loads(binding('ATLAS_CLOUD_GEOJSON').read_text())['metadata']
    product = {'subject':'atmosphere','stem':'cloud-atmosphere','h3_resolution':5,
               'snapshot_sha256':digest(binding('ATLAS_CLOUD_GEOJSON'))}
    for scope in ('world','japan'):
        target = destination/'maps'/scope/'svg/cloud-atmosphere.svg'
        tree = map_tree(target, product, work, config, rendered, {'background':'#fcc553'}, scope, meta, target.parent)
        tree.getroot().set('data-legend-companion',f'../../../legends/{scope}/svg/cloud-atmosphere-legend.svg')
        cloud_annotation_contrast(tree)
        # Move each retained coastline above its observations in the same
        # coordinate frame. No reconstructed or historical coastline is used.
        for coast in tree.xpath('//*[@id="coastline" or @id="terrestrial-coastline" or @id="coastline-antarctic-inset"]'):
            for node in coast.iter():
                if E.QName(node).localname == 'path':
                    node.set('style','fill:none;stroke:#ffffff;stroke-opacity:1;stroke-width:.009166666667')
            parent = coast.getparent();parent.remove(coast);parent.append(coast)
        save(tree.getroot(),target)
    atomic_json(work/'inputs.json',{'dataset_id':manifest['dataset_id'],
                'profile_sha256':digest(binding('ATLAS_CLOUD_PROFILE')),
                'snapshot_sha256':product['snapshot_sha256'],'settings_sha256':digest(work/'settings.json'),
                'renderer_sha256':digest(helper)})


def mineral_comparison(work):
    """Build commodity symbols directly from the selected normalized values."""
    from shapely.geometry import shape
    projection = Projection("authagraph", work / "projection")
    root = projection.base("Minerals / mine production", "Independently normalized commodity symbols; reference years differ")
    resources = binding("RESOURCES_DATA_DIR")
    rows = json.loads((resources / "resources-values.json").read_text())["records"]
    geo = json.loads((resources / "countries-110m.geojson").read_text())
    positions = {}
    for f in geo["features"]:
        geometry = shape(f["geometry"])
        largest = max(geometry.geoms, key=lambda p:p.area) if geometry.geom_type == "MultiPolygon" else geometry
        point = largest.representative_point()
        positions[f["properties"]["RESOURCE_A3"]] = (point.x, point.y)
    positions = dict(zip(positions, projection.project(list(positions.values()))))
    group = el("g", root, id="mineral-type-production")
    kinds = (("rare-earth-mine-production", "rare-earth"), ("lithium-mine-production", "lithium"), ("uranium-mine-production", "uranium"))
    for column, (metric, kind) in enumerate(kinds):
        values = [r for r in rows if r["metric"] == metric]
        maximum = max(r["value"] for r in values)
        style = STYLE["resources"]["mineral_types"][kind]
        for row in values:
            if not row["value"]:
                continue
            x, y = positions[row["iso3"]]
            x += (column - 1) * .48
            radius = .22 * math.sqrt(row["value"] / maximum)
            attrs = {"fill": style["color"], "data_iso3": row["iso3"], "data_value": row["value"], "data_year": row["year"]}
            if style["shape"] == "circle":
                el("circle", group, cx=x, cy=y, r=radius, **attrs)
            elif style["shape"] == "square":
                el("rect", group, x=x-radius, y=y-radius, width=2*radius, height=2*radius, **attrs)
            else:
                el("polygon", group, points=f"{x},{y-radius} {x-radius},{y+radius} {x+radius},{y+radius}", **attrs)
    target = work / ("resources-mineral-mine-production-comparison" + SUFFIX + ".svg")
    save(root, target)
    return target


if __name__ == "__main__":
    try:
        build()
    except (DatasetError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print("current-atlas: " + str(error), file=sys.stderr)
        sys.exit(1)

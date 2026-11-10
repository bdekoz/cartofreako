"""Shared atlas presentation defaults; data palettes are not a page theme."""
import json
from pathlib import Path
import re
import xml.sax
from xml.sax.saxutils import XMLGenerator

ROOT = Path(__file__).resolve().parents[1]


def groundstation_settings(profile):
    path = ROOT/profile['atlas']['presentation']['groundstation_recipe_file']
    config = json.loads(path.read_text())
    shapes = config['capability_markers']
    if (set(shapes) != {'ka', 'ka-e', 'e', 'qv', 'quad', 'community', 'ttc', 'ku', 'unknown'}
            or set(shapes.values()) != {'circle', 'square', 'diamond', 'pentagon', 'hexagon',
                                       'star', 'cross', 'saltire', 'octagon'}):
        raise ValueError('Groundstations require nine distinct capability silhouettes')
    if not 0 < config['radius_spread_multiplier'] < 100:
        raise ValueError('Invalid groundstation radius spread')
    return config


def settings(profile):
    groundstation_settings(profile)
    presentation = profile["atlas"]["presentation"]
    if presentation["data_colors"] != "preserve-source":
        raise ValueError("Atlas presentation must retain data colors")
    config = json.loads((ROOT / presentation["recipe_file"]).read_text())
    choices = {r["randoma11y_pair"]: r for r in config["studies"]
               if r.get("family") == presentation["family"]}
    try:
        recipe = choices[presentation["default_palette"]]
    except KeyError as error:
        raise ValueError("Unknown default atlas palette") from error
    for field in ("background", "land", "text", "neutral", "halo"):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", recipe[field]):
            raise ValueError("Invalid atlas palette color: " + field)
    variant = recipe["variant"]
    for field in ("starlink_marker_linear_scale", "global_starlink_font_size_pt",
                  "observer_starlink_font_size_pt", "global_track_width_scale"):
        if not 0 < variant[field] < 100:
            raise ValueError("Invalid atlas setting: " + field)
    if not 0 < config["astronomy_label_font_size_pt"] < 100:
        raise ValueError("Invalid atlas astronomy label size")
    return config, recipe


def css(attrs):
    return dict(s.strip().split(":", 1) for s in attrs.get("style", "").split(";") if ":" in s)


def paint(attrs, **values):
    style = css(attrs)
    for key, value in values.items():
        key = key.replace("_", "-")
        # Keep both forms consistent, including styles that override attributes.
        if key in attrs:
            attrs[key] = str(value)
        style[key] = str(value)
    attrs["style"] = ";".join(k + ":" + v for k, v in style.items())


class Theme(xml.sax.ContentHandler):
    """Stream the page theme, including multi-million-circle native swarms.

    Only page backgrounds, text and unmeasured basemap decoration change paint.
    Country metrics, bathymetry, astronomy and categorical marks keep their paint.
    """
    def __init__(self, stream, recipe, kind, subject=None, attributes=None):
        self.writer = XMLGenerator(stream, encoding="utf-8")
        self.recipe, self.kind = recipe, kind
        self.subject = subject
        self.attributes = attributes or {}
        self.stack = []

    def startDocument(self):
        self.writer.startDocument()

    def startElement(self, name, attrs):
        a = dict(attrs)
        identifier = a.get("id", "")
        parents = [p.get("id", "") for p in self.stack]
        r = self.recipe
        if not self.stack:
            a.update(self.attributes)
            a["data-atlas-presentation"] = r["id"]
            a["data-sheet-background"] = r["background"]
            self.writer.startElement(name, a)
            if self.kind == "legend":
                self.writer.startElement("rect", {"id": "atlas-sheet-paper", "width": "44", "height": "19.052559",
                                                  "fill": r["background"], "data-presentation-only": "true"})
                self.writer.endElement("rect")
        else:
            if name in ("text", "tspan"):
                paint(a, fill=r["text"], stroke="none", stroke_opacity=0)
            is_background = identifier in ("st2-sheet-paper", "st2-image-background", "legend-paper")
            # Japan composites also contain an unlabelled original page rect.
            is_background |= (name == "rect" and a.get("width") in ("44", "44.0", "4224")
                              and not any(p.endswith("clip") or "clip" in p for p in parents)
                              and a.get("height") in ("19.052559", "1829.045664"))
            is_background |= any(p.endswith("-background") for p in parents)
            if is_background and name in ("rect", "path"):
                paint(a, fill=r["background"], fill_opacity=1, stroke_opacity=0)
            # Do not recolor thematic country fills nested within the land bank.
            plain_land = name == "path" and self.stack[-1].get("id", "").removesuffix("-antarctic-inset") in ("land", "terrestrial-land")
            if plain_land and not any(k.startswith("data-") for k in a):
                current = css(a)
                fill = current.get('fill', a.get('fill'))
                stroke = current.get('stroke', a.get('stroke'))
                if fill and stroke == fill:
                    paint(a, stroke=r["land"])
                paint(a, fill=r["land"])
            if name == "path" and self.subject == "earth" and any(p in ("ocean", "antarctica-source-infill") for p in parents):
                paint(a, fill=r["background"], stroke=r["background"])
            if name == "path" and "antarctica-reference-silhouette" in parents:
                paint(a, fill=r["land"], stroke=r["land"])
            # Locator land/ocean are unmeasured context, not a thematic palette.
            if name == "path" and "locator-land" in parents:
                paint(a, fill=r["land"], stroke=r["land"])
            elif name == "path" and "locator-ocean" in parents:
                paint(a, fill=r["background"], stroke=r["background"])
            reference = {"coastline", "terrestrial-coastline", "minor-islands", "ice", "graticules", "terrestrial-reference"}
            if name in ("path", "line", "polyline") and any(p.removesuffix("-antarctic-inset") in reference for p in parents):
                paint(a, stroke=r["neutral"])
            self.writer.startElement(name, a)
        self.stack.append(a)

    def characters(self, value):
        self.writer.characters(value)

    def endElement(self, name):
        self.stack.pop()
        self.writer.endElement(name)


def theme(source, destination, recipe, kind, subject=None, attributes=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w") as stream:
        xml.sax.parse(str(source), Theme(stream, recipe, kind, subject, attributes))

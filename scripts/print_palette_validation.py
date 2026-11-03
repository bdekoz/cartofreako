"""Check saved Randoma11y pairs against SVG paint and the source receipt."""

import json
import math


def paint(node, attr):
    style = dict(s.strip().split(":", 1) for s in node.get("style", "").split(";") if ":" in s)
    return style.get(attr, node.get(attr))


def channels(value):
    return [int(value[i:i+2], 16) for i in (1, 3, 5)]


def luminance(value):
    rgb = [v/255 for v in channels(value)]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))


def verify_palette(root, recipe, provenance):
    pair = next(p for p in provenance["pairs"] if p["id"] == recipe["randoma11y_pair"])
    assert (recipe["background"], recipe["text"], recipe["source_url"]) == (pair["ground"], pair["foreground"], pair["url"])
    original = (pair["original_background"], pair["original_foreground"])
    assert (pair["ground"], pair["foreground"]) == (original[::-1] if pair["reversed"] else original)
    assert pair["url"] == "https://randoma11y.com/"+"/".join(c.replace("#", "%23") for c in original)
    ratio = (luminance(recipe["text"])+.05)/(luminance(recipe["background"])+.05)
    assert math.isclose(ratio, pair["srgb_contrast_ratio"], abs_tol=.00005)
    assert recipe["srgb_contrast_ratio"] == pair["srgb_contrast_ratio"]
    for key, fraction in (("land", .16), ("neutral", .68)):
        blend = "#"+"".join(f"{round(a*(1-fraction)+b*fraction):02x}"
                           for a, b in zip(channels(recipe["background"]), channels(recipe["text"])))
        assert recipe[key] == blend
    elements = list(root.iter())
    by_id = {e.get("id"): e for e in elements if e.get("id")}
    assert root.get("data-color-study") == recipe["title"]
    assert json.loads(by_id["msp-color-recipe"].text) == recipe
    for identifier in ("st2-sheet-paper", "st2-image-background", "legend-paper"):
        if identifier in by_id:
            assert paint(by_id[identifier], "fill") == recipe["background"], identifier
    for node in elements:
        if node.tag.endswith("}text"):
            assert paint(node, "fill") in (recipe["text"], recipe["neutral"]), node.text
        if node.get("id", "").startswith("terrestrial-land"):
            for path in node.iter():
                if path.tag.endswith("}path"):
                    assert paint(path, "fill") == recipe["land"]
    return round(ratio, 4)


def verify_land_order(root):
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    if "antarctica-consolidated-inset" in by_id:
        children = [e.get("id") for e in by_id["st2-image-frame"]]
        assert children.index("st2-image-background") < children.index("antarctica-consolidated-inset") < children.index("st2-image-window")

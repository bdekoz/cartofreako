#!/usr/bin/env python3
"""Convert local KML to GeoJSON while retaining its source metadata.

One feature is emitted per Placemark, in source order. Coordinates retain
altitude and are never rounded, simplified, deduplicated or reordered.
Name, description, styleUrl, folder_path and ordered extended_data entries
are exposed as properties. properties.kml retains the complete Placemark
XML information as a JSON tree; collection.kml retains the document tree,
with Placemarks replaced by feature_id references. This preserves shared
styles, folder hierarchy, duplicate fields, geometry settings and original
coordinate text without interpreting them as current operational facts.

XML namespaces, attributes, element order and text are preserved; XML
formatting whitespace, namespace prefixes and CDATA wrappers are not.
External links are retained without fetching them. Point, LineString,
LinearRing, Polygon and MultiGeometry are supported. Unsupported geometry
or external NetworkLink inputs fail explicitly rather than losing records.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET


KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
KML = "{" + KML_NAMESPACE + "}"
GEOMETRIES = {KML + name for name in (
    "Point", "LineString", "LinearRing", "Polygon", "MultiGeometry",
)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def xml_tree(element: ET.Element, replacements: dict | None = None) -> dict:
    """Retain XML information, including repeated siblings and empty values."""
    if replacements is not None and element in replacements:
        return {"feature_id": replacements[element]}
    node = {"tag": element.tag}
    if element.attrib:
        node["attributes"] = dict(element.attrib)
    if element.text is not None and (not len(element) or element.text.strip()):
        node["text"] = element.text
    if len(element):
        node["children"] = [xml_tree(child, replacements) for child in element]
    if element.tail is not None and element.tail.strip():
        node["tail"] = element.tail
    return node


def coordinates(element: ET.Element) -> list[list[float]]:
    nodes = element.findall(KML + "coordinates")
    require(len(nodes) == 1, f"{element.tag} must have one coordinates element")
    result = []
    for token in (nodes[0].text or "").split():
        point = [float(value) for value in token.split(",")]
        require(len(point) in (2, 3), f"invalid coordinate tuple: {token}")
        require(all(math.isfinite(value) for value in point),
                f"non-finite coordinate: {token}")
        require(-180 <= point[0] <= 180 and -90 <= point[1] <= 90,
                f"out-of-range coordinate: {token}")
        result.append(point)
    require(bool(result), f"{element.tag} has no coordinates")
    return result


def geometry(element: ET.Element) -> dict:
    kind = element.tag.removeprefix(KML)
    if kind in ("Point", "LineString", "LinearRing"):
        points = coordinates(element)
        if kind == "Point":
            require(len(points) == 1, "Point must have exactly one coordinate")
            return {"type": "Point", "coordinates": points[0]}
        require(len(points) >= 2, "LineString must have at least two coordinates")
        if kind == "LinearRing":
            require(len(points) >= 4 and points[0] == points[-1],
                    "LinearRing must have at least four coordinates and be closed")
        return {"type": "LineString", "coordinates": points}
    if kind == "Polygon":
        outers = element.findall(KML + "outerBoundaryIs")
        require(len(outers) == 1, "Polygon must have one outer boundary")
        rings = []
        for boundary in outers + element.findall(KML + "innerBoundaryIs"):
            children = list(boundary)
            require(len(children) == 1 and children[0].tag == KML + "LinearRing",
                    "Polygon boundary must contain one LinearRing")
            rings.append(geometry(children[0])["coordinates"])
        return {"type": "Polygon", "coordinates": rings}
    if kind == "MultiGeometry":
        require(bool(len(element)), "MultiGeometry must not be empty")
        require(all(child.tag in GEOMETRIES for child in element),
                "MultiGeometry contains unsupported geometry")
        parts = [geometry(child) for child in element]
        types = {part["type"] for part in parts}
        if len(types) == 1 and parts[0]["type"] in ("Point", "LineString", "Polygon"):
            return {"type": "Multi" + parts[0]["type"],
                    "coordinates": [part["coordinates"] for part in parts]}
        return {"type": "GeometryCollection", "geometries": parts}
    raise ValueError(f"unsupported KML geometry: {element.tag}")


def convert(source: Path) -> dict:
    raw = source.read_bytes()
    root = ET.fromstring(raw)
    require(root.tag == KML + "kml", "expected a KML 2.2 <kml> root")
    require(root.find(".//" + KML + "NetworkLink") is None,
            "NetworkLink is not converted; provide the linked local KML instead")
    features = []
    replacements = {}
    ids = set()
    # Reserve supplied IDs so generated IDs cannot collide with later records.
    source_ids = {p.get("id") for p in root.iter(KML + "Placemark") if p.get("id")}

    def visit(element: ET.Element, folders: list[str]) -> None:
        if element.tag == KML + "Folder":
            folders = folders + [element.findtext(KML + "name", "")]
        if element.tag != KML + "Placemark":
            for child in element:
                visit(child, folders)
            return
        index = len(features) + 1
        feature_id = element.get("id")
        if not feature_id:
            feature_id = f"placemark-{index:06d}"
            while feature_id in source_ids or feature_id in ids:
                feature_id += "-generated"
        require(feature_id not in ids, f"duplicate Placemark id: {feature_id}")
        ids.add(feature_id)
        shapes = [child for child in element if child.tag in GEOMETRIES]
        name = element.findtext(KML + "name", "")
        require(len(shapes) == 1,
                f"Placemark {index} ({name!r}) must have one supported geometry")
        # A supported geometry alongside an unsupported one must also fail.
        for child in element:
            require(child.tag not in (KML + "Model",
                    "{http://www.google.com/kml/ext/2.2}Track",
                    "{http://www.google.com/kml/ext/2.2}MultiTrack"),
                    f"Placemark {index} contains unsupported geometry {child.tag}")
        properties = {"Name": name, "folder_path": folders}
        for tag in ("description", "styleUrl"):
            node = element.find(KML + tag)
            if node is not None:
                properties[tag] = node.text or ""
        extended = element.find(KML + "ExtendedData")
        if extended is not None:
            # Never turn Data entries into a dictionary: names can repeat.
            entries = []
            for data in extended.findall(KML + "Data"):
                entry = {"name": data.get("name", ""),
                         "value": data.findtext(KML + "value", "")}
                display = data.find(KML + "displayName")
                if display is not None:
                    entry["displayName"] = display.text or ""
                entries.append(entry)
            properties["extended_data"] = entries
        properties["kml"] = xml_tree(element)
        try:
            shape = geometry(shapes[0])
        except ValueError as error:
            raise ValueError(f"Placemark {index} ({name!r}): {error}") from error
        features.append({"type": "Feature", "id": feature_id,
                         "properties": properties, "geometry": shape})
        replacements[element] = feature_id

    visit(root, [])
    require(bool(features), "KML contains no Placemarks")
    return {
        "type": "FeatureCollection",
        "name": source.stem,
        "source": {"file": source.name, "sha256": hashlib.sha256(raw).hexdigest(),
                   "bytes": len(raw)},
        "kml": {"metadata_schema": "cartofreako-kml-tree-v1",
                "document": xml_tree(root, replacements)},
        "features": features,
    }


def encode(collection: dict) -> str:
    # One feature per line keeps rich metadata readable by record and avoids
    # megabytes of indentation for the retained XML trees.
    header = {key: value for key, value in collection.items() if key != "features"}
    prefix = json.dumps(header, ensure_ascii=False, indent=2, allow_nan=False)
    records = [json.dumps(feature, ensure_ascii=False, allow_nan=False)
               for feature in collection["features"]]
    return prefix[:-2] + ',\n  "features": [\n    ' + ',\n    '.join(records) + '\n  ]\n}\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="local .kml file")
    parser.add_argument("output", type=Path, help="destination .geojson file")
    parser.add_argument("--check", action="store_true",
                        help="verify that output matches conversion without writing")
    args = parser.parse_args()
    temporary = None
    try:
        require(args.source.resolve() != args.output.resolve(),
                "source and output must be different files")
        collection = convert(args.source)
        encoded = encode(collection).encode("utf-8")
        if args.check:
            require(args.output.read_bytes() == encoded,
                    f"{args.output} differs from conversion of {args.source}")
        else:
            # Do not truncate a valid previous output on a failed conversion.
            with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
            temporary.chmod(0o644)
            temporary.replace(args.output)
        counts = Counter(feature["geometry"]["type"] for feature in collection["features"])
        action = "Verified" if args.check else "Wrote"
        print(f"{action} {args.output}: {len(collection['features'])} features "
              f"({', '.join(f'{count} {kind}' for kind, count in sorted(counts.items()))})")
        return 0
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"convert-kml-geojson: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())

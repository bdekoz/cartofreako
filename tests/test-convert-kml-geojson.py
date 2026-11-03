#!/usr/bin/env python3
"""Check geometry and metadata fidelity, including the supplied Starlink KML."""

from collections import Counter
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/convert-kml-geojson.py"
DATA = ROOT / "assets.static/network-groundstations"
SOURCE = DATA / "starlink-global-gateways-pops.20261103.kml"
OUTPUT = SOURCE.with_suffix(".geojson")
SPEC = importlib.util.spec_from_file_location("converter", SCRIPT)
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)
K = converter.KML


def restore(node, features):
    if "feature_id" in node:
        node = features[node["feature_id"]]["properties"]["kml"]
    element = ET.Element(node["tag"], node.get("attributes", {}))
    element.text = node.get("text")
    element.tail = node.get("tail")
    element.extend(restore(child, features) for child in node.get("children", []))
    return element


class SourceFidelity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml = ET.parse(SOURCE).getroot()
        cls.data = json.loads(OUTPUT.read_text(), parse_float=Decimal)

    def test_all_records_coordinates_and_fields(self):
        placemarks = list(self.xml.iter(K + "Placemark"))
        features = self.data["features"]
        self.assertEqual(len(placemarks), 780)
        self.assertEqual(len(features), len(placemarks))
        self.assertEqual(Counter(f["geometry"]["type"] for f in features),
                         {"Point": 656, "LineString": 124})
        self.assertEqual(len({f["id"] for f in features}), 780)
        coordinate_count = 0
        duplicate_fields = 0
        for placemark, feature in zip(placemarks, features):
            properties = feature["properties"]
            self.assertEqual(properties["Name"], placemark.findtext(K + "name"))
            self.assertEqual(properties.get("description"),
                             placemark.findtext(K + "description"))
            self.assertEqual(properties["styleUrl"], placemark.findtext(K + "styleUrl"))
            original = [[Decimal(v) for v in token.split(",")] for token in
                        placemark.find(".//" + K + "coordinates").text.split()]
            actual = feature["geometry"]["coordinates"]
            if feature["geometry"]["type"] == "Point":
                actual = [actual]
            self.assertEqual(original, actual, properties["Name"])
            coordinate_count += len(actual)
            entries = placemark.findall(K + "ExtendedData/" + K + "Data")
            expected = [{"name": e.get("name"), "value": e.findtext(K + "value", "")}
                        for e in entries]
            self.assertEqual(properties.get("extended_data", []), expected)
            duplicate_fields += len(entries) != len({e.get("name") for e in entries})
        self.assertEqual(coordinate_count, 1009)
        self.assertEqual(duplicate_fields, 294)

    def test_document_and_placemarks_reconstruct_source_xml(self):
        features = {f["id"]: f for f in self.data["features"]}
        restored = restore(self.data["kml"]["document"], features)
        # Canonicalization excludes XML formatting while comparing every
        # element, attribute, style, geometry setting and custom field.
        self.assertEqual(
            ET.canonicalize(ET.tostring(self.xml, encoding="unicode"), strip_text=True),
            ET.canonicalize(ET.tostring(restored, encoding="unicode"), strip_text=True))
        folders = [f.findtext(K + "name") for f in self.xml.iter(K + "Folder")]
        self.assertEqual(len(folders), 10)
        self.assertEqual(set(folders),
                         {f["properties"]["folder_path"][0] for f in features.values()})

    def test_profile_and_source_hashes(self):
        profile = json.loads((DATA / "network-groundstations-profile.json").read_text())
        self.assertEqual(self.data["source"]["sha256"], hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(profile["source"]["kml_sha256"], self.data["source"]["sha256"])
        self.assertEqual(profile["source"]["gateways_sha256"], hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
        self.assertEqual(profile["source"]["geojson"], OUTPUT.name)
        self.assertEqual(profile["display"]["expected_features"], len(self.data["features"]))


class Conversion(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "example.kml"

    def convert(self, content):
        self.source.write_text(f'<kml xmlns="{converter.KML_NAMESPACE}">{content}</kml>')
        return converter.convert(self.source)

    def test_nested_folders_unicode_duplicates_and_empty_values(self):
        data = self.convert('''<Document><Folder><name>Outer</name><Folder><name>内側</name>
          <Placemark id="kept"><name>São &amp; 東京</name>
            <description><![CDATA[<b>Details</b>  ]]></description>
            <ExtendedData><Data name="size"><value>1.85</value></Data>
              <Data name="size"><value/></Data></ExtendedData>
            <Point><altitudeMode>relativeToGround</altitudeMode>
              <coordinates>139.123456789012,35.765432109876,-4.5</coordinates></Point>
          </Placemark></Folder></Folder></Document>''')
        feature = data["features"][0]
        self.assertEqual(feature["id"], "kept")
        self.assertEqual(feature["properties"]["Name"], "São & 東京")
        self.assertEqual(feature["properties"]["description"], "<b>Details</b>  ")
        self.assertEqual(feature["properties"]["folder_path"], ["Outer", "内側"])
        self.assertEqual(feature["properties"]["extended_data"],
                         [{"name": "size", "value": "1.85"}, {"name": "size", "value": ""}])
        self.assertEqual(feature["geometry"]["coordinates"],
                         [139.123456789012, 35.765432109876, -4.5])
        self.assertEqual(json.loads(converter.encode(data)), data)

    def test_polygon_holes_and_mixed_geometry(self):
        data = self.convert('''<Placemark><MultiGeometry>
          <Point><coordinates>1,2</coordinates></Point><Polygon>
          <outerBoundaryIs><LinearRing><coordinates>0,0 4,0 4,4 0,0</coordinates>
            </LinearRing></outerBoundaryIs>
          <innerBoundaryIs><LinearRing><coordinates>1,1 1,2 2,2 1,1</coordinates>
            </LinearRing></innerBoundaryIs></Polygon></MultiGeometry></Placemark>''')
        shape = data["features"][0]["geometry"]
        self.assertEqual(shape["type"], "GeometryCollection")
        self.assertEqual(shape["geometries"][1], {"type": "Polygon", "coordinates": [
            [[0, 0], [4, 0], [4, 4], [0, 0]], [[1, 1], [1, 2], [2, 2], [1, 1]]]})

    def test_rejects_invalid_or_unsupported_geometry(self):
        for geometry in ("<Point><coordinates>181,1,0</coordinates></Point>",
                         "<Point><coordinates>1,nan,0</coordinates></Point>",
                         "<LineString><coordinates>1,2</coordinates></LineString>",
                         "<Model/>", ""):
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                self.convert("<Placemark>" + geometry + "</Placemark>")
        with self.assertRaisesRegex(ValueError, "NetworkLink"):
            self.convert("<NetworkLink><Link><href>remote.kml</href></Link></NetworkLink>")

    def test_cli_is_deterministic_and_preserves_output_on_failure(self):
        self.convert("<Placemark><Point><coordinates>1,2,3</coordinates></Point></Placemark>")
        output = self.source.with_suffix(".geojson")
        command = [sys.executable, str(SCRIPT), str(self.source), str(output)]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = output.read_bytes()
        check = subprocess.run(command + ["--check"], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        output.write_bytes(original + b" ")
        self.assertNotEqual(subprocess.run(command + ["--check"], capture_output=True).returncode, 0)
        output.write_bytes(original)
        self.source.write_text("<broken")
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

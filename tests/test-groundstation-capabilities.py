#!/usr/bin/env python3
"""Focused regression checks for consequential antenna-inventory interpretation."""

import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from groundstation_capabilities import interpret, normalize, positive_number


def feature(fields, folder="North America", geometry="Point"):
    return {"id": "test-site", "properties": {"Name": "Test site", "folder_path": [folder],
            "extended_data": [{"name": k, "value": v} for k, v in fields]},
            "geometry": {"type": geometry, "coordinates": [1, 2] if geometry == "Point" else [[1, 2], [3, 4]]}}


class CapabilityTests(unittest.TestCase):
    def test_shared_bands_are_not_added(self):
        result = interpret(feature([("Ka Antenna Size", "1.85"), ("Ka Antenna Count", "40"),
                                    ("E Antenna Size", "1.85"), ("E Antenna Count", "40")]))
        self.assertAlmostEqual(result["aperture_proxy_m2"], 40*math.pi*1.85**2/4)

    def test_blank_duplicate_does_not_erase_diameter(self):
        result = interpret(feature([("Ka Antenna Size", "1.47"), ("Ka Antenna Size", ""), ("Ka Antenna Count", "8")]))
        self.assertAlmostEqual(result["aperture_proxy_m2"], 8*math.pi*1.47**2/4)
        self.assertEqual(result["field_resolutions"][0]["chosen"], "1.47")
        self.assertEqual(len(result["raw_extended_data"]), 3)

    def test_equivalent_numbers_and_trailing_decimal(self):
        result = interpret(feature([("Ka Antenna Size", "5.0"), ("Ka Antenna Size", "5"), ("Ka Antenna Count", "2.")]))
        self.assertAlmostEqual(result["aperture_proxy_m2"], 2*math.pi*25/4)
        self.assertEqual(positive_number("32.", True), 32)

    def test_conflicting_repeated_values_remain_unknown(self):
        result = interpret(feature([("Ka Antenna Size", "1.47"), ("Ka Antenna Size", "1.85"), ("Ka Antenna Count", "8")]))
        self.assertIsNone(result["aperture_proxy_m2"])
        self.assertIn("conflicting-repeated-field", [i["code"] for i in result["issues"]])

    def test_fractional_count_and_composite_diameter_not_coerced(self):
        for value in ("1.85", "-2", "nan", "inf", "0"):
            self.assertIsNone(positive_number(value, True))
        result = interpret(feature([("Ka/E Antenna Size", "1.85+1.999"), ("Ka/E Antenna Count", "40"),
                                    ("Q/V Antenna Size", "1.999"), ("Q/V Antenna Count", "20")]))
        self.assertEqual(result["selected_bank"], "Q/V")
        self.assertTrue(result["incomplete_inventory"])
        self.assertAlmostEqual(result["aperture_proxy_m2"], 20*math.pi*1.999**2/4)

    def test_partial_construction_does_not_become_operating_capacity(self):
        result = interpret(feature([("Ka Antenna Size", "1.85"), ("Ka Antenna Count", "40"),
                                    ("Status", "Built 10 of 40"), ("Ka Operational", "FALSE")]))
        self.assertEqual(result["status"], "unconfirmed")
        self.assertIn("partial-build-status", [i["code"] for i in result["issues"]])
        self.assertAlmostEqual(result["aperture_proxy_m2"], 40*math.pi*1.85**2/4)

    def test_retired_and_negative_status_override_operational_flag(self):
        for status, expected in (("Demolished", "retired"), ("Not built as of June", "unconfirmed")):
            result = interpret(feature([("Ka Operational", "TRUE"), ("Status", status)]))
            self.assertEqual(result["status"], expected)
            self.assertIn("operational-status-conflict", [i["code"] for i in result["issues"]])

    def test_pop_ports_and_link_endpoints_are_not_antennas(self):
        for f, expected in ((feature([], "PoPs & Backbone"), "pop"), (feature([], geometry="LineString"), "link")):
            result = interpret(f)
            self.assertEqual(result["kind"], expected)
            self.assertNotIn("aperture_proxy_m2", result)

    def test_duplicate_ids_fail(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            normalize({"features": [feature([]), feature([])]})


if __name__ == "__main__":
    unittest.main()

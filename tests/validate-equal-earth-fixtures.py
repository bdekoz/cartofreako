#!/usr/bin/env python3
"""Validate the standalone Stage 16J Equal Earth fixture contract."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    schema_path = ROOT / "contracts" / "equal-earth-projection-fixtures-v1.schema.json"
    fixture_path = ROOT / "fixtures" / "projections" / "equal-earth-v1" / "fixtures.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(fixture)

    layout_ids = [layout["layoutId"] for layout in fixture["layouts"]]
    assert layout_ids == [
        "equal-earth/canonical-greenwich",
        "equal-earth/africa-centered-11.5e",
    ]
    case_ids = [
        case["caseId"]
        for layout in fixture["layouts"]
        for case in layout["cases"]
    ]
    assert len(case_ids) == 30
    assert len(set(case_ids)) == len(case_ids)
    print("Equal Earth fixture schema passed: 30 cases, 2 layouts")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate checked and generated Stage 14 JSON contracts."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> object:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate(schema_path: str, instance_path: str) -> None:
    schema = load(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(
        load(instance_path))


def main() -> None:
    validate("contracts/standard-artifact-manifest-v1.schema.json",
             "contracts/standard-artifact-manifest-v1.json")
    validate("contracts/artifacts-v1.schema.json",
             "assets.generated/catalog/artifacts-v1.json")
    validate("contracts/artifact-request-v1.schema.json",
             "tests/fixtures/artifact-selection/request.json")
    validate("contracts/artifact-decision-receipt-v1.schema.json",
             "tests/fixtures/artifact-selection/expected-receipt.json")
    print("artifact JSON schemas passed: standard manifest, catalog, request, receipt")


if __name__ == "__main__":
    main()

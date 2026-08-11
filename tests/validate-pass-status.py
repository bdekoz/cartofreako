#!/usr/bin/env python3
"""Validate current pass maturity against the standard artifact graph."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> object:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    schema = load("contracts/pass-status-v1.schema.json")
    status = load("contracts/pass-status-v1.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(status)
    assert isinstance(status, dict)

    standard = load("contracts/standard-artifact-manifest-v1.json")
    assert isinstance(standard, dict)
    by_pass: dict[str, list[dict]] = {}
    for artifact in standard["artifacts"]:
        by_pass.setdefault(artifact["passId"], []).append(artifact)

    expected = {
        "anthropocene",
        "anthropocene-temperature-2025",
        "anthropocene-temperature-2026",
    }
    passes = status["passes"]
    assert {value["id"] for value in passes} == expected
    for value in passes:
        artifacts = by_pass[value["id"]]
        assert len(artifacts) == value["artifactManifest"]["artifactCount"] == 6
        assert all(artifact["lifecycle"] == "standard" for artifact in artifacts)
        assert {artifact["projectionId"] for artifact in artifacts} == {
            "cahill-keyes", "authagraph", "dymaxion",
            "myriahedral", "star-x", "voronoi",
        }
        assert value["current"] is True
        assert value["defaultGenerated"] is True
        assert value["maturity"] == "accepted-experimental"

    print("Pass status passed: 3 current accepted-experimental Anthropocene passes remain standard across 18 artifacts.")


if __name__ == "__main__":
    main()

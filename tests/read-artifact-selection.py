#!/usr/bin/env python3
"""Minimal independent selection and receipt-hash check for the golden case."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "artifact-selection"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def main() -> None:
    request = json.loads((FIXTURES / "request.json").read_text(encoding="utf-8"))
    catalog = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
    receipt = json.loads((FIXTURES / "expected-receipt.json").read_text(encoding="utf-8"))
    variants = []
    for artifact in catalog["artifacts"]:
        if artifact["pass"]["id"] not in request["passIds"]:
            continue
        if artifact["pass"]["lifecycle"] != "standard":
            continue
        if artifact["projection"]["id"] not in request["projectionIds"]:
            continue
        for format_name, variant_name in (("png", "screen-png"),
                                          ("webp", "screen-webp")):
            if format_name not in request["formats"]:
                continue
            file_record = artifact["screen"][format_name]
            projection_rank = request["preferences"][0]["order"].index(
                artifact["projection"]["id"])
            format_rank = request["preferences"][1]["order"].index(format_name)
            variants.append(((projection_rank, format_rank, file_record["bytes"],
                              artifact["id"], variant_name), artifact["id"], variant_name))
    _, selected_artifact, selected_variant = min(variants)
    assert selected_artifact == receipt["decisionCore"]["selection"]["artifactId"]
    assert selected_variant == receipt["decisionCore"]["selection"]["variantId"]
    digest = hashlib.sha256(canonical(receipt["decisionCore"])).hexdigest()
    assert digest == receipt["decisionCoreSha256"]
    print(f"clean-room artifact selector passed: {selected_artifact} / {selected_variant} / {digest}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Minimal clean-room reader for the neutral projection fixture bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "projections" / "v1"


def main() -> None:
    checksums = {}
    for line in (FIXTURES / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        checksums[filename] = digest
        payload = (FIXTURES / filename).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == digest

    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["totalCaseCount"] > 30_000
    observed = 0
    for family_record in manifest["families"]:
        document = json.loads((FIXTURES / family_record["file"]).read_text(encoding="utf-8"))
        assert document["coordinateContract"]["origin"] == "top-left"
        for layout in document["layouts"]:
            assert layout["nativeAspect"] > 0
            for case in layout["cases"]:
                u, v = case["expected"]["projected"]
                # A consumer can map neutral coordinates to any same-ratio frame.
                x, y = u * 1920.0, v * (1920.0 / layout["nativeAspect"])
                assert -1e-8 <= x <= 1920.0 + 1e-8
                assert -1e-8 <= y <= 1920.0 / layout["nativeAspect"] + 1e-8
                # Candidate order has no semantic meaning; compare set keys.
                candidates = {
                    (candidate["topologyKey"], candidate["component"],
                     tuple(candidate["geographic"]))
                    for candidate in case["expected"]["reverseCandidates"]
                }
                assert candidates
                observed += 1
    assert observed == manifest["totalCaseCount"]
    print(f"clean-room fixture reader passed: {observed} cases, {len(checksums)} hashes")


if __name__ == "__main__":
    main()

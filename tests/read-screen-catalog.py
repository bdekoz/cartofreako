#!/usr/bin/env python3
"""Dependency-free clean-room reader for the Stage 14 screen catalog."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def close(left: list[float], right: list[float]) -> bool:
    return len(left) == len(right) and all(math.isclose(a, b, rel_tol=0,
        abs_tol=1e-12) for a, b in zip(left, right))


def main() -> None:
    manifest_path = ROOT / "contracts" / "standard-artifact-manifest-v1.json"
    catalog_path = ROOT / "assets.generated" / "catalog" / "artifacts-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert manifest["artifactCount"] == 217 == len(catalog["artifacts"])
    assert {value["id"] for value in manifest["artifacts"]} == {
        value["id"] for value in catalog["artifacts"]}
    assert catalog["sourceRevision"]["standardManifestSha256"] == digest(manifest_path)
    file_count = 0
    for artifact in catalog["artifacts"]:
        assert artifact["pass"]["lifecycle"] == "standard"
        frame = artifact["projection"]["artifactFrame"]
        screen = artifact["screen"]
        box = screen["contentRectangle"]
        sx = box["width"] / frame["width"]
        sy = box["height"] / frame["height"]
        expected_forward = [
            sx, 0, box["x"] - frame["x"] * sx,
            0, sy, box["y"] - frame["y"] * sy,
            0, 0, 1,
        ]
        expected_reverse = [
            1 / sx, 0, frame["x"] - box["x"] / sx,
            0, 1 / sy, frame["y"] - box["y"] / sy,
            0, 0, 1,
        ]
        assert close(screen["projectedToScreen"], expected_forward)
        assert close(screen["screenToProjected"], expected_reverse)
        assert box["x"] >= 0 and box["y"] >= 0
        assert box["x"] + box["width"] <= 1920
        assert box["y"] + box["height"] <= 1080
        for record in (*artifact["parents"].values(), screen["png"], screen["webp"]):
            assert digest(ROOT / record["path"]) == record["sha256"]
            file_count += 1
    assert file_count == 1085
    print("clean-room screen catalog passed: 217 artifacts / 1085 files / affine matrices / hashes")


if __name__ == "__main__":
    main()

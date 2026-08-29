#!/usr/bin/env python3
"""Verify the alpha60 media-object audit Cahill-Keyes plate contract."""

from __future__ import annotations

import argparse
import pathlib
import subprocess


AUDIT_OCEAN = "rgb(242,242,242)"
AUDIT_LAND = "rgb(255,255,255)"
EXPECTED_OCEAN_REFERENCES = 30
EXPECTED_LAND_REFERENCES = 102

# Stable solid interiors in the canonical 3840x1920 Cahill-Keyes geometry.
OCEAN_SAMPLE = (800, 800)
LAND_SAMPLE = (1500, 1100)


def command_output(command: list[str]) -> str:
    return subprocess.run(
        command, check=True, capture_output=True, text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--svg", type=pathlib.Path, required=True)
    parser.add_argument("--png", type=pathlib.Path, required=True)
    args = parser.parse_args()

    body = args.svg.read_text(encoding="utf-8")
    ocean_count = body.count(AUDIT_OCEAN)
    land_count = body.count(AUDIT_LAND)
    if ocean_count != EXPECTED_OCEAN_REFERENCES:
        raise SystemExit(
            f"error: {args.svg}: expected {EXPECTED_OCEAN_REFERENCES} "
            f"audit-ocean references, found {ocean_count}")
    if land_count != EXPECTED_LAND_REFERENCES:
        raise SystemExit(
            f"error: {args.svg}: expected {EXPECTED_LAND_REFERENCES} "
            f"white-land references, found {land_count}")

    identity = command_output([
        "identify", "-format", "%w %h %[colorspace]", str(args.png),
    ]).split()
    if identity[:2] != ["3840", "1920"] or len(identity) != 3:
        raise SystemExit(
            f"error: {args.png}: expected 3840x1920 RGB image, "
            f"found {' '.join(identity)}")
    if identity[2].lower() not in ("rgb", "srgb"):
        raise SystemExit(
            f"error: {args.png}: expected RGB colorspace, found {identity[2]}")

    ox, oy = OCEAN_SAMPLE
    lx, ly = LAND_SAMPLE
    colors = command_output([
        "magick", str(args.png), "-format",
        f"%[hex:p{{{ox},{oy}}}] %[hex:p{{{lx},{ly}}}]", "info:",
    ]).upper().split()
    if colors != ["F2F2F2", "FFFFFF"]:
        raise SystemExit(
            f"error: {args.png}: ocean/land samples are {colors}, "
            "expected F2F2F2/FFFFFF")

    print(
        f"{args.png}: 3840x1920 {identity[2]}, "
        f"ocean@{ox},{oy}=F2F2F2, land@{lx},{ly}=FFFFFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

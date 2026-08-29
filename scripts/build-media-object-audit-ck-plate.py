#!/usr/bin/env python3
"""Derive the alpha60 media-object audit Cahill-Keyes plate.

The canonical full-color Earth remains the only geometry source. This
transform changes its ocean to rgb(242,242,242) and its land to white while
preserving every path, transform, and document attribute byte-for-byte.
"""

from __future__ import annotations

import argparse
import pathlib


SOURCE_OCEAN = "rgb(117,99,253)"
AUDIT_OCEAN = "rgb(242,242,242)"
SOURCE_LAND = "rgb(71,160,3)"
AUDIT_LAND = "rgb(255,255,255)"
EXPECTED_OCEAN_REFERENCES = 30
EXPECTED_LAND_REFERENCES = 102


def transform(source: pathlib.Path, output: pathlib.Path) -> tuple[int, int]:
    body = source.read_text(encoding="utf-8")
    ocean_count = body.count(SOURCE_OCEAN)
    land_count = body.count(SOURCE_LAND)
    if ocean_count != EXPECTED_OCEAN_REFERENCES:
        raise SystemExit(
            f"error: expected {EXPECTED_OCEAN_REFERENCES} canonical ocean "
            f"references in {source}, found {ocean_count}")
    if land_count != EXPECTED_LAND_REFERENCES:
        raise SystemExit(
            f"error: expected {EXPECTED_LAND_REFERENCES} canonical land "
            f"references in {source}, found {land_count}")

    transformed = body.replace(SOURCE_OCEAN, AUDIT_OCEAN)
    transformed = transformed.replace(SOURCE_LAND, AUDIT_LAND)
    if SOURCE_OCEAN in transformed or SOURCE_LAND in transformed:
        raise SystemExit("error: canonical colors remain after plate transform")
    if transformed.count(AUDIT_OCEAN) != ocean_count:
        raise SystemExit("error: audit ocean replacement count changed")
    if transformed.count(AUDIT_LAND) != land_count:
        raise SystemExit("error: audit land replacement count changed")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(transformed, encoding="utf-8")
    temporary.replace(output)
    return ocean_count, land_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    ocean_count, land_count = transform(args.source, args.output)
    print(
        f"{args.output}: ocean={AUDIT_OCEAN} ({ocean_count}), "
        f"land={AUDIT_LAND} ({land_count})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

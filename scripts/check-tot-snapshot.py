#!/usr/bin/env python3
"""Validate the committed top-of-tree preview snapshot manifest.

The manifest's `sourceRevision` records the commit that generated the imagery.
It is compared against the live generated catalog when that catalog is
present (the restage host), and its schema/revision presence is checked
everywhere else. It is intentionally not compared against the current HEAD:
HEAD advances with every commit, including documentation-only commits that
cannot change the staged imagery.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "assets.tot" / "manifest.json"
CATALOG_PATH = ROOT / "assets.generated" / "catalog" / "artifacts-v1.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    if not MANIFEST_PATH.is_file():
        print(f"missing TOT manifest: {MANIFEST_PATH}", file=sys.stderr)
        return 1
    try:
        manifest = load_json(MANIFEST_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"unreadable TOT manifest: {exc}", file=sys.stderr)
        return 1
    if manifest.get("schema") != "cartofreako-tot-preview-manifest-v1":
        print("invalid TOT manifest schema", file=sys.stderr)
        return 1
    revision = (manifest.get("sourceRevision") or {}).get("gitCommit")
    if not revision:
        print("TOT manifest missing sourceRevision.gitCommit", file=sys.stderr)
        return 1

    if CATALOG_PATH.is_file():
        try:
            catalog = load_json(CATALOG_PATH)
            catalog_revision = (catalog.get("sourceRevision") or {}).get(
                "gitCommit"
            )
        except (OSError, json.JSONDecodeError) as exc:
            print(f"unreadable generated catalog: {exc}", file=sys.stderr)
            return 1
        if catalog_revision and revision != catalog_revision:
            print(
                "tot snapshot lags generated catalog: "
                f"recorded {revision}, catalog {catalog_revision}",
                file=sys.stderr,
            )
            return 1

    print(f"tot snapshot check passed at {revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

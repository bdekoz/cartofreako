#!/usr/bin/env python3
"""Validate dataset-bound atlas sheets and complete artifact receipts."""
import argparse
import json
from pathlib import Path
import sys

from dataset import ROOT, DatasetError, atomic_json, context, digest, output


def check_atlas():
    selected, dataset = context()
    root = output("atlas")
    receipt = json.loads((root / "sources/current-atlas.json").read_text())
    expected = {p['id'] for p in dataset['products']['plates'] if p['default']}
    keys = {(r["stem"], r["scope"], r["kind"]) for r in receipt["records"]}
    if len(keys) != len(receipt["records"]) or keys != {
            (stem, scope, kind) for stem in expected for scope in ("world", "japan") for kind in ("map", "legend")}:
        raise DatasetError("Incomplete current atlas map/legend selection")
    if receipt["dataset_id"] != dataset["dataset_id"] or receipt["manifest_sha256"] != digest(selected):
        raise DatasetError("Atlas mixes dataset editions")
    exports = json.loads((root / "sources/sheet-export-manifest.json").read_text())["records"]
    by_key = {(r["stem"], r["scope"], r["kind"]): r for r in exports}
    if set(by_key) != keys or len(exports) != len(keys):
        raise DatasetError("Atlas export selection is incomplete")
    for row in receipt["records"]:
        for linked in row.get('linked_inputs', []):
            if digest(linked['path']) != linked['sha256']:
                raise DatasetError('Atlas linked data changed after composition')
        if digest(root / row["svg"]) != row["svg_sha256"] or digest(row["source"]) != row["source_sha256"]:
            raise DatasetError("Atlas source/cartography changed after composition")
        exported = by_key[row["stem"], row["scope"], row["kind"]]
        if exported["fingerprint"]["svg_sha256"] != row["svg_sha256"]:
            raise DatasetError("Atlas exports do not match their source SVG")
        for item in exported["outputs"].values():
            path = root / item["path"]
            if not path.is_file() or not path.stat().st_size or digest(path) != item["sha256"]:
                raise DatasetError("Missing/stale atlas export: " + str(path))
    result = {"status": "passed", "dataset_id": dataset["dataset_id"], "sheets": len(keys),
              "manifest_sha256": digest(selected)}
    atomic_json(root / "sources/current-validation.json", result)
    print(f"Current atlas passed: {len(keys)} sheets; dataset {dataset['dataset_id']}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", action="store_true", required=True)
    parser.parse_args()
    try:
        check_atlas()
    except (DatasetError, OSError, ValueError, KeyError) as error:
        print("current-build: " + str(error), file=sys.stderr)
        sys.exit(1)

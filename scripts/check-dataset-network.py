#!/usr/bin/env python3
"""Verify copied network inputs against the selected edition, without Git."""
from pathlib import Path
import sys

from dataset import DatasetError, binding, context, digest


def main(args):
    names = ["NETWORK_INFRASTRUCTURE_CLOUD_SOURCE"]
    if args[:1] == ["topology"]:
        names += ["SUBMARINE_CABLE_SOURCE", "INTERNET_EXCHANGE_SOURCE"]
    elif args[:1] != ["sites"]:
        raise DatasetError("Unknown network source selection")
    if len(args) != len(names) + 1:
        raise DatasetError("Incomplete network source arguments")
    path, manifest = context()
    for name, supplied in zip(names, args[1:]):
        root = binding(name)
        if Path(supplied).resolve() != root:
            raise DatasetError("Network source conflicts with dataset: " + name)
        rows = [r for r in manifest["files"] if (path.parent / r["path"]).is_relative_to(root)]
        if not rows or any(digest(path.parent / r["path"]) != r["sha256"] for r in rows):
            raise DatasetError("Network source bytes changed: " + name)
    print("Dataset network sources verified: " + manifest["dataset_id"])


if __name__ == "__main__":
    main(sys.argv[1:])

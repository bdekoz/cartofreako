#!/usr/bin/env python3
"""Resolve one immutable edition and execute a build with its exact bindings."""
import argparse
from datetime import datetime
import shlex
import os
from pathlib import Path
import subprocess
import sys

from dataset import DatasetError, ROOT, data_root, digest, load, safe_path


def build_command(manifest_path, manifest, command):
    # Values are argv/environment entries, never parsed as shell/Make code.
    # Reject Make metacharacters in filesystem bindings before handing values
    # to recursive Make (which interprets command-line assignments itself).
    values = {name: str(safe_path(manifest_path.parent, value))
              for name, value in manifest["bindings"].items()}
    values.update(DATASET_MANIFEST=str(manifest_path), DATASET_ID=manifest["dataset_id"],
                  DATASET_MANIFEST_SHA256=digest(manifest_path))
    out = ROOT / "output/data-editions" / manifest["dataset_id"]
    values.update(GENERATED_DIR=str(out / "native"), ATLAS_OUTPUT=str(out / "atlas"),
                  ATLAS_BASE=str(out / "atlas-base"),DATASET_OUTPUT_ROOT=str(out),
                  SOURCE_DATE_EPOCH=str(int(datetime.fromisoformat(manifest['requested_as_of']).timestamp())))
    for name, filename in (("ASTRO_PROFILE", "astro-profile.json"), ("ASTRO_HUBBLE_PROFILE", "astro-hubble-profile.json")):
        values[name] = str(Path(values["ASTRO_DATA_DIR"]) / filename)
    for year in (2025, 2026):
        for family, stem in (("PARTICULATE", "particulate"), ("TEMPERATURE", "land-temperature")):
            prefix = "ANTHROPOCENE_" + family
            base = Path(values["ANTHROPOCENE_DATA_DIR"]) / f"anthropocene-{stem}-{year}"
            values[f"{prefix}_PROFILE_{year}"] = str(base) + "-profile.json"
            values[f"{prefix}_GEOJSON_{year}"] = str(base) + ".geojson"
    if any(any(c in value for c in "\n\r$#;") for value in values.values()):
        raise DatasetError("Unsafe dataset binding path")
    env = {**os.environ, **values, "DATASET_BOUND": "1",
           "PATH":str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH','')}
    if Path(command[0]).name in ("make", "gmake"):
        protected = set(values) | {"DATASET", "DATASET_BOUND"}
        for arg in [*shlex.split(os.environ.get("MAKEFLAGS", "")), *command[1:]]:
            if "=" in arg and arg.split("=", 1)[0] in protected:
                name, value = arg.split("=", 1)
                if (name == "DATASET" and value == "current") or (name in values and value == values[name]):
                    continue
                raise DatasetError("Conflicting dataset/profile override: " + name)
        command = [*command, "DATASET_BOUND=1", *[f"{key}={value}" for key, value in values.items()]]
    return command, env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest")
    parser.add_argument("--print", action="store_true", dest="print_path")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        path, manifest = load(args.manifest)
        if args.print_path:
            print(path)
            return 0
        command = args.command
        if command[:1] == ["--"]:
            command = command[1:]
        if not command:
            parser.error("a build command is required")
        argv, env = build_command(path, manifest, command)
        print(f"Dataset {manifest['dataset_id']}; resolved {manifest['resolved_at']}; manifest {path}", flush=True)
        return subprocess.run(argv, cwd=ROOT, env=env).returncode
    except (DatasetError, OSError, ValueError) as error:
        print(f"dataset-context: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

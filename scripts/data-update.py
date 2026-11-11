#!/usr/bin/env python3
"""Acquire, prepare and atomically select a complete immutable data edition."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import netrc
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from dataset import (ROOT, GROUPS, SCHEMA, DatasetError, activate, atomic_json, data_root,
                     digest, file_record, implementation_record, lock, redact, seal, utcnow, validate)
from data_sources import Sources
from data_http_policy import timestamp


ORDER = ("natural-earth", "orbital", "astronomy", "anthropocene", "resources",
         "atmosphere", "atoll", "network", "petroleum", "ocean", "ocean-context", "india")
DEPENDENCIES = {"astronomy": ("orbital",), "ocean-context": ("ocean", "resources"),
                "india": ("ocean-context",)}
# Context preparation updates the completed ocean source's config/products.
# A failed preparation must not leave that source checkpoint falsely trusted.
MUTATES = {"ocean-context": ("ocean",)}


class IncompleteUpdate(DatasetError):
    """Independent acquisition progressed, but required sources are pending."""


def preflight(root):
    subprocess.run(["bash", str(ROOT / "scripts/fetch-anthropocene-particulate-data.sh"),
                    "--check-credentials"], check=True, cwd=ROOT)
    if os.environ.get("ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY") == "1":
        raise DatasetError("A complete current dataset requires FIRMS; regional debugging uses the direct legacy fetch target")
    credentials = Path(os.environ.get("PTREE_NETRC", Path.home() / ".netrc"))
    if not credentials.is_file() or credentials.stat().st_mode & 0o077:
        raise DatasetError("A private PTREE_NETRC with configured P-Tree access is required before acquisition")
    if not netrc.netrc(credentials).authenticators("ftp.ptree.jaxa.jp"):
        raise DatasetError("PTREE_NETRC must configure ftp.ptree.jaxa.jp before acquisition")
    if not all(shutil.which(tool) for tool in ("bash", "curl", "jq", "rg", "gdalinfo", "make")):
        raise DatasetError("Native dependencies are missing; run make install-prerequisites")
    try:
        from osgeo import ogr
    except ImportError as error:
        raise DatasetError(f"GDAL Python bindings unavailable for {sys.executable}; "
                           "install python3-gdal for this interpreter (from osgeo import ogr): "
                           + redact(error)) from None
    for module in ("numpy", "scipy", "pandas", "geopandas", "lxml", "PIL", "matplotlib", "requests", "bs4"):
        __import__(module)
    from data_sources import local_input_paths
    for path in local_input_paths():
        if not path.exists():
            raise DatasetError("Missing configured local input before acquisition: " + str(path))
    subprocess.run(['make','--no-print-directory','DATASET=legacy','build/generate-native-swarm',
                    'build/validate-dataset-native'],cwd=ROOT,check=True,env={**os.environ,'CCACHE_DISABLE':'1'})
    existing = Path(root).resolve()
    while not existing.exists():
        existing = existing.parent
    minimum = float(os.environ.get("DATA_UPDATE_MIN_FREE_GIB", "160"))
    if minimum < 0:
        raise DatasetError("DATA_UPDATE_MIN_FREE_GIB must be nonnegative")
    free = shutil.disk_usage(existing).free / 1024**3
    print(f"Dataset storage: {free:.1f} GiB free; configured working-space budget {minimum:g} GiB", flush=True)
    if free < minimum:
        raise DatasetError("Insufficient dataset workspace; use DATA_ROOT on a larger filesystem or adjust DATA_UPDATE_MIN_FREE_GIB for a measured warm-cache run")


def update(root, *, requested_as_of, jobs=2, resume=None, adapters=None, candidate_only=False,
           validate_sources=None, keep_going=False, defer=()):
    deferred = set(defer)
    if deferred - set(ORDER):
        raise DatasetError('Unknown deferred source: ' + ', '.join(sorted(deferred - set(ORDER))))
    root = Path(root).resolve()
    implementation_paths=sorted({p for folder in ("scripts", "config", "src.generate", "src.projections")
                                             for p in (ROOT / folder).rglob("*")
                                             if p.is_file() and p.suffix in (".py", ".sh", ".cc", ".h", ".json")} |
                                            {ROOT / "Makefile", ROOT / "generation-style.json", ROOT / "generation-profile.json"})
    identity = implementation_record(implementation_paths)
    with lock(root):
        if resume:
            if not resume.replace("-", "").replace("_", "").isalnum():
                raise DatasetError("Invalid resume run ID")
            state_path = root / "runs" / resume / "state.json"
            state = json.loads(state_path.read_text())
            if state["status"] in ("active", "validated-candidate"):
                raise DatasetError("This run is already complete; build its manifest or start a new update")
            if state["implementation"] != identity:
                raise DatasetError("Update implementation changed; start a new run instead of mixing methods")
            requested_as_of = state["requested_as_of"]
        else:
            ident = datetime.fromisoformat(requested_as_of).strftime("%Y%m%dT%H%M%SZ").lower() + "-" + uuid.uuid4().hex[:12]
            state_path = root / "runs" / ident / "state.json"
            state = {"dataset_id": ident, "requested_as_of": requested_as_of, "implementation": identity,
                     "status": "preparing", "sources": [], "bindings": {}}
        edition = root / "editions" / state["dataset_id"]
        edition.mkdir(parents=True, exist_ok=True)
        source = Sources(edition, requested_as_of, root / "cache", jobs)
        source.records, source.bindings = state["sources"], state["bindings"]
        issues = {}
        state.update(status="preparing", current_source=None, issues=issues,
                     deferred_sources=sorted(deferred), keep_going=keep_going)
        state.pop('error', None)

        def checkpoint():
            state.update(sources=source.records, bindings=source.bindings, issues=issues)
            atomic_json(state_path, state)

        checkpoint()
        requested_display = timestamp(datetime.fromisoformat(requested_as_of).timestamp())
        print(f"Dataset run {state['dataset_id']}; requested as of {requested_display}", flush=True)
        try:
            for ident in ORDER:
                previous = next((record for record in source.records if record["id"] == ident), None)
                if previous:
                    expected = state.get("completed_files", {}).get(ident, [])
                    if not expected or any(not (edition / r["path"]).is_file()
                            or digest(edition / r["path"]) != r["sha256"] for r in expected):
                        raise DatasetError("Resume source bytes changed: " + ident)
                    print("Verified completed source " + ident, flush=True)
                    continue
                if ident in deferred:
                    issues[ident] = {"status": "deferred", "reason": "explicitly deferred for this invocation"}
                    print("Deferred " + ident + "; continuing independent sources", flush=True)
                    checkpoint()
                    continue
                complete = {record["id"] for record in source.records}
                missing = [dep for dep in DEPENDENCIES.get(ident, ()) if dep not in complete]
                if missing:
                    issues[ident] = {"status": "blocked", "dependencies": missing,
                                     "reason": "required source is incomplete: " + ", ".join(missing)}
                    print("Blocked " + ident + " by " + ", ".join(missing) + "; continuing independent sources", flush=True)
                    checkpoint()
                    continue
                print("Updating " + ident, flush=True)
                state['current_source'] = ident
                checkpoint()
                before_records, before_bindings = deepcopy(source.records), dict(source.bindings)
                try:
                    adapter = (adapters or {}).get(ident) or getattr(source, ident.replace("-", "_"), None)
                    if adapter is None:
                        raise DatasetError("No current-data adapter implemented for required source: " + ident)
                    adapter(source) if adapters and ident in adapters else adapter()
                    record = next((r for r in source.records if r["id"] == ident), None)
                    if record is None:
                        raise DatasetError("Source adapter did not produce a validation record: " + ident)
                    completed_files = {r["id"]: [file_record(edition, edition / path) for path in r["files"]]
                                       for r in source.records}
                except Exception as error:
                    source.records, source.bindings = before_records, before_bindings
                    for affected in MUTATES.get(ident, ()):
                        source.records = [r for r in source.records if r['id'] != affected]
                        state.get('completed_files', {}).pop(affected, None)
                        issues[affected] = {'status': 'invalidated',
                                            'reason': ident + ' changed shared inputs before failing; retry required'}
                    issues[ident] = {'status': 'failed', 'reason': redact(error)}
                    state['current_source'] = None
                    checkpoint()
                    if not keep_going:
                        raise
                    print('Source failed: ' + ident + ': ' + redact(error) +
                          '; completed work saved; continuing independent sources', file=sys.stderr, flush=True)
                    continue
                # Only declared shared-input preparation can revise an earlier
                # checkpoint. Never bless unexpected mutations by rehashing it.
                for prior in before_records:
                    previous_id = prior['id']
                    if previous_id in MUTATES.get(ident, ()):
                        continue
                    current = next((r for r in source.records if r['id'] == previous_id), None)
                    if (current != prior or completed_files.get(previous_id) !=
                            state.get('completed_files', {}).get(previous_id)):
                        source.records, source.bindings = before_records, before_bindings
                        raise DatasetError('Completed source changed unexpectedly during ' + ident + ': ' + previous_id)
                state['completed_files'] = completed_files
                state['current_source'] = None
                checkpoint()
            if implementation_record(implementation_paths) != identity:
                raise DatasetError('Implementation changed during acquisition; start a new run to keep method provenance consistent')
            pending = [ident for ident in ORDER if not any(r['id'] == ident for r in source.records)]
            if pending:
                state.update(status='incomplete', current_source=None,
                             error='Required sources pending: ' + ', '.join(pending))
                checkpoint()
                print(f"Incomplete run {state['dataset_id']}: {len(source.records)}/{len(ORDER)} sources saved; no edition selected", flush=True)
                for ident in pending:
                    issue = issues.get(ident, {'status':'pending', 'reason':'not completed'})
                    print(f"  {ident}: {issue['status']}; {issue['reason']}", flush=True)
                print(f"Continue with make data-update-resilient DATA_UPDATE_ARGS='--resume {state['dataset_id']}'", flush=True)
                raise IncompleteUpdate(state['error'])
            (validate_sources or source.validate_profiles)()
            if implementation_record(implementation_paths) != identity:
                raise DatasetError('Implementation changed during acquisition; start a new run to keep method provenance consistent')
            paths = sorted({p for record in source.records for p in record["files"]})
            manifest = seal({"schema": SCHEMA, "dataset_id": state["dataset_id"], "state": "validated",
                             "requested_as_of": requested_as_of, "resolved_at": utcnow(),
                             "product_groups": list(GROUPS), "implementation": identity,
                             "registry": json.loads((ROOT / "config/data-products.json").read_text()),
                             "products": json.loads((ROOT / "config/atlas-plates.json").read_text()),
                             "sources": source.records, "bindings": source.bindings,
                             "files": [file_record(edition, edition / path) for path in paths],
                             "validation": {"status": "passed", "checks": ["source-adapter-validation", "native-generator-loaders", "ocean-preparation-invariants", "all-input-hashes", "complete-product-bindings"]}})
            validate(manifest, edition)
            path = edition / "dataset.json"
            atomic_json(path, manifest)
            for row in manifest["files"]:
                (edition / row["path"]).chmod(0o444)
            path.chmod(0o444)
            state["status"] = "validated-candidate" if candidate_only else "active"
            atomic_json(state_path, state)
            # Commit the selection last, after the complete resumable journal
            # is durable. A journal write failure cannot advance current.
            if not candidate_only:
                activate(root, path)
            print(f"Dataset {state['dataset_id']}: {state['status']}; manifest {path}", flush=True)
            for record in source.records:
                print(f"  {record['id']}: {record['acquisition']}; {json.dumps(record['coverage'], sort_keys=True)}", flush=True)
            return path
        except IncompleteUpdate:
            raise
        except Exception as error:
            state.update(status="failed", error=redact(error))
            checkpoint()
            target = 'data-update-resilient' if keep_going else 'data-update'
            print(f"Failed run {state['dataset_id']}; state {state_path}; retry with make {target} DATA_UPDATE_ARGS='--resume {state['dataset_id']}'", file=sys.stderr)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=data_root())
    parser.add_argument("--as-of", default=os.environ.get("DATA_UPDATE_AS_OF", utcnow()))
    parser.add_argument("--jobs", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument("--resume")
    parser.add_argument("--candidate-only", action="store_true")
    parser.add_argument('--keep-going', action='store_true', help='save failures and continue independent sources; incomplete runs are not activated')
    parser.add_argument('--defer', action='append', default=[], choices=ORDER, metavar='SOURCE',
                        help='defer a required source for this invocation; repeatable; retry it on resume')
    args = parser.parse_args()
    try:
        requested = datetime.fromisoformat(args.as_of)
        if requested.utcoffset() is None or requested.utcoffset().total_seconds() != 0:
            raise DatasetError("--as-of must be an explicit UTC timestamp")
        preflight(args.root)
        update(args.root, requested_as_of=args.as_of, jobs=args.jobs, resume=args.resume,
               candidate_only=args.candidate_only, keep_going=args.keep_going, defer=args.defer)
        print("Next: make atlas-optional")
        return 0
    except Exception as error:
        print("data-update: " + redact(error) + "; previous active edition retained", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

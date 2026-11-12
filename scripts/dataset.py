"""Immutable local data editions shared by acquisition and visualization.

This module has no network or scientific-Python dependencies. Loading a
manifest checks every referenced byte before handing paths to a build.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cartofreako-dataset-v1"
GROUPS = ("standard", "atlas", "anthropocene-optional")
IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,159}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


class DatasetError(ValueError):
    pass


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def data_root():
    return Path(os.environ.get("DATA_ROOT", ROOT / ".cartofreako/data")).resolve()


def safe_path(root, relative):
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise DatasetError("Dataset paths must be nonempty relative paths")
    result = (root / relative).resolve()
    if not result.is_relative_to(root) or result == root:
        raise DatasetError(f"Dataset path escapes its edition: {relative}")
    return result


def file_record(root, path, role="input"):
    root, path = Path(root).resolve(), Path(path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise DatasetError(f"Input is not an edition file: {path}")
    return {"path": path.relative_to(root).as_posix(), "sha256": digest(path),
            "bytes": path.stat().st_size, "role": role}


def redact(message):
    value = str(message)
    for name in ("FIRMS_MAP_KEY", "OPENAQ_API_KEY", "XKDR_API_KEY", "AIRGRADIENT_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"(https?://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", value)
    return value


def implementation_record(paths):
    files = {str(Path(path).resolve().relative_to(ROOT)): digest(path) for path in paths}
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                              capture_output=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                            cwd=ROOT, text=True, capture_output=True, check=True).stdout
    return {"revision": revision, "dirty": bool(status), "files": files}


def validate(manifest, root, required_groups=GROUPS, *, verify_bytes=True):
    if manifest.get("schema") != SCHEMA or manifest.get("state") != "validated":
        raise DatasetError("A complete validated dataset manifest is required")
    ident = manifest.get("dataset_id", "")
    if not IDENTIFIER.fullmatch(ident):
        raise DatasetError("Invalid dataset ID")
    for name in ("requested_as_of", "resolved_at"):
        try:
            instant = datetime.fromisoformat(manifest[name])
            if instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0:
                raise ValueError("not UTC")
        except (KeyError, ValueError, TypeError) as error:
            raise DatasetError(f"Invalid UTC {name}") from error
    if not set(required_groups).issubset(manifest.get("product_groups", [])):
        raise DatasetError("Dataset does not cover the requested product groups")
    records = manifest.get("files", [])
    if not records or len({r.get("path") for r in records}) != len(records):
        raise DatasetError("Dataset files must be nonempty and unique")
    files = {}
    for record in records:
        path = safe_path(root, record.get("path"))
        if not HASH.fullmatch(record.get("sha256", "")) or not path.is_file():
            raise DatasetError(f"Missing or unpinned dataset file: {record.get('path')}")
        if path.stat().st_size != record.get("bytes") or (verify_bytes and digest(path) != record["sha256"]):
            raise DatasetError(f"Dataset checksum mismatch: {record['path']}")
        files[record["path"]] = path
    registry = manifest.get("registry")
    if not isinstance(registry, dict) or registry.get("schema") != "cartofreako-data-products-v1":
        raise DatasetError("Dataset must retain its product dependency registry")
    if not set(GROUPS).issubset(registry.get('groups',{})) or not registry.get('years'):
        raise DatasetError('Dataset product dependency registry is incomplete')
    products=manifest.get('products',{})
    if products.get('schema') != 'cartofreako-atlas-catalog-v1' or not products.get('plates'):
        raise DatasetError('Dataset must retain its product catalog')
    needed = {s for group in required_groups for s in registry["groups"][group]["sources"]}
    sources = manifest.get("sources", [])
    if len({s.get("id") for s in sources}) != len(sources):
        raise DatasetError("Dataset source IDs must be unique")
    by_id = {s["id"]: s for s in sources}
    for ident in needed:
        source = by_id.get(ident)
        if not source or source.get("status") != "validated" or not source.get("files"):
            raise DatasetError(f"Required source is incomplete: {ident}")
        if not isinstance(source.get('coverage'),dict) or not source['coverage']:
            raise DatasetError('Missing declared source coverage: '+ident)
        if source.get("acquisition") not in ("remote-checked", "policy-cache", "pinned-local", "historical-validation-only"):
            raise DatasetError(f"Source has no declared freshness policy: {ident}")
        for path in source["files"]:
            if path not in files:
                raise DatasetError(f"Unpinned source dependency: {ident}: {path}")
    bindings = manifest.get("bindings", {})
    for name in {b for group in required_groups for b in registry["groups"][group]["bindings"]}:
        if name not in bindings:
            raise DatasetError(f"Missing build binding: {name}")
    for name, relative in bindings.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            raise DatasetError("Invalid binding name")
        path = safe_path(root, relative)
        if not path.exists():
            raise DatasetError(f"Missing build binding path: {name}")
        if path.is_file() and relative not in files:
            raise DatasetError(f"Unpinned build binding: {name}")
        if path.is_dir() and not any(p.is_relative_to(path) for p in files.values()):
            raise DatasetError(f"Empty/unpinned build binding: {name}")
    validation = manifest.get("validation", {})
    if validation.get("status") != "passed" or not validation.get("checks"):
        raise DatasetError("Missing successful dataset validation receipt")
    fingerprint = dict(manifest)
    fingerprint.pop("manifest_sha256", None)
    if manifest.get("manifest_sha256") != hashlib.sha256(canonical(fingerprint)).hexdigest():
        raise DatasetError("Dataset manifest fingerprint mismatch")
    return manifest


def seal(manifest):
    result = dict(manifest)
    result.pop("manifest_sha256", None)
    result["manifest_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def load(path=None, required_groups=GROUPS, *, verify_bytes=True):
    path = Path(path or os.environ.get("DATASET_MANIFEST") or data_root() / "current.json").resolve()
    if not path.is_file():
        raise DatasetError("No active validated dataset. Run make data-update or select DATASET=legacy.")
    value = json.loads(path.read_text())
    if value.get("schema") == "cartofreako-dataset-pointer-v1":
        pointer_id=value.get('dataset_id')
        selected = safe_path(path.parent, value.get("manifest"))
        if not selected.is_file() or digest(selected) != value.get("sha256"):
            raise DatasetError("Current dataset pointer is incomplete or changed")
        path = selected
        value = json.loads(path.read_text())
        if value.get('dataset_id') != pointer_id:
            raise DatasetError('Current pointer and immutable dataset IDs differ')
    return path, validate(value, path.parent, required_groups, verify_bytes=verify_bytes)


@contextmanager
def lock(root, name="update"):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / (name + ".lock")).open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise DatasetError(f"Another {name} is already running under {root}") from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def activate(root, manifest_path):
    root, manifest_path = Path(root).resolve(), Path(manifest_path).resolve()
    value = validate(json.loads(manifest_path.read_text()), manifest_path.parent)
    if not manifest_path.is_relative_to(root / "editions"):
        raise DatasetError("Only finalized editions can be activated")
    with lock(root, "activation"):
        atomic_json(root / "current.json", {"schema": "cartofreako-dataset-pointer-v1",
                    "dataset_id": value["dataset_id"], "manifest": manifest_path.relative_to(root).as_posix(),
                    "sha256": digest(manifest_path), "activated_at": utcnow()})


@lru_cache(maxsize=4)
def _immutable_context(path):
    verified_parent = (os.environ.get("DATASET_BOUND") == "1" and
                       os.environ.get("DATASET_MANIFEST_SHA256") == digest(path))
    selected, manifest = load(path, verify_bytes=not verified_parent)
    if selected != Path(path).resolve():
        raise DatasetError("Build contexts must bind an immutable manifest, not the current pointer")
    return selected, manifest


def context(required=True):
    path = os.environ.get("DATASET_MANIFEST")
    if not path:
        if required:
            raise DatasetError("A frozen DATASET_MANIFEST is required for a current-data build")
        return None
    return _immutable_context(path)


def binding(name, default=None):
    selected = context(required=False)
    if selected is None:
        return default
    path, manifest = selected
    if name not in manifest["bindings"]:
        raise DatasetError(f"Dataset does not bind {name}")
    return safe_path(path.parent, manifest["bindings"][name])


def output(name, default=None):
    selected = context(required=False)
    if selected is None:
        return default
    _, manifest = selected
    base = working_output(manifest)
    selected_output = Path(os.environ.get('DATASET_OUTPUT_ROOT', base)).resolve()
    allowed = (base, data_root()/'render-runs'/manifest['dataset_id'],
               ROOT/'output/data-editions'/manifest['dataset_id'])
    if not any(selected_output.is_relative_to(p.resolve()) for p in allowed):
        raise DatasetError('Build output must stay inside its dataset edition directory')
    return selected_output / name


def working_output(manifest):
    return data_root()/'render-work'/manifest['dataset_id']


def delivery_output(manifest):
    """Use the dataset's UTC as-of date, independent of render date/timezone."""
    day = datetime.fromisoformat(manifest['requested_as_of']).strftime('%Y%m%d')
    return ROOT/'output/data-edition'/day


def run_output(manifest, build_id, *, existing=False):
    if not IDENTIFIER.fullmatch(build_id):
        raise DatasetError('Invalid build ID')
    path = data_root()/'render-runs'/manifest['dataset_id']/build_id
    legacy = ROOT/'output/data-editions'/manifest['dataset_id']/'builds'/build_id
    return legacy if existing and not path.exists() and legacy.exists() else path


def publish_output(base, manifest, build_id):
    """Atomically expose a completed run at the short, date-based delivery path."""
    base = Path(base).resolve()
    receipt = base/'validation/full-build.json'
    value = json.loads(receipt.read_text())
    if value.get('status') != 'passed' or value.get('dataset_id') != manifest['dataset_id'] or value.get('build_id') != build_id:
        raise DatasetError('Only a validated complete build can be published')
    public = delivery_output(manifest)
    public.parent.mkdir(parents=True, exist_ok=True)
    # Replacing a managed symlink is atomic; never displace a user's directory.
    if public.exists() and not public.is_symlink():
        raise DatasetError('Delivery path is an existing directory: '+str(public))
    temporary = public.with_name('.'+public.name+'-'+build_id)
    temporary.symlink_to(os.path.relpath(base, public.parent), target_is_directory=True)
    try:
        os.replace(temporary, public)
    finally:
        temporary.unlink(missing_ok=True)
    pointer = {'dataset_id':manifest['dataset_id'], 'build_id':build_id,
               'output':str(public), 'storage_output':str(base),
               'receipt':str(public/'validation/full-build.json'), 'sha256':digest(receipt)}
    atomic_json(data_root()/'build-current.json', pointer)
    return public

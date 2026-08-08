#!/usr/bin/env python3

"""Build a validated, cleaned union of two submarine-cable snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "cartofreako-fiber-synthesized-v1"
LICENSE = "CC BY-NC-SA 3.0 Unported"
REPOSITORY = "https://github.com/telegeography/www.submarinecablemap.com"
SAFE_ID = re.compile(r"^[a-z0-9-]+$")


class SynthesisError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SynthesisError(message)


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise SynthesisError(f"cannot read JSON {path}: {error}") from error


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise SynthesisError(f"cannot hash {path}: {error}") from error
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalized_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    return "".join(character for character in decomposed if character.isalnum())


def normalized_name_tokens(value: str) -> set[str]:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    return {
        token for token in re.findall(r"[a-z0-9]+", decomposed)
        if len(token) >= 3
    }


def validate_identifier(value: Any, context: str) -> str:
    require(isinstance(value, str) and SAFE_ID.fullmatch(value) is not None,
            f"{context} is not a safe identifier")
    return value


def validate_point(value: Any, context: str) -> list[float]:
    require(isinstance(value, list) and len(value) == 2,
            f"{context} must be a two-number coordinate")
    longitude, latitude = value
    require(
        isinstance(longitude, (int, float))
        and not isinstance(longitude, bool)
        and isinstance(latitude, (int, float))
        and not isinstance(latitude, bool),
        f"{context} must contain numbers",
    )
    require(-180 <= longitude <= 180 and -90 <= latitude <= 90,
            f"{context} is outside geographic bounds")
    return [float(longitude), float(latitude)]


def validate_all_json(root: Path) -> int:
    paths = sorted(root.rglob("*.json"))
    require(paths, f"snapshot contains no JSON files: {root}")
    for path in paths:
        load_json(path)
    return len(paths)


def combined_detail_digest(detail_paths: dict[str, Path]) -> str:
    digest = hashlib.sha256()
    for identifier in sorted(detail_paths):
        line = f"{sha256_file(detail_paths[identifier])}  {identifier}.json\n"
        digest.update(line.encode("utf-8"))
    return digest.hexdigest()


@dataclass(frozen=True)
class Snapshot:
    label: str
    root: Path
    routes_path: Path
    landings_path: Path
    route_collection: dict[str, Any]
    landing_collection: dict[str, Any]
    routes_by_system: dict[str, list[dict[str, Any]]]
    route_features_by_id: dict[str, dict[str, Any]]
    systems: dict[str, dict[str, Any]]
    landings: dict[str, dict[str, Any]]
    detail_paths: dict[str, Path]
    json_file_count: int
    route_parts: int
    route_vertices: int
    missing_landing_details: tuple[str, ...]
    extra_landing_details: tuple[str, ...]
    unreferenced_landings: tuple[str, ...]

    def source_summary(self) -> dict[str, Any]:
        return {
            "snapshot": self.label,
            "source_subdirectory": self.root.name,
            "json_file_count": self.json_file_count,
            "systems": len(self.systems),
            "planned_systems": sum(
                1 for system in self.systems.values() if system["is_planned"]
            ),
            "route_features": len(self.route_features_by_id),
            "route_parts": self.route_parts,
            "route_vertices": self.route_vertices,
            "landings": len(self.landings),
            "routes_sha256": sha256_file(self.routes_path),
            "landings_sha256": sha256_file(self.landings_path),
            "details_sha256": combined_detail_digest(self.detail_paths),
            "missing_standalone_landing_details": list(
                self.missing_landing_details
            ),
            "extra_standalone_landing_details": list(
                self.extra_landing_details
            ),
            "aggregate_landings_without_cable_reference": list(
                self.unreferenced_landings
            ),
        }


def validate_snapshot(root: Path, label: str) -> Snapshot:
    require(root.is_dir(), f"snapshot directory does not exist: {root}")
    json_file_count = validate_all_json(root)
    routes_path = root / "cable" / "cable-geo.json"
    landings_path = root / "landing-point" / "landing-point-geo.json"
    all_path = root / "cable" / "all.json"
    route_collection = load_json(routes_path)
    landing_collection = load_json(landings_path)
    cable_index = load_json(all_path)

    require(
        isinstance(route_collection, dict)
        and route_collection.get("type") == "FeatureCollection"
        and isinstance(route_collection.get("features"), list)
        and route_collection["features"],
        f"{routes_path} must be a nonempty FeatureCollection",
    )
    require(
        isinstance(landing_collection, dict)
        and landing_collection.get("type") == "FeatureCollection"
        and isinstance(landing_collection.get("features"), list)
        and landing_collection["features"],
        f"{landings_path} must be a nonempty FeatureCollection",
    )
    require(isinstance(cable_index, list) and cable_index,
            f"{all_path} must be a nonempty array")

    routes_by_system: dict[str, list[dict[str, Any]]] = {}
    route_features_by_id: dict[str, dict[str, Any]] = {}
    route_parts = 0
    route_vertices = 0
    for index, feature in enumerate(route_collection["features"]):
        context = f"{routes_path}.features[{index}]"
        require(isinstance(feature, dict) and feature.get("type") == "Feature",
                f"{context} must be a Feature")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        require(isinstance(properties, dict), f"{context}.properties is invalid")
        require(isinstance(geometry, dict)
                and geometry.get("type") == "MultiLineString",
                f"{context}.geometry must be MultiLineString")
        system_id = validate_identifier(properties.get("id"),
                                        f"{context}.properties.id")
        feature_id = validate_identifier(properties.get("feature_id"),
                                         f"{context}.properties.feature_id")
        require(isinstance(properties.get("name"), str)
                and properties["name"], f"{context}.properties.name is invalid")
        require(isinstance(properties.get("color"), str)
                and properties["color"], f"{context}.properties.color is invalid")
        require(feature_id not in route_features_by_id,
                f"{routes_path} repeats feature_id {feature_id}")
        lines = geometry.get("coordinates")
        require(isinstance(lines, list) and lines,
                f"{context}.geometry.coordinates is empty")
        for line_index, line in enumerate(lines):
            require(isinstance(line, list) and len(line) >= 2,
                    f"{context} route part {line_index} is too short")
            for point_index, point in enumerate(line):
                validate_point(
                    point,
                    f"{context}.geometry.coordinates[{line_index}]"
                    f"[{point_index}]",
                )
                route_vertices += 1
            route_parts += 1
        route_features_by_id[feature_id] = feature
        routes_by_system.setdefault(system_id, []).append(feature)

    index_ids: list[str] = []
    for index, item in enumerate(cable_index):
        require(isinstance(item, dict), f"{all_path}[{index}] is not an object")
        identifier = validate_identifier(item.get("id"),
                                         f"{all_path}[{index}].id")
        require(isinstance(item.get("name"), str) and item["name"],
                f"{all_path}[{index}].name is invalid")
        index_ids.append(identifier)
    require(len(index_ids) == len(set(index_ids)),
            f"{all_path} repeats cable ids")
    require(set(index_ids) == set(routes_by_system),
            f"{all_path} ids do not exactly match routed cable ids")

    detail_paths: dict[str, Path] = {}
    systems: dict[str, dict[str, Any]] = {}
    referenced_landings: set[str] = set()
    for system_id in sorted(routes_by_system):
        detail_path = root / "cable" / f"{system_id}.json"
        detail = load_json(detail_path)
        context = str(detail_path)
        require(isinstance(detail, dict), f"{context} must be an object")
        require(detail.get("id") == system_id,
                f"{context} id does not match its filename")
        require(isinstance(detail.get("name"), str) and detail["name"],
                f"{context}.name is invalid")
        require(isinstance(detail.get("is_planned"), bool),
                f"{context}.is_planned is invalid")
        rfs_year = detail.get("rfs_year")
        require(
            rfs_year is None
            or (isinstance(rfs_year, int) and not isinstance(rfs_year, bool)),
            f"{context}.rfs_year is invalid",
        )
        landing_values = detail.get("landing_points")
        require(isinstance(landing_values, list),
                f"{context}.landing_points is invalid")
        landing_ids: list[str] = []
        for landing_index, landing in enumerate(landing_values):
            require(isinstance(landing, dict),
                    f"{context}.landing_points[{landing_index}] is invalid")
            landing_id = validate_identifier(
                landing.get("id"),
                f"{context}.landing_points[{landing_index}].id",
            )
            landing_ids.append(landing_id)
            referenced_landings.add(landing_id)
        require(len(landing_ids) == len(set(landing_ids)),
                f"{context} repeats landing ids")
        stored = dict(detail)
        stored["landing_ids"] = sorted(landing_ids)
        systems[system_id] = stored
        detail_paths[system_id] = detail_path

    landings: dict[str, dict[str, Any]] = {}
    for index, feature in enumerate(landing_collection["features"]):
        context = f"{landings_path}.features[{index}]"
        require(isinstance(feature, dict) and feature.get("type") == "Feature",
                f"{context} must be a Feature")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        require(isinstance(properties, dict), f"{context}.properties is invalid")
        landing_id = validate_identifier(properties.get("id"),
                                         f"{context}.properties.id")
        require(landing_id not in landings,
                f"{landings_path} repeats landing id {landing_id}")
        require(isinstance(properties.get("name"), str)
                and properties["name"], f"{context}.properties.name is invalid")
        require(isinstance(properties.get("is_tbd"), bool),
                f"{context}.properties.is_tbd is invalid")
        require(isinstance(geometry, dict) and geometry.get("type") == "Point",
                f"{context}.geometry must be Point")
        validate_point(geometry.get("coordinates"),
                       f"{context}.geometry.coordinates")
        landings[landing_id] = feature

    unknown_landings = sorted(referenced_landings - set(landings))
    require(not unknown_landings,
            f"{label} cable details reference unknown landings: "
            + ", ".join(unknown_landings))

    landing_detail_paths = {
        path.stem: path
        for path in (root / "landing-point").glob("*.json")
        if path.name != "landing-point-geo.json"
    }
    missing_landing_details = tuple(sorted(set(landings) - set(landing_detail_paths)))
    extra_landing_details = tuple(sorted(set(landing_detail_paths) - set(landings)))
    for identifier, path in sorted(landing_detail_paths.items()):
        detail = load_json(path)
        require(isinstance(detail, dict) and detail.get("id") == identifier,
                f"{path} id does not match its filename")

    for system_id, features in routes_by_system.items():
        features.sort(key=lambda feature: feature["properties"]["feature_id"])
        require(system_id in systems, f"{label} route has no system {system_id}")

    return Snapshot(
        label=label,
        root=root,
        routes_path=routes_path,
        landings_path=landings_path,
        route_collection=route_collection,
        landing_collection=landing_collection,
        routes_by_system=routes_by_system,
        route_features_by_id=route_features_by_id,
        systems=systems,
        landings=landings,
        detail_paths=detail_paths,
        json_file_count=json_file_count,
        route_parts=route_parts,
        route_vertices=route_vertices,
        missing_landing_details=missing_landing_details,
        extra_landing_details=extra_landing_details,
        unreferenced_landings=tuple(sorted(set(landings) - referenced_landings)),
    )


def system_observation(snapshot: Snapshot, identifier: str) -> dict[str, Any]:
    detail = snapshot.systems[identifier]
    geometries = [
        feature["geometry"] for feature in snapshot.routes_by_system[identifier]
    ]
    return {
        "id": identifier,
        "name": detail["name"],
        "is_planned": detail["is_planned"],
        "rfs": detail.get("rfs"),
        "rfs_year": detail.get("rfs_year"),
        "landing_ids": detail["landing_ids"],
        "route_feature_count": len(snapshot.routes_by_system[identifier]),
        "geometry_sha256": canonical_digest(sorted(
            geometries,
            key=lambda geometry: json.dumps(
                geometry, sort_keys=True, separators=(",", ":")
            ),
        )),
        "detail_sha256": sha256_file(snapshot.detail_paths[identifier]),
    }


def transition(old: dict[str, Any], new: dict[str, Any]) -> str:
    if old["is_planned"] and not new["is_planned"]:
        return "planned-to-active"
    if not old["is_planned"] and new["is_planned"]:
        return "active-to-planned"
    if old["is_planned"]:
        return "retained-planned"
    return "retained-active"


def compare_systems(old: Snapshot, new: Snapshot) -> tuple[
    list[dict[str, Any]], dict[str, str], dict[str, str]
]:
    old_ids = set(old.systems)
    new_ids = set(new.systems)
    pairs: list[tuple[str, str, str]] = [
        (identifier, identifier, "stable-id")
        for identifier in sorted(old_ids & new_ids)
    ]
    old_only = old_ids - new_ids
    new_only = new_ids - old_ids

    old_names: dict[str, list[str]] = {}
    new_names: dict[str, list[str]] = {}
    for identifier in sorted(old_only):
        old_names.setdefault(normalized_name(old.systems[identifier]["name"]), []).append(
            identifier
        )
    for identifier in sorted(new_only):
        new_names.setdefault(normalized_name(new.systems[identifier]["name"]), []).append(
            identifier
        )
    for name in sorted(set(old_names) & set(new_names)):
        if name and len(old_names[name]) == 1 and len(new_names[name]) == 1:
            old_id = old_names[name][0]
            new_id = new_names[name][0]
            pairs.append((old_id, new_id, "unique-normalized-name"))
            old_only.remove(old_id)
            new_only.remove(new_id)

    # A cable's landing set is a strong topology identity signal. Use it only
    # when the exact nonempty set occurs once in each complete snapshot and
    # the names retain a normalized token of at least three characters. This
    # rejects unrelated replacements on the same corridor and keeps the
    # evidence bounded and auditable rather than generally fuzzy.
    old_landing_sets: dict[tuple[str, ...], list[str]] = {}
    new_landing_sets: dict[tuple[str, ...], list[str]] = {}
    for identifier, system in old.systems.items():
        old_landing_sets.setdefault(
            tuple(system["landing_ids"]), []
        ).append(identifier)
    for identifier, system in new.systems.items():
        new_landing_sets.setdefault(
            tuple(system["landing_ids"]), []
        ).append(identifier)
    for landing_set in sorted(set(old_landing_sets) & set(new_landing_sets)):
        if (
            landing_set
            and len(old_landing_sets[landing_set]) == 1
            and len(new_landing_sets[landing_set]) == 1
        ):
            old_id = old_landing_sets[landing_set][0]
            new_id = new_landing_sets[landing_set][0]
            shared_name_tokens = (
                normalized_name_tokens(old.systems[old_id]["name"])
                & normalized_name_tokens(new.systems[new_id]["name"])
            )
            if (
                old_id in old_only
                and new_id in new_only
                and shared_name_tokens
            ):
                pairs.append((
                    old_id, new_id, "unique-exact-landing-set"
                ))
                old_only.remove(old_id)
                new_only.remove(new_id)

    records: list[dict[str, Any]] = []
    old_map: dict[str, str] = {}
    new_map: dict[str, str] = {}
    for old_id, new_id, match_class in sorted(
        pairs, key=lambda item: (item[1], item[0])
    ):
        old_observation = system_observation(old, old_id)
        new_observation = system_observation(new, new_id)
        comparison_id = new_id
        old_map[old_id] = comparison_id
        new_map[new_id] = comparison_id
        records.append({
            "comparison_id": comparison_id,
            "snapshot_membership": "both",
            "match": {
                "class": match_class,
                "confidence": (
                    "strong"
                    if match_class == "unique-exact-landing-set"
                    else "exact"
                ),
                old.label: old_id,
                new.label: new_id,
            },
            "temporal_class": transition(old_observation, new_observation),
            "change_flags": {
                "identifier_changed": old_id != new_id,
                "name_changed": old_observation["name"] != new_observation["name"],
                "planned_state_changed": (
                    old_observation["is_planned"]
                    != new_observation["is_planned"]
                ),
                "rfs_year_changed": (
                    old_observation["rfs_year"] != new_observation["rfs_year"]
                ),
                "landing_set_changed": (
                    old_observation["landing_ids"]
                    != new_observation["landing_ids"]
                ),
                "geometry_changed": (
                    old_observation["geometry_sha256"]
                    != new_observation["geometry_sha256"]
                ),
            },
            "observations": {
                old.label: old_observation,
                new.label: new_observation,
            },
        })

    for identifier in sorted(old_only):
        comparison_id = f"{old.label}:{identifier}"
        old_map[identifier] = comparison_id
        records.append({
            "comparison_id": comparison_id,
            "snapshot_membership": f"{old.label}-only",
            "match": {
                "class": "unmatched",
                "confidence": "none",
                old.label: identifier,
                new.label: None,
            },
            "temporal_class": "not-comparable",
            "change_flags": None,
            "observations": {
                old.label: system_observation(old, identifier),
                new.label: None,
            },
        })
    for identifier in sorted(new_only):
        comparison_id = f"{new.label}:{identifier}"
        new_map[identifier] = comparison_id
        records.append({
            "comparison_id": comparison_id,
            "snapshot_membership": f"{new.label}-only",
            "match": {
                "class": "unmatched",
                "confidence": "none",
                old.label: None,
                new.label: identifier,
            },
            "temporal_class": "not-comparable",
            "change_flags": None,
            "observations": {
                old.label: None,
                new.label: system_observation(new, identifier),
            },
        })
    records.sort(key=lambda record: record["comparison_id"])
    return records, old_map, new_map


def route_comparison(
    snapshot: Snapshot,
    comparison_map: dict[str, str],
    records: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for feature_id, source in sorted(snapshot.route_features_by_id.items()):
        properties = dict(source["properties"])
        system_id = properties["id"]
        comparison_id = comparison_map[system_id]
        record = records[comparison_id]
        properties.update({
            "source_snapshot": snapshot.label,
            "source_system_id": system_id,
            "source_feature_id": feature_id,
            "comparison_id": comparison_id,
            "snapshot_membership": record["snapshot_membership"],
            "match_class": record["match"]["class"],
            "temporal_class": record["temporal_class"],
            "source_is_planned": snapshot.systems[system_id]["is_planned"],
            "source_rfs_year": snapshot.systems[system_id].get("rfs_year"),
        })
        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": source["geometry"],
        })
    return features


def landing_comparison(old: Snapshot, new: Snapshot) -> list[dict[str, Any]]:
    old_ids = set(old.landings)
    new_ids = set(new.landings)
    features: list[dict[str, Any]] = []
    for snapshot in (old, new):
        for identifier, source in sorted(snapshot.landings.items()):
            if identifier in old_ids and identifier in new_ids:
                membership = "both"
                old_feature = old.landings[identifier]
                new_feature = new.landings[identifier]
                coordinate_changed = (
                    old_feature["geometry"]["coordinates"]
                    != new_feature["geometry"]["coordinates"]
                )
                name_changed = (
                    old_feature["properties"]["name"]
                    != new_feature["properties"]["name"]
                )
            else:
                membership = f"{snapshot.label}-only"
                coordinate_changed = None
                name_changed = None
            properties = dict(source["properties"])
            properties.update({
                "source_snapshot": snapshot.label,
                "source_landing_id": identifier,
                "snapshot_membership": membership,
                "coordinate_changed_between_snapshots": coordinate_changed,
                "name_changed_between_snapshots": name_changed,
            })
            features.append({
                "type": "Feature",
                "properties": properties,
                "geometry": source["geometry"],
            })
    return features


def encoded_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with temporary.open("wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise SynthesisError(f"cannot write {path}: {error}") from error


def synthesize(
    old: Snapshot,
    new: Snapshot,
    output_directory: Path,
    repository_commit: str,
) -> dict[str, Any]:
    records, old_map, new_map = compare_systems(old, new)
    record_map = {record["comparison_id"]: record for record in records}
    route_observations = (
        route_comparison(old, old_map, record_map)
        + route_comparison(new, new_map, record_map)
    )
    landing_observations = landing_comparison(old, new)

    # The cleaned union selects the complete newer snapshot, then adds only
    # unmatched older observations. Matched older geometry remains available
    # in the observation files for audit, but is not rendered twice.
    routes = {
        "type": "FeatureCollection",
        "schema": SCHEMA,
        "kind": "cleaned-union",
        "default_snapshot": new.label,
        "features": [
            feature for feature in route_observations
            if feature["properties"]["source_snapshot"] == new.label
            or feature["properties"]["snapshot_membership"]
               == f"{old.label}-only"
        ],
    }
    landings = {
        "type": "FeatureCollection",
        "schema": SCHEMA,
        "kind": "cleaned-union",
        "default_snapshot": new.label,
        "features": [
            feature for feature in landing_observations
            if feature["properties"]["source_snapshot"] == new.label
            or feature["properties"]["snapshot_membership"]
               == f"{old.label}-only"
        ],
    }
    route_observation_document = {
        "type": "FeatureCollection",
        "schema": SCHEMA,
        "kind": "source-separated-observations",
        "default_snapshot": new.label,
        "features": route_observations,
    }
    landing_observation_document = {
        "type": "FeatureCollection",
        "schema": SCHEMA,
        "kind": "source-separated-observations",
        "default_snapshot": new.label,
        "features": landing_observations,
    }
    systems_document = {
        "schema": SCHEMA,
        "kind": "cleaned-union-with-source-separated-observations",
        "default_snapshot": new.label,
        "snapshots": [old.label, new.label],
        "systems": records,
    }

    readme = f"""# Fiber synthesized static dataset

This directory is a validated cleanup and union of the TeleGeography
submarine-cable API snapshots `{old.label}` and `{new.label}`. It is not the
set difference `new - old`; `assets.static/fiber-evolution` remains reserved
for a future strict difference dataset.

The default rendered layer is `{new.label}`. The cleaned union contains every
newer observation plus only unmatched `{old.label}`-only observations, so
matched older geometry is not drawn twice. The source-separated observation
files retain both inputs for audit.

- `routes.geojson`: cleaned union used by the standard generation pass
- `landings.geojson`: cleaned-union landing points
- `systems.json`: identity evidence, matches, and snapshot-only classifications
- `route-observations.geojson`: both source route observations
- `landing-observations.geojson`: both source landing observations
- `manifest.json`: source pins, counts, policies, caveats, and payload hashes
- `SHA256SUMS`: integrity list for this directory

The union has {len(records)} comparison identities, {len(routes['features'])}
route features, and {len(landings['features'])} landing features. A label such
as `{old.label}-only` or `{new.label}-only` records snapshot membership only;
it does not prove construction or decommission.

Source map data is licensed CC BY-NC-SA 3.0 Unported. Generated artifacts
retain that license boundary.
"""

    payloads = {
        "README.md": readme.encode("utf-8"),
        "systems.json": encoded_json(systems_document),
        "routes.geojson": encoded_json(routes),
        "landings.geojson": encoded_json(landings),
        "route-observations.geojson": encoded_json(
            route_observation_document
        ),
        "landing-observations.geojson": encoded_json(
            landing_observation_document
        ),
    }
    for name, content in payloads.items():
        write_atomic(output_directory / name, content)

    match_counts = Counter(record["match"]["class"] for record in records)
    membership_counts = Counter(record["snapshot_membership"] for record in records)
    temporal_counts = Counter(record["temporal_class"] for record in records)
    output_descriptions = {}
    for name in sorted(payloads):
        path = output_directory / name
        output_descriptions[name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    output_descriptions["routes.geojson"]["features"] = len(routes["features"])
    output_descriptions["landings.geojson"]["features"] = len(
        landings["features"]
    )
    output_descriptions["systems.json"]["systems"] = len(records)

    manifest = {
        "schema": SCHEMA,
        "kind": "cleaned-union-with-source-separated-observations",
        "default_snapshot": new.label,
        "license": LICENSE,
        "source_repository": REPOSITORY,
        "source_checkout_head": repository_commit,
        "snapshot_paths_tracked_by_checkout_head": False,
        "sources": [old.source_summary(), new.source_summary()],
        "matching_policy": {
            "authoritative_pairs": [
                "identical safe cable id",
                "unique exact normalized cable name",
                "unique exact nonempty landing-id set across both complete snapshots plus a shared normalized name token (strong topology evidence)",
            ],
            "unmatched_policy": (
                "retain as snapshot-only; do not infer construction, "
                "decommission, or identity"
            ),
            "geometry_policy": (
                "preserve each source geometry as a separate feature; "
                "never interpolate or average coordinates"
            ),
            "cleaned_union_policy": (
                f"select every {new.label} observation and add only "
                f"unmatched {old.label}-only observations; retain matched "
                "older observations in audit files without rendering them "
                "twice"
            ),
        },
        "summary": {
            "comparison_systems": len(records),
            "match_classes": dict(sorted(match_counts.items())),
            "snapshot_memberships": dict(sorted(membership_counts.items())),
            "temporal_classes": dict(sorted(temporal_counts.items())),
            "cleaned_union_route_features": len(routes["features"]),
            "cleaned_union_landing_features": len(landings["features"]),
            "source_observation_route_features": len(route_observations),
            "source_observation_landing_features": len(
                landing_observations
            ),
        },
        "known_source_quirks": [
            {
                "snapshot": source.label,
                "missing_standalone_landing_details": list(
                    source.missing_landing_details
                ),
                "disposition": (
                    "benign: the aggregate landing FeatureCollection and "
                    "all cable-to-landing references validate; the renderer "
                    "does not consume standalone landing detail files"
                ),
            }
            for source in (old, new)
            if source.missing_landing_details
        ],
        "caveats": [
            "Snapshot-only means identifier observation in only one source snapshot; it does not prove physical construction or decommission.",
            "Unique normalized-name pairing is exact but remains an identity assertion limited to this comparison dataset.",
            "Unique exact landing-set pairing also requires a shared normalized name token; it is strong topology evidence, not proof that a cable was merely renamed.",
            "Internet-exchange membership is outside this cable-only synthesis.",
        ],
        "outputs": output_descriptions,
    }
    write_atomic(output_directory / "manifest.json", encoded_json(manifest))

    checksum_names = sorted([*payloads, "manifest.json"])
    checksums = "".join(
        f"{sha256_file(output_directory / name)}  {name}\n"
        for name in checksum_names
    ).encode("utf-8")
    write_atomic(output_directory / "SHA256SUMS", checksums)
    return manifest


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path,
                        help="older dated API snapshot directory")
    parser.add_argument("--new", required=True, type=Path,
                        help="newer dated API snapshot directory")
    parser.add_argument("--old-label", default="v3.2022")
    parser.add_argument("--new-label", default="v3.20260805")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository-commit", required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        require(
            re.fullmatch(r"[0-9a-f]{40}", arguments.repository_commit)
            is not None,
            "--repository-commit must be a lowercase 40-digit Git SHA-1",
        )
        old = validate_snapshot(arguments.old.resolve(), arguments.old_label)
        new = validate_snapshot(arguments.new.resolve(), arguments.new_label)
        require(old.label != new.label, "snapshot labels must differ")
        manifest = synthesize(
            old, new, arguments.output.resolve(), arguments.repository_commit
        )
        summary = manifest["summary"]
        print(
            "submarine-cable cleaned union prepared: "
            f"{summary['comparison_systems']} systems, "
            f"{summary['cleaned_union_route_features']} union routes, "
            f"{summary['cleaned_union_landing_features']} union landings"
        )
        print(f"output: {arguments.output.resolve()}")
        return 0
    except SynthesisError as error:
        print(f"submarine-cable synthesis: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

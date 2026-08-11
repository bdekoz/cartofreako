#!/usr/bin/env python3
"""Validate the approved, exploration-only Stage 15 contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> object:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate(schema_path: str, instance_path: str) -> dict:
    schema = load(schema_path)
    instance = load(instance_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)
    assert isinstance(instance, dict)
    return instance


def validate_instance(schema_path: str, instance: object) -> None:
    schema = load(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        header = source.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert header[12:16] == b"IHDR"
    return struct.unpack(">II", header[16:24])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu-controls", action="store_true")
    arguments = parser.parse_args()

    gpu = validate(
        "contracts/gpu-benchmark-v1.schema.json",
        "fixtures/gpu-benchmark/v1/stage-14-inputs.json",
    )
    assert gpu["documentType"] == "input-freeze"
    assert gpu["lifecycle"] == "exploration-only"
    assert gpu["frozenStage14"]["workingTree"] == "clean"
    assert gpu["frozenStage14"]["artifactCount"] == len(gpu["cases"]) == 205
    assert len({case["passId"] for case in gpu["cases"]}) == 31
    assert len({case["layoutId"] for case in gpu["cases"]}) == 11
    assert sum(case["sliceId"] is not None for case in gpu["cases"]) == 14

    # Exercise the future run-result branch without recording a measurement.
    # Every value is an explicit schema sentinel and status is unsupported.
    null_timing = {"cold": None, "warmMedian": None, "warmP95": None}
    validate_instance("contracts/gpu-benchmark-v1.schema.json", {
        "schemaVersion": "cartofreako-gpu-benchmark-v1",
        "documentType": "run-result",
        "lifecycle": "exploration-only",
        "inputFreeze": {
            "path": "fixtures/gpu-benchmark/v1/stage-14-inputs.json",
            "sha256": sha256(ROOT / "fixtures/gpu-benchmark/v1/stage-14-inputs.json"),
            "sourceCommit": gpu["frozenStage14"]["sourceCommit"],
            "artifactCount": 205,
        },
        "environment": {
            "machineId": "SCHEMA-SENTINEL-NOT-A-MEASUREMENT",
            "cpu": "UNAVAILABLE",
            "memoryBytes": 1,
            "gpu": "UNAVAILABLE",
            "driver": "UNAVAILABLE",
            "operatingSystem": "UNAVAILABLE",
            "runtime": "UNAVAILABLE",
            "runtimeVersion": "UNAVAILABLE",
            "browser": "UNAVAILABLE",
            "displayMode": "UNAVAILABLE",
            "headless": True,
            "powerProfile": "UNAVAILABLE",
            "availableMemoryBytes": 0,
            "softwareRendering": False,
            "toolchain": [],
        },
        "runPolicy": {
            "warmups": 0,
            "repetitions": 1,
            "coldAndWarm": True,
            "statistics": ["median"],
        },
        "results": [{
            "caseId": gpu["cases"][0]["id"],
            "productId": "schema-sentinel",
            "status": "unsupported",
            "encoding": {
                "format": "UNAVAILABLE",
                "encoder": "UNAVAILABLE",
                "encoderVersion": "UNAVAILABLE",
                "decoder": "UNAVAILABLE",
                "decoderVersion": "UNAVAILABLE",
                "options": [],
                "colorSpace": "UNAVAILABLE",
                "alphaMode": "UNAVAILABLE",
                "mipPolicy": "UNAVAILABLE",
                "determinism": "UNAVAILABLE",
                "encodedSha256": None,
            },
            "observations": {
                "encodedBytes": None,
                "compressionRatio": None,
                "encodeMilliseconds": null_timing,
                "cpuDecodeMilliseconds": null_timing,
                "gpuUploadMilliseconds": null_timing,
                "firstUsableFrameMilliseconds": null_timing,
                "peakHostMemoryBytes": None,
                "estimatedTextureBytes": None,
                "steadyState": "UNAVAILABLE",
            },
            "quality": {
                "absoluteErrorPixels": None,
                "maximumChannelError": None,
                "structuralMetric": None,
                "transparency": "UNAVAILABLE",
                "edges": "UNAVAILABLE",
                "titleAndLegend": "UNAVAILABLE",
                "thinLines": "UNAVAILABLE",
                "fieldOpacity": "UNAVAILABLE",
                "moire": "UNAVAILABLE",
                "visualDisposition": "UNAVAILABLE",
            },
            "precision": {
                "float32ProjectedDisplacement": None,
                "screenPixelDisplacement": None,
                "reverseResidual": None,
                "candidateSetAgreement": "UNAVAILABLE",
            },
            "messages": [{
                "level": "unsupported",
                "text": "Schema sentinel; no benchmark was run.",
            }],
        }],
    })

    layout = validate(
        "contracts/consumer-release-layout-v1.schema.json",
        "fixtures/consumer-release-layout/v1/manifest.json",
    )
    layout_input = ROOT / layout["sourceInput"]["path"]
    assert sha256(layout_input) == layout["sourceInput"]["sha256"]
    assert layout["candidateRelease"]["published"] is False
    assert layout["candidateRelease"]["uploadAuthorized"] is False
    assert layout["releaseBoundary"]["builderS3Access"] is False
    assert layout["releaseBoundary"]["completionMarkerBuilt"] is False
    assert layout["precompression"]["status"] == "deferred"

    atoll = validate(
        "contracts/atoll-evidence-v1.schema.json",
        "fixtures/atoll-evidence/v1/manifest.json",
    )
    atoll_sources = {source["id"] for source in atoll["sources"]}
    expected_layers = {
        "topobathymetry", "inundation", "freshwater", "infrastructure",
        "shoreline", "reef", "ocean-heat",
    }
    assert {layer["id"] for layer in atoll["layers"]} == expected_layers
    for layer in atoll["layers"]:
        assert set(layer["sourceIds"]).issubset(atoll_sources)
    infrastructure = next(
        layer for layer in atoll["layers"] if layer["id"] == "infrastructure"
    )
    assert infrastructure["status"] == "UNAVAILABLE"
    assert infrastructure["sourceIds"] == []
    assert {
        layer["id"] for layer in atoll["layers"]
        if layer["status"] == "canary-rendered"
    } == {"topobathymetry", "inundation"}
    assert atoll["downloadsPerformed"] is True
    assert set(atoll["downloadedSourceIds"]) == {
        "usgs-majuro-tbdem-1944-2016",
        "usgs-majuro-inundation-2016",
    }
    assert atoll["evidenceRenderProduced"] is True
    assert atoll["promotionAuthorized"] is False

    # Raw packages are deliberately reproducible but never required in a clean
    # clone.  If present, verify them; in all cases ensure Git ignores and does
    # not track their declared paths.
    for package in atoll["sourcePackages"]:
        package_path = ROOT / package["localPath"]
        assert package["checkedIn"] is False
        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", package["localPath"]],
            cwd=ROOT,
            check=False,
        )
        assert ignored.returncode == 0, package["localPath"]
        tracked = subprocess.run(
            ["git", "ls-files", "--", package["localPath"]],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert tracked.stdout.strip() == ""
        if package_path.exists():
            assert package_path.stat().st_size == package["bytes"]
            assert sha256(package_path) == package["sha256"]

    prepared_by_id = {value["id"]: value for value in atoll["preparedEvidence"]}
    assert set(prepared_by_id) == {
        "majuro-tbdem-observation-10m",
        "majuro-marine-inundation-30in-deterministic-10m",
        "majuro-marine-inundation-30in-probability-10m",
    }
    for prepared in prepared_by_id.values():
        prepared_path = ROOT / prepared["path"]
        assert prepared_path.is_file()
        assert prepared_path.stat().st_size == prepared["bytes"]
        assert sha256(prepared_path) == prepared["sha256"]

    coordinates = validate(
        "contracts/atoll-coordinate-fixtures-v1.schema.json",
        atoll["coordinateFixture"]["path"],
    )
    source_manifest = ROOT / coordinates["sourceManifest"]["path"]
    assert source_manifest == ROOT / "fixtures/atoll-evidence/v1/manifest.json"
    assert source_manifest.stat().st_size == coordinates["sourceManifest"]["bytes"]
    assert sha256(source_manifest) == coordinates["sourceManifest"]["sha256"]
    coordinate_prepared = {value["id"]: value for value in coordinates["prepared"]}
    assert set(coordinate_prepared) == set(prepared_by_id)
    expected_raster_sizes = {
        "majuro-tbdem-observation-10m": (4623, 2381),
        "majuro-marine-inundation-30in-deterministic-10m": (3973, 1272),
        "majuro-marine-inundation-30in-probability-10m": (3973, 1272),
    }
    for prepared_id, record in coordinate_prepared.items():
        manifest_record = prepared_by_id[prepared_id]
        assert record["file"]["path"] == manifest_record["path"]
        assert record["file"]["sha256"] == manifest_record["sha256"]
        assert record["file"]["bytes"] == manifest_record["bytes"]
        assert (record["raster"]["width"], record["raster"]["height"]) \
            == expected_raster_sizes[prepared_id]
        assert len(record["raster"]["wgs84Footprint"]) == 5

    traces = coordinates["projectionTrace"]["points"] + [coordinates["pixelTrace"]]
    assert len(coordinates["projectionTrace"]["points"]) == 5
    for trace in traces:
        geographic = trace["geographic"]
        inverse = trace["qualifiedInverse"]
        candidate = inverse["candidate"]
        assert inverse["status"] == "unique"
        assert inverse["truncated"] is False
        assert abs(candidate["longitude"] - geographic["longitude"]) <= 2e-8
        assert abs(candidate["latitude"] - geographic["latitude"]) <= 2e-8
        assert candidate["nativeCell"] == trace["forward"]["nativeCell"]
        assert candidate["component"] == trace["forward"]["component"]
        assert candidate["forwardResidual"] <= inverse["tolerancePixels"]

    outputs = atoll["canary"]["outputs"]
    context = atoll["canary"]["contextInput"]
    context_path = ROOT / context["path"]
    assert context_path.is_file()
    assert context_path.stat().st_size == context["bytes"]
    assert sha256(context_path) == context["sha256"]
    assert png_dimensions(context_path) == (context["width"], context["height"])
    assert context["analyticalGrid"] is False
    assert len(outputs) == 1
    output = outputs[0]
    output_path = ROOT / output["path"]
    assert output_path.is_file()
    assert output["sha256"] != "0" * 64
    assert sha256(output_path) == output["sha256"]
    assert png_dimensions(output_path) == (output["width"], output["height"])

    debris = validate(
        "contracts/water-debris-evidence-v1.schema.json",
        "fixtures/water-debris-evidence/v1/manifest.json",
    )
    expected_classes = {
        "observed-shoreline", "observed-surface-sample",
        "modeled-concentration", "modeled-river-emission",
        "cleanup-operation", "depth-profile",
    }
    assert {value["id"] for value in debris["evidenceClasses"]} == expected_classes
    assert debris["stableExistingPasses"] == [
        "anthropocene",
        "anthropocene-temperature-2025",
        "anthropocene-temperature-2026",
    ]
    assert not (ROOT / debris["proposedPass"]["generator"]).exists()
    assert debris["renderReadiness"] == "not-ready"
    assert debris["downloadsPerformed"] is False
    assert debris["generatorImplemented"] is False
    assert debris["promotionAuthorized"] is False

    if arguments.gpu_controls:
        controls = validate(
            "contracts/gpu-benchmark-v1.schema.json",
            "assets.generated/catalog/gpu-controls-v1.json",
        )
        assert controls["documentType"] == "control-catalog"
        assert controls["lifecycle"] == "exploration-only"
        assert len(controls["artifacts"]) == 205
        assert sum(len(value["controls"]) for value in controls["artifacts"]) == 410

    suffix = ", including generated controls" if arguments.gpu_controls else ""
    print(f"Stage 15 contracts passed: frozen input, local layout, atoll canary and water-debris prototype{suffix}.")


if __name__ == "__main__":
    main()

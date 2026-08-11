#!/usr/bin/env python3
"""Independent Myriahedral face-local inverse over declared topology."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


WEIGHTS = (
    (0.60, 0.20, 0.20),
    (0.20, 0.60, 0.20),
    (0.20, 0.20, 0.60),
    (1 / 3, 1 / 3, 1 / 3),
)


def geographic(vertices: list[list[float]], weights: tuple[float, ...]) -> list[float]:
    vector = [sum(weights[index] * vertices[index][axis] for index in range(3))
              for axis in range(3)]
    magnitude = math.sqrt(sum(value * value for value in vector))
    vector = [value / magnitude for value in vector]
    longitude = math.degrees(math.atan2(vector[1], vector[0]))
    latitude = math.degrees(math.asin(max(-1.0, min(1.0, vector[2]))))
    return [longitude, latitude]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("topology", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    topology_bytes = args.topology.read_bytes()
    topology = json.loads(topology_bytes)
    cases = []
    for layout in topology["layouts"]:
        for face in layout["faces"]:
            for weight_index, weights in enumerate(WEIGHTS):
                cases.append({
                    "caseId": f"{layout['layoutId']}-face-{face['nativeFace']}-weights-{weight_index}",
                    "layoutId": layout["layoutId"],
                    "nativeFace": face["nativeFace"],
                    "selectedProjectedBarycentricWeights": list(weights),
                    "expectedGeographic": geographic(face["sphericalVertices"], weights),
                    "boundaryClass": "interior",
                    "angularToleranceDegrees": 2e-10,
                })
    output = {
        "schemaVersion": "cartofreako-reverse-oracle-v1",
        "family": "myriahedral",
        "evidenceGrade": "independent-reimplementation",
        "coordinateContract": {
            "selectedProjected": "barycentric weights in one declared planar face",
            "geographic": "[longitude, latitude] degrees",
        },
        "selectionMethod": "four fixed interior planar barycentric coordinates on four terminal faces per base face in every registered layout",
        "provenance": {
            "algorithm": "normalize(sum(weight[i] * sphericalVertex[i])); atan2/asin",
            "implementation": "dependency-free Python; imports no Cartofreako code",
            "sharedInput": "myriahedral-declared-topology.json",
            "sharedInputRole": "topology only",
            "producer": "tests/oracles/generate-myriahedral-clean-room.py",
            "license": "GPL-3.0-or-later",
        },
        "cases": cases,
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"generated {len(cases)} clean-room Myriahedral reverse cases")


if __name__ == "__main__":
    main()

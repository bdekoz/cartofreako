---
layout: default
title: Projection fixtures and independent reverse oracles
---

# Projection fixtures and independent reverse oracles

[Runtime index](README.md) · [Forward/reverse API](projection-api.md) ·
[Stage 14 ledger](../../development/20260815_stage-14.md) ·
[Dymaxion implementation](../projections/dymaxion/implementation.md)

Cartofreako publishes a versioned, implementation-neutral projection fixture
bundle under [`fixtures/projections/v1/`](../../../fixtures/projections/v1/).
Consumers do not need Cartofreako headers, WebAssembly, generated art, S3, or
network access to parse it.

## Contract and contents

[`projection-fixtures-v1.schema.json`](../../../contracts/projection-fixtures-v1.schema.json)
defines longitude/latitude input in degrees and top-left page output as
normalized `u=x/width`, `v=y/height`. Stable geometric topology keys are
normative; Cartofreako numeric native-cell IDs live in a separate crosswalk.
Reverse candidate sets are unordered and retain cut, component, and boundary
identity.

The checked v1 bundle contains 31,008 cases:

| Family | Cases | Coverage |
| --- | ---: | --- |
| Cahill–Keyes | 108 | Octants, construction zones, seams, poles, and compatibility anchors |
| AuthaGraph | 28 | Sectors and singular vertices |
| Dymaxion | 73 | Faces/subfaces, boundaries, and reference registration |
| Myriahedral | 30,720 | All 5,120 face centers in each of six registered layouts |
| Star-X | 17 | Carrier, fixed-60°S cap, cutoff, overlap, quadrants, and pole |
| Voronoi | 62 | All faces plus representative edges and vertices |

Every file is covered by
[`SHA256SUMS`](../../../fixtures/projections/v1/SHA256SUMS), and every case
states a deliberately narrow evidence grade: published anchor, pinned upstream
implementation, independent reimplementation, structural invariant, or
Cartofreako compatibility. A round trip through Cartofreako is never relabeled
as independent proof.

## Three independent consumers

Run the offline gate with:

```sh
make check-projection-fixtures
```

It checks all 31,008 cases in native C++, a representative cross-family pack
through WebAssembly, and the complete bundle with a dependency-free Python
reader. Normal checks consume immutable fixture bytes; they never refresh
them. Maintainers use the separate explicit command only when reviewed values
or provenance change:

```sh
make refresh-projection-fixtures
```

## Cross-implementation reverse evidence

`make check-reverse-oracles` consumes the frozen records in
[`fixtures/projections/v1/oracles/`](../../../fixtures/projections/v1/oracles/)
and writes a local report under `reports/`. The current 2,108-case result is:

| Route | Cases | Result |
| --- | ---: | --- |
| Pinned `d3-geo-polygon` v2.0.1 Voronoi inverse | 96 independently selected projected page points | Maximum angular difference `5.08038e-13°` |
| Pinned D3 Airocean/Gray versus Cartofreako Dymaxion | 92 points | Four upstream face-19 registration exclusions retained; maximum classified difference `0.000165906°`, below the declared `0.0003°` rounded-registration bound |
| Dependency-free Python Myriahedral face-local inverse | 1,920 points | Maximum angular difference `1.32339e-13°` |

The D3 v1.12.1-to-v2.0.1 delta record shows unchanged projection vertices,
faces, parents, rotation, scale, and center; the newer release modernizes
syntax and GeoJSON handling. The four Dymaxion exclusions are not discarded
failures: the fixture records them as an upstream registration difference so
they cannot silently alter production behavior.

Oracle refresh requires an explicitly pinned upstream checkout and is not
reachable from `make all`, a GitHub release, or the human-invoked UCB AAO/S3
path:

```sh
D3_GEO_POLYGON_V2_ROOT=/path/to/d3-geo-polygon-v2.0.1 \
  make refresh-reverse-oracle-fixtures
```

AuthaGraph, Cahill–Keyes, and Star-X retain narrower structural or derived
composition evidence until genuinely independent producers exist.

## Standalone Equal Earth comparison bundle

Stage 16J publishes a separate exploration-only bundle under
[`fixtures/projections/equal-earth-v1/`](../../../fixtures/projections/equal-earth-v1/).
It remains outside the six-family v1 runtime fixture manifest so a research
control cannot silently become a released atlas family.

The bundle contains 30 forward/reverse cases across canonical Greenwich and
an experimental `11.5°E` layout. Each case carries raw unit-sphere and
normalized top-left page coordinates plus frozen PROJ 9.6.2 and D3 Geo 2.0.1
observations. Check it offline with:

```sh
make check-equal-earth-projection
```

The gate validates the JSON Schema, hashes, C++ and JavaScript agreement,
page-outside behavior, forward/reverse residuals, Jacobian/Tissot diagnostics,
and spherical area scale. Fixture refresh is an explicit maintainer action:

```sh
D3_GEO_ROOT=/path/to/d3-geo-2.0.1 \
  make refresh-equal-earth-fixtures
```

PROJ and D3 are cross-implementation observations, not evidence that
Cartofreako has joined a campaign or corrected human perception. See the
[implementation notes](../projections/equal-earth/implementation.md) and
[five comparison plates](../../development/20260815_equal-earth-positioning-speculations-v01.md).

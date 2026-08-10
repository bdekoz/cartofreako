# cartofreako

This repository contains native C++20 forward implementations of the
AuthaGraph, Cahill-Keyes, Dymaxion, Star-X, Myriahedral, and icosahedral
Voronoi projections, plus candidate-aware reverse implementations for every
family and checked layout through one projection-neutral runtime. Star-X keeps
its ordinary carrier and unified Antarctic cap as explicit components.

Start with the [visual gallery](docs/pages/gallery/README.md), where every thumbnail opens
a released 3840-pixel PNG and every plate has separate layered SVG and print
PDF actions. The [technical documentation hub](docs/pages/README.md)
is the compact build, projection, pass, browser, and release index. The
authoritative full project documentation remains [`index.md`](index.md). The
[AI Workflows assessment and 1080p gaming improvement plan](docs/pages/runtime/ai-agent-and-1080p-gaming.md)
adds screen/runtime derivatives while preserving the SVG/PDF archive and art
masters plus the existing projection-specific 44-inch and A0 print products.

The top-level directories separate implementation, generation, verification,
and artifacts:

| Directory | Contents |
| --- | --- |
| `src.projections/` | Native C++20 projection API and implementations |
| `src.generate/` | SVG generator entry points and generation support headers |
| `src.wasm/` | WebAssembly adapters, geographic input, smoke tests, and generated builds |
| `tests/` | Standalone algorithm and API tests only |
| `assets.static/` | Historical, reference, and downloaded source assets |
| `assets.generated/` | Projection-organized SVG, PDF, PNG, and thumbnail renderings |

## Build and test

Install the components listed in
the [prerequisites](docs/pages/getting-started/prerequisites.md) before building the complete
SVG, PDF, and PNG suite. The offline `make check` target needs GNU Make, a
C++20 compiler, RapidJSON and H3 development files, sibling Alpha60/Izzi
headers, and the checked-in astronomy, Cloud-atmosphere fixture, Orbital
Technosphere, Anthropocene, resources, and network-swarm snapshots.

List every supported top-level Make target with:

```sh
make list-targets
```

A bare `make` uses [`generation-profile.json`](generation-profile.json) to
build only the configured projection/pass SVG matrix. Inspect its normalized
selection first with:

```sh
make generation-plan
make
```

The checked-in development profile selects Cahill-Keyes plus the Earth and
water passes (`ocean` is accepted as the legacy alias for `water`). See the
[generation methods](docs/pages/getting-started/generation-methods.md) for custom profiles, explicit
targets, full-suite generation, the central `generate-*` evaluation ledger,
and the Stage 7 design choices.

Run the standalone algorithm and API compatibility checks with:

```sh
make check
```

The checks build in `tests/` with C++20 and strict compiler warnings. See
[`index.md`](index.md#choose-a-projection) to select and use a projection.

The production browser build exposes all six projections, topology-safe
GeoJSON, slices, workers, and SVG/Canvas/D3 adapters. The original
Cahill-Keyes and ocean/land-only Myriahedral builds remain compatibility
targets:

```sh
make check-wasm-projections
make check-wasm-projections-browser
make check-forward-reverse-projection-api
make check-wasm-cahill-keyes
make check-wasm-cahill-myriahedral
```

See the [web-developer quick start](docs/pages/runtime/webassembly-quick-start.md) and
[`src.wasm` README](src.wasm/README.md) for deployment paths, slices,
compatibility contracts, and build requirements. The
[forward/reverse API notes](docs/pages/runtime/projection-api.md) define
runtime API 3, candidate/component statuses, batches, TypeScript, and headless behavior.

Generate 24 production whole-earth maps, 18 timestamped astronomy maps, 12
timestamped Orbital Technosphere maps, 84 Stage 12 resources maps, six
cumulative network-swarm maps, six filled blue Bathymetry Roulette maps, six
blue Hamonshū bathymetry maps, 18
source-separated Anthropocene observation and temperature maps, six cloud/CDN
network-infrastructure site maps, six default-rendered Fiber Synthesized maps, five
exploratory Myriahedral ocean perspectives, 12 Cahill-Keyes enlargement
slices, and two Myriahedral face-group slices as layered SVG, PDF, and opaque-white,
3840-pixel-long-side PNG artifacts. The same graph also makes 31
480-pixel-wide thumbnails for each of the six projections, 186 total, with:

```sh
make all
```

For a release build, run the same graph with bounded concurrency, keep-going
failure isolation, and an automatic serial completion pass:

```sh
make assets-resilient
```

On a memory-constrained machine, run the same complete artifact graph with
only one recipe at a time. This remains serial even when an outer Make was
started with `-j`:

```sh
make assets-single
```

Outputs are organized projection-first as
`assets.generated/PROJECTION/{svg,pdf,png,thumbnail}/`. Review all 31 standard
passes for each of the six projections in the
[generated snapshot catalog](index.md#generated-artifact-previews). The
complete v13 catalog adds the explicitly authorized Cloud-atmosphere pass as
the thirty-second image in every projection. The corrected
[`v20260808.1` generated-assets release notes](docs/pages/releases/v20260808.1.md)
record the static-bundle manifest, render host, hardware sizing, verification,
and source commit; the earlier `v20260808` package is superseded. The
[S3 v13 publication notes](docs/pages/releases/s3-v13.md) document the public
Cloudian extracted tree used by every preview. The
[release runbook](docs/pages/releases/README.md) treats a GitHub source release and a
UCB Active Archive Object Storage deposit over S3 as different operations;
only the latter uses the interactive, human-invoked AAO target.

Astronomy generation is offline by default and uses a checked-in JSON profile
as the authority for both the calculation timestamp and point of reference.
For normal generation, run only:

```sh
make generate-astro
```

That target reads the checked-in ground and Hubble profiles plus bounded
catalogs, producing all-sky, `ground-multiband` observer, and `hubble`
observer SVGs for all six projections without network access. Stable observer
and instrument IDs appear in both filenames and SVG metadata. It does not call
`fetch-astro-data`; `make all` includes the same offline generation
automatically.

`fetch-astro-data` is a separate, optional maintainer operation. Run it only
when deliberately replacing the checked-in Gaia, NASA Exoplanet Archive, and
JPL SBDB snapshots, then review the input diff and regenerate:

```sh
make fetch-astro-data
git diff -- assets.static/astronomy
make generate-astro
make check
```

Neither target calls the other: fetching changes source snapshots but creates
no maps, while generation consumes the snapshots but never refreshes them.

See the
[`astronomy implementation notes`](docs/pages/passes/astronomy.md) for the
San Francisco/Hubble distinction, SGP4 observer geometry, data sources,
instrumentation models, and the planet sizing contract: a 2× fixed display
glyph plus a dotted true-apparent-size outline.

Cloud-atmosphere generation is a source-timed opt-in outside `make all`.
P-Tree supplies physical Himawari clouds with regional/daytime coverage;
public JAXA Earth COGs supply AOD, precipitation, and shortwave radiation.
Refresh requires the existing P-Tree `.netrc` entry, then preparation converts
all observed layers to a common H3 snapshot:

```sh
make install-jaxa-certificate
make EXTERNAL_PASSES=jaxa-ptree authorize-external
make fetch-cloud-atmosphere-data
make prepare-cloud-atmosphere-data
make verify-cloud-atmosphere-data
make generate-cloud-atmosphere
```

See the
[credentialed P-Tree production-download quick start](docs/pages/data/ptree-download.md)
for account registration, secure `.netrc` setup, a login smoke test,
reproducible commands, expected files, and troubleshooting.

Solar illumination is calculated once at generator process start. AOD remains
distinct from smoke and PM2.5, precipitation is not an event count, and
missing data means unobserved. See the
[Cloud-atmosphere implementation notes](docs/pages/passes/cloud-atmosphere.md)
for the astronomy boundary, source and QA contracts, terms, layers, and
limitations.

Orbital Technosphere generation is also offline by default. Its JSON profile
fixes the SGP4 calculation instant and San Francisco reference point, while
checked-in OMM CSV and NASA SSCWeb snapshots preserve the input state:

```sh
make generate-orbiting
make fetch-orbiting-data
```

See the [Orbital Technosphere implementation notes](docs/pages/passes/orbital-technosphere.md)
for source feasibility, naming, propagation, detiling layers, and accuracy
limits.

Anthropocene generation defaults to the separately pinned, broad-coverage
NOAA CPC temperature fields for the complete 2025 calendar year and partial
2026 through August 4:

```sh
make generate-anthropocene
make generate-anthropocene-artifacts
make generate-anthropocene-cahill-keyes
```

The original profile-fixed, partial-2026 observation atlas remains available
as an explicit legacy product. It preserves station temperature records,
rainfall, fire, smoke, flood, severe weather, and EPA PM2.5 exposure as
independent layers:

```sh
make generate-anthropocene-atlas
make generate-anthropocene-atlas-artifacts
```

The explicit `generate-anthropocene-2025`, `generate-anthropocene-2026`, and
`generate-anthropocene-year-artifacts` aliases remain available. A release
refresh of the observation atlas requires
`FIRMS_MAP_KEY` and audits NASA FIRMS acquisition dates plus world regions;
`ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1` is an explicit local-pipeline
override, not a global release path. EPA AirData remains distinct from NOAA HMS
smoke, and CWFIS remains Canadian QA rather than global fire coverage. See the
[Anthropocene implementation notes](docs/pages/passes/anthropocene/implementation.md)
for classifications, formulas, source research, refresh workflow, and limits.
[Stage 8b enrichment plan](docs/pages/passes/anthropocene/enrichment-plan.md) evaluates the
current North American bias, records the implemented CPC/FIRMS-gate increment,
and specifies the remaining CAMS, permission-gated PurpleAir, and ocean work.

Resources Stage 12 implements six current-source families: energy, food,
fauna, flora, mineral, and human. Fourteen independently defined products run
across all six projections: solar, wind, nuclear, petroleum-refinery
throughput, food production, fisheries, actual reef-threat geometry, forest
area, rare-earth production, and five human measures. Unlike units are never
combined into a synthetic score:

```sh
make generate-resources-energy-wind-cahill-keyes
make generate-resources-fauna
make generate-resources-human
make generate-resources
```

The [resource metric catalog](docs/pages/passes/resources/metric-catalog.md) distinguishes
the 14 standard release passes from optional-pass infrastructure and 45
exploration-only definitions, including the unreleased LGBTQIA-related and
drug-policy candidates. The
[Stage 12 implementation notes](docs/pages/development/stage-12.md),
[resources implementation notes](docs/pages/passes/resources/implementation.md),
and [enrichment plan](docs/pages/passes/resources/enrichment-plan.md) define source roles,
the v3 country/spatial contracts, offline snapshot preparation, reef
normalization, coverage QA, and candidate promotion rules.

Stage 12 resource SVG deliverables are deterministic `*.svg.gz` archives. To decompress
every SVG archive in place while keeping each
`.svg.gz` file:

```sh
find assets.generated -type f -name '*.svg.gz' \
  -exec gzip --decompress --keep -- {} +
```

Optional P-Tree, NASA FIRMS, and licensed network-topology passes require
provider-side registration or terms acceptance. After completing that step,
validate the local credentials and authorization without fetching generation
data or printing secrets:

```sh
make install-jaxa-certificate
make authorize-external
```

The mutating companion performs its own authorization check before running the
locally configured acquisition and full-artifact workflows:

```sh
make generate-authorized-external

# strict selection instead of automatic local discovery
make EXTERNAL_PASSES='jaxa-ptree network-topology' \
  NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
  generate-authorized-external
```

With no `EXTERNAL_PASSES` override, the target selects P-Tree when its netrc
entry exists, FIRMS when `FIRMS_MAP_KEY` is set, and topology when the exact
license acknowledgement is set; every skipped provider is reported. A
configured P-Tree pass installs the pinned, fingerprint-verified per-user
certificate if it is missing. An explicit pass list is strict. Every resulting
selection must authorize before any fetch or render starts. P-Tree produces
its six SVG/PDF/PNG sets and topology produces its licensed six sets. NASA
FIRMS deliberately stops at the ignored Anthropocene review candidate;
release rendering remains blocked until that candidate is audited and
promoted with its profile checksum and coverage documentation.

Only a completely successful run updates the local, ignored
`.cartofreako/authorized-external-passes` file (mode `0600`). It contains
canonical pass names, never credentials or tokens. Later `make all` runs
automatically include prepared JAXA Cloud-atmosphere and licensed topology
artifacts recorded there. FIRMS is remembered as an authorized refresh, but
still has no default render until a candidate is promoted. A clean checkout
has no state file and retains the standard credential-free graph.

See [Prerequisites](docs/pages/getting-started/prerequisites.md#optional-external-authorization) for
the per-provider variables and selective checks.

Network-swarm generation is offline and reproducible from a checked-in
cumulative GeoJSON archive. Prepare the bounded source and generate the six H3/Izzi
honeycomb maps with:

```sh
make prepare-network-swarm-data
make generate-network-swarm
```

See the [network-swarm implementation notes](docs/pages/passes/network-swarm.md)
for source validation, independent downloader layers, clustering, projection
cuts, profile overrides, and output previews.

Network-infrastructure generation reads a commit- and digest-pinned external
`cloud_cdn_cache` checkout and produces six projection variants of the located
site atlas. The default root is `../cloud_cdn_cache`; override
`NETWORK_INFRASTRUCTURE_CLOUD_SOURCE` when needed:

```sh
make check-network-infrastructure-sources
make generate-network-infrastructure
make generate-network-infrastructure-artifacts
```

`make check-prerequisite` verifies that both `../cloud_cdn_cache/` and
`../www.submarinecablemap.com/` exist before a complete build. The stricter
source checks above additionally enforce the pinned commits and digests.

TeleGeography submarine cable and Internet-exchange topology is a separate
CC BY-NC-SA 3.0 opt-in and is never part of `make all` or generation-profile
`"all"`:

```sh
make check-network-infrastructure-topology-sources
make generate-network-infrastructure-topology
make generate-network-infrastructure-topology-artifacts
```

See the
[network-infrastructure implementation notes](docs/pages/passes/network-infrastructure.md)
for source pins, checkout overrides, physical-versus-logical edge semantics,
clustering, licensing, and previews.

The checked `assets.static/fiber-synthesized` cleanup/union is a separate
standard pass. It defaults to the complete 20260805 network and adds unmatched
2022-only routes as subdued historical context:

```sh
make check-fiber-synthesized
make generate-fiber-synthesized
make generate-fiber-synthesized-artifacts
```

See the [Fiber Synthesized implementation notes](docs/pages/passes/fiber-synthesized.md)
for the union-versus-difference decision, exact matching policy, source pins,
license, rendering semantics, and refresh command.

Both bathymetry art families are offline from the same pinned Natural Earth
input as the Earth and water maps. Generate either six-projection suite or its
complete SVG/PDF/PNG artifact family with:

```sh
make generate-bathymetry-roulette
make generate-bathymetry-roulette-artifacts
make generate-bathymetry-hamonshu
make generate-bathymetry-hamonshu-artifacts
```

See the [Bathymetry Roulette implementation notes](docs/pages/passes/bathymetry/roulette.md)
for the cycloid-minimum depth catalogue, filled 30% forms, Voronoi grouping,
restored blue ramp, accepted moiré, and layer contract. The separate
[Bathymetry Hamonshū notes](docs/pages/passes/bathymetry/hamonshu.md)
document its source-indexed Izzi motifs, density/curvature depth mapping,
shared field architecture, provenance, commands, and verification.

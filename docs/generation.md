# SVG generation pipeline

[Documentation index](../index.md) ·
[Prerequisites](prerequisites.md) ·
[Generation methods](generation-methods.md) ·
[Cahill-Keyes context](cahill-keyes-context.md) ·
[Astronomy notes](astro-implementation-notes.md) ·
[Cloud-atmosphere notes](cloud-atmosphere-implementation-notes.md) ·
[P-Tree download quick start](ptree-production-download.md) ·
[Orbital Technosphere notes](orbital-technosphere-implementation-notes.md) ·
[Resources Stage 12 implementation](resources-implementation-notes.md) ·
[Stage 12 overview](stage-12-implementation-notes.md) ·
[Projection snapshots](../index.md#generated-artifact-previews) ·
[Resources enrichment plan](resources-enrichment-plan.md) ·
[Anthropocene notes](anthropocene-implementation-notes.md) ·
[Anthropocene Stage 8b plan](anthropocene-enrichment-plan.md) ·
[Network-swarm notes](network-swarm-implementation-notes.md) ·
[Network-infrastructure notes](network-infrastructure-implementation-notes.md) ·
[Fiber Synthesized notes](fiber-synthesized-implementation-notes.md) ·
[Bathymetry Roulette notes](bathymetry-roulette-implementation-notes.md) ·
[Bathymetry Hamonshū notes](bathymetry-hamonshu-implementation-notes.md)

## Purpose

The repository contains seventeen C++20 SVG generation programs under
`src.generate/`.
Fourteen exercise all six production projections through the real Alpha60 and
Izzi APIs. Three derive Cahill-Keyes or Myriahedral slices from an already
projected whole-earth SVG. They write layered SVGs under each
`assets.generated/PROJECTION/svg/` directory, then reopen those files and verify dimensions, layer
structure, path counts, and numeric sanity. Inkscape subsequently exports each
validated SVG as PDF and as a 3840-pixel-long-side PNG.

A separate C++20 profile resolver validates the user-configurable projection
and pass selection used by a bare `make`. It chooses existing Make targets; it
does not duplicate generation logic or filter SVG layers after generation.

| Artifact | Generator | Principal input |
| --- | --- | --- |
| Geometry | [`src.generate/generate-geometry.cc`](../src.generate/generate-geometry.cc) | Native projection faces and screen quadrants |
| Graticules | [`src.generate/generate-graticules.cc`](../src.generate/generate-graticules.cc) | Sampled latitude and longitude lines |
| Earth | [`src.generate/generate-earth.cc`](../src.generate/generate-earth.cc) | Natural Earth 1:10m ocean and land |
| Water | [`src.generate/generate-water.cc`](../src.generate/generate-water.cc) | Every other Natural Earth 1:10m physical layer |
| Bathymetry Roulette | [`src.generate/generate-bathymetry-roulette.cc`](../src.generate/generate-bathymetry-roulette.cc) | Twelve Natural Earth depth thresholds clipped over explicit, filled Izzi roulette fields |
| Bathymetry Hamonshū | [`src.generate/generate-bathymetry-hamonshu.cc`](../src.generate/generate-bathymetry-hamonshu.cc) | The same depth field architecture using twelve source-indexed Izzi Hamonshū wave motifs |
| Astronomy | [`src.generate/generate-astro.cc`](../src.generate/generate-astro.cc) | Dual ground/Hubble observer profiles, SGP4 Hubble state, bounded Gaia/exoplanet/SBDB snapshots, curated sources/events, and physical planet-size cues |
| Cloud-atmosphere | [`src.generate/generate-cloud-atmosphere.cc`](../src.generate/generate-cloud-atmosphere.cc) | Process-start solar geometry plus prepared, source-timed JAXA P-Tree cloud and JAXA Earth atmosphere observations |
| Orbital Technosphere | [`src.generate/generate-orbiting.cc`](../src.generate/generate-orbiting.cc) | Profile timestamp and observer, CelesTrak OMM population and memberships, NASA SSCWeb reference positions, and SGP4 |
| Resources Stage 12 | [`src.generate/generate-resources.cc`](../src.generate/generate-resources.cc) | Pinned current-source country and reef fields for energy, food, fauna, flora, mineral, and human families |
| Anthropocene | [`src.generate/generate-anthropocene.cc`](../src.generate/generate-anthropocene.cc) | Profile-fixed partial year and checksum-pinned H3 cell-day counts from GSN, EPA AirData, HMS, Storm Events, and CWFIS |
| Anthropocene temperature | [`src.generate/generate-anthropocene-temperature.cc`](../src.generate/generate-anthropocene-temperature.cc) | Complete-2025 and partial-2026 CPC temperature fields on a global H3 domain |
| Network swarm | [`src.generate/generate-network-swarm.cc`](../src.generate/generate-network-swarm.cc) | Validated cumulative swarm GeoJSON, H3 parent clustering, fixed display profile, and Izzi radial honeycombs |
| Network infrastructure | [`src.generate/generate-network-infrastructure.cc`](../src.generate/generate-network-infrastructure.cc) | Manifested cloud/CDN sites plus explicitly opted-in TeleGeography cable and Internet-exchange topology |
| Fiber Synthesized | [`src.generate/generate-fiber-synthesized.cc`](../src.generate/generate-fiber-synthesized.cc) | Checked cleanup/union of 2022 and 20260805 cable snapshots, with 20260805 as the default layer |
| Four slices | [`src.generate/generate-4-slice.cc`](../src.generate/generate-4-slice.cc) | Four full-height, quarter-width quadrant-pair enlargements from the Cahill-Keyes Earth SVG |
| Eight slices | [`src.generate/generate-8-slice.cc`](../src.generate/generate-8-slice.cc) | Eight exact-octant enlargements from the Cahill-Keyes Earth SVG |
| Myriahedral groups | [`src.generate/generate-myriahedral-slices.cc`](../src.generate/generate-myriahedral-slices.cc) | Two complementary exact-terminal-face masks from the Myriahedral water SVG |

The aggregate target generates all four terrestrial artifact families, the
blue Bathymetry Roulette and Bathymetry Hamonshū art families, astronomy and two Orbital
Technosphere products, 14 Stage 12 resource products, one
Anthropocene observation atlas, two year-bearing Anthropocene temperature
atlases, one cumulative
network-swarm product, and one cloud/CDN infrastructure-site atlas for all six
production projections, five exploratory
Myriahedral water perspectives, all 12 Cahill-Keyes slices, and two
Myriahedral face-group slices:

```sh
make all
```

The preferred long-running release workflow bounds its first pass to two
concurrent recipes by default, keeps independent targets moving after a
failure, and then reruns the unfinished graph with one active recipe:

```sh
make assets-resilient
make ASSET_JOBS=4 assets-resilient  # only after sizing the host for four jobs
```

`ASSET_JOBS` affects only the keep-going first pass; the completion pass is
always serial. PDF and PNG exports write a process-specific temporary file,
require a nonempty result, and atomically rename it over the destination.
`.DELETE_ON_ERROR` removes ordinary failed targets, while `make
clean-failed-generated` removes zero-length PDF/PNG files and abandoned export
temporaries without deleting successful artifacts.

Use `make assets-single` for the identical artifact set with a forced
single-job recursive build. It is the first workaround when concurrent
generators or Inkscape exports exhaust memory, and it overrides an inherited
or command-line `-j` setting for the generated-asset sub-build:

```sh
make assets-single
```

`make generated-projections`, `make generate-projections`, and
`make make-generated` are equivalent aliases. The original individual
Cahill-Keyes targets also remain available.

The suite fixes the largest print dimension at 44 inches while retaining each
projection's exact aspect-ratio contract:

| Projection | Frame | Exact construction |
| --- | ---: | --- |
| Cahill-Keyes | `44 × 22` | `2:1` |
| AuthaGraph | `44 × 19.052559` | height `= 11√3` |
| Dymaxion | `44 × 20.78461` | height `= 44 × 3√3/11`, ratio `11/(3√3)` |
| Myriahedral | `44 × 24.75` | `16:9` |
| Star-X | `34 × 44` | `17:22` |
| Voronoi | `44 × 22.916667` | height `= 275/12`, ratio `48:25` |

The numeric frame is also the SVG's unitless coordinate system. Generated
root documents attach `in` to `width` and `height`, but leave `viewBox`
numeric: a Cahill-Keyes document is therefore `width="44in"`,
`height="22in"`, and `viewBox="0 0 44 22"`. One viewBox coordinate unit maps
to one physical inch without changing projection formulas or path data.

The filenames round irrational or recurring dimensions to six decimals,
matching Izzi's serialized `viewBox`; the in-memory frames use the exact
double expressions. These files are diagnostic and illustrative rather than
a general map-rendering command line.

## Build orchestration and inputs

The [top-level Makefile](../Makefile) compiles every generator with C++20 and
`-Wall -Wextra -Wpedantic -Werror`. The geometry and graticule programs need
the neighboring Alpha60 and Izzi source trees. The Earth, water, Bathymetry
Roulette, Cloud-atmosphere, resources, Anthropocene, and network-infrastructure programs
also use GDAL. Natural Earth vector clipping requires GEOS;
Cloud-atmosphere preparation additionally requires the GDAL GeoTIFF and
NetCDF raster drivers. Cloud-atmosphere and Anthropocene normalization and
generation also use H3.

The default locations can be overridden:

| Make variable | Default | Purpose |
| --- | --- | --- |
| `ALPHA60_SRC` | `../alpha60/src` | Alpha60 headers |
| `IZZI_SRC` | `../izzi/src` | Izzi SVG headers |
| `GDAL_CONFIG` | `gdal-config` | GDAL compiler and linker flags |
| `GENERATION_PROFILE` | `generation-profile.json` | Projection and generation-pass selection used by `make` and `make configured` |
| `NATURAL_EARTH_DIR` | `assets.static/natural-earth/10m-physical-vectors` | Extracted shapefiles |
| `ASTRO_DATA_DIR` | `assets.static/astronomy` | Astronomy profile and bounded catalog snapshots |
| `ASTRO_PROFILE`, `ASTRO_HUBBLE_PROFILE` | Ground and Hubble JSON files in `$(ASTRO_DATA_DIR)` | Authoritative timestamp, observer/platform, orientation, instrument, event window, and catalog paths |
| `CLOUD_ATMOSPHERE_DATA_DIR` | `assets.static/cloud-atmosphere` | JAXA source profile plus ignored raw and prepared refresh staging |
| `CLOUD_ATMOSPHERE_PROFILE` | `$(CLOUD_ATMOSPHERE_DATA_DIR)/cloud-atmosphere-profile.json` | Process-time, latest-not-after, source, freshness, QA, H3 aggregation, and display contract |
| `CLOUD_ATMOSPHERE_GEOJSON` | `$(CLOUD_ATMOSPHERE_DATA_DIR)/.prepared/cloud-atmosphere-latest.geojson` | Locally prepared, checksum-verified H3 observation snapshot |
| `ORBITING_DATA_DIR` | `assets.static/orbital-technosphere` | Orbital Technosphere profile, OMM CSV snapshots, NASA reference, and checksums |
| `ORBITING_PROFILE` | `$(ORBITING_DATA_DIR)/orbital-technosphere-profile.json` | Authoritative propagation instant, make-invocation reference point, catalog roles, freshness rules, visibility rules, and display budgets |
| `ANTHROPOCENE_DATA_DIR` | `assets.static/anthropocene` | Checked observation and dual-year CPC profiles, normalized H3 GeoJSON files, checksums, and ignored refresh staging |
| `ANTHROPOCENE_PROFILE` | `$(ANTHROPOCENE_DATA_DIR)/anthropocene-profile.json` | Literal duration year, snapshot date, source coverage, thresholds, metric enablement, scales, and styles |
| `ANTHROPOCENE_GEOJSON` | `$(ANTHROPOCENE_DATA_DIR)/anthropocene-2026.geojson` | Checksum-pinned, source-separated H3 cell-day snapshot |
| `ANTHROPOCENE_TEMPERATURE_PROFILE_2025`, `ANTHROPOCENE_TEMPERATURE_PROFILE_2026` | Year-bearing files in `$(ANTHROPOCENE_DATA_DIR)` | Complete-2025 and partial-2026 CPC field, record-baseline, coverage, and display contracts |
| `ANTHROPOCENE_TEMPERATURE_GEOJSON_2025`, `ANTHROPOCENE_TEMPERATURE_GEOJSON_2026` | Year-bearing files in `$(ANTHROPOCENE_DATA_DIR)` | Checksum-pinned global-domain resolution-3 H3 temperature fields |
| `RESOURCES_DATA_DIR` | `assets.static/resources` | Checked Stage 12 profile, values, country/reef geometry, checksums, and source-workflow README |
| `RESOURCES_PROFILE` | `$(RESOURCES_DATA_DIR)/resources-profile.json` | Six resource families, source/metric catalogues, country/spatial gates, defaults, scales, and palettes |
| `RESOURCES_VALUES` | `$(RESOURCES_DATA_DIR)/resources-values.json` | Normalized country values for implemented metrics |
| `RESOURCES_COUNTRIES` | `$(RESOURCES_DATA_DIR)/countries-110m.geojson` | Compact Natural Earth country geometry keyed by `RESOURCE_A3` |
| `RESOURCES_REEFS` | `$(RESOURCES_DATA_DIR)/coral-reefs-025deg.geojson` | Checked quarter-degree coral-reef presence/threat cells derived from WRI geometry |
| `NETWORK_SWARM_SOURCE` | `assets.static/network-swarm/house-of-the-dragon-301-cumulative-aggregate.geojson.zip` | Local ZIP or plain GeoJSON source prepared for the network-swarm pass |
| `NETWORK_SWARM_GEOJSON` | `assets.static/network-swarm/.prepared/house-of-the-dragon-301-cumulative-aggregate.geojson` | Prepared cumulative swarm staging destination |
| `NETWORK_SWARM_PROFILE` | `assets.static/network-swarm/network-swarm-profile.json` | H3 clustering, physical marker dimensions, labels/tethers, fixed scales, and provenance |
| `NETWORK_INFRASTRUCTURE_CLOUD_SOURCE` | `../cloud_cdn_cache` | External checkout at the profile-pinned cloud/CDN commit |
| `SUBMARINE_CABLE_SOURCE` | `../www.submarinecablemap.com` | External TeleGeography cable checkout used only by topology opt-in targets |
| `INTERNET_EXCHANGE_SOURCE` | `../www.internetexchangemap.com` | External TeleGeography exchange checkout used only by topology opt-in targets |
| `NETWORK_INFRASTRUCTURE_SITES_PROFILE` | `assets.static/network-infrastructure/network-infrastructure-sites-profile.json` | Normal cloud/CDN site-atlas sources, counts, detiling, labels, and terms |
| `NETWORK_INFRASTRUCTURE_TOPOLOGY_PROFILE` | `assets.static/network-infrastructure/network-infrastructure-topology-profile.json` | Explicit TeleGeography topology layers, source pins, and CC BY-NC-SA 3.0 opt-in |
| `FIBER_SYNTHESIZED_DATA_DIR` | `assets.static/fiber-synthesized` | Checked manifest, cleaned union, source-separated audit observations, and hashes |
| `INKSCAPE` | `inkscape` | Command-line PDF and PNG exporter |
| `PNG_LONG_SIDE` | `3840` | Pixel count assigned to each PNG's longest side |
| `ASSET_JOBS` | `2` | Concurrent recipes in the keep-going first phase of `assets-resilient`; its second phase is always serial |
| `LABEL_FONT` | `atkinson_hyperlegible` | Installed font used for visible labels in graticule, astronomy, Cloud-atmosphere, Orbital Technosphere, resources, Anthropocene, network-swarm, network-infrastructure, and both bathymetry-art families |

### Generated label typography

All text-bearing generation passes share
[`generation-typography.h`](../src.generate/generation-typography.h). The
default `atkinson_hyperlegible` identifier serializes as the installed SVG
family `Atkinson Hyperlegible`; font sizes, weights, colors, and label
placement remain pass-specific. The generators reject unsafe or empty family
names and reopen each SVG to verify that every visible `<text>` element uses
the configured family.

Override the font for a deliberate artifact variant with an installed family
name. Use `-B` when outputs already exist so Make reruns the generators and
their PDF/PNG exports:

```sh
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-graticules-projections
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-astro
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-orbiting
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-anthropocene-artifacts
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-resources-artifacts
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-network-swarm-artifacts
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-network-infrastructure-artifacts
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-bathymetry-roulette-artifacts
```

When invoking a generator binary directly, set
`CARTOFREAKO_LABEL_FONT` instead. Installation and exact-family validation are
documented in the [prerequisites](prerequisites.md#label-font).

### Configured development generation

A bare `make` now reads the checked-in
[`generation-profile.json`](../generation-profile.json) and builds only the
selected projection/pass combinations as layered SVGs. The default profile is
the fast development case requested for Stage 7:

```json
{
  "schema_version": 1,
  "description": "Fast Cahill-Keyes terrestrial development profile",
  "projections": ["cahill_keyes"],
  "passes": ["earth", "ocean"]
}
```

Inspect the normalized selection and exact Make targets without generating
anything:

```sh
make generation-plan
```

Then build that selection with either equivalent command:

```sh
make
make configured
```

Use another profile without modifying the checked-in preference:

```sh
make GENERATION_PROFILE=/absolute/path/development.json generation-plan
make GENERATION_PROFILE=/absolute/path/development.json
```

Both selectors must be nonempty JSON arrays. The sole value `"all"` expands
to every supported value. Canonical projections are `cahill-keyes`,
`authagraph`, `dymaxion`, `myriahedral`, `star-x`, and `voronoi`. Canonical
passes and their SVG result counts per projection are shown below. Profile
vocabulary and default-graph membership are separate: the credentialed
Cloud-atmosphere pass is selectable but optional, while exploration-only
candidates are not accepted as generation-profile passes at all.

| Profile pass | Result per projection | Pass class |
| --- | --- | --- |
| `geometry` | One native-face geometry SVG | Standard |
| `graticules` | One labeled graticule SVG | Standard |
| `earth` | One Natural Earth `ocean`/`land` base SVG | Standard |
| `water` | One complementary physical-feature SVG | Standard |
| `astronomy` | All-sky and observer SVGs | Standard |
| `cloud-atmosphere` | One process-start solar and source-timed physical-atmosphere SVG | Optional; P-Tree credentials required for production data |
| `orbital-technosphere` | Global and observer SVGs | Standard |
| `anthropocene` | Two temperature-field SVGs, 2025 and 2026 | Standard |
| `resources-energy` | Four country products: solar, wind, nuclear, and refinery throughput | Standard |
| `resources-food` | One food-production-index country choropleth | Standard |
| `resources-fauna` | Fisheries country choropleth and coral-reef threat field | Standard |
| `resources-flora` | One forest-area country choropleth | Standard |
| `resources-mineral` | One rare-earth mine-production country choropleth | Standard |
| `resources-human` | Five country products: under 30, over 60, two attainment levels, and patents | Standard |
| `network-swarm` | One cumulative network-swarm SVG | Standard |
| `bathymetry-roulette` | One blue-ramp, filled, Voronoi-grouped roulette depth SVG | Standard |
| `bathymetry-hamonshu` | One blue-ramp, Voronoi-grouped Hamonshū wave-field depth SVG | Standard |
| `network-infrastructure` | One cloud/CDN infrastructure-site SVG; never the licensed topology product | Standard; licensed topology is a separate optional pass |
| `fiber-synthesized` | One cleaned-union submarine-fiber SVG with 20260805 as the default layer | Standard |

Names are case-insensitive, and underscores normalize to hyphens. The
resolver also accepts `ck`, `starx`, and the established `voroni` spelling as
projection aliases; `graticule`, `astro`, `orbiting`, and the former `network`
and short `swarm` names for `network-swarm`, `infrastructure` for
`network-infrastructure`, `fiber`, `fiber-map`, and `fiber-synthesized` for
`fiber-synthesized`, `clouds`, `atmosphere`, `solar-atmosphere`, and
`solar/cloud/atmosphere` for `cloud-atmosphere`, plus `energy`, `food`,
`fauna`, `fisheries`, `reefs`, `flora`, `mineral`, `minerals`, and `human` for their corresponding resource
families. `resources`, `resource`, and the legacy typo `resouces` expand to all
six Stage 12 resource families; `ressources-flora` remains a spelling alias.
See the [resource metric catalog](resources-metric-catalog.md) for the exact
standard/optional/exploration-only definitions. In particular, catalog status
`supplemental` is exploration-only and does not authorize a generation target.
The retired historical selector names are rejected. `bathymetry-rolette` and
`art-agua-roulette` are aliases for `bathymetry-roulette`; `hamonshu` and
`art-agua-hamonshu` are aliases for `bathymetry-hamonshu`.
For compatibility with the requested `earth, ocean` vocabulary, `ocean`
normalizes to the current `water` generation pass. It does not mean the
`ocean` layer inside the Earth base SVG.

Profile `"all"` means the six projections by 19 selectable passes. It
produces 180 SVGs because astronomy, Orbital Technosphere, Anthropocene, and
several resource families produce multiple products. It deliberately excludes Cahill-Keyes slices, exploratory
Myriahedral perspectives and slices, and PDF/PNG exports. Those products do
not form a projection/pass cross-product and remain available through their
explicit targets. It includes Cloud-atmosphere and therefore requires a
current locally prepared JAXA snapshot. A clean `make all` retains the
credential-free 205 SVG products (84 stored as deterministic `.svg.gz`
archives), 205 PDF, 205 full-size PNG products, and 31 thumbnails per
projection. A recorded `jaxa-ptree` authorization adds all six
Cloud-atmosphere SVG/PDF/PNG products and one thumbnail per projection; the
complete Stage 13 release therefore has 211 products per full-size format and
32 thumbnails per projection. The six opt-in topology products per format
remain separate from this release.

The resolver rejects empty selectors, duplicate aliases or JSON members,
unknown names or members, a mixed `"all"` selector, and unsupported schema
versions before recursive Make begins. It emits only whitelisted target names,
and the recursive Make retains normal dependency checks, `-j` jobserver
behavior, and command-line overrides. The
[generation methods decision record](generation-methods.md) compares this
design with Make variables, included Make fragments, external JSON tools, and
generator-runtime filtering. It also centralizes the preserved evaluation
conclusions and status of proposed `generate-*` passes.

List every supported top-level build, test, generation, export, and cleanup
target alphabetically with:

```sh
make list-targets
```

Run one target normally:

```sh
make generate-geometry
make generate-graticules-ck
make generate-earth-ck
make generate-water-ck
make generate-authagraph
make generate-dymaxion
make generate-myriahedral
make generate-water-myriahedral-perspectives
make generate-myriahedral-slices
make generate-star-x
make generate-voronoi
make generate-astro
make fetch-cloud-atmosphere-data
make prepare-cloud-atmosphere-data
make generate-cloud-atmosphere
make generate-orbiting
make generate-anthropocene
make generate-anthropocene-atlas
make refresh-resources-data
make generate-resources
make generate-resources-energy
make generate-resources-fauna-reefs-cahill-keyes
make generate-resources-human-over-60
make generate-snapshot-ck
make authorize-external
make EXTERNAL_PASSES=jaxa-ptree generate-authorized-external
make generate-resources-mineral-cahill-keyes
make prepare-network-swarm-data
make generate-network-swarm
make generate-network-infrastructure
make generate-network-infrastructure-topology
make generate-fiber-synthesized
make generate-bathymetry-roulette
make generate-bathymetry-hamonshu
make all
```

Every Make workflow rebuilds only when a declared dependency is newer. Use
`make -B`
when an unconditional regeneration is wanted. `make clean` removes the
generator binaries and generated SVG, PDF, PNG, and WASM build products, but
deliberately retains the downloaded Natural Earth input and checked-in WASM
sources.

The full generators are not part of `make check`; invoking a `generate-*`
target both writes its artifact and runs that generator's embedded structural
checks.

The 205 standard products plus explicitly enabled optional products are
generated beneath their projection's `svg/`, `pdf/`, and `png/` directories;
the 84 resource products also have deterministic `.svg.gz` companions in the
SVG directories. A clean projection contact sheet has 31 lower-resolution
PNGs. The complete Stage 13 graph records `jaxa-ptree`, adds one
Cloud-atmosphere preview to each sheet, and has 32 per projection, 192 total.
Large suites are released as versioned static bundles instead of being stored
in Git. Regenerating with a different GDAL, GEOS, font, or Inkscape version
can still produce ordering, coordinate, or rendering differences even though
the input snapshots are pinned. Cloud-atmosphere remains a source-timed
optional pass even though it is explicitly included in this release.

## PDF and 4K PNG export

Every PDF and PNG has a direct Make dependency on its layered SVG, so
conversion starts only after that SVG generator and its embedded structural
checks succeed. Inkscape uses the SVG page as the export area and preserves
the original projection aspect ratio. PNG exports set the background to white
at full opacity and select 8-bit RGB output without an alpha channel,
flattening transparent page regions without changing the layered SVG or PDF
sources.

The default `PNG_LONG_SIDE=3840` follows UHD 4K video's horizontal pixel
resolution. Landscape Cahill-Keyes, AuthaGraph, Dymaxion, Myriahedral, and
Voronoi maps set their PNG width to 3840 pixels. Portrait Star-X maps,
Cahill-Keyes slices, and Myriahedral group 1 set their PNG height to 3840
pixels; Myriahedral group 2 is landscape. Supplying only the longer dimension
lets Inkscape derive the other dimension without anisotropic scaling. Override
the resolution when needed:

```sh
make -B PNG_LONG_SIDE=7680 all
```

Inkscape exports vector PDFs at the SVG's physical page size without changing
the layered SVG originals. For example, a 44-by-22-inch Cahill-Keyes page is
3168 by 1584 PDF points. The explicit PNG pixel override is independent of
that physical page size.

Final files are grouped by projection first and format second:

```text
assets.generated/
├── cahill-keyes/{svg,pdf,png,thumbnail}/
├── authagraph/{svg,pdf,png,thumbnail}/
├── dymaxion/{svg,pdf,png,thumbnail}/
├── myriahedral/{svg,pdf,png,thumbnail}/
├── star-x/{svg,pdf,png,thumbnail}/
└── voronoi/{svg,pdf,png,thumbnail}/
```

## Astronomy generation

The astronomy pass maps declination to geographic latitude and right
ascension to a configurable synthetic longitude before using the same six
projection implementations as the terrestrial generators. Its two checked-in
profiles contain the calculation timestamp, observer, and instrument; no host
clock or location is inferred. The ground profile supplies the all-sky and
`ground-multiband` observer products. The Hubble profile propagates NORAD
20580 with SGP4 and supplies a distinct `hubble` observer product. Both use
celestial handedness, RA 12h at map center, and a seven-day transient lookback.

Generate all-sky plus both observer-filtered products for all projections with:

```sh
make generate-astro
```

The product-family targets are `generate-astro-all-sky`,
`generate-astro-observer-ground`, `generate-astro-observer-hubble`, and the
two-observer aggregate `generate-astro-observer`. Per-projection targets
follow the `generate-astro-PROJECTION` form. Supply alternate profiles with
`ASTRO_PROFILE` and `ASTRO_HUBBLE_PROFILE`.

Planet markers deliberately carry two scales. The dotted outline follows the
calculated true apparent angular radius from JPL equatorial radius and
geocentric distance. The solid legibility glyph is a fixed 0.15 inch, twice
the earlier symbol size. Metadata labels this
`fixed-glyph-plus-true-angular-outline` contract explicitly.

Catalog acquisition is deliberately separate from rendering. The repository
contains bounded snapshots for reproducible offline generation; refresh Gaia
DR3, the NASA Exoplanet Archive, and named JPL Small-Body Database records
with:

```sh
make fetch-astro-data
```

That target is optional and is not called by `generate-astro` or `make all`.
It changes calculation inputs and should be followed by review and full
artifact regeneration; it neither replaces the authoritative profile or the
curated transient snapshot nor calls a generator. For ordinary offline use,
run only `make generate-astro`. The
[astronomy implementation notes](astro-implementation-notes.md) document the
profile schema, source evaluation, orbital and observer formulas,
instrument-band behavior, SVG layers, current limitations, and every output.

## Cloud-atmosphere generation

The Cloud-atmosphere pass calculates the terrestrial subsolar point and five
illumination zones once at generator process start, then overlays a prepared
H3 snapshot of JAXA physical observations. P-Tree supplies regional/daytime
Himawari cloud fraction, optical thickness, top height, and ISCCP type;
GCOM-C, GSMaP, and JASMES supply AOD, precipitation, and shortwave radiation.
Every source remains independently timed and missing values mean unobserved.

Refresh and render explicitly:

```sh
make fetch-cloud-atmosphere-data
make prepare-cloud-atmosphere-data
make verify-cloud-atmosphere-data
make generate-cloud-atmosphere
```

The fetch requires an existing P-Tree `.netrc` entry. Follow the
[credentialed production-download quick start](ptree-production-download.md)
to register, configure and test credentials, run a reproducible refresh, and
diagnose common failures. Use
`generate-cloud-atmosphere-PROJECTION` for one SVG,
`generate-cloud-atmosphere-projections` for all six SVGs, or
`generate-cloud-atmosphere-artifacts` for SVG/PDF/PNG output. This family is
excluded from a clean checkout's `make all` because an offline build cannot
assume credentials or a current snapshot. A fully successful
`generate-authorized-external` run records `jaxa-ptree` locally; later
`make all` runs in that checkout include the prepared artifact graph without
refetching. The
[Cloud-atmosphere implementation notes](cloud-atmosphere-implementation-notes.md)
document the astro boundary, exact sources, time and QA rules, H3
preparation, source terms, layer contract, and tests.

## Orbital Technosphere generation

The Orbital Technosphere pass propagates checked-in OMM elements with the
published Vallado/CelesTrak SGP4 implementation at the exact instant stored in
its JSON profile. The global family maps Earth subpoints over a subdued
Natural Earth base; the observer family maps above-horizon topocentric
positions from the recorded San Francisco make-invocation point.

```sh
make generate-orbiting
```

Use `generate-orbiting-global`, `generate-orbiting-observer`, or
`generate-orbiting-PROJECTION` for a subset. Supply a different profile with
`ORBITING_PROFILE=/absolute/path/profile.json`.
`generate-orbiting-artifacts` additionally exports the 12 PDFs and PNGs.

Orbital refresh is an explicit, atomic action:

```sh
make fetch-orbiting-data
```

The refresh acquires OMM CSV groups from CelesTrak and selected-spacecraft
reference positions from NASA SSCWeb, then rewrites their checksums. It does
not change the profile's timestamp or location; those must be reviewed with
the NASA query interval. The
[implementation notes](orbital-technosphere-implementation-notes.md) cover
the source feasibility decision, profile schema, category memberships,
coordinate pipeline, SVG metadata, verification, and operational-use limits.

## Anthropocene generation

Stage 12 makes the complete-2025 and partial-2026 NOAA CPC temperature fields
the default Anthropocene pair:

```sh
make generate-anthropocene
make generate-anthropocene-artifacts
```

Use `generate-anthropocene-PROJECTION` for both year-bearing SVGs in one
projection and `generate-anthropocene-projections` for all 12. The loader
rejects a year, snapshot, H3-resolution, filename, H3-center, or metric-total
mismatch, and Make verifies each GeoJSON against its profile SHA-256.

The two profiles serialize every resolution-3 global H3
cell and preserve TMAX/TMIN valid-day denominators, so an analyzed cell with no
strict record is not confused with missing or ocean-domain data:

```sh
make generate-anthropocene-2025
make generate-anthropocene-2026
make generate-anthropocene-years
make generate-anthropocene-year-artifacts
```

The explicit year aliases select one member of the default pair across all six
projections. Stage the ignored NOAA archive and prepare both candidates
without replacing checked files with:

```sh
make fetch-anthropocene-cpc-data
make prepare-anthropocene-temperature-data
```

The earlier source-separated observation atlas maps positive unique-day counts
from the checked resolution-4 H3 FeatureCollection and remains explicitly
available:

```sh
make generate-anthropocene-atlas
make generate-anthropocene-atlas-cahill-keyes
make generate-anthropocene-atlas-artifacts
```

Its profile fixes the literal 2026 duration year, partial snapshot, per-source
coverage, thresholds, metric enablement, scales, shapes, and colors. It does
not read the host clock or calculate a composite climate-attribution score.

EPA AirData PM2.5 exceedance days are enabled by default in the independent
`air-quality-exposure` group. They use a cross-square and never become NOAA
HMS `observed-smoke-days`, which use rings in the `atmosphere` group. Coral
bleaching stress is recorded in the profile and metadata as a separate future
raster/reef phase and is not rendered in Stage 8.

Ordinary generation is offline. These explicit targets stage a candidate
refresh without overwriting the checked GeoJSON:

```sh
make fetch-anthropocene-data
make prepare-anthropocene-data
```

The original checked snapshot retains public CWFIS Canada/North America fire
coverage and zero FIRMS rows. A new global refresh requires `FIRMS_MAP_KEY`;
the fetcher joins advertised standard-processing dates to the NRT tail, and
the preparer rejects missing dates or absent world regions. Set
`ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1` only to debug the regional pipeline.
Copernicus Sentinel-3 fire-radiative-power data and Rosleskhoz operational
reports remain validation sources. The
[Anthropocene implementation notes](anthropocene-implementation-notes.md)
document the feasibility boundary, classifications, exact formulas, source
audit, Canada/Russia fire evaluation, candidate resource types, SVG contract,
refresh workflow, and limits.

## Stage 12 resources generation

The resources pass is a strict, offline country/spatial pipeline split into
six independent families and 14 released metrics. `resources-energy` builds
solar, wind, nuclear, and refinery-throughput maps; `resources-fauna` builds
fisheries and coral-reef-threat maps; and `resources-human` builds five
separate demographic, attainment, and patent maps. Food, flora, and mineral
currently contribute one released map each.

The [resource metric catalog](resources-metric-catalog.md) lists all 59
definitions: 14 standard products and 45 exploration-only candidates. There
are currently no optional resource metrics.

Build all released products for a family/projection pair, one family across
all projections, all families for one projection, or the entire 84-map
matrix. Metric aliases select a single product:

```sh
make generate-resources-energy-cahill-keyes
make generate-resources-fauna
make generate-resources-human-over-60
make generate-resources-energy-petrochemical-star-x
make generate-resources-cahill-keyes
make generate-resources-stage12
```

Every checked resource SVG is stored as a deterministic gzip archive. The
plain SVG remains an ignored build intermediate used for PDF/PNG export.
Inspect one without changing the checkout:

```sh
gzip -cd \
  assets.generated/cahill-keyes/svg/resources-fauna-coral-reef-threat-2011-ck-44-22.svg.gz \
  > /tmp/resources-fauna-reefs.svg
```

To decompress all `svg.gz` files anywhere beneath `assets.generated` beside
their archives while retaining the compressed files:

```sh
find assets.generated -type f -name '*.svg.gz' \
  -exec gzip --decompress --keep -- {} +
```

The profile selector `resources` expands to all six family passes. Select a
smaller subset directly:

```json
{
  "schema_version": 1,
  "projections": ["cahill-keyes"],
  "passes": ["resources-fauna", "resources-human"]
}
```

Normal generation reads only checked v3 profile/values, country and reef
geometry, and Natural Earth files. It never downloads. Maintainers can run
`make refresh-resources-data`, then review source periods, country/output/
spatial gates, checksums, and all projection diffs. The
[implementation notes](resources-implementation-notes.md) document exact
metrics, derivations, schemas, reef reduction, target names, and limitations;
the [enrichment plan](resources-enrichment-plan.md) records future products.

## Network-swarm generation

The network-swarm pass reads a strict cumulative swarm FeatureCollection,
validates all ten `properties.downloaders` values and 64-bit H3 cells, then groups
resolution-5 features under profile-selected resolution-3 parents. Parent
groups are split again by the selected projection's native cell before Izzi
radial honeycomb placement, preventing a cluster from crossing an unfolded
map seam. Thin optional tethers retain each true projected location.

```sh
make prepare-network-swarm-data
make generate-network-swarm
```

Use `generate-network-swarm-PROJECTION` for one SVG or
`generate-network-swarm-artifacts` for all six SVG/PDF/PNG products. A
compatible local ZIP or plain GeoJSON is selected with `NETWORK_SWARM_SOURCE`;
`NETWORK_SWARM_GEOJSON` changes the staging destination. Normal generation is
offline from the pinned archive.

The [network-swarm implementation notes](network-swarm-implementation-notes.md)
document the source audit and digests, schema validation, H3 resolution
decision, Izzi lattice canonicalization, independent overlapping fields, visual
grammar, SVG layers, output previews, verification, and interpretation
boundary.

## Network-infrastructure generation

The ordinary network-infrastructure product maps the 1,003 located cloud/CDN
records in an externally checked, commit-pinned manifest. All points enter one
projection-cell-aware Izzi radial-hexagon collision layout; unlocated source
records remain represented in provenance totals and are never assigned
invented coordinates. This non-TeleGeography site atlas is a normal generation
pass and is included in `make all`:

```sh
make check-network-infrastructure-sources
make generate-network-infrastructure
make generate-network-infrastructure-artifacts
```

Set `NETWORK_INFRASTRUCTURE_CLOUD_SOURCE` when the pinned `cloud_cdn_cache`
checkout is not at its default sibling path. The six SVG-only projection
targets use `generate-network-infrastructure-PROJECTION`.

Submarine cable routes, cable landings, Internet-exchange facilities, and
logical exchange-to-facility membership are a separate, explicitly opted-in
product because the source topology is CC BY-NC-SA 3.0:

```sh
make check-network-infrastructure-topology-sources
make generate-network-infrastructure-topology
make generate-network-infrastructure-topology-artifacts
```

The topology rules also require `SUBMARINE_CABLE_SOURCE` and
`INTERNET_EXCHANGE_SOURCE`, defaulting to the two documented sibling
checkouts. They validate all three commits, primary-file digests, and consumed
tracked paths before generation. Topology is deliberately excluded from
`make all` and generation-profile `"all"`; its SVGs visibly attribute
TeleGeography and embed the CC BY-NC-SA 3.0 boundary. Cable paths are
source-backed physical geometry, while dashed exchange membership spokes are
logical incidence—not inferred fiber or traffic.

The [network-infrastructure implementation notes](network-infrastructure-implementation-notes.md)
record the source audit, exact snapshots and counts, license boundary, profile
schema, seam handling, clustering, layer semantics, previews, verification,
and known limits.

## Fiber Synthesized generation

Fiber Synthesized is the standard, checked-in submarine-fiber pass. It is a
cleanup and union—not a `new - old` difference—of the 2022 and 20260805 API
snapshots. The complete 20260805 network is the default visible layer; only
unmatched 2022-only routes and landings are added as subdued historical
context, while source-separated audit files retain both observations.

```sh
make check-fiber-synthesized
make generate-fiber-synthesized
make generate-fiber-synthesized-artifacts
make generate-fiber-synthesized-star-x
```

Normal generation is offline from `assets.static/fiber-synthesized` and is
part of `make all`. `make refresh-fiber-synthesized` is the separate,
reviewable operation that reads the two dated external snapshot directories
and rewrites the static union. Snapshot-only classifications never claim
construction or decommission. See the
[Fiber Synthesized implementation notes](fiber-synthesized-implementation-notes.md)
for exact source hashes, counts, matching policy, layer grammar, license, and
verification.

## Bathymetry art generation

The Bathymetry Roulette pass reuses the twelve nested Natural Earth depth
polygons as projection-safe clip paths. Each depth paints an opaque pale ground
and an explicit projected-page mosaic of Izzi epitrochoid or hypotrochoid
forms. All depths use even-odd fill at 30% opacity. The 0 m family starts at the
cycloid boundary `d/r = 1`; `d/r` increases strictly with depth to 5.00 and
does not vary spatially. Twenty-four jittered Voronoi regions group the twelve
phase/size/offset variations. The original Natural Earth blue ramp supplies a
second depth cue.

Bathymetry Hamonshū is a separate standard art pass over the same Natural
Earth clips, field spacing, 24-region assignment, 30% opacity, blue ramp, and
shallow-to-deep replacement model. It substitutes twelve source-indexed Izzi
Hamonshū wave motifs. Because those motifs are linework, depth increases the
native density and curvature parameters rather than inventing a `d/r` value.
Both generators serialize every field instance; output size is intentionally
not a generation constraint, and overlapping region edges may produce moiré.

```sh
make generate-bathymetry-roulette
make generate-bathymetry-hamonshu
```

Use `generate-bathymetry-roulette-PROJECTION` for one SVG,
`generate-bathymetry-roulette-projections` for the six SVGs, or
`generate-bathymetry-roulette-artifacts` for all six SVG/PDF/PNG products.
The Hamonshū family provides the parallel
`generate-bathymetry-hamonshu-PROJECTION`,
`generate-bathymetry-hamonshu-projections`, and
`generate-bathymetry-hamonshu-artifacts` targets.
The source catalogue is deterministic and needs no profile beyond the common
Natural Earth input. `bathymetry-roulette`, `bathymetry-rolette`, and
`art-agua-roulette` select the roulette pass; `bathymetry-hamonshu`,
`hamonshu`, and `art-agua-hamonshu` select the Hamonshū pass.

The [Bathymetry Roulette implementation notes](bathymetry-roulette-implementation-notes.md)
record the exact twelve curve parameter sets, nested-paint model, visible key,
SVG contract, verification, previews, accepted moiré, and interpretation
limits. The [Bathymetry Hamonshū notes](bathymetry-hamonshu-implementation-notes.md)
record source motifs, density/curvature mapping, common field architecture,
provenance, commands, verification, and limits.

## Natural Earth acquisition

[`scripts/fetch-natural-earth-10m.sh`](../scripts/fetch-natural-earth-10m.sh)
downloads Natural Earth 5.1.1's complete 1:10m physical-vector archive. It:

1. checks for a completion stamp and the `.shp`, `.shx`, `.dbf`, and
   `.prj` components of every required dataset;
2. downloads the official archive only when the local archive is absent;
3. verifies its fixed SHA-256 digest before extraction;
4. extracts only the named physical datasets; and
5. creates the completion stamp last, so interrupted extraction is retried.

The Earth, water, Star-X graticule, both bathymetry-art families, Cloud-atmosphere,
resources, and Anthropocene targets depend on that
stamp and pass
`NATURAL_EARTH_DIR` to their executables. The archive digest and licensing
are recorded in the
[Natural Earth data note](natural-earth-10m-physical-vectors.md).

## Shared coordinate pipeline

The fourteen whole-map generators use
[`projection-generation-common.h`](../src.generate/projection-generation-common.h)
to select a production projection, construct its exact frame, and call the
shared public API in `(latitude, longitude)` order. Projected coordinates use
an upper-left SVG origin.

The three slicing programs instead use
[`cart0freak0-cahill-keyes-slicing.h`](../src.projections/cart0freak0-cahill-keyes-slicing.h),
or
[`cart0freak0-myriahedral-slicing.h`](../src.projections/cart0freak0-myriahedral-slicing.h).
Those headers own the slice descriptors, clipping geometry, SVG wrapper
construction, and verification rules.

```mermaid
flowchart LR
  SOURCE["Geographic construction,<br/>celestial/orbital catalog,<br/>H3 swarm, or WGS84 data"]
  CUT["Clip at geographic<br/>registration seams"]
  DENSE["Sample or densify<br/>in geographic space"]
  PROJECT["Selected production<br/>forward projection"]
  SPLIT["Bisect every native-cell<br/>transition and split cuts"]
  SVG["Izzi path<br/>serialization"]
  CHECK["Reopen SVG and<br/>check structure"]

  SOURCE --> CUT --> DENSE --> PROJECT --> SPLIT --> SVG --> CHECK
```

The ordering matters. A point projection alone does not say whether adjacent
input points remain connected in an unfolded net. Geographic clipping keeps
antimeridian and registered Cahill-Keyes closures local. Densification makes
native-cell crossings short, but an edge that passes close to a mesh vertex
can still cross more than one small face. The shared path projector repeatedly
identifies and bisects the first cell transition until it reaches the endpoint
cell. Each bisection runs for 48 iterations, compares the two limiting
projected points, and starts a new SVG subpath only when those limits are
genuinely separated.

### Registered cut meridians

The native Cahill-Keyes construction changes octants at `-110`, `-20`,
`70`, and `160` degrees. The public projection adds one degree to input
longitude to retain registration with the Visionscarto base map, so generator
input must instead be split at:

```text
-111°, -21°, 69°, 159°
```

The geometry and graticule programs describe four cyclic sectors. The Pacific
sector is represented as `159° ... 249°`, then canonicalized back into the
public `[-180°, 180°]` domain point by point. The polygon programs use five
linear clipping bands because the cyclic Pacific sector is divided by the
antimeridian.

Every generator offsets a cut by `1e-7` degree. That epsilon avoids asking
the piecewise projection to choose both sides of the same boundary. It is
small enough to be visually negligible at the fixture scale, but it is still
a deliberate microscopic gap rather than an exact topological weld.

### Sampling and densification

The Cahill-Keyes/Star-X geometry outlines sample analytic boundaries every
2.5 degrees. Graticules use 0.5-degree samples to keep crossings of the
depth-5 Myriahedral mesh short. The Natural Earth generators retain source
vertices, apply topology-preserving simplification, then call GDAL
`segmentize()` so no input segment exceeds a configured angular length. These
steps greatly reduce the number of face transitions per edge but do not
assume there is only one; a short edge can graze a mesh vertex and enter two
or more faces.

Both approaches are fixed-step approximations. They are predictable and
compact, but not adaptive to projected curvature. A degree of longitude also
represents less physical distance near a pole than at the equator. If these
outputs are enlarged substantially or used as numeric reference artwork,
projected-space error should be measured and the sampling threshold reduced
or made adaptive.

Consecutive points that project to exactly the same coordinate are removed.
All generators reject non-finite points and material out-of-frame results,
then clamp tolerated roundoff at the frame boundary.

## Folding, clipping, and discontinuities

The shared generator does not infer cuts from a projection-independent jump
distance. Instead it assigns every geographic sample to a native cell:

- eight registered octants for Cahill-Keyes and Star-X;
- the nearest tetrahedron vertex plus one of six local sectors for
  AuthaGraph;
- one of 23 Fuller/Airocean faces or subfaces for Dymaxion;
- one of 5,120 subdivided spherical triangles for Myriahedral; or
- one of twenty rotated nearest-site faces for Voronoi.

When adjacent samples select different cells, a geographic bisection retains
the last point on the left cell and the first on the right. If the projected
limits agree within `44 × 10^-5`, the edge is joined in the planar net and both
limits stay in the same path. Otherwise the edge is a cut and a new subpath
begins. The search then resumes just inside the new cell and repeats until the
endpoint cell is reached, with a defensive limit of 64 transitions per source
edge. This tests the assembled net itself: retained Dymaxion hinges and
tree-connected Myriahedral and Voronoi faces remain joined, while exterior or
non-tree edges split without a hard-coded list of relationships.

Cahill-Keyes and Star-X add topology-specific routing before that generic
fallback. Cahill-Keyes applies its 2:1 rectangular frame fold to each original
adjacent pair. Star-X cannot use that rectangle: its lower four-face square
and rotated upper square have internal paired edges. The Star-X router bisects
the registered transition in geographic space, terminates at the outgoing
face-edge copy, and resumes at its paired incoming copy. The `-21 degrees`
and `159 degrees` boundaries always fold between groups; other longitude and
equatorial transitions remain joined only when their one-sided projected
limits coincide. The router consumes multiple folds per source edge and
treats canonical `+180/-180` neighbors as one continuous short arc.

Myriahedral cell lookup and point projection both canonicalize exact
longitude `+180` to `-180`. Without that shared tie rule, an endpoint on the
antimeridian can be classified in one face but projected through a distant
copy of another face, producing a false line across the map.

AuthaGraph has an additional periodic coordinate wrap that can occur without
changing its spherical sector. Adjacent projected samples separated by more
than one third of the frame's largest dimension trigger a second bisection;
the half interval containing the large jump is retained until its paired exit
and entry limits are found.

Filled rings still need more care than open lines. All source polygons are
first intersected with the five antimeridian-safe registered longitude bands
used by Cahill-Keyes. Cahill-Keyes and Star-X can then close those face-safe
pieces directly. AuthaGraph additionally uses a 5-degree geographic grid and
rejects any fragment whose projected closing edge exceeds 2.5 frame units.

Dymaxion, Myriahedral, and Voronoi use exact native-face clipping from
[`projection-area-generation.h`](../src.generate/projection-area-generation.h).
Every 5-degree geographic cell is densified, mapped separately through each
candidate face's local transform, repaired with GEOS if necessary, and
intersected with that face's exact planar triangle. Dymaxion uses Gray's exact
Fuller face transform and the selected subface registration; Myriahedral uses
the same central gnomonic barycentric transform as its 5,120-face
implementation; and Voronoi uses its face-local gnomonic transform and
unfolding affine. Only the clipped planar pieces are normalized into the
output frame, so a filled ring never needs a chord between unrelated net
edges. Same-color area hairlines hide microscopic cracks along adjacent
pieces.

## Geometry generator

[`src.generate/generate-geometry.cc`](../src.generate/generate-geometry.cc) constructs the
selected projection's explanatory skeleton rather than reading external
data. The `triangular-faces` layer is constructed from each projection's
native topology:

| Projection | Face construction | Path count |
| --- | --- | ---: |
| AuthaGraph | Exact 24-sector planar assembly table, cyclically shifted and clipped at the periodic frame edges | at least 24 |
| Cahill-Keyes | Sampled registered octants | 8 |
| Dymaxion | Exact planar triangles from the horizontal Airocean net | 23 |
| Myriahedral | Normalized planar triangles from the fixed depth-5 layout | 5,120 |
| Star-X | Sampled Cahill-Keyes octants assembled into the two stacked groups | 8 |
| Voronoi | Twenty face-local gnomonic triangles transformed through the fixed unfolding tree | 20 |

For Cahill-Keyes and Star-X, the generator additionally:

1. defines four registered 90-degree longitude sectors and their official
   northern and southern octant numbers;
2. traces each octant along its equator edge, eastern seam, pole, and western
   seam;
3. splits every octant at its central meridian to produce two half-octants;
4. constructs four equal-width screen-space rectangles matching Alpha60's
   map-quadrant convention; and
5. writes four semantic SVG layers, plus a Star-X-only `polar-marks` layer.

For those two projections the additional layer counts are:

| Layer | Count | Meaning |
| --- | ---: | --- |
| `triangular-faces` | 8 | Filled presentation of the eight octahedral faces |
| `quadrants` | 4 | Equal-width drawing regions, not spherical quadrants |
| `octants` | 8 | Outlined and officially numbered projected octants |
| `half-octants` | 16 | Western/eastern halves used by the piecewise construction |
| `polar-marks` | 1 | Star-X-only eight-point star centered on the North-pole locus |

The `polar-marks` row applies only to Star-X. The `triangular-faces` and
`octants` layers intentionally contain the same
geometric outlines with different IDs and styles. One communicates the
polyhedral faces perceptually; the other exposes the geographic numbering for
inspection.

Near a pole, the boundary meridians stop at `90° - epsilon`; the exact pole
is then projected at the sector center. This chooses the intended copy of a
polar vertex instead of allowing a seam longitude to choose an adjacent face.
The visible pole duplication is a property of the unfolded net, not numerical
noise.

Every projection also receives four equal-width screen-space `quadrants`.
The program verifies the projection-specific view box, native face count,
quadrant count, optional octant layers, and absence of NaN or infinity.

## Graticule generator

[`src.generate/generate-graticules.cc`](../src.generate/generate-graticules.cc)
creates a conventional ten-degree geographic reference grid:

- 17 parallels from `80°S` through the equator to `80°N`;
- 36 meridians from `180°` through `170°E`;
- seam-safe subpaths determined from native-cell transitions; and
- explicit octant-sector and hemisphere pieces for Cahill-Keyes and Star-X.

Splitting a parallel by longitude sector prevents a line from jumping between
distant octants. Splitting a meridian at the equator reflects the fact that
its northern and southern halves belong to different octahedral faces even
though they touch geographically.

Star-X adds its current Antarctic cap after those ordinary splits. The
generator cuts each graticule edge at the fixed `60°S` parallel, leaves the
northern subpaths on the X, and maps the southern subpaths around one
bottom-center South Pole without changing their source-pole radius. The
visible `antarctic-cap-boundaries` layer draws the four projected source
segments and the unified destination boundary, making the operation directly
inspectable in `graticules-star-x-34-44.png`. Its registration comes entirely
from that projected boundary and proportional lower clearance; the Star-X
graticule target neither depends on nor reads the prepared Natural Earth
dataset.

Each line is a named SVG subgroup with paths, a title, and one visible degree
label. Multiples of 30 degrees receive stronger styling. The label is placed
at the midpoint sample of the longest projected subpath, which keeps it on a
visible part of irregular nets without projection-specific anchor constants.
`180°` is displayed without an east/west suffix.

These are layout heuristics, not a general label-placement engine. They are
tuned for the 44-unit diagnostic frames. Dense overlays or different
typography may require collision detection, leader lines, or multiple labels
per disconnected parallel.

The self-check expects 17 latitude groups and labels, 36 longitude groups and
labels, at least one visible path per group, and finite coordinates. The
subpath count is projection-dependent.

## Natural Earth physical-map generators

[`src.generate/natural-earth-generation.h`](../src.generate/natural-earth-generation.h)
contains the shared GDAL-to-Izzi rendering pipeline. The thin
[`generate-earth.cc`](../src.generate/generate-earth.cc) and
[`generate-water.cc`](../src.generate/generate-water.cc) entry points select two
complementary artifact kinds, ensuring that both use identical clipping,
densification, projection, styling, and validation logic.

### Geometry processing

For each shapefile, the program:

1. opens the first GDAL vector layer read-only and requires a geographic
   spatial reference;
2. clones each nonempty feature;
3. optionally simplifies it while preserving topology;
4. skips clipping bands that cannot overlap the feature envelope;
5. intersects the feature with every relevant seam-safe longitude band;
6. for Star-X, further clips filled areas into northern and southern pieces
   so closing a projected ring cannot bridge an exterior equatorial notch,
   then splits every physical layer at the fixed `60°S` Antarctic boundary;
7. for AuthaGraph, Dymaxion, Myriahedral, and Voronoi, further clips areas to a
   5-degree geographic grid;
8. densifies each surviving piece with `segmentize()`;
9. projects lines with repeated native-cell bisection and areas either
   directly or by exact Dymaxion/Myriahedral/Voronoi face-local triangle
   intersection;
   and
10. serializes the result as one named Izzi path per source feature and band,
    with a hemisphere suffix on Star-X area paths.

Interior polygon rings are retained, and area paths use SVG's `evenodd`
fill rule so lakes or other holes are not painted solid. All tolerances below
are in geographic degrees, because simplification and densification happen
before projection:

The Natural Earth ocean is a complex polygon with interior rings. On the
unfolded Cahill-Keyes net, clipping those rings at an octant boundary and
closing each resulting subpath independently can expose a broad false hole
between otherwise adjacent ocean pieces. Cahill-Keyes and Star-X therefore
paint ten seam-safe background pieces first inside the existing `ocean`
group: five registered longitude bands, each split at the equator and
densified before projection. The detailed Natural Earth ocean is painted over
that underlay, followed by land. A page-sized blue rectangle would also color
the intentional cuts and the area outside the projection, whereas the
face-local underlay keeps those regions white. The Earth self-check verifies
both the piece count and that this paint order is preserved. Star-X also
checks that the cyclic band crossing the antimeridian has distinct north and
south ocean paths; without that split, SVG ring closure fills the lower-left
equatorial notch even though the synthetic face underlay is correct.

| Layer family | Simplification | Maximum segment |
| --- | ---: | ---: |
| Ocean and twelve bathymetry levels | 0.04 | 0.50 |
| Land | 0.03 | 0.50 |
| Minor islands | 0.005 | 0.25 |
| Glaciated areas and Antarctic ice shelves | 0.02 | 0.35 |
| Lakes and reservoirs | 0.01 | 0.25 |
| Playas | 0.005 | 0.25 |
| Rivers and lake centerlines | 0.01 | 0.25 |
| Reefs | 0.005 | 0.20 |
| Coastline | 0.02 | 0.25 |

Finer tolerances preserve small islands, reefs, and playas that would
disappear under the bathymetry setting. Densification is also finer for
features whose local bends or narrow scale matter perceptually.

### Complementary layer partition

The Earth document is an opaque base containing exactly two top-level SVG
groups, in paint order: `ocean` and `land`. The water document is a
transparent overlay containing every other physical family: twelve nested
bathymetry levels, minor islands, glaciated areas, Antarctic ice shelves,
lakes and reservoirs, playas, rivers, reefs, and coastline. It explicitly
contains neither `ocean` nor `land`.

The split is by source layer, not by a geographic definition of water. In
particular, `minor-islands` belongs to the overlay even though it is land
geometry, because the requested base is restricted to the two canonical
Natural Earth polygon families. Both artifacts use the same projection frame,
so compositing water over Earth reconstructs the original complete physical
stack without duplicating a group.

Star-X adds a layer-aware polar composition. Its default point transform
first closes the central group gap and enlarges the complete X 120 percent
about the 34-by-44 page center. The generator then cuts each practical
quadrant at `60°S` and moves the four southern fragments around one
bottom-center pole. This applies to ocean, land, all bathymetry levels, minor
islands, ice, lakes, playas, rivers, reefs, and coastline. The source caps are
removed, so no physical content is duplicated. Cap registration is independent
of Natural Earth: the complete projected `60°S` boundary is sampled every
`0.25°`, centered on the page axis, and placed so its bottommost point retains
`H(0.25/44)` clearance (`0.25` units on the 34-by-44 plate). Every transformed
Antarctic path paints after the ordinary quadrant paths in its layer. The Earth
`land` group contains the central `north-pole-star`; water adds a final
`polar-mark` group with the same black star above its 22 physical groups.

The Antarctic mapping reuses each point's exact distance from its ordinary
Star-X source tip; it introduces no separate radial scale. Geographic bearing
is normalized around the shared pole because the Cahill-Keyes quadrant edges
are bent and cannot all be joined with one rigid rotation per fragment. This
keeps the continent at the map's radial scale while resolving the perceptual
and topological problem of recognizing its four separated pieces.

Within the water overlay, the twelve bathymetry polygons run from 0 m through
-10,000 m. Progressively deeper polygons are painted over shallower ones with
progressively darker blues. Minor islands, ice, lakes, playas, rivers, reefs,
and coastline follow.

Bathymetry here is a stack of depth classes, not a continuous elevation
surface or hillshade. Color steps emphasize categorical depth thresholds;
they are not guaranteed to be perceptually uniform. Likewise, line widths and
feature-specific simplification intentionally favor legibility at the target
view over equal treatment of every source vertex.

Izzi's path constructor requires a stroke color before emitting a path.
Filled areas therefore use a same-color 0.0025-unit hairline. Besides satisfying
the API, the stroke covers sub-pixel cracks between separately clipped pieces.
The tradeoff is that narrow shapes can appear slightly heavier and adjacent
fills can overlap by a fraction of a display pixel.

Each executable prints source-feature, output-path, and projected-point counts
for every selected layer. The Earth check requires exactly the `ocean` and
`land` groups and rejects every overlay group. The water check requires every
overlay group and all twelve bathymetry subgroups, while rejecting `ocean`
and `land`. Both also enforce minimum path counts, the projection-specific
view box, and finite coordinates. Star-X additionally requires its central
star, unified Antarctic land and ice shelves, and unified Antarctic
coastline.

## Cahill-Keyes enlargement slices

The slicing subsystem separates two concepts that must not be conflated:

- the **projection carrier** is the complete Cahill-Keyes world and must
  remain 2:1; and
- a **slice frame** is a viewport into already projected carrier coordinates
  and may have any aspect ratio.

Let the carrier be `W × H`, and let a source viewport be
`V = (x0, y0, w, h)`. The Earth is projected once on the carrier. A slice
only changes the visible coordinate window:

```text
x_local = x_carrier - x0
y_local = y_carrier - y0
```

There is no second forward projection and no geometric enlargement in the
SVG path data. The smaller physical page and the normal 4K raster export make
the selected region an enlargement when printed or displayed. In particular,
the slice frame must never be passed to `make_cahill_keyes_projection()`:
most useful slices are deliberately not 2:1.

[`cart0freak0-cahill-keyes-slicing.h`](../src.projections/cart0freak0-cahill-keyes-slicing.h)
owns carrier validation, slice descriptors, coordinate translation, octant
outlines, SVG wrappers, stable names, and structural checks. The two thin
entry points implement complementary publishing styles:

| Style | Generator | Geometry |
| --- | --- | --- |
| Four strips | [`generate-4-slice.cc`](../src.generate/generate-4-slice.cc) | Four full-height, quarter-width viewports containing octant pairs `(1,6)`, `(2,7)`, `(3,8)`, and `(4,5)` |
| Eight octants | [`generate-8-slice.cc`](../src.generate/generate-8-slice.cc) | Eight face-clipped viewports using each projected octant's natural rectangular bounds |

For the standard 44×22 carrier, the four source viewports begin at `x = 0`,
`11`, `22`, and `33`; each output page is 11×22 inches. The requested ordered
latitude contexts—`-30→20`, `20→-60`, `-50→30`, and `60→-40` degrees—are
stored as descriptive metadata. They do not define the viewport and do not
clip source data. A real latitude filter would need to operate on geographic
geometry before projection.

The exact-octant style samples each face perimeter, computes its tight
axis-aligned carrier bounds, and applies the same outline as an SVG clip path.
Its pages have naturally varying ratios. North and south octant bounds overlap
vertically in the M layout, so an ordinary 4×2 rectangular grid would not
isolate the eight semantic faces.

Slice SVGs are lightweight wrappers whose `<use>` references
`earth-ck-44-22.svg#earth-ck-44-22`. The root `width` and `height` carry inch
units while the `viewBox` stays in the original unitless carrier coordinates.
The master Earth SVG must therefore remain beside the slice SVGs. Inkscape
resolves that vector reference when exporting the self-contained PDFs and
opaque PNGs. With the default 3840-pixel long side, an 11×22 strip becomes
1920×3840 pixels.

Generate or verify the styles independently with:

```sh
make generate-4-slice
make generate-8-slice
make generate-ck-slices
```

The design follows Gene Keyes's historical use of four tall Megamap strips,
while deliberately distinguishing exact octants from his eight square Beta-1
printing installments. Those square installments used a convenient straight
cut at the central `y = 10000` line rather than the diagonal Equator, so each
included material from a neighboring octant. See Keyes's
[Beta-1 Megamap](https://www.genekeyes.com/MEGAMAP-BETA-1/Megamap-Beta-1.html),
[full-size octants](https://www.genekeyes.com/1-DEG-GLOBE/8-octants.html), and
[one-octant construction workflow](https://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-%26-coastline.html).

## Myriahedral perspectives and face-group slices

The generation selector exposes five additional immutable depth-5
Myriahedral layouts: Americas, Atlantic, Afro Eur Asia, Pacific, and Antarctic.
Each has its own embedded Prim tree and planar registration, but uses the same
`44 × 24.75` carrier and Natural Earth water-layer pipeline as the reference
map. Generate their SVGs with:

```sh
make generate-water-myriahedral-perspectives
```

The requested two-way slice is an exact complementary partition of the
reference layout's 5120 terminal triangles. Group 1 contains 2722 faces
selected for North America, South America, Antarctica, Greenland, and Iceland;
group 2 contains the other 2398. Five retained hinges define the boundary.
The writer projects nothing a second time: it uses the union of each group's
carrier-space triangles as an SVG clip path around
`water-myriahedral-44-24.75.svg`, then adopts the group's tight `viewBox`.

The external `<use>` rule is the same as for Cahill-Keyes slices: the two
lightweight SVG wrappers must remain beside their master, while the PDF and
PNG derivatives are self-contained. Generate or verify them with:

```sh
make generate-myriahedral-slices
```

The complete configuration fields, alternate image links, hinge list,
selection method, face counts, and registered viewports are recorded in the
[Myriahedral implementation notes](myriahedral-implementation-notes.md#perspective-configuration-metadata)
and its [slicing section](myriahedral-implementation-notes.md#myriahedral-slicing).

## What the executable checks do—and do not—prove

The generators fail loudly on missing data, unsupported geometry types,
failed GDAL operations, invalid frame dimensions, non-finite projections,
materially out-of-frame coordinates, absent SVG layers, and unexpected
structural counts. This catches many broken-build and numeric regressions at
the point where the artifact is produced.

Those checks do not prove that:

- a polygon has no self-intersection after projection;
- an intended edge was split at every visual discontinuity;
- a simplification tolerance preserved every important small feature;
- labels do not overlap at every renderer zoom level;
- colors and line weights remain distinguishable for every viewer; or
- the separate Earth and water artifacts are perceptually balanced when
  composited.

Human review remains part of generation. Inspect the complete map, zoom into
all seams and poles, toggle layers in an SVG-aware editor, and check both
filled and outline features. The Earth and water files are currently much
larger than the geometry and graticule diagnostics, so browser and editor
performance is itself a practical review concern.

## Guidance for new generators

When adding another generated projection or layer:

1. Define the output frame and enforce its projection-specific aspect ratio.
2. Identify the projection's cuts in the same longitude registration used by
   its public API.
3. Split analytic lines explicitly and clip filled geographic topology before
   projection.
4. Densify in geographic space, then measure projected-space error at the
   intended display scale.
5. Preserve holes, stable IDs, source metadata, and meaningful layer groups.
6. Treat tiny seam strokes and epsilons as visible design decisions, not only
   numeric implementation details.
7. Add structural checks for dimensions, layer counts, provenance, and finite
   coordinates.
8. Review the resulting SVG perceptually; structural assertions cannot detect
   a convincing but incorrect fold.

---

[Documentation index](../index.md) ·
[Cahill-Keyes context](cahill-keyes-context.md)

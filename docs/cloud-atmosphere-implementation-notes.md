# Cloud-atmosphere generation implementation notes

[Documentation index](../index.md) ·
[Generation pipeline](generation.md) ·
[P-Tree download quick start](ptree-production-download.md) ·
[Source profile](../assets.static/cloud-atmosphere/README.md) ·
[Astronomy notes](astro-implementation-notes.md) ·
[Prerequisites](prerequisites.md)

## Stage 4.1a outcome

Stage 4.1a is feasible and implemented as
[`generate-cloud-atmosphere.cc`](../src.generate/generate-cloud-atmosphere.cc).
It produces one terrestrial, source-timed solar/cloud/atmosphere snapshot for
each production projection. Physical clouds use the confirmed
[JAXA/EORC P-Tree](https://www.eorc.jaxa.jp/ptree/) Himawari Level-2 Cloud
Property product, so cloud coverage is deliberately regional and daytime
only. Other observed layers come from the public
[JAXA Earth static STAC catalog](https://data.earth.jaxa.jp/stac/cog/v1/catalog.json).

This pass is not a weather forecast, a seamless global cloud composite, or a
simulated view from space. Every observed value retains its own source
interval and missing cells mean **unobserved**, never clear sky or zero.

## Boundary with astronomy

Atmospheric context was not already implemented by the astronomy pass. The
two passes now share time and solar calculations while preserving distinct
map domains:

| Concern | Astronomy owns | Cloud-atmosphere owns |
| --- | --- | --- |
| Coordinate domain | Celestial right ascension and declination | Terrestrial latitude and east-positive longitude |
| Sun | Apparent geocentric position among celestial sources | Subsolar latitude/longitude and surface illumination |
| Visibility | Observer horizon and instrument/darkness filters | Day, civil, nautical, astronomical twilight, and night zones |
| Observations | Stars, Solar System bodies, and transient catalogs | Cloud properties, aerosol optical depth, precipitation, and surface shortwave radiation |
| Timestamp | Astronomy profile timestamp | Generator process-start instant |
| Output contract | `astro-all-sky-*` and `astro-observer-*` | `cloud-atmosphere-*` |

[`generation-instant.h`](../src.generate/generation-instant.h) supplies strict
UTC parsing, Julian dates, `SOURCE_DATE_EPOCH`, and process clocks.
[`solar-geometry.h`](../src.generate/solar-geometry.h) supplies the shared
JPL-element solar ephemeris, Greenwich mean sidereal time, subsolar position,
solar altitude, and twilight classification. The astronomy implementation now
calls that same solar ephemeris, so the passes cannot quietly disagree about
the Sun.

## Source decision

The authoritative configuration is
[`cloud-atmosphere-profile.json`](../assets.static/cloud-atmosphere/cloud-atmosphere-profile.json).
The default source split is:

| Layer | Source and coverage | Freshness ceiling | Interpretation boundary |
| --- | --- | ---: | --- |
| Confident-cloud sample fraction | P-Tree Himawari-9 L2 CLP 1.0, 10-minute, about 5 km, 60°S–60°N and the Himawari disk | 6 h | Fraction of sampled QA pixels marked confidently cloudy; not a global cloud climatology |
| Cloud optical thickness | Same P-Tree observation | 6 h | Valid retrieved COT only |
| Cloud-top height | Same P-Tree observation | 6 h | Valid retrieved height converted to km when necessary |
| ISCCP cloud type | Same P-Tree observation | 6 h | Modal class among confidently cloudy samples |
| Aerosol optical depth at 500 nm | GCOM-C/SGLI L3 AROT v3 global daytime daily COGs | 96 h | Column aerosol loading; explicitly not observed smoke and not surface PM2.5 exposure |
| Gauge-adjusted precipitation rate | GSMaP standard Gauge 00Z–23Z v6 daily COGs, 60°S–60°N | 96 h | Daily precipitation-rate field expressed in mm h⁻¹; explicitly not flood, above-average-rainfall, or extreme-event counts |
| Surface shortwave radiation | JASMES Aqua/MODIS SWR v811 global daily COGs | 336 h | Latest available daily surface field, whose publication lag is visible in the legend |

The public JAXA catalog exposes overlapping numeric spatial-tile levels. The
resolver walks the static STAC hierarchy, accepts only observations ending no
later than the process instant, and selects only the most subdivided numeric
level. This avoids aggregating overlapping levels as if they were independent
samples. The audited item assets are `AROT`, `PRECIP`, and `swr`, each with
JAXA's DN-to-value and nodata metadata. The resolver supports the current
daily `DD` catalog leaves and compatible subdaily `DD-HH` leaves.

P-Tree is the default for physical clouds because it supplies COT, cloud-top
height, cloud type, and a documented cloud-confidence flag at useful
10-minute cadence. Its limitations are also material: the retrieval depends
on solar radiance, has no nighttime values, and covers the Himawari disk
rather than the whole Earth. The generator says so visibly instead of
interpolating or substituting model cloud.

## Time contract

The generator samples one process-start instant before loading data. All
calculated solar properties and all observation checks use that same value.
For reproducible generation, set `SOURCE_DATE_EPOCH` to an integer Unix UTC
timestamp; otherwise the system clock is sampled to whole seconds.

The time contract has four independent rules:

1. Calculated illumination is valid at process start.
2. Each source observation has its own start and end.
3. An observation ending after process start is rejected.
4. Each enabled layer rejects an observation older than its configured
   freshness ceiling.

This is a latest-not-after source mosaic, not a claim that all instruments
observed simultaneously. The SVG legend prints each layer's age, while root
metadata records the generation process instant, the fetch-selection process
instant, source endpoints, subsolar point, selection rule, and fixture status.

## P-Tree access and terms

For a copy-pasteable account, credential, connection-test, and production
workflow, start with the
[P-Tree production-download quick start](ptree-production-download.md).

P-Tree requires a registered account. The fetcher uses implicit FTPS on port
990 and `curl --netrc`; it never accepts credentials as command-line
arguments or writes them into a manifest. `make install-jaxa-certificate`
downloads and fingerprint-verifies the current SECOM root into private
per-user data; authorization and production fetching discover it automatically.
An explicit absolute `PTREE_CACERT` overrides that location. The existing user
entry is expected to resemble:

```text
machine ftp.ptree.jaxa.jp
  login ACCOUNT
  password PASSWORD
```

Do not add that file or its contents to this repository. The
[P-Tree terms](https://www.eorc.jaxa.jp/ptree/terms.html) require an account,
source acknowledgment, and a publication statement. The linked
[JAXA research-data terms](https://earth.jaxa.jp/en/data/policy/) govern use,
modification, distribution, upstream credits, and commercial-use notice.
Terms differ for some older Himawari/JMA data, so an operator publishing a
different historical snapshot must review the terms that apply to that
observation. Generated output visibly credits JAXA/EORC and the NASA source
of the JASMES MODIS layer.

Raw and prepared refresh products are ignored by Git because they are large,
mutable operational inputs. That repository policy is separate from the
source license.

## Acquisition and preparation

The normal workflow is explicit because it performs credentialed and network
I/O:

```sh
make fetch-cloud-atmosphere-data
make prepare-cloud-atmosphere-data
make verify-cloud-atmosphere-data
make generate-cloud-atmosphere
```

`fetch-cloud-atmosphere-data` captures the process instant, finds the newest
complete P-Tree H09 L2 CLP ten-minute interval within six hours, resolves the
three public STAC
collections, downloads their NetCDF/GeoTIFF assets, records source URLs and
observation intervals, and computes SHA-256 digests. Files are staged below
`assets.static/cloud-atmosphere/.raw/`; an interrupted refresh never replaces
the prepared snapshot.

`prepare-cloud-atmosphere-data` first recomputes every staged raster's
SHA-256 digest, then opens the configured P-Tree `CLOT`, `CLTH`,
`CLTYPE`, and `QA` NetCDF variables (with documented aliases for compatible
products) and the configured public COG variables
COGs through GDAL. It applies source or band scale, offset, nodata, and unit
metadata, bounds raster sampling to the configured maximum axis, and assigns
sample centers to resolution-3 H3 cells. For the evolving P-Tree grid, the
preparer recognizes both the published 2401×2401 grid whose first pixel center
is 80°E and a future-compatible 2801×2401 grid whose first center is 70°E when
a NetCDF lacks usable CF georeferencing.

Continuous layers use means, cloud type uses a deterministic mode, and cloud
fraction counts the confident-cloud QA state. A cell property is emitted only
when its valid-sample fraction reaches the configured 0.20 threshold. Every
feature stores the per-layer valid fraction, and every prepared observation
retains provenance. The final GeoJSON and checksum manifest are installed
atomically under `.prepared/`.

P-Tree QA follows the documented bit fields:

| Use | QA bits | Accepted state |
| --- | ---: | --- |
| Confident-cloud fraction | 3–4 | `11`, confidently cloudy |
| Cloud type | 3–4 | `11`, confidently cloudy |
| COT and cloud-top height retrieval | 0–2 | Every code except `011`, retrieval failed |

The verifier rejects a missing checksum, checksum drift, fixture data in the
production path, the wrong schema, missing observations, or altered
`unobserved-not-zero` semantics before Make invokes the renderer.

## Rendering contract

All source rasters become a common H3 observation model before projection.
The generator obtains each H3 boundary from the H3 library and sends it
through the same seam-aware spherical path machinery as the other terrestrial
passes. Values are quantized into six stable display bins. No planar raster
warp is reused across projections.

Each SVG contains these ordered groups:

1. `cloud-atmosphere-background`
2. `solar-illumination`, including 60°/30° daylight, horizon, civil,
   nautical, and astronomical solar-altitude contours plus `subsolar-point`
3. the seven profile layer IDs, when enabled
4. `terrestrial-coastline` from Natural Earth 1:10m
5. `legend-and-provenance`
6. `coverage-note`

Solar illumination is calculated as configurable 1°-sampled spherical
solar-altitude contours. Open projected fragments avoid false filled wedges
at interrupted projection cuts.
Observed properties are source-colored translucent H3 fills; AOD,
cloud-top height, and cloud type also use outlines to remain distinguishable
through overlap. The renderer intentionally rejects astronomy-only group
names such as `celestial-reference` and `observer-horizon`.

## Make and generation-profile integration

The source, profile, preparer, verifier, generator, and all six projection
rules are integrated into the top-level Makefile. Useful targets include:

```sh
make generate-cloud-atmosphere-cahill-keyes
make generate-cloud-atmosphere-projections
make generate-cloud-atmosphere-artifacts
make EXTERNAL_PASSES=jaxa-ptree generate-authorized-external
```

`generate-cloud-atmosphere` and `generate-cloud-atmosphere-projections`
produce six SVGs. `generate-cloud-atmosphere-artifacts` additionally exports
the corresponding PDF and PNG set. The generation-profile resolver accepts
`cloud-atmosphere` plus `clouds`, `atmosphere`, `solar-atmosphere`, and the
literal requested alias `solar/cloud/atmosphere`.

The last command is the credentialed end-to-end path: it installs the pinned
per-user certificate when missing, validates P-Tree access, then fetches,
prepares, verifies, and exports all six SVG/PDF/PNG sets. The narrower targets
remain useful for working from an already prepared snapshot.

The family is deliberately absent from `make all`: a standard offline build
cannot assume a P-Tree account or a current local observation snapshot. It is
still available through explicit targets and through a configured profile
that selects the pass. A missing prepared snapshot reports the exact fetch
and prepare commands instead of silently falling back to fixture data.

## Validation and fixture

[`cloud-atmosphere-fixture.geojson`](../assets.static/cloud-atmosphere/fixtures/cloud-atmosphere-fixture.geojson)
is a small synthetic, time-pinned H3 snapshot. It covers all source and layer
schemas while leaving part of the world without P-Tree values. It is marked
`fixture: true`; generated fixture SVGs retain that label and must never be
presented as observations.

The offline checks cover strict profile loading, source distinctions, P-Tree
QA rules, H3 geometry in all six projections, future and stale observation
rejection, `SOURCE_DATE_EPOCH`, pinned subsolar coordinates, exact shared Sun
coordinates with astronomy, SVG metadata semantics, and static-STAC
latest-not-after/overview selection. A fixture-backed render of each
projection supplies the final integration and visual smoke test.

## Deferred classifications

The initial pass stays narrow enough to remain physically legible:

| Candidate | Classification | Reason deferred |
| --- | --- | --- |
| Water vapor | Cloud-atmosphere extension | Appropriate snapshot layer, but no direct collection was selected from the current public JAXA catalog |
| GOSAT greenhouse gases | Climate-composition or Anthropocene extension | Sparse composition retrievals have different time and causal semantics from a weather snapshot |
| EarthCARE vertical cloud/aerosol profiles | Separate orbital-profile phase | Swath and vertical coordinates need altitude-aware rendering rather than flat global H3 fills |
| Forecast or reanalysis clouds | Optional modeled-atmosphere product | It could fill nighttime/global gaps, but must remain visibly separate from physical P-Tree retrievals |

These classifications preserve the confirmed physical-observation contract
without closing off a later modeled or altitude-aware phase.

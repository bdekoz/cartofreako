# Orbital Technosphere implementation notes

[Documentation index](../../../index.md) ·
[Generation pipeline](../getting-started/generation.md) ·
[Prerequisites](../getting-started/prerequisites.md)

## Current local selection

`make data-update` captures CelesTrak inputs into a complete validated edition
and automatically selects it for subsequent native/atlas builds. The two-hour
request policy remains; NASA may remain a dated historical validation
reference. The manifest records that distinction. Hubble observer elements
come from the same science catalog and are checked at the selected calculation
time. Japan observer profiles derive from that edition's inputs.

`make atlas-optional` freezes the edition across recursive builds and records
its ID and hashes in output metadata/receipts. For an older edition pass
`DATASET_MANIFEST=/absolute/path/to/dataset.json`; for checked repository
snapshots use `DATASET=legacy`. Direct orbital fetch targets retain their
candidate-review workflow. See [the complete workflow](../getting-started/generation.md#updating-all-configured-data-sources).

## Outcome and naming

Stage 4.2 is feasible as a visualization-grade generation pass and is
implemented under the public name **Orbital Technosphere**. That name makes
the subject explicit: the maps describe the human-built population and
infrastructure occupying Earth orbit, not every naturally orbiting body.

The requested entry point remains
[`src.generate/generate-orbiting.cc`](../../../src.generate/generate-orbiting.cc),
and Make targets retain `generate-orbiting` as a short command namespace.
Output files and document metadata use `orbital-technosphere`.

Other names considered were **Near-Earth Technosphere**, **Orbital
Infrastructure**, **Engineered Orbit**, **Artificial Sky**, **Anthropogenic
Orbit**, **Human-Made Orbital Population**, **Satellite Ecology**, and
**Celestial Infrastructure**. “Orbital Technosphere” best combines the
physical domain, human origin, and system-scale character without implying
that every object is currently functional.

## Source evaluation

No single NASA service provides the complete live Earth-orbiting population.
The implemented hybrid follows the roles each authoritative source can
actually support:

| Source | Evaluation | Role in this pass |
| --- | --- | --- |
| [NASA Planetary Data System](https://planetary.data.nasa.gov/find-data) | Durable archive for planetary missions, instruments, and derived data; not a comprehensive current Earth-satellite element catalog | Mission/archive context and the starting point requested for NASA research |
| [NASA SSCWeb REST services](https://sscweb.gsfc.nasa.gov/WebServices/REST/) | Authoritative ephemeris service for selected scientific spacecraft | Historical regression reference for ISS, Aqua, Landsat 9, and GOES 19 |
| [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) | High-value ephemerides but only a small subset of artificial Earth satellites | Evaluated, not used as the population feed |
| [CelesTrak GP data](https://celestrak.org/NORAD/documentation/gp-data-formats.php) | Broad public general-perturbations catalog with OMM-compatible CSV and documented SGP4 conventions | Primary active population, category membership, and bounded debris-event supplements |
| [Vallado/Crawford/Hujsak/Kelso SGP4](https://celestrak.org/publications/AIAA/2006-6753/) | Published reference implementation and verification vectors | Vendored propagation core |

The supplied [satellite-internet constellation](https://en.wikipedia.org/wiki/Satellite_internet_constellation)
and [satellite constellation](https://en.wikipedia.org/wiki/Satellite_constellation)
articles are useful terminology and historical context, but mutable secondary
pages are not reproducible calculation inputs. The supplied
[Starlink infrastructure essay](https://alpha60.co/2022/05/27/starlink-infrastructure/)
helped frame a constellation as infrastructure rather than isolated points;
its deployment counts are not used as catalog truth.

Legacy two-line element text is deliberately not the storage contract.
CelesTrak exhausted the original five-digit catalog-number namespace in 2026;
OMM CSV preserves larger `NORAD_CAT_ID` values and named fields. Cartofreako
stores catalog IDs as strings and initializes SGP4 directly from OMM fields.

## Reproducible profile and acquisition

[`orbital-technosphere-profile.json`](../../../assets.static/orbital-technosphere/20261109/orbital-technosphere-profile.json)
is authoritative. It records:

- calculation time `2026-11-09T01:12:00Z`;
- the make-invocation reference point, San Francisco at `37.7749° N`,
  `122.4194° W`, elevation 16 m, as an explicit profile value;
- SGP4, WGS-72, and AFSPC compatibility mode;
- maximum element age and future-epoch tolerance;
- horizon, illumination, display, label, track, and debris budgets;
- every catalog path and source URL; and
- snapshot collection times and checksum-file name.

Generation never infers a location from an IP address and never silently
uses the host clock. This keeps one build repeatable from any machine.

[`scripts/fetch-orbiting-data.sh`](../../../scripts/fetch-orbiting-data.sh)
invokes [the snapshot recorder](../../../scripts/refresh-orbiting-snapshot.py).
It reads all catalog URLs from the profile, validates OMM schemas, unique
NORAD IDs, finite elements, population limits and epoch freshness, then
installs a new dated directory with acquisition receipts and `SHA256SUMS`.
`make fetch-orbiting-data` writes a new directory under `build/`; use
`ORBITING_REFRESH_DIR` to select another new destination and
`ORBITING_TIMESTAMP` for an explicit calculation time. Selecting a refreshed
snapshot for generation is a separate profile change. Existing snapshots
are preserved. Ordinary generation and `make check-orbiting` are offline.

The fetcher honors CelesTrak's current usage policy: it reuses a complete
download inside the service's two-hour update interval and stops on any
CelesTrak HTTP error instead of retrying a 403 or 404. The shared download
cache is `build/orbital-technosphere-download-cache`.

The default November 9 snapshot contains 16,893 primary active records and 25
membership/debris catalogs, downloaded at 01:04 UTC. Of the active records,
16,867 pass the epoch freshness limits at the pinned calculation instant.
Both `make generate-orbiting` and the standalone fetch script select this
snapshot by default. The retained November 3 snapshot contains 16,844 primary
active records. At its pinned instant, 17,909 objects are plotted:
16,808 active records and 1,101 bounded debris records. Forty-four records
are excluded by the epoch filter; none failed propagation. The original
August snapshot remains the historical SGP4/NASA and Hubble test input.
The current NASA query was unreachable, so the new profile explicitly retains
the August reference as `historical-validation-only`; it is not a current
independent ephemeris comparison.

The active catalog is the one object population. Starlink, OneWeb, Kuiper,
Qianfan, Hulianwang, GNSS, communications, Earth-resource, science, and space
station files contribute membership rather than duplicate markers. Fengyun
1C, Iridium 33, and Cosmos 2251 debris-event catalogs supplement the active
population and are deterministically capped at 500 records per group.

## Propagation and coordinate pipeline

[`orbiting-data.h`](../../../src.generate/orbiting-data.h) validates the profile and
OMM schema, then converts OMM units to the reference SGP4 interface:

```text
mean motion:       rev/day   × 2π / 1440       → rad/min
mean-motion dot:   rev/day²  × 2π / 1440²      → rad/min²
mean-motion ddot:  rev/day³  × 2π / 1440³      → rad/min³
SGP4 epoch:        Julian date − 2433281.5
```

The upstream SGP4 record still has a five-character bookkeeping slot even
though the initializer accepts a longer identifier. Cartofreako retains the
real OMM identifier separately and passes a harmless five-character
placeholder to avoid truncation or overflow; the identifier does not enter
the propagation mathematics.

At the profile time, SGP4 produces a TEME position and velocity in kilometres
and kilometres per second. Greenwich sidereal time rotates TEME into an
Earth-fixed frame. An iterative WGS-84 ellipsoid solution supplies subpoint
latitude, longitude, and altitude. The observer path subtracts the WGS-84
site vector and derives east/north/up azimuth, elevation, range, and
topocentric right ascension/declination.

A low-precision solar vector supports two explicit boolean states. A
cylindrical Earth shadow labels an object `sunlit`; `optical-candidate` also
requires it to be above the configured horizon while the Sun is at or below
civil twilight (`−6°` in the captured profile). This is geometry only. It
does not estimate magnitude, attitude, flare probability, weather, or human
visibility.

## Products and detiling

The pass creates two products across all six projections:

- **Global** plots every admitted object's instantaneous terrestrial
  subpoint over a subdued Natural Earth 1:10m land base, adds the captured
  observer site, and traces one bounded representative ground track per
  configured group.
- **Observer** plots only objects above the captured horizon in topocentric
  celestial coordinates. The equator and exact profile horizon remain named
  reference layers.

This is a true generate pass, not a raster-tile mosaic. Every object is an
independent SVG marker. The current profile defines 18 named constellation
or fleet layers: Starlink, OneWeb, Kuiper, Qianfan, Hulianwang, Iridium,
Globalstar, ORBCOMM, Planet, Spire, Intelsat, SES, Eutelsat, Telesat, GPS,
GLONASS, Galileo and BeiDou. Generic role layers retain the other objects.
These names describe source catalogs, not an exhaustive operator registry.

Each parent contains `name` and `locpoint` sublayers, for example
`starlink/name` and `starlink/locpoint`. They are marked as editable Inkscape
layers. Every plotted object has one vector marker and a separate text label
using its original `OBJECT_NAME`; both carry the same `data-norad-id`.
In native generation, names default to hidden, with
`display.show_satellite_names` available to enable them. The name's
`data-locpoint-id` identifies its matching marker.
The earlier observer map showed a small representative selection of names.
The named-constellation renderer replaced that selection with the complete
hidden name layers; all 1,088 observer names remain in the current SVG.

Both products use black `x` marks for debris, eight-point sunbursts for
Starlink, squares for Intelsat, and upright triangles for the remaining
Earth-observation objects (including Planet and Spire). Other objects use
circles. Named groups retain their assigned colors. Debris remains solid
black while retaining illumination metadata.

On the native global sheet, `starlink/id` contains visible NORAD catalog IDs
at a physical 9 pt after map framing. The hidden Starlink name layer also uses
9 pt. No other vendor receives an ID layer;
observer ID layers are absent. The original name layers remain hidden.

Named membership is joined by NORAD ID. If catalogs overlap, the first named
catalog in profile order selects the one displayed parent; all memberships
remain in `data-groups`. The legend counts the displayed objects once and
uses the same colors and shapes as their markers. Iridium 33 debris remains
in the debris layer. The complete provenance and derived state are
embedded as `data-*` attributes, including catalog ID, COSPAR ID, group,
element epoch and age, terrestrial and observer coordinates, illumination,
candidate state, and source URL. Named profiles retain every admitted label;
the legacy label budget applies only to historical profiles without named
constellations. Representative tracks remain budgeted overlays.

Each map has a separate `-legend.svg` companion using the Setouchi ST2
typography, vertical headings, stacked keys and source bibliography. The
native map has proportional white margins and no overlaid legend. Both sheets
carry the calculation timestamp and source metadata; the legend embeds the
acquisition ledger. The Make composition step is
[`split-orbiting-plates.py`](../../../scripts/split-orbiting-plates.py).

Run all twelve map/legend pairs (24 SVG sheets) with:

```sh
make generate-orbiting
```

Family targets are `generate-orbiting-global` and
`generate-orbiting-observer`; projection targets use
`generate-orbiting-PROJECTION`. Override the input with
`ORBITING_PROFILE=/absolute/path/profile.json` using a current named-group
profile. `generate-orbiting-artifacts` also exports PDF and PNG companions.

The separate [MSP print studies](../../../output/msp-speculations-20261103/index.html)
cover the updated groundstations and both orbital subjects in the confirmed
Setouchi AuthaGraph frame, including its +4.35-inch printed horizontal move.
Four Randoma11y pairs replace the earlier green palettes: wine/amber,
ultramarine/porcelain, plum/ice blue and midnight blue/champagne. The light
member supplies type and groundstation marks/links over the dark ground.
Orbital markers and legend keys retain their original vendor/group colors.
These are intended
RGB hues; final printed color remains unmeasured with the reported low inks
and metallic glossy paper. Exact source pairs, recipes and hashes accompany
the sheets.

MSP speculation 4 is available in all four color pairs, each with the three
map/legend companions. It uses 1.5× Starlink sunbursts on both orbital plates.
Every MSP 4 global plate uses 6 pt Starlink IDs beneath all satellite markers;
studies 1–3 retain 9 pt. All current MSP terrestrial sheets place Antarctica
below labels and vectors. MSP 4's groundstation companion adopts the petal
capability visualization. Rebuild with `make msp-speculations`, which also
builds and verifies the capability studies used by that companion.

MSP speculation 5 is nested under
[`msp-speculation-5/`](../../../output/msp-speculations-20261103/msp-speculation-5/index.html),
with one subdirectory for each of the four color pairs. It adds the astronomy
all-sky map and attribution companion, using each pair's background and the
pinned 29 October 2026 sky. Both orbital plates retain distinct vendor colors
and 1.5× Starlink sunbursts. Global Starlink IDs remain 6 pt; representative
ground tracks use twice their original stroke width, with graticule widths
retained. Observer plates show only Starlink names, at 6 pt in their separate
name layer beneath all satellite markers.

### Default atlas presentation

`make atlas` adopts MSP 5 with **wine/amber** selected: `#240413` background
and `#fcc553` typography. Both orbital subjects use 1.5× Starlink sunbursts
and retain distinct vendor colors, black debris x marks with light halos,
Intelsat squares and residual Earth-observation triangles. Global Starlink
NORAD IDs and observer Starlink names use **6 physical pt**, with all satellite
markers above the text. Other name layers remain hidden. Global ground tracks
use twice the source stroke width; graticule widths are retained.

World global and observer sheets use the November 3 snapshot: **17,909 global
objects / 11,155 Starlink IDs**, and **1,088 observer objects / 549 Starlink
names**. The Japan global viewport uses those same global observations. The
Japan observer retains its **October 29 Setouchi** positions and memberships:
**1,078 objects / 471 Starlink names**. Its label size is compensated for the
viewport scale, and its separate legend records the older observation time.

These atlas settings are applied by
[`build-atlas-defaults.py`](../../../scripts/build-atlas-defaults.py).
The [atlas build guide](../getting-started/generation-styles.md#setouchi-st2-print-layout)
lists the saved recipe, build stages and validation commands. The native
`generate-orbiting` sheets described above retain 9 pt global IDs and hidden
observer names.

## Verification and accuracy boundary

[`tests/test-orbiting-generation.cc`](../../../tests/test-orbiting-generation.cc)
checks profile authority, fractional timestamps, six-digit catalog IDs,
catalog membership and budgets, WGS-84 round trips, finite propagated states,
and solar geometry. Its first propagation reproduces the published Vanguard
1 SGP4 TEME reference vector. ISS and GOES 19 are also compared with the
checked-in NASA SSCWeb GEO response at 15:36 UTC with deliberately
visualization-scale tolerances.

`make check-orbiting` runs the historical reference tests, the named grouping
tests and current snapshot checksums. `scripts/verify-orbiting-layers.py`
checks unique SVG IDs, exact marker/name pairing, original names, layer nesting,
visibility and conserved per-group counts against the selected profile. It
also verifies each marker shape, black debris strokes, matching companion
keys and attribution, and Starlink-only 9 pt IDs on native global plates.
All twelve global/observer map/legend pairs were checked for the November 3 snapshot;
each global product has 17,909 pairs and each observer product has 1,088 pairs.

For a composed default atlas, run
`python3 scripts/build-atlas-defaults.py --output output/atlas --check --skip-exports`
to verify the SVG receipts, 6 pt labels, name visibility, marker ordering,
sunburst scale and global track widths. Omit `--skip-exports` after a complete
atlas export to include the export hashes.

Each generator reopens its SVG and checks the projection viewBox, semantic
layers, profile timestamp, object count, horizon or terrestrial base, and
absence of non-finite coordinates. `make check` and ordinary generation need
no network access.

Public general-perturbations elements have finite age and observational
uncertainty. The TEME/Earth rotation omits full IERS polar motion and UT1
corrections, the solar model is approximate, and no covariance or maneuver
information is available. These products must not be used for conjunction
assessment, collision avoidance, operational tracking, antenna pointing,
navigation, or safety decisions.

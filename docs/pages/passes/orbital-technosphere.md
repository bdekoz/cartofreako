# Orbital Technosphere implementation notes

[Documentation index](../../../index.md) ·
[Generation pipeline](../getting-started/generation.md) ·
[Prerequisites](../getting-started/prerequisites.md)

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
| [NASA SSCWeb REST services](https://sscweb.gsfc.nasa.gov/WebServices/REST/) | Authoritative ephemeris service for selected scientific spacecraft | Checked-in independent position reference for ISS, Aqua, Landsat 9, and GOES 19 |
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

[`orbital-technosphere-profile.json`](../../../assets.static/orbital-technosphere/orbital-technosphere-profile.json)
is authoritative. It records:

- calculation time `2026-08-05T04:03:56Z`;
- the make-invocation reference point, San Francisco at `37.7749° N`,
  `122.4194° W`, elevation 16 m, as an explicit profile value;
- SGP4, WGS-72, and AFSPC compatibility mode;
- maximum element age and future-epoch tolerance;
- horizon, illumination, display, label, track, and debris budgets;
- every catalog path and source URL; and
- snapshot collection times and checksum-file name.

Generation never infers a location from an IP address and never silently
uses the host clock. This keeps one build repeatable from any machine.

[`scripts/fetch-orbiting-data.sh`](../../../scripts/fetch-orbiting-data.sh) performs
the explicit network refresh. It downloads OMM CSV groups and the NASA
SSCWeb JSON response into a temporary directory, checks schemas and a minimum
active-catalog size, installs the complete set only after all requests pass,
and writes `SHA256SUMS`. Ordinary generation and `make check` are offline.
The profile time and NASA query interval must be updated together for a new
capture.

The fetcher honors CelesTrak's current usage policy: it reuses a complete
snapshot inside the service's two-hour update interval and stops on any HTTP
error instead of retrying a 403 or 404. An intentional same-window request
requires `ORBITING_FORCE_REFRESH=1`; it should only be used after confirming
that no other process has downloaded the large groups for the current update.

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
independent SVG marker in a semantic role layer: megaconstellation,
navigation, communications, Earth observation, science, human presence,
other active, or debris. The complete provenance and derived state are
embedded as `data-*` attributes, including catalog ID, COSPAR ID, group,
element epoch and age, terrestrial and observer coordinates, illumination,
candidate state, and source URL. Labels and tracks are budgeted overlays;
they do not reduce the underlying marker population.

Run all 12 SVG products with:

```sh
make generate-orbiting
```

Family targets are `generate-orbiting-global` and
`generate-orbiting-observer`; projection targets use
`generate-orbiting-PROJECTION`. Override the input with
`ORBITING_PROFILE=/absolute/path/profile.json`.

## Verification and accuracy boundary

[`tests/test-orbiting-generation.cc`](../../../tests/test-orbiting-generation.cc)
checks profile authority, fractional timestamps, six-digit catalog IDs,
catalog membership and budgets, WGS-84 round trips, finite propagated states,
and solar geometry. Its first propagation reproduces the published Vanguard
1 SGP4 TEME reference vector. ISS and GOES 19 are also compared with the
checked-in NASA SSCWeb GEO response at 04:04 UTC with deliberately
visualization-scale tolerances.

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

# Astronomy generation implementation notes

[Documentation index](../../../index.md) ·
[Generation pipeline](../getting-started/generation.md) ·
[Astronomy data](../../../assets.static/astronomy/README.md) ·
[Prerequisites](../getting-started/prerequisites.md)

## Scope and products

`src.generate/generate-astro.cc` is a C++20 generation pass for naturally
occurring objects and events on the celestial sphere. Stage 13 produces three
explicit products through every production cartographic projection:

- `astro-all-sky-*` retains every object admitted by the ground profile's
  configured catalog budgets, without an observer-visibility filter;
- `astro-observer-ground-multiband-*` applies the San Francisco terrestrial
  horizon, twilight, band, and magnitude rules; and
- `astro-observer-hubble-*` propagates the Hubble Space Telescope orbit and
  applies its Earth-limb, Sun-avoidance, and UV/optical/near-IR band rules.

The filenames deliberately include `ground-multiband` or `hubble`; the
profile also embeds independent observer and instrument IDs. “Observer” is
therefore no longer ambiguous. All three products use the same pinned
calculation instant, catalog snapshots, celestial orientation, map frames,
and object identifiers, while each observer owns its visibility geometry and
instrument contract.

The pass includes bright stars, confirmed-exoplanet host systems, persistent
multi-wavelength sources, the Sun, Moon, seven major planets, four asteroids,
three comets, gamma-ray bursts, magnetar candidates, and X-ray transients. The
output is an instrument-aware map of source positions, not a simulated
photograph, mission pointing product, or physical spectral-energy rendering.

## Authoritative JSON profile

[`astro-profile.json`](../../../assets.static/astronomy/astro-profile.json) and
[`astro-hubble-profile.json`](../../../assets.static/astronomy/astro-hubble-profile.json)
are the sole authorities for timestamp, observer, and instrumentation. The
generator never infers them from the build host. Both profiles use schema
version 2 and the same pinned timestamp. Their distinguishing fields are:

```json
{
  "timestamp": "2026-08-05T01:59:44Z",
  "observer": {
    "id": "ground-multiband",
    "name": "San Francisco, California, USA",
    "kind": "terrestrial",
    "latitude_deg": 37.7749,
    "longitude_deg_east": -122.4194,
    "elevation_m": 16.0
  },
  "instrumentation": {
    "id": "generic-ground-multiband",
    "mode": "ground-multi-band"
  },
  "orientation": {
    "handedness": "celestial",
    "central_right_ascension_hours": 12.0
  },
  "dynamic_events": { "lookback_days": 7.0 }
}
```

```json
{
  "timestamp": "2026-08-05T01:59:44Z",
  "products": ["observer"],
  "observer": {
    "id": "hubble",
    "name": "Hubble Space Telescope",
    "kind": "orbiting",
    "norad_id": "20580",
    "maximum_element_age_days": 7.0,
    "earth_limb_avoidance_deg": 20.0,
    "sun_avoidance_deg": 60.3
  },
  "instrumentation": {
    "id": "hst-composite",
    "mode": "hst-composite",
    "bands": ["infrared", "optical", "ultraviolet"]
  }
}
```

`timestamp` accepts either an exact `YYYY-MM-DDTHH:MM:SSZ` UTC value or
`"now"`. The latter is sampled once when the process starts and the resolved
UTC value is embedded in the SVG metadata. A pinned value is preferable for
checked-in artifacts. Longitudes are degrees east, so San Francisco is
negative.

The complete schema is intentionally small and directly validated at load
time:

| Section | Fields and behavior |
| --- | --- |
| `products` | Ground enables `all-sky` and `observer`; Hubble enables only `observer` |
| `observer` | Stable ID/name and kind; terrestrial geodetic position or orbiting NORAD/OMM, freshness, Earth-limb, and Sun-avoidance fields |
| `orientation` | Celestial or terrestrial handedness and central right ascension in hours |
| `instrumentation` | Stable ID/name/mode and enabled bands; optional ground darkness, magnitude, altitude, and twilight rules |
| `dynamic_events` | Nonnegative past-looking interval in days |
| `display` | Upper bounds for stars, exoplanet hosts, and labels, plus reference-line switches |
| `catalogs` | Paths relative to the profile for Gaia, exoplanets, curated sources, and small bodies |

Ground elevation is preserved as provenance but is not yet used for topocentric
parallax, atmospheric refraction, extinction, or a terrain horizon. Those are
precision extensions, not silently implied by the observer filter.

## Orientation and projection mapping

Catalog right ascension is stored in degrees on `[0, 360)`, while declination
is stored in degrees on `[-90, 90]`. Right ascension in hours is converted with

```text
RA_degrees = 15 RA_hours.
```

The shared projection API expects geographic latitude and longitude. The
astronomy pass supplies declination as latitude and constructs a synthetic
longitude around the configured central right ascension `C`:

```text
celestial:    longitude = wrap180(C - RA)
terrestrial:  longitude = wrap180(RA - C).
```

The default therefore puts RA 12h at the center, RA 6h to its right, and RA
18h to its left. This is the conventional celestial-map handedness: looking
outward at the celestial sphere rather than inward at a terrestrial globe.

The resulting spherical points use the existing seam-aware path and point
dispatch for Cahill-Keyes, AuthaGraph, Dymaxion, Myriahedral, Star-X, and
Voronoi. Celestial equator, ecliptic, galactic equator, transient error
contours, and the observer horizon are sampled on the sphere before they are
split and projected. Point sources are never interpolated in the plane.

## Source evaluation and bounded snapshots

The requested source portals serve different roles. They are not
interchangeable catalogs:

| Source | Role in this pass |
| --- | --- |
| [NASA Planetary Data](https://planetary.data.nasa.gov/find-data) | Repository discovery and planetary-data provenance; JPL Solar System Dynamics supplies the calculation-ready elements |
| [JAXA Earth API](https://data.earth.jaxa.jp/en/) | Physical atmosphere and cloud observations owned by the separate Cloud-atmosphere pass; it does not provide celestial source coordinates and is not downloaded by astronomy |
| [China NSSDC](https://www.nssdc.ac.cn/nssdc_en/html/index.html) | Mission context for SVOM, Einstein Probe, ASO-S, and GECAM observations represented in the transient layer |
| [Gaia DR3](https://gea.esac.esa.int/archive/) | Bright-star positions, proper motions, magnitudes, and color indices |
| [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html) | Confirmed planets and host-system sky positions |
| [JPL approximate positions](https://ssd.jpl.nasa.gov/planets/approx_pos.html) | Calculation-ready mean orbital elements for the major planets |
| [JPL Small-Body Database API](https://ssd-api.jpl.nasa.gov/doc/sbdb.html) | Osculating elements and physical parameters for representative asteroids and comets |
| [CelesTrak science OMM](https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=csv) | Checked Hubble orbital elements, propagated with the repository's SGP4 implementation |
| [NASA GCN](https://gcn.nasa.gov/circulars/) | Timestamped transient positions, bands, and localization uncertainty |
| [NASA HEASARC](https://heasarc.gsfc.nasa.gov/) | Persistent high-energy and multi-wavelength source context |

`make fetch-astro-data` runs
[`fetch-astro-data.sh`](../../../scripts/fetch-astro-data.sh) and refreshes bounded
snapshots: 500 Gaia DR3 stars brighter than G 5.5, 250 nearby confirmed-planet
rows, and seven named JPL SBDB records. The script checks row counts and writes
`SHA256SUMS`. It does not modify the profile or the curated transient file.
Hubble's checked OMM row comes from
`assets.static/orbital-technosphere/celestrak-science.csv`, shared with the
Orbital Technosphere pass and refreshed deliberately by
`make fetch-orbiting-data`, not by `fetch-astro-data`.

This refresh target is not a prerequisite of `generate-astro` and is never
called by `generate-astro` or `make all`. Conversely, it does not invoke a
generator or create an SVG, PDF, or PNG. Normal users should generate directly
from the checked-in snapshots; maintainers use the fetch target only to propose
and review an intentional source-data update.

Normal generation is offline. Keeping acquisition separate avoids an
unreviewed upstream change altering a map during `make all`; a deliberate
refresh can instead be inspected together with its generated diff.

## Time and astrometric calculations

### Common time base

The parser resolves the profile timestamp to whole UTC seconds and computes
Julian date from Unix time `t`:

```text
JD = 2440587.5 + t / 86400.
```

Leap-second, UT1, polar-motion, and relativistic time-scale corrections are
outside this visualization pass. Every catalog is evaluated against the same
resolved `JD`.

### Gaia proper motion

Gaia DR3 coordinates are propagated linearly from epoch J2016.0. With elapsed
Julian years `Y`, catalog proper motions in milliarcseconds per year are
applied as

```text
RA  = RA_2016  + pmra  Y / (3.6e6 cos(dec_2016))
dec = dec_2016 + pmdec Y / 3.6e6.
```

Rows without proper motion retain their catalog coordinates. Radial velocity,
parallax, precession, nutation, aberration, and perspective acceleration are
not applied.

### Major planets and Sun

The major-planet implementation uses the JPL approximate elements valid from
1800 through 2050. Each element is evaluated linearly in Julian centuries
`T = (JD - 2451545.0) / 36525`. The mean anomaly is

```text
M = L - longitude_of_perihelion,
```

and eccentric anomaly is solved iteratively from Kepler's equation

```text
E - e sin(E) = M.
```

The ellipse coordinates

```text
x = a (cos(E) - e)
y = a sqrt(1 - e^2) sin(E)
```

are rotated by argument of perihelion, longitude of ascending node, and
inclination into heliocentric ecliptic coordinates. Subtracting Earth's vector
gives the geocentric planet vector; negating Earth's vector gives the Sun. A
fixed J2000 obliquity of `23.43928°` converts ecliptic vectors to equatorial
right ascension and declination.

The Moon uses a separate low-precision elliptic orbit. It is adequate for
placement at atlas scale but does not model the lunar perturbation series.

Each major planet also carries the JPL equatorial radius: Mercury
`2440.53 km`, Venus `6051.8 km`, Mars `3396.19 km`, Jupiter `71492 km`,
Saturn `60268 km`, Uranus `25559 km`, and Neptune `24764 km`. The geocentric
vector from the same orbital calculation supplies distance `D`; with the
astronomical unit fixed at `149597870.7 km`, the true apparent angular radius
is:

```text
alpha = asin(equatorial_radius_km / (D_AU × 149597870.7 km)).
```

These radii follow [JPL Solar System physical parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html),
and the angular interpretation follows the observer quantities documented by
the [JPL Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html).

True size and legibility are shown simultaneously. Every planet gets a
projected, dotted white outline at its calculated angular radius. Its colored
display glyph remains fixed-size because a true planet disk is generally too
small for this atlas; Stage 13 doubles that glyph from `0.075` to `0.15` page
inches. Thus the solid disk is explicitly a `2×` display-symbol revision, not
a claim of common physical scale, while the dotted outline is the true
geocentric apparent size. SVG attributes preserve equatorial radius, distance,
angular radius/diameter, display radius, and scale.

### Asteroids and comets

Every SBDB snapshot supplies an osculating epoch, semi-major axis,
eccentricity, inclination, node, argument of perihelion, mean anomaly, and
mean motion. The two-body propagation is

```text
M(JD) = M_epoch + mean_motion (JD - epoch).
```

The same Kepler solver and rotations produce a heliocentric vector, from which
the calculated Earth vector is subtracted. This ignores perturbations and can
degrade quickly for close approaches or long intervals from the SBDB epoch.

### Ground sidereal time, altitude, and horizon

For `D = JD - 2451545.0` and `T = D / 36525`, Greenwich mean sidereal time is

```text
GMST = wrap360(280.46061837 + 360.98564736629 D
               + 0.000387933 T^2 - T^3 / 38710000).
```

Local sidereal time adds the east-positive observer longitude. With hour
angle `H = LST - RA`, latitude `phi`, and declination `delta`, observer
altitude is

```text
sin(altitude) = sin(phi) sin(delta)
              + cos(phi) cos(delta) cos(H).
```

The observer map admits an object when its altitude is at least the configured
minimum and at least one object band is enabled. Infrared, optical, and
ultraviolet are disabled until the calculated Sun is at or below the
configured astronomical-twilight threshold. Optical objects with a magnitude
fainter than the configured limit do not qualify through the optical band.
Radio, microwave, X-ray, gamma-ray, neutrino, and gravitational-wave bands are
not coupled to daylight in this first instrumentation model.

At the checked-in timestamp the calculated Sun altitude over San Francisco is
about `13.18°`. The observer artifact consequently suppresses the optical,
infrared, and ultraviolet star field and emphasizes the above-horizon radio
and high-energy sky. This is an expected consequence of profile authority,
not a missing-catalog condition.

The visible-horizon path is generated by converting a complete azimuth sweep
at the minimum altitude back to equatorial coordinates. Thus its geometry is
derived from the same timestamp and observer as the object filter.

### Hubble orbit and pointing limits

The Hubble profile selects NORAD `20580` from the checked CelesTrak science
OMM catalogue. The shared SGP4 implementation propagates that element set to
the profile timestamp, rejects an epoch in the future or more than seven days
old, and converts the TEME state to a geodetic subpoint for provenance. The
Earth-center direction is the negative propagated position vector. At orbital
distance `d`, the apparent Earth angular radius is:

```text
earth_radius_angle = asin(6378.137 km / d).
```

For each celestial object the observer stores two angular quantities:

```text
earth_limb_clearance = separation(object, Earth center)
                       - earth_radius_angle
sun_separation = separation(object, Sun).
```

The Hubble product keeps an object only when limb clearance is at least
`20.0°`, Sun separation is at least `60.3°`, and at least one object band is
in the `hst-composite` infrared/optical/ultraviolet set. It has no terrestrial
horizon, daylight gate, or atmosphere. Its reference layer instead draws the
Earth limb, the configured limb-avoidance boundary, and the Sun-avoidance
boundary. These are reproducible visualization constraints, not a complete
HST scheduling or safety model.

### Dynamic events

The configured interval is a lookback window. An event is retained exactly
when

```text
0 <= calculation_timestamp - observed_timestamp <= lookback_days.
```

The default seven-day profile contains six GCN events. Their source time,
age, bands, position, and uncertainty remain machine-readable SVG attributes.
Localization circles use spherical destination-point geometry rather than a
constant planar radius.

## SVG structure

Each output carries these named groups:

| Layer | Contents |
| --- | --- |
| `astronomy-background` | Opaque dark celestial canvas |
| `celestial-reference` | Equator, ecliptic, galactic equator, plus ground horizon or Hubble Earth/Sun avoidance guides where applicable |
| `stars` | Gaia sources with magnitude-scaled, color-index-informed markers |
| `exoplanet-hosts` | Deduplicated host-system positions |
| `deep-sky` | Persistent galaxies, nebulae, remnants, black holes, binaries, and quasars |
| `solar-system` | Sun, Moon, planets, asteroids, and comets; planets include solid display glyphs and dotted true-angular-size outlines |
| `transients` | Recent events and their localization contours |
| `labels` | Budgeted labels for selected nonstellar objects |

The root metadata records the profile name, product, resolved timestamp,
observer/instrument IDs, orientation, enabled bands, transient interval, and
the planet sizing contract. Ground metadata adds reference coordinates and
calculated Sun altitude. Hubble metadata adds NORAD ID, OMM source and epoch,
element age, propagated subpoint/altitude, Earth angular radius, and avoidance
angles. Each object marker records its identifier, type, bands, RA,
declination, observer altitude or Earth-limb clearance, provenance URL, and
available magnitude, planet-size, event time, age, and uncertainty values.

One legacy Cahill-Keyes numerical hole can reject a sampled point on a large
transient contour. In that exceptional case only, the contour is rendered as
a marked planar fallback with `data-projection-fallback`; the correctly
projected source center and true angular uncertainty remain in metadata. The
other projections use the spherical contour without this fallback.

## Make targets and outputs

Use the checked-in profile by default:

```sh
make generate-astro
```

This is the complete normal astronomy command. It works offline and does not
need a preceding `make fetch-astro-data`. For an intentional catalog refresh,
use the distinct sequence:

```sh
make fetch-astro-data
git diff -- assets.static/astronomy
make generate-astro
make check
```

The first command changes bounded, reproducibility-sensitive inputs; the later
commands review their effect, render from them, and run the repository checks.

Select one product or projection with `generate-astro-all-sky`,
`generate-astro-observer-ground`, `generate-astro-observer-hubble`, the
two-observer aggregate `generate-astro-observer`, `generate-astro-cahill-keyes`,
`generate-astro-authagraph`, `generate-astro-dymaxion`,
`generate-astro-myriahedral`, `generate-astro-star-x`, or
`generate-astro-voronoi`. `generate-astro-projections` is an aggregate alias;
`generate-astro-artifacts` adds all SVG/PDF/PNG forms. Different authoritative
profiles can be supplied without editing the Makefile:

```sh
make ASTRO_PROFILE=/absolute/path/to/ground-profile.json \
  ASTRO_HUBBLE_PROFILE=/absolute/path/to/hubble-profile.json generate-astro
```

Every SVG is also part of `make all`, so Inkscape emits matching PDF and PNG
files. The public v13 names make the two observer/instrument combinations
unambiguous:

| Projection | All sky | Ground multiband | Hubble |
| --- | --- | --- | --- |
| Cahill-Keyes | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/png/astro-all-sky-ck-44-22.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/png/astro-observer-ground-multiband-ck-44-22.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/cahill-keyes/png/astro-observer-hubble-ck-44-22.png) |
| AuthaGraph | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/authagraph/png/astro-all-sky-authagraph-44-19.052559.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/authagraph/png/astro-observer-ground-multiband-authagraph-44-19.052559.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/authagraph/png/astro-observer-hubble-authagraph-44-19.052559.png) |
| Dymaxion | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/astro-all-sky-dymaxion-44-20.78461.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/astro-observer-ground-multiband-dymaxion-44-20.78461.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/dymaxion/png/astro-observer-hubble-dymaxion-44-20.78461.png) |
| Myriahedral | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/myriahedral/png/astro-all-sky-myriahedral-44-24.75.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/myriahedral/png/astro-observer-ground-multiband-myriahedral-44-24.75.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/myriahedral/png/astro-observer-hubble-myriahedral-44-24.75.png) |
| Star-X | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/star-x/png/astro-all-sky-star-x-34-44.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/star-x/png/astro-observer-ground-multiband-star-x-34-44.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/star-x/png/astro-observer-hubble-star-x-34-44.png) |
| Voronoi | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/voronoi/png/astro-all-sky-voronoi-44-22.916667.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/voronoi/png/astro-observer-ground-multiband-voronoi-44-22.916667.png) | [PNG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/tree/voronoi/png/astro-observer-hubble-voronoi-44-22.916667.png) |

The command-line program itself accepts
`generate-astro PROJECTION PRODUCT PROFILE.json`. Each invocation reopens its
SVG and verifies the frame, required layers, catalog budgets, object classes,
ground-horizon or Hubble-avoidance contract, observer/instrument identity,
planet-size outlines, timestamp metadata, and finite numeric output.

## Verification and accuracy boundary

[`test-astro-generation.cc`](../../../tests/test-astro-generation.cc) locks the
two profile identities, Julian and sidereal reference, celestial handedness,
ground-horizon round trip, SGP4 Hubble state, OMM freshness, Earth-limb and
Sun-avoidance filtering, catalog counts, event window, band/daylight
filtering, coordinate domains, planet radii/apparent sizes, and object-class
coverage. It also compares the approximate Sun and Jupiter positions with
pinned topocentric JPL Horizons values for San Francisco at the profile
timestamp. The differences remain comfortably below the test's `0.05°`
visualization tolerance.

This is not an observatory ephemeris. It does not yet use IAU SOFA/ERFA, IERS
Earth-orientation parameters, JPL DE kernels, SPICE, light-time, aberration,
precession/nutation, refraction, terrain, extinction, a point-spread function,
HST attitude/occultation scheduling, or per-instrument response curves. It
must not be used for telescope pointing,
navigation, occultation prediction, spacecraft operations, or safety-critical
decisions.

The implementation is deliberately staged so those improvements have clear
attachment points: SOFA/IERS for time and reference frames, SPICE or Horizons
for precision Solar System state, automated GCN/NSSDC ingestion for events,
and calibrated bandpass/sensitivity profiles for specific instruments. JAXA
physical cloud and atmospheric context is implemented independently by
[`generate-cloud-atmosphere.cc`](../../../src.generate/generate-cloud-atmosphere.cc),
while both passes share the same time and solar-geometry headers.

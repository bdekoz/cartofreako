# Astronomy generator data

`astro-profile.json` is the authoritative ground/all-sky configuration, and
`astro-hubble-profile.json` is the independent Hubble observer configuration.
Both store the calculation timestamp, stable observer and instrument IDs,
visibility constraints, and catalog paths. `timestamp` accepts an ISO-8601
UTC instant or the literal `now`; `now` is sampled exactly once when
`generate-astro` starts.

The checked-in ground profile uses the generation-session timestamp
`2026-08-05T01:59:44Z` and San Francisco, California, USA
(`37.7749`, `-122.4194`, 16 m elevation). The orientation defaults to
conventional celestial handedness with right ascension increasing leftward and
RA 12h at the projection center. The transient window defaults to seven days.
Its observer ID is `ground-multiband` and its instrument ID is
`generic-ground-multiband`.

The Hubble profile uses the same instant but selects NORAD `20580` from the
checked Orbital Technosphere CelesTrak science OMM catalog. Its observer ID is
`hubble`; its `hst-composite` instrument enables infrared, optical, and
ultraviolet sources subject to a 20° Earth-limb clearance and 60.3° Sun
avoidance. It produces only `astro-observer-hubble-*`; the ground product is
named `astro-observer-ground-multiband-*` so the platforms cannot be confused.

Run `make fetch-astro-data` to refresh the bounded catalog snapshots:

- 500 Gaia DR3 sources with `phot_g_mean_mag < 5.5`, ordered by magnitude;
- 250 nearby confirmed-planet rows from the NASA Exoplanet Archive;
- JPL Small-Body Database records for four representative asteroids and three
  representative comets.

The fetch is intentionally separate from SVG rendering. A normal generator run
is offline and reproducible from the profile and snapshots. Refreshing a
catalog may change results because the upstream archives evolve.

`curated-sky.json` adds a small multi-wavelength deep-sky collection and the
GCN transient snapshot associated with the checked-in timestamp. Its source
URLs preserve provenance for every item. JAXA Earth data is owned by the
separate Cloud-atmosphere generator and is not used as a celestial-position
catalog. Astronomy and Cloud-atmosphere share the solar ephemeris, but not
their observations or coordinate domains.

The Solar System calculations are visualization-grade. Major-planet positions
use the JPL Solar System Dynamics approximate Keplerian elements valid from
1800 through 2050. Small bodies use the osculating elements in their SBDB
snapshots and a two-body propagation. These results must not be used for
telescope pointing, navigation, occultation prediction, or other precision
work; JPL Horizons or SPICE is required for those uses.

Major planets use JPL equatorial radii and calculated geocentric distances to
draw a dotted outline at true apparent angular size. Their legibility glyph is
separate, fixed at 0.15 inch—twice the former 0.075-inch symbol. Metadata and
per-object attributes distinguish the physical outline from this display
scale.

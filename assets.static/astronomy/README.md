# Astronomy generator data

`astro-profile.json` is the authoritative configuration for the generated
astronomy products. It stores both the calculation timestamp and the observer
reference point. `timestamp` accepts an ISO-8601 UTC instant or the literal
`now`; `now` is sampled exactly once when `generate-astro` starts.

The checked-in profile uses the generation-session timestamp
`2026-08-05T01:59:44Z` and San Francisco, California, USA
(`37.7749`, `-122.4194`, 16 m elevation). The orientation defaults to
conventional celestial handedness with right ascension increasing leftward and
RA 12h at the projection center. The transient window defaults to seven days.

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

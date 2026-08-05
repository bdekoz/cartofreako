# Orbital Technosphere snapshots

This directory is the offline, reproducible input profile for the
`generate-orbiting` pass. The profile fixes both the calculation instant and
the observer at the location where this Stage 4.2 capture was invoked.

The primary catalog and group memberships are OMM-keyed CSV snapshots from
[CelesTrak](https://celestrak.org/NORAD/documentation/gp-data-formats.php).
OMM is used because legacy TLE catalog-number fields no longer represent the
complete catalog. Group files classify the same primary objects into
megaconstellation, navigation, communications, Earth-observation, science,
and human-presence layers. Three debris-event files are bounded supplements;
the profile caps each at 500 objects.

NASA sources provide context and independent checks:

- [NASA Planetary Data System](https://planetary.data.nasa.gov/find-data) was
  evaluated as the durable planetary and mission archive. It is not a live,
  comprehensive Earth-orbiting element service.
- [`nasa-ssc-reference.json`](nasa-ssc-reference.json) is an official NASA
  SSCWeb response for ISS, Aqua, Landsat 9, and GOES 19 around the profile
  time. Tests compare SGP4 results with these visualization-scale reference
  positions.
- NASA/JPL Horizons covers only a small subset of Earth satellites and itself
  directs comprehensive catalog use to services such as CelesTrak or
  Space-Track. That is why this pass deliberately uses a hybrid source model.

Run `make fetch-orbiting-data` to refresh all network snapshots atomically.
Refreshing changes the orbital state represented by the files; update the
profile timestamp and SSCWeb interval together before committing a new
reproducible capture. `SHA256SUMS` records every fetched input.

The fetcher follows CelesTrak's two-hour update/cache policy. A complete
snapshot less than two hours old is reused without a request, and any HTTP
error stops the refresh without replacing old inputs. Set
`ORBITING_FORCE_REFRESH=1` only for a deliberate refresh after confirming no
other process has downloaded the large groups during the current update.

The results are visualization-grade. Public general-perturbations elements,
the TEME-to-Earth rotation, and the low-precision solar illumination model do
not support conjunction assessment, collision avoidance, antenna pointing,
or operational navigation.

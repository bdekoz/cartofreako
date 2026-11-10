# Data update source coverage, 2026-11-09

This is a code-path audit of the default immutable-edition workflow, rather
than a provider availability test. `make data-update` and its `make update-data`
alias call the adapters in [`scripts/data-update.py`](../../scripts/data-update.py)
and [`scripts/data_sources.py`](../../scripts/data_sources.py).

## Covered by the default update

| Adapter | Acquisition scope |
| --- | --- |
| Natural Earth | Configured basemap release with checksum verification |
| Orbital | Current CelesTrak snapshot; optional historical NASA reference retains its period |
| Astronomy | Configured remote catalogs and selected object records; curated local inputs retain their dates |
| Anthropocene | CPC temperature, GHCN, EPA PM2.5, HMS smoke, Storm Events, CWFIS and required FIRMS; preparation and coverage checks |
| Resources | Configured resource feeds and audited annual mineral additions |
| Atmosphere | JAXA/CAMS acquisition, preparation and validation |
| Atoll | Configured USGS evidence, with its historical source periods |
| Network | Configured local snapshots/archives, synthesis and preparation; no external checkout pulls |
| Petroleum | Audited local EIA/OPEC tables, retaining their publication years |
| Ocean and ocean context | OISST, CRW coral context and JMA, with preparation and validation |
| India | Selected Indian OpenAQ PM2.5 station-days for optional heat–particulate coexposure |

The India fetcher is now named
[`fetch-india-openaq-pm25.py`](../../scripts/fetch-india-openaq-pm25.py).
It checks that the inventory declares India and that observations have Indian
coordinates and the expected local timezone. It is not a general OpenAQ
downloader. The old generic executable name is removed.

India daily archive bytes from January 2025 onward are preserved in the shared
`cache/india-openaq` directory. Each update refreshes listings and downloads only
missing daily archives. Earlier local downloads are imported and checked
against recorded hashes when available. Explicit manual `--refresh-since`
remains available for intentional revision acquisition. Download, import and
reuse counts are recorded in `openaq-quality.json` and the source record.

## Standalone acquisition and preparation outside the aggregate

| Source or step | Existing entry point | Gap and integration requirements |
| --- | --- | --- |
| Japan hourly PM2.5 | [`fetch-soramame-pm25.py`](../../scripts/fetch-soramame-pm25.py) | Not called by any default source adapter. Needs a station inventory and rolling observation windows; current default windows end September 2026. |
| China daily PM2.5 | [`fetch-cnemc-pm25.py`](../../scripts/fetch-cnemc-pm25.py) | Not called. Uses the Quotsoft mirror and requires a local CNEMC station inventory; default cutoff is October 28, 2026. |
| Asia PM2.5 native particulate enrichment | [`prepare-asia-pm25.py`](../../scripts/prepare-asia-pm25.py) | Not called. Merges Japan, China and India normalized observations into native particulate inputs. The default India adapter feeds the optional coexposure product, rather than this broader enrichment. |
| Additional India research context | [`fetch-india-particulate-context.py`](../../scripts/fetch-india-particulate-context.py) | Not called. Includes XKDR CPCB, rolling South Asia fire context, historical LongPMInd monthly files and IITM DSS discovery. XKDR 2025/2026 access requires `XKDR_API_KEY`; demo access covers 2024. Rolling fire data are not historical fire coverage. |
| ITU terrestrial fiber acquisition | [`fetch-itu-fiber.py`](../../scripts/fetch-itu-fiber.py) | Not called as a live refresh. The network adapter intentionally consumes configured local route snapshots. Switching this to provider acquisition changes that policy. |

ERA5 acquisition is not implemented by the India context adapter: it records
that CDS-authenticated acquisition is separate. It should not be described as
an already supported fetcher merely absent from the aggregate.

Integrating the Asia feeds would require inventories, date selection, persistent
archive caches, source records and validated output bindings. Running the
standalone scripts alone would not incorporate their results into the selected
immutable edition. These gaps are documented here; they are not silently added
to the required update set.

## Deliberately fixed or derived inputs

- PurpleAir experiments use checked rendering anchors, rather than live sensor
  observations. There is no live PurpleAir observation fetcher to invoke.
- Water-debris uses checked historical station observations and contextual
  sources; it has no general live observation downloader.
- GPU/consumer layout inputs and projection/oracle fixtures are versioned test
  or presentation inputs. Their maintainer refresh targets do not belong in
  routine observational acquisition.
- Network swarm, groundstation, CDN, cable/IXP and geolocation inputs are
  configured local snapshots. The update copies/prepares them without pulling
  their external repositories. Petroleum and audited mineral publications also
  keep their actual source periods.
- `fetch-marshall-islands-sources` builds derived cloud SVG/PNG assets; the
  atmosphere adapter handles the underlying observations.
- `fetch-ocean-stage-2.py` restores frozen legacy inputs. Current ocean and
  India adapters provide the current-edition path.

`DATASET=legacy` follows a fixed historical Make target list and has narrower
coverage than the default edition workflow. It should not be used to assess
the default adapters' coverage.

## Validation

`tests/test-india-openaq-cache.py` checks cross-edition reuse, legacy imports,
checksum rejection, preservation of old edition bytes after explicit refresh,
new-day discovery and the India adapter command. `tests/test-data-update.py`
checks the Make alias, duplicate-target suppression and error propagation
without contacting providers.

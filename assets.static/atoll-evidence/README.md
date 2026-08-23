# Majuro atoll-evidence canary inputs

[Stage 15 ledger](../../docs/development/20260815_stage-15.md) ·
[canary report](../../reports/stage-15-atoll-evidence-canary.md) ·
[source manifest](../../fixtures/atoll-evidence/v1/manifest.json)

This directory separates authoritative public source packages from compact,
checked exploration derivatives used by the Stage 15 Majuro evidence canary.
It does not define a standard or optional generation pass.

## Storage boundary

`assets.static/atoll-evidence/.raw/` contains the original USGS archives,
catalog responses, and metadata. The complete directory is explicitly ignored
by Git. In particular, the 2,355,022,535-byte 1 m TBDEM archive and the
80,927,783-byte inundation archive are local source evidence, not repository
or release payloads.

`prepared/` contains three checked approximately 10 m GeoTIFF derivatives:

| Derivative | Source grid | Preparation |
| --- | --- | --- |
| `majuro-tbdem-observation-10m.tif` | USGS 1 m Float32 topobathymetric DEM | Average resampling; 4,623 × 2,381; source CRS, LMSL heights, and NoData retained |
| `majuro-marine-inundation-30in-deterministic-10m.tif` | USGS 1 m Byte 30-inch static-water scenario | Nearest-neighbor resampling; 3,973 × 1,272 |
| `majuro-marine-inundation-30in-probability-10m.tif` | USGS 1 m Float32 probability field | Average resampling; 3,973 × 1,272; values remain zero through one |

These derivatives are review and rendering conveniences. They are not a
replacement for the authoritative 1 m packages and may not lend their nominal
resolution to freshwater, infrastructure, shoreline, reef, or ocean-heat
claims.

`context/water-myriahedral-pacific-700x394.png` is a fixed 8-bit sRGB
derivative of the Stage 14 authoritative Myriahedral Pacific water raster. It
is only a planetary locator. Keeping this 219,197-byte input checked makes the
canary generator offline and prevents a clean clone from transitively fetching
Natural Earth merely to rebuild the inset.

## Explicit workflow

Fetching, preparation, generation, and checking are separate operations:

```sh
# Network operation; writes only to ignored .raw/.
make fetch-atoll-evidence-data

# Local source conversion; requires the two raw archives.
make prepare-atoll-evidence-data

# Offline fixture and PNG generation from checked compact inputs.
make build-atoll-evidence-fixtures
make generate-atoll-evidence-canary

# Rebuild the exploration PNG and check hashes, dimensions, schemas,
# ignored-source boundaries, and face-qualified forward/reverse traces.
make check-atoll-evidence-canary
```

No target above is included by `make all`, ordinary `make check`, a GitHub
release, or the human-invoked UCB AAO/S3 path. `prepare-atoll-evidence-data`
does not fetch, and generation never reads or downloads the raw archives.

## Evidence and uncertainty

- The TBDEM is a 1944–2016 multi-source composite in ITRF2008 / UTM zone
  59N with local mean-sea-level heights. Published validation reports land
  RMSE 0.197 m, Landsat-derived bathymetry RMSE 1.066 m, and
  WorldView-3-derived bathymetry RMSE 1.112 m. These are source-class values,
  not one per-cell certainty field.
- The selected inundation layer is a modeled 0.762 m, or 30-inch, water level
  above Mean Higher High Water. It is not an observed flood. The source gives
  cumulative vertical RMSE 0.192 m and a separate probability surface from
  750 Monte Carlo DEM realizations.
- Freshwater spatial evidence, authoritative infrastructure, a current
  independent shoreline, reviewed benthic reef geometry, and local/regional
  governance review remain unavailable or incomplete and are not rendered.

The [manifest](../../fixtures/atoll-evidence/v1/manifest.json) is the
machine-readable authority for package hashes, preparation history, layer
status, output identity, and claim boundaries.

# Resources Stage 12 snapshot

This directory contains the checked, offline inputs for the six resource
families documented in
[`docs/resources-implementation-notes.md`](../../docs/resources-implementation-notes.md).

- `resources-profile.json` is the strict
  `cartofreako-resources-profile-v3` source/metric catalogue and release-gate
  contract.
- `resources-values.json` is the
  `cartofreako-resources-values-v3` store with 1,679 normalized country
  records.
- `countries-110m.geojson` is Natural Earth 5.1.1 Admin-0 geometry with the
  normalized `RESOURCE_A3` join key.
- `coral-reefs-025deg.geojson` contains 7,215 quarter-degree cells derived
  from actual WRI reef polygons and their integrated local-threat classes.
- `SHA256SUMS` authenticates all four checked data files.

Ordinary generation is network-free. `make check` validates both JSON
contracts, six family defaults, all 14 released metrics, country and spatial
release gates, record counts, geometry joins, reef statistics, and digests.

## Released products

| Family | Products |
| --- | --- |
| `resources-energy` | Solar and wind installed capacity; operating nuclear capacity; petroleum refinery throughput (public alias `petrochemical`) |
| `resources-food` | Food production index |
| `resources-fauna` | Total fisheries production; coral-reef integrated local threat |
| `resources-flora` | Forest area as a percentage of land |
| `resources-mineral` | Rare-earth mine production |
| `resources-human` | Population under 30; population 60+; upper-secondary attainment; bachelor’s attainment; resident patent applications per million person-years |

Country metrics pass either the broad country/population gate or the
source-world-output gate appropriate to producer and count-activity
statistics. The patent rate uses the latter and separately discloses its
country/population coverage. The reef field passes its separate
spatial-domain gate. Missing always means unknown, never zero.

The coral-reef preparation audits 24 WRI source features and 63,383 reef
polygons, assigns each polygon by an interior point to a 0.25° cell, and keeps
the highest Low/Medium/High/Very High threat class where polygons overlap.
The result indicates reef presence and threat class, not fractional reef area
within each cell.

## Source boundary

The snapshot is a normalized factual extract, not a redistribution of the
upstream reports. The profile records source URL, release, retrieval date,
license note, and SHA-256 digest/status.

- Natural Earth 5.1.1 Admin-0 geometry is public domain.
- IRENA *Renewable Capacity Statistics 2026* supplies 2025 solar and wind
  capacity.
- IAEA RDS-2/45 supplies operating nuclear capacity at 31 December 2024.
- UN Energy Statistics supplies current petroleum refinery throughput; rows
  older than 2018 are excluded from the rendered product.
- USGS *Mineral Commodity Summaries 2026* supplies estimated 2025 rare-earth
  mine production.
- World Development Indicators supplies the FAO food, forest, and fisheries
  series plus population, education, and patent inputs under CC BY 4.0.
- WRI *Reefs at Risk Revisited* supplies the 500 m reef/threat geometry under
  CC BY 3.0.

## Explicit refresh workflow

A refresh can change observations, geometry, coverage, names, and visual
output and is therefore a maintainer action:

```sh
make refresh-resources-data
make check
git diff -- assets.static/resources
```

`scripts/fetch-resources-data.sh` downloads the pinned inputs into a temporary
directory. `scripts/prepare-resources-data.py` performs deterministic joins,
age/rate derivations, reef reduction, release-gate calculations, schema
emission, and checksums; the preparer itself never downloads data.

Before accepting a refresh, review source names, URLs, terms, and digests;
IRENA/IAEA/USGS table anchors and totals; all country-name joins; the human
age and patent formulas; current-year filters; country/output/spatial gates;
and generated visual/XML diffs in all six projections.

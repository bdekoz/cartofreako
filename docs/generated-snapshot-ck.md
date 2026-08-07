# Cahill–Keyes generated snapshot

[Documentation index](../index.md) ·
[Generation guide](generation.md) ·
[Stage 12 implementation notes](stage-12-implementation-notes.md) ·
[S3 v12 publication](releases/s3-v12.md)

This contact sheet covers every credential-free Cahill–Keyes whole-map pass
in the Stage 12 release graph, plus the explicitly retained legacy
Anthropocene atlas. Each preview is a real 480-pixel-wide PNG generated from
the corresponding layered SVG. Select a thumbnail to open the S3-hosted viewer,
which streams the matching `.svg.gz` object through the browser's
`DecompressionStream` API and displays the full-resolution SVG. The previews,
viewer, and compressed SVGs are served from the same immutable public S3
release at `cartofreako/v12/`, whose
[completion marker](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/release.json)
records its source commit, inventory, manifest, and HTTP delivery contract.

Generate or refresh the complete sheet with:

```sh
make generate-snapshot-ck
```

## Projection foundations

| Pass | Preview |
| --- | --- |
| Native geometry | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=geometry-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/geometry-ck-44-22.png" width="360" alt="Cahill-Keyes native geometry"></a> |
| Graticules | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=graticules-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/graticules-ck-44-22.png" width="360" alt="Cahill-Keyes graticules"></a> |
| Earth | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=earth-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/earth-ck-44-22.png" width="360" alt="Cahill-Keyes Earth"></a> |
| Water | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=water-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/water-ck-44-22.png" width="360" alt="Cahill-Keyes water"></a> |

## Sky and orbital passes

| Pass | Preview |
| --- | --- |
| Astronomy — all sky | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=astro-all-sky-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/astro-all-sky-ck-44-22.png" width="360" alt="Cahill-Keyes all-sky astronomy"></a> |
| Astronomy — observer | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=astro-observer-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/astro-observer-ck-44-22.png" width="360" alt="Cahill-Keyes observer astronomy"></a> |
| Orbital Technosphere — global | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=orbital-technosphere-global-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/orbital-technosphere-global-ck-44-22.png" width="360" alt="Cahill-Keyes global orbital technosphere"></a> |
| Orbital Technosphere — observer | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=orbital-technosphere-observer-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/orbital-technosphere-observer-ck-44-22.png" width="360" alt="Cahill-Keyes observer orbital technosphere"></a> |

## Networks and Anthropocene

| Pass | Preview |
| --- | --- |
| Network swarm | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=network-swarm-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/network-swarm-ck-44-22.png" width="360" alt="Cahill-Keyes network swarm"></a> |
| Network infrastructure sites | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=network-infrastructure-sites-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/network-infrastructure-sites-ck-44-22.png" width="360" alt="Cahill-Keyes network infrastructure sites"></a> |
| Anthropocene — 2025 default | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=anthropocene-temperature-2025-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/anthropocene-temperature-2025-ck-44-22.png" width="360" alt="Cahill-Keyes Anthropocene 2025"></a> |
| Anthropocene — 2026 default | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=anthropocene-temperature-2026-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/anthropocene-temperature-2026-ck-44-22.png" width="360" alt="Cahill-Keyes Anthropocene 2026"></a> |
| Anthropocene — legacy observation atlas | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=anthropocene-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/anthropocene-ck-44-22.png" width="360" alt="Cahill-Keyes legacy Anthropocene observation atlas"></a> |

## Stage 12 resources

| Pass | Preview |
| --- | --- |
| Energy — solar | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-energy-solar-capacity-2025-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-energy-solar-capacity-2025-ck-44-22.png" width="360" alt="Cahill-Keyes solar capacity"></a> |
| Energy — wind | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-energy-wind-capacity-2025-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-energy-wind-capacity-2025-ck-44-22.png" width="360" alt="Cahill-Keyes wind capacity"></a> |
| Energy — nuclear | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-energy-nuclear-operating-capacity-2024-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-energy-nuclear-operating-capacity-2024-ck-44-22.png" width="360" alt="Cahill-Keyes nuclear operating capacity"></a> |
| Energy — petrochemical refinery throughput | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-energy-petrochemical-refinery-throughput-latest-2024-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-energy-petrochemical-refinery-throughput-latest-2024-ck-44-22.png" width="360" alt="Cahill-Keyes petroleum refinery throughput"></a> |
| Food — production index | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-food-food-production-index-2022-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-food-food-production-index-2022-ck-44-22.png" width="360" alt="Cahill-Keyes food production index"></a> |
| Fauna — fisheries | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-fauna-fisheries-production-latest-2024-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-fauna-fisheries-production-latest-2024-ck-44-22.png" width="360" alt="Cahill-Keyes fisheries production"></a> |
| Fauna — reefs | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-fauna-coral-reef-threat-2011-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-fauna-coral-reef-threat-2011-ck-44-22.png" width="360" alt="Cahill-Keyes coral reef threat"></a> |
| Flora — forest area | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-flora-forest-area-percent-2023-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-flora-forest-area-percent-2023-ck-44-22.png" width="360" alt="Cahill-Keyes forest area"></a> |
| Mineral — rare-earth production | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-mineral-rare-earth-mine-production-2025-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-mineral-rare-earth-mine-production-2025-ck-44-22.png" width="360" alt="Cahill-Keyes rare-earth production"></a> |
| Human — under 30 | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-human-population-under-30-2024-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-human-population-under-30-2024-ck-44-22.png" width="360" alt="Cahill-Keyes population under 30"></a> |
| Human — over 60 | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-human-population-over-60-2024-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-human-population-over-60-2024-ck-44-22.png" width="360" alt="Cahill-Keyes population over 60"></a> |
| Human — upper-secondary attainment | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-human-upper-secondary-attainment-latest-2025-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-human-upper-secondary-attainment-latest-2025-ck-44-22.png" width="360" alt="Cahill-Keyes upper-secondary attainment"></a> |
| Human — bachelor’s attainment | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-human-bachelors-attainment-latest-2024-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-human-bachelors-attainment-latest-2024-ck-44-22.png" width="360" alt="Cahill-Keyes bachelor's attainment"></a> |
| Human — resident patent applications | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=resources-human-resident-patent-applications-per-million-2019-2021-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/resources-human-resident-patent-applications-per-million-2019-2021-ck-44-22.png" width="360" alt="Cahill-Keyes resident patent applications per million"></a> |

## Art pass

| Pass | Preview |
| --- | --- |
| Bathymetry Roulette | <a href="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/viewer.html?asset=bathymetry-roulette-ck-44-22.svg.gz"><img src="https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v12/tree/thumbnail/cahill-keyes/bathymetry-roulette-ck-44-22.png" width="360" alt="Cahill-Keyes Bathymetry Roulette"></a> |

Credentialed P-Tree cloud-atmosphere and licensed network-topology products
are intentionally excluded from this default sheet. After the operator has
completed the provider-side account or terms step, `make authorize-external`
verifies the local P-Tree, NASA FIRMS, and topology authorization boundary;
the optional products remain separate generation targets.

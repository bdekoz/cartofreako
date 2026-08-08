{% assign release_base = "https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13" %}
{% assign viewer_base = release_base | append: "/viewer.html?asset=" | append: page.projection_key | append: "/svg/" %}
{% assign preview_base = release_base | append: "/" | append: page.preview_path %}

# {{ page.projection_name }} generated snapshot

[Documentation index](../index.html) ·
[AuthaGraph](generated-snapshot-authagraph.html) ·
[Cahill–Keyes](generated-snapshot-ck.html) ·
[Dymaxion](generated-snapshot-dymaxion.html) ·
[Myriahedral](generated-snapshot-myriahedral.html) ·
[Star-X](generated-snapshot-star-x.html) ·
[Voronoi](generated-snapshot-voronoi.html)

[Generation guide](generation.html) ·
[Stage 13 convergence notes](converge-generation-13.html) ·
[S3 v13 publication](releases/s3-v13.html)

This contact sheet covers every {{ page.projection_name }} whole-map pass in
the complete Stage 13 release graph, including its authorized P-Tree
Cloud-atmosphere snapshot and the explicitly retained legacy Anthropocene
atlas. Each preview is an immutable public PNG rendered at contact-sheet
width; offscreen previews are loaded only as they approach the viewport.
Select an image to open the S3-hosted viewer, which streams the matching
`.svg.gz` object through the browser's `DecompressionStream` API and displays
the full-resolution SVG. The previews, viewer, and compressed SVGs are served
from the same immutable public S3 release at `cartofreako/v13/`, whose
[completion marker]({{ release_base }}/release.json) records its source
commit, inventory, manifest, and HTTP delivery contract.

## Projection foundations

| Pass | Preview |
| --- | --- |
| Native geometry | <a href="{{ viewer_base }}geometry-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/geometry-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} native geometry"></a> |
| Graticules | <a href="{{ viewer_base }}graticules-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/graticules-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} graticules"></a> |
| Earth | <a href="{{ viewer_base }}earth-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/earth-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Earth"></a> |
| Water | <a href="{{ viewer_base }}water-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/water-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} water"></a> |

## Sky and orbital passes

| Pass | Preview |
| --- | --- |
| Astronomy — all sky | <a href="{{ viewer_base }}astro-all-sky-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/astro-all-sky-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} all-sky astronomy"></a> |
| Astronomy — ground multiband observer | <a href="{{ viewer_base }}astro-observer-ground-multiband-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/astro-observer-ground-multiband-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} ground multiband observer astronomy"></a> |
| Astronomy — Hubble observer | <a href="{{ viewer_base }}astro-observer-hubble-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/astro-observer-hubble-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Hubble observer astronomy"></a> |
| Orbital Technosphere — global | <a href="{{ viewer_base }}orbital-technosphere-global-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/orbital-technosphere-global-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} global orbital technosphere"></a> |
| Orbital Technosphere — observer | <a href="{{ viewer_base }}orbital-technosphere-observer-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/orbital-technosphere-observer-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} observer orbital technosphere"></a> |

## Networks and Anthropocene

| Pass | Preview |
| --- | --- |
| Network swarm | <a href="{{ viewer_base }}network-swarm-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/network-swarm-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} network swarm"></a> |
| Network infrastructure sites | <a href="{{ viewer_base }}network-infrastructure-sites-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/network-infrastructure-sites-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} network infrastructure sites"></a> |
| Fiber Synthesized | <a href="{{ viewer_base }}fiber-synthesized-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/fiber-synthesized-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Fiber Synthesized cleaned union"></a> |
| Cloud-atmosphere — authorized P-Tree snapshot | <a href="{{ viewer_base }}cloud-atmosphere-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/cloud-atmosphere-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} authorized P-Tree cloud and atmosphere snapshot"></a> |
| Anthropocene — 2025 default | <a href="{{ viewer_base }}anthropocene-temperature-2025-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/anthropocene-temperature-2025-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Anthropocene 2025"></a> |
| Anthropocene — 2026 default | <a href="{{ viewer_base }}anthropocene-temperature-2026-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/anthropocene-temperature-2026-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Anthropocene 2026"></a> |
| Anthropocene — legacy observation atlas | <a href="{{ viewer_base }}anthropocene-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/anthropocene-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} legacy Anthropocene observation atlas"></a> |

## Stage 12 resources

| Pass | Preview |
| --- | --- |
| Energy — solar | <a href="{{ viewer_base }}resources-energy-solar-capacity-2025-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-energy-solar-capacity-2025-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} solar capacity"></a> |
| Energy — wind | <a href="{{ viewer_base }}resources-energy-wind-capacity-2025-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-energy-wind-capacity-2025-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} wind capacity"></a> |
| Energy — nuclear | <a href="{{ viewer_base }}resources-energy-nuclear-operating-capacity-2024-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-energy-nuclear-operating-capacity-2024-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} nuclear operating capacity"></a> |
| Energy — petrochemical refinery throughput | <a href="{{ viewer_base }}resources-energy-petrochemical-refinery-throughput-latest-2024-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-energy-petrochemical-refinery-throughput-latest-2024-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} petroleum refinery throughput"></a> |
| Food — production index | <a href="{{ viewer_base }}resources-food-food-production-index-2022-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-food-food-production-index-2022-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} food production index"></a> |
| Fauna — fisheries | <a href="{{ viewer_base }}resources-fauna-fisheries-production-latest-2024-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-fauna-fisheries-production-latest-2024-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} fisheries production"></a> |
| Fauna — reefs | <a href="{{ viewer_base }}resources-fauna-coral-reef-threat-2011-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-fauna-coral-reef-threat-2011-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} coral reef threat"></a> |
| Flora — forest area | <a href="{{ viewer_base }}resources-flora-forest-area-percent-2023-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-flora-forest-area-percent-2023-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} forest area"></a> |
| Mineral — rare-earth production | <a href="{{ viewer_base }}resources-mineral-rare-earth-mine-production-2025-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-mineral-rare-earth-mine-production-2025-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} rare-earth production"></a> |
| Human — under 30 | <a href="{{ viewer_base }}resources-human-population-under-30-2024-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-human-population-under-30-2024-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} population under 30"></a> |
| Human — over 60 | <a href="{{ viewer_base }}resources-human-population-over-60-2024-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-human-population-over-60-2024-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} population over 60"></a> |
| Human — upper-secondary attainment | <a href="{{ viewer_base }}resources-human-upper-secondary-attainment-latest-2025-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-human-upper-secondary-attainment-latest-2025-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} upper-secondary attainment"></a> |
| Human — bachelor’s attainment | <a href="{{ viewer_base }}resources-human-bachelors-attainment-latest-2024-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-human-bachelors-attainment-latest-2024-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} bachelor's attainment"></a> |
| Human — resident patent applications | <a href="{{ viewer_base }}resources-human-resident-patent-applications-per-million-2019-2021-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/resources-human-resident-patent-applications-per-million-2019-2021-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} resident patent applications per million"></a> |

## Art pass

| Pass | Preview |
| --- | --- |
| Bathymetry Roulette | <a href="{{ viewer_base }}bathymetry-roulette-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/bathymetry-roulette-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Bathymetry Roulette"></a> |
| Bathymetry Hamonshū | <a href="{{ viewer_base }}bathymetry-hamonshu-{{ page.artifact_suffix }}.svg.gz"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/bathymetry-hamonshu-{{ page.artifact_suffix }}.png" width="360" alt="{{ page.projection_name }} Bathymetry Hamonshū"></a> |

The P-Tree account workflow was completed explicitly for this release, so its
Cloud-atmosphere product is part of the sheet rather than being implied by a
clean checkout. Licensed network topology remains outside this release sheet.
NASA FIRMS remains an unrendered review candidate until deliberate promotion;
it is not a missing map layer.

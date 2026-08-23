# Resources Stage 12 enrichment plan

[Documentation index](../../../../index.md) ·
[Generation methods](../../getting-started/generation-methods.md) ·
[Generation guide](../../getting-started/generation.md) ·
[Metric catalog](metric-catalog.md) ·
[Stage 12 implementation](../../../development/20260815_stage-12.md)

## Status and recommendation

Stage 12 is implemented as six independently sourced product families:

- `resources-energy`;
- `resources-food`;
- `resources-fauna`;
- `resources-flora`;
- `resources-mineral`; and
- `resources-human`.

`resources-flora` is the canonical spelling; `ressources-flora` remains an
input alias. `fisheries` and `reefs` select `resources-fauna`.

The normalized v3 contract now releases 14 products: four energy metrics,
food production, fisheries, coral-reef threat, forest area, rare-earth mine
production, and five human metrics. Each has its own artifact, unit, period,
source class, and country or spatial release gate. The catalogue continues to
record crops, livestock, land cover, biodiversity, critical minerals, legal
policy, travel, reading, and mobility candidates with honest lifecycle
status.

See the [resource metric catalog](metric-catalog.md) for the complete
59-entry lifecycle view and the explicit distinction between standard,
optional, and exploration-only passes.

Facility, deposit, biodiversity-occurrence, travel, and legal-policy layers
can enrich those global baselines. They must not be used to make a sparse point
inventory look globally complete.

The superseded feasibility work is not a v3 data source and is documented only
in [generation methods](../../getting-started/generation-methods.md). The v3 files, parser, renderer,
tests, Make rules, and generated names contain no legacy values or output path.

## Product and artifact contract

Each category is a **target family**. It can produce several metric-specific
maps; it is not one image with unrelated quantities painted on top of one
another. A static PNG or PDF should display one metric and unit. A layered SVG
may retain compatible supporting layers such as a country field and audited
facility points, but it must not create a cross-metric resource score.

Released artifact names carry family, metric, reference period, and
projection:

```text
resources-energy-solar-capacity-2025-ck-44-22.svg.gz
resources-energy-wind-capacity-2025-star-x-34-44.svg.gz
resources-fauna-coral-reef-threat-2011-ck-44-22.svg.gz
resources-flora-forest-area-percent-2023-voronoi-44-22.916667.svg.gz
resources-mineral-rare-earth-mine-production-2025-ck-44-22.svg.gz
resources-human-population-over-60-2024-ck-44-22.svg.gz
```

Rolling-latest products state their actual accepted year range in the legend
and preserve each country's observation year. Prefer a common complete year
when the source supports it.

Implemented target semantics are:

```sh
make generate-resources-energy
make generate-resources-food
make generate-resources-fauna
make generate-resources-flora
make generate-resources-mineral
make generate-resources-human
make generate-resources-stage12
```

`generate-resources` and the generation-profile selector `resources` expand
to all six families. `generate-resources-FAMILY-PROJECTION` builds every
released metric in that family, while `generate-resources-PROJECTION` builds
all 14 released products for that projection. `generate-resources-stage6b`
is a compatibility alias for the current graph.

Continue the existing deterministic compression rule: validate and export
from a plain SVG intermediate, then store the checked SVG as GNU gzip level 9
without a filename or timestamp header.

## Evidence classes and non-sparse gate

### Geometry and evidence classes

Every normalized record must declare both its evidence class and geography:

| Evidence class | Geography | Examples | Rendering role |
| --- | --- | --- | --- |
| Reported statistic | ISO 3166 / UN M49 area | national production, attainment, patents | Country choropleth; show missing countries distinctly |
| Modeled or remote-sensed field | Raster or H3 cell | crop allocation, land cover, tree density | Filled global or biome-domain cells with valid-area coverage |
| Audited facility or field | Point, polygon, or line | reactor, mine, oil/gas field, refinery | Supplemental marks above a non-sparse baseline |
| Legal or policy observation | Jurisdiction and review date | equality law, same-sex law, drug possession penalty | Country layer with explicit dimensions, source date, and exceptions |
| Derived statistic | Source geography plus formula | patents per million, population under 30 | Same geography as inputs; preserve formula and all input versions |

Reported, modeled, remotely sensed, legal, and derived values remain separate
in schema, layer identifiers, legends, and metadata. Facility presence does
not establish production, a law on the books does not establish enforcement,
and a modeled field is not an observation.

### Release gate

A released Stage 12 metric is non-sparse only when it meets one of these gates:

- a global field has valid values for at least 99% of its declared land,
  ocean, or biome-domain cells, excluding a source-declared mask;
- a human country statistic covers at least 80% of mapped countries **and**
  at least 90% of the mapped world population;
- a production or capacity statistic covers at least 90% of the
  source-reported world output for that commodity and discloses named
  producer coverage when the source supplies that denominator; or
- a rate derived from a count-based activity covers at least 90% of the
  compatible source-world numerator and discloses country and population
  coverage separately; or
- a legal dataset reviews at least 190 economies or all 193 UN member states
  under one documented methodology.

If a source cannot supply the denominator needed for a gate, report country
count, regional gaps, and covered population or production separately and
classify the metric as supplemental. Never use the number of point features as
evidence of global completeness.

An observed zero is a record with positive source coverage. A missing record
is unknown, never zero. No default map should impute missing country values.
Modeled estimates may fill a field only when they are explicitly identified as
modeled and kept distinct from reports.

The strongest first-wave non-sparse options are:

| Family | Baseline | Why it avoids point sparsity |
| --- | --- | --- |
| Energy | IRENA/PRIS/EIA country capacity, generation, and production | Values are attached to complete country areas; facilities provide optional detail |
| Food | FAOSTAT country series, SPAM crop grid, and GLW livestock grid | Country totals cover the atlas while global modeled grids distribute selected production |
| Flora | Copernicus or MODIS global land-cover fields plus FRA country statistics | Remote sensing supplies continuous spatial coverage and FRA supplies a separate national evidence class |
| Mineral | Current USGS/BGS country production and reserves | Country output coverage is measurable against the reported world total; deposits are optional context |
| Human | WPP age structure, WBL legal dimensions, and coverage-gated UIS/WIPO/UNDP indicators | Broad country/population denominators are explicit and missing countries remain visible |

## Recommended sources and measures

The sources below are candidates for a pinned snapshot, not blanket approval
to redistribute every upstream file. Before promotion, record the exact
release, retrieval date, URL, digest, license, attribution, API or form terms,
and whether raw or only derived data may be checked in.

### `resources-energy`

| Requested concept | Primary non-sparse layer | Spatial enrichment | Boundary |
| --- | --- | --- | --- |
| Solar power | [IRENA Renewable Capacity Statistics 2026](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2026/Mar/IRENA_DAT_RE_capacity_statistics_2026.pdf) 2025 capacity by country; IRENA tools for generation | [Global Integrated Power Tracker](https://globalenergymonitor.org/projects/global-integrated-power-tracker/) facilities | Capacity, generation, and proposed projects are separate measures |
| Wind power | IRENA 2025 capacity and separately sourced generation by country | Global Integrated Power Tracker facilities | Separate onshore/offshore where the source permits |
| Nuclear | [IAEA PRIS](https://pris.iaea.org/PRIS/home.aspx) operating capacity and generation | Reactor locations and status from PRIS | Do not count under-construction or shutdown units as operating |
| Oil wells | [EIA international](https://www.eia.gov/opendata/) country production | [Global Oil and Gas Extraction Tracker](https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/) fields and extraction areas | A globally complete open well-level inventory was not identified; label fields as fields, not wells |
| Petroleum refining | EIA country refinery capacity and throughput | Audited refinery tracker if its release and terms pass review | Capacity is not throughput and neither is extraction |
| Petroleum processing | Define a specific process before ingestion | Facility data only after scope and units are fixed | “Processing” is too broad for a comparable scalar |
| Natural-gas refining | Rename to gas processing and LNG | [Global Gas Infrastructure Tracker](https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/) terminals and pipelines | LNG terminals and pipelines do not enumerate all gas-processing plants |
| Natural-gas fracking | Country unconventional-gas production where explicitly reported | GOGET assets with a sourced extraction-method field | No defensible, comprehensive global fracked-well layer was identified; keep supplemental |

The non-sparse energy backbone should therefore be country capacity,
generation, production, refinery capacity, and throughput. Facility and field
trackers improve geography, but their inclusion thresholds and lifecycle
statuses mean that absence is not evidence that a country has no activity.

### `resources-food`

| Measure | Recommended source | Coverage role | Boundary |
| --- | --- | --- | --- |
| Crops and other primary food production | [FAOSTAT](https://www.fao.org/faostat/en/#home) annual country production | Non-sparse country baseline | Keep tonnes, harvested area, and yield separate |
| Spatial crop production | [IFPRI SPAM](https://mapspam.info/data/) 2020 v2 | Global 10 km allocation for 46 crops | Modeled spatial allocation for 2020, not a current farm census |
| Livestock | FAOSTAT country totals plus [Gridded Livestock of the World](https://www.fao.org/livestock-systems/global-distributions/en/) | Country baseline plus aligned 2020 spatial density | Animal counts, biomass, meat, milk, and eggs are different measures |
| Fish | FAOSTAT capture fisheries and aquaculture | Broad annual country coverage | Keep wild capture, aquaculture, aquatic animals, and plants separate |
| Edible nutrition | FAOSTAT Food Balances | Dietary energy and protein supply by country | Food supply is not production, consumption, nutrition outcome, or food security |

Use separate metric maps for crop production, livestock density, capture
fisheries, aquaculture, dietary-energy supply, and protein supply. A single
“food” tonnage is invalid because water content and edible fraction make
unlike commodities incomparable. If an aggregate is needed later, convert
with a cited food-composition method and publish the formula and uncertainty.

### `resources-flora`

| Requested concept | Recommended source | Coverage role | Boundary |
| --- | --- | --- | --- |
| Plant life and land-cover class | [Copernicus Global Land Cover and Forest Monitoring](https://land.copernicus.eu/en/products/global-dynamic-land-cover/land-cover-2020-raster-10-m-global-annual) | Continuous 10 m global field, initially 2020 | Land cover is not species diversity |
| Long annual land-cover series | [MODIS MCD12Q1](https://lpdaac.usgs.gov/products/mcd12q1v061/) | Global annual 500 m classification | Coarser and classification-dependent; do not silently splice with 10 m classes |
| Forest extent, type, and change | [FAO Global Forest Resources Assessment 2025](https://www.fao.org/forest-resources-assessment/en/) | 236 countries and areas with forest variables | National reporting and remote sensing are different evidence classes |
| Forest-cover density | Copernicus tree-cover-density products | Continuous values over the product's declared domain | Current pan-tropical products are not a global all-biome field |
| Savanna and tropical rainforest | Land-cover class intersected with a pinned ecological-zone layer | Non-sparse biome-domain field | Publish the exact class crosswalk; neither biome is a simple tree-percentage threshold |
| Plant biodiversity | [GBIF](https://www.gbif.org/) vascular-plant occurrences plus survey-effort metadata | Supplemental research layer | Raw occurrence richness is dominated by sampling effort and is not a biodiversity census |

The default flora products should be land-cover fractions by H3 cell, forest
area/change by country, and explicitly defined forest, savanna, and tropical
rainforest masks. Plant biodiversity should remain supplemental until the
pipeline can model observation effort, taxonomic coverage, duplicates,
coordinate quality, and survey design. At minimum, render a separate sampling
effort/coverage layer beside any derived richness estimate.

### `resources-mineral`

The retired dataset must not supply Stage 12 mineral values. The primary
current sources should be:

- the [USGS Mineral Commodity Summaries 2026](https://pubs.usgs.gov/publication/mcs2026),
  which reports 2025 world production, reserves, and context for more than 90
  mineral commodities and materials; and
- [BGS World Mineral Production 2020–2024](https://www.bgs.ac.uk/news/latest-data-on-world-mineral-production-now-available/),
  which supplies an independent multi-year country series for more than 70
  commodities.

Use USGS as the release-year backbone and BGS for cross-checks, trends, and
commodity definitions. Store disagreements rather than silently selecting the
larger value. [IAEA UDEPO](https://nucleus.iaea.org/Pages/udepo.aspx) can add
uranium-deposit context, but its selective coverage and update metadata make
it a supplemental deposit layer, not the non-sparse uranium baseline.

The initial critical-mineral catalogue should include:

- rare-earth elements, with light/heavy groups and scandium/yttrium separated
  only where the source actually reports them;
- uranium and the battery materials lithium, cobalt, nickel, natural graphite,
  and manganese;
- grid and electronics inputs including copper, aluminum/bauxite, gallium,
  germanium, indium, tellurium, and silicon metal;
- strategic alloy and manufacturing inputs including antimony, tungsten, tin,
  tantalum, niobium, titanium, and vanadium;
- platinum-group metals; and
- phosphate rock and potash because energy-transition materials do not replace
  agricultural mineral dependence.

“Critical” is a jurisdiction- and year-specific policy designation. Store any
US, EU, IEA, or other criticality-list membership as dated metadata rather
than excluding a commodity or inventing one timeless worldwide criticality
score.

For every commodity, preserve distinct measures for mine production, refined
production, processing capacity, reserves, resources, and trade. Do not add
them or show them on one numeric scale. A country choropleth of current mine
production or reserves is the non-sparse default. Mine and deposit points are
supplemental because there is no single current, open, globally comprehensive
facility database with consistent status and capacity fields.

Normalize units only through a commodity-specific rule. Record source units,
conversion factors, contained-material versus gross-ore basis, fiscal versus
calendar year, source estimates, withheld values, and whether “rare earths”
are reported as rare-earth-oxide equivalent. Missing and withheld values stay
distinct from zero.

### `resources-human`

| Requested measure | Definition and source | Non-sparse treatment |
| --- | --- | --- |
| Literacy | Adult literacy, age 15+, from the [UNESCO UIS Data Browser](https://databrowser.uis.unesco.org/) and its [2026 release](https://www.uis.unesco.org/en/news/2026-education-data-refresh) | Latest accepted observation within a declared year window; expose each country's year and missingness |
| High school or equivalent | Population age 25+ completing ISCED 3 or higher, UIS | Do not use enrollment or expected schooling as attainment |
| College | Population age 25+ completing ISCED 6 or higher, UIS | Keep short-cycle ISCED 5 separate unless the metric is explicitly “tertiary” |
| Advanced degree | Population age 25+ completing ISCED 7 or 8, UIS | Preserve sex disaggregation where coverage passes the gate |
| Patents per capita | Resident-origin patent applications from [WIPO IP Statistics](https://www.wipo.int/en/web/ip-statistics/about), divided by matched population | Use a three-year mean per million residents; applications are not grants or patent quality |
| Population under 30 | Ages 0–29 divided by all ages from [UN World Population Prospects 2024](https://www.un.org/development/desa/pd/content/World-Population-Prospects-2024) | Broad, same-model country coverage; mark projected rather than estimated years |
| Population over 60 | Ages 60+ divided by all ages from WPP 2024 | Use `60+` literally; do not substitute retirement age |
| Gender equality | [World Bank Women, Business and the Law](https://wbl.worldbank.org/en/data/download-data) legal/support/enforcement dimensions and [UNDP Gender Inequality Index](https://hdr.undp.org/data-center/thematic-composite-indices/gender-inequality-index) outcomes | Render law and outcome measures separately; never call either complete social equality |
| Social mobility | [World Bank GDIM](https://www.worldbank.org/en/topic/poverty/brief/what-is-the-global-database-on-intergenerational-mobility-gdim) education and income mobility | Education has broad population coverage; cohort estimates are not a current-year behavior metric |

UIS attainment definitions must be fixed in the metric catalogue before data
preparation. “College” is ambiguous across national systems; ISCED levels make
the cross-country rule explicit. Literacy and attainment should use a rolling
latest-observation window only when a common year is too sparse, and every map
must include a recency layer or hatch.

The requested quality-of-life candidates need these substitutions or limits:

| Request | Decision | Defensible option |
| --- | --- | --- |
| Percentage taking one international trip in the current year | Do not implement under that label | [UN Tourism / World Bank outbound departures](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/ST.INT.DPRT) per 100 residents for the latest complete year, labelled **departures**, because repeat trips mean it is not a percentage of unique people |
| Median books read in a calendar year | Omit from the default pass | No harmonized, current, worldwide median dataset was identified; use UIS reading proficiency or a separately reviewed library-use statistic, clearly labelled as a different concept |
| Sexual freedom | Do not create one score | Use dated legal dimensions from [ILGA World Laws on Us](https://ilga.org/wp-content/uploads/2024/05/Laws_On_Us_2024.pdf), such as consensual same-sex criminalization, recognition, expression, and legal gender recognition; preserve exceptions and enforcement caveats |
| Drug decriminalization | Do not infer a scalar from a law repository | Build a reviewed jurisdiction-by-dimension table from the [UNODC legal database](https://www.unodc.org/LSS/Country/List) and named specialist sources: possession, use, cultivation, substance, quantity, sanction, and review date |
| Social mobility | Include with time/cohort warning | GDIM education mobility is the broadest baseline; income mobility is a lower-coverage supplemental layer |

Better broad-coverage quality-of-life additions are:

- [UNDP HDI](https://hdr.undp.org/data-center/human-development-index), with
  its health, education, and income components also available separately;
- [WHO healthy life expectancy](https://www.who.int/data/global-health-estimates),
  labelled as a modeled comparable estimate;
- WHO/UNICEF JMP “at least basic” drinking water and sanitation from the
  [global WASH database](https://washdata.org/), using “safely managed” only
  where its lower country coverage passes the gate; and
- World Bank access to electricity and internet-use indicators, rendered as
  separate infrastructure-access measures rather than a quality-of-life
  composite.

Do not average these into a cartofreako quality-of-life index. If a published
source composite such as HDI or GII is rendered, preserve its source name,
version, component definitions, and source methodology.

## Normalized data contract

The implemented country baseline uses a long-form metric catalogue and one
normalized country-value store:

```text
assets.static/resources/resources-profile.json
assets.static/resources/resources-values.json
assets.static/resources/countries-110m.geojson
assets.static/resources/coral-reefs-025deg.geojson
assets.static/resources/SHA256SUMS
```

The profile contains the source register, complete six-family metric
catalogue, palettes, default selection, artifact tags, and coverage. Every
normalized value contains:

```json
{
  "family": "resources-human",
  "metric": "population-under-30",
  "iso3": "USA",
  "year": 2024,
  "value": 38.2,
  "state": "derived"
}
```

Catalogue metadata includes title, definition notes, unit, evidence class,
scale, snapshot/reference period, source release/URL/retrieval time/digest or
ingestion status, license boundary, lifecycle status, and coverage.

Implemented geography rules are:

- use normalized ISO3 `RESOURCE_A3` keys and retain Natural Earth source codes
  in the checked geometry;
- pin the boundary dataset and record aggregation for territories and disputed
  areas;
- never join by display name;
- keep reported/estimated/derived values, zeros, and missing distinct; and
- emit machine-readable country, population, output, or spatial coverage for
  every released product.

Future grid and facility stores remain separate extensions. H3 resolution 3
is a sensible default display grid for global raster fields, but preparation
must area-weight source pixels and retain valid-area fractions. High-resolution
source rasters remain source inputs; checking one SVG polygon per 10 m pixel
into the repository is neither necessary nor tractable.

## Acquisition and reproducibility

Normal generation remains offline. Acquisition is an explicit maintainer
operation:

```sh
make refresh-resources-data     # explicit network plus deterministic preparation
make check                      # schemas, hashes, joins, coverage, renderer tests
git diff -- assets.static/resources
```

The implemented fetcher writes upstream files to an automatically removed
temporary directory and never runs as a dependency of `make`, `make all`, or a
generation-profile target. The deterministic preparer can also be invoked
against audited local inputs. A maintainer reviews license and source changes,
compares coverage and totals with the previous snapshot, and accepts the
checked v3 files and checksums only after review.

APIs, forms, credentials, and manual downloads need source-specific adapters.
The repository should not bypass a download form, invent an API, or treat
interactive access as permission to redistribute a full raw dataset.

## Implementation sequence and status

### 1. V3 and Stage 12 cutover — complete

- The profile, normalized values, country/spatial parser, renderer, focused
  tests, Make rules, selectors, and artifact names are v3-only.
- The metric catalogue, source manifest, ISO3 concordance, value states,
  derived-age formulas, and country/population/output coverage are checked.
- Fourteen non-sparse products generate across all six projections and are
  stored as deterministic `.svg.gz` archives.
- The patent-rate product uses the count-activity gate: 93 countries account
  for 95.814% of the compatible resident-application numerator; it does not
  silently treat unreported countries as zero.

### 2. Broaden each family — in progress

- Energy: wind, nuclear, and refinery throughput are released; next add
  separately labeled generation, extraction, gas-processing, and explicitly
  unconventional-gas measures.
- Food/fauna: fisheries is released; next add separately labeled FAOSTAT
  crops, aquaculture, food balances, and livestock.
- Flora: add Copernicus/MODIS land cover plus FRA forest variables.
- Mineral: add current USGS commodities and BGS trend cross-checks for the
  catalogued critical-mineral shortlist.
- Human: age 60+, two attainment levels, and resident patent applications are
  released; literacy and advanced degrees remain planned after failing the
  current gate, with WBL/GII dimensions still separate future products.

### 3. Add spatial enrichment — in progress

- Coral-reef threat is released from actual WRI geometry. Add SPAM crops, GLW
  livestock, land-cover H3 fields, PRIS reactors, GEM
  energy facilities/fields, and audited mineral points.
- Require every point source to document inclusion thresholds, coordinate
  quality, lifecycle/status values, last review, and known geographic gaps.
- Add GBIF plant richness only with sampling effort and sensitivity tests.

### 4. Add policy and quality-of-life dimensions

- Add travel departures only under the corrected label.
- Implement legal dimensions rather than a sexual-freedom or drug-freedom
  score.
- Add GDIM mobility with cohort/reference-period metadata.
- Omit books-read median until a source passes definition, country, population,
  recency, and redistribution gates.

### 5. Promote additional defaults

- Keep one metric/unit per static artifact and add a metric-bearing output tag.
- Require the appropriate coverage gate before a metric becomes a default.
- Generate all six projections, deterministic `.svg.gz` files, PDFs, and PNGs;
  compare coverage reports and visual fixtures before promotion.

## Release checks

Every Stage 12 snapshot and metric should require:

- a pinned release, raw digest, retrieval date, source URL, rights decision,
  and source citation;
- exact metric definitions and units, including commodity-specific conversion
  rules;
- the relevant non-sparse coverage gate or an explicit `supplemental` status;
- no values from retired datasets and no missing-to-zero conversion;
- country-name-independent joins and a reviewed territory concordance;
- per-country observation years for rolling-latest metrics;
- separate evidence classes and no unlike-source composite score;
- source totals reconciled before and after preparation within a documented
  tolerance;
- all six projection structural checks and finite coordinates;
- deterministic gzip output and a bulk decompression test; and
- a visible legend statement for modeled, remote-sensed, legal, derived, or
  incomplete layers.

## Deferred or rejected shortcuts

- Do not relabel retired categories and call the result current.
- Do not use mine, well, reactor, plant, GBIF, or survey points as a substitute
  for a coverage denominator.
- Do not imply that GOGET extraction areas enumerate individual oil or fracked
  gas wells.
- Do not merge crop tonnes, livestock heads, fish tonnes, calories, and protein
  into one “food production” value.
- Do not infer plant biodiversity from forest density or raw GBIF occurrence
  counts.
- Do not combine mine production, refined production, reserves, resources,
  processing, and trade.
- Do not call outbound departures the percentage of unique international
  travelers.
- Do not invent a worldwide books-read median from commercial polls or
  self-selected reading applications.
- Do not collapse gender equality, sexual rights, drug policy, or social
  mobility into one moral ranking.
- Do not fetch external data during normal generation.

The next confirmation point is the end of step 3: keep the 14 current
Cahill–Keyes fixtures passing, add any new spatial product only with a pinned
source and domain gate, and review the generated contact sheet before
facility, biodiversity, and policy adapters multiply further.

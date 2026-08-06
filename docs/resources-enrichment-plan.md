# Resources Stage 6b enrichment plan

[Documentation index](../index.md) ·
[Generation methods](generation-methods.md) ·
[Generation guide](generation.md)

## Status and recommendation

This document is a **proposed Stage 6b design**, not a description of the
currently implemented generator or Make targets. The checked
`generate-resources` pass remains the bounded Stage 6a World Game artifact
recorded in [generation methods](generation-methods.md). Its 1960 production
leaders must not be relabelled as current resource data, and the Stage 6b
cutover must remove that generated product rather than preserve a legacy
variant.

Stage 6b should replace that default with five independently sourced product
families:

- `resources-energy`;
- `resources-food`;
- `resources-flora`;
- `resources-mineral`; and
- `resources-human`.

`resources-flora` is the canonical spelling. The requested
`ressources-flora` spelling can be retained only as an input alias during the
migration.

The first implementation increment should establish the normalized schema and
one non-sparse primary layer for every family:

1. renewable and nuclear capacity or generation by country for energy;
2. crop, livestock, fisheries, and food-supply measures by country, with
   SPAM and GLW as optional spatial detail;
3. global land cover plus forest statistics for flora;
4. current USGS/BGS mine production by country for a critical-mineral
   shortlist; and
5. UN population age structure plus education, literacy, patents, and a
   separately named equality measure for human resources.

Facility, deposit, biodiversity-occurrence, travel, and legal-policy layers
can enrich those global baselines. They must not be used to make a sparse point
inventory look globally complete.

## Why the checked pass is not a Stage 6b foundation

The current profile is internally consistent with its stated historical
scope, but it does not satisfy the new scope:

| Checked input | Current content | Stage 6b consequence |
| --- | --- | --- |
| Historical table | 40 commodity headings and marked 1960 country leaders | Retire the generated artifact; retain only a historical method note and exclude all values from Stage 6b |
| Modern context | Four global or country facts from FAO and IRENA | Too small to define the new taxonomy or a global atlas |
| Geographic marks | 39 representative historical-country points and two modern country points | Leader points are not production fields, facilities, country rates, or coverage |
| Categories | Metals, industrial materials, and energy feedstocks | Replace with energy, food, flora, mineral, and human product families |
| Missing-data model | Appropriate null semantics for the historical table | Extend to explicit coverage, observation status, uncertainty, and source-period fields |

Only two of the four modern context records currently create a geographic
mark. Adding more leader dots would preserve the same sparsity and would
continue to confuse a representative country point with the geography of a
resource. Stage 6b needs country polygons, global grids, and facility or field
geometries selected per metric.

## Product and artifact contract

Each category is a **target family**. It can produce several metric-specific
maps; it is not one image with unrelated quantities painted on top of one
another. A static PNG or PDF should display one metric and unit. A layered SVG
may retain compatible supporting layers such as a country field and audited
facility points, but it must not create a cross-metric resource score.

Proposed artifact names carry family, metric, reference period, and
projection:

```text
resources-energy-solar-capacity-2025-ck-44-22.svg.gz
resources-food-crop-production-2024-star-x-34-44.svg.gz
resources-flora-tree-cover-2020-voronoi-44-22.916667.svg.gz
resources-mineral-lithium-mine-production-2025-ck-44-22.svg.gz
resources-human-adult-literacy-latest-2026-ck-44-22.svg.gz
```

The `latest-2026` form means “latest accepted observation not later than the
2026 snapshot cutoff”; it does not imply that every country was measured in
2026. The legend and SVG metadata must expose the observation year for every
country. Prefer a common complete year when the source supports it.

Proposed target semantics are:

```sh
make generate-resources-energy
make generate-resources-food
make generate-resources-flora
make generate-resources-mineral
make generate-resources-human
make generate-resources-stage6b
```

Those targets do not exist yet. Make the cutover atomic: after all five first
snapshots pass release gates, change the generic `generate-resources` and
generation-profile selector to expand to the Stage 6b families, remove the
World Game rules and generated artifacts, and replace the v1 implementation
and tests. Do not add a `generate-resources-world-game` compatibility target.

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

A default Stage 6b metric is non-sparse only when it meets one of these gates:

- a global field has valid values for at least 99% of its declared land,
  ocean, or biome-domain cells, excluding a source-declared mask;
- a human country statistic covers at least 80% of mapped countries **and**
  at least 90% of the mapped world population;
- a production statistic covers at least 80% of mapped producer countries and
  at least 90% of the source-reported world output for that commodity; or
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

The 1960 matrix must not supply Stage 6b mineral values. The primary current
sources should be:

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

Stage 6b should use a long-form metric catalogue plus three geographic stores,
rather than extending the v1 historical JSON structure:

```text
assets.static/resources/v2/resources-profile.json
assets.static/resources/v2/resources-catalog.json
assets.static/resources/v2/resources-country.json
assets.static/resources/v2/resources-grid-res3.geojson.gz
assets.static/resources/v2/resources-facilities.geojson.gz
assets.static/resources/v2/SHA256SUMS
```

The exact storage encoding can change after fixtures establish realistic file
sizes. The semantic contract should not. Every value needs:

```json
{
  "metric_id": "human:population-under-30-percent",
  "family": "resources-human",
  "evidence_class": "modeled-estimate",
  "geography_kind": "country",
  "geography_id": "UNM49:840",
  "value": 38.2,
  "unit": "percent",
  "reference_period": "2025",
  "source_release": "WPP2024",
  "source_id": "un-wpp",
  "value_state": "present",
  "quality_flags": []
}
```

Required catalogue metadata includes title, exact definition, numerator,
denominator, unit, allowed evidence classes, domain, preferred color scale,
snapshot cutoff, source release and URL, retrieval time, raw digest, license,
redistribution decision, derivation formula, and known limitations.

Required geography rules are:

- use UN M49 as the stable country key and retain source-native codes for
  audit;
- pin the boundary dataset and record aggregation for territories and disputed
  areas;
- never join by display name;
- keep source estimates, modeled estimates, reported values, zeros, missing,
  withheld, and not-applicable states distinct;
- store numerator and denominator whenever a percentage or per-capita value is
  derived;
- include uncertainty bounds or source quality flags when available; and
- emit a machine-readable coverage report for every metric and source.

H3 resolution 3 is a sensible default display grid for global raster fields,
but preparation should area-weight source pixels and retain valid-area
fractions. High-resolution source rasters remain source inputs; checking one
SVG polygon per 10 m pixel into the repository is neither necessary nor
tractable.

## Acquisition and reproducibility

Normal generation remains offline. Acquisition is an explicit maintainer
operation:

```sh
make fetch-resources-data       # explicit network/form/API step
make prepare-resources-data     # raw to normalized candidates
make check-resources-data       # schema, hashes, coverage, rights manifest
make promote-resources-data     # reviewed snapshot only
```

These are proposed targets. Fetchers must write to ignored staging paths,
never overwrite a promoted snapshot in place, and never run as a dependency of
`make`, `make all`, or a generation-profile target. A maintainer reviews
license and source changes, compares coverage and totals with the previous
snapshot, then promotes an immutable version with checksums.

APIs, forms, credentials, and manual downloads need source-specific adapters.
The repository should not bypass a download form, invent an API, or treat
interactive access as permission to redistribute a full raw dataset.

## Implementation sequence

### 1. Record and retire Stage 6a

- Retain a concise historical method and feasibility record in
  `generation-methods.md`.
- Remove the World Game generated SVG, PDF, and PNG artifacts at the Stage 6b
  cutover; do not retain an opt-in generation target.
- Replace the v1 profile, parser, renderer, and focused tests with the v2
  implementation instead of maintaining parallel legacy code.
- Do not copy any 1960 value into v2 and do not use “modern context” as a seed
  schema.

### 2. Build v2 schema and coverage QA

- Implement the metric catalogue, UN M49 concordance, long-form values,
  explicit value states, source manifest, and derived-value formulas.
- Add fixture tests for zero versus missing, units, source periods, country
  joins, duplicate records, withheld values, and coverage denominators.
- Make every candidate emit country count, covered population or production,
  regional gaps, reference-year distribution, and source/evidence-class
  totals.

### 3. Seed five non-sparse products

- Energy: IRENA solar/wind, PRIS nuclear, and EIA country petroleum/gas.
- Food: FAOSTAT crops, fisheries, aquaculture, food balances, and livestock.
- Flora: Copernicus or MODIS land cover plus FRA forest statistics.
- Mineral: USGS 2025 values with BGS 2020–2024 cross-checks for the critical
  shortlist.
- Human: WPP age shares, UIS literacy/attainment, WIPO resident applications,
  and WBL/GII as separate equality layers.

Generate one metric-specific Cahill-Keyes fixture per family before expanding
to six projections or checking in full artifact families.

### 4. Add spatial enrichment

- Add SPAM crops, GLW livestock, land-cover H3 fields, PRIS reactors, GEM
  energy facilities/fields, and audited mineral points.
- Require every point source to document inclusion thresholds, coordinate
  quality, lifecycle/status values, last review, and known geographic gaps.
- Add GBIF plant richness only with sampling effort and sensitivity tests.

### 5. Add policy and quality-of-life dimensions

- Add travel departures only under the corrected label.
- Implement legal dimensions rather than a sexual-freedom or drug-freedom
  score.
- Add GDIM mobility with cohort/reference-period metadata.
- Omit books-read median until a source passes definition, country, population,
  recency, and redistribution gates.

### 6. Switch the default

- Add five pass selectors plus the `ressources-flora` input alias.
- Make `resources` expand to all five only when every family has at least one
  released non-sparse metric.
- Remove the World Game product from generic `resources`, `all`, default
  profiles, exact targets, and checked generated artifacts.
- Generate all six projections, deterministic `.svg.gz` files, PDFs, and PNGs;
  compare coverage reports and visual fixtures before promotion.

## Release checks

Every Stage 6b snapshot and metric should require:

- a pinned release, raw digest, retrieval date, source URL, rights decision,
  and source citation;
- exact metric definitions and units, including commodity-specific conversion
  rules;
- the relevant non-sparse coverage gate or an explicit `supplemental` status;
- no 1960 values in Stage 6b and no missing-to-zero conversion;
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

- Do not rename the 1960 World Game categories and call the result current.
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

The recommended confirmation point is the end of step 3: five
Cahill-Keyes metric fixtures, each backed by a pinned current source and a
passing non-sparse coverage report. That increment replaces the misleading
leader-point model and proves the shared v2 contract before facility,
biodiversity, and policy enrichment multiplies the number of adapters.

# Resources metric catalog

[Documentation index](../../../../index.md) ·
[Resources implementation](implementation.md) ·
[Enrichment plan](enrichment-plan.md) ·
[Stage 12 overview](../../../development/stage-12.md) ·
[Generated previews](../../../../index.md#generated-artifact-previews)

This is the human-readable index to the checked
[`cartofreako-resources-profile-v3`](../../../../assets.static/resources/resources-profile.json)
metric catalog. The JSON profile remains authoritative for exact units,
reference periods, source IDs, coverage, output tags, palettes, and lifecycle
status. The checked snapshot contains 59 metric definitions across six
families; 14 are standard release passes and 45 remain exploration-only.

## Pass classes

The public pass class describes build and release behavior. It is deliberately
separate from whether an upstream source happens to require credentials.

| Pass class | Definition | Build and release behavior | Current examples |
| --- | --- | --- | --- |
| **Standard pass** | Implemented, source-pinned, coverage-checked, and released | Included in the offline `make all` graph and generated for all six projections; appears in the public snapshot catalog | All 14 resource products listed below |
| **Optional pass** | Implemented, but initially excluded from the standard graph because it requires credentials, license acceptance, or an explicit operator decision | Run through `generate-authorized-external`; a fully successful run persists only the pass name and enables its prepared artifact graph in later `make all` runs for that checkout. Absence never breaks a clean checkout | P-Tree Cloud-atmosphere and licensed network topology; no resource metric currently has this class |
| **Exploration only** | Cataloged, researched, or source-tested, but not released | Has no production output tag or complete artifact rule and is absent from `make all`, release manifests, and public preview sheets | Every resource metric marked `planned`, `supplemental`, or `research-gap` below |

Authorization and pass maturity are independent. NASA FIRMS, for example,
has an optional credentialed acquisition boundary, but its data remains an
unrendered exploration candidate until a separate review promotes a defined
metric. Supplying a key does not turn an exploration entry into an optional or
standard pass.

## Catalog lifecycle mapping

The resource profile uses lifecycle values that map to the public pass classes
as follows:

| Profile status | Count | Public pass class | Meaning |
| --- | ---: | --- | --- |
| `default` | 6 | Standard | Released and selected as the default metric for its family |
| `released` | 8 | Standard | Released alongside the family default |
| `planned` | 41 | Exploration only | Definition retained, but promotion work is incomplete |
| `supplemental` | 3 | Exploration only | Potential supporting product; not an optional production pass |
| `research-gap` | 1 | Exploration only | No source currently satisfies the definition and release gates |

An **optional pass is not a resource-profile lifecycle status**. If a resource
metric later becomes an implemented opt-in product, its pass class and
authorization contract must be documented explicitly instead of overloading
`supplemental`.

## Standard resource passes

These 14 metrics have a nonempty output tag, normalized data or checked
spatial input, a passing release gate, Make rules, six-projection outputs, and
public v12 previews.

| Family | Metric ID | Reference period | Output tag |
| --- | --- | --- | --- |
| Energy | `solar-capacity` | 2025 | `solar-capacity-2025` |
| Energy | `wind-capacity` | 2025 | `wind-capacity-2025` |
| Energy | `nuclear-operating-capacity` | 31 December 2024 | `nuclear-operating-capacity-2024` |
| Energy | `petroleum-refinery-throughput` | Latest reported from 2018–2024 | `petrochemical-refinery-throughput-latest-2024` |
| Food | `food-production-index` | 2022 | `food-production-index-2022` |
| Fauna | `fisheries-production` | Latest accepted through 2024 | `fisheries-production-latest-2024` |
| Fauna | `coral-reef-threat` | *Reefs at Risk Revisited*, 2011 | `coral-reef-threat-2011` |
| Flora | `forest-area-percent` | 2023 | `forest-area-percent-2023` |
| Mineral | `rare-earth-mine-production` | 2025 estimate | `rare-earth-mine-production-2025` |
| Human | `population-under-30` | 2024 | `population-under-30-2024` |
| Human | `population-over-60` | 2024 | `population-over-60-2024` |
| Human | `upper-secondary-attainment` | Latest observation from 2018–2025 | `upper-secondary-attainment-latest-2025` |
| Human | `bachelors-attainment` | Latest observation from 2018–2024 | `bachelors-attainment-latest-2024` |
| Human | `resident-patent-applications-per-million` | 2019–2021 mean | `resident-patent-applications-per-million-2019-2021` |

## Exploration-only catalog

The entries below are visible so that a planned definition cannot be mistaken
for a hidden release. None currently has a production output tag or public
artifact.

### Energy, food, fauna, and flora

| Family | Metric ID | Status | Current boundary |
| --- | --- | --- | --- |
| Energy | `oil-field-production` | Planned | Keep extraction separate from refining and capacity |
| Energy | `petroleum-refinery-capacity` | Planned | Do not substitute the released throughput metric |
| Energy | `gas-processing-and-lng` | Planned | Needs a pinned global capacity source and facility rules |
| Energy | `unconventional-gas-production` | Supplemental | Explicit reporting only; no inferred worldwide field |
| Food | `crop-production` | Planned | Preserve crop, unit, and production basis |
| Food | `livestock-production` | Planned | Keep livestock heads and production quantities separate |
| Food | `dietary-energy-supply` | Planned | Food availability is not production or consumption |
| Fauna | `capture-fisheries` | Planned | Separate capture from aquaculture |
| Fauna | `aquaculture` | Planned | Separate aquaculture from capture production |
| Flora | `land-cover` | Planned | Needs a pinned categorical land-cover snapshot |
| Flora | `forest-cover-density` | Planned | Density is not biodiversity |
| Flora | `savanna-mask` | Planned | Source-specific categorical field |
| Flora | `tropical-rainforest-mask` | Planned | Source-specific categorical field |
| Flora | `plant-biodiversity` | Supplemental | Requires sampling-effort correction and sensitivity tests |

### Minerals

The following 23 USGS-oriented commodity definitions are all `planned` and
exploration-only. A commodity name does not yet imply a released metric:
mine production, refined production, processing capacity, reserves,
resources, and trade must remain separate.

| Metric ID | Title | Metric ID | Title |
| --- | --- | --- | --- |
| `uranium` | Uranium | `lithium` | Lithium |
| `cobalt` | Cobalt | `nickel` | Nickel |
| `natural-graphite` | Natural graphite | `manganese` | Manganese |
| `copper` | Copper | `bauxite-aluminum` | Bauxite and aluminum |
| `gallium` | Gallium | `germanium` | Germanium |
| `indium` | Indium | `tellurium` | Tellurium |
| `silicon-metal` | Silicon metal | `antimony` | Antimony |
| `tungsten` | Tungsten | `tin` | Tin |
| `tantalum` | Tantalum | `niobium` | Niobium |
| `titanium` | Titanium | `vanadium` | Vanadium |
| `platinum-group-metals` | Platinum-group metals | `phosphate-rock` | Phosphate rock |
| `potash` | Potash |  |  |

### Human and policy metrics

| Metric ID | Status | Current boundary or blocker |
| --- | --- | --- |
| `adult-literacy` | Planned | Tested data cover 89.432% of mapped population and miss the 90% gate |
| `advanced-degree-attainment` | Planned | Tested data cover 126 mapped countries and miss the 80% country gate |
| `international-departures-per-capita` | Supplemental | A flow of departures, not a percentage of unique travelers |
| `books-read-median` | Research gap | No harmonized, current, non-sparse worldwide source identified |
| `gender-equality-law` | Planned | Legal framework, supportive systems, enforcement, and outcomes must remain separate |
| `consensual-same-sex-activity-law` | Planned | No source is pinned and there are no normalized records; use separate dated legal dimensions rather than an LGBTQIA or “sexual freedom” score |
| `drug-possession-penalty` | Planned | No source is pinned and there are no normalized records; distinguish substance, quantity, conduct, sanction, enforcement, and review date |
| `intergenerational-mobility` | Planned | Cohort estimates require explicit period metadata and are not current behavior |

The LGBTQIA-related design is intentionally narrower than an umbrella score.
A reviewed implementation should preserve consensual same-sex
criminalization, relationship recognition, expression restrictions, legal
gender recognition, exceptions, and enforcement caveats as separate dated
observations. The drug-policy design similarly requires jurisdiction- and
substance-specific dimensions for possession, use, cultivation, quantity,
sanction, and review date. Neither candidate currently has values, coverage,
Make targets, artifacts, or v12 previews.

## Promotion boundary

An exploration-only metric becomes a standard pass only after all of these
are present and reviewed:

1. a pinned source release, retrieval date, digest, citation, and rights
   decision;
2. an exact metric definition, unit, reference period, geography, and missing
   value semantics;
3. normalized country records or a checked spatial input with a passing
   coverage gate;
4. a nonempty output tag and metric-specific Make rules;
5. successful generation and structural checks for all six projections;
6. deterministic SVG gzip, PDF, and PNG exports; and
7. release-manifest and public contact-sheet inclusion.

An optional pass must meet the same implementation and quality boundary. Its
only difference is a deliberate, documented opt-in constraint such as source
credentials or license acceptance.

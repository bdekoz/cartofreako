# World Game resources implementation notes

[Documentation index](../index.md) ·
[Generation pipeline](generation.md) ·
[Generation methods](generation-methods.md) ·
[Static profile](../assets.static/resources/resources-profile.json) ·
[Profile README](../assets.static/resources/README.md)

## Outcome

Stage 6 is implemented as `generate-resources`. The pass is feasible as a
historical production-leader atlas, but the accessible archival material does
not support a defensible claim that every resource concept ever used in
Fuller's World Game has been digitized. The implemented scope is therefore
explicit and testable:

- every one of the 40 commodity columns in the report's 1960 production
  matrix;
- its reported world total and original unit;
- its asterisk-marked leading producer and percentage of world production;
- the source pages for the heading and leader cell; and
- four separately sourced modern context indicators for fisheries,
  agriculture, and installed solar capacity.

The pass does not reproduce the scan or the complete 5,040-cell country
matrix. It makes no mine, well, field, facility, reserve, trade-flow, or
present-day boundary claim.

## Historical source audit

The primary source used was the Buckminster Fuller Institute's
[catalog page and scan for *Inventory of World Resources, Human Trends, and
Needs*, Phase I, Document 1](https://www.bfi.org/resource/phase-i-document-1-inventory-of-world-resources-human-trends-and-needs-1963/),
by R. Buckminster Fuller and John McHale, published by the World Resources
Inventory at Southern Illinois University in 1963.

The scan itself explains that 1960 was chosen as a representative year. Its
major-minerals-and-metals table occupies one-based PDF pages 62–73. The source
alternates commodity-column blocks and country-row blocks across those pages.
Blank cells can mean unavailable or secret data or a production deficiency,
and the report warns that statistics may be incomplete or unreliable.
Consequently, blanks are not zeros and the pass does not sum the incomplete
country matrix.

The audited PDF digest is:

```text
11f0a4f7617a34b58bf620bba62ddbfe01a6389dffc348e95142b86db964f816
```

The archival links in the original request serve different roles:

| Archive | Finding | Role in this pass |
| --- | --- | --- |
| [Buckminster Fuller Institute](https://www.bfi.org/resource/phase-i-document-1-inventory-of-world-resources-human-trends-and-needs-1963/) | A directly inspectable scan of the cited 1963 document | Numeric source and page-level audit authority |
| [Virginia Tech, Box 1 Folder 7](https://aspace.lib.vt.edu/repositories/2/archival_objects/197582) | An archival-object description open for research | Corroborating collection pointer, not a machine-readable dataset |
| [Stanford Fuller papers](https://archives.stanford.edu/catalog/m1378) | A large special-collections record | Research lead, not the source of the checked values |
| [Online Archive of California finding aid](https://oac.cdlib.org/findaid/ark:/13030/tf109n9832/) | Collection description and access conditions | Research lead; no normalized World Game resource table was identified |

These collection records are valuable for deeper scholarship, but their
existence is not evidence that a complete World Game data product is available
for automated ingestion.

## Rights and acquisition decision

The BFI [legal terms](https://www.bfi.org/about-bfi/legal/) reserve rights in
website content and do not grant a general redistribution or automated
download license. BFI's
[licensing page](https://www.bfi.org/about-bfi/contact/licensing/) directs
permission requests for reproducing Fuller publications to the Fuller Estate.
The archive finding aids likewise describe research access, not a broad data
redistribution license.

For that reason:

- the source scan and page images are not checked in;
- the Makefile has no source-download target;
- ordinary generation reads only the small factual profile;
- the profile cites the source URL, pages, title, authors, publisher, and PDF
  digest; and
- the OCR helper operates only on an authorized local copy supplied by a
  maintainer.

This is a conservative engineering boundary, not legal advice or a declaration
about the copyright status of individual facts.

## Historical data contract

[`resources-profile.json`](../assets.static/resources/resources-profile.json)
uses schema `cartofreako-resources-profile-v1`. The loader rejects duplicate or
unknown JSON members, malformed identifiers, non-finite or out-of-range values,
duplicate record identifiers, wrong source years, invalid source-page ranges,
count drift, and inconsistent nulls.

The historical section must contain exactly 40 records in source-column order.
Each reported record has:

| Field | Meaning |
| --- | --- |
| `index`, `id`, `label` | Stable source order, machine identifier, and visible commodity heading |
| `category` | `metals`, `industrial-materials`, or `energy-feedstocks`; this is a display classification, not a claim made by the report |
| `world_total`, `source_unit` | Printed total and unconverted source abbreviation |
| `header_pdf_page`, `leader_pdf_page` | One-based PDF audit pointers |
| `leader.historical_label` | Country label exactly in the historical table |
| `leader.modern_area` | Present-day descriptive lookup label, never a boundary conversion |
| `leader.longitude`, `leader.latitude` | Documented representative point for display |
| `leader.share_percent` | Three-decimal percentage marked with the source asterisk |

The one unavailable record must be Thorium, with null total, null leader page,
null leader, and source unit `N.A.`. Every other record must have a positive
world total, a leader page, and a leader share in `(0, 100]`.

Historical labels such as `USSR`, `Germany (East)`, and `Congo
(Leopoldville)` are intentionally preserved. The corresponding `modern_area`
and coordinates are presentation aids only. A marker means “this historical
country label was the table's marked leading producer,” not “production
occurred at this point.”

## Modern context is a separate evidence class

The four modern records are pinned comparisons, not a time series and not
updates to Fuller's unlike commodity definitions:

| Indicator | Reference year | Pinned fact | Primary source |
| --- | ---: | --- | --- |
| Capture fisheries | 2022 | 92.3 million tonnes globally; no matching country share asserted | [FAO, SOFIA 2024 release](https://www.fao.org/newsroom/detail/fao-report-global-fisheries-and-aquaculture-production-reaches-a-new-record-high/) |
| Aquatic animal production | 2022 | 185.4 million tonnes; China 36% | [FAO, SOFIA 2024 release](https://www.fao.org/newsroom/detail/fao-report-global-fisheries-and-aquaculture-production-reaches-a-new-record-high/) |
| Primary crops | 2023 | 9.9 billion tonnes globally; no country share asserted | [FAO, Agricultural production statistics 2010–2023](https://www.fao.org/statistics/highlights-archive/highlights-detail/agricultural-production-statistics-2010-2023/en) |
| Installed solar capacity | 2025 | 2,391,584 MW globally; China 1,202,179 MW, or 50.267% | [IRENA, *Renewable Capacity Statistics 2026*](https://www.irena.org/Publications/2026/Mar/Renewable-capacity-statistics-2026) |

Every modern record carries its own reference year, organization, title, URL,
unit, and scope note. Global-only records remain visible in the bottom legend
but create no geographic marker. This prevents an unsupported country leader
from being inferred merely to make the map look complete.

## Rendering contract

The generator uses the shared production implementations for Cahill-Keyes,
AuthaGraph, Dymaxion, Myriahedral, Star-X, and Voronoi. Natural Earth provides
a subdued land reference. The resulting SVG contains these testable layers:

1. `resources-background` and `terrestrial-land`;
2. `resource-tethers` from representative country points to collision-free
   display positions;
3. `historical-metals`, `historical-industrial-materials`, and
   `historical-energy-feedstocks`, with different marker shapes and colors;
4. `modern-resource-context`, using a distinct ring symbol;
5. `resource-legend`, containing all 40 historical rows; and
6. `modern-context-legend`, visibly stating that the indicators are separate.

Records that share a representative point use a deterministic concentric
layout. Tethers preserve the geographic anchor. Marker radius varies modestly
with leader share; area is not a quantitative encoding, and precise values are
printed in the legend and retained as SVG data attributes.

The SVG metadata embeds the profile name, projection, source years and pages,
source URL and digest, all 40 historical facts, all modern context facts,
missing-value semantics, and the historical/modern separation. Generation
then reopens the SVG and verifies its viewBox, required layers, 39 historical
markers, two modern markers, complete catalogs, finite coordinates,
provenance, and configured font.

## Easy generation workflow

Install the normal project prerequisites and fetch Natural Earth once, then:

```sh
# One fast SVG
make generate-resources-cahill-keyes

# All six projection SVGs
make generate-resources

# All six SVGs plus PDF and 3840-pixel PNG exports
make generate-resources-artifacts
```

One other projection can be requested directly, for example:

```sh
make generate-resources-star-x
```

Or select the pass in a generation profile:

```json
{
  "schema_version": 1,
  "projections": ["cahill-keyes", "star-x"],
  "passes": ["resources"]
}
```

`resource`, `world-game`, `world-game-resources`, and the legacy typo
`resouces` normalize to the canonical `resources` pass.

## Re-auditing an authorized scan

This workflow is intentionally outside normal builds.

1. Review the current source and archive terms. Obtain an authorized local
   copy without placing it in the repository.
2. Verify whether it is byte-identical to the audited scan:

   ```sh
   sha256sum authorized-inventory.pdf
   ```

3. Render pages 62–73 at exactly 150 DPI:

   ```sh
   mkdir -p /tmp/cartofreako-fuller-pages
   pdftoppm -f 62 -l 73 -r 150 -png authorized-inventory.pdf \
     /tmp/cartofreako-fuller-pages/cartofreako-minerals
   ```

4. Install Tesseract and the Python OpenCV module, then produce an audit
   candidate:

   ```sh
   python3 -B scripts/transcribe-fuller-minerals.py \
     /tmp/cartofreako-fuller-pages /tmp/full-resource-matrix-audit.json
   ```

5. Inspect the candidate rather than copying it into the profile:

   ```sh
   jq '.audit.unparsed_nonblank_cells | length' \
     /tmp/full-resource-matrix-audit.json
   jq '.audit.column_sums[]' /tmp/full-resource-matrix-audit.json
   ```

6. Compare every proposed heading, world total, leader asterisk, share, unit,
   and page pointer against the page image. Update the digest and notes if the
   authorized edition differs. Run the focused and generation checks.

The OCR helper understands the scan's non-linear final country-page order and
reports ambiguous cells. It is deliberately conservative and currently serves
as an audit workbench; OCR does not establish source truth.

## Verification

The focused native test checks the complete profile, the 1960/1963 year
distinction, source digest, null semantics, record counts, modern facts,
strict-schema failures, and finite collision layouts on all six projections:

```sh
make check
cd assets.static/resources && sha256sum -c SHA256SUMS && cd ../..
make -B generate-resources-cahill-keyes
```

For a visual review, inspect the generated SVG or PNG at full size. In
particular, confirm the dense United States cluster has readable tethers, the
modern China rings are distinct from historical symbols, Thorium appears only
as `N.A.` in the historical legend/catalog, and the bottom band never implies
that modern records continue the 1960 series.

## Limitations

- The source matrix is a historical document with acknowledged incomplete and
  uncertain statistics. This pass preserves its claims; it does not endorse or
  correct them.
- World totals retain heterogeneous source units. No cross-commodity magnitude
  comparison is valid without a separate conversion and definition study.
- Representative points collapse large and historical territories and should
  not be used for spatial analysis.
- “Leading producer” is the report's asterisk mark, not a recomputation from
  blank-prone country cells.
- The four modern indicators have different years and scopes. They are context,
  not a trend line or comprehensive contemporary resource inventory.
- The bounded v1 profile does not claim to exhaust World Game files held in
  archival collections. Future additions need item-level provenance, rights
  review, definitions, and a versioned schema rather than an inferred merge.

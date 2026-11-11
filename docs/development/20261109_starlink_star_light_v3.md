This is a continuation of the updated starlink explorations in:
20261103_starlink_update_explore.md
20261106_setouchi_triennale_futures.md

Please use the latest version of these four plates:
SLSL1: astro all sky
astro-all-sky-authagraph-44-19.052559.svg

SLSL2: orbital technosphere observer
orbital-technosphere-observer.svg

SLSL3: orbital technosphere global
orbital-technosphere-global.svg

SLSL4: starlink terrestrial groundstations and fibre
network-groundstations-authagraph*.svg

The coloring should be as last accepted, the wine-amber plates.
For the four plates, do a world view and a detail of the USA inclusive of Hawaii and Alaska.

Make the following changes:

1) SLSL4 groundstation refinements

in SLSL4, remove the layers
 - antarctica consolidated insed
 - the filled continental land

Then, aperature proxy size betwen low and high needs to have 2x more variance.

Also, change the different antenna types icon from variants of a triangle, to 9 different markers points.

2) SLSL1 refinements
sometimes, the orbital objects are clipped at the edges of the frame. In addition, some of the text on the edge objects clips and some of it is off the page. Is there a way to adjust the layout such that these things don't happen? Also, redice the size of the type used to name elements by 20%, and put the starting and ending type sizes in the generated plan documentation for further refinement.

3) Change the legend plates to be be plate size landscape A3, scale type to closely fit existing legend plates. In addition, switch the randomally pairs wine-amber to be reversed on the legend plates, so the background is light and the text is dark.

4) Add an "observer notes" section of the legend plates, where the view of the objects on the plate is described concisely in a text paragraph. Where is the viewer located in space? What does the viewer see? How is it related to the perspective in other four plates?


5) Examine 1-3 options of taking these plates and making a smaller POD book. Use Ingram Spark as the publishing vendor
https://www.ingramspark.com/book-printing

Investigate various sizes, prefer something small like A5, but consider A3

---

## Implementation record — 9 November 2026

The brief above is retained as supplied. The focused implementation is
[`scripts/build-starlink-star-light.py`](../../scripts/build-starlink-star-light.py),
with the saved [edition configuration](../../config/starlink-star-light-v3-20261109.json).
It produces four World and four USA map sheets, each with a separate A3
landscape legend, in
[`output/starlink-star-light-v3-20261109/`](../../output/starlink-star-light-v3-20261109/index.html).
The generated [production record](../../output/starlink-star-light-v3-20261109/plan.md)
contains the source dates, stages, exact type sizes, radius formula and build
instructions. The [IngramSpark study](20261109_starlink_star_light_v3_pod.md)
compares three formats with actual-size proof pages.

### Sources and interpretation

SLSL2 and SLSL3 use the checked-in **9 November 2026** orbital snapshot and
are calculated at **01:12 UTC**: 17,956 global objects and 972 above the
San Francisco horizon. There are 46 epoch exclusions and no propagation
failures. The accepted vendor colors, 1.5× Starlink sunbursts, 6 pt World
Starlink text and doubled global track strokes are retained.

The 10 November follow-up changes SLSL3 **Orbital Debris** to a **white x**
(`#ffffff`) in both World and USA views and their companion legends. The
existing amber halo is retained.

The observer follow-up retains the **9 November 2026, 01:12 UTC** calculation
and its 972 above-horizon objects, while restoring SLSL2's accepted **cyclic
framing**: the 43.5-inch World image shifts 4.35 printed inches to the right,
with artwork wrapping across the side edges. The USA context uses the same
complete cyclic sky within its viewport. Both legends explain that this
changes the display seam, and identify the brighter amber **horizon curve**
as San Francisco's zero-degree elevation boundary. The fainter curve is the
celestial equator. The linked reference shows a different calculation time,
so the retained November sky has different satellite positions and horizon
geometry.

The November astronomy exports and staged data directory described in
`docs/pages/passes/astronomy.md` are absent from this checkout. SLSL1 therefore
uses the latest preserved accepted all-sky artwork, calculated at
**29 October 2026, 20:00 UTC**, with 685 objects and 35 labels. This limitation
is stated on both legends and in the generated source manifest. The builder
accepts `--astronomy-source PATH` for a newer matching AuthaGraph all-sky SVG
and reads its actual timestamp; it does not relabel the preserved sky.

SLSL4 retains the supplied **3 November 2026** KML/GeoJSON collection:
590 antenna records, 66 PoPs and 124 lines. The aperture interpretation and
all incomplete/unknown inventories remain source-preserving. Source dates
are distinct from acquisition dates and per-site verification.

USA detail means three independently scaled geographic panels: mainland,
Alaska including the Aleutians, and Hawaii including the northwest islands.
Sky coordinates cannot be cropped by US longitude/latitude. Accordingly,
SLSL1 and SLSL2 retain their complete celestial view beside the three USA
locators. These locators do not relocate the San Francisco observer. The
SLSL3 and SLSL4 panels enlarge actual terrestrial coordinates.

### Implemented refinements

SLSL4 removes the filled continental land and consolidated Antarctic inset.
Nine equal-area silhouettes replace the triangle variants: circle, square,
diamond, pentagon, hexagon, star, cross, saltire and octagon. They retain
independent status strokes and the central unknown-size square.

“2× more variance” is implemented as twice the low-to-high **radius span**:
`r_new = 0.04 + 2 × (r_previous - 0.04)` in source inches. The known range
changes from **0.040000–0.179088 in** to **0.040000–0.318176 in**. Unknown
sizes remain 0.055 in; PoPs remain 0.032 in. This is an enhanced display scale,
so final symbol area is not directly proportional to the listed aperture.
The largest complete antenna-bank calculation is unchanged. Placement is
recomputed for the enlarged marks, with tethers to original locations.
The USA crop expands to retain the complete displaced symbols of every
record selected by its original geographic position. This prevents the
larger collision offsets from excluding mainland sites at the crop edges.

SLSL1 names change from **12 pt to 9.6 pt**, a 20% reduction in both scopes.
The builder compensates for each viewport's scale. The centered complete
sky frame replaces cyclic clipping and includes a source gutter for rays
and glyphs; text moves inward where its measured width crosses the edge.
Object coordinates, colors and names remain intact.

The follow-up halves SLSL1's World left/right frame margins from **1.846680
to 0.923340 inches** each, using uniform enlargement. The USA sky viewport
also halves its internal side gutters. Export validation checks actual
rendered objects, rays and labels against all page edges; names remain 9.6 pt.

The SLSL4 treatment is now the saved **default atlas groundstation
presentation**. `generation-style.json` selects this edition's groundstation
recipe. Both the current dataset builder and retained-edition builder call
the shared renderer through `scripts/atlas_groundstations.py`, with matching
legends and source-specific counts. Current builds use their bound source
profile; neither builder requires the generated SLSL delivery. Historical
MSP studies and the raw native source pass remain reproducible.

Legends are **420 × 297 mm**, with amber `#fcc553` behind wine `#240413`
text. The content is reflowed into three columns. Titles use 27 pt; headings
15 pt; observer notes 12 pt; body 11 pt; sources 10.5 pt. Each legend explains
where the conceptual viewer is, what is plotted and how its perspective
relates to the other plates. Categorical symbols use dark swatches so their
source colors remain visible on the light sheet.

### Reproduction and checks

```sh
make DATASET=legacy starlink-star-light-v3
make DATASET=legacy check-starlink-star-light-v3
```

The target is independent of the incomplete full data-update edition. It
uses the repository compiler prerequisites plus lxml, Pillow, Shapely,
ReportLab, Inkscape, fontconfig and Poppler. `SLSL_PYTHON`, `SLSL_LAND_DIR`,
`SLSL_NATIVE_DIR` and `SLSL_OUTPUT` permit explicit local overrides. The
initial run installed ReportLab in `build/slsl-venv/`, leaving system Python
unchanged. That environment is selected automatically when present.

The focused native build used Natural Earth 5.1.1's
[land-only archive](https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip),
downloaded into `build/starlink-star-light-v3/native-data/`. Its SHA-256 is
`e547d749445eaa0964aba76738090ec88f5e63c4585122170f98c67a7ea922dc`.
An existing full Natural Earth directory also works; the repository's
`make fetch-natural-earth-10m` target supplies it. Neither orbital inputs
nor the preserved astronomy archive is refreshed implicitly.

Checks cover source/output hashes, all 16 map/legend pairs, unique SVG IDs,
object and label conservation, physical typography, source population
counts, all nine symbols, doubled radius span, collision clearance, USA
coverage, removed layers, reversed legend colors, observer notes, rendered
astronomy bounds and PDF page dimensions. The [validation receipt](../../output/starlink-star-light-v3-20261109/validation.json)
and [delivery manifest](../../output/starlink-star-light-v3-20261109/manifest.json)
are generated with the artifacts. Seven focused display regressions and nine
existing capability-interpretation regressions accompany the build.

The follow-up also passes the generation-style checks (eight style and five
atlas-presentation tests plus the native honeycomb check) and all 16 data
workflow tests. Eight rendered World/Japan map and legend proofs exercise
the current groundstation compositor and retained viewport replacement,
including source counts and legend bounds. The complete atlas was not
rebuilt: the retained ST2 edition and full current dataset are absent here.

The new development/research pages and delivery links pass the targeted
documentation check (111 local links). The repository-wide checker reports
397 existing errors in unrelated pages, including absent atlas/mineral/ocean
deliveries, old anchors and unexpanded template placeholders. Those are
outside this focused edition.

The gallery includes vector PDFs, editable SVG/SVG.gz and 2560-pixel
PNG/WebP previews, an alternating 16-page combined PDF, and six actual-size
book-format comparison pages. Generated delivery files are ignored by Git;
the configuration, implementation, tests and research record are durable
source changes. The book comparisons are RGB layout studies, not press-ready
interiors or a publishing submission.

## World regeneration and atlas defaults — 10 November 2026

The accepted changes are now regenerated as **four World maps and four A3
landscape legends**, without rebuilding USA details. The new delivery is
[`output/starlink-star-light-world-20261110/`](../../output/starlink-star-light-world-20261110/index.html),
with an [eight-page PDF](../../output/starlink-star-light-world-20261110/starlink-star-light-v3.pdf),
[production record](../../output/starlink-star-light-world-20261110/plan.md),
[source manifest](../../output/starlink-star-light-world-20261110/sources/input-manifest.json)
and [validation receipt](../../output/starlink-star-light-world-20261110/validation.json).
The saved [World recipe](../../config/starlink-star-light-world-20261110.json)
pins the selected local sources. This is a local regeneration, without a new
remote acquisition or activation of an incomplete data edition.

The November astronomy files are now present, superseding the earlier
availability limitation above. SLSL1 uses the **9 November 2026, 17:31:33 UTC**
AuthaGraph all-sky artwork: **726 objects and 35 labels**. Names remain
**9.6 pt**, reduced from 12 pt; the complete sky, halved side margins and
inward edge-label placement are retained. The selected SVG SHA-256 is
`f7694b5eca2a77fdfba9fb6ef018d100f5e1cba988ca310a7b0c808c78835458`.

As requested, SLSL2 and SLSL3 retain the **9 November 2026, 01:12 UTC**
orbital calculation: **972 above-horizon objects** and **17,956 global
objects**. SLSL2 restores the 43.5-inch cyclic World frame with a 4.35-inch
printed shift. Its legend explains horizontal edge wrapping, San Francisco's
zero-degree elevation horizon curve and the fainter celestial equator.
SLSL3 uses **white x debris markers**, including its legend key, while
retaining amber halos, 6 pt Starlink IDs, 1.5× sunbursts and 2× track strokes.
SLSL4 retains the supplied **3 November 2026** collection: 590 antenna
records, 66 PoPs and 124 links, with nine capability silhouettes, doubled
radius span, tethers and the removed land/inset layers. All legends use
**420 × 297 mm**, amber ground, wine text and observer notes.

[`generation-style.json`](../../generation-style.json) now selects this
World recipe. The shared
[`atlas_world.py`](../../scripts/atlas_world.py) compositor supplies these
four World map/legend pairs to both atlas builders. Dataset-bound atlas
builds use their selected native sources and profiles; retained-edition
builds preserve their historical dates and populations while adopting the
presentation. Neither requires this generated World delivery to exist.
Legend counts and source timestamps come from the selected sources. The
atlas exporter reads physical SVG dimensions, supporting 44-inch maps and
A3 legends in the same edition; catalog numbering fits inside the A3 sheet
and preserves its amber background.

```sh
make DATASET=legacy starlink-star-light-world
make DATASET=legacy check-starlink-star-light-world
```

All eight delivered SVG/PDF pairs pass population, rendered-bound, source
hash and physical-page checks. Seven SLSL display tests, seven atlas
presentation/export tests, eight generation-style tests and 40 data-workflow
tests pass. Integration checks compose all eight World sheets through the
current-atlas builder with explicitly selected local sources, plus all
eight through the shared retained-source path. A World map and its A3
legend also pass the atlas's actual 300 dpi exporter: **13,200 × 5,716 px**
and **4,961 × 3,508 px**, respectively. These are focused checks; the full
atlas and its unrelated plates were not regenerated.

### All-sky margin correction and observer debris key

The earlier margin statement above described the outer fit calculation,
not the final rendered artwork. The November astronomy source already
contained a `setouchi-astronomy-frame` inset. Keeping that inset inside the
SLSL framing compounded the projection-frame inset to about **1.16 inches per side**.
The previous checks conserved objects and prevented clipping but missed
this nested presentation transform.

The shared sky renderer now removes that source print-frame transform,
measures the rendered sky glyphs, rays and reference curves, and fits them
uniformly with a **0.125-inch minimum page inset**. Name labels remain
**9.6 pt** and move inward as needed. Measured World ink margins are
**0.1515 inches left/right** and **0.1250 inches top/bottom**. These values
supersede the earlier theoretical 0.923340-inch margin. Object coordinates,
the 726-object population and the astronomy timestamp are preserved.
The production receipt now records rendered margins and rejects a fit
whose measured minimum differs from the requested inset.

The same saved `astronomy_page_margin_inches: 0.125` setting and shared
renderer apply to **both default atlas creation paths**, preventing either
native or previously framed astronomy inputs from reintroducing the inset.
A regression exercises an already framed source and checks the resulting
ink fit and physical label size.

The debris color instruction is also applied to **SLSL2**: its **Objects
Debris** legend key and all plotted debris marks now use a **white x**
(`#ffffff`) with the existing map halos retained. Both orbital World
plates and both World atlas defaults use white debris x markers; the
observer legend's reading notes now describe the white symbol. The eight
World sheets and combined PDF are regenerated together.

The legend follow-up removes the dark backing boxes from every symbol
in the **Symbols / full source population** column, including status,
unknown-size, PoP and aperture examples. Symbols now sit directly on the
amber sheet. Groundstation keys use wine strokes/fills for contrast;
celestial and fleet keys retain their categorical colors and both debris
keys remain white x marks. This shared legend change also applies to the
World atlas defaults. The unknown-size central square remains part of its
symbol, rather than a backing box.

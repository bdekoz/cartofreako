# AuthaGraph bibliography and source provenance

[Documentation index](../index.md) ·
[Geometric context](authagraph-context.md) ·
[Implementation notes](authagraph-implementation-notes.md)

This bibliography distinguishes the analytic formula used by the C++ code
from the earlier graphical construction, the official project description,
the checked-in drawing sheet, and repository integration sources. Web
resources were last checked on 2026-08-01.

## Source hierarchy

When sources describe the construction at different levels, this
implementation uses them in the following order:

1. Narukawa's 2022 peer-reviewed formula paper for the numeric forward
   transform and its distortion qualifications;
2. Narukawa's 2017 paper for the original polyhedral method, rectangular
   tiling, and applications;
3. the official Narukawa Lab AuthaGraph page for the project's own summary and
   terminology; and
4. the checked-in A3 PDF for viewport measurement and visual registration.

The PDF is not used to derive the projection formula. Where the analytic
method and the earlier drawing differ slightly, the formula paper controls the
mathematics and the drawing controls only the compatibility viewport.

## Primary analytic source

1. **Narukawa, Hajime.** “Formulation of AuthaGraph Map Projection and an
   Evaluation of its Distortion” (`オーサグラフ図法の数式化と歪み評価`).
   *Map, Journal of the Japan Cartographers Association*, vol. 60, no. 1,
   2022, pp. 1–16. Japan Cartographers Association.
   [DOI](https://doi.org/10.11212/jjca.60.1_1) ·
   [J-STAGE record](https://www.jstage.jst.go.jp/article/jjca/60/1/60_1/_article/-char/ja/) ·
   [J-STAGE PDF](https://www.jstage.jst.go.jp/article/jjca/60/1/60_1/_pdf/-char/en?download=1)

   This is the direct mathematical source for the implementation. It treats
   Earth as a sphere, restates the four tetrahedron vertices, replaces the
   earlier curved auxiliary tetrahedron with a close conical model, exploits
   symmetry to derive the transform on a 1/24-region, and gives the planar
   coordinate formulas used in `project_spherical_triangle()` as equations
   2.22 and 2.23.

   It is also the controlling source for limitations. The paper compares the
   analytic coastline and graticule with the earlier method rather than
   claiming they are identical. Its Tissot-indicatrix analysis reports
   remaining local area, angular, and distance distortion.

## Original method and design context

2. **Narukawa, Hajime.** “An Original Two Dimensional Map Projection and Its
   Applications in Geopolitical Themes”
   (`正多面体図法を用いた歪みの少ない長方形世界地図図法の提案`).
   *Keio SFC Journal*, vol. 17, no. 1, 2017, pp. 208–232. ISSN 1347-2828.
   [DOI](https://doi.org/10.14991/003.00170001-0208) ·
   [Keio Research Repository record](https://koara.lib.keio.ac.jp/xoonips/modules/xoonips/detail.php?koara_id=0402-1701-0208)

   This paper presents the earlier regular-polyhedron method. It explains the
   sphere-to-curved-tetrahedron-to-tetrahedron construction, the 96-region
   subdivision, rectangular unfolding, periodic tiling, and the ability to
   choose different centers and map aspects. The 2022 paper explicitly treats
   this as the prior method that its formulas approximate.

3. **Narukawa Lab.** “AuthaGraph Map.” Official project page.
   [AuthaGraph Map](https://narukawa-lab.jp/archives/authagraph-map/).

   The laboratory describes the map as an equal-area-type world map invented
   in 1999, explains the tetrahedral transfer and rectangular tessellation,
   and notes that further subdivision is required for a strictly equal-area
   result. It also distributes official drawing-sheet material. This is the
   preferred source for the project's concise public description and for the
   qualified “equal-area type” terminology used in these documents.

4. **Japan Institute of Design Promotion.** “Focused Issues 2016: AuthaGraph
   World Map.” *Good Design Award Journal*, 2016-12-31.
   [Official Good Design article](https://journal.g-mark.org/en/posts/focusedissues2016_004).

   This is design and educational context rather than a formula source. It
   records how the rectangular, tessellating map supports alternative centers
   and viewpoints and discusses the design's communication goals.

## Checked-in source plate

5. **Narukawa Lab.** *15-SP-TESD-03-AG*, AuthaGraph A3 drawing sheet, PDF.
   [Repository asset](../assets/authagraph/15-SP-TESD-03-AG.pdf).

   Local file metadata:

   | Property | Value |
   | --- | --- |
   | Pages | 1 |
   | Page size | 1190.55 x 841.89 PDF points (A3 landscape) |
   | Creator recorded by PDF | Adobe Illustrator CS3 |
   | Creation timestamp recorded by PDF | 2016-02-16 19:12:46 PST |
   | File size | 1,787,675 bytes |
   | SHA-256 | `65c053590f2693038d8d4db3fbc2c6858d7c79705072f195adf2bf2f386f4805` |

   The implementation measures the map rectangle and four singular vertices
   in this plate to define `ag_a3`. The asset provides a visual and coordinate
   reference only; projection results are computed from the analytic formula.

## Supporting cartographic reference

6. **Masaharu, Hiroshi.** *Map Projections: Techniques of Geospatial
   Information* (`地図投影法：地理空間情報の技法`). Asakura Publishing,
   2011.

   Narukawa's 2022 paper cites this text for general projection and distortion
   concepts, including the interpretation of area, angular, and distance
   distortion. It is supporting background and was not used as a source for
   AuthaGraph-specific constants.

## Repository implementation and verification sources

7. **AuthaGraph C++20 forward projection.**
   [`src/cart0freak0-authagraph.h`](../src/cart0freak0-authagraph.h).

   This file contains the four published vertex coordinates, spherical local
   coordinate conversion, equations 2.22 and 2.23, the 24-sector
   rotation/translation table, normalized periodic registration, variable
   `frame.frame_area` validation, and the A3 preset.

8. **AuthaGraph public API test.**
   [`tests/test-authagraph-projection-api.cc`](../tests/test-authagraph-projection-api.cc).

   The test records independently calculated reference points, measured PDF
   vertices, variable-size behavior, complete integer-degree domain coverage,
   antimeridian handling, invalid input, raster naming, and integration with
   the common projection API.

9. **Cartographic integration locations.**
   [`src/a60-svg-carto-geo.h`](../src/a60-svg-carto-geo.h).

   `augment_carto_geo_specific()` defines the poles, seam probes, supple-zone
   probes, and world cities used as integration anchors. The AuthaGraph API
   test covers the complete current set.

10. **AuthaGraph tetrahedral-net illustration.**
    [`docs/authagraph-tetrahedron-net.svg`](authagraph-tetrahedron-net.svg).

    The diagram is a repository-native vector rendering of the exact 24-sector
    origin and rotation table in the C++ implementation. It is explanatory,
    not an independent numeric authority.

## Terminology and claim boundary

The sources use several related descriptions of AuthaGraph. These documents
use the following deliberately narrow language:

- **“Original” or “earlier method”** means the 96-region graphical/modeling
  construction documented in the 2017 paper.
- **“Analytic formulation”** means the conical approximation and equations
  published in 2022 and implemented here.
- **“Equal-area type”** is the official project's qualified description.
  Neither the official page nor the 2022 distortion study supports claiming
  that this finite-subdivision implementation is locally equal-area at every
  point.
- **“A3 compatibility”** means coordinate registration to the checked-in
  drawing sheet's map viewport; it does not mean pixel identity with the
  earlier construction.

These distinctions keep API documentation, mathematical provenance, and
visual-asset provenance separate.

---

[Documentation index](../index.md) ·
[Geometric context](authagraph-context.md) ·
[Implementation notes](authagraph-implementation-notes.md)

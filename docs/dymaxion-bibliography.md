# Dymaxion bibliography and source provenance

[Documentation index](../index.md) ·
[Geometric context](dymaxion-context.md) ·
[Implementation notes](dymaxion-implementation-notes.md)

This bibliography separates Fuller's historical design, Gray's exact
mathematics, the permissively licensed Airocean net data, vendor property
documentation, secondary orientation material, and repository verification.
Web resources were last checked on 2026-08-04.

## Source hierarchy

When sources use “Dymaxion,” “Fuller,” or “Airocean” for related but not
identical operations, this implementation applies them in this order:

1. Gray's 1995 peer-reviewed paper controls the exact sphere-to-equilateral-
   face equations.
2. Gray's author notes control the published Fuller orientation and explain
   the distinction between exact Fuller, gnomonic, and Snyder transforms.
3. PROJ 9.6.2 supplies the MIT-licensed 23-piece spherical and planar net
   registration, not the face-transform formula.
4. BFI and Esri supply historical, usage, distortion, and terminology
   context.
5. Wikipedia is retained because it was named in the development brief, but
   no numeric constant depends on it.

That separation matters. An icosahedron with Fuller's orientation is not by
itself the exact Fuller projection, and an implementation can share the
Airocean outline while using a different face transform.

## Primary mathematical sources

1. **Gray, Robert W.** “Exact Transformation Equations for Fuller's World
   Map.” *Cartographica: The International Journal for Geographic Information
   and Geovisualization*, vol. 32, no. 3, 1995, pp. 17–25.
   [DOI](https://doi.org/10.3138/1677-3273-Q862-1885) ·
   [PROJ bibliography record](https://proj.org/en/stable/zreferences.html#gray1995)

   This is the controlling mathematical source. It gives the exact
   sphere-to-plane equations implemented in
   `project_to_fuller_triangle()`, including the icosahedron edge arc, chord
   length, three symmetric edge-distance terms, and equilateral-triangle
   coordinates.

2. **Gray, Robert W.** “Fuller's Dymaxion™ Map.” *Cartography and Geographic
   Information Systems*, vol. 21, no. 4, 1994, pp. 243–246.
   [DOI](https://doi.org/10.1559/152304094782540628)

   This paper describes the projection method, relates it to Fuller's earlier
   three-way great-circle construction, and reports selected area distortion.
   It supplies general method context rather than the final equations.

3. **Crider, John E.** “Exact Equations for Fuller's Map Projection and
   Inverse.” *Cartographica*, vol. 43, no. 1, 2008, pp. 67–72.
   [DOI](https://doi.org/10.3138/carto.43.1.67)

   Crider derives three alternative exact formulations—spherical linear
   interpolation, geodesic intersection, and spherical triangles—and gives
   inverse procedures. The current public API implements only the forward
   Gray equations, but Crider is the appropriate source for a future inverse.

## Gray's primary author notes

4. **Gray, Robert W.** “Notes to Fuller's World Maps.”
   [Author's index](https://www.rwgrayprojects.com/rbfnotes/maps/graymap1.html).

   The page links Gray's papers, orientation coordinates, algorithm overview,
   distortion material, face/LCD diagrams, and comparison projections.

5. **Gray, Robert W.** “Fuller's World Map: Coordinates.”
   [Icosahedron coordinates](https://www.rwgrayprojects.com/rbfnotes/maps/graymap4.html).

   This is the primary web source for the twelve Fuller-oriented icosahedron
   vertices. The same values appear in PROJ's independently generated
   Airocean tables.

6. **Gray, Robert W.** “An Algorithm for Fuller's World Map.”
   [Algorithm overview](https://www.rwgrayprojects.com/rbfnotes/maps/graymapa.html).

   Gray explains the sequence: select one of 20 spherical triangles, rotate
   to a standard face, compute three spherical arc distances, reuse those
   distances on a planar equilateral triangle, and rotate/translate the
   result into the map.

7. **Gray, Robert W.** “A Visual Comparison of Fuller's World Map.”
   [Fuller, gnomonic, and Snyder comparison](https://www.rwgrayprojects.com/rbfnotes/maps/graymap7.html).

   This is the primary source for the algorithm distinction emphasized in the
   implementation notes. Gray found the coast-only maps visually difficult to
   distinguish but records mathematical and graticule differences, including
   Fuller's exact edge scale and the gnomonic projection's exact inverse.

8. **Gray, Robert W.** “Source Code for Coordinate Transformation.”
   [Reference-program page](https://www.rwgrayprojects.com/rbfnotes/maps/graymap6.html).

   Gray distributes a C reference program and states additional
   non-commercial terms on the page and in the source. That program is not
   copied into this repository. It was executed externally as a numeric oracle
   for the checked-in reference coordinates; the production C++ is an
   independent expression of the published equations.

## Fuller history, terminology, and projection properties

9. **Buckminster Fuller Institute.** “Dymaxion Map.”
   [Official BFI page](https://www.bfi.org/about-fuller/big-ideas/dymaxion-map/).

   BFI describes the map's “one island in one ocean” intent, its educational
   use, and its relationship to Fuller's broader design work. The page also
   identifies `Dymaxion`, `Spaceship Earth`, and `Fuller Projection Map` as BFI
   trademarks and directs licensing inquiries to the institute.

10. **Esri.** “Fuller.” *ArcGIS Pro projection documentation*.
    [Current documentation](https://pro.arcgis.com/en/pro-app/latest/help/mapping/properties/fuller.htm).

    Esri identifies the projection as spherical, faceted, neither conformal
    nor equal-area, and intended for the complete globe. It states that both
    poles are inside facets, graticules break at facet edges, facet-edge scale
    is correct, and distortion increases away from those edges. Esri cites
    Gray 1994, Gray 1995, and Snyder 1993.

11. **Snyder, John P.** *Flattening the Earth: Two Thousand Years of Map
    Projections*. University of Chicago Press, 1993.
    [Publisher record](https://press.uchicago.edu/ucp/books/book/chicago/F/bo3620731.html).

    Snyder supplies broader historical and mathematical context for
    polyhedral and world-map projections. Esri lists this book among its
    Fuller sources; it is not the source of the implemented equations.

12. **Wikipedia contributors.** “Dymaxion map.”
    [Article](https://en.wikipedia.org/wiki/Dymaxion_map).

    This secondary overview distinguishes the 1943 cuboctahedral map from the
    1954 icosahedral Airocean map, describes the land-preserving cuts, and
    correctly warns that the Dymaxion face transform is not gnomonic. Primary
    sources above control disputed or numeric details.

## Permissively licensed net registration

13. **PROJ contributors.** “Airocean.” *PROJ 9.6 documentation*.
    [Projection documentation](https://proj.org/en/9.6/operations/projections/airocean.html).

    PROJ documents vertical and horizontal orientations, global use, and the
    `+proj=airocean` operation introduced in PROJ 9.6. The repository adopts
    its horizontal net bounds and 23-piece layout.

14. **PROJ contributors.** `src/projections/airocean.cpp`, PROJ 9.6.2.
    [Pinned source](https://github.com/OSGeo/PROJ/blob/9.6.2/src/projections/airocean.cpp) ·
    [PROJ license](https://github.com/OSGeo/PROJ/blob/9.6.2/COPYING)

    This is the source of the spherical subface and unfolded planar-triangle
    tables. PROJ's code uses radial face-plane intersection; cartofreako does
    not copy that transform. It instead feeds the same face/net registration
    with Gray's exact edge-distance transform.

    PROJ distributes these data under its MIT-style license. The required
    permission and warranty notice is retained in
    [`a60-carto-projection-dymaxion.h`](../src.projections/a60-carto-projection-dymaxion.h).

## Repository implementation and verification

15. **Dymaxion C++20 forward projection.**
    [`src.projections/a60-carto-projection-dymaxion.h`](../src.projections/a60-carto-projection-dymaxion.h).

    The header contains the orientation and net data, oriented half-space face
    test, exact Fuller equations, split-face registration, normalization,
    variable-frame validation, API class, factory, and native-size preset.

16. **Dymaxion API test.**
    [`tests/test-dymaxion-projection-api.cc`](../tests/test-dymaxion-projection-api.cc).

    The test includes exact edge-fraction behavior and reference coordinates
    evaluated by Gray's separately distributed implementation. Gray's
    unit-edge, lower-left-origin output was transformed only by:

    ```text
    native_x = gray_x * e
    native_y = ((3sqrt(3)/2) - gray_y) * e
    ```

    It also checks all face centroids, variable frames, the complete integer-
    degree domain, antimeridian equivalence, invalid state, and common API
    behavior.

17. **Generation integration.**
    [`projection-generation-common.h`](../src.generate/projection-generation-common.h) ·
    [`projection-area-generation.h`](../src.generate/projection-area-generation.h) ·
    [`generate-geometry.cc`](../src.generate/generate-geometry.cc)

    These files define the 44-inch frame and command argument, seam-safe line
    folding, native-face area clipping, and the 23-face geometry layer.

18. **Generated visual references.**

    - [Geometry SVG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/viewer.html?asset=dymaxion/svg/geometry-dymaxion-44-20.78461.svg.gz)
    - [Graticules SVG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/viewer.html?asset=dymaxion/svg/graticules-dymaxion-44-20.78461.svg.gz)
    - [Earth SVG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/viewer.html?asset=dymaxion/svg/earth-dymaxion-44-20.78461.svg.gz)
    - [Water SVG](https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/viewer.html?asset=dymaxion/svg/water-dymaxion-44-20.78461.svg.gz)

    The corresponding PDF and opaque 3840-pixel PNG forms are checked in
    under `assets.generated/dymaxion/pdf/` and
    `assets.generated/dymaxion/png/`.

## Licensing and claim boundary

- Cartofreako's new C++ code is distributed under the repository's GPLv3-or-
  later terms.
- The substantial PROJ-derived geometry tables retain PROJ's MIT-style notice
  in the implementation header.
- Gray's mathematical papers and author notes are cited as formula sources.
  His separately published C source has additional non-commercial conditions
  and is not incorporated into the repository.
- Numeric reference values are facts produced by an external execution and do
  not embed the reference program.
- BFI's trademark statement is recorded above. Use of a projection name for
  technical identification does not imply BFI endorsement or grant branding
  rights.

---

[Documentation index](../index.md) ·
[Geometric context](dymaxion-context.md) ·
[Implementation notes](dymaxion-implementation-notes.md)

# Star-X bibliography and source provenance

[Documentation index](../index.md) ·
[Geometric context](star-x-context.md) ·
[Implementation notes](star-x-implementation-notes.md)

This bibliography separates the Star-X arrangement from the inherited
Cahill-Keyes geometry, historical octahedral material, and repository test
artifacts. Web resources were last checked on 2026-08-01.

## Direct Star-X sources

1. **De Kosnik, Benjamin.** “Cahill Keyes Star-X.” *sunglint*, 2022-06-27.
   [Project description and plate diagram](https://sunglint.wordpress.com/2022/06/27/cahill-keyes-star-x/).

   This is the primary arrangement source. It describes cutting the four
   horizontal Cahill-Keyes sections into two groups, keeping the first two
   below, rotating the third and fourth sections above them around the North
   Pole, and using a `4 3 / 1 2` plate order. It also records four 17-by-22
   portrait components and the resulting 34-by-44 carrier.

2. **De Kosnik, Benjamin.** “Star-X Internet Maps.” Portfolio entry,
   2022–ongoing.
   [Project overview](https://benjamin.dekosnik.com/work/202x/star-x-internet-maps/).

   This identifies Star-X as a vertically compact, North-Pole-centered
   redesign of the Cahill-Keyes Butterfly M map and records its rotational,
   tiling, and internet-geography context.

3. **De Kosnik, Benjamin.** Historical Star-X rendered composition, 2024.
   [Repository image](../assets.static/adhoc/star-x-2024-08.png).

   The image is used to illustrate orientation and visual context. Its data
   overlays, crops, and page decoration are not numeric projection inputs.

## Inherited Cahill-Keyes implementation

4. **Graça, Mary Jo, and Gene Keyes.** “MegamapMaker-prep9.” Perl source,
   2012-03-15, with later notes dated 2013-11-28.
   [Repository copy](../assets.static/cahill-keyes/MegamapMaker-prep9.pl).

   This is the direct source of the half-octant A–L formulas, preliminary
   scaffold, geographic normalization, and ordinary M-layout used by both
   C++ projections. Its header contains the applicable attribution,
   non-commercial-use, modification, redistribution, and commercial-contact
   terms.

5. **cartofreako contributors.** Native C++20 Cahill-Keyes forward
   projection.
   [`cart0freak0-cahill-keyes.h`](../src.projections/cart0freak0-cahill-keyes.h).

   Star-X calls this implementation directly. It is the numerical authority
   for local face geometry and the source M-layout; Star-X adds the group
   rearrangement, uniform page scale, and polar-composition helpers.

6. **cartofreako contributors.** Cahill-Keyes implementation notes and
   source map.
   [Implementation documentation](cahill-keyes-implementation-notes.md).

   This gives the formulas, constants, scaling proof, raster registration,
   test provenance, and licensing detail intentionally not duplicated in the
   Star-X notes.

## Octant numbering and geometric specifications

7. **Keyes, Gene.** “Around the World in 8 Easy Pieces: The Cahill-Keyes
   1-Degree Globe.” 2013-09-19.
   [All eight octants and polar assemblies](https://www.genekeyes.com/1-DEG-GLOBE/8-octants.html).

   The page labels individual octants and shows the four-octant North- and
   South-Pole assemblies. It is the visual reference for distinguishing
   official geographic octant numbers from left-to-right M-layout slots.

8. **Keyes, Gene.** “Cahill-Keyes Megamap Principles & Specifications.”
   [CKOG principles](https://www.genekeyes.com/CKOG-OOo/1-CKOG-principles.html).

   This specifies the 10,000-unit octant scaffold, mirrored half-octants,
   meridian regimes, polar spacing, equisection, and supple zones inherited
   by Star-X.

9. **Keyes, Gene.** “Cahill-Keyes Octant Graticule and Grid.” 2011-01-12.
   [Construction illustrations](https://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-%26-coastline.html).

   The diagrams connect longitude/latitude input, reference half-octant
   geometry, and final eight-face assembly.

10. **Keyes, Gene.** “Ongoing Development of the Cahill-Keyes Multi-Scale
    Megamap: Papers and Prototypes, 1973–2014.” Updated 2014-09-21.
    [Development index](https://www.genekeyes.com/MENUS/C-K-linklist.html).

11. **Keyes, Gene.** “Zooming to Crimea in the Cahill-Keyes Multi-Scale
    Megamap, Beta-2.” 2014-03-11.
    [Beta-2 demonstration](https://www.genekeyes.com/BETA-2-FOXIT/Beta-2-Foxit.html).

   These two sources document the wider design history and scale-independent
   vector-map intent of the inherited projection.

## Historical octahedral background

12. **Cahill, Bernard J.S.** “An Account of a New Land Map of the World.”
    *Scottish Geographical Magazine*, September 1909, pp. 449–469.

13. **Cahill, Bernard J.S.** “Map of the World.” U.S. Patent 1,054,276.
    Filed 1912-03-05; issued 1913-02-25.
    [Patent text and drawings](https://patents.google.com/patent/US1054276A/en).

14. **Cahill, Bernard J.S.** “A Land Map of the World on a New Projection.”
    *Journal of the Association of Engineering Societies*, October 1913,
    pp. 153–207.

These establish the octahedral and Butterfly background. Star-X uses the
later Cahill-Keyes geometry and De Kosnik arrangement; it is not a direct
implementation of Cahill's 1909 graticule.

## Registration and repository verification

15. **Visionscarto.** “Cahill-Keyes 44 × 22.” SVG map asset, 2018.
    [Repository SVG](../assets.static/visionscarto/visionscarto-cahillkeyes-44x22.svg).

   This is the registration family whose one-degree longitude adjustment is
   shared by the Cahill-Keyes and Star-X public APIs.

16. **cartofreako contributors.** Star-X public API verification.
    [`test-star-x-projection-api.cc`](../tests/test-star-x-projection-api.cc).

17. **cartofreako contributors.** Perl-derived Cahill-Keyes API anchors.
    [`test-cahill-keyes-projection-api.cc`](../tests/test-cahill-keyes-projection-api.cc).

18. **alpha60 contributors.** Geographic integration anchors.
    [`augment_carto_geo_specific`](../src.projections/a60-svg-carto-geo.h).

The Star-X reference points apply its documented rigid transform and centered
page scale to item 17. The test also compares both public projections across
a separate global grid and checks every item 18 location.

19. **De Kosnik, Benjamin.** “Geometry Star-X 34 × 44 with poles.” SVG
    concept drawing, 2026.
    [Repository reference](../assets.static/adhoc/geometry-star-x-34-44.with-poles.svg).

    This illustrates the requested 120-percent page-centered scale, central
    star, and unified Antarctic presentation. Its Antarctica silhouette is
    intentionally not a scale or placement reference; the implementation uses
    the documented projection-relative radius, fixed `60°S` boundary, and
    projection-only lower-clearance registration instead.

20. **Natural Earth.** “1:10m Physical Vectors.”
    [Dataset page](https://www.naturalearthdata.com/downloads/10m-physical-vectors/).

    GDAL clips these physical source layers at the projection's fixed `60°S`
    boundary. Natural Earth supplies geographic content only: it does not
    select the cutoff, radius, bearing, pole position, or lower clearance. The
    same cap can therefore be registered and drawn as a graticule without the
    dataset.

## Source-to-implementation map

| Implementation concern | Principal source |
| --- | --- |
| Half-octant formulas and ordinary M assembly | `MegamapMaker-prep9.pl` and native C++ port |
| Left/right split, 180-degree rotation, `4 3 / 1 2` ordering | 2022 Star-X project description and plate diagram |
| 17:22 variable carrier ratio | Historical 34-by-44 four-panel composition |
| Gap closure and 120-percent page scale | Requested Stage 4/5 geometry and repository concept drawing |
| North-pole star and unified Antarctica | Repository concept drawing for intent; analytic star, fixed `60°S` cut, radius-preserving bearing transform, and projection-only `0.25/44` lower-clearance registration for final geometry |
| Official octant numbering | Keyes's eight-octant and polar-assembly page |
| Longitude registration | Visionscarto asset family and shared C++ helper |
| Numeric compatibility | Perl-derived CK anchors and Star-X API test |

---

[Documentation index](../index.md) ·
[Geometric context](star-x-context.md) ·
[Implementation notes](star-x-implementation-notes.md)

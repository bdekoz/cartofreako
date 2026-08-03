# Cahill-Keyes bibliography and source provenance

[Documentation index](../index.md) ·
[Geometric context](cahill-keyes-context.md) ·
[Implementation notes](cahill-keyes-implementation-notes.md)

This bibliography separates the implementation's direct source from design
specifications, historical Cahill material, related software, and rendering
assets. Web resources were last checked on 2026-08-01.

## Direct implementation source

1. **Graça, Mary Jo, and Gene Keyes.** “MegamapMaker-prep9.” Perl source,
   2012-03-15, with additional notes dated 2013-11-28.
   [Repository copy](../assets.static/cahill-keyes/MegamapMaker-prep9.pl).

   This is the authoritative source for the C++ port. In particular, its
   `Preliminary`, `LLtoMP`, `MPtoXY`, and `MJtoMM` subroutines supply the
   scaffold, geographic normalization, A–L zones, supple-zone construction,
   and standard eight-octant M-layout. The header credits Keyes with the design
   and calculations and Graça with the program. It also contains the applicable
   non-commercial-use, attribution, modification, redistribution, and
   commercial-contact language.

2. **Graça, Mary Jo, and Gene Keyes.** “MegamapMaker-prep9.pl.” Enrico
   Spinielli's public source mirror, created 2012-12-12.
   [GitHub Gist](https://gist.github.com/espinielli/4269612).

   The repository copy, rather than the mirror, is used for reference outputs
   and line-by-line translation. The mirror is useful as an independently
   hosted copy and for source history.

## Gene Keyes specifications and development record

3. **Keyes, Gene.** “Cahill-Keyes Megamap Principles & Specifications.”
   [CKOG in Apache OpenOffice, part 1](https://www.genekeyes.com/CKOG-OOo/1-CKOG-principles.html).

   This is the primary geometric specification used to understand the numeric
   construction. It describes the 10,000-unit octant scaffold, 40,000-unit
   M-layout span, use of a single mirrored half-octant, three meridian-angle
   regimes (`m`, `2m/3`, and `m/3`), polar spacing, equisection, and supple
   transition zones.

4. **Keyes, Gene.** “Cahill-Keyes Octant Graticule and Grid.” 2011-01-12.
   [CKOG construction illustrations, part 7](https://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-%26-coastline.html).

   The construction sequence illustrates longitude/latitude input,
   normalization to one half-octant, conversion to Cartesian template
   coordinates, and assembly of the eight-octant map. It is the best visual
   companion to the C++ numeric pipeline.

5. **Keyes, Gene.** “Ongoing Development of the Cahill-Keyes Multi-Scale
   Megamap: Papers and Prototypes, 1973–2014.” Updated 2014-09-21.
   [Development index](https://www.genekeyes.com/MENUS/C-K-linklist.html).

   This curated chronology links the evolving principles, prototypes,
   Graça's programs, comparison maps, and third-party implementations. It also
   records Keyes's development work from 1975 onward and Graça's programming
   work beginning in 2010.

6. **Keyes, Gene.** “Zooming to Crimea in the Cahill-Keyes Multi-Scale Megamap,
   Beta-2.” 2014-03-11.
   [Beta-2 Foxit demonstration](https://www.genekeyes.com/BETA-2-FOXIT/Beta-2-Foxit.html).

   This demonstrates the projection as a large vector “megamap” that remains
   usable across scales, and provides context for the source program's Beta-2
   construction.

7. **Keyes, Gene, compiler.** “B.J.S. Cahill Online Resource: Octahedral Map of
   the World.” 22nd edition, 2016-09-14.
   [Cahill resource and bibliography](https://www.genekeyes.com/B.J.S._CAHILL_RESOURCE.html).

   This is the principal index to Cahill's original publications, patents,
   diagrams, later commentary, and Keyes's development. Bibliographic details
   for the historical entries below follow this resource.

## B.J.S. Cahill historical sources

8. **Cahill, Bernard J.S.** “An Account of a New Land Map of the World.”
   *Scottish Geographical Magazine*, September 1909, pp. 449–469.

   The first publication of Cahill's Butterfly world map and octahedral
   approach, as catalogued in Keyes's
   [B.J.S. Cahill Online Resource](https://www.genekeyes.com/B.J.S._CAHILL_RESOURCE.html).

9. **Cahill, Bernard J.S.** “Map of the World.” U.S. Patent 1,054,276. Filed
   1912-03-05; issued 1913-02-25.
   [Patent text and drawings](https://patents.google.com/patent/US1054276A/en).

10. **Cahill, Bernard J.S.** “A Land Map of the World on a New Projection.”
    *Journal of the Association of Engineering Societies*, October 1913,
    pp. 153–207.

11. **Cahill, Bernard J.S.** “A World Map to End World Maps.”
    *Geografiska Annaler*, 1934, pp. 97–108.

These works establish the octahedral and Butterfly context from which Keyes's
redesign developed. The C++ code implements the later Cahill-Keyes graticule
specified by Keyes and programmed by Graça; it is not a direct transcription of
Cahill's 1909 projection.

## Related implementations

12. **Fil.** “Cahill-Keyes projection.” Observable notebook.
    [Interactive implementation](https://observablehq.com/@fil/cahill-keyes-projection).

    This provides an interactive JavaScript implementation useful for visual
    comparison. It is not executed by the native C++ projection.

13. **Spinielli, Enrico.** Public mirrors and D3 experiments linked from
    Keyes's [development index](https://www.genekeyes.com/MENUS/C-K-linklist.html),
    including the Graça/Keyes Perl source mirror cited above.

Related implementations are comparison material only. Reference coordinates
for the tests were generated from the checked-in Perl source.

## Repository map and test artifacts

14. **Visionscarto.** “Cahill-Keyes 44 × 22.” SVG map asset, 2018.
    [44-by-22-inch SVG](../assets.static/visionscarto/visionscarto-cahillkeyes-44x22.svg).

15. **Visionscarto.** “Cahill-Keyes 44 × 22, inverse.” 300-DPI PNG map
    asset, 13200 × 6600 pixels.
    [Inverse raster](../assets.static/visionscarto/visionscarto-cahillkeyes-44x22.300-inverse.png).

16. **Visionscarto.** Compact Cahill-Keyes SVG map asset.
    [Compact SVG](../assets.static/visionscarto/visionscarto-cahillkeyes.svg).

The large SVG establishes a 4224 × 2112 logical coordinate example, while the
PNG establishes the 13200 × 6600 raster example. Both are exact 2:1 frames and
motivated the variable-size `frame.frame_area` interface. The public
projection's one-degree longitude adjustment preserves registration with this
asset family.

17. **cartofreako contributors.** Native mathematical verification.
    [`test-cahill-keyes-projection.cc`](../tests/test-cahill-keyes-projection.cc).

18. **cartofreako contributors.** Public API and variable-frame verification.
    [`test-cahill-keyes-projection-api.cc`](../tests/test-cahill-keyes-projection-api.cc).

19. **alpha60 contributors.** Geographic integration anchors.
    [`augment_carto_geo_specific`](../src.projections/a60-svg-carto-geo.h).

## Source-to-implementation map

| Implementation concern | Principal source |
| --- | --- |
| Numeric constants, A–L branching, intersections, octant transforms | Checked-in `MegamapMaker-prep9.pl` |
| Design rationale and construction diagrams | Keyes's CKOG principles and illustration pages |
| Historical relationship to Cahill | Keyes's B.J.S. Cahill resource and Cahill publications |
| Scale-independent vector-map intent | Keyes's Beta-2 demonstration |
| Frame sizes and project-specific registration | Checked-in Visionscarto SVG and PNG assets |
| Numeric compatibility | Perl-derived native and public API tests |

[Documentation index](../index.md) ·
[Geometric context](cahill-keyes-context.md) ·
[Implementation notes](cahill-keyes-implementation-notes.md)

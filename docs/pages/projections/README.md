---
layout: default
title: Projection reference
---

# Projection reference

[Documentation index](../README.md) · [Visual gallery](../gallery/README.md) ·
[Forward/reverse API](../runtime/projection-api.md)

Each projection family keeps its mathematical context, implementation
contract, sources, and visual contact sheet together.

Equal Earth is currently a Stage 16J exploration-only comparison method. Its
standalone forward/reverse API and five comparison plates do not add a seventh
standard runtime or release projection.

Runtime API 3 implements forward and candidate-aware reverse support for all
six families. Cuts, duplicated edges, poles, and Star-X carrier/cap overlap
remain explicit candidates rather than being forced into a false unique
answer. See the [portable fixtures and independent reverse oracles](../runtime/projection-fixtures.md).

| Projection | Context | Implementation | Sources | Contact sheet |
| --- | --- | --- | --- | --- |
| AuthaGraph | [Context](authagraph/context.md) | [Implementation](authagraph/implementation.md) | [Sources](authagraph/bibliography.md) | [Gallery](../gallery/authagraph.md) |
| Cahill–Keyes | [Context](cahill-keyes/context.md) | [Implementation](cahill-keyes/implementation.md) | [Sources](cahill-keyes/bibliography.md) | [Gallery](../gallery/cahill-keyes.md) |
| Dymaxion | [Context](dymaxion/context.md) | [Implementation](dymaxion/implementation.md) | [Sources](dymaxion/bibliography.md) | [Gallery](../gallery/dymaxion.md) |
| Myriahedral | [Context](myriahedral/context.md) | [Implementation](myriahedral/implementation.md) | [Sources](myriahedral/bibliography.md) | [Gallery](../gallery/myriahedral.md) |
| Star-X | [Context](star-x/context.md) | [Implementation](star-x/implementation.md) | [Sources](star-x/bibliography.md) | [Gallery](../gallery/star-x.md) |
| Icosahedral Voronoi | [Context](voronoi/context.md) | [Implementation](voronoi/implementation.md) | [Sources](voronoi/bibliography.md) | [Gallery](../gallery/voronoi.md) |
| Equal Earth *(exploration only)* | [Context](equal-earth/context.md) | [Implementation](equal-earth/implementation.md) | [Sources](equal-earth/bibliography.md) | [Five Stage 16J comparisons](../../development/20260815_equal-earth-positioning-speculations-v01.md) |

## Projection summaries

### AuthaGraph

The AuthaGraph implementation follows Hajime Narukawa's 2022 analytic
formulation, orients the tetrahedron with the four published geographic
vertices, and scales the unfolded periodic net to any valid map frame. A named
A3 preset aligns projected coordinates with the checked-in AuthaGraph drawing
sheet.

Construction examples, screen-coordinate conventions, optional raster naming,
the exact frame predicate, and the source-plate `ag_a3` preset are in the
[AuthaGraph public API notes](authagraph/implementation.md#public-api-and-usage).

### Cahill-Keyes

The Cahill-Keyes implementation is derived from Mary Jo Graça and Gene
Keyes's [`MegamapMaker-prep9.pl`](../../../assets.static/cahill-keyes/MegamapMaker-prep9.pl),
preserves the existing Visionscarto map registration, and scales to any finite,
positive 2:1 `a60::carto::frame`.

Construction examples, compatibility presets, screen coordinates, and error
behavior are in the
[Cahill-Keyes public API notes](cahill-keyes/implementation.md#public-construction-and-usage).
The same guide distinguishes a valid 2:1 world carrier from arbitrary-ratio
[enlargement slices](cahill-keyes/implementation.md#carrier-slicing-and-enlargement).

### Star-X

Star-X reuses the native Cahill-Keyes geometry, splits the ordinary M layout
into left and right groups of four spatial face slots, rotates the right
group by 180 degrees, and stacks it above the left group. This produces the
portrait X arrangement around the northern polar locus without raster tiles
or temporary maps. Its default layout closes the former central gap, enlarges
the complete X 120 percent about the page center, adds a central North-pole
star, and composes Antarctic source geometry once at the lower end at the
projection's geographic scale. Natural Earth provides the standard physical
content but does not control the cap geometry.

The current compositor cuts every source at the fixed `60°S` parallel and
reunites the four southern physical and graticule fragments around one
bottom-center pole. It preserves ordinary source-tip radius and registers the
complete projected boundary independently of any land dataset. Its bottommost
point retains `0.25/44` of frame height—exactly `0.25` units on a 34-by-44
plate—so the blue edge remains inside the view box. Every unified Antarctic
fragment is emitted after the ordinary quadrants and paints above them. The
[Star-X snapshot](../gallery/star-x.md) shows the released
projection family; the next generated release will carry the corrected lower
clearance.

Construction examples and `star_x_layout` configuration are in the
[Star-X public API notes](star-x/implementation.md#public-c-api).
The signed gap and page-centered enlargement default to `-9/88` of frame
height and `1.2`. The central star and unified Antarctica remain layer-aware
SVG composition helpers, not hidden changes to the point transform; cap
points preserve their ordinary source-tip radius while normalizing bearing so
all four bent Cahill-Keyes edges meet. This fixed, data-independent cap makes
a checked reverse practical: undo the carrier into Cahill–Keyes candidates,
or recover cap bearing and solve latitude on `[-90°,-60°]`, while retaining
component identity for overlaps and cuts. The runtime still advertises Star-X
reverse as `candidates`: component `0` owns the ordinary carrier north of
`60°S`, component `1` owns the cutoff and unified cap, and qualifiers resolve
otherwise valid overlap candidates without guessing.

### Dymaxion

The Dymaxion implementation uses Fuller's geographic icosahedron orientation
and Robert W. Gray's exact sphere-to-equilateral-face equations. It places the
result through the 23-piece horizontal Airocean net: 18 complete faces, two
pieces of the Australia parent face, and three pieces of the Japan parent
face. The local transform preserves uniform scale along every facet edge and
is intentionally distinct from a radial, gnomonic projection.

The public frame may have any finite positive size that retains the exact
`11/(3sqrt(3))` net ratio. Construction examples, formulas, face selection,
split-face registration, generator behavior, and verification are in the
[Dymaxion implementation notes](dymaxion/implementation.md). The
[geometric context](dymaxion/context.md) illustrates the facets, cuts,
screen quadrants, graticules, and resulting Earth map.

### Myriahedral

The Myriahedral implementation reproduces the depth-5 icosahedral mesh of
`temporaer/myriaworld` and uses a fixed default tree reconstructed and
registered for the checked-in source raster. Compact embedded
minimum-spanning trees specify which of the 5120 small faces stay attached;
the generation layer also includes five exploratory perspectives and two
exact complementary face-group slices.
The projection locates a spherical face, intersects its central ray with the
face plane, transfers the gnomonic barycentric coordinates to the unfolded
planar copy, and scales the complete net to a variable frame. It has
no runtime dependency on the historical generator, Boost.Graph, S2, GDAL, or
Natural Earth.

Construction examples, the `myriahedral_source` preset, and the distinction
between this raster-registered 16:9 net and other possible Myriahedral nets
are in the
[Myriahedral public API notes](myriahedral/implementation.md#public-api-and-use).
The same notes record the
[perspective configurations](myriahedral/implementation.md#perspective-configuration-metadata)
and [Myriahedral slicing](myriahedral/implementation.md#myriahedral-slicing).
The production
[WebAssembly base-map option](myriahedral/implementation.md#webassembly-land-and-ocean-option)
emits only the `ocean` and `land` layers.

### Icosahedral Voronoi

The Voronoi implementation reproduces the default `geoIcosahedral()` layout
from `d3-geo-polygon` without a JavaScript dependency. Twelve spherical
vertices define twenty regular triangular faces. Each triangle centroid is a
Voronoi site; the forward transform selects the nearest site by maximizing its
dot product with the geographic unit vector, projects onto that face's
gnomonic tangent plane, and carries the result through the fixed shared-edge
unfolding tree.

This is distinct from the Myriahedral projection above: both begin with an
icosahedron, but this projection retains 20 regular faces and a conventional
fixed net, while Myriahedral subdivides to 5120 faces and uses a land-aware
tree.

Construction examples, source-canvas registration, screen coordinates, and
the `voronoi_source` preset are in the
[Voronoi public API notes](voronoi/implementation.md#public-api-and-use).

---
layout: default
title: Cartofreako
---

{% include image-backend.md %}

# Cartofreako

<p class="page-deck">Six projection systems, 32 whole-map plates apiece, and
one visual catalog for comparing physical, sky, network, Anthropocene, and
resource layers.</p>

## Start with the maps

The water pass holds the subject constant across all six projections. Select
a thumbnail for the full-size image; layered SVG and print PDF remain explicit
secondary actions on the AAO backend.

{% include v14-projection-gallery.md %}

[Explore featured subjects and all six projection catalogs](docs/pages/gallery/README.md).

## Start here

| Need | Go to |
| --- | --- |
| Browse the maps | [Visual gallery](docs/pages/gallery/README.md) |
| Build and generate artifacts | [Build and generated artifacts](docs/pages/getting-started/build.md) |
| Choose a projection and read its mathematics | [Projection reference](docs/pages/projections/README.md) |
| Track releases and preservation | [Releases and preservation](docs/pages/releases/README.md) |

## Choose a projection

| Projection | Geometric model | Required map ratio | Public class | Factory |
| --- | --- | ---: | --- | --- |
| AuthaGraph | Oblique tetrahedron, 24 symmetric sectors, periodic rectangle | `4:sqrt(3)` | `agproj` | `make_authagraph_projection()` |
| Cahill-Keyes | Octahedron, 8 octants, M-shaped rectangular layout | `2:1` | `ckproj` | `make_cahill_keyes_projection()` |
| Dymaxion | Fuller-oriented icosahedron, exact 20-face transform, 23-piece Airocean net | `11/(3sqrt(3))` | `dymaxionproj` | `make_dymaxion_projection()` |
| Star-X | Cahill-Keyes octants, two stacked four-face groups, polar-centered X | `17:22` | `starxproj` | `make_star_x_projection()` |
| Myriahedral | Depth-5 icosahedral mesh, land-aware spanning-tree net | `16:9` source canvas | `myriaproj` | `make_myriahedral_projection()` |
| Voronoi | Regular icosahedron, 20 nearest-site gnomonic faces | `48:25` source canvas | `voronoiproj` | `make_voronoi_projection()` |

Equal Earth is not a seventh entry in that release table. Its Stage 16J
standalone API uses the method's native `2.0545821300028537:1` spherical
carrier for explicit comparison work; see the
[implementation boundary](docs/pages/projections/equal-earth/implementation.md).

The six projection summaries are consolidated in the
[projection reference](docs/pages/projections/README.md).

## Attribution and licensing

AuthaGraph was invented and developed by Hajime Narukawa. The implementation
uses his published 2022 analytic formulation and an official Narukawa Lab
drawing sheet. See the
[AuthaGraph implementation provenance](docs/pages/projections/authagraph/implementation.md#provenance)
and [bibliography](docs/pages/projections/authagraph/bibliography.md).

The Cahill-Keyes map design is Gene Keyes's development of B.J.S. Cahill's
octahedral map. The computational construction ported here was written in Perl
by Mary Jo Graça. Its source header permits non-commercial use with attribution
to Graça and Keyes and asks commercial users to contact Gene Keyes. See the
[Cahill-Keyes provenance and licensing note](docs/pages/projections/cahill-keyes/implementation.md#provenance-and-licensing)
and [bibliography](docs/pages/projections/cahill-keyes/bibliography.md).

The Dymaxion map is R. Buckminster Fuller's icosahedral world-map design. The
exact face equations follow Robert W. Gray's published work; the spherical
subface and horizontal net tables derive from PROJ 9.6.2 under its retained
MIT-style notice. Gray's separately distributed reference C program is not
incorporated. See the
[Dymaxion provenance and licensing note](docs/pages/projections/dymaxion/implementation.md#provenance-and-licensing)
and [bibliography](docs/pages/projections/dymaxion/bibliography.md).

Star-X retains that Cahill-Keyes construction and its terms, then applies
Benjamin De Kosnik's two-group arrangement. See the
[Star-X implementation provenance](docs/pages/projections/star-x/implementation.md#provenance-and-limitations)
and [bibliography](docs/pages/projections/star-x/bibliography.md).

The Myriahedral method was published by Jarke J. van Wijk. The fixed mesh,
tree-building method, source command, and raster derive from Hannes Schulz's
`temporaer/myriaworld` implementation; historical land geometry came from
Natural Earth. See the
[Myriahedral implementation provenance](docs/pages/projections/myriahedral/implementation.md#provenance)
and [bibliography](docs/pages/projections/myriahedral/bibliography.md).

The icosahedral Voronoi geometry, parent tree, and registration derive from
the ISC-licensed [`d3-geo-polygon`](https://github.com/d3/d3-geo-polygon)
implementation by Mike Bostock, with the Icosahedral map implemented by Jason
Davies, Enrico Spinielli, and Philippe Rivière. The required ISC notice is
retained in `src.projections/cart0freak0-voronoi.h`. See the
[Voronoi implementation provenance](docs/pages/projections/voronoi/implementation.md#provenance-and-licensing)
and [bibliography](docs/pages/projections/voronoi/bibliography.md).

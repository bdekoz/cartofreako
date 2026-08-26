---
layout: default
title: Cartofreako
---

{% include image-backend.md %}

# Cartofreako

<p class="page-deck">Cartofreako is an atlas explorer with an optional
ai-agented exploration workflow. It has six projection systems, 32 whole-map
plates apiece, and one visual catalog for comparing physical, sky, network,
anthropocene, and resource layers.</p>

{% include v14-projection-gallery.md %}

## Start here

| Need | Go to |
| --- | --- |
| Browse the maps | [Visual gallery](docs/pages/gallery/README.md) |
| Build and generate artifacts | [Build and generated artifacts](docs/pages/getting-started/build.md) |
| Track releases and preservation | [Releases and preservation](docs/pages/releases/README.md) |

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

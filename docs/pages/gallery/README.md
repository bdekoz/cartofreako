---
layout: default
title: Cartofreako visual gallery
---

{% assign release_base = "https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13" %}

# Visual gallery

The Stage 13 catalog contains 32 released whole-map passes in each of six
projections. Start with the images, then follow any projection name to its
complete contact sheet.

This is a sealed v13 release browser, not a preview of the current working
tree. Post-v13 reverse APIs, 1080p catalog products, dual-year particulate
passes, and Stage 15 experiments are documented in the
[technical index](../README.md) and intentionally do not rewrite these S3
links.

Every thumbnail opens the released PNG, whose longest side is 3840 pixels.
The separate **Layered SVG** action opens the compressed vector file in the
S3 viewer; **Print PDF** opens the 44-inch plate. This makes the PNG the fast,
predictable browsing path even for dense Bathymetry Roulette artwork.

## Compare projections

The water pass holds the subject constant so the six projection structures
can be compared directly.

{% include v13-projection-gallery.md %}

## Browse by subject

These six plates lead into the major release families. The full projection
contact sheets retain every pass and the same PNG, SVG, and PDF choices.

<div class="subject-grid">
  <figure class="gallery-card">
    <h3><a href="dymaxion.html#projection-foundations">Earth and water</a></h3>
    <a href="{{ release_base }}/tree/dymaxion/png/water-dymaxion-44-20.78461.png"><img loading="lazy" decoding="async" src="{{ release_base }}/tree/dymaxion/thumbnail/water-dymaxion-44-20.78461.png" width="480" alt="Dymaxion water v13 preview"></a>
    <figcaption>Water · Dymaxion</figcaption>
    <nav class="artifact-actions" aria-label="Dymaxion water formats"><a href="{{ release_base }}/tree/dymaxion/png/water-dymaxion-44-20.78461.png">Full PNG</a><a href="{{ release_base }}/viewer.html?asset=dymaxion/svg/water-dymaxion-44-20.78461.svg.gz">Layered SVG</a><a href="{{ release_base }}/tree/dymaxion/pdf/water-dymaxion-44-20.78461.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="authagraph.html#sky-and-orbital-passes">Sky and orbit</a></h3>
    <a href="{{ release_base }}/tree/authagraph/png/astro-observer-hubble-authagraph-44-19.052559.png"><img loading="lazy" decoding="async" src="{{ release_base }}/tree/authagraph/thumbnail/astro-observer-hubble-authagraph-44-19.052559.png" width="480" alt="AuthaGraph Hubble observer astronomy v13 preview"></a>
    <figcaption>Hubble observer · AuthaGraph</figcaption>
    <nav class="artifact-actions" aria-label="AuthaGraph Hubble observer formats"><a href="{{ release_base }}/tree/authagraph/png/astro-observer-hubble-authagraph-44-19.052559.png">Full PNG</a><a href="{{ release_base }}/viewer.html?asset=authagraph/svg/astro-observer-hubble-authagraph-44-19.052559.svg.gz">Layered SVG</a><a href="{{ release_base }}/tree/authagraph/pdf/astro-observer-hubble-authagraph-44-19.052559.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="star-x.html#networks-and-anthropocene">Networks</a></h3>
    <a href="{{ release_base }}/tree/star-x/png/fiber-synthesized-star-x-34-44.png"><img loading="lazy" decoding="async" src="{{ release_base }}/tree/star-x/thumbnail/fiber-synthesized-star-x-34-44.png" width="480" alt="Star-X Fiber Synthesized v13 preview"></a>
    <figcaption>Fiber Synthesized · Star-X</figcaption>
    <nav class="artifact-actions" aria-label="Star-X Fiber Synthesized formats"><a href="{{ release_base }}/tree/star-x/png/fiber-synthesized-star-x-34-44.png">Full PNG</a><a href="{{ release_base }}/viewer.html?asset=star-x/svg/fiber-synthesized-star-x-34-44.svg.gz">Layered SVG</a><a href="{{ release_base }}/tree/star-x/pdf/fiber-synthesized-star-x-34-44.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="myriahedral.html#networks-and-anthropocene">Anthropocene</a></h3>
    <a href="{{ release_base }}/tree/myriahedral/png/anthropocene-myriahedral-44-24.75.png"><img loading="lazy" decoding="async" src="{{ release_base }}/tree/myriahedral/thumbnail/anthropocene-myriahedral-44-24.75.png" width="480" alt="Myriahedral legacy Anthropocene observation atlas v13 preview"></a>
    <figcaption>Legacy observation atlas · Myriahedral</figcaption>
    <nav class="artifact-actions" aria-label="Myriahedral Anthropocene formats"><a href="{{ release_base }}/tree/myriahedral/png/anthropocene-myriahedral-44-24.75.png">Full PNG</a><a href="{{ release_base }}/viewer.html?asset=myriahedral/svg/anthropocene-myriahedral-44-24.75.svg.gz">Layered SVG</a><a href="{{ release_base }}/tree/myriahedral/pdf/anthropocene-myriahedral-44-24.75.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="myriahedral.html#stage-12-resources">Resources</a></h3>
    <a href="{{ release_base }}/tree/myriahedral/png/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png"><img loading="lazy" decoding="async" src="{{ release_base }}/tree/myriahedral/thumbnail/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png" width="480" alt="Myriahedral coral reef threat v13 preview"></a>
    <figcaption>Coral reef threat · Myriahedral</figcaption>
    <nav class="artifact-actions" aria-label="Myriahedral coral reef threat formats"><a href="{{ release_base }}/tree/myriahedral/png/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png">Full PNG</a><a href="{{ release_base }}/viewer.html?asset=myriahedral/svg/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.svg.gz">Layered SVG</a><a href="{{ release_base }}/tree/myriahedral/pdf/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="voronoi.html#art-passes">Art passes</a></h3>
    <a href="{{ release_base }}/tree/voronoi/png/bathymetry-roulette-voronoi-44-22.916667.png"><img loading="lazy" decoding="async" src="{{ release_base }}/tree/voronoi/thumbnail/bathymetry-roulette-voronoi-44-22.916667.png" width="480" alt="Voronoi Bathymetry Roulette v13 preview"></a>
    <figcaption>Bathymetry Roulette · Voronoi</figcaption>
    <nav class="artifact-actions" aria-label="Voronoi Bathymetry Roulette formats"><a href="{{ release_base }}/tree/voronoi/png/bathymetry-roulette-voronoi-44-22.916667.png">Full PNG</a><a href="{{ release_base }}/viewer.html?asset=voronoi/svg/bathymetry-roulette-voronoi-44-22.916667.svg.gz">Layered SVG</a><a href="{{ release_base }}/tree/voronoi/pdf/bathymetry-roulette-voronoi-44-22.916667.pdf">Print PDF</a></nav>
  </figure>
</div>

## Complete projection contact sheets

- [AuthaGraph — 32 passes](authagraph.md)
- [Cahill–Keyes — 32 passes](cahill-keyes.md)
- [Dymaxion — 32 passes](dymaxion.md)
- [Myriahedral — 32 passes](myriahedral.md)
- [Star-X — 32 passes](star-x.md)
- [Voronoi — 32 passes](voronoi.md)

The v13 [release marker]({{ release_base }}/release.json) is the machine-readable
authority for the sealed S3 inventory. For build instructions, metric status,
projection mathematics, and preservation procedures, continue to the
[technical documentation](../README.md).

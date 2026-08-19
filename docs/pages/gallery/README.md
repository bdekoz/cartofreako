---
layout: default
title: Cartofreako visual gallery
---

{% assign release_base = "https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v14" %}
{% assign viewer_base = "https://bdekoz.github.io/cartofreako/docs/releases/v14-aao-viewer.html?asset=products/standard/" %}

# Visual gallery

The v14 generated-assets release contains 33 standard whole-map passes in each
of six projections. Start with the images, then follow any projection name to
its complete contact sheet.

This is a sealed v14 release browser, not a preview of the current working
tree. Screen-1080p catalog products, the artifact and pass indexes, and the
versioned runtime are documented in the
[v14 AAO release record](../releases/aao-v14.md) and the
[technical index](../README.md).

Every thumbnail opens the released PNG, whose longest side is 3840 pixels.
The separate **Layered SVG** action opens the compressed vector file in the
S3 viewer; **Print PDF** opens the 44-inch plate. This makes the PNG the fast,
predictable browsing path even for dense Bathymetry Roulette artwork.

## Compare projections

The water pass holds the subject constant so the six projection structures
can be compared directly.

{% include v14-projection-gallery.md %}

## Browse by subject

These six plates lead into the major release families. The full projection
contact sheets retain every pass and the same PNG, SVG, and PDF choices.

<div class="subject-grid">
  <figure class="gallery-card">
    <h3><a href="dymaxion.html#projection-foundations">Earth and water</a></h3>
    <a href="{{ release_base }}/products/standard/dymaxion/full/water-dymaxion-44-20.78461.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/dymaxion/thumbnail/water-dymaxion-44-20.78461.png" width="480" alt="Dymaxion water v14 preview"></a>
    <figcaption>Water · Dymaxion</figcaption>
    <nav class="artifact-actions" aria-label="Dymaxion water formats"><a href="{{ release_base }}/products/standard/dymaxion/full/water-dymaxion-44-20.78461.png">Full PNG</a><a href="{{ viewer_base }}dymaxion/master/water-dymaxion-44-20.78461.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/dymaxion/print/water-dymaxion-44-20.78461.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="cahill-keyes.html#projection-foundations">Earth and water</a></h3>
    <a href="{{ release_base }}/products/standard/cahill-keyes/full/water-ck-44-22.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/cahill-keyes/thumbnail/water-ck-44-22.png" width="480" alt="Cahill–Keyes water v14 preview"></a>
    <figcaption>Water · Cahill–Keyes</figcaption>
    <nav class="artifact-actions" aria-label="Cahill–Keyes water formats"><a href="{{ release_base }}/products/standard/cahill-keyes/full/water-ck-44-22.png">Full PNG</a><a href="{{ viewer_base }}cahill-keyes/master/water-ck-44-22.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/cahill-keyes/print/water-ck-44-22.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="authagraph.html#sky-and-orbital-passes">Sky and orbit</a></h3>
    <a href="{{ release_base }}/products/standard/authagraph/full/astro-observer-hubble-authagraph-44-19.052559.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/authagraph/thumbnail/astro-observer-hubble-authagraph-44-19.052559.png" width="480" alt="AuthaGraph Hubble observer astronomy v14 preview"></a>
    <figcaption>Hubble observer · AuthaGraph</figcaption>
    <nav class="artifact-actions" aria-label="AuthaGraph Hubble observer formats"><a href="{{ release_base }}/products/standard/authagraph/full/astro-observer-hubble-authagraph-44-19.052559.png">Full PNG</a><a href="{{ viewer_base }}authagraph/master/astro-observer-hubble-authagraph-44-19.052559.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/authagraph/print/astro-observer-hubble-authagraph-44-19.052559.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="star-x.html#networks-and-anthropocene">Networks</a></h3>
    <a href="{{ release_base }}/products/standard/star-x/full/network-fiber-star-x-34-44.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/star-x/thumbnail/network-fiber-star-x-34-44.png" width="480" alt="Star-X Network Fiber v14 preview"></a>
    <figcaption>Network Fiber · Star-X</figcaption>
    <nav class="artifact-actions" aria-label="Star-X Network Fiber formats"><a href="{{ release_base }}/products/standard/star-x/full/network-fiber-star-x-34-44.png">Full PNG</a><a href="{{ viewer_base }}star-x/master/network-fiber-star-x-34-44.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/star-x/print/network-fiber-star-x-34-44.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="myriahedral.html#networks-and-anthropocene">Anthropocene</a></h3>
    <a href="{{ release_base }}/products/standard/myriahedral/full/anthropocene-particulate-2026-myriahedral-44-24.75.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/myriahedral/thumbnail/anthropocene-particulate-2026-myriahedral-44-24.75.png" width="480" alt="Myriahedral Anthropocene particulate 2026 v14 preview"></a>
    <figcaption>Particulate 2026 · Myriahedral</figcaption>
    <nav class="artifact-actions" aria-label="Myriahedral Anthropocene particulate 2026 formats"><a href="{{ release_base }}/products/standard/myriahedral/full/anthropocene-particulate-2026-myriahedral-44-24.75.png">Full PNG</a><a href="{{ viewer_base }}myriahedral/master/anthropocene-particulate-2026-myriahedral-44-24.75.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/myriahedral/print/anthropocene-particulate-2026-myriahedral-44-24.75.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="myriahedral.html#stage-12-resources">Resources</a></h3>
    <a href="{{ release_base }}/products/standard/myriahedral/full/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/myriahedral/thumbnail/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png" width="480" alt="Myriahedral coral reef threat v14 preview"></a>
    <figcaption>Coral reef threat · Myriahedral</figcaption>
    <nav class="artifact-actions" aria-label="Myriahedral coral reef threat formats"><a href="{{ release_base }}/products/standard/myriahedral/full/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png">Full PNG</a><a href="{{ viewer_base }}myriahedral/master/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/myriahedral/print/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.pdf">Print PDF</a></nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="voronoi.html#art-passes">Art passes</a></h3>
    <a href="{{ release_base }}/products/standard/voronoi/full/bathymetry-roulette-voronoi-44-22.916667.png"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/voronoi/thumbnail/bathymetry-roulette-voronoi-44-22.916667.png" width="480" alt="Voronoi Bathymetry Roulette v14 preview"></a>
    <figcaption>Bathymetry Roulette · Voronoi</figcaption>
    <nav class="artifact-actions" aria-label="Voronoi Bathymetry Roulette formats"><a href="{{ release_base }}/products/standard/voronoi/full/bathymetry-roulette-voronoi-44-22.916667.png">Full PNG</a><a href="{{ viewer_base }}voronoi/master/bathymetry-roulette-voronoi-44-22.916667.svg.gz">Layered SVG</a><a href="{{ release_base }}/products/standard/voronoi/print/bathymetry-roulette-voronoi-44-22.916667.pdf">Print PDF</a></nav>
  </figure>
</div>

## Complete projection contact sheets

- [AuthaGraph — 33 passes](authagraph.md)
- [Cahill–Keyes — 33 passes](cahill-keyes.md)
- [Dymaxion — 33 passes](dymaxion.md)
- [Myriahedral — 33 passes](myriahedral.md)
- [Star-X — 33 passes](star-x.md)
- [Voronoi — 33 passes](voronoi.md)

The v14 [release marker]({{ release_base }}/release.json) is the machine-readable
authority for the sealed S3 inventory. For build instructions, metric status,
projection mathematics, and preservation procedures, continue to the
[technical documentation](../README.md).

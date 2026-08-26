---
layout: default
title: Cartofreako visual gallery
---

{% include image-backend.md %}
{% assign viewer_query = viewer_base | append: "?asset=products/standard/" %}

# Visual gallery

The selected image backend ({{ backend_label }}) contains 33 standard
whole-map passes in each of six projections. The contact sheets present 32
plates in one canonical order on the top-of-tree snapshot (31 standard passes
plus the preview-only Cloud-atmosphere snapshot) and 31 standard passes on
the immutable AAO backend. Start with the images, then follow any projection
name to its complete contact sheet.

The AAO release records, screen-1080p catalog products, the artifact and pass
indexes, and the versioned runtime are documented in the
[v14 AAO release record](../releases/aao-v14.md) and the
[technical index](../README.md).

Every thumbnail opens the {{ full_label }} image, whose longest side is 3840
pixels.{% if show_layered %} The separate **Layered SVG** action opens the
compressed vector file in the viewer.{% endif %}{% if show_print %} **Print
PDF** opens the 44-inch plate.{% endif %} This makes the raster image the
fast, predictable browsing path even for dense artwork.

## Compare projections

The water pass holds the subject constant so the six projection structures
can be compared directly.

{% include v14-projection-gallery.md %}

## Browse by subject

These plates lead into the major release families. The full projection
contact sheets retain every pass and the same format choices.

<div class="subject-grid">
  <figure class="gallery-card">
    <h3><a href="dymaxion.html#projection-foundations">Earth and water</a></h3>
    <a href="{{ release_base }}/products/standard/dymaxion/full/water-dymaxion-44-20.78461{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/dymaxion/thumbnail/water-dymaxion-44-20.78461.png" width="480" alt="Dymaxion water preview"></a>
    <figcaption>Water · Dymaxion</figcaption>
    <nav class="artifact-actions" aria-label="Dymaxion water formats"><a href="{{ release_base }}/products/standard/dymaxion/full/water-dymaxion-44-20.78461{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}dymaxion/master/water-dymaxion-44-20.78461.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/dymaxion/print/water-dymaxion-44-20.78461.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="cahill-keyes.html#projection-foundations">Earth and water</a></h3>
    <a href="{{ release_base }}/products/standard/cahill-keyes/full/water-ck-44-22{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/cahill-keyes/thumbnail/water-ck-44-22.png" width="480" alt="Cahill–Keyes water preview"></a>
    <figcaption>Water · Cahill–Keyes</figcaption>
    <nav class="artifact-actions" aria-label="Cahill–Keyes water formats"><a href="{{ release_base }}/products/standard/cahill-keyes/full/water-ck-44-22{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}cahill-keyes/master/water-ck-44-22.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/cahill-keyes/print/water-ck-44-22.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="authagraph.html#sky-and-orbital-passes">Sky and orbit</a></h3>
    <a href="{{ release_base }}/products/standard/authagraph/full/astro-observer-hubble-authagraph-44-19.052559{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/authagraph/thumbnail/astro-observer-hubble-authagraph-44-19.052559.png" width="480" alt="AuthaGraph Hubble observer astronomy preview"></a>
    <figcaption>Hubble observer · AuthaGraph</figcaption>
    <nav class="artifact-actions" aria-label="AuthaGraph Hubble observer formats"><a href="{{ release_base }}/products/standard/authagraph/full/astro-observer-hubble-authagraph-44-19.052559{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}authagraph/master/astro-observer-hubble-authagraph-44-19.052559.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/authagraph/print/astro-observer-hubble-authagraph-44-19.052559.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="star-x.html#networks">Networks</a></h3>
    <a href="{{ release_base }}/products/standard/star-x/full/network-fiber-star-x-34-44{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/star-x/thumbnail/network-fiber-star-x-34-44.png" width="480" alt="Star-X Network Fiber preview"></a>
    <figcaption>Network Fiber · Star-X</figcaption>
    <nav class="artifact-actions" aria-label="Star-X Network Fiber formats"><a href="{{ release_base }}/products/standard/star-x/full/network-fiber-star-x-34-44{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}star-x/master/network-fiber-star-x-34-44.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/star-x/print/network-fiber-star-x-34-44.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="myriahedral.html#anthropocene">Anthropocene</a></h3>
    <a href="{{ release_base }}/products/standard/myriahedral/full/anthropocene-particulate-2026-myriahedral-44-24.75{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/myriahedral/thumbnail/anthropocene-particulate-2026-myriahedral-44-24.75.png" width="480" alt="Myriahedral Anthropocene particulate 2026 preview"></a>
    <figcaption>Particulate 2026 · Myriahedral</figcaption>
    <nav class="artifact-actions" aria-label="Myriahedral Anthropocene particulate 2026 formats"><a href="{{ release_base }}/products/standard/myriahedral/full/anthropocene-particulate-2026-myriahedral-44-24.75{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}myriahedral/master/anthropocene-particulate-2026-myriahedral-44-24.75.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/myriahedral/print/anthropocene-particulate-2026-myriahedral-44-24.75.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  <figure class="gallery-card">
    <h3><a href="myriahedral.html#stage-12-resources">Resources</a></h3>
    <a href="{{ release_base }}/products/standard/myriahedral/full/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/myriahedral/thumbnail/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.png" width="480" alt="Myriahedral coral reef threat preview"></a>
    <figcaption>Coral reef threat · Myriahedral</figcaption>
    <nav class="artifact-actions" aria-label="Myriahedral coral reef threat formats"><a href="{{ release_base }}/products/standard/myriahedral/full/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}myriahedral/master/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/myriahedral/print/resources-fauna-coral-reef-threat-2011-myriahedral-44-24.75.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  {% if backend_id == "tot" %}
  <figure class="gallery-card">
    <h3><a href="voronoi.html#projection-foundations">Atmosphere</a></h3>
    <a href="{{ release_base }}/products/standard/voronoi/full/cloud-atmosphere-voronoi-44-22.916667{{ full_suffix }}"><img loading="lazy" decoding="async" src="{{ release_base }}/products/standard/voronoi/thumbnail/cloud-atmosphere-voronoi-44-22.916667.png" width="480" alt="Voronoi Cloud-atmosphere preview"></a>
    <figcaption>Cloud-atmosphere · Voronoi</figcaption>
    <nav class="artifact-actions" aria-label="Voronoi Cloud-atmosphere formats"><a href="{{ release_base }}/products/standard/voronoi/full/cloud-atmosphere-voronoi-44-22.916667{{ full_suffix }}">{{ full_label }}</a>{% if show_layered %}<a href="{{ viewer_query }}voronoi/master/cloud-atmosphere-voronoi-44-22.916667.svg.gz">Layered SVG</a>{% endif %}{% if show_print %}<a href="{{ release_base }}/products/standard/voronoi/print/cloud-atmosphere-voronoi-44-22.916667.pdf">Print PDF</a>{% endif %}</nav>
  </figure>
  {% endif %}
</div>

## Complete projection contact sheets

- [AuthaGraph — {% if backend_id == "tot" %}32 plates{% else %}31 passes{% endif %}](authagraph.md)
- [Cahill–Keyes — {% if backend_id == "tot" %}32 plates{% else %}31 passes{% endif %}](cahill-keyes.md)
- [Dymaxion — {% if backend_id == "tot" %}32 plates{% else %}31 passes{% endif %}](dymaxion.md)
- [Myriahedral — {% if backend_id == "tot" %}32 plates{% else %}31 passes{% endif %}](myriahedral.md)
- [Star-X — {% if backend_id == "tot" %}32 plates{% else %}31 passes{% endif %}](star-x.md)
- [Voronoi — {% if backend_id == "tot" %}32 plates{% else %}31 passes{% endif %}](voronoi.md)

The backend [marker]({{ release_base }}/{{ marker_name }}) is the
machine-readable authority for the selected inventory. For build
instructions, metric status, projection mathematics, and preservation
procedures, continue to the
[technical documentation](../README.md).

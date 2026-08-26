{% include image-backend.md %}
{% assign projection_tree = release_base | append: "/products/standard/" | append: page.projection_key %}
{% assign preview_base = release_base | append: "/" | append: page.preview_path %}
{% assign viewer_query = viewer_base | append: "?asset=products/standard/" | append: page.projection_key | append: "/master/" %}

# {{ page.projection_name }} generated snapshot

[Visual gallery]({{site.baseurl}}/docs/pages/gallery/README.html) ·
[Technical documentation]({{site.baseurl}}/docs/pages/README.html) ·
[AuthaGraph]({{site.baseurl}}/docs/pages/gallery/authagraph.html) ·
[Cahill–Keyes]({{site.baseurl}}/docs/pages/gallery/cahill-keyes.html) ·
[Dymaxion]({{site.baseurl}}/docs/pages/gallery/dymaxion.html) ·
[Myriahedral]({{site.baseurl}}/docs/pages/gallery/myriahedral.html) ·
[Star-X]({{site.baseurl}}/docs/pages/gallery/star-x.html) ·
[Voronoi]({{site.baseurl}}/docs/pages/gallery/voronoi.html)

[Generation guide]({{site.baseurl}}/docs/pages/getting-started/generation.html) ·
[v14 AAO release record]({{site.baseurl}}/docs/pages/releases/aao-v14.html) ·
[v13 AAO publication]({{site.baseurl}}/docs/pages/releases/aao-v13.html)

This contact sheet covers every {{ page.projection_name }} whole-map plate in
the selected image backend ({{ backend_label }}). The top-of-tree snapshot
shows 32 plates — 31 standard passes plus the restored preview-only
Cloud-atmosphere snapshot — while the immutable AAO backend shows the 31
standard passes. The legacy Anthropocene observation atlas is not part of
either sheet. Each thumbnail is rendered at contact-sheet width; offscreen
previews load only as they approach the viewport.

Select a thumbnail or **{{ full_label }}** to open the matching full-size
image, whose longest side is 3840 pixels.{% if show_layered %} **Layered SVG**
opens the viewer, which streams the matching `.svg.gz` object through the
browser's `DecompressionStream` API.{% endif %}{% if show_print %} **Print
PDF** opens the 44-inch release plate.{% endif %} This keeps slow, complex
SVGs out of the ordinary image-browsing path.
All artifacts are served from the selected backend, whose
[completion marker]({{ release_base }}/{{ marker_name }}) records its source
revision and inventory.

{% for category in site.data.generated_passes %}
<h2 id="{{ category.id }}">{{ category.title }}</h2>

<table class="artifact-table">
  <thead>
    <tr>
      <th scope="col">Pass</th>
      <th scope="col">Preview and released formats</th>
    </tr>
  </thead>
  <tbody>
  {% for pass in category.passes %}
    {% if pass.tot_only and backend_id != "tot" %}{% continue %}{% endif %}
    {% assign artifact_name = pass.stem | append: "-" | append: page.artifact_suffix %}
    <tr>
      <th scope="row">{{ pass.label }}</th>
      <td>
        <a href="{{ projection_tree }}/full/{{ artifact_name }}{{ full_suffix }}"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/{{ artifact_name }}.png" width="360" alt="{{ page.projection_name }} {{ pass.alt }} preview"></a>
        <nav class="artifact-actions" aria-label="{{ page.projection_name }} {{ pass.label }} formats">
          <a href="{{ projection_tree }}/full/{{ artifact_name }}{{ full_suffix }}">{{ full_label }}</a>
          {%- if show_layered %}<a href="{{ viewer_query }}{{ artifact_name }}.svg.gz">Layered SVG</a>{% endif %}
          {%- if show_print %}<a href="{{ projection_tree }}/print/{{ artifact_name }}.pdf">Print PDF</a>{% endif %}
        </nav>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endfor %}

{% if backend_id == "tot" %}
This top-of-tree sheet is a mutable preview snapshot, not an AAO publication;
its revision is recorded in the [manifest]({{ release_base }}/manifest.json).
Layered SVG and print PDF are not staged under the `browse` tier, so only the
raster actions above are offered.
{% else %}
The AAO prefix is immutable; see the
[v14 AAO release record]({{site.baseurl}}/docs/pages/releases/aao-v14.html)
for the viewer and the direct `.svg.gz` download note.
{% endif %}
Licensed network topology remains outside this release sheet. NASA FIRMS
remains an unrendered review candidate until deliberate promotion; it is not
a missing map layer.

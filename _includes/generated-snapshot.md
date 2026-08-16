{% assign release_base = "https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13" %}
{% assign projection_tree = release_base | append: "/tree/" | append: page.projection_key %}
{% assign viewer_base = release_base | append: "/viewer.html?asset=" | append: page.projection_key | append: "/svg/" %}
{% assign preview_base = release_base | append: "/" | append: page.preview_path %}

# {{ page.projection_name }} generated snapshot

[Visual gallery]({{site.baseurl}}/docs/pages/gallery/) ·
[Technical documentation]({{site.baseurl}}/docs/pages/) ·
[AuthaGraph]({{site.baseurl}}/docs/pages/gallery/authagraph.html) ·
[Cahill–Keyes]({{site.baseurl}}/docs/pages/gallery/cahill-keyes.html) ·
[Dymaxion]({{site.baseurl}}/docs/pages/gallery/dymaxion.html) ·
[Myriahedral]({{site.baseurl}}/docs/pages/gallery/myriahedral.html) ·
[Star-X]({{site.baseurl}}/docs/pages/gallery/star-x.html) ·
[Voronoi]({{site.baseurl}}/docs/pages/gallery/voronoi.html)

[Generation guide]({{site.baseurl}}/docs/pages/getting-started/generation.html) ·
[Stage 13 convergence notes]({{site.baseurl}}/docs/development/stage-13.html) ·
[S3 v13 publication]({{site.baseurl}}/docs/pages/releases/s3-v13.html)

This contact sheet covers every {{ page.projection_name }} whole-map pass in
the complete Stage 13 release graph, including its authorized P-Tree
Cloud-atmosphere snapshot and the explicitly retained legacy Anthropocene
atlas. Each thumbnail is an immutable public PNG rendered at contact-sheet
width; offscreen previews load only as they approach the viewport.

Select a thumbnail or **Full PNG** to open the matching released PNG, whose
longest side is 3840 pixels. **Layered SVG** opens the S3 viewer, which streams
the matching `.svg.gz` object through the browser's `DecompressionStream` API.
**Print PDF** opens the 44-inch release plate. This keeps slow, complex SVGs—
especially the roulette passes—out of the ordinary image-browsing path.
All artifacts are served from the same immutable public S3 release at
`cartofreako/v13/`, whose
[completion marker]({{ release_base }}/release.json) records its source
commit, inventory, manifest, and HTTP delivery contract.

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
    {% assign artifact_name = pass.stem | append: "-" | append: page.artifact_suffix %}
    <tr>
      <th scope="row">{{ pass.label }}</th>
      <td>
        <a href="{{ projection_tree }}/png/{{ artifact_name }}.png"><img class="defer-render" loading="lazy" decoding="async" src="{{ preview_base }}/{{ artifact_name }}.png" width="360" alt="{{ page.projection_name }} {{ pass.alt }} v13 preview"></a>
        <nav class="artifact-actions" aria-label="{{ page.projection_name }} {{ pass.label }} formats">
          <a href="{{ projection_tree }}/png/{{ artifact_name }}.png">Full PNG</a>
          <a href="{{ viewer_base }}{{ artifact_name }}.svg.gz">Layered SVG</a>
          <a href="{{ projection_tree }}/pdf/{{ artifact_name }}.pdf">Print PDF</a>
        </nav>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endfor %}

The P-Tree account workflow was completed explicitly for this release, so its
Cloud-atmosphere product is part of the sheet rather than being implied by a
clean checkout. Licensed network topology remains outside this release sheet.
NASA FIRMS remains an unrendered review candidate until deliberate promotion;
it is not a missing map layer.

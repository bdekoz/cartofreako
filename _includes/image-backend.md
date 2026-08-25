{% assign backend_id = site.image_backend %}
{% if backend_id == "tot" %}
  {% assign release_base = site.image_backend_tot_base | relative_url %}
  {% assign viewer_base = site.image_backend_tot_viewer | relative_url %}
  {% assign backend_label = site.image_backend_tot_label %}
  {% assign full_suffix = site.image_backend_tot_full_suffix %}
  {% assign full_label = site.image_backend_tot_full_label %}
  {% assign show_layered = site.image_backend_tot_layered %}
  {% assign show_print = site.image_backend_tot_print %}
  {% assign marker_name = "manifest.json" %}
{% else %}
  {% assign release_base = site.image_backend_aao_base %}
  {% assign viewer_base = site.image_backend_aao_viewer | relative_url %}
  {% assign backend_label = site.image_backend_aao_label %}
  {% assign full_suffix = site.image_backend_aao_full_suffix %}
  {% assign full_label = site.image_backend_aao_full_label %}
  {% assign show_layered = site.image_backend_aao_layered %}
  {% assign show_print = site.image_backend_aao_print %}
  {% assign marker_name = "release.json" %}
{% endif %}

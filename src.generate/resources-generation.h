// Projection-aware Stage 6b resources country choropleth generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_RESOURCES_GENERATION_H
#define CART0FREAK0_RESOURCES_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <limits>
#include <numeric>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"
#include "resources-data.h"

namespace cart0freak0::resources_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

inline std::string
resources_xml_escape(std::string value)
{
  constexpr std::array replacements {
    std::pair {std::string_view {"&"}, std::string_view {"&amp;"}},
    std::pair {std::string_view {"\""}, std::string_view {"&quot;"}},
    std::pair {std::string_view {"<"}, std::string_view {"&lt;"}},
    std::pair {std::string_view {">"}, std::string_view {"&gt;"}},
  };
  for (const auto& [source, replacement] : replacements)
    {
      std::size_t position = 0;
      while ((position = value.find(source, position)) != std::string::npos)
        {
          value.replace(position, source.size(), replacement);
          position += replacement.size();
        }
    }
  return value;
}

inline std::string
format_resource_number(const double value, const int precision = 3)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  std::string result = output.str();
  if (result.find('.') != std::string::npos)
    {
      while (!result.empty() && result.back() == '0') result.pop_back();
      if (!result.empty() && result.back() == '.') result.pop_back();
    }
  return result;
}

inline svg::typography
resources_typography(const double size, const svg::color_qi color)
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 1, svg::color::none, 0, 0};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline svg::color_qi
resource_color(const std::array<int, 3>& color)
{
  using component = svg::color_qi::itype;
  return {static_cast<component>(color[0]), static_cast<component>(color[1]),
          static_cast<component>(color[2])};
}

inline svg::color_qi
interpolate_resource_color(const resource_palette& palette, const double value)
{
  const double amount = std::clamp(value, 0.0, 1.0);
  std::array<int, 3> result {};
  for (std::size_t index = 0; index != result.size(); ++index)
    result[index] = static_cast<int>(std::lround(
      palette.low[index] + amount * (palette.high[index] - palette.low[index])));
  return resource_color(result);
}

inline std::pair<double, double>
resource_value_range(const std::vector<const country_value*>& values)
{
  resources_require(!values.empty(), "cannot scale an empty resource metric");
  double minimum = std::numeric_limits<double>::infinity();
  double maximum = -std::numeric_limits<double>::infinity();
  for (const country_value* value : values)
    {
      minimum = std::min(minimum, value->value);
      maximum = std::max(maximum, value->value);
    }
  resources_require(std::isfinite(minimum) && std::isfinite(maximum),
                    "resource metric range is not finite");
  return {minimum, maximum};
}

inline double
scale_resource_value(const double value, const double minimum,
                     const double maximum, const metric_scale scale)
{
  if (maximum <= minimum)
    return 0.5;
  if (scale == metric_scale::log1p)
    return (std::log1p(value) - std::log1p(minimum))
      / (std::log1p(maximum) - std::log1p(minimum));
  return (value - minimum) / (maximum - minimum);
}

inline std::string
resources_output_basename(const generation::projection_spec& spec,
                          const resource_family& family,
                          const metric_definition& metric)
{
  resources_require(!metric.output_tag.empty(),
                    "resources output requires a released metric");
  return generation::output_basename(
    family.id + "-" + metric.output_tag, spec);
}

inline void
add_resources_background(generation::projection_document& document,
                         const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("resources-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{239, 238, 231}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"resources-ground\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

struct country_render_stats
{
  std::size_t source_features = 0;
  std::size_t value_features = 0;
  std::size_t missing_features = 0;
  std::size_t paths = 0;
};

inline country_render_stats
add_resource_country_coverage(
  generation::projection_document& document,
  const generation::projection_context& context,
  const resources_profile& profile, const resource_family& family,
  const metric_definition& metric,
  const std::vector<const country_value*>& selected_values)
{
  std::unordered_map<std::string, const country_value*> by_iso3;
  for (const country_value* value : selected_values)
    resources_require(by_iso3.emplace(value->iso3, value).second,
                      "duplicate selected country value " + value->iso3);
  const auto [minimum, maximum] = resource_value_range(selected_values);

  natural_earth::dataset_ptr dataset = natural_earth::open_dataset(
    profile.country_geometry_path);
  OGRLayer* source_layer = dataset->GetLayer(0);
  resources_require(source_layer != nullptr,
                    "resources country geometry has no vector layer");
  const OGRSpatialReference* spatial_reference = source_layer->GetSpatialRef();
  resources_require(spatial_reference != nullptr
                      && spatial_reference->IsGeographic(),
                    "resources country geometry is not geographic WGS84");

  svg::group_element terrestrial;
  terrestrial.start_element("terrestrial-land");
  terrestrial.add_title("Natural Earth Admin-0 country coverage");

  // The country layer intentionally uses compact 1:110m geometry.  Star-X's
  // unified Antarctic cap still comes from the shared Stage 7 implementation;
  // it is drawn underneath the country coverage and remains visible where the
  // Admin-0 Antarctica feature is skipped.
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::layer_spec land {
        "star-x-antarctic-land", "Unified Star-X Antarctic land",
        "ne_10m_land.shp", natural_earth::geometry_role::area,
        natural_earth::area_style(resource_color(family.palette.missing)),
        0.25, 0.5,
      };
      const natural_earth::antarctic_cap cap
        = natural_earth::make_antarctic_cap(context, land);
      svg::group_element star_x_land;
      star_x_land.start_element("star-x-antarctic-land");
      static_cast<void>(natural_earth::render_star_x_source(
        star_x_land, land, context, cap));
      star_x_land.finish_element();
      terrestrial.add_element(star_x_land);
    }

  svg::group_element coverage_layer;
  coverage_layer.start_element("resource-country-coverage");
  svg::group_element missing_layer;
  missing_layer.start_element("resource-missing-data");
  missing_layer.add_title("Countries with no accepted observation");
  svg::group_element value_layer;
  value_layer.start_element("resource-country-values");
  value_layer.add_title(family.title + " — " + metric.title);

  const natural_earth::layer_spec geometry_spec {
    "resource-country", "Resource country geometry", "countries-110m.geojson",
    natural_earth::geometry_role::area,
    natural_earth::area_style(resource_color(family.palette.missing)),
    0.02, 0.4,
  };
  country_render_stats stats;
  source_layer->ResetReading();
  std::size_t sequential_feature = 0;
  while (natural_earth::feature_ptr feature {source_layer->GetNextFeature()})
    {
      ++sequential_feature;
      ++stats.source_features;
      const char* raw_iso3 = feature->GetFieldAsString("RESOURCE_A3");
      const std::string iso3 = raw_iso3 == nullptr ? "" : raw_iso3;
      if (context.spec.kind == generation::projection_kind::star_x
          && iso3 == "ATA")
        continue;
      const auto selected = by_iso3.find(iso3);
      const country_value* value
        = selected == by_iso3.end() ? nullptr : selected->second;
      if (value == nullptr)
        ++stats.missing_features;
      else
        ++stats.value_features;

      const OGRGeometry* source = feature->GetGeometryRef();
      resources_require(source != nullptr && !source->IsEmpty(),
                        "resources country geometry contains an empty feature");
      natural_earth::geometry_ptr prepared
        = natural_earth::prepare_geometry(*source, geometry_spec);
      OGREnvelope envelope;
      prepared->getEnvelope(&envelope);

      svg::style style = value == nullptr
        ? natural_earth::area_style(resource_color(family.palette.missing))
        : natural_earth::area_style(interpolate_resource_color(
            family.palette,
            scale_resource_value(value->value, minimum, maximum, metric.scale)));
      for (std::size_t band_index = 0;
           band_index != natural_earth::longitude_bands.size(); ++band_index)
        {
          const natural_earth::longitude_band band
            = natural_earth::longitude_bands[band_index];
          const bool split_hemispheres
            = natural_earth::requires_star_x_hemisphere_clipping(
                geometry_spec, context);
          const int latitude_piece_count = split_hemispheres ? 2 : 1;
          for (int latitude_piece = 0;
               latitude_piece != latitude_piece_count; ++latitude_piece)
            {
              natural_earth::latitude_range latitude;
              std::string hemisphere_suffix;
              if (split_hemispheres)
                {
                  const bool north = latitude_piece == 1;
                  latitude.south = north ? 0 : -90;
                  latitude.north = north ? 90 : -natural_earth::seam_epsilon;
                  hemisphere_suffix = north ? "-north" : "-south";
                }
              if (!natural_earth::envelope_overlaps(envelope, band, latitude))
                continue;

              std::string path_data;
              std::size_t point_count = 0;
              const std::string error_context = profile.country_geometry_path.string()
                + " feature " + std::to_string(sequential_feature);
              if (natural_earth::requires_area_grid(geometry_spec, context))
                natural_earth::append_gridded_band(
                  path_data, point_count, *prepared, envelope, band,
                  geometry_spec, context, error_context);
              else
                {
                  natural_earth::geometry_ptr clip
                    = natural_earth::make_clip_rectangle(
                        band.west, latitude.south, band.east, latitude.north);
                  natural_earth::geometry_ptr clipped(
                    prepared->Intersection(clip.get()));
                  resources_require(clipped != nullptr,
                                    "GDAL failed to clip " + error_context);
                  if (clipped->IsEmpty())
                    continue;
                  clipped->segmentize(geometry_spec.maximum_segment);
                  natural_earth::append_geometry(
                    path_data, point_count, *clipped, context,
                    natural_earth::geometry_role::area);
                }
              if (path_data.empty())
                continue;

              std::string id = value == nullptr
                ? "resource-missing-" : "resource-value-";
              id += iso3.empty() ? "unassigned" : iso3;
              id += "-feature-" + std::to_string(sequential_feature)
                + "-band-" + std::to_string(band_index + 1)
                + hemisphere_suffix;
              std::string attributes = "fill-rule=\"evenodd\" data-iso3=\""
                + resources_xml_escape(iso3.empty() ? "unassigned" : iso3)
                + "\" data-resource-missing=\""
                + std::string(value == nullptr ? "true" : "false") + "\"";
              if (value != nullptr)
                attributes += " data-resource-family=\""
                  + resources_xml_escape(family.id)
                  + "\" data-resource-metric=\""
                  + resources_xml_escape(metric.id) + "\" data-value=\""
                  + format_resource_number(value->value, 8)
                  + "\" data-observation-year=\""
                  + std::to_string(value->year) + "\" data-value-state=\""
                  + resources_xml_escape(value->state) + "\"";
              svg::group_element& destination
                = value == nullptr ? missing_layer : value_layer;
              destination.add_element(svg::make_path(
                path_data, style, id, true, attributes));
              ++stats.paths;
            }
        }
    }
  resources_require(stats.source_features == 177,
                    "resources country feature count drifted");
  resources_require(stats.value_features == selected_values.size(),
                    "not every normalized resource value joined to a country");
  resources_require(stats.paths != 0 && stats.value_features != 0
                      && stats.missing_features != 0,
                    "resources country layer lacks values or missing coverage");

  missing_layer.finish_element();
  value_layer.finish_element();
  coverage_layer.add_element(missing_layer);
  coverage_layer.add_element(value_layer);
  coverage_layer.finish_element();
  terrestrial.add_element(coverage_layer);
  terrestrial.finish_element();
  document.add_element(terrestrial);
  return stats;
}

inline std::string
resources_metadata_element(
  const generation::projection_spec& spec, const resources_profile& profile,
  const resource_family& family, const metric_definition& metric,
  const std::vector<const country_value*>& selected_values)
{
  resources_require(metric.coverage.has_value(),
                    "selected resources metric lacks coverage metadata");
  const coverage_definition& coverage = *metric.coverage;
  std::string result = "<metadata id=\"resources-metadata\""
    " data-workflow=\"Resources Stage 6b\" data-schema=\"v2\""
    " data-profile=\"" + resources_xml_escape(profile.path.filename().string())
    + "\" data-projection=\"" + std::string(spec.argument)
    + "\" data-family=\"" + resources_xml_escape(family.id)
    + "\" data-metric=\"" + resources_xml_escape(metric.id)
    + "\" data-unit=\"" + resources_xml_escape(metric.unit)
    + "\" data-reference-period=\""
    + resources_xml_escape(metric.reference_period)
    + "\" data-snapshot-as-of=\"" + profile.snapshot_as_of
    + "\" data-country-geometry-sha256=\""
    + profile.country_geometry_sha256 + "\" data-values-sha256=\""
    + profile.values_sha256 + "\" data-covered-countries=\""
    + std::to_string(coverage.covered_countries)
    + "\" data-mapped-countries=\""
    + std::to_string(coverage.mapped_countries)
    + "\" data-country-percent=\""
    + format_resource_number(coverage.country_percent)
    + "\" data-population-percent=\"";
  result += coverage.population_percent.has_value()
    ? format_resource_number(*coverage.population_percent) : "not-applicable";
  result += "\" data-output-percent=\"";
  result += coverage.output_percent.has_value()
    ? format_resource_number(*coverage.output_percent) : "not-applicable";
  result += "\" data-passes-non-sparse=\"true\""
    " data-missing-is-zero=\"false\">\n"
    "<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">\n";
  for (const source_definition& source : profile.sources)
    result += "<rdf:Description id=\"resource-source-"
      + resources_xml_escape(source.id)
      + "\" data-resource-source=\"true\" data-organization=\""
      + resources_xml_escape(source.organization) + "\" data-title=\""
      + resources_xml_escape(source.title) + "\" data-release=\""
      + resources_xml_escape(source.release) + "\" data-url=\""
      + resources_xml_escape(source.url) + "\" data-retrieved-at=\""
      + resources_xml_escape(source.retrieved_at) + "\" data-license=\""
      + resources_xml_escape(source.license) + "\" data-sha256=\""
      + resources_xml_escape(source.sha256) + "\"></rdf:Description>\n";
  for (const resource_family& profile_family : profile.families)
    for (const metric_definition& profile_metric : profile_family.metrics)
      result += "<rdf:Description id=\"resource-metric-"
        + resources_xml_escape(profile_family.id + "-" + profile_metric.id)
        + "\" data-resource-metric-catalog=\"true\" data-family=\""
        + resources_xml_escape(profile_family.id) + "\" data-metric=\""
        + resources_xml_escape(profile_metric.id) + "\" data-title=\""
        + resources_xml_escape(profile_metric.title) + "\" data-unit=\""
        + resources_xml_escape(profile_metric.unit)
        + "\" data-evidence-class=\""
        + resources_xml_escape(profile_metric.evidence_class)
        + "\" data-status=\""
        + std::string(metric_status_name(profile_metric.status))
        + "\"></rdf:Description>\n";
  for (const country_value* value : selected_values)
    result += "<rdf:Description id=\"resource-value-catalog-"
      + resources_xml_escape(value->iso3)
      + "\" data-resource-value-record=\"true\" data-iso3=\""
      + resources_xml_escape(value->iso3) + "\" data-value=\""
      + format_resource_number(value->value, 8)
      + "\" data-observation-year=\"" + std::to_string(value->year)
      + "\" data-value-state=\"" + resources_xml_escape(value->state)
      + "\"></rdf:Description>\n";
  result += "</rdf:RDF>\n</metadata>\n";
  return result;
}

inline void
add_resources_legend(generation::projection_document& document,
                     const generation::projection_context& context,
                     const resources_profile& profile,
                     const resource_family& family,
                     const metric_definition& metric,
                     const std::vector<const country_value*>& selected_values)
{
  const auto [minimum, maximum] = resource_value_range(selected_values);
  const coverage_definition& coverage = *metric.coverage;
  svg::group_element layer;
  layer.start_element("resource-legend");
  const double width = std::min(14.5, context.map_frame.width() - 0.6);
  const double height = 1.38;
  const double left = 0.30;
  const double top = 0.30;
  svg::rect_element panel;
  panel.start_element();
  panel.add_data({left, top, width, height});
  panel.add_style({{250, 249, 244}, 0.93, {62, 61, 57}, 0.62, 0.015});
  panel.add_raw("id=\"resource-legend-panel\"");
  panel.finish_element();
  layer.add_element(panel);

  svg::typography heading = resources_typography(0.18, {34, 35, 35});
  heading._M_w = svg::typography::weight::bold;
  svg::styled_text(layer,
    resources_xml_escape(family.title + " / " + metric.title),
    {left + 0.22, top + 0.24}, heading);
  svg::typography detail = resources_typography(0.105, {60, 61, 59});
  svg::styled_text(layer,
    resources_xml_escape(metric.unit + " · " + metric.reference_period
      + " · " + metric.evidence_class),
    {left + 0.22, top + 0.49}, detail);

  constexpr std::size_t swatch_count = 5;
  const double swatch_width = 0.62;
  const double swatch_top = top + 0.69;
  for (std::size_t index = 0; index != swatch_count; ++index)
    {
      const double amount = static_cast<double>(index) / (swatch_count - 1);
      svg::rect_element swatch;
      swatch.start_element();
      swatch.add_data({left + 0.22 + index * swatch_width, swatch_top,
                       swatch_width, 0.22});
      swatch.add_style({interpolate_resource_color(family.palette, amount), 1,
                        svg::color::none, 0, 0});
      swatch.add_raw("data-resource-legend-swatch=\"true\"");
      swatch.finish_element();
      layer.add_element(swatch);
    }
  svg::rect_element missing;
  missing.start_element();
  missing.add_data({left + 3.62, swatch_top, 0.34, 0.22});
  missing.add_style({resource_color(family.palette.missing), 1,
                     {92, 91, 85}, 0.8, 0.008});
  missing.add_raw("data-resource-legend-missing=\"true\"");
  missing.finish_element();
  layer.add_element(missing);
  svg::typography labels = resources_typography(0.09, {65, 66, 63});
  svg::styled_text(layer, format_resource_number(minimum),
                   {left + 0.22, top + 1.03}, labels);
  svg::styled_text(layer, format_resource_number(maximum),
                   {left + 2.72, top + 1.03}, labels);
  svg::styled_text(layer, "missing / unknown",
                   {left + 4.06, swatch_top + 0.11}, labels);

  std::string coverage_text = "Coverage: "
    + std::to_string(coverage.covered_countries) + "/"
    + std::to_string(coverage.mapped_countries) + " mapped countries";
  if (coverage.population_percent.has_value())
    coverage_text += " · "
      + format_resource_number(*coverage.population_percent)
      + "% mapped population";
  if (coverage.output_percent.has_value())
    coverage_text += " · " + format_resource_number(*coverage.output_percent)
      + "% source world output";
  coverage_text += " · gate passed";
  svg::styled_text(layer, resources_xml_escape(coverage_text),
                   {left + 5.70, swatch_top + 0.11}, labels);
  svg::styled_text(layer,
    resources_xml_escape("Snapshot " + profile.snapshot_as_of
      + " · missing is not zero · catalogue "
      + std::to_string(family.metrics.size()) + " metrics"),
    {left + 5.70, top + 1.03}, labels);
  layer.finish_element();
  document.add_element(layer);
}

inline void
generate_resources(const generation::projection_spec& spec,
                   const resources_profile& profile,
                   const resource_family& family)
{
  const metric_definition& metric = default_resource_metric(family);
  const std::vector<const country_value*> values
    = resource_metric_values(profile, family, metric);
  resources_require(!values.empty(), family.id + " default metric has no values");
  const std::string basename = resources_output_basename(spec, family, metric);
  const generation::projection_context context(spec, basename);
  generation::projection_document document(
    basename, std::string(spec.title) + " " + family.title + ": "
      + metric.title + " (Resources Stage 6b)",
    context.map_frame.frame_area);
  document.add_raw(resources_metadata_element(
    spec, profile, family, metric, values));
  add_resources_background(document, context);
  natural_earth::initialize_gdal();
  static_cast<void>(add_resource_country_coverage(
    document, context, profile, family, metric, values));
  add_resources_legend(document, context, profile, family, metric, values);
}

inline std::string
read_generated_resources(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  resources_require(input.good(), "failed to open generated " + basename
                                    + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline std::size_t
resources_token_count(const std::string_view text,
                      const std::string_view token)
{
  std::size_t count = 0;
  std::size_t position = 0;
  while ((position = text.find(token, position)) != std::string_view::npos)
    {
      ++count;
      position += token.size();
    }
  return count;
}

inline void
verify_generated_resources(
  const std::string& generated,
  const generation::projection_context& context,
  const resources_profile& profile, const resource_family& family,
  const metric_definition& metric,
  const std::vector<const country_value*>& values)
{
  resources_require(generated.find(generation::view_box_fragment(context))
                      != std::string::npos,
                    "generated resources SVG has the wrong viewBox");
  constexpr std::array required_layers {
    std::string_view {"resources-background"},
    std::string_view {"terrestrial-land"},
    std::string_view {"resource-country-coverage"},
    std::string_view {"resource-missing-data"},
    std::string_view {"resource-country-values"},
    std::string_view {"resource-legend"},
  };
  for (const std::string_view layer : required_layers)
    resources_require(generated.find("<g id=\"" + std::string(layer) + "\">")
                        != std::string::npos,
                      "generated resources SVG is missing layer "
                        + std::string(layer));
  resources_require(resources_token_count(
    generated, "data-resource-value-record=\"true\"") == values.size(),
    "generated resources SVG has an incomplete value catalogue");
  resources_require(resources_token_count(
    generated, "data-resource-metric-catalog=\"true\"")
      == std::accumulate(profile.families.begin(), profile.families.end(),
                         std::size_t {0},
                         [](const std::size_t count,
                            const resource_family& item) {
                           return count + item.metrics.size();
                         }),
    "generated resources SVG has an incomplete metric catalogue");
  resources_require(generated.find("id=\"resources-metadata\"")
                      != std::string::npos
                      && generated.find("data-workflow=\"Resources Stage 6b\"")
                           != std::string::npos
                      && generated.find("data-family=\"" + family.id + "\"")
                           != std::string::npos
                      && generated.find("data-metric=\"" + metric.id + "\"")
                           != std::string::npos
                      && generated.find("data-passes-non-sparse=\"true\"")
                           != std::string::npos
                      && generated.find("data-missing-is-zero=\"false\"")
                           != std::string::npos,
                    "generated resources SVG lacks Stage 6b metadata");
  resources_require(generated.find(" nan ") == std::string::npos
                      && generated.find(" -nan ") == std::string::npos
                      && generated.find(" inf ") == std::string::npos
                      && generated.find(" -inf ") == std::string::npos,
                    "generated resources SVG has non-finite data");
  generation::verify_configured_label_font(generated, "resources SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-resources FAMILY PROJECTION PROFILE.json");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[2]);
  const resources_profile profile = load_resources_profile(
    std::filesystem::absolute(argv[3]));
  const resource_family& family = find_resource_family(profile, argv[1]);
  const metric_definition& metric = default_resource_metric(family);
  const std::vector<const country_value*> values
    = resource_metric_values(profile, family, metric);
  const std::string basename = resources_output_basename(spec, family, metric);
  const generation::projection_context context(spec, basename);
  generate_resources(spec, profile, family);
  verify_generated_resources(
    read_generated_resources(basename), context, profile, family, metric, values);
  return 0;
}

} // namespace cart0freak0::resources_generation

#endif // CART0FREAK0_RESOURCES_GENERATION_H

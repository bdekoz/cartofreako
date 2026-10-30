// Projection-aware Stage 12 resources country and spatial generation.
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
#include <map>
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
#include <izzi-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"
#include "resources-data.h"

#include "resource-colors.h"
#include "generation-honeycomb.h"

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

// Country fills and spatial cells use the reviewed shared style opacity.
inline svg::style
resource_data_style(const svg::color_qi color, const double opacity)
{
  resources_require(opacity > 0 && opacity <= 1,
                    "resource data opacity must be in (0, 1]");
  return {color, opacity, color, opacity, 0.0025};
}

inline constexpr auto solar_capacity_colors = generation_style::solar_colors;

inline std::size_t
solar_capacity_bin(const double megawatts)
{
  constexpr auto bounds = generation_style::solar_upper_mw;
  return std::upper_bound(bounds.begin(), bounds.end(), megawatts) - bounds.begin();
}

inline double
resource_metric_opacity(const resources_profile&, const metric_definition&)
{ return generation_style::resources_fill_opacity; }

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
  rectangle.add_style({{241, 241, 241}, 1, svg::color::none, 0, 0});
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
        = natural_earth::make_antarctic_cap(context);
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
        : resource_data_style(
            metric.id == "solar-capacity" ? solar_capacity_colors[solar_capacity_bin(value->value)] : resource_metric_palette(metric.id)[std::min<std::size_t>(4, static_cast<std::size_t>(5 * scale_resource_value(value->value, minimum, maximum, metric.scale)))],
            resource_metric_opacity(profile, metric));
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

inline svg::color_qi
reef_threat_color(const int rank)
{
  switch (rank)
    {
    case 1: return generation_style::coral_colors[0];
    case 2: return generation_style::coral_colors[1];
    case 3: return generation_style::coral_colors[2];
    case 4: return generation_style::coral_colors[3];
    default: throw std::runtime_error("unknown coral-reef threat rank");
    }
}

struct spatial_render_stats
{
  std::size_t source_features = 0;
  std::size_t rendered_features = 0;
  std::size_t paths = 0;
  std::size_t points = 0;
};

inline spatial_render_stats
add_resource_spatial_coverage(
  generation::projection_document& document,
  const generation::projection_context& context,
  const resources_profile& profile,
  const metric_definition& metric)
{
  resources_require(metric.spatial.has_value(), "selected resource lacks spatial metadata");
  const spatial_definition& spatial = *metric.spatial;
  svg::group_element terrestrial;
  terrestrial.start_element("terrestrial-land");
  const natural_earth::layer_spec land {
    "resource-land", "Subdued terrestrial land", "ne_10m_land.shp",
    natural_earth::geometry_role::area,
    natural_earth::area_style({242, 242, 242}), 0.05, 0.5,
  };
  if (context.spec.kind == generation::projection_kind::star_x)
    static_cast<void>(natural_earth::render_star_x_source(
      terrestrial, land, context, natural_earth::make_antarctic_cap(context)));
  else
    static_cast<void>(natural_earth::render_source(terrestrial, land, context));

  struct group {
    int q, r;
    std::array<std::size_t, 4> counts {};
    std::vector<std::pair<std::string, int>> members;
  };
  std::vector<group> groups;
  std::map<std::pair<int, int>, std::size_t> lookup;
  auto dataset = natural_earth::open_dataset(spatial.path);
  OGRLayer* layer = dataset->GetLayer(0);
  resources_require(layer && layer->GetSpatialRef() && layer->GetSpatialRef()->IsGeographic(),
                    "reef input must contain geographic geometry");
  const int index = layer->GetLayerDefn()->GetFieldIndex(spatial.class_property.c_str());
  resources_require(index >= 0, "reef input lacks threat class");
  constexpr double radius = generation_style::coral_macrohex_radius_in;
  spatial_render_stats stats;
  layer->ResetReading();
  while (natural_earth::feature_ptr feature {layer->GetNextFeature()})
    {
      ++stats.source_features;
      const int rank = feature->GetFieldAsInteger(index);
      resources_require(rank >= 1 && rank <= 4, "invalid reef threat rank");
      const auto* geometry = feature->GetGeometryRef();
      resources_require(geometry && !geometry->IsEmpty(), "empty reef source cell");
      OGREnvelope envelope;
      geometry->getEnvelope(&envelope);
      const auto [x, y] = generation::project_point(context,
        {(envelope.MinY + envelope.MaxY) / 2, (envelope.MinX + envelope.MaxX) / 2});
      const auto key = generation_honeycomb::cell(x, y, radius);
      const auto [entry, inserted] = lookup.emplace(key, groups.size());
      if (inserted) groups.push_back(group {key.first, key.second, {}, {}});
      auto& item = groups[entry->second];
      ++item.counts[rank-1];
      const int id_field = feature->GetFieldIndex("id");
      const std::string id = id_field >= 0 ? feature->GetFieldAsString(id_field)
                                          : std::to_string(feature->GetFID());
      item.members.emplace_back(id, rank);
      ++stats.rendered_features;
    }
  resources_require(stats.source_features == spatial.mapped_features,
                    "reef source-cell count drifted");
  svg::group_element coverage;
  coverage.start_element("resource-spatial-coverage");
  coverage.add_title("Radial honeycombs preserve source-cell counts and threat-class composition; display footprints are not reef area");
  svg::group_element glyphs;
  glyphs.start_element("reef-groups");
  for (const auto& item : groups)
    {
      const double x = 1.5 * radius * item.q;
      const double y = std::sqrt(3.0) * radius * (item.r + item.q / 2.0);
      const auto allocated = generation_honeycomb::allocation(
        item.counts, generation_style::coral_display_cell_cap);
      const auto visible = std::accumulate(allocated.begin(), allocated.end(), std::size_t{});
      const auto positions = generation_honeycomb::offsets(
        visible, generation_style::coral_microhex_spacing_radius_in);
      std::string classes;
      for (auto count : item.counts) classes += (classes.empty() ? "" : ",") + std::to_string(count);
      glyphs.add_raw("<g data-cell-count=\"" + std::to_string(item.members.size())
        + "\" data-class-counts=\"" + classes + "\">\n");
      // Preserve every original cell's membership even when a glyph is capped.
      for (const auto& [id, rank] : item.members)
        glyphs.add_raw("<desc data-resource-spatial=\"true\" data-source-cell=\"" + resources_xml_escape(id)
          + "\" data-threat-rank=\"" + std::to_string(rank) + "\"/>\n");
      std::size_t n = 0;
      for (std::size_t rank = 0; rank < 4; ++rank)
        for (std::size_t c = 0; c < allocated[rank]; ++c)
          {
            const auto [dx, dy] = positions[n++];
            svg::vrange vertices;
            for (unsigned corner = 0; corner < 7; ++corner)
              {
                const double angle = corner * std::acos(-1.0) / 3;
                vertices.emplace_back(x+dx+generation_style::coral_microhex_radius_in*std::cos(angle),
                                      y+dy+generation_style::coral_microhex_radius_in*std::sin(angle));
              }
            glyphs.add_element(svg::make_path(svg::make_path_data_from_points(vertices),
              {reef_threat_color(rank+1), resource_metric_opacity(profile, metric), svg::color::white,
               1, generation_style::coral_microhex_outline_in}, "", true));
            ++stats.paths; stats.points += 6;
          }
      glyphs.add_raw("</g>\n");
    }
  glyphs.finish_element(); coverage.add_element(glyphs); coverage.finish_element();
  terrestrial.add_element(coverage); terrestrial.finish_element(); document.add_element(terrestrial);
  return stats;
}

inline std::string
resources_metadata_element(
  const generation::projection_spec& spec, const resources_profile& profile,
  const resource_family& family, const metric_definition& metric,
  const std::vector<const country_value*>& selected_values)
{
  std::string result = "<metadata id=\"resources-metadata\""
    " data-workflow=\"Resources Stage 12\" data-schema=\"v3\""
    " data-title-scale=\"2\""
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
    + profile.values_sha256 + "\" data-graphic-opacity=\""
    + format_resource_number(resource_metric_opacity(profile, metric), 2) + "\"";
  if (metric.coverage.has_value())
    {
      const coverage_definition& coverage = *metric.coverage;
      result += " data-coverage-kind=\"country\" data-covered-countries=\""
        + std::to_string(coverage.covered_countries)
        + "\" data-mapped-countries=\""
        + std::to_string(coverage.mapped_countries)
        + "\" data-country-percent=\""
        + format_resource_number(coverage.country_percent)
        + "\" data-population-percent=\"";
      result += coverage.population_percent.has_value()
        ? format_resource_number(*coverage.population_percent)
        : "not-applicable";
      result += "\" data-output-percent=\"";
      result += coverage.output_percent.has_value()
        ? format_resource_number(*coverage.output_percent)
        : "not-applicable";
      result += "\"";
    }
  else
    {
      resources_require(metric.spatial.has_value(),
                        "selected resources metric lacks release metadata");
      const spatial_definition& spatial = *metric.spatial;
      result += " data-coverage-kind=\"spatial\" data-spatial-sha256=\""
        + spatial.sha256 + "\" data-source-features=\""
        + std::to_string(spatial.source_features)
        + "\" data-source-polygons=\""
        + std::to_string(spatial.source_polygons)
        + "\" data-mapped-features=\""
        + std::to_string(spatial.mapped_features)
        + "\" data-resolution-degrees=\""
        + format_resource_number(spatial.resolution_degrees)
        + "\" data-class-property=\""
        + resources_xml_escape(spatial.class_property) + "\"";
    }
  result += " data-passes-non-sparse=\"true\""
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
  if (metric.id == "solar-capacity")
    {
      svg::group_element layer;
      layer.start_element("resource-legend",
        generation::bottom_right_legend_transform(context, 20.2, 2.6));
      svg::rect_element panel; panel.start_element();
      panel.add_data({0, 0, 20.2, 2.6});
      panel.add_style({{255, 255, 255}, 0.96, svg::color::none, 0, 0});
      panel.add_raw("id=\"resource-legend-panel\"");
      panel.finish_element(); layer.add_element(panel);
      auto heading = resources_typography(0.36, {42, 40, 36});
      heading._M_w = svg::typography::weight::bold;
      svg::styled_text(layer, "INSTALLED SOLAR GENERATING CAPACITY / " + metric.reference_period,
        {0.3, 0.40}, heading);
      std::array<std::string, 6> labels;
      const auto number = [](double value) {
        std::string text = format_resource_number(value, 0);
        for (int i = static_cast<int>(text.size()) - 3; i > 0; i -= 3)
          text.insert(i, ",");
        return text;
      };
      for (std::size_t i = 0; i < labels.size(); ++i)
        labels[i] = number(i == 0 ? 0 : generation_style::solar_upper_mw[i-1])
          + (i == labels.size()-1 ? "+" : " to <" + number(generation_style::solar_upper_mw[i]));
      for (std::size_t i = 0; i < labels.size(); ++i)
        {
          svg::rect_element swatch; swatch.start_element();
          swatch.add_data({0.3 + i * 3.30, 0.78, 0.48, 0.28});
          swatch.add_style({solar_capacity_colors[i], 1, svg::color::none, 0, 0});
          swatch.add_raw("data-resource-legend-swatch=\"true\"");
          swatch.finish_element(); layer.add_element(swatch);
          svg::styled_text(layer, labels[i], {0.90 + i * 3.30, 0.92}, resources_typography(0.18, {42, 40, 36}));
        }
      svg::styled_text(layer, "MW per country, at year end. 1,000 MW = 1 GW. Solid colours indicate installed capacity; grey = missing.",
        {0.3, 1.42}, resources_typography(0.22, {42, 40, 36}));
      svg::styled_text(layer, "IRENA Renewable Capacity Statistics 2026; 169 of 176 mapped countries. Not electricity generation or local irradiance.",
        {0.3, 1.86}, resources_typography(0.21, {42, 40, 36}));
      svg::styled_text(layer, "Country totals do not locate solar farms. Future comparisons should add capacity per person, generation and annual additions.",
        {0.3, 2.25}, resources_typography(0.20, {42, 40, 36}));
      layer.finish_element(); document.add_element(layer); return;
    }
  const auto [minimum, maximum] = resource_value_range(selected_values);
  const auto palette = resource_metric_palette(metric.id);
  svg::group_element layer;
  layer.start_element("resource-legend", generation::bottom_right_legend_transform(context, 23.6, 2.6));
  svg::rect_element panel; panel.start_element();panel.add_data({0, 0, 23.6, 2.6});
  panel.add_style({{255, 255, 255}, 0.96, svg::color::none, 0, 0});
  panel.add_raw("id=\"resource-legend-panel\"");panel.finish_element();layer.add_element(panel);
  auto title = resources_typography(0.36, {42, 40, 36});title._M_w=svg::typography::weight::bold;
  svg::styled_text(layer, family.title + " / " + metric.title, {0.3, 0.4}, title);
  const auto boundary = [&](double fraction) {
    return metric.scale == metric_scale::log1p
      ? std::expm1(std::log1p(minimum) + fraction * (std::log1p(maximum)-std::log1p(minimum)))
      : minimum + fraction * (maximum-minimum);
  };
  for (std::size_t i=0; i<5; ++i) {
    svg::rect_element swatch;swatch.start_element();swatch.add_data({0.3+i*4.6, 0.78, 0.48, 0.28});
    swatch.add_style({palette[i],1,svg::color::none,0,0});
    swatch.add_raw("data-resource-legend-swatch=\"true\"");swatch.finish_element();layer.add_element(swatch);
    const std::string label = format_resource_number(boundary(i/5.0),2)
      + (i==4 ? " to " : " to <") + format_resource_number(boundary((i+1)/5.0),2);
    svg::styled_text(layer,label,{0.9+i*4.6,0.92},resources_typography(0.19,{42,40,36}));
  }
  svg::styled_text(layer, metric.unit + " / " + metric.reference_period + " / " + metric.evidence_class,
    {0.3,1.4},resources_typography(0.22,{42,40,36}));
  const std::string scale_text = metric.scale == metric_scale::log1p ? "Five equal intervals of log(1 + value)." : "Five equal intervals of value.";
  svg::styled_text(layer, scale_text + " izzi-hue named colours at " + std::to_string(std::lround(resource_metric_opacity(profile, metric)*100)) + "% opacity. Grey: missing, never zero.",
    {0.3,1.85},resources_typography(0.21,{42,40,36}));
  svg::styled_text(layer, "Country statistics; " + std::to_string(metric.coverage->covered_countries)
    + " of " + std::to_string(metric.coverage->mapped_countries)
    + " mapped countries. Source dates and definitions: see the atlas source notes.",
    {0.3,2.25},resources_typography(0.18,{42,40,36}));
  layer.finish_element();document.add_element(layer);
}

inline void
add_resources_spatial_legend(
  generation::projection_document& document,
  const generation::projection_context& context,
  const resources_profile& profile, const resource_family& family,
  const metric_definition& metric)
{
  resources_require(metric.spatial.has_value(),
                    "spatial legend requires spatial metadata");
  const spatial_definition& spatial = *metric.spatial;
  const std::string heading_text
    = resources_xml_escape(family.title + " / " + metric.title);
  const std::string detail_text = resources_xml_escape(
    metric.unit + " · " + metric.reference_period
      + " · " + metric.evidence_class);
  const std::string cells_text = resources_xml_escape(
    std::to_string(spatial.mapped_features) + " mapped 0.25° cells · "
      + std::to_string(spatial.source_polygons)
      + " source reef polygons · gate passed");
  const std::string snapshot_text = resources_xml_escape(
    "Snapshot " + profile.snapshot_as_of
      + " · radial honeycombs, cap " + std::to_string(static_cast<unsigned>(generation_style::coral_display_cell_cap))
      + "; class mix retained · glyphs are not reef area");
  constexpr double column_gap = 0.115;
  constexpr double page_margin = 0.573;
  constexpr double key_column_width = 0.48;
  const double label_x = page_margin + key_column_width + column_gap;
  svg::group_element layer;
  const double width = std::clamp(
    generation::legend_text_width(heading_text, 0.42) + 2 * page_margin,
    5.0,
    context.map_frame.width() - 0.6);
  const double height = 3.65;
  const double left = 0.30;
  const double top = 0.30;
  layer.start_element("resource-legend", "translate("
    + std::to_string(context.map_frame.width() - width - 0.573) + " "
    + std::to_string(context.map_frame.height() - height - 0.573) + ")");
  svg::rect_element panel;
  panel.start_element();
  panel.add_data({left, top + 1.99, width, height - 1.99});
  panel.add_style({{255, 255, 255}, 0.94, svg::color::none, 0, 0});
  panel.add_raw("id=\"resource-legend-panel\"");
  panel.finish_element();
  layer.add_element(panel);

  svg::typography heading = resources_typography(0.42, {42, 40, 36});
  heading._M_w = svg::typography::weight::bold;
  heading._M_anchor = svg::typography::anchor::end;
  heading._M_align = svg::typography::align::right;
  svg::styled_text(layer, heading_text,
    {left + width - page_margin, top + 2.60}, heading);
  svg::typography detail = resources_typography(0.12, {87, 82, 74});
  detail._M_anchor = svg::typography::anchor::end;
  detail._M_align = svg::typography::align::right;
  svg::styled_text(layer, detail_text,
    {left + width - page_margin, top + 2.99}, detail);
  svg::typography other = resources_typography(0.12, {87, 82, 74});
  other._M_anchor = svg::typography::anchor::end;
  other._M_align = svg::typography::align::right;
  svg::styled_text(layer, cells_text,
    {left + width - page_margin, top + 3.23}, other);
  svg::styled_text(layer, snapshot_text,
    {left + width - page_margin, top + 3.47}, other);

  constexpr std::array threat_labels {
    std::string_view {"Low"}, std::string_view {"Medium"},
    std::string_view {"High"}, std::string_view {"Very High"},
  };
  svg::typography labels = resources_typography(0.12, {54, 51, 46});
  for (std::size_t index = 0; index != threat_labels.size(); ++index)
    {
      const double y = top + 0.36 + index * 0.36;
      const double x = left + page_margin;
      svg::rect_element swatch;
      swatch.start_element();
      swatch.add_data({x, y - 0.165, 0.48, 0.33});
      const svg::color_qi threat_color
        = reef_threat_color(static_cast<int>(index + 1));
      const svg::color_qi threat_outline
        = threat_color == svg::color_qi {255, 255, 255}
          ? svg::color::black : svg::color::none;
      swatch.add_style({threat_color, 1, threat_outline,
                        threat_outline == svg::color::none ? 0.0 : 1.0, 0.006});
      swatch.add_raw("data-resource-legend-swatch=\"true\"");
      swatch.finish_element();
      layer.add_element(swatch);
      svg::styled_text(layer, std::string(threat_labels[index]),
                       {left + label_x, y}, labels);
    }
  svg::rect_element absent;
  absent.start_element();
  const double absent_y = top + 0.36 + 4 * 0.36;
  absent.add_data({left + page_margin, absent_y - 0.165, 0.48, 0.33});
  absent.add_style({resource_color(family.palette.missing), 1,
                    {92, 91, 85}, 0.8, 0.008});
  absent.add_raw("data-resource-legend-missing=\"true\"");
  absent.finish_element();
  layer.add_element(absent);
  svg::styled_text(layer, "no mapped reef",
                   {left + label_x, absent_y}, labels);
  layer.finish_element();
  document.add_element(layer);
}

inline void
generate_resources(const generation::projection_spec& spec,
                   const resources_profile& profile,
                   const resource_family& family,
                   const metric_definition& metric)
{
  const std::vector<const country_value*> values
    = resource_metric_values(profile, family, metric);
  resources_require(metric.coverage.has_value() != metric.spatial.has_value(),
                    family.id + "/" + metric.id
                      + " lacks a unique release definition");
  if (metric.coverage.has_value())
    resources_require(!values.empty(), family.id + "/" + metric.id
                                       + " has no country values");
  else
    resources_require(values.empty(), family.id + "/" + metric.id
                                      + " spatial metric has country values");
  const std::string basename = resources_output_basename(spec, family, metric);
  const generation::projection_context context(spec, basename);
  generation::projection_document document(
    basename, std::string(spec.title) + " " + family.title + ": "
      + metric.title + " (Resources Stage 12)",
    context.map_frame.frame_area);
  document.add_raw(resources_metadata_element(
    spec, profile, family, metric, values));
  add_resources_background(document, context);
  natural_earth::initialize_gdal();
  if (metric.coverage.has_value())
    {
      static_cast<void>(add_resource_country_coverage(
        document, context, profile, family, metric, values));
      add_resources_legend(document, context, profile, family, metric, values);
    }
  else
    {
      static_cast<void>(add_resource_spatial_coverage(
        document, context, profile, metric));
      add_resources_spatial_legend(
        document, context, profile, family, metric);
    }
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
  constexpr std::array common_layers {
    std::string_view {"resources-background"},
    std::string_view {"terrestrial-land"},
    std::string_view {"resource-legend"},
  };
  for (const std::string_view layer : common_layers)
    resources_require(generated.find("<g id=\"" + std::string(layer) + "\"")
                        != std::string::npos,
                      "generated resources SVG is missing layer "
                        + std::string(layer));
  if (metric.coverage.has_value())
    {
      constexpr std::array country_layers {
        std::string_view {"resource-country-coverage"},
        std::string_view {"resource-missing-data"},
        std::string_view {"resource-country-values"},
      };
      for (const std::string_view layer : country_layers)
        resources_require(
          generated.find("<g id=\"" + std::string(layer) + "\"")
            != std::string::npos,
          "generated country resources SVG is missing layer "
            + std::string(layer));
      resources_require(generated.find("data-coverage-kind=\"country\"")
                          != std::string::npos,
                        "generated country resources SVG lacks coverage kind");
    }
  else
    {
      resources_require(
        generated.find("<g id=\"resource-spatial-coverage\">")
          != std::string::npos,
        "generated spatial resources SVG lacks its coverage layer");
      resources_require(generated.find("data-coverage-kind=\"spatial\"")
                          != std::string::npos,
                        "generated spatial resources SVG lacks coverage kind");
      resources_require(metric.spatial.has_value()
                          && resources_token_count(
                               generated, "data-resource-spatial=\"true\"")
                               >= metric.spatial->mapped_features,
                        "generated spatial resources SVG is incomplete");
    }
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
                      && generated.find("data-workflow=\"Resources Stage 12\"")
                           != std::string::npos
                      && generated.find("data-family=\"" + family.id + "\"")
                           != std::string::npos
                      && generated.find("data-metric=\"" + metric.id + "\"")
                           != std::string::npos
                      && generated.find("data-passes-non-sparse=\"true\"")
                           != std::string::npos
                      && generated.find("data-missing-is-zero=\"false\"")
                           != std::string::npos,
                    "generated resources SVG lacks Stage 12 metadata");
  resources_require(generated.find("data-title-scale=\"2\"")
                      != std::string::npos,
                    "generated resources SVG lacks title-scale metadata");
  resources_require(generated.find(
                      "data-graphic-opacity=\""
                        + format_resource_number(
                            resource_metric_opacity(profile, metric), 2) + "\"")
                      != std::string::npos,
                    "generated resources SVG lacks data-graphic opacity metadata");
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
  if (argc != 4 && argc != 5)
    throw std::invalid_argument(
      "usage: generate-resources FAMILY PROJECTION PROFILE.json [METRIC]");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[2]);
  const resources_profile profile = load_resources_profile(
    std::filesystem::absolute(argv[3]));
  const resource_family& family = find_resource_family(profile, argv[1]);
  const metric_definition& metric = argc == 5
    ? find_resource_metric(family, argv[4])
    : default_resource_metric(family);
  const std::vector<const country_value*> values
    = resource_metric_values(profile, family, metric);
  const std::string basename = resources_output_basename(spec, family, metric);
  const generation::projection_context context(spec, basename);
  generate_resources(spec, profile, family, metric);
  verify_generated_resources(
    read_generated_resources(basename), context, profile, family, metric, values);
  return 0;
}

} // namespace cart0freak0::resources_generation

#endif // CART0FREAK0_RESOURCES_GENERATION_H

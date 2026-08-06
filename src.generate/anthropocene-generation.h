// Projection-aware, source-separated Anthropocene SVG generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ANTHROPOCENE_GENERATION_H
#define CART0FREAK0_ANTHROPOCENE_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <map>
#include <numbers>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "anthropocene-data.h"
#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"

namespace cart0freak0::anthropocene_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

inline std::string
xml_escape(std::string value)
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
format_number(const double value, const int precision = 6)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  return output.str();
}

inline svg::color_qi
svg_color(const rgb_color color)
{ return {color.red, color.green, color.blue}; }

inline std::string
layer_id(std::string value)
{
  std::replace(value.begin(), value.end(), '_', '-');
  std::replace(value.begin(), value.end(), ':', '-');
  return value;
}

inline std::string
shape_name(const marker_shape shape)
{
  switch (shape)
    {
    case marker_shape::triangle_up: return "triangle-up";
    case marker_shape::triangle_down: return "triangle-down";
    case marker_shape::diamond: return "diamond";
    case marker_shape::circle: return "circle";
    case marker_shape::hexagon: return "hexagon";
    case marker_shape::ring: return "ring";
    case marker_shape::square: return "square";
    case marker_shape::star: return "star";
    case marker_shape::cross_square: return "cross-square";
    }
  throw std::logic_error("unhandled Anthropocene marker shape");
}

inline std::string
polygon_path(const svg::point_2t origin, const double outer_radius,
             const unsigned points, const double rotation_degrees,
             const double inner_fraction = 1)
{
  svg::vrange vertices;
  const unsigned vertex_count = inner_fraction == 1 ? points : points * 2;
  vertices.reserve(vertex_count + 1);
  for (unsigned index = 0; index < vertex_count; ++index)
    {
      const double angle = (rotation_degrees
        + 360.0 * index / vertex_count) * std::numbers::pi / 180.0;
      const double radius = inner_fraction != 1 && index % 2 != 0
        ? outer_radius * inner_fraction : outer_radius;
      vertices.emplace_back(std::get<0>(origin) + std::cos(angle) * radius,
                            std::get<1>(origin) + std::sin(angle) * radius);
    }
  vertices.push_back(vertices.front());
  return svg::make_path_data_from_points(vertices);
}

inline void
add_path(svg::group_element& layer, const std::string& path_data,
         const svg::style& style, const std::string& attributes = {})
{
  layer.add_element(svg::make_path(
    path_data, style, "", true, attributes));
}

inline void
add_circle(svg::group_element& layer, const svg::point_2t origin,
           const svg::style& style, const double radius,
           const std::string& attributes = {})
{
  svg::circle_element circle;
  circle.start_element();
  circle.add_data({std::get<0>(origin), std::get<1>(origin), radius});
  circle.add_style(style);
  if (!attributes.empty())
    circle.add_raw(attributes);
  circle.finish_element();
  layer.add_element(circle);
}

inline void
add_line(svg::group_element& layer, const svg::point_2t start,
         const svg::point_2t finish, const svg::style& style)
{
  svg::line_element line;
  line.start_element();
  line.add_data({std::get<0>(start), std::get<0>(finish),
                 std::get<1>(start), std::get<1>(finish)});
  line.add_style(style);
  line.finish_element();
  layer.add_element(line);
}

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("anthropocene-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{246, 242, 232}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"anthropocene-ground\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_subdued_land(generation::projection_document& document,
                 const generation::projection_context& context)
{
  const natural_earth::layer_spec land {
    "terrestrial-land", "Subdued Natural Earth 1:10m land",
    "ne_10m_land.shp", natural_earth::geometry_role::area,
    natural_earth::area_style({218, 213, 201}), 0.05, 0.82,
  };
  svg::group_element layer;
  layer.start_element(std::string(land.id));
  layer.add_title(std::string(land.title));
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::antarctic_cap cap
        = natural_earth::make_antarctic_cap(context, land);
      static_cast<void>(natural_earth::render_star_x_source(
        layer, land, context, cap));
    }
  else
    static_cast<void>(natural_earth::render_source(layer, land, context));
  layer.finish_element();
  document.add_element(layer);
}

struct projected_dataset
{
  std::vector<svg::point_2t> points;
};

inline projected_dataset
project_dataset(const generation::projection_context& context,
                const anthropocene_dataset& dataset)
{
  projected_dataset result;
  result.points.reserve(dataset.features.size());
  for (const anthropocene_feature& feature : dataset.features)
    result.points.push_back(generation::project_point(
      context, {feature.latitude, feature.longitude}));
  return result;
}

inline double
scaled_opacity(const std::uint64_t count, const metric_definition& metric,
               const anthropocene_profile& profile)
{
  if (count == 0)
    return 0;
  const double fraction = std::min(
    1.0, std::log1p(static_cast<double>(count))
      / std::log1p(static_cast<double>(metric.scale_days)));
  return profile.minimum_nonzero_opacity
    + (1 - profile.minimum_nonzero_opacity) * fraction;
}

inline std::string
marker_attributes(const anthropocene_feature& feature,
                  const metric_definition& metric,
                  const std::uint64_t count)
{
  return "data-anthropocene-observation=\"true\" data-h3=\""
    + h3_string(feature.h3) + "\" data-metric-id=\""
    + xml_escape(metric.id) + "\" data-property=\""
    + xml_escape(metric.property) + "\" data-family=\""
    + xml_escape(metric.family) + "\" data-shape=\""
    + shape_name(metric.shape) + "\" data-day-count=\""
    + std::to_string(count) + "\"";
}

inline void
add_marker(svg::group_element& layer, const svg::point_2t point,
           const metric_definition& metric, const anthropocene_profile& profile,
           const anthropocene_feature& feature, const std::uint64_t count)
{
  const double opacity = scaled_opacity(count, metric, profile);
  const double radius = profile.marker_radius * (0.62 + 0.38 * opacity);
  const svg::color_qi color = svg_color(metric.color);
  const svg::style filled {
    color, 0.12 + 0.62 * opacity, color, opacity,
    0.0025 + 0.0045 * opacity,
  };
  const svg::style outlined {
    svg::color::none, 0, color, opacity,
    0.003 + 0.006 * opacity,
  };
  const std::string attributes = marker_attributes(feature, metric, count);
  switch (metric.shape)
    {
    case marker_shape::triangle_up:
      add_path(layer, polygon_path(point, radius, 3, -90), filled, attributes);
      break;
    case marker_shape::triangle_down:
      add_path(layer, polygon_path(point, radius, 3, 90), filled, attributes);
      break;
    case marker_shape::diamond:
      add_path(layer, polygon_path(point, radius, 4, 0), filled, attributes);
      break;
    case marker_shape::circle:
      add_circle(layer, point, filled, radius * 0.82, attributes);
      break;
    case marker_shape::hexagon:
      add_path(layer, polygon_path(point, radius, 6, 0), filled, attributes);
      break;
    case marker_shape::ring:
      add_circle(layer, point, outlined, radius * 0.88, attributes);
      break;
    case marker_shape::square:
      add_path(layer, polygon_path(point, radius, 4, 45), filled, attributes);
      break;
    case marker_shape::star:
      add_path(layer, polygon_path(point, radius, 5, -90, 0.42),
               filled, attributes);
      break;
    case marker_shape::cross_square:
      {
        add_path(layer, polygon_path(point, radius, 4, 45),
                 outlined, attributes);
        const double delta = radius * 0.55;
        const svg::style cross_style {
          svg::color::none, 0, color, opacity,
          0.003 + 0.005 * opacity,
        };
        add_line(layer,
                 {std::get<0>(point) - delta, std::get<1>(point)},
                 {std::get<0>(point) + delta, std::get<1>(point)},
                 cross_style);
        add_line(layer,
                 {std::get<0>(point), std::get<1>(point) - delta},
                 {std::get<0>(point), std::get<1>(point) + delta},
                 cross_style);
        break;
      }
    }
}

inline svg::group_element
metric_layer(const anthropocene_profile& profile,
             const anthropocene_dataset& dataset,
             const projected_dataset& projected, const std::size_t metric_index)
{
  const metric_definition& metric = profile.metrics[metric_index];
  svg::group_element layer;
  layer.start_element(layer_id(metric.property));
  layer.add_title(metric.title);
  for (std::size_t feature_index = 0;
       feature_index < dataset.features.size(); ++feature_index)
    {
      const anthropocene_feature& feature = dataset.features[feature_index];
      const std::uint64_t count = feature.counts[metric_index];
      if (count != 0)
        add_marker(layer, projected.points[feature_index], metric, profile,
                   feature, count);
    }
  layer.finish_element();
  return layer;
}

inline void
add_metric_layers(generation::projection_document& document,
                  const anthropocene_profile& profile,
                  const anthropocene_dataset& dataset,
                  const projected_dataset& projected)
{
  constexpr std::array family_order {
    std::string_view {"atmosphere"}, std::string_view {"fire"},
    std::string_view {"hydrology"}, std::string_view {"severe-weather"},
    std::string_view {"air-quality-exposure"},
    std::string_view {"climate-records"},
  };
  for (const std::string_view family : family_order)
    {
      svg::group_element group;
      group.start_element(std::string(family));
      bool populated = false;
      for (std::size_t index = 0; index < profile.metrics.size(); ++index)
        if (profile.metrics[index].enabled
            && profile.metrics[index].family == family)
          {
            group.add_element(metric_layer(profile, dataset, projected, index));
            populated = true;
          }
      group.finish_element();
      if (populated)
        document.add_element(group);
    }
}

inline svg::typography
label_typography(const double size = 0.11,
                 const svg::color_qi color = {58, 56, 51})
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 0.94, {249, 247, 240}, 0.88, 0.006};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline std::string
short_metric_title(const metric_definition& metric)
{
  constexpr std::array replacements {
    std::pair {std::string_view {"New daily maximum-temperature record days"},
               std::string_view {"record highs"}},
    std::pair {std::string_view {"New daily minimum-temperature record days"},
               std::string_view {"record lows"}},
    std::pair {std::string_view {"New daily precipitation-record days"},
               std::string_view {"precipitation records"}},
    std::pair {std::string_view {"Heavy-precipitation days above the 1991-2020 wet-day p95"},
               std::string_view {"heavy precipitation"}},
    std::pair {std::string_view {"Satellite active-fire detection days"},
               std::string_view {"active fire"}},
    std::pair {std::string_view {"Analyst-observed smoke plume days"},
               std::string_view {"observed smoke"}},
    std::pair {std::string_view {"Reported flood or heavy-rain event days"},
               std::string_view {"flood / heavy rain"}},
    std::pair {std::string_view {"Reported severe-weather event days"},
               std::string_view {"severe weather"}},
    std::pair {std::string_view {"EPA PM2.5 AQI exceedance days (AQI > 100)"},
               std::string_view {"EPA PM2.5 > 100 AQI"}},
  };
  for (const auto& [long_title, short_title] : replacements)
    if (metric.title == long_title)
      return std::string(short_title);
  return metric.title;
}

inline void
add_legend_marker(svg::group_element& layer, const svg::point_2t point,
                  const metric_definition& metric)
{
  constexpr double radius = 0.038;
  const svg::color_qi color = svg_color(metric.color);
  const svg::style filled {color, 0.72, color, 1, 0.004};
  const svg::style outlined {svg::color::none, 0, color, 1, 0.008};
  switch (metric.shape)
    {
    case marker_shape::triangle_up:
      add_path(layer, polygon_path(point, radius, 3, -90), filled);
      break;
    case marker_shape::triangle_down:
      add_path(layer, polygon_path(point, radius, 3, 90), filled);
      break;
    case marker_shape::diamond:
      add_path(layer, polygon_path(point, radius, 4, 0), filled);
      break;
    case marker_shape::circle:
      add_circle(layer, point, filled, radius * 0.82);
      break;
    case marker_shape::hexagon:
      add_path(layer, polygon_path(point, radius, 6, 0), filled);
      break;
    case marker_shape::ring:
      add_circle(layer, point, outlined, radius * 0.88);
      break;
    case marker_shape::square:
      add_path(layer, polygon_path(point, radius, 4, 45), filled);
      break;
    case marker_shape::star:
      add_path(layer, polygon_path(point, radius, 5, -90, 0.42), filled);
      break;
    case marker_shape::cross_square:
      {
        add_path(layer, polygon_path(point, radius, 4, 45), outlined);
        constexpr double delta = radius * 0.55;
        add_line(layer,
                 {std::get<0>(point) - delta, std::get<1>(point)},
                 {std::get<0>(point) + delta, std::get<1>(point)}, outlined);
        add_line(layer,
                 {std::get<0>(point), std::get<1>(point) - delta},
                 {std::get<0>(point), std::get<1>(point) + delta}, outlined);
        break;
      }
    }
}

inline void
add_legend(generation::projection_document& document,
           const generation::projection_context& context,
           const anthropocene_profile& profile,
           const anthropocene_dataset& dataset)
{
  if (!profile.show_legend)
    return;
  svg::group_element layer;
  layer.start_element("legend-and-provenance");
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, context.map_frame.width(), 1.02});
  band.add_style({{249, 247, 240}, 0.94, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);

  svg::typography title = label_typography(0.21, {42, 40, 36});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer, "ANTHROPOCENE / "
    + std::to_string(profile.calendar_year)
    + (profile.partial_year ? " PARTIAL YEAR" : ""), {0.30, 0.20}, title);
  svg::styled_text(layer,
    xml_escape(profile.snapshot_as_of_utc + "  |  "
      + std::to_string(dataset.features.size()) + " H3 r"
      + std::to_string(profile.h3_resolution)
      + " cells  |  absent is unobserved, not zero"),
    {0.30, 0.41}, label_typography(0.105, {87, 82, 74}));

  std::vector<std::size_t> enabled;
  for (std::size_t index = 0; index < profile.metrics.size(); ++index)
    if (profile.metrics[index].enabled)
      enabled.push_back(index);
  const std::size_t columns = 5;
  const double usable_width = context.map_frame.width() - 0.6;
  const double column_width = usable_width / columns;
  for (std::size_t position = 0; position < enabled.size(); ++position)
    {
      const std::size_t index = enabled[position];
      const std::size_t row = position / columns;
      const std::size_t column = position % columns;
      const double x = 0.34 + column * column_width;
      const double y = 0.64 + row * 0.22;
      const metric_definition& metric = profile.metrics[index];
      const svg::point_2t marker_point {x, y};
      add_legend_marker(layer, marker_point, metric);
      svg::styled_text(layer, xml_escape(short_metric_title(metric)),
                       {x + 0.08, y}, label_typography(0.102, {54, 51, 46}));
    }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_coverage_note(generation::projection_document& document,
                  const generation::projection_context& context,
                  const anthropocene_profile& profile)
{
  svg::group_element layer;
  layer.start_element("coverage-note");
  const double y = context.map_frame.height() - 0.18;
  svg::typography text = label_typography(0.095, {73, 69, 63});
  text._M_anchor = svg::typography::anchor::middle;
  text._M_align = svg::typography::align::center;
  svg::styled_text(layer,
    "Distinct observations, not a climate-attribution score. "
    "EPA PM2.5 exposure is separate from observed smoke; coral bleaching is deferred.",
    {context.map_frame.width() / 2, y}, text);
  static_cast<void>(profile);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
metadata_element(const generation::projection_spec& spec,
                 const anthropocene_profile& profile,
                 const anthropocene_dataset& dataset)
{
  std::string result = "<metadata id=\"anthropocene-metadata\""
    " data-workflow=\"Anthropocene source-separated observations\""
    " data-profile=\"" + xml_escape(profile.path.filename().string()) + "\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-calendar-year=\"" + std::to_string(profile.calendar_year) + "\""
    " data-snapshot-as-of-utc=\"" + xml_escape(profile.snapshot_as_of_utc) + "\""
    " data-partial-year=\"" + std::string(profile.partial_year ? "true" : "false") + "\""
    " data-h3-resolution=\"" + std::to_string(profile.h3_resolution) + "\""
    " data-feature-count=\"" + std::to_string(dataset.features.size()) + "\""
    " data-geojson-sha256=\"" + profile.geojson_sha256 + "\""
    " data-pm25-smoke-separation=\"true\""
    " data-coral-bleaching-phase=\"separate\"";
  for (std::size_t index = 0; index < profile.metrics.size(); ++index)
    result += " data-total-" + layer_id(profile.metrics[index].property)
      + "=\"" + std::to_string(dataset.reported_metric_totals[index]) + "\"";
  return result + "></metadata>\n";
}

inline std::string
output_basename(const generation::projection_spec& spec)
{ return generation::output_basename("anthropocene", spec); }

inline void
generate(const generation::projection_spec& spec,
         const anthropocene_profile& profile,
         const anthropocene_dataset& dataset)
{
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  const projected_dataset projected = project_dataset(context, dataset);
  generation::projection_document document(
    basename, std::string(spec.title) + " Anthropocene observation atlas for "
      + std::to_string(profile.calendar_year), context.map_frame.frame_area);
  document.add_raw(metadata_element(spec, profile, dataset));
  add_background(document, context);
  natural_earth::initialize_gdal();
  add_subdued_land(document, context);
  add_metric_layers(document, profile, dataset, projected);
  add_legend(document, context, profile, dataset);
  add_coverage_note(document, context, profile);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  anthropocene_require(input.good(), "failed to open generated " + basename
                                      + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline std::size_t
token_count(const std::string_view text, const std::string_view token)
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
verify(const std::string& generated,
       const generation::projection_context& context,
       const anthropocene_profile& profile,
       const anthropocene_dataset& dataset)
{
  anthropocene_require(generated.find(generation::view_box_fragment(context))
                         != std::string::npos,
                       "generated Anthropocene SVG has the wrong viewBox");
  constexpr std::array required_layers {
    std::string_view {"anthropocene-background"},
    std::string_view {"terrestrial-land"},
    std::string_view {"atmosphere"}, std::string_view {"fire"},
    std::string_view {"hydrology"}, std::string_view {"severe-weather"},
    std::string_view {"air-quality-exposure"},
    std::string_view {"climate-records"},
    std::string_view {"legend-and-provenance"},
    std::string_view {"coverage-note"},
  };
  for (const std::string_view layer : required_layers)
    anthropocene_require(generated.find("<g id=\"" + std::string(layer) + "\">")
                           != std::string::npos,
                         "generated Anthropocene SVG is missing layer "
                           + std::string(layer));
  std::size_t expected_observations = 0;
  for (std::size_t index = 0; index < profile.metrics.size(); ++index)
    if (profile.metrics[index].enabled)
      {
        anthropocene_require(generated.find("<g id=\""
          + layer_id(profile.metrics[index].property) + "\">")
          != std::string::npos,
          "generated Anthropocene SVG is missing metric layer "
            + profile.metrics[index].id);
        expected_observations += static_cast<std::size_t>(
          dataset.reported_metric_feature_counts[index]);
      }
  anthropocene_require(token_count(
    generated, "data-anthropocene-observation=\"true\"")
      == expected_observations,
    "generated Anthropocene SVG has the wrong observation-marker count");
  anthropocene_require(generated.find("id=\"anthropocene-metadata\"")
                         != std::string::npos
                         && generated.find("data-geojson-sha256=\""
                           + profile.geojson_sha256 + "\"")
                              != std::string::npos
                         && generated.find("data-pm25-smoke-separation=\"true\"")
                              != std::string::npos,
                       "generated Anthropocene SVG lacks provenance metadata");
  anthropocene_require(generated.find("<g id=\"pm25-exceedance-days\">")
                         != std::string::npos
                         && generated.find("<g id=\"observed-smoke-days\">")
                              != std::string::npos
                         && generated.find("data-shape=\"cross-square\"")
                              != std::string::npos
                         && generated.find("data-shape=\"ring\"")
                              != std::string::npos,
                       "PM2.5 exposure and observed smoke are not distinct");
  anthropocene_require(generated.find(
    "<g id=\"coral-bleaching-stress-days\">") == std::string::npos,
    "deferred coral bleaching was rendered as a Stage 8 metric");
  anthropocene_require(generated.find(" nan") == std::string::npos
                         && generated.find(" -nan") == std::string::npos
                         && generated.find(" inf") == std::string::npos
                         && generated.find(" -inf") == std::string::npos,
                       "generated Anthropocene SVG has non-finite data");
  generation::verify_configured_label_font(generated, "Anthropocene SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-anthropocene PROJECTION PROFILE.json INPUT.geojson");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const anthropocene_profile profile = load_anthropocene_profile(
    std::filesystem::absolute(argv[2]));
  const anthropocene_dataset dataset = load_anthropocene_dataset(
    std::filesystem::absolute(argv[3]), profile);
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate(spec, profile, dataset);
  verify(read_generated(basename), context, profile, dataset);
  return 0;
}

} // namespace cart0freak0::anthropocene_generation

#endif // CART0FREAK0_ANTHROPOCENE_GENERATION_H

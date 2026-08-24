// Projection-aware cumulative network swarm SVG generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_SWARM_GENERATION_H
#define CART0FREAK0_NETWORK_SWARM_GENERATION_H 1

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
#include <set>
#include <sstream>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <izzi-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "network-swarm-clustering.h"
#include "network-swarm-data.h"
#include "projection-generation-common.h"

namespace cart0freak0::network_swarm_generation {

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
interpolate_color(const svg::color_qi low, const svg::color_qi high,
                  const double fraction)
{
  const auto channel = [fraction](const unsigned short left,
                                  const unsigned short right) {
    return static_cast<unsigned short>(std::lround(
      left + fraction * (static_cast<double>(right) - left)));
  };
  return {channel(low.r, high.r), channel(low.g, high.g),
          channel(low.b, high.b)};
}

inline std::string
polygon_path(const svg::point_2t origin, const double radius,
             const unsigned points)
{
  const double angle = 360.0 / points;
  const double zero = svg::zero_angle_north_cw(angle);
  svg::vrange vertices;
  vertices.reserve(points + 1);
  for (unsigned index = 0; index < points; ++index)
    vertices.push_back(svg::get_circumference_point_d(
      zero + angle * index, radius, origin));
  vertices.push_back(vertices.front());
  return svg::make_path_data_from_points(vertices);
}

inline void
add_polygon(svg::group_element& layer, const svg::point_2t origin,
            const svg::style& style, const double radius,
            const unsigned points, const std::string& attributes = {})
{
  layer.add_element(svg::make_path(
    polygon_path(origin, radius, points), style, "", true, attributes));
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
         const svg::point_2t finish, const svg::style& style,
         const std::string& attributes = {})
{
  svg::line_element line;
  line.start_element();
  line.add_data({std::get<0>(start), std::get<0>(finish),
                 std::get<1>(start), std::get<1>(finish)});
  line.add_style(style);
  if (!attributes.empty())
    line.add_raw(attributes);
  line.finish_element();
  layer.add_element(line);
}

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("network-swarm-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{242, 244, 243}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"network-swarm-ocean\"");
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
    natural_earth::area_style({216, 221, 219}), 0.05, 0.82,
  };
  svg::group_element layer;
  layer.start_element(std::string(land.id));
  layer.add_title(std::string(land.title));
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::antarctic_cap cap
        = natural_earth::make_antarctic_cap(context);
      static_cast<void>(natural_earth::render_star_x_source(
        layer, land, context, cap));
    }
  else
    static_cast<void>(natural_earth::render_source(layer, land, context));
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
feature_attributes(const projected_feature& projected)
{
  const swarm_feature& feature = *projected.source;
  std::string result = "data-network-swarm-feature=\"true\" data-h3=\""
    + h3_string(feature.h3) + "\" data-h3-uint64=\""
    + std::to_string(feature.h3) + "\" data-parent-h3=\""
    + h3_string(projected.parent) + "\" data-projection-cell=\""
    + std::to_string(projected.projection_cell) + "\" data-cluster-size=\""
    + std::to_string(projected.cluster_size) + "\" data-country-code=\""
    + xml_escape(feature.country_code) + "\" data-city=\""
    + xml_escape(feature.city) + "\" data-geoname-id=\""
    + xml_escape(feature.geoname_id) + "\"";
  for (const metric_descriptor descriptor : metric_descriptors)
    result += " data-downloaders-" + std::string(descriptor.field)
      + "=\"" + std::to_string(metric_value(feature.downloaders,
                                               descriptor.metric)) + "\"";
  return result;
}

inline std::string
value_attribute(const projected_feature& feature,
                const downloader_metric metric)
{
  return "data-h3=\"" + h3_string(feature.source->h3)
    + "\" data-value=\""
    + std::to_string(metric_value(feature.source->downloaders, metric)) + "\"";
}

inline double
metric_opacity(const projected_feature& feature,
               const network_swarm_profile& config,
               const downloader_metric metric)
{
  return scaled_log_opacity(
    metric_value(feature.source->downloaders, metric),
    metric_value(config.scale_reference, metric),
    config.minimum_nonzero_opacity);
}

inline void
add_tethers(generation::projection_document& document,
            const projected_layout& layout, const network_swarm_profile& config)
{
  svg::group_element layer;
  layer.start_element("cluster-tethers");
  if (config.show_tethers)
    for (const projected_feature& feature : layout.features)
      if (generation::point_distance(feature.geographic_point,
                                     feature.display_point)
          >= config.minimum_tether)
        add_line(layer, feature.geographic_point, feature.display_point,
                 {{52, 77, 159}, 0, {52, 77, 159}, 0.42, 0.006},
                 "data-h3=\"" + h3_string(feature.source->h3) + "\"");
  layer.finish_element();
  document.add_element(layer);
}

inline svg::group_element
total_layer(const projected_layout& layout, const network_swarm_profile& config)
{
  svg::group_element layer;
  layer.start_element("downloaders-total");
  for (const projected_feature& feature : layout.features)
    {
      add_polygon(layer, feature.display_point,
                  {svg::color::purple, 0.20,
                   svg::color::none, 0, 0},
                  config.marker_radius * 0.94, 6,
                  feature_attributes(feature));
    }
  layer.finish_element();
  return layer;
}

inline svg::group_element
mobile_layer(const projected_layout& layout, const network_swarm_profile& config)
{
  svg::group_element layer;
  layer.start_element("downloaders-mobile");
  for (const projected_feature& feature : layout.features)
    if (feature.source->downloaders.mobile != 0)
      {
        const double opacity = metric_opacity(
          feature, config, downloader_metric::mobile);
        add_circle(layer, feature.display_point,
                   {svg::color::blue, 0.50 + 0.50 * opacity,
                    svg::color::blue, 0, 0},
                   config.marker_radius * (0.24 + 0.26 * opacity),
                   value_attribute(feature, downloader_metric::mobile));
      }
  layer.finish_element();
  return layer;
}

inline svg::group_element
satellite_layer(const projected_layout& layout,
                const network_swarm_profile& config)
{
  svg::group_element layer;
  layer.start_element("downloaders-satellite");
  for (const projected_feature& feature : layout.features)
    if (feature.source->downloaders.satellite != 0)
      {
        const double opacity = metric_opacity(
          feature, config, downloader_metric::satellite);
        add_polygon(layer, feature.display_point,
                    {svg::color::blue, 0.60 + 0.40 * opacity,
                     svg::color::blue, 0, 0},
                    config.marker_radius * (0.36 + 0.30 * opacity), 3,
                    value_attribute(feature, downloader_metric::satellite));
      }
  layer.finish_element();
  return layer;
}

inline svg::group_element
outline_layer(const projected_layout& layout, const network_swarm_profile& config,
              const downloader_metric metric, const std::string_view id,
              const svg::color_qi color, const unsigned sides,
              const double radius_fraction)
{
  svg::group_element layer;
  layer.start_element(std::string(id));
  for (const projected_feature& feature : layout.features)
    if (metric_value(feature.source->downloaders, metric) != 0)
      {
        const double opacity = metric_opacity(feature, config, metric);
        add_polygon(layer, feature.display_point,
                    {svg::color::none, 0, color, 0.70 + 0.30 * opacity,
                     0.005 + 0.009 * opacity},
                    config.marker_radius * radius_fraction, sides,
                    value_attribute(feature, metric));
      }
  layer.finish_element();
  return layer;
}

inline svg::group_element
ring_layer(const projected_layout& layout, const network_swarm_profile& config,
           const downloader_metric metric, const std::string_view id,
           const svg::color_qi color, const double radius_fraction)
{
  svg::group_element layer;
  layer.start_element(std::string(id));
  for (const projected_feature& feature : layout.features)
    if (metric_value(feature.source->downloaders, metric) != 0)
      {
        const double opacity = metric_opacity(feature, config, metric);
        add_circle(layer, feature.display_point,
                   {svg::color::none, 0, color, 0.70 + 0.30 * opacity,
                    0.005 + 0.009 * opacity},
                   config.marker_radius * radius_fraction,
                   value_attribute(feature, metric));
      }
  layer.finish_element();
  return layer;
}

inline svg::group_element
corner_layer(const projected_layout& layout, const network_swarm_profile& config,
             const downloader_metric metric, const std::string_view id,
             const svg::color_qi color, const double x_sign,
             const double y_sign, const unsigned sides)
{
  svg::group_element layer;
  layer.start_element(std::string(id));
  for (const projected_feature& feature : layout.features)
    if (metric_value(feature.source->downloaders, metric) != 0)
      {
        const double opacity = metric_opacity(feature, config, metric);
        const svg::point_2t point {
          std::get<0>(feature.display_point)
            + x_sign * config.marker_radius * 0.34,
          std::get<1>(feature.display_point)
            + y_sign * config.marker_radius * 0.34,
        };
        add_polygon(layer, point,
                    {color, 0.70 + 0.30 * opacity,
                     color, 0.72 + 0.28 * opacity, 0.003},
                    config.marker_radius * 0.19, sides,
                    value_attribute(feature, metric));
      }
  layer.finish_element();
  return layer;
}

inline svg::group_element
slash_layer(const projected_layout& layout, const network_swarm_profile& config,
            const downloader_metric metric, const std::string_view id,
            const svg::color_qi color, const bool crossed)
{
  svg::group_element layer;
  layer.start_element(std::string(id));
  for (const projected_feature& feature : layout.features)
    if (metric_value(feature.source->downloaders, metric) != 0)
      {
        const double opacity = metric_opacity(feature, config, metric);
        const double delta = config.marker_radius * 0.42;
        const double x = std::get<0>(feature.display_point);
        const double y = std::get<1>(feature.display_point);
        const svg::style style {
          svg::color::none, 0, color, 0.70 + 0.30 * opacity,
          0.005 + 0.009 * opacity,
        };
        add_line(layer, {x - delta, y + delta}, {x + delta, y - delta},
                 style, value_attribute(feature, metric));
        if (crossed)
          add_line(layer, {x - delta, y - delta}, {x + delta, y + delta},
                   style, value_attribute(feature, metric));
      }
  layer.finish_element();
  return layer;
}

inline void
add_downloader_layers(generation::projection_document& document,
                      const projected_layout& layout,
                      const network_swarm_profile& config)
{
  document.add_element(total_layer(layout, config));

  svg::group_element access;
  access.start_element("access");
  access.add_element(mobile_layer(layout, config));
  access.add_element(satellite_layer(layout, config));
  access.finish_element();
  document.add_element(access);

  svg::group_element infrastructure;
  infrastructure.start_element("infrastructure");
  infrastructure.add_element(outline_layer(
    layout, config, downloader_metric::hosting, "downloaders-hosting",
    svg::color::blue, 6, 0.86));
  infrastructure.add_element(ring_layer(
    layout, config, downloader_metric::service, "downloaders-service",
    svg::color::blue, 0.66));
  infrastructure.finish_element();
  document.add_element(infrastructure);

  svg::group_element privacy;
  privacy.start_element("privacy-routing");
  privacy.add_element(outline_layer(
    layout, config, downloader_metric::vpn, "downloaders-vpn",
    svg::color::blue, 4, 0.5));
  privacy.add_element(corner_layer(
    layout, config, downloader_metric::tor, "downloaders-tor",
    svg::color::blue, -1, -1, 6));
  privacy.add_element(corner_layer(
    layout, config, downloader_metric::tor_exit_nodes,
    "downloaders-tor-exit-nodes", svg::color::blue, 1, -1, 4));
  privacy.add_element(slash_layer(
    layout, config, downloader_metric::relay, "downloaders-relay",
    svg::color::blue, false));
  privacy.add_element(slash_layer(
    layout, config, downloader_metric::proxy, "downloaders-proxy",
    svg::color::blue, true));
  privacy.finish_element();
  document.add_element(privacy);
}

inline svg::typography
label_typography(const double size = 0.13,
                 const svg::color_qi color = {37, 48, 51})
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 1, {250, 251, 250}, 0.94, 0.012};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline void
add_labels(generation::projection_document& document,
           const generation::projection_context& context,
           const projected_layout& layout, const network_swarm_profile& config)
{
  std::vector<const projected_feature*> ranked;
  ranked.reserve(layout.features.size());
  for (const projected_feature& feature : layout.features)
    ranked.push_back(&feature);
  std::sort(ranked.begin(), ranked.end(), [](const auto left,
                                              const auto right) {
    if (left->source->downloaders.size
        != right->source->downloaders.size)
      return left->source->downloaders.size
        > right->source->downloaders.size;
    return left->source->h3 < right->source->h3;
  });

  svg::group_element layer;
  layer.start_element("labels");
  std::set<std::pair<int, int>> occupied;
  std::size_t count = 0;
  for (const projected_feature* feature : ranked)
    {
      if (count >= config.maximum_labels)
        break;
      const double x = std::get<0>(feature->display_point);
      const double y = std::get<1>(feature->display_point);
      if (y < 0.95 || y > context.map_frame.height() - 0.2)
        continue;
      const std::pair grid {
        static_cast<int>(std::floor(x / 0.8)),
        static_cast<int>(std::floor(y / 0.28)),
      };
      if (!occupied.insert(grid).second)
        continue;
      const bool place_left = x > context.map_frame.width() - 2.2;
      svg::typography typography = label_typography();
      typography._M_anchor = place_left ? svg::typography::anchor::end
                                        : svg::typography::anchor::start;
      typography._M_align = place_left ? svg::typography::align::right
                                       : svg::typography::align::left;
      const double label_x = x + (place_left ? -1 : 1)
        * (config.marker_radius + 0.035);
      std::string label = feature->source->city;
      if (!feature->source->country_code.empty())
        label += " / " + feature->source->country_code;
      svg::styled_text(layer, xml_escape(label), {label_x, y}, typography);
      ++count;
    }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_legend(generation::projection_document& document,
           const generation::projection_context& context,
           const swarm_dataset& dataset, const network_swarm_profile& config)
{
  constexpr double panel_width = 20.0;
  constexpr double panel_height = 0.82;
  svg::group_element layer;
  layer.start_element("legend-and-provenance",
    generation::bottom_right_legend_transform(
      context, panel_width, panel_height));
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, panel_width, panel_height});
  band.add_style({{226, 230, 228}, 0.96, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);

  svg::typography title = label_typography(0.44, {0, 0, 205});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer, xml_escape("NETWORK SWARM / " + dataset.id),
                   {0.32, 0.27}, title);
  svg::styled_text(layer,
    xml_escape(dataset.datestamp + "  |  "
      + std::to_string(dataset.features.size()) + " H3 cells  |  parent r"
      + std::to_string(config.parent_h3_resolution) + " honeycomb"),
    {0.32, 0.62}, label_typography(0.115, {55, 67, 72}));
  const std::string fields
    = "size  mobile  satellite  hosting  service  vpn  tor  tor_exit_nodes  relay  proxy";
  svg::typography field_typography = label_typography(0.105, {70, 83, 85});
  field_typography._M_anchor = svg::typography::anchor::end;
  field_typography._M_align = svg::typography::align::right;
  svg::styled_text(layer, fields,
                   {panel_width - 0.32, 0.62},
                   field_typography);
  layer.finish_element();
  document.add_element(layer);
}

inline std::uint64_t
total_downloaders(const swarm_dataset& dataset)
{
  std::uint64_t result = 0;
  for (const swarm_feature& feature : dataset.features)
    {
      network_swarm_require(std::numeric_limits<std::uint64_t>::max() - result
                        >= feature.downloaders.size,
                      "downloaders.size total overflowed uint64");
      result += feature.downloaders.size;
    }
  return result;
}

inline std::string
metadata_element(const generation::projection_spec& spec,
                 const network_swarm_profile& config,
                 const swarm_dataset& dataset,
                 const projected_layout& layout)
{
  return "<metadata id=\"network-swarm-metadata\""
    " data-workflow=\"Network cumulative swarm\""
    " data-profile=\"" + xml_escape(config.path.filename().string()) + "\""
    " data-marker-radius-inches=\"" + format_number(config.marker_radius, 3)
      + "\" data-background-color=\"#f2f4f3\" data-title-scale=\"2\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-dataset-id=\"" + xml_escape(dataset.id) + "\""
    " data-datestamp=\"" + xml_escape(dataset.datestamp) + "\""
    " data-duration-type=\"" + xml_escape(dataset.duration_type) + "\""
    " data-duration-index=\"" + std::to_string(dataset.duration_index) + "\""
    " data-version=\"" + xml_escape(dataset.data_version) + "\""
    " data-source-h3-resolution=\""
      + std::to_string(dataset.h3_resolution) + "\""
    " data-parent-h3-resolution=\""
      + std::to_string(config.parent_h3_resolution) + "\""
    " data-feature-count=\"" + std::to_string(dataset.features.size()) + "\""
    " data-cluster-count=\"" + std::to_string(layout.cluster_count) + "\""
    " data-largest-cluster=\"" + std::to_string(layout.largest_cluster) + "\""
    " data-downloaders-size-total=\""
      + std::to_string(total_downloaders(dataset)) + "\""
    " data-reported-swarm-features-size=\""
      + std::to_string(dataset.reported_swarm_features_size) + "\""
    " data-btiha-size=\"" + std::to_string(dataset.btiha_size) + "\""
    " data-source-archive=\"" + xml_escape(config.archive) + "\""
    " data-source-archive-sha256=\""
      + xml_escape(config.archive_sha256) + "\""
    " data-source-geojson-member=\""
      + xml_escape(config.geojson_member) + "\""
    " data-source-geojson-sha256=\""
      + xml_escape(config.geojson_sha256) + "\""
    " data-source-repository=\""
      + xml_escape(config.source_repository) + "\""
    " data-source-commit=\"" + xml_escape(config.source_commit) + "\""
    " data-source-license=\"" + xml_escape(config.license) + "\""
    "></metadata>\n";
}

inline std::string
output_basename(const generation::projection_spec& spec)
{ return generation::output_basename("network-swarm", spec); }

inline void
generate(const generation::projection_spec& spec,
         const network_swarm_profile& config, const swarm_dataset& dataset)
{
  network_swarm_require(dataset.h3_resolution == config.source_h3_resolution,
                  "network-swarm profile and GeoJSON H3 resolutions differ");
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  const projected_layout layout = make_projected_layout(
    context, dataset, config);
  generation::projection_document document(
    basename, std::string(spec.title) + " cumulative network swarm for "
      + dataset.datestamp, context.map_frame.frame_area);
  document.add_raw(metadata_element(spec, config, dataset, layout));
  add_background(document, context);
  natural_earth::initialize_gdal();
  add_subdued_land(document, context);
  add_tethers(document, layout, config);
  add_downloader_layers(document, layout, config);
  add_labels(document, context, layout, config);
  add_legend(document, context, dataset, config);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  network_swarm_require(input.good(), "failed to open generated " + basename
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
       const network_swarm_profile& config, const swarm_dataset& dataset)
{
  network_swarm_require(generated.find(generation::view_box_fragment(context))
                    != std::string::npos,
                  "generated Network-swarm SVG has the wrong viewBox");
  constexpr std::array layers {
    "network-swarm-background", "terrestrial-land", "cluster-tethers",
    "downloaders-total", "access", "downloaders-mobile",
    "downloaders-satellite", "infrastructure", "downloaders-hosting",
    "downloaders-service", "privacy-routing", "downloaders-vpn",
    "downloaders-tor", "downloaders-tor-exit-nodes", "downloaders-relay",
    "downloaders-proxy", "labels", "legend-and-provenance",
  };
  for (const std::string_view layer : layers)
    network_swarm_require(generated.find("<g id=\"" + std::string(layer) + "\"")
                      != std::string::npos,
                    "generated Network-swarm SVG is missing layer "
                      + std::string(layer));
  network_swarm_require(generated.find("id=\"network-swarm-metadata\"")
                    != std::string::npos
                    && generated.find("data-background-color=\"#f2f4f3\"")
                         != std::string::npos
                    && generated.find("data-title-scale=\"2\"")
                         != std::string::npos
                    && generated.find("data-source-archive-sha256=\""
                      + config.archive_sha256 + "\"") != std::string::npos,
                  "generated Network-swarm SVG is missing provenance metadata");
  network_swarm_require(token_count(generated,
                              "data-network-swarm-feature=\"true\"")
                    == dataset.features.size(),
                  "generated Network-swarm SVG has the wrong feature count");
  network_swarm_require(generated.find(" nan") == std::string::npos
                    && generated.find(" -nan") == std::string::npos
                    && generated.find(" inf") == std::string::npos
                    && generated.find(" -inf") == std::string::npos,
                  "generated Network-swarm SVG has non-finite data");
  generation::verify_configured_label_font(generated, "Network-swarm SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-network-swarm PROJECTION PROFILE.json INPUT.geojson");
  const generation::projection_spec& spec = generation::find_projection_spec(
    argv[1]);
  const network_swarm_profile config = load_network_swarm_profile(
    std::filesystem::absolute(argv[2]));
  const swarm_dataset dataset = load_swarm_dataset(
    std::filesystem::absolute(argv[3]));
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate(spec, config, dataset);
  verify(read_generated(basename), context, config, dataset);
  return 0;
}

} // namespace cart0freak0::network_swarm_generation

#endif

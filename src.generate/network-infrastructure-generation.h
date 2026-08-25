// Projection-aware cloud/CDN and opt-in network-topology SVG generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_INFRASTRUCTURE_GENERATION_H
#define CART0FREAK0_NETWORK_INFRASTRUCTURE_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iterator>
#include <map>
#include <numbers>
#include <optional>
#include <set>
#include <span>
#include <sstream>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <izzi-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "network-infrastructure-clustering.h"
#include "network-infrastructure-data.h"
#include "projection-generation-common.h"

namespace cart0freak0::network_infrastructure_generation {

namespace natural_earth = cart0freak0::natural_earth_generation;

inline std::string
xml_escape(std::string value)
{
  for (char& character : value)
    if (static_cast<unsigned char>(character) < 0x20
        && character != '\t' && character != '\n' && character != '\r')
      character = ' ';
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

inline std::string
polygon_path(const svg::point_2t origin, const double radius,
             const unsigned points, const double rotation = 0)
{
  const double angle = 360.0 / points;
  const double zero = svg::zero_angle_north_cw(angle) + rotation;
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
            const unsigned points, const std::string& attributes = {},
            const double rotation = 0)
{
  layer.add_element(svg::make_path(
    polygon_path(origin, radius, points, rotation), style, "", true,
    attributes));
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

inline svg::typography
infrastructure_typography(const double size = 0.13,
                          const svg::color_qi color = {37, 48, 51})
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

inline void
add_background(generation::projection_document& document,
               const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("network-infrastructure-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{242, 244, 243}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"network-infrastructure-ocean\"");
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

inline std::vector<std::vector<generation::geographic_point>>
split_at_dateline(const std::vector<generation::geographic_point>& source)
{
  std::vector<std::vector<generation::geographic_point>> result;
  if (source.empty())
    return result;
  result.push_back({source.front()});
  for (std::size_t index = 1; index < source.size(); ++index)
    {
      const generation::geographic_point left = source[index - 1];
      const generation::geographic_point right = source[index];
      const double delta = right.longitude - left.longitude;
      if (std::abs(delta) <= 180)
        {
          result.back().push_back(right);
          continue;
        }
      const double adjusted_right = right.longitude + (delta > 0 ? -360 : 360);
      const double boundary = adjusted_right > 180 ? 180 : -180;
      const double opposite = boundary == 180 ? -180 : 180;
      const double fraction
        = (boundary - left.longitude) / (adjusted_right - left.longitude);
      infrastructure_require(fraction >= 0 && fraction <= 1,
                             "failed to split a path at the dateline");
      const double latitude
        = left.latitude + fraction * (right.latitude - left.latitude);
      result.back().push_back({latitude, boundary});
      result.push_back({{latitude, opposite}, right});
    }
  result.erase(std::remove_if(result.begin(), result.end(),
    [](const auto& path) { return path.size() < 2; }), result.end());
  return result;
}

inline std::vector<generation::geographic_point>
densify_path(const std::vector<generation::geographic_point>& source,
             const double maximum_step = 2)
{
  if (source.size() < 2)
    return source;
  std::vector<generation::geographic_point> result;
  result.push_back(source.front());
  for (std::size_t index = 1; index < source.size(); ++index)
    {
      const generation::geographic_point left = source[index - 1];
      const generation::geographic_point right = source[index];
      const double span = std::max(std::abs(right.latitude - left.latitude),
                                   std::abs(right.longitude - left.longitude));
      const std::size_t steps = std::max<std::size_t>(
        1, static_cast<std::size_t>(std::ceil(span / maximum_step)));
      for (std::size_t step = 1; step <= steps; ++step)
        result.push_back(generation::interpolate(
          left, right, static_cast<double>(step) / steps));
    }
  return result;
}

inline std::string
project_open_path(const generation::projection_context& context,
                  const std::vector<generation::geographic_point>& source)
{
  std::string path_data;
  for (const auto& dateline_part : split_at_dateline(source))
    {
      const generation::projected_path_result detailed
        = generation::project_path_detailed(
          context, densify_path(dateline_part), false, true);
      for (const auto& piece : detailed.pieces)
        if (piece.points.size() >= 2)
          path_data += svg::make_path_data_from_points(piece.points);
    }
  return path_data;
}

inline void
add_submarine_cables(generation::projection_document& document,
                     const generation::projection_context& context,
                     const infrastructure_dataset& dataset,
                     const infrastructure_profile& profile)
{
  svg::group_element layer;
  layer.start_element("submarine-cables");
  layer.add_title("Physical submarine cable routes from TeleGeography");
  svg::group_element not_planned;
  not_planned.start_element("submarine-cables-not-planned");
  svg::group_element planned;
  planned.start_element("submarine-cables-planned");
  if (profile.include_submarine_cables)
    for (const cable_route& route : dataset.cables.routes)
      {
        std::string path_data;
        for (const auto& part : route.paths)
          path_data += project_open_path(context, part);
        infrastructure_require(!path_data.empty(),
          "submarine cable route produced no projected path: "
            + route.feature_id);
        const svg::style style = route.planned
          ? svg::style {svg::color::none, 0, {137, 76, 0}, 0.86, 0.020}
          : svg::style {svg::color::none, 0, {0, 96, 120}, 0.82, 0.024};
        std::string attributes
          = "data-submarine-cable-route=\"true\" data-cable-id=\""
          + xml_escape(route.cable_id) + "\" data-cable-name=\""
          + xml_escape(route.name) + "\" data-feature-id=\""
          + xml_escape(route.feature_id) + "\" data-source-color=\""
          + xml_escape(route.source_color) + "\" data-status=\""
            + (route.planned ? "planned" : "not-planned")
          + "\" stroke-linecap=\"round\" stroke-linejoin=\"round\"";
        if (route.planned)
          attributes += " stroke-dasharray=\"0.08 0.055\"";
        (route.planned ? planned : not_planned).add_element(svg::make_path(
          path_data, style, "", true, attributes));
      }
  not_planned.finish_element();
  planned.finish_element();
  layer.add_element(not_planned);
  layer.add_element(planned);
  layer.finish_element();
  document.add_element(layer);
}

inline generation::geographic_point
spherical_centroid(const exchange_dataset& dataset,
                   const internet_exchange& exchange)
{
  double x = 0;
  double y = 0;
  double z = 0;
  constexpr double radians = std::numbers::pi / 180.0;
  for (const std::size_t index : exchange.building_indices)
    {
      const generation::geographic_point point
        = dataset.buildings[index].point;
      const double latitude = point.latitude * radians;
      const double longitude = point.longitude * radians;
      x += std::cos(latitude) * std::cos(longitude);
      y += std::cos(latitude) * std::sin(longitude);
      z += std::sin(latitude);
    }
  infrastructure_require(std::hypot(x, y, z) > 1e-12,
                         "Internet exchange has an indeterminate logical centroid");
  const double longitude = std::atan2(y, x) / radians;
  const double latitude = std::atan2(z, std::hypot(x, y)) / radians;
  infrastructure_require(std::isfinite(longitude) && std::isfinite(latitude),
                         "Internet exchange has an invalid logical centroid");
  return {latitude, longitude};
}

inline std::size_t
multi_building_exchange_count(const exchange_dataset& dataset)
{
  return static_cast<std::size_t>(std::count_if(
    dataset.exchanges.begin(), dataset.exchanges.end(),
    [](const internet_exchange& exchange) {
      return exchange.building_indices.size() > 1;
    }));
}

inline bool
exchange_has_distinct_building_points(const exchange_dataset& dataset,
                                      const internet_exchange& exchange)
{
  if (exchange.building_indices.size() < 2)
    return false;
  const generation::geographic_point first
    = dataset.buildings.at(exchange.building_indices.front()).point;
  return std::any_of(std::next(exchange.building_indices.begin()),
                     exchange.building_indices.end(),
    [&](const std::size_t index) {
      const generation::geographic_point point = dataset.buildings.at(index).point;
      return point.latitude != first.latitude
        || point.longitude != first.longitude;
    });
}

inline std::size_t
colocated_multi_building_exchange_count(const exchange_dataset& dataset)
{
  return static_cast<std::size_t>(std::count_if(
    dataset.exchanges.begin(), dataset.exchanges.end(),
    [&](const internet_exchange& exchange) {
      return exchange.building_indices.size() > 1
        && !exchange_has_distinct_building_points(dataset, exchange);
    }));
}

inline void
add_exchange_membership(generation::projection_document& document,
                        const generation::projection_context& context,
                        const infrastructure_dataset& dataset,
                        const infrastructure_profile& profile)
{
  svg::group_element membership;
  membership.start_element("internet-exchange-membership");
  membership.add_title(
    "Logical exchange-to-building membership; not physical fiber");
  svg::group_element hubs;
  hubs.start_element("internet-exchange-logical-hubs");
  if (profile.include_exchange_membership)
    for (const internet_exchange& exchange : dataset.exchanges.exchanges)
      {
        if (exchange.building_indices.size() < 2)
          continue;
        const generation::geographic_point hub = spherical_centroid(
          dataset.exchanges, exchange);
        const bool has_distinct_points = exchange_has_distinct_building_points(
          dataset.exchanges, exchange);
        std::string path_data;
        if (has_distinct_points)
          {
            for (const std::size_t building_index : exchange.building_indices)
              {
                const generation::geographic_point point
                  = dataset.exchanges.buildings[building_index].point;
                if (point.latitude == hub.latitude
                    && point.longitude == hub.longitude)
                  continue;
                path_data += project_open_path(context, {hub, point});
              }
            infrastructure_require(!path_data.empty(),
              "distinct multi-building exchange produced no logical path: "
                + exchange.slug);
            membership.add_element(svg::make_path(
              path_data,
              {svg::color::none, 0, {139, 28, 99}, 0.58, 0.012}, "", true,
              "data-internet-exchange-membership=\"true\" data-exchange=\""
                + xml_escape(exchange.slug) + "\" data-building-count=\""
                + std::to_string(exchange.building_indices.size())
                + "\" data-topology-semantics=\"logical-membership\""
                  " stroke-dasharray=\"0.035 0.045\" stroke-linecap=\"round\""));
          }
        const std::string colocated_attributes = has_distinct_points
          ? std::string {}
          : " data-internet-exchange-membership=\"true\""
            " data-topology-semantics=\"co-located-logical-membership\"";
        add_circle(hubs, generation::project_point(context, hub),
          {svg::color::none, 0, {139, 28, 99}, 0.86, 0.013},
          profile.marker_radius * 0.8,
          "data-internet-exchange-logical-hub=\"true\" data-exchange=\""
            + xml_escape(exchange.slug) + "\" data-building-count=\""
            + std::to_string(exchange.building_indices.size())
            + "\" data-derived=\"spherical-centroid\""
            + colocated_attributes);
      }
  hubs.finish_element();
  membership.add_element(hubs);
  membership.finish_element();
  document.add_element(membership);
}

inline const cloud_site&
cloud_source(const projected_infrastructure_point& point,
             const infrastructure_dataset& dataset)
{
  infrastructure_require(point.source.kind
                           == infrastructure_point_kind::cloud_site,
                         "point is not a cloud source");
  return dataset.cloud.sites.at(point.source.source_index);
}

inline const landing_point&
landing_source(const projected_infrastructure_point& point,
               const infrastructure_dataset& dataset)
{
  infrastructure_require(point.source.kind
                           == infrastructure_point_kind::cable_landing,
                         "point is not a landing source");
  return dataset.cables.landings.at(point.source.source_index);
}

inline const exchange_building&
building_source(const projected_infrastructure_point& point,
                const infrastructure_dataset& dataset)
{
  infrastructure_require(point.source.kind
                           == infrastructure_point_kind::exchange_building,
                         "point is not an exchange-building source");
  return dataset.exchanges.buildings.at(point.source.source_index);
}

inline std::string
common_point_attributes(const projected_infrastructure_point& point)
{
  return "data-network-infrastructure-point=\"true\" data-point-kind=\""
    + std::string(point_kind_name(point.source.kind))
    + "\" data-source-id=\"" + xml_escape(point.source.id)
    + "\" data-projection-cell=\"" + std::to_string(point.projection_cell)
    + "\" data-cluster-size=\"" + std::to_string(point.cluster_size)
    + "\" data-true-x=\"" + format_number(std::get<0>(point.geographic_point))
    + "\" data-true-y=\"" + format_number(std::get<1>(point.geographic_point))
    + "\"";
}

inline void
add_cluster_tethers(generation::projection_document& document,
                    const infrastructure_point_layout& layout,
                    const infrastructure_profile& profile)
{
  svg::group_element layer;
  layer.start_element("infrastructure-cluster-tethers");
  if (profile.show_tethers)
    for (const projected_infrastructure_point& point : layout.points)
      if (generation::point_distance(point.geographic_point, point.display_point)
          >= profile.minimum_tether)
        add_line(layer, point.geographic_point, point.display_point,
                 {{70, 83, 85}, 0, {70, 83, 85}, 0.48, 0.007},
                 "data-source-id=\"" + xml_escape(point.source.id)
                   + "\" data-semantics=\"display-displacement\"");
  layer.finish_element();
  document.add_element(layer);
}

inline svg::color_qi
provider_color(const std::string_view provider)
{
  constexpr auto spectrum = svg::spectrum<svg::palette_kind::izzi_hue>();
  const std::size_t usable = spectrum.size() - 1;
  return spectrum[std::hash<std::string_view> {}(provider) % usable];
}

inline void
add_cloud_marker(svg::group_element& layer,
                 const projected_infrastructure_point& point,
                 const cloud_site& site,
                 const infrastructure_profile& profile)
{
  // alpha60 CDN style: black clustered marks, translucent fill, solid
  // black stroke, uniform hexagonal mark for every provider entity type.
  std::string attributes = common_point_attributes(point)
    + " data-infrastructure-cloud-site=\"true\" data-provider=\""
    + xml_escape(site.provider) + "\" data-service=\""
    + xml_escape(site.service) + "\" data-entity-type=\""
    + xml_escape(site.entity_type) + "\" data-name=\""
    + xml_escape(site.name) + "\" data-source-scope=\""
    + xml_escape(site.source_scope) + "\" data-location-precision=\""
    + xml_escape(site.location_precision) + "\"";
  const svg::color_qi color = provider_color(site.provider);
  if (site.entity_type == "edge_pop")
    add_polygon(layer, point.display_point,
      {color, 0.30, color, 1.0, 0.010},
      profile.marker_radius * 2.0, 6, attributes, 0);
  else if (site.entity_type == "data_center")
    add_polygon(layer, point.display_point,
      {color, 0.30, color, 1.0, 0.010},
      profile.marker_radius * 2.1, 6, attributes, 0);
  else if (site.entity_type == "cloud_region"
           || site.entity_type == "availability_zone"
           || site.entity_type == "local_zone")
    add_polygon(layer, point.display_point,
      {color, 0.30, color, 1.0, 0.010},
      profile.marker_radius * 2.0, 6, attributes, 0);
  else
    add_polygon(layer, point.display_point,
      {color, 0.30, color, 1.0, 0.010},
      profile.marker_radius * 1.8, 6, attributes, 0);
}

inline void
add_infrastructure_points(generation::projection_document& document,
                          const infrastructure_point_layout& layout,
                          const infrastructure_dataset& dataset,
                          const infrastructure_profile& profile)
{
  svg::group_element cloud;
  cloud.start_element("cloud-cdn-sites");
  cloud.add_title("Located cloud and CDN source records; sites, not links");
  svg::group_element landings;
  landings.start_element("landing-points");
  landings.add_title("Physical submarine cable landing points");
  svg::group_element buildings;
  buildings.start_element("internet-exchange-buildings");
  buildings.add_title("Geolocated Internet-exchange facilities");
  for (const projected_infrastructure_point& point : layout.points)
    {
      if (point.source.kind != infrastructure_point_kind::cloud_site
          && profile.product == infrastructure_product::sites)
        continue;
      switch (point.source.kind)
        {
        case infrastructure_point_kind::cloud_site:
          add_cloud_marker(cloud, point, cloud_source(point, dataset), profile);
          break;
        case infrastructure_point_kind::cable_landing:
          {
            const landing_point& landing = landing_source(point, dataset);
            add_circle(landings, point.display_point,
              {{0, 96, 120}, 0.90, {0, 62, 79}, 0.98, 0.009},
              profile.marker_radius * 0.78,
              common_point_attributes(point)
                + " data-infrastructure-landing-point=\"true\" data-name=\""
                + xml_escape(landing.name) + "\" data-cable-count=\""
                + std::to_string(landing.cable_count) + "\" data-tbd=\""
                + (landing.tbd ? "true" : "false") + "\"");
            break;
          }
        case infrastructure_point_kind::exchange_building:
          {
            const exchange_building& building = building_source(point, dataset);
            add_polygon(buildings, point.display_point,
              {{139, 28, 99}, 0.88, {91, 17, 64}, 0.98, 0.009},
              profile.marker_radius * 0.92, 4,
              common_point_attributes(point)
                + " data-infrastructure-exchange-building=\"true\" data-name=\""
                + xml_escape(building.name) + "\" data-country=\""
                + xml_escape(building.country) + "\" data-metro-area=\""
                + xml_escape(building.metro_area) + "\" data-exchange-count=\""
                + std::to_string(building.exchanges.size()) + "\"");
            break;
          }
        }
    }
  cloud.finish_element();
  landings.finish_element();
  buildings.finish_element();
  document.add_element(cloud);
  if (profile.product == infrastructure_product::topology)
    {
      document.add_element(landings);
      document.add_element(buildings);
    }
}

inline std::string
point_label(const projected_infrastructure_point& point,
            const infrastructure_dataset& dataset)
{
  switch (point.source.kind)
    {
    case infrastructure_point_kind::cloud_site:
      {
        const cloud_site& site = cloud_source(point, dataset);
        return site.provider + " / " + site.name;
      }
    case infrastructure_point_kind::cable_landing:
      return landing_source(point, dataset).name;
    case infrastructure_point_kind::exchange_building:
      {
        const exchange_building& building = building_source(point, dataset);
        return "IX / " + (building.metro_area.empty()
          ? building.name : building.metro_area);
      }
    }
  throw std::logic_error("unhandled point label kind");
}

inline void
add_point_labels(generation::projection_document& document,
                 const generation::projection_context& context,
                 const infrastructure_point_layout& layout,
                 const infrastructure_dataset& dataset,
                 const infrastructure_profile& profile)
{
  std::vector<const projected_infrastructure_point*> ranked;
  ranked.reserve(layout.points.size());
  for (const projected_infrastructure_point& point : layout.points)
    ranked.push_back(&point);
  std::sort(ranked.begin(), ranked.end(), [](const auto left,
                                              const auto right) {
    if (left->source.priority != right->source.priority)
      return left->source.priority > right->source.priority;
    if (left->source.kind != right->source.kind)
      return left->source.kind < right->source.kind;
    return left->source.id < right->source.id;
  });
  svg::group_element layer;
  layer.start_element("infrastructure-labels");
  std::set<std::pair<int, int>> occupied;
  std::size_t count = 0;
  for (const projected_infrastructure_point* point : ranked)
    {
      if (count >= profile.maximum_labels)
        break;
      const double x = std::get<0>(point->display_point);
      const double y = std::get<1>(point->display_point);
      if (y < 1.05 || y > context.map_frame.height() - 0.2)
        continue;
      const std::pair grid {
        static_cast<int>(std::floor(x / 1.0)),
        static_cast<int>(std::floor(y / 0.31)),
      };
      if (!occupied.insert(grid).second)
        continue;
      const bool place_left = x > context.map_frame.width() - 3.0;
      svg::typography typography = infrastructure_typography();
      typography._M_anchor = place_left ? svg::typography::anchor::end
                                        : svg::typography::anchor::start;
      typography._M_align = place_left ? svg::typography::align::right
                                       : svg::typography::align::left;
      const double label_x = x + (place_left ? -1 : 1)
        * (profile.marker_radius * 2.0 + 0.04);
      svg::styled_text(layer, xml_escape(point_label(*point, dataset)),
                       {label_x, y}, typography);
      ++count;
    }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_cable_labels(generation::projection_document& document,
                 const generation::projection_context& context,
                 const infrastructure_dataset& dataset,
                 const infrastructure_profile& profile)
{
  svg::group_element layer;
  layer.start_element("submarine-cable-labels");
  if (profile.include_submarine_cables)
    {
      std::vector<const cable_system*> systems;
      systems.reserve(dataset.cables.systems.size());
      for (const cable_system& system : dataset.cables.systems)
        systems.push_back(&system);
      std::sort(systems.begin(), systems.end(), [](const auto left,
                                                   const auto right) {
        if (left->landing_ids.size() != right->landing_ids.size())
          return left->landing_ids.size() > right->landing_ids.size();
        return left->id < right->id;
      });
      std::map<std::string, const cable_route*> first_route;
      for (const cable_route& route : dataset.cables.routes)
        first_route.try_emplace(route.cable_id, &route);
      std::set<std::pair<int, int>> occupied;
      std::size_t count = 0;
      for (const cable_system* system : systems)
        {
          if (count >= profile.maximum_cable_labels)
            break;
          const auto route = first_route.find(system->id);
          if (route == first_route.end() || route->second->paths.empty()
              || route->second->paths.front().empty())
            continue;
          const auto& source = route->second->paths.front();
          const svg::point_2t point = generation::project_point(
            context, source[source.size() / 2]);
          const double x = std::get<0>(point);
          const double y = std::get<1>(point);
          if (y < 1.05 || y > context.map_frame.height() - 0.2)
            continue;
          const std::pair grid {static_cast<int>(std::floor(x / 1.5)),
                                static_cast<int>(std::floor(y / 0.45))};
          if (!occupied.insert(grid).second)
            continue;
          svg::typography typography = infrastructure_typography(
            0.105, system->planned ? svg::color_qi {137, 76, 0}
                                  : svg::color_qi {0, 96, 120});
          typography._M_anchor = svg::typography::anchor::middle;
          typography._M_align = svg::typography::align::center;
          svg::styled_text(layer, xml_escape(system->name), point, typography);
          ++count;
        }
    }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_legend(generation::projection_document& document,
           const generation::projection_context& context,
           const infrastructure_dataset& dataset,
           const infrastructure_profile& profile)
{
  const bool topology = profile.product == infrastructure_product::topology;
  const std::string title_text = topology
    ? "NETWORK INFRASTRUCTURE / TOPOLOGY"
    : "NETWORK INFRASTRUCTURE / SITES";
  std::string counts = std::to_string(dataset.cloud.sites.size())
    + " located cloud/CDN records";
  if (topology)
    counts += "  |  " + std::to_string(dataset.cables.systems.size())
      + " cable systems  |  " + std::to_string(dataset.cables.landings.size())
      + " landings  |  " + std::to_string(dataset.exchanges.buildings.size())
      + " IX facilities";
  const std::string semantics = topology
    ? "solid cable = physical route  ·  dashed magenta = logical IX membership, not fiber"
    : "provider/source records = sites only  ·  no links inferred";
  const std::string notice = topology
    ? "TeleGeography map data: CC BY-NC-SA 3.0 · cable "
      + profile.cables.snapshot + " · IX " + profile.exchanges.snapshot
    : "cloud_cdn_cache: ODC-By 1.0; source-specific terms retained · "
      + profile.cloud.snapshot + " snapshot";
  constexpr double page_margin = 0.573;
  const double panel_width = std::clamp(
    generation::legend_text_width(title_text, 0.42) + 2 * page_margin,
    5.0,
    context.map_frame.width() - 0.6);
  constexpr double panel_height = 1.64;
  svg::group_element layer;
  layer.start_element("network-infrastructure-legend-and-provenance",
    generation::bottom_right_legend_transform(
      context, panel_width, panel_height));
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, panel_width, panel_height});
  band.add_style({{255, 255, 255}, 0.94, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);
  svg::typography title = infrastructure_typography(
    0.42, {42, 40, 36});
  title._M_w = svg::typography::weight::bold;
  title._M_anchor = svg::typography::anchor::end;
  title._M_align = svg::typography::align::right;
  svg::styled_text(layer, title_text,
    {panel_width - page_margin, 0.61}, title);
  svg::typography body = infrastructure_typography(0.12, {87, 82, 74});
  body._M_anchor = svg::typography::anchor::end;
  body._M_align = svg::typography::align::right;
  svg::styled_text(layer, counts, {panel_width - page_margin, 1.00}, body);
  svg::styled_text(layer, semantics,
    {panel_width - page_margin, 1.24}, body);
  svg::typography attribution = infrastructure_typography(
    0.12, {87, 82, 74});
  attribution._M_anchor = svg::typography::anchor::end;
  attribution._M_align = svg::typography::align::right;
  svg::styled_text(layer, notice,
    {panel_width - page_margin, 1.48}, attribution);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
metadata_element(const generation::projection_spec& spec,
                 const infrastructure_profile& profile,
                 const infrastructure_dataset& dataset,
                 const infrastructure_point_layout& layout)
{
  const bool topology = profile.product == infrastructure_product::topology;
  std::string result = "<metadata id=\"network-infrastructure-metadata\""
    " data-product=\"" + std::string(topology ? "topology" : "sites") + "\""
    " data-profile=\"" + xml_escape(profile.path.filename().string()) + "\""
    " data-marker-radius-inches=\"" + format_number(profile.marker_radius, 3)
      + "\" data-background-color=\"#f2f4f3\" data-title-scale=\"2\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-generated-artifact-license=\""
      + xml_escape(profile.generated_artifact_license) + "\""
    " data-tele-geography-opt-in=\""
      + std::string(profile.topology_opt_in ? "true" : "false") + "\""
    " data-cloud-source-repository=\"" + xml_escape(profile.cloud.repository)
      + "\" data-cloud-source-commit=\"" + profile.cloud.commit + "\""
    " data-cloud-source-license=\"" + xml_escape(profile.cloud.license) + "\""
    " data-cloud-source-snapshot=\"" + xml_escape(profile.cloud.snapshot) + "\""
    " data-cloud-manifest=\"" + xml_escape(profile.cloud.manifest.string())
      + "\" data-cloud-manifest-sha256=\""
      + profile.cloud.manifest_sha256 + "\""
    " data-cloud-record-count=\"" + std::to_string(dataset.cloud.record_count)
      + "\" data-cloud-located-count=\""
      + std::to_string(dataset.cloud.sites.size()) + "\""
    " data-point-cluster-count=\"" + std::to_string(layout.cluster_count)
      + "\" data-largest-point-cluster=\""
      + std::to_string(layout.largest_cluster) + "\"";
  if (topology)
    result += " data-cable-source-repository=\""
      + xml_escape(profile.cables.repository) + "\" data-cable-source-commit=\""
      + profile.cables.commit + "\" data-cable-source-license=\""
      + xml_escape(profile.cables.license) + "\" data-cable-source-snapshot=\""
      + xml_escape(profile.cables.snapshot) + "\" data-cable-routes-sha256=\""
      + profile.cables.routes_sha256 + "\" data-cable-landings-sha256=\""
      + profile.cables.landings_sha256 + "\" data-cable-details-sha256=\""
      + profile.cables.details_sha256 + "\" data-cable-system-count=\""
      + std::to_string(dataset.cables.systems.size())
      + "\" data-cable-route-feature-count=\""
      + std::to_string(dataset.cables.routes.size())
      + "\" data-cable-landing-count=\""
      + std::to_string(dataset.cables.landings.size())
      + "\" data-internet-exchange-source-repository=\""
      + xml_escape(profile.exchanges.repository)
      + "\" data-internet-exchange-source-commit=\""
      + profile.exchanges.commit
      + "\" data-internet-exchange-source-license=\""
      + xml_escape(profile.exchanges.license)
      + "\" data-internet-exchange-source-snapshot=\""
      + xml_escape(profile.exchanges.snapshot)
      + "\" data-internet-exchange-buildings-sha256=\""
      + profile.exchanges.buildings_sha256
      + "\" data-internet-exchange-building-count=\""
      + std::to_string(dataset.exchanges.buildings.size())
      + "\" data-internet-exchange-count=\""
      + std::to_string(dataset.exchanges.exchanges.size())
      + "\" data-internet-exchange-membership-count=\""
      + std::to_string(dataset.exchanges.membership_count)
      + "\" data-internet-exchange-unique-membership-count=\""
      + std::to_string(dataset.exchanges.membership_count
                       - dataset.exchanges.duplicate_membership_count)
      + "\" data-internet-exchange-duplicate-membership-count=\""
      + std::to_string(dataset.exchanges.duplicate_membership_count)
      + "\" data-internet-exchange-colocated-group-count=\""
      + std::to_string(colocated_multi_building_exchange_count(
                         dataset.exchanges))
      + "\" data-physical-topology=\"submarine-cable-routes\""
        " data-logical-topology=\"internet-exchange-building-membership\""
        " data-inferred-cross-source-edges=\"0\"";
  return result + "></metadata>\n";
}

inline std::string
output_basename(const generation::projection_spec& spec,
                const infrastructure_product product)
{
  return generation::output_basename(
    product == infrastructure_product::topology
      ? "network-infrastructure-topology"
      : "network-cdn",
    spec);
}

inline void
generate(const generation::projection_spec& spec,
         const infrastructure_profile& profile,
         const infrastructure_dataset& dataset)
{
  const std::string basename = output_basename(spec, profile.product);
  const generation::projection_context context(spec, basename);
  const infrastructure_point_layout layout
    = make_infrastructure_point_layout(context, dataset, profile);
  generation::projection_document document(
    basename, std::string(spec.title)
      + (profile.product == infrastructure_product::topology
           ? " opt-in network infrastructure topology"
           : " network CDN site atlas"),
    context.map_frame.frame_area);
  document.add_raw(metadata_element(spec, profile, dataset, layout));
  add_background(document, context);
  natural_earth::initialize_gdal();
  add_subdued_land(document, context);
  if (profile.product == infrastructure_product::topology)
    {
      add_submarine_cables(document, context, dataset, profile);
      add_exchange_membership(document, context, dataset, profile);
      add_cluster_tethers(document, layout, profile);
      add_cable_labels(document, context, dataset, profile);
    }
  add_infrastructure_points(document, layout, dataset, profile);
  add_point_labels(document, context, layout, dataset, profile);
  add_legend(document, context, dataset, profile);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  infrastructure_require(input.good(), "failed to open generated "
                                      + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline std::size_t
token_count(const std::string_view text, const std::string_view token)
{
  std::size_t result = 0;
  std::size_t position = 0;
  while ((position = text.find(token, position)) != std::string_view::npos)
    {
      ++result;
      position += token.size();
    }
  return result;
}

inline bool
has_invalid_xml_control(const std::string_view text)
{
  return std::any_of(text.begin(), text.end(), [](const unsigned char value) {
    return value < 0x20 && value != '\t' && value != '\n' && value != '\r';
  });
}

inline void
verify(const std::string& generated,
       const generation::projection_context& context,
       const infrastructure_profile& profile,
       const infrastructure_dataset& dataset)
{
  infrastructure_require(generated.find(generation::view_box_fragment(context))
                           != std::string::npos,
                         "generated infrastructure SVG has the wrong viewBox");
  constexpr std::array<std::string_view, 5> sites_layers {
    "network-infrastructure-background", "terrestrial-land",
    "cloud-cdn-sites", "infrastructure-labels",
    "network-infrastructure-legend-and-provenance",
  };
  constexpr std::array<std::string_view, 14> topology_layers {
    "network-infrastructure-background", "terrestrial-land",
    "submarine-cables", "submarine-cables-not-planned",
    "submarine-cables-planned", "internet-exchange-membership",
    "internet-exchange-logical-hubs", "infrastructure-cluster-tethers",
    "cloud-cdn-sites", "landing-points", "internet-exchange-buildings",
    "submarine-cable-labels", "infrastructure-labels",
    "network-infrastructure-legend-and-provenance",
  };
  const std::span<const std::string_view> layers
    = profile.product == infrastructure_product::sites
      ? std::span<const std::string_view>(sites_layers)
      : std::span<const std::string_view>(topology_layers);
  for (const std::string_view layer : layers)
    infrastructure_require(generated.find("<g id=\"" + std::string(layer)
                                            + "\"") != std::string::npos,
      "generated infrastructure SVG is missing layer " + std::string(layer));
  infrastructure_require(generated.find(
    "id=\"network-infrastructure-metadata\"") != std::string::npos
    && generated.find("data-background-color=\"#f2f4f3\"")
         != std::string::npos
    && generated.find("data-title-scale=\"2\"") != std::string::npos
    && generated.find("data-cloud-manifest-sha256=\""
      + profile.cloud.manifest_sha256 + "\"") != std::string::npos,
    "generated infrastructure SVG is missing cloud provenance");
  infrastructure_require(token_count(generated,
    "data-infrastructure-cloud-site=\"true\"") == dataset.cloud.sites.size(),
    "generated infrastructure SVG has the wrong cloud-site count");
  if (profile.product == infrastructure_product::topology)
    {
      infrastructure_require(token_count(generated,
        "data-submarine-cable-route=\"true\"") == dataset.cables.routes.size(),
        "generated topology SVG has the wrong cable-route count");
      infrastructure_require(token_count(generated,
        "data-infrastructure-landing-point=\"true\"")
          == dataset.cables.landings.size(),
        "generated topology SVG has the wrong landing-point count");
      infrastructure_require(token_count(generated,
        "data-infrastructure-exchange-building=\"true\"")
          == dataset.exchanges.buildings.size(),
        "generated topology SVG has the wrong exchange-building count");
      infrastructure_require(token_count(generated,
        "data-internet-exchange-membership=\"true\"")
          == multi_building_exchange_count(dataset.exchanges),
        "generated topology SVG has the wrong logical-membership count");
      infrastructure_require(generated.find(
        "data-inferred-cross-source-edges=\"0\"") != std::string::npos
        && generated.find("data-tele-geography-opt-in=\"true\"")
             != std::string::npos
        && generated.find("data-cable-landings-sha256=\""
          + profile.cables.landings_sha256 + "\"") != std::string::npos
        && generated.find("data-cable-details-sha256=\""
          + profile.cables.details_sha256 + "\"") != std::string::npos
        && generated.find("data-internet-exchange-buildings-sha256=\""
          + profile.exchanges.buildings_sha256 + "\"") != std::string::npos
        && generated.find("CC BY-NC-SA 3.0") != std::string::npos,
        "generated topology SVG is missing its semantic or license boundary");
    }
  else
    infrastructure_require(token_count(generated,
      "data-submarine-cable-route=\"true\"") == 0
      && token_count(generated,
        "data-infrastructure-exchange-building=\"true\"") == 0,
      "sites product unexpectedly contains licensed topology");
  infrastructure_require(generated.find(" nan ") == std::string::npos
                           && generated.find(" -nan ") == std::string::npos
                           && generated.find(" inf ") == std::string::npos
                           && generated.find(" -inf ") == std::string::npos,
                         "generated infrastructure SVG has non-finite data");
  infrastructure_require(!has_invalid_xml_control(generated),
                         "generated infrastructure SVG has invalid XML controls");
  generation::verify_configured_label_font(
    generated, "Network-infrastructure SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 4 && argc != 6)
    throw std::invalid_argument(
      "usage: generate-network-infrastructure PROJECTION PROFILE.json "
      "CLOUD_ROOT [SUBMARINE_ROOT INTERNET_EXCHANGE_ROOT]");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const infrastructure_profile profile = load_infrastructure_profile(
    fs::absolute(argv[2]));
  if (profile.product == infrastructure_product::sites)
    infrastructure_require(argc == 4,
      "sites profile accepts only the cloud/CDN source root");
  else
    infrastructure_require(argc == 6,
      "topology profile requires both TeleGeography source roots");
  const std::optional<fs::path> cable_root
    = argc == 6 ? std::optional<fs::path> {fs::absolute(argv[4])}
                : std::nullopt;
  const std::optional<fs::path> exchange_root
    = argc == 6 ? std::optional<fs::path> {fs::absolute(argv[5])}
                : std::nullopt;
  const infrastructure_dataset dataset = load_infrastructure_dataset(
    profile, fs::absolute(argv[3]), cable_root, exchange_root);
  const std::string basename = output_basename(spec, profile.product);
  const generation::projection_context context(spec, basename);
  generate(spec, profile, dataset);
  verify(read_generated(basename), context, profile, dataset);
  return 0;
}

} // namespace cart0freak0::network_infrastructure_generation

#endif

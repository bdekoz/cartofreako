// Projection-safe Izzi honeycomb placement for infrastructure point layers.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_INFRASTRUCTURE_CLUSTERING_H
#define CART0FREAK0_NETWORK_INFRASTRUCTURE_CLUSTERING_H 1

#include <algorithm>
#include <cmath>
#include <compare>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <izzi-svg.h>

#include "network-infrastructure-data.h"
#include "projection-generation-common.h"

namespace cart0freak0::network_infrastructure_generation {

enum class infrastructure_point_kind
{
  cloud_site,
  cable_landing,
  exchange_building,
};

inline std::string_view
point_kind_name(const infrastructure_point_kind kind)
{
  switch (kind)
    {
    case infrastructure_point_kind::cloud_site: return "cloud-site";
    case infrastructure_point_kind::cable_landing: return "cable-landing";
    case infrastructure_point_kind::exchange_building:
      return "exchange-building";
    }
  throw std::logic_error("unhandled infrastructure point kind");
}

struct infrastructure_point_source
{
  infrastructure_point_kind kind = infrastructure_point_kind::cloud_site;
  std::size_t source_index = 0;
  std::string id;
  generation::geographic_point point {};
  std::size_t priority = 0;
};

struct infrastructure_cluster_key
{
  std::uint64_t projection_cell = 0;
  long long column = 0;
  long long row = 0;

  auto operator<=>(const infrastructure_cluster_key&) const = default;
};

struct projected_infrastructure_point
{
  infrastructure_point_source source;
  svg::point_2t geographic_point {};
  svg::point_2t display_point {};
  std::uint64_t projection_cell = 0;
  std::size_t cluster_size = 0;
};

struct infrastructure_point_layout
{
  std::vector<projected_infrastructure_point> points;
  std::size_t cluster_count = 0;
  std::size_t largest_cluster = 0;
};

inline std::vector<svg::point_2t>
infrastructure_honeycomb_offsets(const double radius,
                                 const std::size_t count)
{
  infrastructure_require(count > 0
    && count <= std::numeric_limits<svg::uint>::max(),
    "infrastructure cluster has an invalid size");
  std::vector<svg::point_2t> result;
  for (std::size_t multiplier = 1; multiplier <= 16
       && result.size() < count; multiplier *= 2)
    {
      const std::size_t requested = std::min<std::size_t>(
        std::numeric_limits<svg::uint>::max(), count * multiplier + 7);
      const std::vector<svg::point_2t> candidates
        = svg::radiate_hexagon_honeycomb(
            {0, 0}, radius, static_cast<svg::uint>(requested), true);
      std::set<std::pair<long long, long long>> lattice;
      result.clear();
      for (const auto& [x, y] : candidates)
        {
          infrastructure_require(std::isfinite(x) && std::isfinite(y),
                                 "Izzi honeycomb returned a non-finite point");
          const long long column = std::llround(x / radius);
          const long long row = std::llround(
            y / (std::sqrt(3.0) * radius));
          if (lattice.emplace(column, row).second)
            result.emplace_back(column * radius,
                                row * std::sqrt(3.0) * radius);
        }
    }
  infrastructure_require(result.size() >= count,
                         "Izzi honeycomb did not provide enough unique points");
  std::sort(result.begin(), result.end(), [](const auto left,
                                             const auto right) {
    const double left_distance = std::hypot(
      std::get<0>(left), std::get<1>(left));
    const double right_distance = std::hypot(
      std::get<0>(right), std::get<1>(right));
    return std::tie(left_distance, std::get<1>(left), std::get<0>(left))
      < std::tie(right_distance, std::get<1>(right), std::get<0>(right));
  });
  result.resize(count);
  std::set<std::pair<long long, long long>> unique;
  for (const auto& [x, y] : result)
    unique.emplace(std::llround(x * 1e9), std::llround(y * 1e9));
  infrastructure_require(unique.size() == result.size(),
                         "Izzi honeycomb returned duplicate points");
  return result;
}

inline std::size_t
cloud_priority(const cloud_site& site)
{
  if (site.entity_type == "data_center")
    return 80;
  if (site.entity_type == "cloud_region")
    return 70;
  if (site.entity_type == "local_zone")
    return 60;
  if (site.entity_type == "edge_pop")
    return 50;
  if (site.entity_type == "availability_zone")
    return 40;
  return 30;
}

inline std::vector<infrastructure_point_source>
make_point_sources(const infrastructure_dataset& dataset,
                   const infrastructure_profile& profile)
{
  std::vector<infrastructure_point_source> result;
  result.reserve(dataset.cloud.sites.size() + dataset.cables.landings.size()
                 + dataset.exchanges.buildings.size());
  if (profile.include_cloud_sites)
    for (std::size_t index = 0; index < dataset.cloud.sites.size(); ++index)
      {
        const cloud_site& site = dataset.cloud.sites[index];
        result.push_back({infrastructure_point_kind::cloud_site, index,
                          site.id, site.point, cloud_priority(site)});
      }
  if (profile.include_landing_points)
    for (std::size_t index = 0; index < dataset.cables.landings.size(); ++index)
      {
        const landing_point& landing = dataset.cables.landings[index];
        result.push_back({infrastructure_point_kind::cable_landing, index,
                          landing.id, landing.point,
                          100 + landing.cable_count});
      }
  if (profile.include_exchange_buildings)
    for (std::size_t index = 0; index < dataset.exchanges.buildings.size();
         ++index)
      {
        const exchange_building& building = dataset.exchanges.buildings[index];
        result.push_back({infrastructure_point_kind::exchange_building, index,
                          building.id, building.point,
                          120 + building.exchanges.size()});
      }
  return result;
}

inline infrastructure_point_layout
make_infrastructure_point_layout(
  const generation::projection_context& context,
  const infrastructure_dataset& dataset,
  const infrastructure_profile& profile)
{
  infrastructure_point_layout result;
  const std::vector<infrastructure_point_source> sources
    = make_point_sources(dataset, profile);
  result.points.reserve(sources.size());
  std::map<infrastructure_cluster_key, std::vector<std::size_t>> clusters;
  for (const infrastructure_point_source& source : sources)
    {
      const svg::point_2t projected = generation::project_point(
        context, source.point);
      const infrastructure_cluster_key key {
        generation::projection_cell(context, source.point),
        static_cast<long long>(std::floor(
          std::get<0>(projected) / profile.collision_cell)),
        static_cast<long long>(std::floor(
          std::get<1>(projected) / profile.collision_cell)),
      };
      const std::size_t index = result.points.size();
      result.points.push_back(
        {source, projected, projected, key.projection_cell, 0});
      clusters[key].push_back(index);
    }

  result.cluster_count = clusters.size();
  for (auto& [key, indices] : clusters)
    {
      static_cast<void>(key);
      result.largest_cluster = std::max(result.largest_cluster, indices.size());
      std::sort(indices.begin(), indices.end(), [&](const std::size_t left,
                                                    const std::size_t right) {
        const infrastructure_point_source& a = result.points[left].source;
        const infrastructure_point_source& b = result.points[right].source;
        if (a.priority != b.priority)
          return a.priority > b.priority;
        if (a.kind != b.kind)
          return a.kind < b.kind;
        return a.id < b.id;
      });
      double anchor_x = 0;
      double anchor_y = 0;
      for (const std::size_t index : indices)
        {
          anchor_x += std::get<0>(result.points[index].geographic_point);
          anchor_y += std::get<1>(result.points[index].geographic_point);
        }
      anchor_x /= indices.size();
      anchor_y /= indices.size();
      const std::vector<svg::point_2t> offsets
        = infrastructure_honeycomb_offsets(
            profile.marker_radius * 1.16, indices.size());
      const auto [minimum_x, maximum_x] = std::minmax_element(
        offsets.begin(), offsets.end(), [](const auto left, const auto right) {
          return std::get<0>(left) < std::get<0>(right);
        });
      const auto [minimum_y, maximum_y] = std::minmax_element(
        offsets.begin(), offsets.end(), [](const auto left, const auto right) {
          return std::get<1>(left) < std::get<1>(right);
        });
      const double lower_x = profile.marker_radius - std::get<0>(*minimum_x);
      const double upper_x = context.map_frame.width() - profile.marker_radius
        - std::get<0>(*maximum_x);
      const double lower_y = profile.marker_radius - std::get<1>(*minimum_y);
      const double upper_y = context.map_frame.height() - profile.marker_radius
        - std::get<1>(*maximum_y);
      infrastructure_require(lower_x <= upper_x && lower_y <= upper_y,
                             "infrastructure cluster does not fit map frame");
      anchor_x = std::clamp(anchor_x, lower_x, upper_x);
      anchor_y = std::clamp(anchor_y, lower_y, upper_y);
      for (std::size_t offset = 0; offset < indices.size(); ++offset)
        {
          projected_infrastructure_point& point = result.points[indices[offset]];
          point.display_point = {
            anchor_x + std::get<0>(offsets[offset]),
            anchor_y + std::get<1>(offsets[offset]),
          };
          point.cluster_size = indices.size();
        }
    }
  return result;
}

} // namespace cart0freak0::network_infrastructure_generation

#endif

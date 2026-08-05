// H3 parent clustering and projection-safe Izzi honeycomb placement.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_NETWORK_SWARM_CLUSTERING_H
#define CART0FREAK0_NETWORK_SWARM_CLUSTERING_H 1

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <tuple>
#include <utility>
#include <vector>

#include <a60-svg.h>

#include "network-swarm-data.h"
#include "projection-generation-common.h"

namespace cart0freak0::network_swarm_generation {

namespace generation = cart0freak0::generation;

struct cluster_key
{
  H3Index parent = 0;
  std::uint64_t projection_cell = 0;

  auto operator<=>(const cluster_key&) const = default;
};

struct projected_feature
{
  const swarm_feature* source = nullptr;
  svg::point_2t geographic_point {};
  svg::point_2t display_point {};
  H3Index parent = 0;
  std::uint64_t projection_cell = 0;
  std::size_t cluster_size = 0;
};

struct projected_layout
{
  std::vector<projected_feature> features;
  std::size_t cluster_count = 0;
  std::size_t largest_cluster = 0;
};

inline std::vector<svg::point_2t>
honeycomb_offsets(const double radius, const std::size_t count)
{
  network_swarm_require(count > 0
                    && count <= std::numeric_limits<svg::uint>::max(),
                  "network-swarm cluster has an invalid size");
  // Izzi intentionally works in floating-point Cartesian coordinates. Its
  // current hash and epsilon equality policies can admit numerically
  // equivalent centers through different BFS paths, so canonicalize the
  // returned centers onto the routine's own r/sqrt(3)r lattice. Asking for a
  // bounded surplus preserves use of its radial traversal while guaranteeing
  // one display cell per source feature.
  std::vector<svg::point_2t> result;
  for (std::size_t multiplier = 1; multiplier <= 16
       && result.size() < count; multiplier *= 2)
    {
      const std::size_t requested = std::min<std::size_t>(
        std::numeric_limits<svg::uint>::max(), count * multiplier + 7);
      const std::vector<svg::point_2t> candidates
        = svg::radiate_hexagon_honeycomb(
            {0, 0}, radius, static_cast<svg::uint>(requested), true);
      std::set<std::pair<long long, long long>> axial;
      result.clear();
      for (const auto& [x, y] : candidates)
        {
          network_swarm_require(std::isfinite(x) && std::isfinite(y),
                          "Izzi honeycomb returned a non-finite position");
          const long long column = std::llround(x / radius);
          const long long row = std::llround(
            y / (std::sqrt(3.0) * radius));
          if (axial.emplace(column, row).second)
            result.emplace_back(column * radius,
                                row * std::sqrt(3.0) * radius);
        }
    }
  network_swarm_require(result.size() >= count,
                  "Izzi honeycomb could not provide enough unique positions");
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
    {
      network_swarm_require(std::isfinite(x) && std::isfinite(y),
                      "Izzi honeycomb returned a non-finite position");
      unique.emplace(std::llround(x * 1e9), std::llround(y * 1e9));
    }
  network_swarm_require(unique.size() == result.size(),
                  "Izzi honeycomb returned duplicate positions");
  return result;
}

inline projected_layout
make_projected_layout(const generation::projection_context& context,
                      const swarm_dataset& dataset,
                      const network_swarm_profile& config)
{
  projected_layout result;
  result.features.reserve(dataset.features.size());
  std::map<cluster_key, std::vector<std::size_t>> clusters;
  for (const swarm_feature& feature : dataset.features)
    {
      const generation::geographic_point geographic {
        feature.latitude, feature.longitude,
      };
      const H3Index parent = h3_parent(
        feature.h3, static_cast<int>(config.parent_h3_resolution));
      const std::uint64_t cell = generation::projection_cell(
        context, geographic);
      const std::size_t index = result.features.size();
      const svg::point_2t projected = generation::project_point(
        context, geographic);
      result.features.push_back(
        {&feature, projected, projected, parent, cell, 0});
      clusters[{parent, cell}].push_back(index);
    }

  result.cluster_count = clusters.size();
  for (auto& [key, indices] : clusters)
    {
      static_cast<void>(key);
      result.largest_cluster = std::max(result.largest_cluster, indices.size());
      std::sort(indices.begin(), indices.end(), [&](const auto left,
                                                    const auto right) {
        const swarm_feature& a = *result.features[left].source;
        const swarm_feature& b = *result.features[right].source;
        if (a.downloaders.size != b.downloaders.size)
          return a.downloaders.size > b.downloaders.size;
        return a.h3 < b.h3;
      });

      double anchor_x = 0;
      double anchor_y = 0;
      for (const std::size_t index : indices)
        {
          anchor_x += std::get<0>(result.features[index].geographic_point);
          anchor_y += std::get<1>(result.features[index].geographic_point);
        }
      anchor_x /= indices.size();
      anchor_y /= indices.size();

      const std::vector<svg::point_2t> offsets = honeycomb_offsets(
        config.marker_radius, indices.size());
      const auto [minimum_x, maximum_x] = std::minmax_element(
        offsets.begin(), offsets.end(), [](const auto left, const auto right) {
          return std::get<0>(left) < std::get<0>(right);
        });
      const auto [minimum_y, maximum_y] = std::minmax_element(
        offsets.begin(), offsets.end(), [](const auto left, const auto right) {
          return std::get<1>(left) < std::get<1>(right);
        });
      const double lower_x
        = config.marker_radius - std::get<0>(*minimum_x);
      const double upper_x = context.map_frame.width() - config.marker_radius
        - std::get<0>(*maximum_x);
      const double lower_y
        = config.marker_radius - std::get<1>(*minimum_y);
      const double upper_y = context.map_frame.height() - config.marker_radius
        - std::get<1>(*maximum_y);
      network_swarm_require(lower_x <= upper_x && lower_y <= upper_y,
                      "network-swarm honeycomb cluster does not fit the "
                      "projection frame");
      anchor_x = std::clamp(anchor_x, lower_x, upper_x);
      anchor_y = std::clamp(anchor_y, lower_y, upper_y);
      for (std::size_t offset_index = 0; offset_index < indices.size();
           ++offset_index)
        {
          projected_feature& feature = result.features[indices[offset_index]];
          feature.display_point = {
            anchor_x + std::get<0>(offsets[offset_index]),
            anchor_y + std::get<1>(offsets[offset_index]),
          };
          feature.cluster_size = indices.size();
        }
    }
  return result;
}

} // namespace cart0freak0::network_swarm_generation

#endif

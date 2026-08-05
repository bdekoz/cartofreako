#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <vector>

#include "network-swarm-clustering.h"

namespace network_swarm = cart0freak0::network_swarm_generation;
namespace generation = cart0freak0::generation;

int
main()
{
  const network_swarm::network_swarm_profile profile
    = network_swarm::load_network_swarm_profile(
      "assets.static/network-swarm/network-swarm-profile.json");
  assert(profile.source_h3_resolution == 5);
  assert(profile.parent_h3_resolution == 3);
  assert(profile.maximum_labels == 40);
  assert(profile.show_tethers);
  assert(profile.archive_sha256
         == "ec51be8cafcdc2e009874e2aebd84927dc5c3d87ec589c0fe5d8d1df0818e0b8");
  assert(profile.geojson_sha256
         == "9fbd453d174df834208718e110396c5a22bff4312aeeff3e42d0175510b0ff69");

  const network_swarm::swarm_dataset dataset
    = network_swarm::load_swarm_dataset(
      "assets.static/network-swarm/.prepared/"
      "house-of-the-dragon-301-cumulative-aggregate.geojson");
  assert(dataset.id == "house-of-the-dragon-301");
  assert(dataset.datestamp == "2026-06-22-to-2026-07-26");
  assert(dataset.duration_type == "cumulative");
  assert(dataset.duration_index == 0);
  assert(dataset.data_version == "20260701");
  assert(dataset.h3_resolution == 5);
  assert(dataset.minimum_size == 3);
  assert(dataset.reported_swarm_features_size == 1644284);
  assert(dataset.btiha_size == 411);
  assert(dataset.features.size() == 23825);

  const network_swarm::swarm_feature& first = dataset.features.front();
  assert(first.country_code == "CHN");
  assert(first.city == "Nanjing");
  assert(first.h3 == 599833147210727423ULL);
  assert(first.downloaders.size == 806158);
  assert(first.downloaders.mobile == 1257);
  assert(first.downloaders.vpn == 10061);

  std::uint64_t total = 0;
  bool overlapping_categories = false;
  std::map<H3Index, std::size_t> parent_sizes;
  for (const network_swarm::swarm_feature& feature : dataset.features)
    {
      total += feature.downloaders.size;
      const std::uint64_t specialized = feature.downloaders.mobile
        + feature.downloaders.satellite + feature.downloaders.tor
        + feature.downloaders.tor_exit_nodes + feature.downloaders.vpn
        + feature.downloaders.relay + feature.downloaders.proxy
        + feature.downloaders.hosting + feature.downloaders.service;
      overlapping_categories = overlapping_categories
        || specialized > feature.downloaders.size;
      ++parent_sizes[network_swarm::h3_parent(feature.h3, 3)];
    }
  assert(total == 19187402);
  assert(overlapping_categories);
  assert(parent_sizes.size() == 4404);
  assert(std::max_element(
           parent_sizes.begin(), parent_sizes.end(),
           [](const auto& left, const auto& right) {
             return left.second < right.second;
           })->second == 48);

  for (std::size_t count = 1; count <= 48; ++count)
    {
      const std::vector<svg::point_2t> offsets
        = network_swarm::honeycomb_offsets(profile.marker_radius, count);
      assert(offsets.size() == count);
      assert(std::hypot(std::get<0>(offsets.front()),
                        std::get<1>(offsets.front())) < 1e-12);
      std::set<std::pair<long long, long long>> unique;
      for (const auto& [x, y] : offsets)
        unique.emplace(std::llround(x * 1e9), std::llround(y * 1e9));
      assert(unique.size() == count);
    }

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-network-swarm-" + std::string(name));
      const network_swarm::projected_layout layout
        = network_swarm::make_projected_layout(
          context, dataset, profile);
      assert(layout.features.size() == dataset.features.size());
      assert(layout.cluster_count >= parent_sizes.size());
      assert(layout.largest_cluster <= 48);
      if (name == "cahill-keyes")
        assert(layout.cluster_count == 4418);
      for (const network_swarm::projected_feature& feature : layout.features)
        {
          const auto [x, y] = feature.display_point;
          assert(std::isfinite(x) && std::isfinite(y));
          assert(x >= 0 && x <= context.map_frame.width());
          assert(y >= 0 && y <= context.map_frame.height());
        }
    }

  assert(network_swarm::scaled_log_opacity(0, 100, 0.2) == 0);
  assert(network_swarm::scaled_log_opacity(1, 100, 0.2) > 0.2);
  assert(network_swarm::scaled_log_opacity(1000, 100, 0.2) == 1);
}

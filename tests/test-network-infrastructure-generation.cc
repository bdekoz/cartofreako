#include <array>
#include <cassert>
#include <cmath>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "network-infrastructure-generation.h"

namespace infrastructure
  = cart0freak0::network_infrastructure_generation;
namespace generation = cart0freak0::generation;

int
main()
{
  const infrastructure::infrastructure_profile sites
    = infrastructure::load_infrastructure_profile(
      "assets.static/network-infrastructure/"
      "network-infrastructure-sites-profile.json");
  const infrastructure::infrastructure_profile topology
    = infrastructure::load_infrastructure_profile(
      "assets.static/network-infrastructure/"
      "network-infrastructure-topology-profile.json");
  assert(sites.product == infrastructure::infrastructure_product::sites);
  assert(!sites.topology_opt_in);
  assert(sites.include_cloud_sites && !sites.include_submarine_cables);
  assert(sites.cloud.expected_layers == 19);
  assert(sites.cloud.expected_records == 15113);
  assert(sites.cloud.expected_located == 1003);
  assert(topology.product
         == infrastructure::infrastructure_product::topology);
  assert(topology.topology_opt_in);
  assert(topology.generated_artifact_license.find("CC BY-NC-SA 3.0")
         != std::string::npos);
  assert(topology.include_submarine_cables
         && topology.include_exchange_membership);

  const auto dateline = infrastructure::split_at_dateline(
    {{12, 170}, {16, -170}});
  assert(dateline.size() == 2);
  assert(dateline.front().back().longitude == 180);
  assert(dateline.back().front().longitude == -180);
  const auto dense = infrastructure::densify_path({{0, 0}, {0, 10}}, 2);
  assert(dense.size() == 6);

  for (std::size_t count = 1; count <= 64; ++count)
    {
      const std::vector<svg::point_2t> offsets
        = infrastructure::infrastructure_honeycomb_offsets(0.035, count);
      assert(offsets.size() == count);
      std::set<std::pair<long long, long long>> unique;
      for (const auto& [x, y] : offsets)
        {
          assert(std::isfinite(x) && std::isfinite(y));
          unique.emplace(std::llround(x * 1e9), std::llround(y * 1e9));
        }
      assert(unique.size() == count);
    }

  infrastructure::infrastructure_dataset dataset;
  dataset.cloud.record_count = 2;
  dataset.cloud.sites = {
    {"cloud:edge:a", "Example", "edge", "edge_pop", "Alpha",
     "Alpha City", "Exampleland", "provider_declared", "operational",
     "metro", {37.77, -122.42}},
    {"cloud:dc:b", "Example", "compute", "data_center", "Beta",
     "Beta City", "Exampleland", "provider_declared", "operational",
     "facility", {37.771, -122.421}},
  };
  dataset.cables.systems = {
    {"example-cable", "Example Cable", false, 2020,
     {"example-landing"}},
  };
  dataset.cables.routes = {
    {"example-cable", "Example Cable", "example-cable-0", "#00aacc",
     false, {{{37.77, -122.42}, {35.68, 139.69}}}},
  };
  dataset.cables.landings = {
    {"example-landing", "Example Landing", false, 1, {37.77, -122.42}},
  };
  dataset.exchanges.buildings = {
    {"1", "alpha", "Alpha Facility", "exampleland", "alpha",
     {37.77, -122.42}, {{"example-ix", "Example IX"}}},
    {"2", "beta", "Beta Facility", "exampleland", "beta",
     {37.78, -122.41}, {{"example-ix", "Example IX"}}},
  };
  dataset.exchanges.exchanges = {
    {"example-ix", "Example IX", {0, 1}},
  };
  dataset.exchanges.membership_count = 2;

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-network-infrastructure-" + std::string(name));
      const infrastructure::infrastructure_point_layout layout
        = infrastructure::make_infrastructure_point_layout(
          context, dataset, topology);
      assert(layout.points.size() == 5);
      assert(layout.cluster_count > 0);
      for (const infrastructure::projected_infrastructure_point& point
           : layout.points)
        {
          const auto [x, y] = point.display_point;
          assert(std::isfinite(x) && std::isfinite(y));
          assert(x >= 0 && x <= context.map_frame.width());
          assert(y >= 0 && y <= context.map_frame.height());
        }
      const std::string route = infrastructure::project_open_path(
        context, dataset.cables.routes.front().paths.front());
      assert(!route.empty());
    }

  assert(infrastructure::multi_building_exchange_count(dataset.exchanges) == 1);
  infrastructure::exchange_dataset colocated;
  colocated.buildings = {
    {"3", "gamma", "Gamma A", "exampleland", "gamma",
     {45.4789921, 9.1026941}, {{"colocated-ix", "Co-located IX"}}},
    {"4", "delta", "Gamma B", "exampleland", "gamma",
     {45.4789921, 9.1026941}, {{"colocated-ix", "Co-located IX"}}},
  };
  colocated.exchanges = {{"colocated-ix", "Co-located IX", {0, 1}}};
  assert(!infrastructure::exchange_has_distinct_building_points(
    colocated, colocated.exchanges.front()));
  assert(infrastructure::colocated_multi_building_exchange_count(colocated)
         == 1);
  const generation::geographic_point hub = infrastructure::spherical_centroid(
    dataset.exchanges, dataset.exchanges.exchanges.front());
  assert(std::isfinite(hub.latitude) && std::isfinite(hub.longitude));
  assert(infrastructure::xml_escape("a&\"<\v") == "a&amp;&quot;&lt; ");
}

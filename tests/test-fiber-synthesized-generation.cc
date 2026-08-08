#include <array>
#include <cassert>
#include <string_view>

#include "fiber-synthesized-generation.h"

namespace fiber = cart0freak0::fiber_synthesized_generation;
namespace generation = cart0freak0::generation;

int
main()
{
  const fiber::fiber_dataset dataset = fiber::load_fiber_dataset(
    "assets.static/fiber-synthesized");
  assert(dataset.profile.default_snapshot == "v3.20260805");
  assert(dataset.profile.older_snapshot == "v3.2022");
  assert(dataset.profile.comparison_systems == 746);
  assert(dataset.profile.expected_route_observations == 1250);
  assert(dataset.profile.expected_landing_observations == 3358);
  assert(dataset.profile.stable_id_matches == 456);
  assert(dataset.profile.normalized_name_matches == 3);
  assert(dataset.profile.landing_set_matches == 18);
  assert(dataset.profile.unmatched_systems == 269);
  assert(dataset.routes.size() == 767);
  assert(dataset.current_routes == 718);
  assert(dataset.historical_routes == 49);
  assert(dataset.planned_routes == 91);
  assert(dataset.planned_to_active_routes == 44);
  assert(dataset.current_only_routes == 223);
  assert(dataset.landings.size() == 2037);
  assert(dataset.current_landings == 1922);
  assert(dataset.historical_landings == 115);
  assert(dataset.profile.routes_sha256
    == "1a414af0bf940edd8b48e56af9a36b8b108a168806a45c8046de1c5015e20c46");
  assert(dataset.profile.landings_sha256
    == "c8b445e6d5760a22131f2ff927997b39166ab9571d27ad5bf40fbe6ddfe03ae0");

  constexpr std::array projection_names {
    "cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x",
    "voronoi",
  };
  for (const std::string_view name : projection_names)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(name);
      const generation::projection_context context(
        spec, "test-fiber-synthesized-" + std::string(name));
      const auto projected = generation::project_point(
        context, dataset.landings.front().point);
      assert(std::get<0>(projected) >= 0
        && std::get<0>(projected) <= context.map_frame.width());
      assert(std::get<1>(projected) >= 0
        && std::get<1>(projected) <= context.map_frame.height());
      assert(!fiber::infrastructure::project_open_path(
        context, dataset.routes.front().paths.front()).empty());
    }
}

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "projection-generation-common.h"

namespace {

namespace generation = cart0freak0::generation;

double
maximum_segment(const std::vector<svg::vrange>& paths)
{
  double result = 0;
  for (const svg::vrange& path : paths)
    for (std::size_t index = 1; index < path.size(); ++index)
      result = std::max(
        result,
        generation::point_distance(path[index - 1], path[index]));
  return result;
}

} // namespace

int
main()
{
  using generation::geographic_point;
  const generation::projection_context context(
    generation::find_projection_spec("myriahedral"), "");

  // The point transform canonicalizes +180 to -180. Cell classification must
  // make the same choice or an exact antimeridian endpoint can be connected
  // to the distant planar copy selected by the noncanonical face.
  constexpr geographic_point east_antimeridian {68.9810503210001, 180};
  constexpr geographic_point west_antimeridian {68.9810503210001, -180};
  assert(generation::projection_cell(context, east_antimeridian)
         == generation::projection_cell(context, west_antimeridian));
  const std::vector antimeridian_source {
    east_antimeridian,
    geographic_point {68.9986, 179.846},
  };
  const auto antimeridian_paths
    = generation::project_path(context, antimeridian_source, false);
  assert(!antimeridian_paths.empty());
  assert(maximum_segment(antimeridian_paths) < 0.75);

  // This simplified Porcupine River edge crosses faces 377 -> 369 -> 355.
  // Faces 377 and 369 share a retained hinge; 369 and 355 are separated by a
  // cut. Processing only the first transition creates a 9.62-unit chord.
  constexpr geographic_point porcupine_left {
    66.3432070984317, -138.731005859375,
  };
  constexpr geographic_point porcupine_right {
    66.4821231140566, -138.64189453125,
  };
  assert(generation::projection_cell(context, porcupine_left) == 377);
  assert(generation::projection_cell(context, porcupine_right) == 355);
  const geographic_point porcupine_middle
    = generation::interpolate(porcupine_left, porcupine_right, 0.5);
  assert(generation::projection_cell(context, porcupine_middle) == 369);

  const auto porcupine_paths = generation::project_path(
    context, std::vector {porcupine_left, porcupine_right}, false);
  assert(porcupine_paths.size() == 2);
  assert(maximum_segment(porcupine_paths) < 0.75);
}

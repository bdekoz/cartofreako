#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cmath>
#include <limits>
#include <string_view>
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

  const generation::projection_context cahill_keyes_context(
    generation::find_projection_spec("cahill-keyes"), "");

  // The classifier must make the same one-sided seam choice as the native
  // forward projection, including for the immediately adjacent floating-point
  // values found by transition bisection.
  struct cahill_keyes_seam
  {
    double longitude;
    std::uint64_t preceding_cell;
    std::uint64_t following_cell;
  };
  constexpr std::array cahill_keyes_seams {
    cahill_keyes_seam {-111, 0, 1},
    cahill_keyes_seam {-21, 1, 2},
    cahill_keyes_seam {69, 2, 3},
    cahill_keyes_seam {159, 3, 0},
  };
  for (const cahill_keyes_seam seam : cahill_keyes_seams)
    {
      const double before = std::nextafter(
        seam.longitude, -std::numeric_limits<double>::infinity());
      const double after = std::nextafter(
        seam.longitude, std::numeric_limits<double>::infinity());
      assert(generation::cahill_keyes_cell({0, before})
             == seam.preceding_cell);
      assert(generation::cahill_keyes_cell({0, seam.longitude})
             == seam.following_cell);
      assert(generation::cahill_keyes_cell({0, after})
             == seam.following_cell);
      assert(generation::cahill_keyes_cell({-1, before})
             == seam.preceding_cell + 4);
      assert(generation::cahill_keyes_cell({-1, seam.longitude})
             == seam.following_cell + 4);
    }

  // A sampled celestial equator crosses the registered 159-degree cut.  It
  // must leave and re-enter at opposite frame edges instead of retaining the
  // almost-full-width chord between the two octant copies.
  std::vector<geographic_point> equator;
  for (int longitude = 180; longitude >= -180; --longitude)
    equator.push_back({0, static_cast<double>(longitude)});
  const auto equator_paths = generation::project_path(
    cahill_keyes_context, equator, false);
  assert(equator_paths.size() >= 2);
  bool found_frame_fold = false;
  for (std::size_t index = 1; index < equator_paths.size(); ++index)
    {
      const svg::point_2t exit = equator_paths[index - 1].back();
      const svg::point_2t entry = equator_paths[index].front();
      if (std::abs(std::get<0>(exit)) < 1e-12
          && std::abs(std::get<0>(entry)
                      - cahill_keyes_context.map_frame.width()) < 1e-12
          && std::abs(std::get<1>(exit) - std::get<1>(entry)) < 1e-12)
        found_frame_fold = true;
    }
  assert(found_frame_fold);
  assert(maximum_segment(equator_paths)
         < cahill_keyes_context.map_frame.width() / 4);

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

  // Dymaxion participates in the shared generator dispatch with its exact
  // frame, public projection type, output tag, and antimeridian tie rule.
  const generation::projection_spec& dymaxion_spec
    = generation::find_projection_spec("dymaxion");
  assert(dymaxion_spec.kind == generation::projection_kind::dymaxion);
  assert(dymaxion_spec.output_tag == "dymaxion-44-20.78461");
  const generation::projection_context dymaxion_context(dymaxion_spec, "");
  assert(generation::has_valid_frame(
    dymaxion_spec, dymaxion_context.map_frame));
  assert(std::holds_alternative<a60::carto::dymaxionproj>(
    dymaxion_context.projection));
  const svg::point_2t fuller_point = generation::project_point(
    dymaxion_context, geographic_point {40.7128, -74.0060});
  assert(std::get<0>(fuller_point) >= 0);
  assert(std::get<0>(fuller_point) <= dymaxion_context.map_frame.width());
  assert(std::get<1>(fuller_point) >= 0);
  assert(std::get<1>(fuller_point) <= dymaxion_context.map_frame.height());
  assert(generation::projection_cell(
           dymaxion_context, geographic_point {12.5, -180})
         == generation::projection_cell(
           dymaxion_context, geographic_point {12.5, 180}));

  // The five exploratory Myriahedral perspectives have immutable, complete
  // generation metadata and use their own cut trees and registrations.
  namespace myria = cart0freak0::myriahedral_generation;
  assert(myria::perspectives.size() == 6);
  const myria::perspective_metadata& reference
    = myria::metadata(myria::perspective::reference);
  assert(reference.depth == 5);
  assert(reference.sigma == 0.7);
  assert(reference.legacy_wlat == 0.5);
  assert(reference.legacy_wlon == 0.1);
  assert(reference.legacy_clat == -60);
  assert(reference.legacy_clon == -65);
  assert(reference.rotation_degrees == 335);

  constexpr std::array<std::string_view, 5> perspective_arguments {
    "myriahedral-americas",
    "myriahedral-atlantic",
    "myriahedral-afro-eur-asia",
    "myriahedral-pacific",
    "myriahedral-antarctic",
  };
  std::array<svg::point_2t, perspective_arguments.size()> registrations {};
  for (std::size_t index = 0; index < perspective_arguments.size(); ++index)
    {
      const generation::projection_spec& spec
        = generation::find_projection_spec(perspective_arguments[index]);
      assert(spec.kind == generation::projection_kind::myriahedral);
      const myria::perspective_metadata& metadata
        = myria::metadata(spec.myriahedral_perspective);
      assert(metadata.argument == perspective_arguments[index]);
      assert(metadata.output_tag == spec.output_tag);
      assert(metadata.depth == 5);
      assert(metadata.alpha == 1);
      assert(metadata.parent_hex != nullptr);
      assert(metadata.parent_hex_sha256.size() == 64);
      assert(metadata.tree_sha256.size() == 64);

      const generation::projection_context alternate(spec, "");
      registrations[index] = generation::project_point(
        alternate, generation::geographic_point {12.5, -7.25});
      static_cast<void>(generation::project_point(
        alternate, generation::geographic_point {70, 160}));
      static_cast<void>(generation::project_point(
        alternate, generation::geographic_point {-75, -60}));
      const auto& selected = std::get<a60::carto::myriaproj>(
        alternate.projection).layout();
      assert(&selected == &myria::layout(spec.myriahedral_perspective));
      assert(std::abs(selected.minimum_x - metadata.minimum_x) < 1e-12);
      assert(std::abs(selected.minimum_y - metadata.minimum_y) < 1e-12);
      assert(std::abs(selected.maximum_x - metadata.maximum_x) < 1e-12);
      assert(std::abs(selected.maximum_y - metadata.maximum_y) < 1e-12);
    }
  for (std::size_t index = 1; index < registrations.size(); ++index)
    assert(generation::point_distance(
             registrations[index - 1], registrations[index]) > 0.01);
}

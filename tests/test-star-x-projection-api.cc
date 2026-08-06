#include <array>
#include <cassert>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <vector>

namespace a60 {

using point_2t = std::tuple<double, double>;
using string = std::string;
using vd = std::vector<double>;

namespace carto {

struct frame
{
  struct area
  {
    double _M_width;
    double _M_height;
  };

  area frame_area;
  double moriginx;
  double moriginy;

  frame(const area dimensions, const double x = 0, const double y = 0)
  : frame_area(dimensions), moriginx(x), moriginy(y)
  { }

  frame(const double width, const double height,
        const double x = 0, const double y = 0)
  : frame({width, height}, x, y)
  { }

  double width() const { return frame_area._M_width; }
  double height() const { return frame_area._M_height; }
};

inline const frame pck_1x1080 {1920, 960};
inline const frame pck_2x1080 {3840, 1920};
inline const frame pck_7x {4984, 2492};
inline const frame pck_3x {2004, 1002};
inline const frame f44x22h {4224, 2112};

} // namespace carto

namespace io {

struct resources
{
  string data;
};

inline resources&
get_run_time_resources()
{
  static resources value;
  return value;
}

inline string
end_path(const string& value)
{ return value.empty() || value.back() == '/' ? value : value + '/'; }

} // namespace io

} // namespace a60

#include "a60-carto-projection.h"
#include "cart0freak0-star-x-functions.h"

namespace {

struct expected_point
{
  double latitude;
  double longitude;
  double x;
  double y;
};

void
expect_invalid(const a60::carto::projection_api& projection,
               const double latitude, const double longitude)
{
  bool rejected = false;
  try
    {
      static_cast<void>(
        projection.meridians_to_point_2d(latitude, longitude));
    }
  catch (const std::invalid_argument&)
    {
      rejected = true;
    }
  assert(rejected);
}

bool
is_second_group(const double longitude)
{
  const double adjusted
    = a60::carto::cahill_keyes_registered_longitude(longitude);
  return adjusted >= -20 && adjusted < 160;
}

bool
near_point(const a60::point_2t left, const a60::point_2t right,
           const double tolerance)
{
  return std::hypot(std::get<0>(right) - std::get<0>(left),
                    std::get<1>(right) - std::get<1>(left)) <= tolerance;
}

} // namespace

int
main()
{
  using namespace a60::carto;
  static_assert(std::is_base_of_v<projection_api, starxproj>);

  // This reference frame is the historic 17-by-22 Engineering C carrier
  // at 96 DPI. The values independently apply the original edge-to-edge
  // Star-X rigid transforms to the Perl-derived 2112-by-1056 Cahill-Keyes
  // anchors used by augment_carto_geo_specific. The default configurable
  // gap then moves each group 108 pixels toward the center, the
  // scale-equivalent of 2.25 units in the generated 34-by-44 frame. The
  // second transform enlarges the assembled result 120 percent about the
  // center of the page.
  const frame reference_frame {1632, 2112};
  const starxproj reference = make_star_x_projection(
    reference_frame, "star-x.svg");
  const double reference_group_shift
    = star_x_default_group_shift_ratio * reference_frame.height();
  const auto enlarge_x = [&reference_frame](const double x)
  {
    return reference_frame.width() / 2
           + star_x_default_enlargement_factor
               * (x - reference_frame.width() / 2);
  };
  const auto enlarge_y = [&reference_frame](const double y)
  {
    return reference_frame.height() / 2
           + star_x_default_enlargement_factor
               * (y - reference_frame.height() / 2);
  };
  const projection_api& api = reference;
  assert(std::abs(reference_group_shift - 108) < 1e-12);
  assert(std::abs(reference.group_gap_ratio()
                  - star_x_default_group_gap_ratio) < 1e-12);
  assert(std::abs(reference.enlargement_factor()
                  - star_x_default_enlargement_factor) < 1e-12);
  assert(reference.pmode == star_x);
  assert(reference.pframe.width() == reference_frame.width());
  assert(reference.pframe.height() == reference_frame.height());

  constexpr std::array specific_locations {
    expected_point {0, 0, 1202.456203484586922, 598.700122045765966},
    expected_point {89.9, 0, 841.260247411951013, 941.956075719814976},
    expected_point {80, 0, 885.240741195116925, 910.002376583669957},
    expected_point {-89.9, 0, 1319.126601330249969, 114.267271505629992},
    expected_point {-80, 0, 1313.444133025046995, 168.332345960908015},
    expected_point {0, 179.9, 429.033562334226986, 1513.005294112376987},
    expected_point {0, 170, 383.458491085170976, 1477.406020019109974},
    expected_point {0, -179.9, 430.054030696599000, 1513.594461796091082},
    expected_point {0, -170, 480.567214633991000, 1542.758262139969929},
    expected_point {-80, -20, 1332.468415131168967, 167.002038563712972},
    expected_point {-20, -19, 1333.648297958563035, 515.489913867786981},
    expected_point {-20, -21, 1344.000000000000000, 515.670380062186041},
    expected_point {-20, -23, 1333.648297958563035, 1596.510086132213019},
    expected_point {-56, -19, 1338.531271084967102, 305.697478836093978},
    expected_point {-56, -23, 1338.531271084967102, 1806.302521163906022},
    expected_point {40.7128, -74.006, 946.943678228346016, 1411.919887450434089},
    expected_point {34.0549, -118.2426, 785.483918061388977, 1487.997343354652912},
    expected_point {48.8575, 2.3514, 1007.561690781366906, 789.866212890070074},
    expected_point {-29.8587, 31.0218, 1132.771433954791974, 376.005341660713952},
    expected_point {28.7041, 77.1025, 778.958763073939963, 593.527682091115025},
    expected_point {35.6895, 139.6917, 560.096134613120967, 747.692146271549063},
    expected_point {-33.8688, 151.2093, 320.911134515742106, 432.805144226109974},
    expected_point {21.1444, -157.0226, 603.533804960986004, 1484.832454891035013},
    expected_point {-23.5558, -46.6396, 1223.050471917684945, 1647.939479527904950},
    expected_point {64.147, -21.9408, 977.367705678395964, 1222.274610083414927},
    expected_point {-18.1266, 178.4399, 388.434953967515980, 1604.837680253911003},
    expected_point {-62.2001, 58.9642, 1184.159168233798937, 189.839193562169044},
  };

  for (const auto& expected : specific_locations)
    {
      const auto [x, y] = api.meridians_to_point_2d(
        expected.latitude, expected.longitude);
      const double placed_y
        = expected.y
          + (is_second_group(expected.longitude)
               ? reference_group_shift : -reference_group_shift);
      assert(std::isfinite(x) && std::isfinite(y));
      assert(std::abs(x - enlarge_x(expected.x)) < 1e-9);
      assert(std::abs(y - enlarge_y(placed_y)) < 1e-9);
      assert(x >= 0 && x <= reference_frame.width());
      assert(y >= 0 && y <= reference_frame.height());
    }
  assert(std::abs(reference.longitude_zero_x
                  - enlarge_x(specific_locations.front().x)) < 1e-9);
  assert(std::abs(reference.latitude_zero_y
                  - enlarge_y(specific_locations.front().y
                              + reference_group_shift)) < 1e-9);

  // A zero carrier gap reproduces the previous edge-to-edge placement.
  // The default signed gap is -4.5 inches in a 34-by-44 frame, split
  // symmetrically into the requested 2.25-inch inward translations.
  const star_x_layout adjacent_layout {
    .group_gap_ratio = 0,
    .enlargement_factor = 1,
  };
  const starxproj adjacent = make_star_x_projection(
    reference_frame, "adjacent-star-x.svg", adjacent_layout);
  assert(adjacent.group_gap_ratio() == 0);
  assert(adjacent.enlargement_factor() == 1);
  for (const auto& expected : specific_locations)
    {
      const auto [adjacent_x, adjacent_y]
        = adjacent.meridians_to_point_2d(
            expected.latitude, expected.longitude);
      const auto [default_x, default_y]
        = reference.meridians_to_point_2d(
            expected.latitude, expected.longitude);
      const double direction
        = is_second_group(expected.longitude) ? 1 : -1;
      assert(std::abs(adjacent_x - expected.x) < 1e-9);
      assert(std::abs(adjacent_y - expected.y) < 1e-9);
      assert(std::abs(default_x - enlarge_x(adjacent_x)) < 1e-9);
      assert(std::abs(default_y
                      - enlarge_y(adjacent_y
                                  + direction * reference_group_shift))
             < 1e-9);
    }
  assert(star_x_default_group_shift_ratio * 44 == 2.25);
  assert(star_x_default_group_gap_ratio * 44 == -4.5);
  assert(star_x_default_enlargement_factor == 1.2);

  // The enlargement is independently configurable and remains centered.
  const starxproj enlarged = make_star_x_projection(
    reference_frame, "enlarged-star-x.svg",
    star_x_layout {.group_gap_ratio = 0, .enlargement_factor = 1.1});
  for (const auto& expected : specific_locations)
    {
      const auto [x, y]
        = enlarged.meridians_to_point_2d(
            expected.latitude, expected.longitude);
      assert(std::abs(x - (reference_frame.width() / 2
                           + 1.1 * (expected.x
                                    - reference_frame.width() / 2)))
             < 1e-9);
      assert(std::abs(y - (reference_frame.height() / 2
                           + 1.1 * (expected.y
                                    - reference_frame.height() / 2)))
             < 1e-9);
    }

  // Verify the defining assembly independently against the ordinary
  // Cahill-Keyes API. Spatial face slots 1-4 occupy the source's left
  // half; slots 5-8 occupy its right half and receive the 180-degree
  // upper-group transform.
  const ckproj cahill_keyes_source(frame {2112, 1056});
  constexpr double group_side = 1056;
  constexpr double side_margin = 288;
  for (int latitude = -90; latitude <= 90; latitude += 5)
    for (int longitude = -180; longitude <= 180; longitude += 5)
      {
        const auto [source_x, source_y]
          = cahill_keyes_source.meridians_to_point_2d(
              latitude, longitude);
        const double adjusted
          = cahill_keyes_registered_longitude(longitude);
        const bool second_group = adjusted >= -20 && adjusted < 160;
        const double assembled_x
          = second_group
              ? side_margin + 2 * group_side - source_x
              : side_margin + source_x;
        const double assembled_y
          = second_group
              ? group_side - source_y + reference_group_shift
              : group_side + source_y - reference_group_shift;
        const auto [x, y]
          = reference.meridians_to_point_2d(latitude, longitude);
        assert(std::abs(x - enlarge_x(assembled_x)) < 1e-9);
        assert(std::abs(y - enlarge_y(assembled_y)) < 1e-9);

        const auto assembled = star_x_detail::project_to_normalized_map(
          latitude, longitude);
        assert((assembled.group == star_x_detail::face_group::two)
               == second_group);
      }

  // Northern polar copies meet around the central horizontal axis; the
  // southern polar copies remain at the two outer ends of the X.
  const auto [north_lower_x, north_lower_y]
    = reference.meridians_to_point_2d(90, -156);
  const auto [north_upper_x, north_upper_y]
    = reference.meridians_to_point_2d(90, 24);
  static_cast<void>(north_lower_x);
  static_cast<void>(north_upper_x);
  assert(north_lower_y > reference_frame.height() / 2);
  assert(north_upper_y < reference_frame.height() / 2);
  assert(std::abs(north_lower_y - reference_frame.height() / 2)
         < reference_frame.height() / 10);
  assert(std::abs(north_upper_y - reference_frame.height() / 2)
         < reference_frame.height() / 10);
  const auto [south_lower_x, south_lower_y]
    = reference.meridians_to_point_2d(-90, -156);
  const auto [south_upper_x, south_upper_y]
    = reference.meridians_to_point_2d(-90, 24);
  static_cast<void>(south_lower_x);
  static_cast<void>(south_upper_x);
  assert(south_lower_y > 7 * reference_frame.height() / 8);
  assert(south_upper_y < reference_frame.height() / 8);

  // Every integral geographic coordinate is finite and inside the frame.
  for (int latitude = -90; latitude <= 90; ++latitude)
    for (int longitude = -180; longitude <= 180; ++longitude)
      {
        const auto [x, y]
          = reference.meridians_to_point_2d(latitude, longitude);
        assert(std::isfinite(x) && std::isfinite(y));
        assert(x >= 0 && x <= reference_frame.width());
        assert(y >= 0 && y <= reference_frame.height());
      }

  const frame::area large_dimensions {5100, 6600};
  const std::array variable_frames {
    frame {17, 22},
    frame {34, 44},
    frame {reference_frame.frame_area},
    frame {large_dimensions},
    frame {star_x_width_to_height_ratio * 617.25, 617.25},
  };
  for (const frame& map_frame : variable_frames)
    {
      assert(is_star_x_frame(map_frame));
      const auto projection = make_star_x_projection(
        map_frame, "variable-star-x.svg");
      assert(projection.pframe.width() == map_frame.width());
      assert(projection.pframe.height() == map_frame.height());
      assert(projection.pframe.moriginx == 0);
      assert(projection.pframe.moriginy == 0);

      const double factor = map_frame.height() / reference_frame.height();
      const double tolerance = 1e-9 * std::max(1.0, factor);
      for (const auto& expected : specific_locations)
        {
          const auto [x, y] = projection.meridians_to_point_2d(
            expected.latitude, expected.longitude);
          const double placed_y
            = expected.y
              + (is_second_group(expected.longitude)
                   ? reference_group_shift : -reference_group_shift);
          assert(std::abs(x - enlarge_x(expected.x) * factor) < tolerance);
          assert(std::abs(y - enlarge_y(placed_y) * factor) < tolerance);
          assert(x >= 0 && x <= map_frame.width());
          assert(y >= 0 && y <= map_frame.height());
        }
    }

  // Star-X path routing follows the assembled net's actual topology. The
  // -21/159-degree boundaries always cross between the lower and rotated
  // upper square groups. The -111/69-degree boundaries either retain a
  // coincident hinge or fold between two separated copies within one group.
  namespace star_path = star_x_path_detail;
  struct path_seam
  {
    double longitude;
    star_path::edge_kind folded_kind;
  };
  constexpr std::array path_seams {
    path_seam {-111, star_path::edge_kind::intra_group_fold},
    path_seam {-21, star_path::edge_kind::inter_group_fold},
    path_seam {69, star_path::edge_kind::intra_group_fold},
    path_seam {159, star_path::edge_kind::inter_group_fold},
  };
  const double path_tolerance = reference_frame.height() * 1e-10;
  assert(star_path::classify_edge(
           reference, 1, 2, {17, 22}, {17, 22})
         == star_path::edge_kind::inter_group_fold);
  assert(star_path::classify_edge(
           reference, 0, 1, {17, 22}, {17, 22})
         == star_path::edge_kind::retained_hinge);
  for (const path_seam seam : path_seams)
    for (const double latitude : {-30.0, 80.0})
      {
        const star_path::geographic_coordinate west {
          latitude, seam.longitude - 1,
        };
        const star_path::geographic_coordinate east {
          latitude, seam.longitude + 1,
        };
        const auto west_to_east
          = star_path::first_edge_transition(reference, west, east);
        const auto east_to_west
          = star_path::first_edge_transition(reference, east, west);
        assert(west_to_east && east_to_west);
        assert(west_to_east->is_fold() && east_to_west->is_fold());
        assert(west_to_east->kind == seam.folded_kind);
        assert(east_to_west->kind == seam.folded_kind);
        assert(near_point(west_to_east->exit, east_to_west->entry,
                          path_tolerance));
        assert(near_point(west_to_east->entry, east_to_west->exit,
                          path_tolerance));
        assert(star_path::path_cell(west_to_east->geographic_entry)
               != star_path::path_cell(west));
        assert(star_path::path_cell(east_to_west->geographic_entry)
               != star_path::path_cell(east));
      }

  for (const double seam : {-111.0, 69.0})
    {
      const auto hinge = star_path::first_edge_transition(
        reference, {40, seam - 1}, {40, seam + 1});
      assert(hinge);
      assert(!hinge->is_fold());
      assert(hinge->kind == star_path::edge_kind::retained_hinge);
      assert(near_point(hinge->exit, hinge->entry, path_tolerance));
    }
  for (const double longitude
       : star_x_detail::quadrant_center_longitudes)
    {
      const auto equatorial_hinge = star_path::first_edge_transition(
        reference, {-1, longitude}, {1, longitude});
      assert(equatorial_hinge);
      assert(!equatorial_hinge->is_fold());
      assert(equatorial_hinge->kind
             == star_path::edge_kind::retained_hinge);
      assert(near_point(equatorial_hinge->exit, equatorial_hinge->entry,
                        path_tolerance));
    }
  const auto equatorial_fold = star_path::first_edge_transition(
    reference, {-1, -111}, {1, -111});
  assert(equatorial_fold);
  assert(equatorial_fold->is_fold());
  assert(equatorial_fold->kind
         == star_path::edge_kind::intra_group_fold);

  // Only frame_area controls the map projection. Placement remains the
  // responsibility of the surrounding cartography object.
  const frame positioned_frame {large_dimensions, 17, 23};
  const auto positioned_projection
    = make_star_x_projection(positioned_frame);
  assert(positioned_projection.pframe.moriginx == 0);
  assert(positioned_projection.pframe.moriginy == 0);

  const auto rejects_frame = [](const frame& invalid_frame)
  {
    assert(!is_star_x_frame(invalid_frame));
    bool rejected = false;
    try
      {
        static_cast<void>(make_star_x_projection(invalid_frame));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_frame(frame {44, 22});
  rejects_frame(frame {17.001, 22});
  rejects_frame(frame {22, 17});
  rejects_frame(frame {0, 0});
  rejects_frame(frame {-17, -22});
  rejects_frame(frame {std::numeric_limits<double>::infinity(), 22});
  rejects_frame(frame {17, std::numeric_limits<double>::quiet_NaN()});
  rejects_frame(frame {std::numeric_limits<double>::max(),
                       std::numeric_limits<double>::max()});

  const auto rejects_layout = [&reference_frame](
    const star_x_layout invalid_layout)
  {
    bool rejected = false;
    try
      {
        static_cast<void>(make_star_x_projection(
          reference_frame, "", invalid_layout));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_layout(star_x_layout {.group_gap_ratio = 0.001});
  rejects_layout(star_x_layout {.group_gap_ratio = -0.501});
  rejects_layout(star_x_layout {
    .group_gap_ratio = std::numeric_limits<double>::quiet_NaN(),
  });
  rejects_layout(star_x_layout {
    .enlargement_factor = 0,
  });
  rejects_layout(star_x_layout {
    .enlargement_factor = -1,
  });
  rejects_layout(star_x_layout {
    .enlargement_factor = std::numeric_limits<double>::infinity(),
  });
  rejects_layout(star_x_layout {
    .enlargement_factor = std::numeric_limits<double>::quiet_NaN(),
  });

  // Composition helpers derive both the central mark and each Antarctic
  // source radius from the enlarged Star-X frame.
  const auto polar_star = star_x_detail::make_north_pole_star(reference_frame);
  const double star_outer_radius
    = reference_frame.height() * star_x_polar_star_outer_radius_ratio;
  for (std::size_t i = 0; i < polar_star.size(); ++i)
    {
      const double dx = polar_star[i].x - reference_frame.width() / 2;
      const double dy = polar_star[i].y - reference_frame.height() / 2;
      const double expected_radius
        = i % 2 == 0
            ? star_outer_radius
            : star_outer_radius * star_x_polar_star_inner_radius_factor;
      assert(std::abs(std::hypot(dx, dy) - expected_radius) < 1e-9);
      const auto& opposite = polar_star[(i + 8) % polar_star.size()];
      assert(std::abs(polar_star[i].x + opposite.x
                      - reference_frame.width()) < 1e-9);
      assert(std::abs(polar_star[i].y + opposite.y
                      - reference_frame.height()) < 1e-9);
    }
  assert(std::abs(polar_star.front().x - reference_frame.width() / 2)
         < 1e-9);
  assert(polar_star.front().y < reference_frame.height() / 2);

  // Reassembly preserves each source radius while normalizing geographic
  // bearing, so the bent neighboring Cahill-Keyes edges coincide throughout
  // the complete Antarctic cap.
  constexpr std::array quadrants {
    star_x_detail::quadrant::lower_left,
    star_x_detail::quadrant::lower_right,
    star_x_detail::quadrant::upper_right,
    star_x_detail::quadrant::upper_left,
  };
  for (const auto quadrant : quadrants)
    {
      const double longitude
        = star_x_detail::quadrant_center_longitude(quadrant);
      assert(star_x_detail::quadrant_for_longitude(longitude) == quadrant);
      const auto source_tip = star_x_detail::antarctic_source_tip(
        quadrant, reference_frame);
      const double tip_distance = std::hypot(
        source_tip.x - reference_frame.width() / 2,
        source_tip.y - reference_frame.height() / 2);
      for (int latitude = -90; latitude <= 90; latitude += 2)
        for (int offset = -44; offset <= 44; offset += 2)
          {
            double sample_longitude = longitude + offset;
            if (sample_longitude > 180)
              sample_longitude -= 360;
            else if (sample_longitude < -180)
              sample_longitude += 360;
            const auto sample = star_x_detail::project_to_frame(
              latitude, sample_longitude, reference_frame);
            const double sample_distance = std::hypot(
              sample.x - reference_frame.width() / 2,
              sample.y - reference_frame.height() / 2);
            assert(sample_distance <= tip_distance + 1e-9);
          }
      const auto point = star_x_detail::project_to_frame(
        -75, longitude, reference_frame);
      const double radius = std::hypot(
        point.x - source_tip.x, point.y - source_tip.y);
      const auto local
        = star_x_detail::project_antarctic_fragment_local(
            -75, longitude, reference_frame);
      assert(std::abs(std::hypot(local.x, local.y) - radius) < 1e-9);
    }

  struct quadrant_seam
  {
    double longitude;
    star_x_detail::quadrant west;
    star_x_detail::quadrant east;
  };
  constexpr std::array quadrant_seams {
    quadrant_seam {-111, star_x_detail::quadrant::lower_left,
                   star_x_detail::quadrant::lower_right},
    quadrant_seam {-21, star_x_detail::quadrant::lower_right,
                   star_x_detail::quadrant::upper_right},
    quadrant_seam {69, star_x_detail::quadrant::upper_right,
                   star_x_detail::quadrant::upper_left},
    quadrant_seam {159, star_x_detail::quadrant::upper_left,
                   star_x_detail::quadrant::lower_left},
  };
  constexpr double seam_epsilon = 1e-8;
  for (const quadrant_seam seam : quadrant_seams)
    for (const double latitude : {-89.0, -80.0, -70.0})
      {
        assert(star_x_detail::quadrant_for_longitude(
                 seam.longitude - seam_epsilon) == seam.west);
        assert(star_x_detail::quadrant_for_longitude(
                 seam.longitude + seam_epsilon) == seam.east);
        const auto west
          = star_x_detail::project_antarctic_fragment_local(
              latitude, seam.longitude - seam_epsilon, reference_frame);
        const auto east
          = star_x_detail::project_antarctic_fragment_local(
              latitude, seam.longitude + seam_epsilon, reference_frame);
        const double separation
          = std::hypot(west.x - east.x, west.y - east.y);
        assert(separation < 1e-5);
      }

  assert(api.image_filename(projection_base::filled) == "star-x.svg");
  a60::io::get_run_time_resources().data = "/opt/alpha60-data";
  assert(api.image_filename(projection_base::inverse)
         == "/opt/alpha60-data/star-x.svg");
  a60::io::get_run_time_resources().data.clear();

  expect_invalid(api, -90.001, 0);
  expect_invalid(api, 90.001, 0);
  expect_invalid(api, 0, -180.001);
  expect_invalid(api, 0, 180.001);
  expect_invalid(api, std::numeric_limits<double>::quiet_NaN(), 0);
  expect_invalid(api, 0, std::numeric_limits<double>::infinity());
}

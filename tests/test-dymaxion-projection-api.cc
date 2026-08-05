#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>
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
#include "a60-carto-projection-dymaxion.h"

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

} // namespace

int
main()
{
  using namespace a60::carto;
  static_assert(std::is_base_of_v<projection_api, dymaxionproj>);
  static_assert(dymaxion_detail::face_count == 23);
  static_assert(dymaxion_width_to_height_ratio > 2.11);
  static_assert(dymaxion_width_to_height_ratio < 2.12);

  const projection_api& api = dymaxion_source;
  assert(dymaxion_source.pmode == dymaxion);
  assert(dymaxion_source.pframe.width() == dymaxion_source_width);
  assert(dymaxion_source.pframe.height() == dymaxion_source_height);
  assert(is_dymaxion_frame(dymaxion_source.pframe));

  // Each oriented spherical subface selects itself at its centroid. The last
  // five entries are the Australia and Japan subdivisions.
  constexpr auto spherical = dymaxion_detail::spherical_faces();
  constexpr auto planar = dymaxion_detail::planar_faces();
  for (std::size_t index = 0; index < spherical.size(); ++index)
    {
      const auto centroid
        = spherical[index][0] + spherical[index][1] + spherical[index][2];
      assert(dymaxion_detail::containing_face(centroid) == index);
      for (const auto point : planar[index])
        {
          assert(point.x >= 0 && point.x <= dymaxion_source_width);
          assert(point.y >= 0 && point.y <= dymaxion_source_height);
        }
    }

  // Fuller's construction preserves uniform scale along every icosahedron
  // edge. Quarter-arc samples on a spherical edge therefore land at the same
  // fractions of the corresponding planar edge. This is not true of a
  // gnomonic face transform and guards the defining exact-equation behavior.
  const auto spherical_interpolate = [](const auto left, const auto right,
                                        const double fraction) {
    const double angle = std::acos(std::clamp(
      dymaxion_detail::dot(left, right), -1.0, 1.0));
    return (left * std::sin((1 - fraction) * angle)
            + right * std::sin(fraction * angle)) / std::sin(angle);
  };
  for (const double fraction : {0.25, 0.5, 0.75})
    {
      const auto spherical_point = spherical_interpolate(
        spherical[0][0], spherical[0][1], fraction);
      const auto projected
        = dymaxion_detail::project_on_face(0, spherical_point);
      const auto expected
        = planar[0][0] + (planar[0][1] - planar[0][0]) * fraction;
      assert(std::abs(projected.x - expected.x) < 2e-14);
      assert(std::abs(projected.y - expected.y) < 2e-14);
    }

  // Native-unit references generated independently with Robert W. Gray's
  // exact-transform program. Its unit-edge, lower-left-origin coordinates
  // are multiplied by the icosahedron chord edge and y-reflected into the
  // PROJ-derived landscape net used by this implementation.
  constexpr std::array specific_locations {
    expected_point {0, 0,
                    2.017393697178697, 0.052380842038240},
    expected_point {90, 0,
                    2.735812783682923, 1.319254645315929},
    expected_point {-90, 0,
                    5.364468344278590, 1.412524346614159},
    expected_point {0, -180,
                    3.682715549061752, 2.631516767482271},
    expected_point {0, 180,
                    3.682715549061752, 2.631516767482271},
    expected_point {40.7128, -74.0060,
                    3.437640038787786, 1.095609257783957},
    expected_point {34.0549, -118.2426,
                    3.513021801535528, 1.623279601590790},
    expected_point {48.8575, 2.3514,
                    2.498012034519876, 0.670719856791125},
    expected_point {-29.8587, 31.0218,
                    1.357835681677196, 0.167954502445578},
    expected_point {28.7041, 77.1025,
                    1.839712970392319, 1.243599769256516},
    expected_point {35.6895, 139.6917,
                    2.277837492363724, 1.988638380813348},
    expected_point {-33.8688, 151.2093,
                    1.055171304709382, 2.390897973082171},
    expected_point {21.1444, -157.0226,
                    3.539279584720069, 2.155655330675844},
    expected_point {-23.5558, -46.6396,
                    4.483841261033453, 0.726740559998188},
    expected_point {64.1470, -21.9408,
                    2.859367314705199, 0.955259691315074},
    expected_point {-18.1266, 178.4399,
                    3.950636316969628, 2.710799331829362},
    expected_point {-62.2001, 58.9642,
                    5.736553301775646, 1.199861882901615},
  };

  for (const auto& expected : specific_locations)
    {
      const auto [x, y] = api.meridians_to_point_2d(
        expected.latitude, expected.longitude);
      assert(std::abs(x - expected.x) < 3e-13);
      assert(std::abs(y - expected.y) < 3e-13);
    }
  assert(std::abs(dymaxion_source.longitude_zero_x
                  - specific_locations[0].x) < 3e-13);
  assert(std::abs(dymaxion_source.latitude_zero_y
                  - specific_locations[0].y) < 3e-13);

  // Frame dimensions scale the native net uniformly. Placement offsets are
  // discarded because cartography, rather than a projection, owns placement.
  const frame::area compact_dimensions {
    dymaxion_width_to_height_ratio * 25, 25
  };
  const std::array variable_frames {
    frame {dymaxion_width_to_height_ratio, 1},
    frame {compact_dimensions},
    frame {dymaxion_source_width, dymaxion_source_height},
    frame {44, 44 / dymaxion_width_to_height_ratio},
    frame {dymaxion_width_to_height_ratio * 4000, 4000},
  };
  for (const frame& map_frame : variable_frames)
    {
      assert(is_dymaxion_frame(map_frame));
      const auto projection = make_dymaxion_projection(
        map_frame, "fuller-airocean.png");
      assert(projection.pframe.width() == map_frame.width());
      assert(projection.pframe.height() == map_frame.height());
      assert(projection.pframe.moriginx == 0);
      assert(projection.pframe.moriginy == 0);
      assert(projection.image_filename(projection_base::filled)
             == "fuller-airocean.png");
      const double scale = map_frame.width() / dymaxion_source_width;
      const double tolerance = 3e-13 * std::max(1.0, scale);
      for (const auto& expected : specific_locations)
        {
          const auto [x, y] = projection.meridians_to_point_2d(
            expected.latitude, expected.longitude);
          assert(std::abs(x - expected.x * scale) < tolerance);
          assert(std::abs(y - expected.y * scale) < tolerance);
          assert(x >= 0 && x <= map_frame.width());
          assert(y >= 0 && y <= map_frame.height());
        }
    }

  const frame positioned_frame {compact_dimensions, 17, 23};
  const auto positioned_projection
    = make_dymaxion_projection(positioned_frame);
  assert(positioned_projection.pframe.moriginx == 0);
  assert(positioned_projection.pframe.moriginy == 0);

  a60::io::get_run_time_resources().data = "/projection-data";
  const auto named_projection = make_dymaxion_projection(
    pdymaxion_source, "dymaxion.png");
  assert(named_projection.image_filename(projection_base::outline)
         == "/projection-data/dymaxion.png");
  a60::io::get_run_time_resources().data.clear();

  const auto rejects_frame = [](const frame& invalid_frame)
  {
    assert(!is_dymaxion_frame(invalid_frame));
    bool rejected = false;
    try
      {
        static_cast<void>(make_dymaxion_projection(invalid_frame));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_frame(frame {2, 1});
  rejects_frame(frame {dymaxion_source_width,
                       dymaxion_source_height + 0.001});
  rejects_frame(frame {1, 2});
  rejects_frame(frame {0, 0});
  rejects_frame(frame {-dymaxion_source_width, -dymaxion_source_height});
  rejects_frame(frame {std::numeric_limits<double>::infinity(), 1});
  rejects_frame(frame {std::numeric_limits<double>::max(),
                       std::numeric_limits<double>::max()});
  rejects_frame(frame {dymaxion_width_to_height_ratio,
                       std::numeric_limits<double>::quiet_NaN()});

  // Sweep the complete API domain, including the poles and all net cuts.
  for (int latitude = -90; latitude <= 90; ++latitude)
    for (int longitude = -180; longitude <= 180; ++longitude)
      {
        const auto native = dymaxion_detail::project_to_unfolded_net(
          latitude, longitude);
        constexpr double native_tolerance = 2e-14;
        assert(std::isfinite(native.x) && std::isfinite(native.y));
        assert(native.x >= -native_tolerance);
        assert(native.x <= dymaxion_source_width + native_tolerance);
        assert(native.y >= -native_tolerance);
        assert(native.y <= dymaxion_source_height + native_tolerance);
        const auto [x, y] = api.meridians_to_point_2d(latitude, longitude);
        assert(std::isfinite(x) && std::isfinite(y));
        assert(x >= 0 && x <= dymaxion_source_width);
        assert(y >= 0 && y <= dymaxion_source_height);
      }

  for (int latitude = -90; latitude <= 90; latitude += 5)
    {
      const auto west = api.meridians_to_point_2d(latitude, -180);
      const auto east = api.meridians_to_point_2d(latitude, 180);
      assert(std::get<0>(west) == std::get<0>(east));
      assert(std::get<1>(west) == std::get<1>(east));
    }

  expect_invalid(api, -90.0001, 0);
  expect_invalid(api, 90.0001, 0);
  expect_invalid(api, 0, -180.0001);
  expect_invalid(api, 0, 180.0001);
  expect_invalid(api, std::numeric_limits<double>::infinity(), 0);
  expect_invalid(api, 0, -std::numeric_limits<double>::infinity());
  expect_invalid(api, std::numeric_limits<double>::quiet_NaN(), 0);
  expect_invalid(api, 0, std::numeric_limits<double>::quiet_NaN());
}

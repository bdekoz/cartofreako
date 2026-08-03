#include <algorithm>
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
#include "cart0freak0-myriahedral.h"

namespace {

struct expected_point
{
  double latitude;
  double longitude;
  double x;
  double y;
};

struct expected_vertex
{
  std::size_t face;
  std::size_t vertex;
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
  static_assert(std::is_base_of_v<projection_api, myriaproj>);
  static_assert(myriahedral_detail::face_count == 5120);
  static_assert(myriahedral_detail::tree_parent(103) == 103);

  const projection_api& api = myriahedral_source;
  assert(myriahedral_source.pmode == myriahedral);
  assert(myriahedral_source.pframe.width() == myriahedral_source_width);
  assert(myriahedral_source.pframe.height() == myriahedral_source_height);
  assert(is_myriahedral_frame(myriahedral_source.pframe));
  const auto [zero_x, zero_y] = api.meridians_to_point_2d(0, 0);
  assert(std::abs(zero_x - myriahedral_source.longitude_zero_x) < 1e-12);
  assert(std::abs(zero_y - myriahedral_source.latitude_zero_y) < 1e-12);

  constexpr auto source
    = "assets.static/myriahedral/black-white-downsampled.png";
  constexpr std::array modes {
    projection_base::filled,
    projection_base::outline,
    projection_base::inverse,
    projection_base::grid,
    projection_base::glitch,
  };
  for (const auto mode : modes)
    assert(api.image_filename(mode) == source);

  a60::io::get_run_time_resources().data = "/opt/alpha60-data";
  assert(api.image_filename(projection_base::filled)
         == "/opt/alpha60-data/assets.static/myriahedral/"
            "black-white-downsampled.png");
  a60::io::get_run_time_resources().data.clear();

  // Independent fixed references for every coordinate used by
  // augment_carto_geo_specific: poles, antimeridian and supple-zone probes,
  // followed by its twelve cities.
  constexpr std::array specific_locations {
    expected_point {0, 0, 2234.0946382533166, 1360.417650346466},
    expected_point {89.9, 0, 2641.5574923902936, 574.63719113079026},
    expected_point {80, 0, 2608.1923365476232, 664.64555800164135},
    expected_point {-89.9, 0, 1446.3829295329158, 1929.8287900788173},
    expected_point {-80, 0, 1539.0426869861499, 1904.7509330665555},
    expected_point {0, 179.9, 4002.454351992038, 1501.8211812265251},
    expected_point {0, 170, 3907.077156240739, 1512.6802831340472},
    expected_point {0, -179.9, 668.07003699449524, 482.34424968825732},
    expected_point {0, -170, 742.34954951451755, 543.14954208462325},
    expected_point {-80, -20, 1524.7249770598683, 1874.2188379803122},
    expected_point {-20, -19, 1972.2626587867969, 1439.3442691498592},
    expected_point {-20, -21, 1957.0352441974162, 1429.3552285606563},
    expected_point {-20, -23, 1941.672808299734, 1419.5661857260632},
    expected_point {-56, -19, 1719.4708522841538, 1735.2713050791435},
    expected_point {-56, -23, 1705.4486954825886, 1718.7261624276221},
    expected_point {40.7128, -74.006, 1672.3914750126473,
                    673.84652284592642},
    expected_point {34.0549, -118.2426, 1351.3128044037403,
                    552.15320677771206},
    expected_point {48.8575, 2.3514, 2517.2758871422448,
                    972.39218244955384},
    expected_point {-29.8587, 31.0218, 2324.4890728955243,
                    1758.0981768783581},
    expected_point {28.7041, 77.1025, 3007.1186435919121,
                    1301.5885879449875},
    expected_point {35.6895, 139.6917, 3411.6328979469154,
                    956.67736245199706},
    expected_point {-33.8688, 151.2093, 3700.3638175190272,
                    1904.3702443644747},
    expected_point {21.1444, -157.0226, 1073.0093255551963,
                    329.6014522485857},
    expected_point {-23.5558, -46.6396, 1737.6436803930335,
                    1349.7529572638309},
    expected_point {64.147, -21.9408, 2474.2062079977227,
                    760.0521355316381},
    expected_point {-18.1266, 178.4399, 619.5415673925603,
                    1688.9324537150205},
    expected_point {-62.2001, 58.9642, 1688.023511693737,
                    2103.175063304318},
  };

  for (const auto& expected : specific_locations)
    {
      const auto [x, y] = api.meridians_to_point_2d(
        expected.latitude, expected.longitude);
      assert(std::isfinite(x));
      assert(std::isfinite(y));
      assert(std::abs(x - expected.x) < 1e-9);
      assert(std::abs(y - expected.y) < 1e-9);
      assert(x >= 0 && x <= myriahedral_source_width);
      assert(y >= 0 && y <= myriahedral_source_height);
    }

  // The tree and unfolding agree with an independent reconstruction of the
  // original SPHEmesh face order and raster-registered spanning tree.
  const auto& layout = myriahedral_detail::layout();
  assert(std::abs(layout.minimum_x - -3.7949260457158975) < 2e-14);
  assert(std::abs(layout.minimum_y - -2.9255931762882703) < 2e-14);
  assert(std::abs(layout.maximum_x - 2.5709697874339961) < 2e-14);
  assert(std::abs(layout.maximum_y - 1.6095082077949852) < 2e-14);
  constexpr std::array layout_vertices {
    expected_vertex {0, 0, 0, 0},
    expected_vertex {0, 1, 0.06270108289432319,
                     -0.029237995128234273},
    expected_vertex {0, 2, 0.0472266615643552,
                     0.0505561924190785},
    expected_vertex {103, 0, 0.8341486317370738,
                     -0.36972395540109254},
    expected_vertex {103, 1, 0.8149114340498341,
                     -0.43885637108861664},
    expected_vertex {103, 2, 0.8915064763256819,
                     -0.4136417702597633},
    expected_vertex {5119, 0, -3.270595477649819,
                     -0.6361296716703474},
    expected_vertex {5119, 1, -3.2091499069135705,
                     -0.5829224172852846},
    expected_vertex {5119, 2, -3.2765229398945452,
                     -0.5672010756700169},
  };
  for (const auto& expected : layout_vertices)
    {
      const auto actual = layout.planar[expected.face][expected.vertex];
      assert(std::abs(actual.x - expected.x) < 3e-14);
      assert(std::abs(actual.y - expected.y) < 3e-14);
    }

  // Construct projections directly from frame/frame_area at arbitrary
  // scales. Every reference coordinate must scale uniformly.
  const frame::area compact_dimensions {
    myriahedral_width_to_height_ratio * 100, 100
  };
  const frame::area large_dimensions {
    myriahedral_width_to_height_ratio * 6600, 6600
  };
  const std::array variable_frames {
    frame {myriahedral_width_to_height_ratio, 1},
    frame {16, 9},
    frame {compact_dimensions},
    frame {myriahedral_source_width, myriahedral_source_height},
    frame {large_dimensions},
    frame {myriahedral_width_to_height_ratio * 617.25, 617.25},
  };
  for (const frame& map_frame : variable_frames)
    {
      assert(is_myriahedral_frame(map_frame));
      const auto projection = make_myriahedral_projection(
        map_frame, "variable-myriahedral.png");
      assert(projection.pframe.frame_area._M_width == map_frame.width());
      assert(projection.pframe.frame_area._M_height == map_frame.height());
      assert(projection.pframe.moriginx == 0);
      assert(projection.pframe.moriginy == 0);
      assert(projection.image_filename(projection_base::filled)
             == "variable-myriahedral.png");

      const auto [origin_x, origin_y]
        = projection.meridians_to_point_2d(0, 0);
      assert(std::abs(origin_x - projection.longitude_zero_x) < 1e-9);
      assert(std::abs(origin_y - projection.latitude_zero_y) < 1e-9);

      const double factor = map_frame.height() / myriahedral_source_height;
      const double tolerance = 1e-9 * std::max(1.0, factor);
      for (const auto& expected : specific_locations)
        {
          const auto [x, y] = projection.meridians_to_point_2d(
            expected.latitude, expected.longitude);
          assert(std::abs(x - expected.x * factor) < tolerance);
          assert(std::abs(y - expected.y * factor) < tolerance);
          assert(x >= 0 && x <= map_frame.width());
          assert(y >= 0 && y <= map_frame.height());
        }
    }

  // Only frame_area controls the projection. Placement offsets belong to
  // cartography and are deliberately discarded by the factory.
  const frame positioned_frame {compact_dimensions, 17, 23};
  const auto positioned_projection
    = make_myriahedral_projection(positioned_frame);
  assert(positioned_projection.pframe.moriginx == 0);
  assert(positioned_projection.pframe.moriginy == 0);

  const auto rejects_frame = [](const frame& invalid_frame)
  {
    assert(!is_myriahedral_frame(invalid_frame));
    bool rejected = false;
    try
      {
        static_cast<void>(make_myriahedral_projection(invalid_frame));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_frame(frame {2, 1});
  rejects_frame(frame {1920, 1080 + 0.001});
  rejects_frame(frame {1, 2});
  rejects_frame(frame {0, 0});
  rejects_frame(frame {-16, -9});
  rejects_frame(frame {std::numeric_limits<double>::infinity(), 1});
  rejects_frame(frame {std::numeric_limits<double>::max(),
                       std::numeric_limits<double>::max()});
  rejects_frame(frame {myriahedral_width_to_height_ratio,
                       std::numeric_limits<double>::quiet_NaN()});

  // The hierarchical search must recover every one of the 5120 leaves from
  // a point strictly inside that face.
  for (std::size_t index = 0; index < layout.spherical.size(); ++index)
    {
      const auto& face = layout.spherical[index];
      const auto centroid = myriahedral_detail::normalized(
        face[0] + face[1] + face[2]);
      assert(myriahedral_detail::containing_face(centroid) == index);
    }

  // Exercise every whole-degree coordinate through the hierarchical face
  // selection, including poles, geographic quadrants, and map cuts.
  for (int latitude = -90; latitude <= 90; ++latitude)
    for (int longitude = -180; longitude <= 180; ++longitude)
      {
        const auto [x, y] = api.meridians_to_point_2d(latitude, longitude);
        assert(std::isfinite(x));
        assert(std::isfinite(y));
        assert(x >= 0 && x <= myriahedral_source_width);
        assert(y >= 0 && y <= myriahedral_source_height);

        const auto geographic = myriahedral_detail::geographic_vector(
          latitude, longitude == 180 ? -180 : longitude);
        const std::size_t face
          = myriahedral_detail::containing_face(geographic);
        assert(myriahedral_detail::containment_margin(
                 layout.spherical[face], geographic) >= -1e-14);
      }

  // -180 and +180 are the same meridian and are canonicalized before face
  // selection, including when that coordinate lies on a cut.
  for (int latitude = -90; latitude <= 90; latitude += 5)
    {
      const auto west = api.meridians_to_point_2d(latitude, -180);
      const auto east = api.meridians_to_point_2d(latitude, 180);
      assert(std::abs(std::get<0>(west) - std::get<0>(east)) < 1e-12);
      assert(std::abs(std::get<1>(west) - std::get<1>(east)) < 1e-12);
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

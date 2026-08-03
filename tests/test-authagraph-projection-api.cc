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
#include "cart0freak0-authagraph.h"

namespace {

struct expected_point
{
  double latitude;
  double longitude;
  double x;
  double y;
};

constexpr double
dms(const double degrees, const double minutes, const double seconds,
    const double sign)
{ return sign * (degrees + (minutes + seconds / 60) / 60); }

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
  static_assert(std::is_base_of_v<projection_api, agproj>);

  const projection_api& api = ag_a3;
  assert(ag_a3.pmode == authagraph);
  assert(ag_a3.pframe.width() == authagraph_page_width);
  assert(ag_a3.pframe.height() == authagraph_page_height);
  assert(ag_a3.map_frame.width() == authagraph_map_width);
  assert(ag_a3.map_frame.height() == authagraph_map_height);
  assert(ag_a3.map_frame.moriginx == authagraph_map_left);
  assert(ag_a3.map_frame.moriginy == authagraph_map_top);
  assert(ag_a3.longitude_zero_x == authagraph_longitude_zero_x);
  assert(ag_a3.latitude_zero_y == authagraph_latitude_zero_y);
  const auto [zero_x, zero_y] = api.meridians_to_point_2d(0, 0);
  assert(std::abs(zero_x - ag_a3.longitude_zero_x) < 1e-12);
  assert(std::abs(zero_y - ag_a3.latitude_zero_y) < 1e-12);

  constexpr auto source = "assets.static/authagraph/15-SP-TESD-03-AG.pdf";
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
         == "/opt/alpha60-data/assets.static/authagraph/"
            "15-SP-TESD-03-AG.pdf");
  a60::io::get_run_time_resources().data.clear();

  // Reference values calculated independently from the published equations
  // and triangle assembly. This is exactly the location set in
  // augment_carto_geo_specific: poles, antimeridian and supple-zone probes,
  // followed by its twelve cities.
  constexpr std::array specific_locations {
    expected_point {0, 0, 120.059171352683464, 267.894521334396359},
    expected_point {89.9, 0, 599.837864528364321, 208.610795865588756},
    expected_point {80, 0, 374.907956674248908, 200.849590850363199},
    expected_point {-89.9, 0, 1005.920255678818194, 516.889654838472779},
    expected_point {-80, 0, 1015.335594586978232, 491.442254338525686},
    expected_point {0, 179.9, 563.202629667065025, 503.456637352486155},
    expected_point {0, 170, 534.963680785365455, 501.969355154562095},
    expected_point {0, -179.9, 563.761667537704966, 503.480306316641872},
    expected_point {0, -170, 591.608937178592555, 504.576179061034054},
    expected_point {-80, -20, 1005.033188701992117, 489.756761288608686},
    expected_point {-20, -19, 999.258829726257886, 288.297808515341444},
    expected_point {-20, -21, 992.369055123726866, 289.211516757039817},
    expected_point {-20, -23, 985.586946169796079, 291.355264254832036},
    expected_point {-56, -19, 1003.049380180671392, 419.090925535319002},
    expected_point {-56, -23, 996.855582307713121, 419.192185359366306},
    expected_point {40.7128, -74.006, 736.858291797103334, 302.749893403812166},
    expected_point {34.0549, -118.2426, 680.926407666646355, 380.014550542883285},
    expected_point {48.8575, 2.3514, 274.340357906223403, 227.459721091850497},
    expected_point {-29.8587, 31.0218, 139.181890318476576, 404.548639580661472},
    expected_point {28.7041, 77.1025, 331.341300310516885, 375.453297472903273},
    expected_point {35.6895, 139.6917, 464.823400706407369, 393.931036213492234},
    expected_point {-33.8688, 151.2093, 478.801449413275861, 587.752570527602870},
    expected_point {21.1444, -157.0226, 614.683160794565879, 441.241401068535993},
    expected_point {-23.5558, -46.6396, 922.302247441546683, 352.277729954628342},
    expected_point {64.147, -21.9408, 703.905298259811161, 209.722939182817328},
    expected_point {-18.1266, 178.4399, 555.135140348515733, 552.151044142573141},
    expected_point {-62.2001, 58.9642, 1082.750196587678602, 499.262771884090967},
  };

  for (const auto& expected : specific_locations)
    {
      const auto [x, y] = api.meridians_to_point_2d(
        expected.latitude, expected.longitude);
      assert(std::isfinite(x));
      assert(std::isfinite(y));
      assert(std::abs(x - expected.x) < 1e-9);
      assert(std::abs(y - expected.y) < 1e-9);
      assert(x >= authagraph_map_left);
      assert(x <= authagraph_map_left + authagraph_map_width);
      assert(y >= authagraph_map_top);
      assert(y <= authagraph_map_top + authagraph_map_height);
    }

  // Construct map-only projections directly from frame/frame_area at
  // arbitrary scales. The normalized projection must scale uniformly while
  // preserving every reference location.
  const frame::area compact_dimensions {
    authagraph_width_to_height_ratio * 100, 100
  };
  const frame::area large_dimensions {
    authagraph_width_to_height_ratio * 6600, 6600
  };
  const std::array variable_frames {
    frame {authagraph_width_to_height_ratio, 1},
    frame {4, std::sqrt(3)},
    frame {compact_dimensions},
    frame {authagraph_map_width, authagraph_map_height},
    frame {large_dimensions},
    frame {authagraph_width_to_height_ratio * 617.25, 617.25},
  };
  for (const frame& map_frame : variable_frames)
    {
      assert(is_authagraph_frame(map_frame));
      const auto projection = make_authagraph_projection(
        map_frame, "variable-authagraph.svg");
      assert(projection.pframe.frame_area._M_width == map_frame.width());
      assert(projection.pframe.frame_area._M_height == map_frame.height());
      assert(projection.map_frame.frame_area._M_width == map_frame.width());
      assert(projection.map_frame.frame_area._M_height == map_frame.height());
      assert(projection.map_frame.moriginx == 0);
      assert(projection.map_frame.moriginy == 0);
      assert(projection.image_filename(projection_base::filled)
             == "variable-authagraph.svg");

      const auto [origin_x, origin_y]
        = projection.meridians_to_point_2d(0, 0);
      assert(std::abs(origin_x - projection.longitude_zero_x) < 1e-9);
      assert(std::abs(origin_y - projection.latitude_zero_y) < 1e-9);

      const double factor = map_frame.height() / authagraph_map_height;
      const double tolerance = 1e-9 * std::max(1.0, factor);
      for (const auto& expected : specific_locations)
        {
          const auto [x, y] = projection.meridians_to_point_2d(
            expected.latitude, expected.longitude);
          const double reference_x = expected.x - authagraph_map_left;
          const double reference_y = expected.y - authagraph_map_top;
          assert(std::abs(x - reference_x * factor) < tolerance);
          assert(std::abs(y - reference_y * factor) < tolerance);
          assert(x >= 0 && x <= map_frame.width());
          assert(y >= 0 && y <= map_frame.height());
        }
    }

  // Only frame_area controls a map-only projection. Placement offsets belong
  // to cartography and are deliberately discarded by this factory.
  const frame positioned_frame {compact_dimensions, 17, 23};
  const auto positioned_projection
    = make_authagraph_projection(positioned_frame);
  assert(positioned_projection.pframe.moriginx == 0);
  assert(positioned_projection.pframe.moriginy == 0);
  assert(positioned_projection.map_frame.moriginx == 0);
  assert(positioned_projection.map_frame.moriginy == 0);

  const auto rejects_frame = [](const frame& invalid_frame)
  {
    assert(!is_authagraph_frame(invalid_frame));
    bool rejected = false;
    try
      {
        static_cast<void>(make_authagraph_projection(invalid_frame));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_frame(frame {1920, 1080});
  rejects_frame(frame {2, 1});
  rejects_frame(frame {authagraph_width_to_height_ratio * 100 + 0.001,
                       100});
  rejects_frame(frame {1, 2});
  rejects_frame(frame {0, 0});
  rejects_frame(frame {-authagraph_width_to_height_ratio, -1});
  rejects_frame(frame {std::numeric_limits<double>::infinity(), 1});
  rejects_frame(frame {std::numeric_limits<double>::max(),
                       std::numeric_limits<double>::max()});
  rejects_frame(frame {authagraph_width_to_height_ratio,
                       std::numeric_limits<double>::quiet_NaN()});

  const auto rejects_layout = [](const frame& container,
                                 const frame& viewport)
  {
    bool rejected = false;
    try
      {
        const projection_base base {
          container, 0, 0, authagraph, "invalid-layout"
        };
        static_cast<void>(agproj(base, viewport));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_layout(frame {100, 100}, frame {50, 50});
  rejects_layout(frame {100, 100},
                 frame {authagraph_width_to_height_ratio * 100, 100});

  // The full A3 page is a source-plate container rather than a map-only
  // frame; its embedded map viewport still has the required map ratio.
  assert(!is_authagraph_frame(pauthagraph_a3));
  assert(is_authagraph_frame(pauthagraph_a3_map));

  // These are the four singular vertices measured from the PDF's vector
  // graticule. The looser tolerance accounts for source-coordinate rounding.
  constexpr std::array pdf_vertices {
    expected_point {dms(76, 52, 51.82608, 1),
                    dms(149, 27, 3.56868, 1),
                    509.310892, 199.632551},
    expected_point {dms(27, 57, 9.99792, -1),
                    dms(97, 21, 25.2126, 1),
                    265.280630, 622.323384},
    expected_point {dms(22, 55, 41.65104, -1),
                    dms(133, 16, 57.93168, -1),
                    753.345153, 622.323384},
    expected_point {dms(6, 38, 13.37028, -1),
                    dms(18, 51, 8.037, -1),
                    997.376915, 199.632551},
  };
  for (const auto& expected : pdf_vertices)
    {
      const auto [x, y] = api.meridians_to_point_2d(
        expected.latitude, expected.longitude);
      assert(std::abs(x - expected.x) < 0.02);
      assert(std::abs(y - expected.y) < 0.02);
    }

  // Sweep the complete degree grid to exercise every tetrahedron face,
  // triangle sector, geographic boundary, and both poles.
  for (int latitude = -90; latitude <= 90; ++latitude)
    for (int longitude = -180; longitude <= 180; ++longitude)
      {
        const auto [x, y] = api.meridians_to_point_2d(latitude, longitude);
        assert(std::isfinite(x));
        assert(std::isfinite(y));
        assert(x >= authagraph_map_left - 1e-9);
        assert(x <= authagraph_map_left + authagraph_map_width + 1e-9);
        assert(y >= authagraph_map_top - 1e-9);
        assert(y <= authagraph_map_top + authagraph_map_height + 1e-9);
        assert(x >= 0 && x <= authagraph_page_width);
        assert(y >= 0 && y <= authagraph_page_height);
      }

  // -180 and +180 describe the same meridian. If it falls on the rectangular
  // cut, coordinates one map width apart are equivalent.
  for (int latitude = -90; latitude <= 90; latitude += 5)
    {
      const auto [west_x, west_y]
        = api.meridians_to_point_2d(latitude, -180);
      const auto [east_x, east_y]
        = api.meridians_to_point_2d(latitude, 180);
      const double direct_x_delta = std::abs(west_x - east_x);
      const double periodic_x_delta = std::min(
        direct_x_delta,
        std::abs(ag_a3.map_frame.width() - direct_x_delta));
      assert(periodic_x_delta < 1e-9);
      assert(std::abs(west_y - east_y) < 1e-9);
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

#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <tuple>
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
#include "cart0freak0-cahill-keyes.h"

namespace {

struct expected_point
{
  double latitude;
  double longitude;
  double x;
  double y;
};

} // namespace

int
main()
{
  // Exercise every location used by augment_carto_geo_specific through
  // projection_api itself: poles, antimeridian probes, supple-zone probes,
  // and all twelve named cities. Expected values come from the original Perl
  // at 10,000 units, scaled and translated into the 2112x1056 API frame.
  const a60::carto::projection_api& api = a60::carto::ck_1xengc;
  constexpr std::array specific_locations {
    expected_point {0, 0, 1197.543796515413, 457.299877954234},
    expected_point {89.9, 0, 1558.739752588049, 114.043924280185},
    expected_point {80, 0, 1514.759258804883, 145.997623416330},
    expected_point {-89.9, 0, 1080.873398669750, 941.732728494370},
    expected_point {-80, 0, 1086.555866974953, 887.667654039092},
    expected_point {0, 179.9, 141.033562334227, 457.005294112377},
    expected_point {0, 170, 95.458491085171, 421.406020019110},
    expected_point {0, -179.9, 142.054030696599, 457.594461796091},
    expected_point {0, -170, 192.567214633991, 486.758262139970},
    expected_point {-80, -20, 1067.531584868831, 888.997961436287},
    expected_point {-20, -19, 1066.351702041437, 540.510086132213},
    expected_point {-20, -21, 1056.000000000000, 540.329619937814},
    expected_point {-20, -23, 1045.648297958563, 540.510086132213},
    expected_point {-56, -19, 1061.468728915033, 750.302521163906},
    expected_point {-56, -23, 1050.531271084967, 750.302521163906},
    expected_point {40.7128, -74.0060, 658.943678228346, 355.919887450434},
    expected_point {34.0549, -118.2426, 497.483918061389, 431.997343354653},
    expected_point {48.8575, 2.3514, 1392.438309218633, 266.133787109930},
    expected_point {-29.8587, 31.0218, 1267.228566045208, 679.994658339286},
    expected_point {28.7041, 77.1025, 1621.041236926060, 462.472317908885},
    expected_point {35.6895, 139.6917, 1839.903865386879, 308.307853728451},
    expected_point {-33.8688, 151.2093, 2079.088865484258, 623.194855773890},
    expected_point {21.1444, -157.0226, 315.533804960986, 428.832454891035},
    expected_point {-23.5558, -46.6396, 935.050471917685, 591.939479527905},
    expected_point {64.1470, -21.9408, 689.367705678396, 166.274610083415},
    expected_point {-18.1266, 178.4399, 100.434953967516, 548.837680253911},
    expected_point {-62.2001, 58.9642, 1215.840831766201, 866.160806437831},
  };
  for (const auto& point : specific_locations)
    {
      const auto [x, y]
        = api.meridians_to_point_2d(point.latitude, point.longitude);
      assert(std::isfinite(x));
      assert(std::isfinite(y));
      assert(std::abs(x - point.x) < 1e-9);
      assert(std::abs(y - point.y) < 1e-9);
      assert(x >= 0 && x <= 2112);
      assert(y >= 0 && y <= 1056);
    }

  // Construct projections directly from frame/frame_area at arbitrary scales.
  // The 44x22 examples cover the SVG's 96-DPI coordinate space and the
  // checked-in 13200x6600 300-DPI PNG dimensions.
  using a60::carto::frame;
  const frame::area svg_44x22 {4224, 2112};
  const frame::area png_44x22_300 {13200, 6600};
  const std::array variable_frames {
    frame {320, 160},
    frame {44, 22},
    frame {svg_44x22},
    frame {png_44x22_300},
    frame {1234.5, 617.25},
  };
  for (const frame& map_frame : variable_frames)
    {
      assert(a60::carto::is_cahill_keyes_frame(map_frame));
      const auto projection = a60::carto::make_cahill_keyes_projection(
        map_frame, "variable-cahill-keyes");
      assert(projection.pframe.frame_area._M_width == map_frame.width());
      assert(projection.pframe.frame_area._M_height == map_frame.height());
      assert(projection.longitude_zero_x == map_frame.width() / 2);
      assert(projection.latitude_zero_y == map_frame.height() / 2);

      const double factor = map_frame.height() / 1056;
      const double tolerance = 1e-9 * std::max(1.0, factor);
      for (const auto& point : specific_locations)
        {
          const auto [x, y] = projection.meridians_to_point_2d(
            point.latitude, point.longitude);
          assert(std::abs(x - point.x * factor) < tolerance);
          assert(std::abs(y - point.y * factor) < tolerance);
          assert(x >= 0 && x <= map_frame.width());
          assert(y >= 0 && y <= map_frame.height());
        }
    }

  const auto raster_projection = a60::carto::make_cahill_keyes_projection(
    frame {png_44x22_300}, "visionscarto-cahillkeyes-44x22.300");
  assert(raster_projection.image_filename(a60::carto::projection_base::inverse)
         == "visionscarto-map/visionscarto-cahillkeyes-44x22.300-inverse.png");

  // The original projection_base constructor remains available, including
  // callers that intentionally provide a non-centered drawing origin.
  const a60::carto::projection_base offset_base {
    frame {320, 160}, 12, 34, a60::carto::cahill_keyes, "offset"
  };
  const a60::carto::ckproj offset_projection(offset_base);
  assert(offset_projection.longitude_zero_x == 12);
  assert(offset_projection.latitude_zero_y == 34);

  const auto rejects_frame = [](const frame& invalid_frame)
  {
    bool rejected = false;
    try
      {
        static_cast<void>(
          a60::carto::make_cahill_keyes_projection(invalid_frame));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_frame(frame {1920, 1080});
  rejects_frame(frame {2000.001, 1000});
  rejects_frame(frame {22, 44});
  rejects_frame(frame {0, 0});
  rejects_frame(frame {-2, -1});
  rejects_frame(frame {std::numeric_limits<double>::infinity(), 1});

  bool rejected_legacy_base = false;
  try
    {
      const a60::carto::projection_base invalid_base {
        frame {1920, 1080}, 960, 540, a60::carto::cahill_keyes, "invalid"
      };
      static_cast<void>(a60::carto::ckproj(invalid_base));
    }
  catch (const std::invalid_argument&)
    {
      rejected_legacy_base = true;
    }
  assert(rejected_legacy_base);
}

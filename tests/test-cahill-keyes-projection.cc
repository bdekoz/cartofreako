#include <array>
#include <cassert>
#include <cmath>
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
#include "a60-carto-projection-cahill-keyes.h"

namespace {

using projection = a60::carto::ck_native::forward_projection;

struct expected_point
{
  double latitude;
  double longitude;
  double x;
  double y;
};

bool
near(const double actual, const double expected, const double tolerance = 1e-9)
{
  return std::abs(actual - expected) <= tolerance;
}

} // namespace

int
main()
{
  // Values are from MegamapMaker-prep9.pl evaluated at its canonical
  // 10,000-unit scale and reduced to a 528-unit scaffold.
  constexpr std::array reference {
    expected_point {0, 1, 141.543796515413, 70.7001220457658},
    expected_point {89.9, 1, 502.739752588049, 413.956075719816},
    expected_point {80, 1, 458.759258804883, 382.002376583670},
    expected_point {-89.9, 1, 24.8733986697495, -413.732728494370},
    expected_point {-80, 1, 30.5558669749534, -359.667654039092},
    expected_point {0, -179.1, -914.966437665773, 70.9947058876233},
    expected_point {0, -178.9, -913.945969303401, 70.4055382039085},
    expected_point {-20, -18, 10.3517020414369, -12.5100861322132},
    expected_point {-20, -20, 0, -12.3296199378144},
    expected_point {-20, -22, -10.3517020414369, -12.5100861322132},
    expected_point {40, 25, 369.6, 182.904565279273},
    expected_point {74, 45, 487.964084523849, 327.962410421540},
    expected_point {40, 45, 435.724135095205, 149.038559560815},
    expected_point {74, 60, 510.838495371388, 326.787557911344},
    expected_point {10, 60, 464.425005628717, -39.4147939954772},
    expected_point {40, 60, 489.948295253431, 131.708273141814},
    expected_point {74, 70, 529.708235987449, 328.039491013402},
    expected_point {10, 70, 536.272, -47.6948496650124},
    expected_point {40, 70, 528, 128.941401228282},
    // The same nontrivial point in each of the eight Megamap octants.
    expected_point {40, -135, -620.275864904795, 149.038559560815},
    expected_point {40, -45, -307.209111175504, 223.236743215766},
    expected_point {40, 135, 748.790888824496, 223.236743215766},
    expected_point {-40, -135, -835.209111175504, -223.236743215766},
    expected_point {-40, -45, -92.275864904795, -149.038559560815},
    expected_point {-40, 45, 220.790888824496, -223.236743215766},
    expected_point {-40, 135, 963.724135095205, -149.038559560815},
  };

  const projection ck(528);
  for (const auto& point : reference)
    {
      const auto [x, y] = ck(point.longitude, point.latitude);
      assert(near(x, point.x));
      assert(near(y, point.y));
    }

  // Every construction length must scale with the selected raster. This is
  // especially important in the polar zones, where the former JavaScript
  // implementation left the 100/104 units-per-degree values unscaled.
  for (const double scaffold : {1056.0, 1320.0, 2112.0})
    {
      const projection scaled(scaffold);
      const double factor = scaffold / 528;
      for (const auto& point : reference)
        {
          const auto [x, y] = scaled(point.longitude, point.latitude);
          assert(near(x, point.x * factor, 1e-8));
          assert(near(y, point.y * factor, 1e-8));
        }
    }

  // Every location used by augment_carto_geo_specific must produce a finite
  // in-bounds point. Longitudes include ckproj's +1 raster adjustment.
  constexpr std::array specific_locations {
    std::pair {0.0, 1.0},
    std::pair {89.9, 1.0}, std::pair {80.0, 1.0},
    std::pair {-89.9, 1.0}, std::pair {-80.0, 1.0},
    std::pair {0.0, -179.1}, std::pair {0.0, 171.0},
    std::pair {0.0, -178.9}, std::pair {0.0, -169.0},
    std::pair {-80.0, -19.0},
    std::pair {-20.0, -18.0}, std::pair {-20.0, -20.0},
    std::pair {-20.0, -22.0}, std::pair {-56.0, -18.0},
    std::pair {-56.0, -22.0},
    std::pair {40.7128, -73.0060}, std::pair {34.0549, -117.2426},
    std::pair {48.8575, 3.3514}, std::pair {-29.8587, 32.0218},
    std::pair {28.7041, 78.1025}, std::pair {35.6895, 140.6917},
    std::pair {-33.8688, 152.2093}, std::pair {21.1444, -156.0226},
    std::pair {-23.5558, -45.6396}, std::pair {64.1470, -20.9408},
    std::pair {-18.1266, 179.4399}, std::pair {-62.2001, 59.9642},
  };
  for (const auto [latitude, longitude] : specific_locations)
    {
      const auto [x, y] = ck(longitude, latitude);
      assert(std::isfinite(x));
      assert(std::isfinite(y));
      assert(x >= -1056 && x <= 1056);
      assert(y >= -528 && y <= 528);
    }

  // Sweep the complete geographic domain at half-degree intervals. Besides
  // broad coverage, this lands exactly on every integer zone and octant seam.
  for (double latitude = -90; latitude <= 90; latitude += 0.5)
    for (double longitude = -180; longitude <= 180; longitude += 0.5)
      {
        const auto [x, y] = ck(longitude, latitude);
        assert(std::isfinite(x));
        assert(std::isfinite(y));
        assert(x >= -1056 && x <= 1056);
        assert(y >= -528 && y <= 528);
      }

  bool rejected = false;
  try
    {
      static_cast<void>(ck(0, 90.1));
    }
  catch (const std::invalid_argument&)
    {
      rejected = true;
    }
  assert(rejected);
}

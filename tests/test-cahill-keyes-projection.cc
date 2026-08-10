#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
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

double
longitude_distance(const double left, const double right)
{ return std::abs(std::remainder(left - right, 360.0)); }

int
assembly_octant(const double registered_longitude, const double latitude)
{
  int northern
    = static_cast<int>((registered_longitude + 200) / 90) + 1;
  if (northern == 5)
    northern = 1;
  if (latitude >= 0)
    return northern;
  constexpr std::array south {0, 6, 7, 8, 5};
  return south.at(northern);
}

void
assert_scale_invariant(const double longitude, const double latitude)
{
  constexpr std::array scaffolds {11.0, 528.0, 1056.0, 3300.0};
  static const std::array projections {
    projection(scaffolds[0]), projection(scaffolds[1]),
    projection(scaffolds[2]), projection(scaffolds[3]),
  };
  const auto [reference_x, reference_y]
    = projections.front()(longitude, latitude);
  assert(std::isfinite(reference_x));
  assert(std::isfinite(reference_y));

  const double normalized_x = reference_x / scaffolds.front();
  const double normalized_y = reference_y / scaffolds.front();
  for (std::size_t index = 0; index != scaffolds.size(); ++index)
    {
      const double scaffold = scaffolds[index];
      const auto [x, y] = projections[index](longitude, latitude);
      assert(std::isfinite(x));
      assert(std::isfinite(y));
      assert(x >= -2 * scaffold && x <= 2 * scaffold);
      assert(y >= -scaffold && y <= scaffold);
      assert(near(x / scaffold, normalized_x, 2e-13));
      assert(near(y / scaffold, normalized_y, 2e-13));
    }
}

void
check_representable_neighborhood(const double longitude,
                                 const double latitude,
                                 const int steps)
{
  assert_scale_invariant(longitude, latitude);
  double below = longitude;
  double above = longitude;
  for (int step = 0; step != steps; ++step)
    {
      below = std::nextafter(below,
        -std::numeric_limits<double>::infinity());
      above = std::nextafter(above,
        std::numeric_limits<double>::infinity());
      assert_scale_invariant(below, latitude);
      assert_scale_invariant(above, latitude);
    }
}

void
check_latitude_neighborhood(const double longitude,
                            const double latitude,
                            const int steps)
{
  assert_scale_invariant(longitude, latitude);
  double below = latitude;
  double above = latitude;
  for (int step = 0; step != steps; ++step)
    {
      below = std::nextafter(below,
        -std::numeric_limits<double>::infinity());
      above = std::nextafter(above,
        std::numeric_limits<double>::infinity());
      assert_scale_invariant(longitude, below);
      assert_scale_invariant(longitude, above);
    }
}

double
normalized_distance(const double first_longitude, const double first_latitude,
                    const double second_longitude,
                    const double second_latitude)
{
  constexpr double scaffold = 528;
  static const projection value(scaffold);
  const auto [first_x, first_y] = value(first_longitude, first_latitude);
  const auto [second_x, second_y] = value(second_longitude, second_latitude);
  return std::hypot(second_x - first_x, second_y - first_y) / scaffold;
}

} // namespace

int
main()
{
  // Coarse compatibility anchors from MegamapMaker-prep9.pl evaluated at its
  // 10,000-unit scale and reduced to a 528-unit scaffold. These check the
  // intended map construction, but are not the numerical correctness oracle.
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
      const auto reversed = ck.inverse(
        x, y, assembly_octant(point.longitude, point.latitude), 1e-7);
      assert(reversed);
      assert(std::abs(reversed->latitude - point.latitude) < 2e-8);
      assert(longitude_distance(
               reversed->registered_longitude, point.longitude) < 2e-8);
      assert(reversed->forward_residual <= 1e-7);
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

  // Generator path splitting converges to projection cuts in representable
  // floating-point steps, rather than in the half-degree increments used by
  // the broad domain sweep below. Every valid point in those neighborhoods
  // must remain finite and independent of the requested output scale.
  constexpr std::array cut_longitudes {-110.0, -20.0, 70.0, 160.0};
  constexpr std::array representative_latitudes {1.0, 15.0, 20.0, 73.0, 74.0};
  for (const double longitude : cut_longitudes)
    for (const double latitude : representative_latitudes)
      {
        check_representable_neighborhood(longitude, latitude, 64);
        check_representable_neighborhood(longitude, -latitude, 64);

        // Exact cuts select the octant to their east. Check that copy against
        // its one-sided limit; check the western copy between its two nearest
        // representable samples because a point API cannot return both copies.
        const double east = std::nextafter(longitude,
          std::numeric_limits<double>::infinity());
        const double west = std::nextafter(longitude,
          -std::numeric_limits<double>::infinity());
        const double farther_west = std::nextafter(west,
          -std::numeric_limits<double>::infinity());
        assert(normalized_distance(longitude, latitude, east, latitude)
               < 2e-12);
        assert(normalized_distance(west, latitude, farther_west, latitude)
               < 2e-12);
      }

  constexpr std::array center_longitudes {-155.0, -65.0, 25.0, 115.0};
  for (const double longitude : center_longitudes)
    for (const double latitude : representative_latitudes)
      {
        check_representable_neighborhood(longitude, latitude, 32);
        check_representable_neighborhood(longitude, -latitude, 32);
      }

  // The 29/30-degree meridian and 15/73/75-degree parallel transitions use
  // different construction formulae on either side. Exercise their immediate
  // floating-point neighborhoods as well as exact equality branches.
  constexpr std::array transition_longitudes {-5.0, -4.0, 54.0, 55.0};
  constexpr std::array transition_latitudes {0.0, 15.0, 73.0, 75.0};
  for (const double longitude : transition_longitudes)
    for (const double latitude : transition_latitudes)
      {
        check_representable_neighborhood(longitude, latitude, 16);
        check_latitude_neighborhood(longitude, latitude, 16);
        const double west = std::nextafter(longitude,
          -std::numeric_limits<double>::infinity());
        const double east = std::nextafter(longitude,
          std::numeric_limits<double>::infinity());
        const double south = std::nextafter(latitude,
          -std::numeric_limits<double>::infinity());
        const double north = std::nextafter(latitude,
          std::numeric_limits<double>::infinity());
        assert(normalized_distance(longitude, latitude, west, latitude)
               < 2e-12);
        assert(normalized_distance(longitude, latitude, east, latitude)
               < 2e-12);
        if (latitude == 0)
          {
            const double farther_south = std::nextafter(south,
              -std::numeric_limits<double>::infinity());
            assert(normalized_distance(longitude, south,
                                       longitude, farther_south) < 2e-12);
          }
        else
          assert(normalized_distance(longitude, latitude,
                                     longitude, south) < 2e-12);
        assert(normalized_distance(longitude, latitude, longitude, north)
               < 2e-12);
        if (latitude != 0)
          {
            check_representable_neighborhood(longitude, -latitude, 16);
            check_latitude_neighborhood(longitude, -latitude, 16);
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

  assert(!ck.inverse(10000, 10000, 1, 1e-7));
  const auto rejects_inverse = [&ck](const double x, const double y,
                                     const int octant,
                                     const double tolerance)
  {
    bool rejected_inverse = false;
    try
      {
        static_cast<void>(ck.inverse(x, y, octant, tolerance));
      }
    catch (const std::invalid_argument&)
      { rejected_inverse = true; }
    assert(rejected_inverse);
  };
  rejects_inverse(0, 0, 0, 1e-7);
  rejects_inverse(0, 0, 9, 1e-7);
  rejects_inverse(0, 0, 1, 0);
  rejects_inverse(std::numeric_limits<double>::quiet_NaN(), 0, 1, 1e-7);

  const auto rejects_scaffold = [](const double scaffold)
  {
    bool rejected_scaffold = false;
    try
      {
        static_cast<void>(projection(scaffold));
      }
    catch (const std::invalid_argument&)
      {
        rejected_scaffold = true;
      }
    assert(rejected_scaffold);
  };
  rejects_scaffold(0);
  rejects_scaffold(-1);
  rejects_scaffold(std::numeric_limits<double>::infinity());
  rejects_scaffold(std::numeric_limits<double>::max());

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

#include <cassert>
#include <cmath>
#include <initializer_list>
#include <limits>
#include <string>
#include <tuple>
#include <vector>

namespace a60 {

using point_2t = std::tuple<double, double>;
using string = std::string;
using vd = std::vector<double>;
using vrange = std::vector<point_2t>;
using vvranges = std::vector<vrange>;

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

  frame(const double width, const double height,
        const double x = 0, const double y = 0)
  : frame_area {width, height}, moriginx(x), moriginy(y)
  { }

  double width() const { return frame_area._M_width; }
  double height() const { return frame_area._M_height; }
};

inline const frame pck_1x1080 {1920, 960};
inline const frame pck_2x1080 {3840, 1920};
inline const frame pck_7x {4984, 2492};
inline const frame pck_3x {2004, 1002};
inline const frame f44x22h {4224, 2112};

struct test_projection
{
  frame pframe;
};

template<typename Projection>
struct cartography
{
  frame f;
  Projection p;

  point_2t
  to_point_2d(const double latitude, const double longitude) const
  {
    auto [x, y] = p.meridians_to_point_2d(latitude, longitude);
    return {x + f.moriginx, y + f.moriginy};
  }
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
#include "cart0freak0-cahill-keyes.h"
#include "cart0freak0-cahill-keyes-functions.h"

namespace {

using a60::point_2t;
using a60::vrange;
using a60::vvranges;
using a60::carto::cartography;
using a60::carto::test_projection;

bool
near(const double actual, const double expected)
{
  return std::abs(actual - expected) <= 1e-12;
}

void
expect_point(const point_2t& actual, const point_2t& expected)
{
  assert(near(std::get<0>(actual), std::get<0>(expected)));
  assert(near(std::get<1>(actual), std::get<1>(expected)));
}

void
expect_path(const vrange& actual,
            const std::initializer_list<point_2t> expected)
{
  assert(actual.size() == expected.size());
  auto actual_position = actual.begin();
  for (const point_2t& point : expected)
    expect_point(*actual_position++, point);
}

void
expect_paths(const vvranges& actual,
             const std::initializer_list<vrange> expected)
{
  assert(actual.size() == expected.size());
  auto actual_position = actual.begin();
  for (const vrange& path : expected)
    {
      assert(actual_position->size() == path.size());
      for (std::size_t i = 0; i < path.size(); ++i)
        expect_point(actual_position->at(i), path[i]);
      ++actual_position;
    }
}

template<typename Callable>
void
expect_invalid_argument(Callable&& callable)
{
  bool rejected = false;
  try
    {
      callable();
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
  // The projection occupies [10, 210] x [20, 120]. The outer drawing frame
  // dimensions are deliberately different: path edges derive from p.pframe,
  // while their placement derives from f.moriginx/f.moriginy.
  const cartography<test_projection> context {
    {300, 180, 10, 20},
    {{200, 100}}
  };

  vrange empty;
  assert(a60::carto::fold_path_edges(context, empty).empty());
  assert(a60::carto::minimize_path_distance(context, empty).empty());

  // Exercise the helper with the real Cahill-Keyes forward projection. At
  // this latitude, 158 E and 162 E lie on opposite screen sides of the
  // projection cut even though they are geographically adjacent.
  const a60::carto::ckproj projection {{200, 100}, "path-test"};
  const cartography<a60::carto::ckproj> projected_context {
    {300, 180, 10, 20},
    projection
  };
  const point_2t projected_right
    = projected_context.to_point_2d(-20, 158);
  const point_2t projected_left
    = projected_context.to_point_2d(-20, 162);
  const auto projected_segments = a60::carto::fold_path_edges(
    projected_context, vrange {projected_right, projected_left});
  assert(projected_segments.size() == 2);
  assert(near(std::get<0>(projected_segments.front().back()), 210));
  assert(near(std::get<0>(projected_segments.back().front()), 10));
  expect_point(projected_segments.front().front(), projected_right);
  expect_point(projected_segments.back().back(), projected_left);

  const vrange continuous {{20, 40}, {80, 50}, {140, 60}};
  const auto continuous_paths
    = a60::carto::fold_path_edges(context, continuous);
  expect_paths(continuous_paths, {continuous});
  expect_path(continuous, {{20, 40}, {80, 50}, {140, 60}});

  // A large internal jump is not an outer-edge wrap. It must be retained,
  // rather than silently dropping its current point as the former code did.
  const vrange internal_jump {{20, 40}, {150, 50}};
  expect_paths(a60::carto::fold_path_edges(context, internal_jump),
               {internal_jump});

  const vrange left_to_right {{20, 45}, {200, 55}, {190, 60}};
  expect_paths(
    a60::carto::fold_path_edges(context, left_to_right),
    {{{20, 45}, {10, 50}}, {{210, 50}, {200, 55}, {190, 60}}});

  const vrange right_to_left {{200, 55}, {20, 45}};
  expect_paths(a60::carto::fold_path_edges(context, right_to_left),
               {{{200, 55}, {210, 50}}, {{10, 50}, {20, 45}}});

  const vrange north_to_south {{80, 30}, {100, 110}};
  expect_paths(a60::carto::fold_path_edges(context, north_to_south),
               {{{80, 30}, {90, 20}}, {{90, 120}, {100, 110}}});

  const vrange south_to_north {{100, 110}, {80, 30}};
  expect_paths(a60::carto::fold_path_edges(context, south_to_north),
               {{{100, 110}, {90, 120}}, {{90, 20}, {80, 30}}});

  // Equal crossing parameters route through opposite frame corners in one
  // transition instead of duplicating or dropping the current point.
  const vrange corner_crossing {{20, 30}, {200, 110}};
  expect_paths(a60::carto::fold_path_edges(context, corner_crossing),
               {{{20, 30}, {10, 20}}, {{210, 120}, {200, 110}}});

  // When the two parameters differ, the segment crosses one edge and then
  // the other. The middle segment connects the corresponding adjacent edges.
  const vrange two_edge_crossing {{20, 35}, {200, 110}};
  expect_paths(
    a60::carto::fold_path_edges(context, two_edge_crossing),
    {{{20, 35}, {10, 22.5}},
     {{210, 22.5}, {208, 20}},
     {{208, 120}, {200, 110}}});

  vrange two_edge_remaining = two_edge_crossing;
  vvranges incremental_two_edge;
  while (!two_edge_remaining.empty())
    {
      assert(incremental_two_edge.size() < 3);
      incremental_two_edge.push_back(a60::carto::minimize_path_distance(
        context, two_edge_remaining));
    }
  expect_paths(
    incremental_two_edge,
    {{{20, 35}, {10, 22.5}},
     {{210, 22.5}, {208, 20}},
     {{208, 120}, {200, 110}}});

  // The incremental compatibility API returns exactly the same segmentation
  // while preserving the unprocessed suffix between calls.
  vrange remaining = left_to_right;
  const vrange first
    = a60::carto::minimize_path_distance(context, remaining);
  expect_path(first, {{20, 45}, {10, 50}});
  expect_path(remaining, {{210, 50}, {200, 55}, {190, 60}});
  const vrange second
    = a60::carto::minimize_path_distance(context, remaining);
  expect_path(second, {{210, 50}, {200, 55}, {190, 60}});
  assert(remaining.empty());

  vrange continuous_remaining = continuous;
  expect_path(
    a60::carto::minimize_path_distance(context, continuous_remaining),
    {{20, 40}, {80, 50}, {140, 60}});
  assert(continuous_remaining.empty());

  // Scaling and negative/positive placement offsets alter only the frame-edge
  // coordinates; the normalized two-edge result remains the same.
  const cartography<test_projection> scaled_context {
    {500, 260, -50, 7},
    {{400, 200}}
  };
  const vrange scaled_crossing {{-30, 37}, {330, 197}};
  expect_paths(
    a60::carto::fold_path_edges(scaled_context, scaled_crossing),
    {{{-30, 37}, {-50, 17}},
     {{350, 17}, {340, 7}},
     {{340, 207}, {330, 197}}});

  const cartography<test_projection> zero_frame {
    {100, 100},
    {{0, 0}}
  };
  expect_invalid_argument([&]
  {
    static_cast<void>(
      a60::carto::fold_path_edges(zero_frame, vrange {{0, 0}}));
  });

  const cartography<test_projection> wrong_aspect {
    {200, 100},
    {{200, 101}}
  };
  expect_invalid_argument([&]
  {
    static_cast<void>(
      a60::carto::fold_path_edges(wrong_aspect, vrange {{0, 0}}));
  });

  const cartography<test_projection> infinite_origin {
    {100, 100, std::numeric_limits<double>::infinity(), 0},
    {{200, 100}}
  };
  expect_invalid_argument([&]
  {
    static_cast<void>(
      a60::carto::fold_path_edges(infinite_origin, vrange {{0, 0}}));
  });

  expect_invalid_argument([&]
  {
    const double nan = std::numeric_limits<double>::quiet_NaN();
    static_cast<void>(
      a60::carto::fold_path_edges(context, vrange {{20, 40}, {nan, 50}}));
  });
}

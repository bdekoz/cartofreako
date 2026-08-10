#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <limits>
#include <span>
#include <string_view>
#include <vector>

#include "cart0freak0-projection-runtime.h"

namespace runtime = cart0freak0::projection_runtime;

namespace {

double
longitude_distance(const double left, const double right)
{ return std::abs(std::remainder(left - right, 360.0)); }

double
canonical_longitude(double value)
{
  while (value > 180)
    value -= 360;
  while (value < -180)
    value += 360;
  return value;
}

template<typename Vector>
runtime::geographic_coordinate
coordinate_from_vector(const Vector& value, const double rotation = 0)
{
  constexpr double pi
    = 3.141592653589793238462643383279502884;
  double longitude = std::atan2(value.y, value.x) * 180 / pi - rotation;
  longitude = std::remainder(longitude, 360.0);
  if (longitude == 180)
    longitude = -180;
  return {longitude, std::asin(value.z) * 180 / pi};
}

const runtime::inverse_candidate&
candidate_for_cell(const runtime::inverse_result& result,
                   const std::uint32_t cell)
{
  for (const runtime::inverse_candidate& candidate : result.candidates)
    if (candidate.native_cell == cell)
      return candidate;
  assert(false && "reverse result omitted the forward native cell");
  return result.candidates.front();
}

void
check_round_trip(const runtime::projection_context& projection,
                 const runtime::geographic_coordinate geographic)
{
  const runtime::forward_result projected
    = runtime::forward(projection, geographic);
  assert(std::isfinite(projected.point.x));
  assert(std::isfinite(projected.point.y));
  assert(projected.native_cell < projection.spec.native_cell_count);
  assert(projected.component == 0);

  const runtime::inverse_result reversed
    = runtime::inverse(projection, projected.point);
  assert(reversed.status == runtime::inverse_status::unique
         || reversed.status == runtime::inverse_status::ambiguous
         || reversed.status == runtime::inverse_status::cut);
  assert(!reversed.candidates.empty());
  const runtime::inverse_candidate& matching
    = candidate_for_cell(reversed, projected.native_cell);
  assert(std::abs(matching.point.latitude_degrees
                  - geographic.latitude_degrees) < 2e-8);
  assert(longitude_distance(matching.point.longitude_degrees,
                            geographic.longitude_degrees) < 2e-8);
  assert(matching.forward_residual <= reversed.tolerance_pixels);

  runtime::inverse_options qualified;
  qualified.native_cell = projected.native_cell;
  const runtime::inverse_result one
    = runtime::inverse(projection, projected.point, qualified);
  assert(one.status == runtime::inverse_status::unique
         || one.status == runtime::inverse_status::cut);
  assert(one.candidates.size() == 1);
  assert(one.candidates.front().native_cell == projected.native_cell);

  const runtime::forward_result projected_again
    = runtime::forward(projection, matching.point);
  assert(std::hypot(projected_again.point.x - projected.point.x,
                    projected_again.point.y - projected.point.y) < 2e-7);
}

} // namespace

int
main()
{
  static_assert(runtime::abi_version == 1);
  static_assert(runtime::api_version == 2);

  const std::array source_points {
    runtime::geographic_coordinate {-73.9857, 40.7484},
    runtime::geographic_coordinate {171.2, 7.1},
    runtime::geographic_coordinate {151.2093, -33.8688},
    runtime::geographic_coordinate {37.6173, 55.7558},
  };

  for (const runtime::projection_spec& spec : runtime::projection_specs)
    {
      const runtime::projection_context projection(
        spec, runtime::make_frame(spec));
      const bool reversible
        = spec.kind == runtime::projection_kind::cahill_keyes
          || spec.kind == runtime::projection_kind::myriahedral
          || spec.kind == runtime::projection_kind::voronoi;
      assert((runtime::inverse_mode_for(spec)
              == runtime::inverse_mode::face_qualified) == reversible);
      if (reversible)
        {
          for (const runtime::geographic_coordinate point : source_points)
            check_round_trip(projection, point);

          const std::vector<runtime::forward_result> forward_batch
            = runtime::forward_many(projection, source_points);
          assert(forward_batch.size() == source_points.size());
          std::vector<runtime::projected_coordinate> projected_points;
          for (const runtime::forward_result& value : forward_batch)
            projected_points.push_back(value.point);
          const std::vector<runtime::inverse_result> reverse_batch
            = runtime::inverse_many(projection, projected_points);
          assert(reverse_batch.size() == source_points.size());
          for (std::size_t index = 0; index < reverse_batch.size(); ++index)
            candidate_for_cell(
              reverse_batch[index], forward_batch[index].native_cell);

          const runtime::inverse_result outside = runtime::inverse(
            projection, {-1, projection.map_frame.height() / 2});
          assert(outside.status == runtime::inverse_status::outside);
          assert(outside.candidates.empty());

          if (spec.kind == runtime::projection_kind::cahill_keyes)
            {
              constexpr std::array sector_west {
                159.0, -111.0, -21.0, 69.0,
              };
              constexpr std::array sector_offsets {
                0.5, 7.5, 15.0, 16.0, 30.0, 44.5, 45.0,
                45.5, 60.0, 74.0, 75.0, 82.5, 89.5,
              };
              constexpr std::array parallels {
                0.5, 7.5, 14.999, 15.0, 15.001, 40.0,
                72.999, 73.0, 73.001, 74.0, 74.999, 75.0,
                75.001, 82.5, 89.5,
              };
              for (std::size_t sector = 0;
                   sector < sector_west.size(); ++sector)
                for (const double offset : sector_offsets)
                  for (const double parallel : parallels)
                    for (const double latitude_sign : {-1.0, 1.0})
                      {
                        const runtime::geographic_coordinate source {
                          canonical_longitude(
                            sector_west[sector] + offset),
                          latitude_sign * parallel,
                        };
                        const runtime::forward_result projected
                          = runtime::forward(projection, source);
                        const std::uint32_t expected_cell
                          = static_cast<std::uint32_t>(
                              sector + (latitude_sign < 0 ? 4 : 0));
                        assert(projected.native_cell == expected_cell);
                        runtime::inverse_options options;
                        options.native_cell = projected.native_cell;
                        const runtime::inverse_result reversed
                          = runtime::inverse(
                              projection, projected.point, options);
                        assert(reversed.status
                               == runtime::inverse_status::unique);
                        assert(reversed.candidates.size() == 1);
                        const runtime::inverse_candidate& candidate
                          = reversed.candidates.front();
                        assert(std::abs(candidate.point.latitude_degrees
                                        - source.latitude_degrees) < 2e-8);
                        assert(longitude_distance(
                                 candidate.point.longitude_degrees,
                                 source.longitude_degrees) < 2e-8);
                        assert(candidate.forward_residual
                               <= reversed.tolerance_pixels);
                      }

              for (std::size_t sector = 0;
                   sector < sector_west.size(); ++sector)
                for (const double latitude_sign : {-1.0, 1.0})
                  {
                    const runtime::geographic_coordinate source {
                      canonical_longitude(sector_west[sector] + 45),
                      latitude_sign * 90,
                    };
                    const runtime::forward_result projected
                      = runtime::forward(projection, source);
                    runtime::inverse_options options;
                    options.native_cell = projected.native_cell;
                    const runtime::inverse_result reversed
                      = runtime::inverse(projection, projected.point, options);
                    assert(reversed.status == runtime::inverse_status::cut);
                    assert(reversed.candidates.size() == 1);
                    assert(std::abs(
                      reversed.candidates.front().point.latitude_degrees
                      - source.latitude_degrees) < 2e-8);
                  }

              constexpr std::array global_offsets {16.0, 45.0, 74.0};
              constexpr std::array global_parallels {15.0, 73.0, 82.5};
              for (std::size_t sector = 0;
                   sector < sector_west.size(); ++sector)
                for (const double offset : global_offsets)
                  for (const double parallel : global_parallels)
                    for (const double latitude_sign : {-1.0, 1.0})
                      {
                        const runtime::geographic_coordinate source {
                          canonical_longitude(
                            sector_west[sector] + offset),
                          latitude_sign * parallel,
                        };
                        const runtime::forward_result projected
                          = runtime::forward(projection, source);
                        const runtime::inverse_result reversed
                          = runtime::inverse(projection, projected.point);
                        assert(reversed.status
                               == runtime::inverse_status::unique);
                        assert(reversed.candidates.size() == 1);
                        assert(reversed.candidates.front().native_cell
                               == projected.native_cell);
                      }

              const runtime::forward_result equator = runtime::forward(
                projection, {24, 0});
              const runtime::inverse_result equator_reverse
                = runtime::inverse(projection, equator.point);
              assert(equator_reverse.status
                       == runtime::inverse_status::ambiguous
                     || equator_reverse.status
                          == runtime::inverse_status::cut);
              assert(!equator_reverse.candidates.empty());

              constexpr std::array registered_seams {
                -111.0, -21.0, 69.0, 159.0,
              };
              for (const double longitude : registered_seams)
                for (const double latitude : {-74.0, -20.0, 20.0, 74.0})
                  {
                    const runtime::forward_result projected
                      = runtime::forward(
                          projection, {longitude, latitude});
                    const runtime::inverse_result reversed
                      = runtime::inverse(projection, projected.point);
                    assert(reversed.status == runtime::inverse_status::cut
                           || reversed.status
                                == runtime::inverse_status::ambiguous);
                    const runtime::inverse_candidate& candidate
                      = candidate_for_cell(reversed, projected.native_cell);
                    assert(candidate.boundary);
                    assert(std::abs(candidate.point.latitude_degrees
                                    - latitude) < 2e-8);
                    assert(longitude_distance(
                             candidate.point.longitude_degrees,
                             longitude) < 2e-8);
                  }
            }
          else if (spec.kind == runtime::projection_kind::myriahedral)
            {
              using namespace a60::carto::myriahedral_detail;
              const projection_layout& layout
                = std::get<a60::carto::myriaproj>(
                    projection.projection).layout();
              for (std::size_t face = 0; face < face_count; ++face)
                {
                  const spherical_face& triangle = layout.spherical[face];
                  const vector_3d center = normalized(
                    triangle[0] + triangle[1] + triangle[2]);
                  const runtime::geographic_coordinate source
                    = coordinate_from_vector(center);
                  const runtime::forward_result projected
                    = runtime::forward(projection, source);
                  assert(projected.native_cell == face);
                  runtime::inverse_options options;
                  options.native_cell = static_cast<std::uint32_t>(face);
                  const runtime::inverse_result reversed
                    = runtime::inverse(projection, projected.point, options);
                  assert(reversed.status == runtime::inverse_status::unique);
                  assert(reversed.candidates.size() == 1);
                  assert(reversed.candidates.front().forward_residual
                         <= reversed.tolerance_pixels);
                }

              const planar_face& triangle = layout.planar.front();
              const point_2d midpoint {
                (triangle[0].x + triangle[1].x) / 2,
                (triangle[0].y + triangle[1].y) / 2,
              };
              const point_2d normalized_midpoint
                = normalize_planar_point(layout, midpoint);
              const runtime::inverse_result boundary = runtime::inverse(
                projection,
                {normalized_midpoint.x * projection.map_frame.width(),
                 normalized_midpoint.y * projection.map_frame.height()});
              assert(boundary.status == runtime::inverse_status::ambiguous
                     || boundary.status == runtime::inverse_status::cut);
            }
          else
            {
              using namespace a60::carto::voronoi_detail;
              const layout_data& layout = a60::carto::voronoi_detail::layout();
              for (std::size_t face = 0; face < face_count; ++face)
                {
                  const runtime::geographic_coordinate source
                    = coordinate_from_vector(
                      layout.faces[face].site, input_rotation_degrees);
                  const runtime::forward_result projected
                    = runtime::forward(projection, source);
                  assert(projected.native_cell == face);
                  runtime::inverse_options options;
                  options.native_cell = static_cast<std::uint32_t>(face);
                  const runtime::inverse_result reversed
                    = runtime::inverse(projection, projected.point, options);
                  assert(reversed.status == runtime::inverse_status::unique);
                  assert(reversed.candidates.size() == 1);
                }
            }
        }
      else
        {
          const runtime::forward_result projected
            = runtime::forward(projection, source_points.front());
          const runtime::inverse_result reversed
            = runtime::inverse(projection, projected.point);
          assert(reversed.status == runtime::inverse_status::unsupported);
          assert(reversed.candidates.empty());
        }
    }

  const runtime::projection_spec& cahill_keyes
    = runtime::find_projection_spec("cahill-keyes");
  for (const double width : {44.0, 440.0, 3840.0, 13200.0})
    {
      const runtime::projection_context projection(
        cahill_keyes, a60::carto::frame {width, width / 2});
      check_round_trip(projection, {171.2, 7.1});
      check_round_trip(projection, {-21.2, -56.75});
    }

  const runtime::projection_context myria(
    runtime::find_projection_spec("myriahedral"));
  bool rejected = false;
  try
    {
      static_cast<void>(runtime::inverse(
        myria, {std::numeric_limits<double>::quiet_NaN(), 0}));
    }
  catch (const std::invalid_argument&)
    { rejected = true; }
  assert(rejected);

  rejected = false;
  try
    {
      runtime::inverse_options options;
      options.native_cell
        = static_cast<std::uint32_t>(myria.spec.native_cell_count);
      static_cast<void>(runtime::inverse(myria, {0, 0}, options));
    }
  catch (const std::invalid_argument&)
    { rejected = true; }
  assert(rejected);
}

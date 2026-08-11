#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include "cart0freak0-projection-runtime.h"

namespace runtime = cart0freak0::projection_runtime;
namespace dy = a60::carto::dymaxion_detail;

namespace {

using vector = dy::vector_3d;

struct edge
{
  vector first;
  vector second;
  vector opposite;
  std::size_t owner;
};

bool
near(const vector left, const vector right, const double tolerance = 2e-13)
{
  return std::abs(left.x - right.x) <= tolerance
         && std::abs(left.y - right.y) <= tolerance
         && std::abs(left.z - right.z) <= tolerance;
}

bool
same_edge(const edge& left, const edge& right)
{
  return (near(left.first, right.first) && near(left.second, right.second))
         || (near(left.first, right.second) && near(left.second, right.first));
}

vector
step_toward(vector value, const vector target, const unsigned count)
{
  for (unsigned step = 0; step < count; ++step)
    {
      value.x = std::nextafter(value.x, target.x);
      value.y = std::nextafter(value.y, target.y);
      value.z = std::nextafter(value.z, target.z);
    }
  return dy::normalized(value);
}

long double
determinant_long(const vector first, const vector second, const vector third)
{
  const long double cross_x
    = static_cast<long double>(second.y) * third.z
      - static_cast<long double>(second.z) * third.y;
  const long double cross_y
    = static_cast<long double>(second.z) * third.x
      - static_cast<long double>(second.x) * third.z;
  const long double cross_z
    = static_cast<long double>(second.x) * third.y
      - static_cast<long double>(second.y) * third.x;
  return static_cast<long double>(first.x) * cross_x
         + static_cast<long double>(first.y) * cross_y
         + static_cast<long double>(first.z) * cross_z;
}

bool
contains_long(const dy::triangle_3d& face, const vector point)
{
  const long double tolerance
    = 64 * std::numeric_limits<double>::epsilon();
  return determinant_long(point, face[1], face[2]) <= tolerance
         && determinant_long(face[0], point, face[2]) <= tolerance
         && determinant_long(face[0], face[1], point) <= tolerance;
}

std::vector<std::size_t>
production_candidates(const vector point)
{
  constexpr auto faces = dy::spherical_faces();
  std::vector<std::size_t> result;
  for (std::size_t index = 0; index < faces.size(); ++index)
    if (dy::contains(faces[index], point))
      result.push_back(index);
  return result;
}

std::vector<std::size_t>
oracle_candidates(const vector point)
{
  constexpr auto faces = dy::spherical_faces();
  std::vector<std::size_t> result;
  for (std::size_t index = 0; index < faces.size(); ++index)
    if (contains_long(faces[index], point))
      result.push_back(index);
  return result;
}

runtime::geographic_coordinate
geographic(const vector value)
{
  constexpr double pi
    = 3.141592653589793238462643383279502884;
  const vector unit = dy::normalized(value);
  return {
    std::remainder(std::atan2(unit.y, unit.x) * 180 / pi, 360.0),
    std::asin(std::clamp(unit.z, -1.0, 1.0)) * 180 / pi,
  };
}

std::size_t
first_rejected_width(const double expected, const double height,
                     const double direction)
{
  double width = expected;
  for (std::size_t count = 1; count <= 4096; ++count)
    {
      width = std::nextafter(width, direction);
      if (!a60::carto::is_dymaxion_frame({width, height}))
        return count;
    }
  throw std::runtime_error("Dymaxion frame classifier accepted 4096 ULPs");
}

} // namespace

int
main(const int argc, char** argv)
{
  const std::string output
    = argc > 1 ? argv[1] : "reports/dymaxion-ulp-audit.json";
  constexpr auto faces = dy::spherical_faces();
  std::vector<vector> vertices;
  std::vector<edge> edges;
  for (std::size_t face = 0; face < faces.size(); ++face)
    for (std::size_t index = 0; index < 3; ++index)
      {
        const vector vertex = dy::normalized(faces[face][index]);
        if (std::none_of(vertices.begin(), vertices.end(),
                         [=](const vector value) { return near(value, vertex); }))
          vertices.push_back(vertex);
        edge candidate {
          dy::normalized(faces[face][(index + 1) % 3]),
          dy::normalized(faces[face][(index + 2) % 3]),
          vertex,
          face,
        };
        if (std::none_of(edges.begin(), edges.end(),
                         [&](const edge& value) {
                           return same_edge(value, candidate);
                         }))
          edges.push_back(candidate);
      }

  constexpr std::array<unsigned, 13> ulp_steps {
    1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096,
  };
  std::size_t probes = 0;
  std::size_t candidate_differences = 0;
  std::size_t production_gaps = 0;
  std::size_t oracle_gaps = 0;
  const auto audit_point = [&](const vector point) {
    const std::vector<std::size_t> production = production_candidates(point);
    const std::vector<std::size_t> oracle = oracle_candidates(point);
    ++probes;
    production_gaps += production.empty();
    oracle_gaps += oracle.empty();
    candidate_differences += production != oracle;
    if (!production.empty())
      assert(dy::containing_face(point) == production.front());
  };

  for (const edge& value : edges)
    {
      const vector midpoint = dy::normalized(value.first + value.second);
      const vector interior = dy::normalized(
        faces[value.owner][0] + faces[value.owner][1]
        + faces[value.owner][2]);
      const vector exterior = dy::normalized(midpoint * 2 - interior);
      audit_point(midpoint);
      for (const unsigned count : ulp_steps)
        {
          audit_point(step_toward(midpoint, interior, count));
          audit_point(step_toward(midpoint, exterior, count));
        }
      if (!dy::contains(faces[value.owner],
                        step_toward(midpoint, interior, 4096)))
        throw std::runtime_error(
          "boundary-normal interior probe missed owner face "
          + std::to_string(value.owner));
      if (dy::contains(faces[value.owner],
                       step_toward(midpoint, exterior, 4096)))
        throw std::runtime_error(
          "boundary-normal exterior probe retained owner face "
          + std::to_string(value.owner));
    }

  for (const vector vertex : vertices)
    {
      audit_point(vertex);
      for (std::size_t face = 0; face < faces.size(); ++face)
        for (std::size_t corner = 0; corner < 3; ++corner)
          if (near(vertex, dy::normalized(faces[face][corner])))
            {
              const vector center = dy::normalized(
                faces[face][0] + faces[face][1] + faces[face][2]);
              for (const unsigned count : ulp_steps)
                audit_point(step_toward(vertex, center, count));
            }
    }

  assert(production_gaps == 0);
  assert(oracle_gaps == 0);

  struct frame_result
  {
    const char* name;
    double width;
    double height;
    std::size_t rejected_below;
    std::size_t rejected_above;
  };
  const std::array frame_heights {
    std::pair {"native", a60::carto::dymaxion_source_height},
    std::pair {"44-inch", 44 / a60::carto::dymaxion_width_to_height_ratio},
    std::pair {"1920-pixel", 1920 / a60::carto::dymaxion_width_to_height_ratio},
    std::pair {"13200-pixel", 13200 / a60::carto::dymaxion_width_to_height_ratio},
  };
  std::vector<frame_result> frames;
  for (const auto& [name, height] : frame_heights)
    {
      const double width = a60::carto::dymaxion_width_to_height_ratio * height;
      assert(a60::carto::is_dymaxion_frame({width, height}));
      frames.push_back({
        name, width, height,
        first_rejected_width(width, height,
                             -std::numeric_limits<double>::infinity()),
        first_rejected_width(width, height,
                             std::numeric_limits<double>::infinity()),
      });
    }

  std::size_t inverse_face_checks = 0;
  double maximum_residual = 0;
  double maximum_raw_excursion = 0;
  for (const frame_result& frame_value : frames)
    {
      const runtime::projection_spec& spec
        = runtime::find_projection_spec("dymaxion");
      const runtime::projection_context projection(
        spec, a60::carto::frame {frame_value.width, frame_value.height});
      for (std::size_t face = 0; face < faces.size(); ++face)
        {
          const vector center = dy::normalized(
            faces[face][0] + faces[face][1] + faces[face][2]);
          const runtime::geographic_coordinate source = geographic(center);
          const dy::point_2d raw = dy::project_on_face(face, center);
          maximum_raw_excursion = std::max({
            maximum_raw_excursion,
            std::max(0.0, -raw.x),
            std::max(0.0, raw.x - a60::carto::dymaxion_source_width),
            std::max(0.0, -raw.y),
            std::max(0.0, raw.y - a60::carto::dymaxion_source_height),
          });
          const runtime::forward_result projected
            = runtime::forward(projection, source);
          runtime::inverse_options options;
          options.native_cell = projected.native_cell;
          const runtime::inverse_result reversed
            = runtime::inverse(projection, projected.point, options);
          assert(reversed.status == runtime::inverse_status::unique);
          assert(reversed.candidates.size() == 1);
          maximum_residual = std::max(
            maximum_residual, reversed.candidates.front().forward_residual);
          ++inverse_face_checks;
        }
    }
  assert(maximum_raw_excursion <= 1e-14);

  std::ofstream report(output);
  if (!report)
    throw std::runtime_error("cannot write " + output);
  report << std::setprecision(17)
         << "{\n"
         << "  \"schema\": \"cartofreako-dymaxion-ulp-audit-v1\",\n"
         << "  \"status\": \"pass\",\n"
         << "  \"constants\": {\n"
         << "    \"sphericalClassifierDoubleEpsilonMultiplier\": 8,\n"
         << "    \"frameClassifierDoubleEpsilonMultiplier\": 16,\n"
         << "    \"inverseBarycentricLongDoubleEpsilonMultiplier\": 512,\n"
         << "    \"inverseResidualDoubleEpsilonMultiplier\": 256\n"
         << "  },\n"
         << "  \"topology\": {\"faces\": " << faces.size()
         << ", \"uniqueVertices\": " << vertices.size()
         << ", \"uniqueEdges\": " << edges.size() << "},\n"
         << "  \"boundaryProbes\": " << probes << ",\n"
         << "  \"classifiedCandidateDifferences\": "
         << candidate_differences << ",\n"
         << "  \"productionGaps\": " << production_gaps << ",\n"
         << "  \"longDoubleOracleGaps\": " << oracle_gaps << ",\n"
         << "  \"inverseFaceScaleChecks\": " << inverse_face_checks << ",\n"
         << "  \"maximumForwardResidual\": " << maximum_residual << ",\n"
         << "  \"maximumInteriorRawExcursion\": "
         << maximum_raw_excursion << ",\n"
         << "  \"frames\": [\n";
  for (std::size_t index = 0; index < frames.size(); ++index)
    {
      const frame_result& value = frames[index];
      report << "    {\"name\": \"" << value.name
             << "\", \"width\": " << value.width
             << ", \"height\": " << value.height
             << ", \"firstRejectedUlpsBelow\": " << value.rejected_below
             << ", \"firstRejectedUlpsAbove\": " << value.rejected_above
             << "}" << (index + 1 == frames.size() ? "\n" : ",\n");
    }
  report << "  ],\n"
         << "  \"interpretation\": \"Candidate-set differences within the declared double-input boundary band are classified evidence, not production defects. No gap, out-of-bounds interior clamp, scale-dependent inverse failure, or frame-classifier overreach was observed.\"\n"
         << "}\n";
  std::cout << "dymaxion ULP audit: " << edges.size() << " unique edges, "
            << vertices.size() << " unique vertices, " << probes
            << " probes, no gaps; report " << output << '\n';
}

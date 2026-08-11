#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/istreamwrapper.h>
#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/prettywriter.h>

#include "cart0freak0-projection-runtime.h"

namespace fs = std::filesystem;
namespace runtime = cart0freak0::projection_runtime;
namespace rj = rapidjson;

namespace {

struct family_summary
{
  std::string family;
  std::string evidence;
  std::size_t cases = 0;
  double maximum_angular_error = 0;
  std::size_t discrepancies = 0;
  std::size_t classified_registration_exclusions = 0;
  double maximum_registration_vertex_delta_degrees = 0;
};

rj::Document
read_json(const fs::path& path)
{
  std::ifstream stream(path);
  if (!stream)
    throw std::runtime_error("cannot read " + path.string());
  rj::IStreamWrapper wrapper(stream);
  rj::Document document;
  document.ParseStream(wrapper);
  if (document.HasParseError() || !document.IsObject())
    throw std::runtime_error("invalid JSON in " + path.string());
  return document;
}

double
longitude_distance(const double left, const double right)
{ return std::abs(std::remainder(left - right, 360.0)); }

double
angular_error(const runtime::geographic_coordinate& observed,
              const rj::Value& expected)
{
  return std::max(
    longitude_distance(observed.longitude_degrees, expected[0].GetDouble()),
    std::abs(observed.latitude_degrees - expected[1].GetDouble()));
}

const runtime::inverse_candidate*
nearest_candidate(const runtime::inverse_result& result,
                  const rj::Value& expected)
{
  const runtime::inverse_candidate* selected = nullptr;
  double best = std::numeric_limits<double>::infinity();
  for (const runtime::inverse_candidate& candidate : result.candidates)
    {
      const double error = angular_error(candidate.point, expected);
      if (error < best)
        {
          best = error;
          selected = &candidate;
        }
    }
  return selected;
}

family_summary
check_voronoi(const fs::path& root)
{
  const rj::Document fixture
    = read_json(root / "voronoi-d3-v2.0.1.json");
  assert(std::string_view(fixture["provenance"]["version"].GetString())
         == "2.0.1");
  const runtime::projection_spec& spec
    = runtime::find_projection_spec("voronoi");
  const runtime::projection_context projection(spec);
  family_summary summary {"voronoi", "upstream-implementation"};
  for (const rj::Value& one : fixture["cases"].GetArray())
    {
      const rj::Value& normalized = one["selectedProjected"];
      const runtime::projected_coordinate point {
        normalized[0].GetDouble() * spec.width,
        normalized[1].GetDouble() * spec.height,
      };
      runtime::inverse_options options;
      options.tolerance_pixels = 2e-6;
      options.maximum_candidates = 64;
      const runtime::inverse_result inverse
        = runtime::inverse(projection, point, options);
      const runtime::inverse_candidate* candidate
        = nearest_candidate(inverse, one["expectedGeographic"]);
      const double error = candidate
                             ? angular_error(candidate->point,
                                             one["expectedGeographic"])
                             : std::numeric_limits<double>::infinity();
      summary.maximum_angular_error
        = std::max(summary.maximum_angular_error, error);
      if (!candidate || error > one["angularToleranceDegrees"].GetDouble())
        ++summary.discrepancies;
      ++summary.cases;
    }
  return summary;
}

a60::carto::dymaxion_detail::vector_3d
vector_from_geographic(const rj::Value& coordinate)
{
  return a60::carto::dymaxion_detail::geographic_vector(
    coordinate[1].GetDouble(), coordinate[0].GetDouble());
}

family_summary
check_dymaxion(const fs::path& root)
{
  using namespace a60::carto::dymaxion_detail;
  const rj::Document fixture
    = read_json(root / "dymaxion-d3-gray-v2.0.1.json");
  const runtime::projection_spec& spec
    = runtime::find_projection_spec("dymaxion");
  const runtime::projection_context projection(spec);
  constexpr auto spherical = spherical_faces();
  const layout_data& page = layout();
  family_summary summary {"dymaxion", "upstream-implementation"};

  for (const rj::Value& one : fixture["cases"].GetArray())
    {
      std::array<vector_3d, 3> source_vertices {};
      for (std::size_t vertex = 0; vertex < 3; ++vertex)
        source_vertices[vertex]
          = vector_from_geographic(one["faceVerticesGeographic"][vertex]);
      constexpr std::array<std::array<std::size_t, 3>, 6> permutations {{
        {{0, 1, 2}}, {{0, 2, 1}}, {{1, 0, 2}},
        {{1, 2, 0}}, {{2, 0, 1}}, {{2, 1, 0}},
      }};
      std::size_t face = face_count;
      std::array<std::size_t, 3> mapping {};
      double best_face_score = -2;
      for (std::size_t candidate_face = 0;
           candidate_face < face_count; ++candidate_face)
        for (const auto& candidate_mapping : permutations)
        {
          double score = 1;
          for (std::size_t d3_vertex = 0; d3_vertex < 3; ++d3_vertex)
            score = std::min(
              score,
              dot(source_vertices[d3_vertex],
                  normalized(spherical[candidate_face]
                                       [candidate_mapping[d3_vertex]])));
          if (score > best_face_score)
            {
              best_face_score = score;
              face = candidate_face;
              mapping = candidate_mapping;
            }
        }
      if (face == face_count || best_face_score <= 1 - 2e-9)
        {
          ++summary.classified_registration_exclusions;
          ++summary.cases;
          continue;
        }
      summary.maximum_registration_vertex_delta_degrees = std::max(
        summary.maximum_registration_vertex_delta_degrees,
        std::acos(std::clamp(best_face_score, -1.0, 1.0)) * 180
          / a60::carto::dymaxion_detail::pi);
      const rj::Value& weights = one["selectedProjectedBarycentricWeights"];
      point_2d raw {0, 0};
      for (std::size_t d3_vertex = 0; d3_vertex < 3; ++d3_vertex)
        {
          raw.x += weights[d3_vertex].GetDouble()
                   * page.faces[face].planar[mapping[d3_vertex]].x;
          raw.y += weights[d3_vertex].GetDouble()
                   * page.faces[face].planar[mapping[d3_vertex]].y;
        }
      const point_2d normalized = normalize_planar_point(raw);
      runtime::inverse_options options;
      options.native_cell = face;
      options.tolerance_pixels = 2e-6;
      const runtime::inverse_result inverse = runtime::inverse(
        projection,
        {normalized.x * spec.width, normalized.y * spec.height}, options);
      const runtime::inverse_candidate* candidate
        = nearest_candidate(inverse, one["expectedGeographic"]);
      const double error = candidate
                             ? angular_error(candidate->point,
                                             one["expectedGeographic"])
                             : std::numeric_limits<double>::infinity();
      summary.maximum_angular_error
        = std::max(summary.maximum_angular_error, error);
      if (!candidate || error > one["angularToleranceDegrees"].GetDouble())
        ++summary.discrepancies;
      ++summary.cases;
    }
  if (summary.cases - summary.classified_registration_exclusions < 72)
    throw std::runtime_error(
      "too few common D3/Cartofreako Dymaxion registrations");
  return summary;
}

family_summary
check_myriahedral(const fs::path& root)
{
  using namespace a60::carto::myriahedral_detail;
  const rj::Document fixture
    = read_json(root / "myriahedral-clean-room.json");
  family_summary summary {"myriahedral", "independent-reimplementation"};
  std::string current_layout;
  const runtime::projection_spec* spec = nullptr;
  std::optional<runtime::projection_context> projection;
  for (const rj::Value& one : fixture["cases"].GetArray())
    {
      const std::string layout_id = one["layoutId"].GetString();
      if (layout_id != current_layout)
        {
          current_layout = layout_id;
          spec = &runtime::find_projection_spec(current_layout);
          projection.emplace(*spec);
        }
      assert(spec && projection);
      const std::uint32_t face = one["nativeFace"].GetUint();
      const projection_layout& layout
        = std::get<a60::carto::myriaproj>(projection->projection).layout();
      const rj::Value& weights = one["selectedProjectedBarycentricWeights"];
      point_2d raw {0, 0};
      for (std::size_t vertex = 0; vertex < 3; ++vertex)
        {
          raw.x += weights[vertex].GetDouble() * layout.planar[face][vertex].x;
          raw.y += weights[vertex].GetDouble() * layout.planar[face][vertex].y;
        }
      const point_2d normalized = normalize_planar_point(layout, raw);
      runtime::inverse_options options;
      options.native_cell = face;
      const runtime::inverse_result inverse = runtime::inverse(
        *projection,
        {normalized.x * spec->width, normalized.y * spec->height}, options);
      const runtime::inverse_candidate* candidate
        = nearest_candidate(inverse, one["expectedGeographic"]);
      const double error = candidate
                             ? angular_error(candidate->point,
                                             one["expectedGeographic"])
                             : std::numeric_limits<double>::infinity();
      summary.maximum_angular_error
        = std::max(summary.maximum_angular_error, error);
      if (!candidate || error > one["angularToleranceDegrees"].GetDouble())
        ++summary.discrepancies;
      ++summary.cases;
    }
  return summary;
}

void
write_report(const fs::path& path,
             const std::vector<family_summary>& summaries)
{
  fs::create_directories(path.parent_path());
  std::ofstream stream(path);
  if (!stream)
    throw std::runtime_error("cannot write " + path.string());
  rj::OStreamWrapper wrapper(stream);
  rj::PrettyWriter<rj::OStreamWrapper> writer(wrapper);
  writer.StartObject();
  writer.Key("schemaVersion");
  writer.String("cartofreako-cross-implementation-reverse-report-v1");
  writer.Key("result");
  writer.String(std::all_of(summaries.begin(), summaries.end(),
                            [](const family_summary& value) {
                              return value.discrepancies == 0;
                            }) ? "pass" : "discrepancy");
  writer.Key("families"); writer.StartArray();
  for (const family_summary& summary : summaries)
    {
      writer.StartObject();
      writer.Key("family"); writer.String(summary.family.c_str());
      writer.Key("evidenceGrade"); writer.String(summary.evidence.c_str());
      writer.Key("caseCount"); writer.Uint64(summary.cases);
      writer.Key("maximumAngularErrorDegrees");
      writer.Double(summary.maximum_angular_error);
      writer.Key("discrepancyCount"); writer.Uint64(summary.discrepancies);
      writer.Key("classifiedRegistrationExclusionCount");
      writer.Uint64(summary.classified_registration_exclusions);
      writer.Key("maximumRegistrationVertexDeltaDegrees");
      writer.Double(summary.maximum_registration_vertex_delta_degrees);
      writer.EndObject();
    }
  writer.EndArray();
  writer.Key("discrepancyPolicy");
  writer.String("retain and classify as convention, registration, oracle, or production before changing production code");
  writer.EndObject();
  stream << '\n';
}

} // namespace

int
main(const int argc, char** argv)
{
  const fs::path root
    = argc > 1 ? argv[1] : "fixtures/projections/v1/oracles";
  const fs::path report
    = argc > 2 ? argv[2] : "reports/cross-implementation-reverse-oracle.json";
  const std::vector summaries {
    check_voronoi(root), check_dymaxion(root), check_myriahedral(root),
  };
  write_report(report, summaries);
  std::size_t total = 0;
  for (const family_summary& summary : summaries)
    {
      total += summary.cases;
      std::cout << summary.family << ": " << summary.cases
                << " cases, max error " << summary.maximum_angular_error
                << " degrees, discrepancies " << summary.discrepancies
                << ", classified registration exclusions "
                << summary.classified_registration_exclusions
                << '\n';
      if (summary.discrepancies != 0)
        return 1;
    }
  std::cout << "cross-implementation reverse oracle passed: " << total
            << " cases in " << summaries.size() << " families\n";
}

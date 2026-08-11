#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

#include <rapidjson/document.h>
#include <rapidjson/istreamwrapper.h>

#include "cart0freak0-projection-runtime.h"

namespace runtime = cart0freak0::projection_runtime;
namespace rj = rapidjson;

namespace {

std::string
two_digits(const std::uint32_t value)
{
  std::ostringstream output;
  output.width(2);
  output.fill('0');
  output << value;
  return output.str();
}

std::string
myriahedral_path(const std::uint32_t cell)
{
  std::uint32_t remainder = cell % 256;
  std::string result(4, '0');
  for (int index = 3; index >= 0; --index)
    {
      result[static_cast<std::size_t>(index)]
        = static_cast<char>('0' + remainder % 4);
      remainder /= 4;
    }
  return result;
}

std::string
topology_key(const runtime::projection_spec& spec,
             const std::uint32_t native_cell,
             const std::uint32_t component)
{
  switch (spec.kind)
    {
    case runtime::projection_kind::cahill_keyes:
      return std::string(native_cell < 4 ? "octant:north:" : "octant:south:")
             + std::to_string(native_cell % 4);
    case runtime::projection_kind::authagraph:
      return "tetrahedron-vertex:" + std::to_string(native_cell / 6)
             + "/sector:" + std::to_string(native_cell % 6);
    case runtime::projection_kind::dymaxion:
      return "fuller-registered-face:" + two_digits(native_cell);
    case runtime::projection_kind::myriahedral:
      return "icosahedron-base-face:" + two_digits(native_cell / 256)
             + "/subdivision:" + myriahedral_path(native_cell);
    case runtime::projection_kind::star_x:
      return std::string(component == 0 ? "carrier/" : "antarctic-cap/")
             + (native_cell < 4 ? "octant:north:" : "octant:south:")
             + std::to_string(native_cell % 4);
    case runtime::projection_kind::voronoi:
      {
        auto vertices
          = a60::carto::voronoi_detail::face_vertex_indices()[native_cell];
        std::sort(vertices.begin(), vertices.end());
        return "icosahedron-face:" + std::to_string(vertices[0]) + "-"
               + std::to_string(vertices[1]) + "-"
               + std::to_string(vertices[2]);
      }
    }
  throw std::logic_error("unknown topology");
}

double
longitude_distance(const double left, const double right)
{ return std::abs(std::remainder(left - right, 360.0)); }

struct observed_candidate
{
  std::string topology;
  std::uint32_t component;
  double longitude;
  double latitude;
  bool boundary;
};

bool
candidate_less(const observed_candidate& left,
               const observed_candidate& right)
{
  return std::tuple(left.topology, left.component,
                    left.longitude, left.latitude)
         < std::tuple(right.topology, right.component,
                      right.longitude, right.latitude);
}

const runtime::projection_spec&
spec_for_layout(const std::string_view family, const std::string_view layout)
{
  if (family == "myriahedral")
    return runtime::find_projection_spec(layout);
  return runtime::find_projection_spec(family);
}

std::size_t
check_file(const std::string& path)
{
  std::ifstream stream(path);
  if (!stream)
    throw std::runtime_error("cannot read " + path);
  rj::IStreamWrapper wrapper(stream);
  rj::Document document;
  document.ParseStream(wrapper);
  if (document.HasParseError() || !document.IsObject())
    throw std::runtime_error("invalid JSON in " + path);
  const std::string family = document["family"].GetString();
  std::size_t count = 0;

  for (const rj::Value& layout : document["layouts"].GetArray())
    {
      const std::string layout_id = layout["layoutId"].GetString();
      const runtime::projection_spec& spec
        = spec_for_layout(family, layout_id);
      const runtime::projection_context projection(spec);
      for (const rj::Value& fixture : layout["cases"].GetArray())
        {
          ++count;
          const rj::Value& input = fixture["input"]["geographic"];
          const runtime::geographic_coordinate geographic {
            input[0].GetDouble(), input[1].GetDouble(),
          };
          const runtime::forward_result forward
            = runtime::forward(projection, geographic);
          const rj::Value& expected = fixture["expected"];
          const rj::Value& point = expected["projected"];
          const double tolerance
            = fixture["tolerances"]["normalizedPlanar"].GetDouble();
          assert(std::abs(forward.point.x / spec.width
                          - point[0].GetDouble()) <= tolerance);
          assert(std::abs(forward.point.y / spec.height
                          - point[1].GetDouble()) <= tolerance);
          assert(topology_key(spec, forward.native_cell, forward.component)
                 == expected["topologyKey"].GetString());
          assert(forward.component == expected["component"].GetUint());

          runtime::inverse_options options;
          options.maximum_candidates = 64;
          const runtime::inverse_result reverse
            = runtime::inverse(projection, forward.point, options);
          assert(runtime::inverse_status_name(reverse.status)
                 == expected["reverseStatus"].GetString());

          std::vector<observed_candidate> observed;
          for (const runtime::inverse_candidate& candidate : reverse.candidates)
            observed.push_back({
              topology_key(spec, candidate.native_cell, candidate.component),
              candidate.component,
              candidate.point.longitude_degrees,
              candidate.point.latitude_degrees,
              candidate.boundary,
            });
          std::sort(observed.begin(), observed.end(), candidate_less);
          const rj::Value& wanted = expected["reverseCandidates"];
          assert(observed.size() == wanted.Size());
          const double angular
            = fixture["tolerances"]["angularDegrees"].GetDouble();
          for (rj::SizeType index = 0; index < wanted.Size(); ++index)
            {
              const rj::Value& candidate = wanted[index];
              assert(observed[index].topology
                     == candidate["topologyKey"].GetString());
              assert(observed[index].component
                     == candidate["component"].GetUint());
              assert(observed[index].boundary
                     == candidate["boundary"].GetBool());
              assert(std::abs(observed[index].latitude
                              - candidate["geographic"][1].GetDouble())
                     <= angular);
              assert(longitude_distance(
                       observed[index].longitude,
                       candidate["geographic"][0].GetDouble()) <= angular);
            }
        }
    }
  return count;
}

} // namespace

int
main(const int argc, char** argv)
{
  const std::string root = argc == 2 ? argv[1] : "fixtures/projections/v1";
  constexpr std::array families {
    "cahill-keyes", "authagraph", "dymaxion",
    "myriahedral", "star-x", "voronoi",
  };
  std::size_t count = 0;
  for (const std::string_view family : families)
    count += check_file(root + "/" + std::string(family) + ".json");
  std::cout << "native projection fixture adapter passed: " << count
            << " cases\n";
}

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

#include <rapidjson/ostreamwrapper.h>
#include <rapidjson/writer.h>

#include "cart0freak0-projection-runtime.h"

namespace fs = std::filesystem;
namespace runtime = cart0freak0::projection_runtime;
namespace rj = rapidjson;

namespace {

struct fixture_case
{
  std::string id;
  runtime::geographic_coordinate input;
  runtime::forward_result forward;
  runtime::inverse_result reverse;
  std::string boundary_class;
  std::string evidence_grade;
};

struct fixture_layout
{
  std::string id;
  double aspect;
  std::string component_model;
  std::string cut_topology;
  std::vector<fixture_case> cases;
};

double
canonical_longitude(double value)
{
  value = std::remainder(value, 360.0);
  return value == 180 ? -180 : value;
}

template<typename Vector>
runtime::geographic_coordinate
coordinate_from_vector(const Vector& value, const double rotation = 0)
{
  constexpr double pi
    = 3.141592653589793238462643383279502884;
  return {canonical_longitude(std::atan2(value.y, value.x) * 180 / pi
                              - rotation),
          std::asin(std::clamp(value.z, -1.0, 1.0)) * 180 / pi};
}

std::string
two_digits(const std::uint32_t value)
{
  std::ostringstream output;
  output << std::setw(2) << std::setfill('0') << value;
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
        const auto vertices
          = a60::carto::voronoi_detail::face_vertex_indices()[native_cell];
        std::array<std::size_t, 3> ordered = vertices;
        std::sort(ordered.begin(), ordered.end());
        return "icosahedron-face:" + std::to_string(ordered[0]) + "-"
               + std::to_string(ordered[1]) + "-"
               + std::to_string(ordered[2]);
      }
    }
  throw std::logic_error("unknown projection topology");
}

void
add_case(fixture_layout& output,
         const runtime::projection_context& projection,
         const std::string& id,
         const runtime::geographic_coordinate input,
         const std::string& boundary_class = "interior",
         const std::string& evidence_grade = "structural-invariant")
{
  const runtime::forward_result forward = runtime::forward(projection, input);
  runtime::inverse_options options;
  options.maximum_candidates = 64;
  const runtime::inverse_result reverse
    = runtime::inverse(projection, forward.point, options);
  if (reverse.candidates.empty())
    throw std::runtime_error("fixture reverse produced no candidate: " + id);
  output.cases.push_back(
    {id, input, forward, reverse, boundary_class, evidence_grade});
}

fixture_layout
make_cahill_keyes(const runtime::projection_context& projection)
{
  fixture_layout result {
    "cahill-keyes/reference-m", 2, "eight octants; component 0",
    "interrupted octants with equator, meridian, and pole cuts", {}};
  constexpr std::array west {159.0, -111.0, -21.0, 69.0};
  constexpr std::array offsets {
    5.0, 12.0, 18.0, 25.0, 32.0, 40.0,
    48.0, 56.0, 64.0, 72.0, 80.0, 87.0,
  };
  constexpr std::array latitudes {
    7.0, 14.0, 20.0, 29.0, 40.0, 55.0,
    68.0, 72.0, 74.0, 76.0, 83.0, 88.0,
  };
  for (std::size_t hemisphere = 0; hemisphere < 2; ++hemisphere)
    for (std::size_t octant = 0; octant < west.size(); ++octant)
      for (std::size_t zone = 0; zone < offsets.size(); ++zone)
        add_case(result, projection,
                 "octant-" + std::to_string(hemisphere * 4 + octant)
                   + "-zone-" + static_cast<char>('A' + zone),
                 {canonical_longitude(west[octant] + offsets[zone]),
                  (hemisphere == 0 ? 1 : -1) * latitudes[zone]});
  for (std::size_t octant = 0; octant < west.size(); ++octant)
    {
      add_case(result, projection, "equator-" + std::to_string(octant),
               {canonical_longitude(west[octant] + 24), 0}, "cut");
      for (const double sign : {-1.0, 1.0})
        add_case(result, projection,
                 std::string(sign < 0 ? "south" : "north") + "-pole-"
                   + std::to_string(octant),
                 {canonical_longitude(west[octant] + 45), sign * 90},
                 "pole");
    }
  return result;
}

fixture_layout
make_authagraph(const runtime::projection_context& projection)
{
  using namespace a60::carto::authagraph_detail;
  fixture_layout result {
    "authagraph/reference-a3", a60::carto::authagraph_width_to_height_ratio,
    "24 tetrahedral sectors; component 0",
    "periodic page copies and four singular vertices", {}};
  const auto& vertices = tetrahedron_vertices();
  for (std::size_t cell = 0; cell < cell_origins.size(); ++cell)
    {
      const std::size_t vertex = cell / 6;
      const double longitude
        = (-30 + 60 * static_cast<double>(cell % 6)) * pi / 180;
      const double latitude = 70 * pi / 180;
      const vector_3d pole = vertices[vertex];
      const vector_3d tangent
        = unit_tangent_toward(pole, vertices[(vertex + 1) % vertices.size()]);
      const vector_3d quarter_turn = cross(pole, tangent);
      const double cosine = std::cos(latitude);
      const vector_3d source {
        cosine * (std::cos(longitude) * tangent.x
                  + std::sin(longitude) * quarter_turn.x)
          + std::sin(latitude) * pole.x,
        cosine * (std::cos(longitude) * tangent.y
                  + std::sin(longitude) * quarter_turn.y)
          + std::sin(latitude) * pole.y,
        cosine * (std::cos(longitude) * tangent.z
                  + std::sin(longitude) * quarter_turn.z)
          + std::sin(latitude) * pole.z,
      };
      add_case(result, projection, "sector-" + two_digits(cell),
               coordinate_from_vector(source));
    }
  for (std::size_t vertex = 0; vertex < vertices.size(); ++vertex)
    add_case(result, projection, "singular-vertex-" + std::to_string(vertex),
             coordinate_from_vector(vertices[vertex]), "vertex");
  return result;
}

fixture_layout
make_dymaxion(const runtime::projection_context& projection)
{
  using namespace a60::carto::dymaxion_detail;
  fixture_layout result {
    "dymaxion/fuller-horizontal", a60::carto::dymaxion_width_to_height_ratio,
    "23 registered faces/subfaces; component 0",
    "icosahedral interruptions plus Australia and Japan subdivisions", {}};
  constexpr auto faces = spherical_faces();
  for (std::size_t face = 0; face < face_count; ++face)
    add_case(result, projection, "face-center-" + two_digits(face),
             coordinate_from_vector(normalized(
               faces[face][0] + faces[face][1] + faces[face][2])));

  std::vector<vector_3d> unique_vertices;
  std::vector<std::pair<vector_3d, vector_3d>> unique_edges;
  const auto same = [](const vector_3d& left, const vector_3d& right) {
    return std::abs(left.x - right.x) < 1e-14
           && std::abs(left.y - right.y) < 1e-14
           && std::abs(left.z - right.z) < 1e-14;
  };
  for (const auto& face : faces)
    {
      for (const vector_3d vertex : face)
        if (std::none_of(unique_vertices.begin(), unique_vertices.end(),
                         [&](const vector_3d& known) {
                           return same(vertex, known);
                         }))
          unique_vertices.push_back(vertex);
      for (std::size_t edge = 0; edge < 3; ++edge)
        {
          const vector_3d a = face[edge];
          const vector_3d b = face[(edge + 1) % 3];
          if (std::none_of(unique_edges.begin(), unique_edges.end(),
                           [&](const auto& known) {
                             return (same(a, known.first)
                                     && same(b, known.second))
                                    || (same(a, known.second)
                                        && same(b, known.first));
                           }))
            unique_edges.emplace_back(a, b);
        }
    }
  for (std::size_t edge = 0; edge < unique_edges.size(); ++edge)
    add_case(result, projection, "edge-" + two_digits(edge),
             coordinate_from_vector(normalized(
               unique_edges[edge].first + unique_edges[edge].second)),
             "edge");
  for (std::size_t vertex = 0; vertex < unique_vertices.size(); ++vertex)
    add_case(result, projection, "vertex-" + two_digits(vertex),
             coordinate_from_vector(unique_vertices[vertex]), "vertex");
  return result;
}

fixture_layout
make_myriahedral(const runtime::projection_context& projection)
{
  using namespace a60::carto::myriahedral_detail;
  fixture_layout result {
    std::string(projection.spec.argument),
    a60::carto::myriahedral_width_to_height_ratio,
    "5,120 terminal faces; component 0",
    "depth-five icosahedral spanning-tree interruptions", {}};
  const projection_layout& layout
    = std::get<a60::carto::myriaproj>(projection.projection).layout();
  result.cases.reserve(face_count);
  for (std::size_t face = 0; face < face_count; ++face)
    {
      const spherical_face& triangle = layout.spherical[face];
      add_case(result, projection, "face-center-" + std::to_string(face),
               coordinate_from_vector(normalized(
                 triangle[0] + triangle[1] + triangle[2])));
    }
  return result;
}

fixture_layout
make_star_x(const runtime::projection_context& projection)
{
  fixture_layout result {
    "star-x/fixed-60s", 34.0 / 44.0,
    "Cahill-Keyes carrier component 0 and unified Antarctic cap component 1",
    "fourfold carrier cuts, fixed 60S overlap, and cap quadrant cuts", {}};
  constexpr std::array longitude {-156.0, -66.0, 24.0, 114.0};
  for (std::size_t quadrant = 0; quadrant < longitude.size(); ++quadrant)
    for (const double latitude : {30.0, -30.0, -75.0})
      add_case(result, projection,
               "quadrant-" + std::to_string(quadrant) + "-latitude-"
                 + std::to_string(static_cast<int>(latitude)),
               {longitude[quadrant], latitude});
  for (std::size_t quadrant = 0; quadrant < longitude.size(); ++quadrant)
    add_case(result, projection, "cutoff-" + std::to_string(quadrant),
             {longitude[quadrant], -60}, "overlap");
  add_case(result, projection, "south-pole", {24, -90}, "pole");
  return result;
}

fixture_layout
make_voronoi(const runtime::projection_context& projection)
{
  using namespace a60::carto::voronoi_detail;
  fixture_layout result {
    "voronoi/d3-icosahedral", a60::carto::voronoi_width_to_height_ratio,
    "20 icosahedral Voronoi cells; component 0",
    "fixed face-tree interruptions", {}};
  const layout_data& data = layout();
  for (std::size_t face = 0; face < face_count; ++face)
    add_case(result, projection, "face-center-" + two_digits(face),
             coordinate_from_vector(data.faces[face].site,
                                    input_rotation_degrees));

  std::set<std::pair<std::size_t, std::size_t>> edges;
  for (const face_geometry& face : data.faces)
    for (std::size_t index = 0; index < 3; ++index)
      edges.emplace(std::min(face.vertices[index],
                             face.vertices[(index + 1) % 3]),
                    std::max(face.vertices[index],
                             face.vertices[(index + 1) % 3]));
  std::size_t edge_index = 0;
  for (const auto [left, right] : edges)
    add_case(result, projection, "edge-" + two_digits(edge_index++),
             coordinate_from_vector(normalized(
               data.vertices[left] + data.vertices[right]),
               input_rotation_degrees), "edge");
  for (std::size_t vertex = 0; vertex < data.vertices.size(); ++vertex)
    add_case(result, projection, "vertex-" + two_digits(vertex),
             coordinate_from_vector(data.vertices[vertex],
                                    input_rotation_degrees), "vertex");
  return result;
}

template<typename Writer>
void
write_pair(Writer& writer, const double first, const double second)
{
  writer.StartArray();
  writer.Double(first);
  writer.Double(second);
  writer.EndArray();
}

void
write_family(const fs::path& path, const std::string_view family,
             const runtime::projection_spec& topology_spec,
             const std::vector<fixture_layout>& layouts)
{
  std::ofstream stream(path);
  if (!stream)
    throw std::runtime_error("cannot write " + path.string());
  rj::OStreamWrapper wrapper(stream);
  rj::Writer<rj::OStreamWrapper> writer(wrapper);
  writer.SetMaxDecimalPlaces(17);
  writer.StartObject();
  writer.Key("schemaVersion");
  writer.String("cartofreako-projection-fixtures-v1");
  writer.Key("family");
  writer.String(family.data(), static_cast<rj::SizeType>(family.size()));
  writer.Key("coordinateContract");
  writer.StartObject();
  writer.Key("geographic"); writer.String("[longitude, latitude] degrees");
  writer.Key("projected"); writer.String("[u, v] normalized page coordinates");
  writer.Key("origin"); writer.String("top-left");
  writer.Key("xAxis"); writer.String("right");
  writer.Key("yAxis"); writer.String("down");
  writer.EndObject();
  writer.Key("layouts");
  writer.StartArray();
  for (const fixture_layout& layout : layouts)
    {
      writer.StartObject();
      writer.Key("layoutId"); writer.String(layout.id.c_str());
      writer.Key("nativeAspect"); writer.Double(layout.aspect);
      writer.Key("componentModel"); writer.String(layout.component_model.c_str());
      writer.Key("cutTopology"); writer.String(layout.cut_topology.c_str());
      writer.Key("cases");
      writer.StartArray();
      for (const fixture_case& one : layout.cases)
        {
          writer.StartObject();
          writer.Key("caseId"); writer.String(one.id.c_str());
          writer.Key("operation"); writer.String("forward-reverse");
          writer.Key("input"); writer.StartObject();
          writer.Key("geographic");
          write_pair(writer, one.input.longitude_degrees,
                     one.input.latitude_degrees);
          writer.EndObject();
          writer.Key("expected"); writer.StartObject();
          writer.Key("projected");
          write_pair(writer,
                     one.forward.point.x / topology_spec.width,
                     one.forward.point.y / topology_spec.height);
          writer.Key("topologyKey");
          writer.String(topology_key(topology_spec, one.forward.native_cell,
                                     one.forward.component).c_str());
          writer.Key("component"); writer.Uint(one.forward.component);
          writer.Key("reverseStatus");
          const std::string_view status = runtime::inverse_status_name(
            one.reverse.status);
          writer.String(status.data(), static_cast<rj::SizeType>(status.size()));
          writer.Key("reverseCandidates"); writer.StartArray();
          std::vector<runtime::inverse_candidate> candidates
            = one.reverse.candidates;
          std::sort(candidates.begin(), candidates.end(),
                    [&](const auto& left, const auto& right) {
                      return std::tuple(
                        topology_key(topology_spec, left.native_cell,
                                     left.component),
                        left.component, left.point.longitude_degrees,
                        left.point.latitude_degrees)
                        < std::tuple(
                          topology_key(topology_spec, right.native_cell,
                                       right.component),
                          right.component, right.point.longitude_degrees,
                          right.point.latitude_degrees);
                    });
          for (const runtime::inverse_candidate& candidate : candidates)
            {
              writer.StartObject();
              writer.Key("geographic");
              write_pair(writer, candidate.point.longitude_degrees,
                         candidate.point.latitude_degrees);
              writer.Key("topologyKey");
              writer.String(topology_key(topology_spec, candidate.native_cell,
                                         candidate.component).c_str());
              writer.Key("component"); writer.Uint(candidate.component);
              writer.Key("boundary"); writer.Bool(candidate.boundary);
              writer.EndObject();
            }
          writer.EndArray();
          writer.EndObject();
          writer.Key("boundaryClass"); writer.String(one.boundary_class.c_str());
          writer.Key("tolerances"); writer.StartObject();
          writer.Key("angularDegrees"); writer.Double(2e-8);
          writer.Key("normalizedPlanar"); writer.Double(1e-9);
          writer.EndObject();
          writer.Key("evidence"); writer.StartObject();
          writer.Key("grade"); writer.String(one.evidence_grade.c_str());
          writer.Key("source");
          writer.String(one.evidence_grade == "structural-invariant"
                          ? "declared spherical topology and registered layout"
                          : "Cartofreako API 3 compatibility observation");
          writer.Key("revision"); writer.Uint(1);
          writer.EndObject();
          writer.EndObject();
        }
      writer.EndArray();
      writer.EndObject();
    }
  writer.EndArray();
  writer.EndObject();
  stream << '\n';
}

} // namespace

int
main(const int argc, char** argv)
{
  if (argc != 2)
    {
      std::cerr << "usage: generate-projection-fixtures OUTPUT-DIRECTORY\n";
      return 2;
    }
  const fs::path output = argv[1];
  fs::create_directories(output);

  for (const std::string_view family : runtime::reference_projection_ids)
    {
      const runtime::projection_spec& spec
        = runtime::find_projection_spec(family);
      if (spec.kind == runtime::projection_kind::myriahedral)
        continue;
      const runtime::projection_context projection(spec);
      std::vector<fixture_layout> layouts;
      switch (spec.kind)
        {
        case runtime::projection_kind::cahill_keyes:
          layouts.push_back(make_cahill_keyes(projection)); break;
        case runtime::projection_kind::authagraph:
          layouts.push_back(make_authagraph(projection)); break;
        case runtime::projection_kind::dymaxion:
          layouts.push_back(make_dymaxion(projection)); break;
        case runtime::projection_kind::star_x:
          layouts.push_back(make_star_x(projection)); break;
        case runtime::projection_kind::voronoi:
          layouts.push_back(make_voronoi(projection)); break;
        case runtime::projection_kind::myriahedral: break;
        }
      write_family(output / (std::string(family) + ".json"), family,
                   spec, layouts);
    }

  std::vector<fixture_layout> myriahedral;
  for (const runtime::projection_spec& spec : runtime::projection_specs)
    if (spec.kind == runtime::projection_kind::myriahedral)
      {
        const runtime::projection_context projection(spec);
        myriahedral.push_back(make_myriahedral(projection));
      }
  const runtime::projection_spec& reference
    = runtime::find_projection_spec("myriahedral");
  write_family(output / "myriahedral.json", "myriahedral", reference,
               myriahedral);

  std::cout << "generated six-family projection fixtures in " << output
            << '\n';
}

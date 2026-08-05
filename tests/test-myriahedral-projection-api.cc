#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <limits>
#include <map>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>
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
#include "cart0freak0-myriahedral.h"

namespace {

struct expected_point
{
  double latitude;
  double longitude;
  double x;
  double y;
};

struct expected_vertex
{
  std::size_t face;
  std::size_t vertex;
  double x;
  double y;
};

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
  static_assert(std::is_base_of_v<projection_api, myriaproj>);
  static_assert(myriahedral_detail::face_count == 5120);
  static_assert(myriahedral_detail::tree_parent(
                  myriahedral_detail::mst_root)
                == myriahedral_detail::mst_root);

  const projection_api& api = myriahedral_source;
  assert(myriahedral_source.pmode == myriahedral);
  assert(myriahedral_source.pframe.width() == myriahedral_source_width);
  assert(myriahedral_source.pframe.height() == myriahedral_source_height);
  assert(is_myriahedral_frame(myriahedral_source.pframe));
  const auto [zero_x, zero_y] = api.meridians_to_point_2d(0, 0);
  assert(std::abs(zero_x - myriahedral_source.longitude_zero_x) < 1e-12);
  assert(std::abs(zero_y - myriahedral_source.latitude_zero_y) < 1e-12);

  constexpr auto source
    = "assets.static/myriahedral/black-white-downsampled.png";
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
         == "/opt/alpha60-data/assets.static/myriahedral/"
            "black-white-downsampled.png");
  a60::io::get_run_time_resources().data.clear();

  // Fixed gnomonic references for every coordinate used by
  // augment_carto_geo_specific: poles, antimeridian and supple-zone probes,
  // followed by its twelve cities. Geometric independence comes from the
  // exhaustive face, edge, barycentric, and hinge invariants below.
  constexpr std::array specific_locations {
    expected_point {0, 0, 2234.0946382632919, 1360.4176503986041},
    expected_point {89.9, 0, 2641.5578774400651, 574.63848085774964},
    expected_point {80, 0, 2608.2002375116294, 664.64794892032819},
    expected_point {-89.9, 0, 1446.3841794881898, 1929.8292890677212},
    expected_point {-80, 0, 1539.0443229456068, 1904.7590240718239},
    expected_point {0, 179.9, 4002.4531912568987, 1501.8205001167371},
    expected_point {0, 170, 3907.0767555304474, 1512.6720382856693},
    expected_point {0, -179.9, 668.07138177191791, 482.344305969777},
    expected_point {0, -170, 742.35435376411624, 543.14282934427899},
    expected_point {-80, -20, 1524.7205217174562, 1874.2259209881668},
    expected_point {-20, -19, 1972.2621615440046, 1439.3472586747137},
    expected_point {-20, -21, 1957.0281523070505, 1429.3596407160951},
    expected_point {-20, -23, 1941.6701887396953, 1419.5667096449286},
    expected_point {-56, -19, 1719.4708265422964, 1735.2647430211525},
    expected_point {-56, -23, 1705.4569218423223, 1718.7249756570347},
    expected_point {40.7128, -74.006, 1672.3958573173111,
                    673.85401928773956},
    expected_point {34.0549, -118.2426, 1351.3169747155021,
                    552.14748355199686},
    expected_point {48.8575, 2.3514, 2517.2713168562477,
                    972.38536265312666},
    expected_point {-29.8587, 31.0218, 2324.4886302700911,
                    1758.1059099108486},
    expected_point {28.7041, 77.1025, 3007.1162263011388,
                    1301.5810288107871},
    expected_point {35.6895, 139.6917, 3411.6272807983505,
                    956.66783739986192},
    expected_point {-33.8688, 151.2093, 3700.3724957139889,
                    1904.375996185518},
    expected_point {21.1444, -157.0226, 1073.0036311154079,
                    329.60577600167653},
    expected_point {-23.5558, -46.6396, 1737.6335529741,
                    1349.7523593381929},
    expected_point {64.147, -21.9408, 2474.2114772415334,
                    760.04661618545379},
    expected_point {-18.1266, 178.4399, 619.54911655649164,
                    1688.9237841985673},
    expected_point {-62.2001, 58.9642, 1688.027234976639,
                    2103.1843011014157},
  };

  for (const auto& expected : specific_locations)
    {
      const auto [x, y] = api.meridians_to_point_2d(
        expected.latitude, expected.longitude);
      assert(std::isfinite(x));
      assert(std::isfinite(y));
      assert(std::abs(x - expected.x) < 1e-9);
      assert(std::abs(y - expected.y) < 1e-9);
      assert(x >= 0 && x <= myriahedral_source_width);
      assert(y >= 0 && y <= myriahedral_source_height);
    }

  // Fixed references for the corrected unit mesh, signed seed embedding,
  // original SPHEmesh face order, and raster-registered spanning tree.
  const auto& layout = myriahedral_detail::layout();
  assert(std::abs(layout.minimum_x - -3.7949260457510388) < 2e-14);
  assert(std::abs(layout.minimum_y - -2.9255931761393548) < 2e-14);
  assert(std::abs(layout.maximum_x - 2.5709697873847457) < 2e-14);
  assert(std::abs(layout.maximum_y - 1.6095082079710128) < 2e-14);
  constexpr std::array layout_vertices {
    expected_vertex {0, 0, 0, 0},
    expected_vertex {0, 1, 0.062701082895108062,
                     -0.029237995128600328},
    expected_vertex {0, 2, 0.047226661568802147,
                     0.050556192424124478},
    expected_vertex {103, 0, 0.83414863173029163,
                     -0.36972395539775221},
    expected_vertex {103, 1, 0.81491143403496458,
                     -0.43885637108135206},
    expected_vertex {103, 2, 0.89150647631801005,
                     -0.41364177025496218},
    expected_vertex {5119, 0, -3.2705954776215069,
                     -0.63612967140212029},
    expected_vertex {5119, 1, -3.2091499068764469,
                     -0.58292241702457126},
    expected_vertex {5119, 2, -3.2765229398561528,
                     -0.5672010754000536},
  };
  for (const auto& expected : layout_vertices)
    {
      const auto actual = layout.planar[expected.face][expected.vertex];
      assert(std::abs(actual.x - expected.x) < 3e-14);
      assert(std::abs(actual.y - expected.y) < 3e-14);
    }

  // Construct projections directly from frame/frame_area at arbitrary
  // scales. Every reference coordinate must scale uniformly.
  const frame::area compact_dimensions {
    myriahedral_width_to_height_ratio * 100, 100
  };
  const frame::area large_dimensions {
    myriahedral_width_to_height_ratio * 6600, 6600
  };
  const std::array variable_frames {
    frame {myriahedral_width_to_height_ratio, 1},
    frame {16, 9},
    frame {compact_dimensions},
    frame {myriahedral_source_width, myriahedral_source_height},
    frame {large_dimensions},
    frame {myriahedral_width_to_height_ratio * 617.25, 617.25},
  };
  for (const frame& map_frame : variable_frames)
    {
      assert(is_myriahedral_frame(map_frame));
      const auto projection = make_myriahedral_projection(
        map_frame, "variable-myriahedral.png");
      assert(projection.pframe.frame_area._M_width == map_frame.width());
      assert(projection.pframe.frame_area._M_height == map_frame.height());
      assert(projection.pframe.moriginx == 0);
      assert(projection.pframe.moriginy == 0);
      assert(projection.image_filename(projection_base::filled)
             == "variable-myriahedral.png");

      const auto [origin_x, origin_y]
        = projection.meridians_to_point_2d(0, 0);
      assert(std::abs(origin_x - projection.longitude_zero_x) < 1e-9);
      assert(std::abs(origin_y - projection.latitude_zero_y) < 1e-9);

      const double factor = map_frame.height() / myriahedral_source_height;
      const double tolerance = 1e-9 * std::max(1.0, factor);
      for (const auto& expected : specific_locations)
        {
          const auto [x, y] = projection.meridians_to_point_2d(
            expected.latitude, expected.longitude);
          assert(std::abs(x - expected.x * factor) < tolerance);
          assert(std::abs(y - expected.y * factor) < tolerance);
          assert(x >= 0 && x <= map_frame.width());
          assert(y >= 0 && y <= map_frame.height());
        }
    }

  // Only frame_area controls the projection. Placement offsets belong to
  // cartography and are deliberately discarded by the factory.
  const frame positioned_frame {compact_dimensions, 17, 23};
  const auto positioned_projection
    = make_myriahedral_projection(positioned_frame);
  assert(positioned_projection.pframe.moriginx == 0);
  assert(positioned_projection.pframe.moriginy == 0);

  const auto rejects_frame = [](const frame& invalid_frame)
  {
    assert(!is_myriahedral_frame(invalid_frame));
    bool rejected = false;
    try
      {
        static_cast<void>(make_myriahedral_projection(invalid_frame));
      }
    catch (const std::invalid_argument&)
      {
        rejected = true;
      }
    assert(rejected);
  };
  rejects_frame(frame {2, 1});
  rejects_frame(frame {1920, 1080 + 0.001});
  rejects_frame(frame {1, 2});
  rejects_frame(frame {0, 0});
  rejects_frame(frame {-16, -9});
  rejects_frame(frame {std::numeric_limits<double>::infinity(), 1});
  rejects_frame(frame {std::numeric_limits<double>::max(),
                       std::numeric_limits<double>::max()});
  rejects_frame(frame {myriahedral_width_to_height_ratio,
                       std::numeric_limits<double>::quiet_NaN()});

  // The corrected unit mesh and unfolding preserve every terminal chord.
  constexpr double unit_tolerance
    = 4 * std::numeric_limits<double>::epsilon();
  for (std::size_t index = 0; index < layout.spherical.size(); ++index)
    {
      for (std::size_t vertex = 0; vertex < 3; ++vertex)
        assert(std::abs(myriahedral_detail::length(
                          layout.spherical[index][vertex]) - 1)
               <= unit_tolerance);
      for (std::size_t edge = 0; edge < 3; ++edge)
        {
          const std::size_t next = (edge + 1) % 3;
          const double spherical_length = myriahedral_detail::length(
            layout.spherical[index][next] - layout.spherical[index][edge]);
          const double planar_length = myriahedral_detail::length(
            layout.planar[index][next] - layout.planar[index][edge]);
          assert(std::abs(planar_length - spherical_length) < 2e-14);
        }
    }

  // The hierarchical search must recover every one of the 5120 leaves from
  // a point strictly inside that face. Central barycentrics recover a small
  // deterministic grid in the same face without negative weights.
  for (std::size_t index = 0; index < layout.spherical.size(); ++index)
    {
      const auto& face = layout.spherical[index];
      const auto centroid = myriahedral_detail::normalized(
        face[0] + face[1] + face[2]);
      assert(myriahedral_detail::containing_face(centroid) == index);

      constexpr int divisions = 4;
      for (int first = 0; first <= divisions; ++first)
        for (int second = 0; second <= divisions - first; ++second)
          {
            const int third = divisions - first - second;
            const auto value = myriahedral_detail::normalized(
              face[0] * (static_cast<double>(first) / divisions)
              + face[1] * (static_cast<double>(second) / divisions)
              + face[2] * (static_cast<double>(third) / divisions));
            const auto weights
              = myriahedral_detail::gnomonic_barycentric(face, value);
            constexpr long double barycentric_tolerance = 5e-15L;
            assert(weights.first >= -barycentric_tolerance);
            assert(weights.second >= -barycentric_tolerance);
            assert(weights.third >= -barycentric_tolerance);
            assert(std::abs(weights.first + weights.second + weights.third - 1)
                   < barycentric_tolerance);
            const auto raw = myriahedral_detail::project_on_face(
              face, layout.planar[index], value);
            const auto canvas
              = myriahedral_detail::normalize_planar_point(layout, raw);
            assert(canvas.x >= 0 && canvas.x <= 1);
            assert(canvas.y >= 0 && canvas.y <= 1);
          }
    }

  // Reconstruct exact mesh topology. Every geographic edge has two adjacent
  // faces; gnomonic images agree across all retained hinges and separate at
  // every omitted tree edge. Boundary probes select the expected side.
  using vertex_key = std::array<double, 3>;
  struct edge_record
  {
    std::array<std::size_t, 2> faces {};
    std::size_t count = 0;
  };
  std::map<vertex_key, std::size_t> vertex_indices;
  std::vector<myriahedral_detail::vector_3d> vertices;
  std::array<std::array<std::size_t, 3>,
             myriahedral_detail::face_count> face_vertices {};
  for (std::size_t face = 0; face < layout.spherical.size(); ++face)
    for (std::size_t vertex = 0; vertex < 3; ++vertex)
      {
        const auto value = layout.spherical[face][vertex];
        const vertex_key key {value.x, value.y, value.z};
        const auto [iterator, inserted]
          = vertex_indices.emplace(key, vertices.size());
        if (inserted)
          vertices.push_back(value);
        face_vertices[face][vertex] = iterator->second;
      }
  assert(vertices.size() == 2562);

  std::vector<std::set<std::size_t>> vertex_faces(vertices.size());
  for (std::size_t face = 0; face < face_vertices.size(); ++face)
    for (const std::size_t vertex : face_vertices[face])
      vertex_faces[vertex].insert(face);
  for (std::size_t vertex = 0; vertex < vertices.size(); ++vertex)
    {
      const std::size_t selected
        = myriahedral_detail::containing_face(vertices[vertex]);
      assert(vertex_faces[vertex].contains(selected));
      for (const std::size_t face : vertex_faces[vertex])
        {
          const auto& spherical = layout.spherical[face];
          const auto centroid = myriahedral_detail::normalized(
            spherical[0] + spherical[1] + spherical[2]);
          const auto probe = myriahedral_detail::normalized(
            vertices[vertex] + centroid * 1e-12);
          assert(myriahedral_detail::containing_face(probe) == face);
        }
    }

  std::map<std::pair<std::size_t, std::size_t>, edge_record> mesh_edges;
  for (std::size_t face = 0; face < layout.spherical.size(); ++face)
    for (std::size_t edge = 0; edge < 3; ++edge)
      {
        std::size_t first = face_vertices[face][edge];
        std::size_t second = face_vertices[face][(edge + 1) % 3];
        if (first > second)
          std::swap(first, second);
        edge_record& record = mesh_edges[{first, second}];
        assert(record.count < record.faces.size());
        record.faces[record.count++] = face;
      }
  assert(mesh_edges.size() == 7680);

  std::set<std::pair<std::size_t, std::size_t>> hinges;
  for (std::size_t face = 0; face < layout.spherical.size(); ++face)
    {
      const std::size_t parent = myriahedral_detail::tree_parent(face);
      if (face != parent)
        hinges.emplace(std::min(face, parent), std::max(face, parent));
    }
  assert(hinges.size() == myriahedral_detail::face_count - 1);

  std::size_t verified_hinges = 0;
  std::size_t verified_cuts = 0;
  for (const auto& [edge, record] : mesh_edges)
    {
      assert(record.count == 2);
      const auto midpoint = myriahedral_detail::normalized(
        vertices[edge.first] + vertices[edge.second]);
      const std::size_t selected
        = myriahedral_detail::containing_face(midpoint);
      assert(selected == record.faces[0] || selected == record.faces[1]);

      for (const std::size_t face : record.faces)
        {
          const auto& spherical = layout.spherical[face];
          const auto centroid = myriahedral_detail::normalized(
            spherical[0] + spherical[1] + spherical[2]);
          const auto probe = myriahedral_detail::normalized(
            midpoint + centroid * 1e-12);
          assert(myriahedral_detail::containing_face(probe) == face);
        }

      const auto face_pair = std::minmax(
        record.faces[0], record.faces[1]);
      const bool hinge = hinges.contains(face_pair);
      for (const double parameter : {0.25, 0.5, 0.75})
        {
          const auto value = myriahedral_detail::normalized(
            vertices[edge.first] * (1 - parameter)
            + vertices[edge.second] * parameter);
          const auto first = myriahedral_detail::project_on_face(
            layout, record.faces[0], value);
          const auto second = myriahedral_detail::project_on_face(
            layout, record.faces[1], value);
          const double separation = std::hypot(
            first.x - second.x, first.y - second.y);
          if (hinge)
            assert(separation < 5e-14);
          else
            assert(separation > 1e-8);
        }
      if (hinge)
        ++verified_hinges;
      else
        ++verified_cuts;
    }
  assert(verified_hinges == myriahedral_detail::face_count - 1);
  assert(verified_cuts == mesh_edges.size() - verified_hinges);

  // Independently compare hierarchical selection with an exhaustive terminal
  // scan for deterministic uniform random directions.
  std::mt19937_64 random(0x6d79726961686564ULL);
  std::uniform_real_distribution<double> unit(0, 1);
  for (std::size_t sample = 0; sample < 256; ++sample)
    {
      const double z = 2 * unit(random) - 1;
      const double angle = 2 * myriahedral_detail::pi * unit(random);
      const double radius = std::sqrt(std::max(0.0, 1 - z * z));
      const myriahedral_detail::vector_3d value {
        radius * std::cos(angle), radius * std::sin(angle), z
      };
      const std::size_t selected
        = myriahedral_detail::containing_face(value);
      std::size_t exhaustive = 0;
      double best = myriahedral_detail::containment_margin(
        layout.spherical[0], value);
      for (std::size_t face = 1; face < layout.spherical.size(); ++face)
        {
          const double margin = myriahedral_detail::containment_margin(
            layout.spherical[face], value);
          if (margin > best)
            {
              best = margin;
              exhaustive = face;
            }
        }
      assert(selected == exhaustive);
      assert(best >= 0);
    }

  // Exercise every whole-degree coordinate through the hierarchical face
  // selection, including poles, geographic quadrants, and map cuts.
  for (int latitude = -90; latitude <= 90; ++latitude)
    for (int longitude = -180; longitude <= 180; ++longitude)
      {
        const auto [x, y] = api.meridians_to_point_2d(latitude, longitude);
        assert(std::isfinite(x));
        assert(std::isfinite(y));
        assert(x >= 0 && x <= myriahedral_source_width);
        assert(y >= 0 && y <= myriahedral_source_height);

        const auto geographic = myriahedral_detail::geographic_vector(
          latitude, longitude);
        const std::size_t face
          = myriahedral_detail::containing_face(geographic);
        assert(myriahedral_detail::containment_margin(
                 layout.spherical[face], geographic) >= -1e-14);
      }

  // -180 and +180 are the same meridian and are canonicalized before face
  // selection, including when that coordinate lies on a cut.
  for (int latitude = -90; latitude <= 90; latitude += 5)
    {
      const auto west_vector
        = myriahedral_detail::geographic_vector(latitude, -180);
      const auto east_vector
        = myriahedral_detail::geographic_vector(latitude, 180);
      assert(west_vector.x == east_vector.x);
      assert(west_vector.y == east_vector.y);
      assert(west_vector.z == east_vector.z);
      assert(myriahedral_detail::containing_face(west_vector)
             == myriahedral_detail::containing_face(east_vector));

      const auto west = api.meridians_to_point_2d(latitude, -180);
      const auto east = api.meridians_to_point_2d(latitude, 180);
      assert(std::abs(std::get<0>(west) - std::get<0>(east)) < 1e-12);
      assert(std::abs(std::get<1>(west) - std::get<1>(east)) < 1e-12);
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

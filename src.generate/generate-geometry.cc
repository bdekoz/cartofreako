// Generate layered native geometry for the cartofreako projections.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iterator>
#include <string>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "projection-generation-common.h"

namespace {

namespace generation = cart0freak0::generation;
using generation::projection_context;
using generation::projection_kind;
using generation::projection_spec;
using a60::carto::frame;

constexpr double seam_epsilon = 1e-7;
constexpr double sample_step = 2.5;

struct longitude_sector
{
  double west;
  double east;
  int north_octant;
  int south_octant;
};

constexpr std::array cahill_keyes_sectors {
  longitude_sector {159, 249, 1, 6},
  longitude_sector {-111, -21, 2, 7},
  longitude_sector {-21, 69, 3, 8},
  longitude_sector {69, 159, 4, 5},
};

struct named_path
{
  std::string id;
  svg::vrange points;
};

double
canonical_longitude(double longitude)
{
  while (longitude > 180)
    longitude -= 360;
  while (longitude < -180)
    longitude += 360;
  return longitude;
}

void
append_projected(svg::vrange& points, const projection_context& context,
                 const double latitude, const double longitude)
{
  generation::append_unique(points, generation::project_point(
    context, {latitude, canonical_longitude(longitude)}));
}

void
append_parallel(svg::vrange& points, const projection_context& context,
                const double latitude, const double longitude_begin,
                const double longitude_end)
{
  const double direction = longitude_end >= longitude_begin ? 1 : -1;
  for (double longitude = longitude_begin;
       direction * (longitude_end - longitude) > 0;
       longitude += direction * sample_step)
    append_projected(points, context, latitude, longitude);
  append_projected(points, context, latitude, longitude_end);
}

void
append_meridian(svg::vrange& points, const projection_context& context,
                const double longitude, const double latitude_begin,
                const double latitude_end)
{
  const double direction = latitude_end >= latitude_begin ? 1 : -1;
  for (double latitude = latitude_begin;
       direction * (latitude_end - latitude) > 0;
       latitude += direction * sample_step)
    append_projected(points, context, latitude, longitude);
  append_projected(points, context, latitude_end, longitude);
}

double
sector_center(const longitude_sector& sector)
{ return (sector.west + sector.east) / 2; }

svg::vrange
make_octant_outline(const projection_context& context,
                    const longitude_sector& sector,
                    const double hemisphere)
{
  const double west = sector.west + seam_epsilon;
  const double east = sector.east - seam_epsilon;
  const double center = sector_center(sector);
  const double pole = hemisphere * 90;
  const double near_pole = hemisphere * (90 - seam_epsilon);

  svg::vrange points;
  append_parallel(points, context, 0, west, east);
  append_meridian(points, context, east, 0, near_pole);
  append_projected(points, context, pole, center);
  append_meridian(points, context, west, near_pole, 0);
  return points;
}

svg::vrange
make_half_octant_outline(const projection_context& context,
                         const longitude_sector& sector,
                         const double hemisphere,
                         const bool eastern_half)
{
  const double west = sector.west + seam_epsilon;
  const double east = sector.east - seam_epsilon;
  const double center = sector_center(sector);
  const double pole = hemisphere * 90;
  const double near_pole = hemisphere * (90 - seam_epsilon);

  svg::vrange points;
  if (eastern_half)
    {
      append_parallel(points, context, 0, center, east);
      append_meridian(points, context, east, 0, near_pole);
      append_projected(points, context, pole, center);
      append_meridian(points, context, center, near_pole, 0);
    }
  else
    {
      append_parallel(points, context, 0, west, center);
      append_meridian(points, context, center, 0, near_pole);
      append_projected(points, context, pole, center);
      append_meridian(points, context, west, near_pole, 0);
    }
  return points;
}

std::vector<named_path>
make_quadrants(const frame& map_frame)
{
  std::vector<named_path> paths;
  const double quadrant_width = map_frame.width() / 4;
  for (int quadrant = 0; quadrant != 4; ++quadrant)
    {
      const double x0 = quadrant * quadrant_width;
      const double x1 = (quadrant + 1) * quadrant_width;
      paths.push_back({
        "quadrant-" + std::to_string(quadrant + 1),
        {{x0, 0}, {x1, 0}, {x1, map_frame.height()},
         {x0, map_frame.height()}},
      });
    }
  return paths;
}

std::vector<named_path>
make_cahill_keyes_faces(const projection_context& context,
                        std::vector<named_path>& octants,
                        std::vector<named_path>& half_octants)
{
  std::vector<named_path> triangular_faces;
  for (const longitude_sector& sector : cahill_keyes_sectors)
    for (const auto [hemisphere, octant]
         : std::array<std::pair<double, int>, 2> {
             std::pair {1.0, sector.north_octant},
             std::pair {-1.0, sector.south_octant},
           })
      {
        const std::string number = std::to_string(octant);
        svg::vrange outline = make_octant_outline(
          context, sector, hemisphere);
        triangular_faces.push_back({"triangular-face-" + number, outline});
        octants.push_back({"octant-" + number, std::move(outline)});
        half_octants.push_back({
          "half-octant-" + number + "-west",
          make_half_octant_outline(context, sector, hemisphere, false),
        });
        half_octants.push_back({
          "half-octant-" + number + "-east",
          make_half_octant_outline(context, sector, hemisphere, true),
        });
      }
  return triangular_faces;
}

std::vector<named_path>
make_star_x_polar_marks(const frame& map_frame)
{
  svg::vrange star;
  for (const auto point
       : a60::carto::star_x_detail::make_north_pole_star(map_frame))
    star.push_back({point.x, point.y});
  return {{"north-pole-star", std::move(star)}};
}

struct unit_point
{
  double x;
  double y;
};

struct unit_triangle
{
  unit_point points[3];
};

constexpr std::array authagraph_triangles {
  unit_triangle {{{.5, 0}, {.375, .5}, {.25, 1.0 / 3}}},
  unit_triangle {{{.5, 0}, {.375, .5}, {.5, 2.0 / 3}}},
  unit_triangle {{{.5, 0}, {.625, .5}, {.5, 2.0 / 3}}},
  unit_triangle {{{.5, 0}, {.625, .5}, {.75, 1.0 / 3}}},
  unit_triangle {{{.5, 0}, {.75, 0}, {.75, 1.0 / 3}}},
  unit_triangle {{{.5, 0}, {.25, 0}, {.25, 1.0 / 3}}},
  unit_triangle {{{.25, 1}, {0, 1}, {0, 2.0 / 3}}},
  unit_triangle {{{.25, 1}, {.5, 1}, {.5, 2.0 / 3}}},
  unit_triangle {{{.25, 1}, {.375, .5}, {.5, 2.0 / 3}}},
  unit_triangle {{{.25, 1}, {.375, .5}, {.25, 1.0 / 3}}},
  unit_triangle {{{.25, 1}, {.125, .5}, {.25, 1.0 / 3}}},
  unit_triangle {{{.25, 1}, {.125, .5}, {0, 2.0 / 3}}},
  unit_triangle {{{.75, 1}, {.875, .5}, {1, 2.0 / 3}}},
  unit_triangle {{{.75, 1}, {.875, .5}, {.75, 1.0 / 3}}},
  unit_triangle {{{.75, 1}, {.625, .5}, {.75, 1.0 / 3}}},
  unit_triangle {{{.75, 1}, {.625, .5}, {.5, 2.0 / 3}}},
  unit_triangle {{{.75, 1}, {.5, 1}, {.5, 2.0 / 3}}},
  unit_triangle {{{.75, 1}, {1, 1}, {1, 2.0 / 3}}},
  unit_triangle {{{0, 0}, {.25, 0}, {.25, 1.0 / 3}}},
  unit_triangle {{{1, 0}, {.75, 0}, {.75, 1.0 / 3}}},
  unit_triangle {{{1, 0}, {.875, .5}, {.75, 1.0 / 3}}},
  unit_triangle {{{1, 0}, {.875, .5}, {1, 2.0 / 3}}},
  unit_triangle {{{0, 0}, {.125, .5}, {0, 2.0 / 3}}},
  unit_triangle {{{0, 0}, {.125, .5}, {.25, 1.0 / 3}}},
};

std::vector<unit_point>
clip_x(const std::vector<unit_point>& source, const double boundary,
       const bool keep_greater)
{
  std::vector<unit_point> result;
  if (source.empty())
    return result;
  auto inside = [boundary, keep_greater](const unit_point point) {
    return keep_greater ? point.x >= boundary : point.x <= boundary;
  };
  unit_point previous = source.back();
  bool previous_inside = inside(previous);
  for (const unit_point current : source)
    {
      const bool current_inside = inside(current);
      if (current_inside != previous_inside)
        {
          const double fraction
            = (boundary - previous.x) / (current.x - previous.x);
          result.push_back({boundary,
                            previous.y
                              + fraction * (current.y - previous.y)});
        }
      if (current_inside)
        result.push_back(current);
      previous = current;
      previous_inside = current_inside;
    }
  return result;
}

std::vector<named_path>
make_authagraph_faces(const projection_context& context)
{
  std::vector<named_path> result;
  for (std::size_t sector = 0; sector < authagraph_triangles.size(); ++sector)
    for (int copy = -1; copy <= 1; ++copy)
      {
        std::vector<unit_point> polygon;
        for (const unit_point point : authagraph_triangles[sector].points)
          polygon.push_back({
            point.x + a60::carto::authagraph_detail::horizontal_shift + copy,
            point.y,
          });
        polygon = clip_x(polygon, 0, true);
        polygon = clip_x(polygon, 1, false);
        if (polygon.size() >= 3)
        {
          svg::vrange points;
          for (const unit_point point : polygon)
            points.push_back({point.x * context.map_frame.width(),
                              point.y * context.map_frame.height()});
          result.push_back({
            "triangular-face-" + std::to_string(sector + 1)
              + "-copy-" + std::to_string(copy + 2),
            std::move(points),
          });
        }
      }
  generation::require(result.size() >= 24,
                      "AuthaGraph must produce all 24 triangular sectors");
  return result;
}

svg::point_2t
normalize_myriahedral(const a60::carto::myriahedral_detail::point_2d point,
                      const frame& map_frame)
{
  using namespace a60::carto::myriahedral_detail;
  const auto& projection = layout();
  const double extent_x = projection.maximum_x - projection.minimum_x;
  const double extent_y = projection.maximum_y - projection.minimum_y;
  const double scale = std::min(
    a60::carto::myriahedral_width_to_height_ratio / extent_x,
    1 / extent_y);
  const double left = (a60::carto::myriahedral_width_to_height_ratio
                       - extent_x * scale) / 2;
  const double bottom = (1 - extent_y * scale) / 2;
  return {(left + (point.x - projection.minimum_x) * scale)
            / a60::carto::myriahedral_width_to_height_ratio
            * map_frame.width(),
          (1 - (bottom + (point.y - projection.minimum_y) * scale))
            * map_frame.height()};
}

std::vector<named_path>
make_myriahedral_faces(const projection_context& context)
{
  const auto& planar = a60::carto::myriahedral_detail::layout().planar;
  std::vector<named_path> result;
  result.reserve(planar.size());
  for (std::size_t index = 0; index < planar.size(); ++index)
    {
      svg::vrange points;
      for (const auto point : planar[index])
        points.push_back(normalize_myriahedral(point, context.map_frame));
      result.push_back({
        "triangular-face-" + std::to_string(index + 1), std::move(points),
      });
    }
  return result;
}

svg::point_2t
normalize_voronoi(const a60::carto::voronoi_detail::point_2d raw,
                  const frame& map_frame)
{
  using namespace a60::carto::voronoi_detail;
  static const point_2d registration = project_to_unfolded_net(
    0, registration_longitude_degrees);
  return {(source_center_x + source_scale * (raw.x - registration.x))
            / a60::carto::voronoi_source_width * map_frame.width(),
          (source_center_y - source_scale * (raw.y - registration.y))
            / a60::carto::voronoi_source_height * map_frame.height()};
}

std::vector<named_path>
make_voronoi_faces(const projection_context& context)
{
  using namespace a60::carto::voronoi_detail;
  const auto& data = layout();
  std::vector<named_path> result;
  result.reserve(data.faces.size());
  for (std::size_t index = 0; index < data.faces.size(); ++index)
    {
      const face_geometry& face = data.faces[index];
      svg::vrange points;
      for (const std::size_t vertex_index : face.vertices)
        {
          const point_2d local = project_on_face(
            face, data.vertices[vertex_index]);
          const point_2d transformed = apply(face.transform, local);
          points.push_back(normalize_voronoi(
            {transformed.x, -transformed.y}, context.map_frame));
        }
      result.push_back({
        "triangular-face-" + std::to_string(index + 1), std::move(points),
      });
    }
  return result;
}

std::vector<named_path>
make_dymaxion_faces(const projection_context& context)
{
  constexpr auto planar = a60::carto::dymaxion_detail::planar_faces();
  std::vector<named_path> result;
  result.reserve(planar.size());
  for (std::size_t index = 0; index < planar.size(); ++index)
    {
      svg::vrange points;
      for (const auto point : planar[index])
        {
          const auto normalized
            = a60::carto::dymaxion_detail::normalize_planar_point(point);
          points.push_back({normalized.x * context.map_frame.width(),
                            normalized.y * context.map_frame.height()});
        }
      result.push_back({
        "triangular-face-" + std::to_string(index + 1), std::move(points),
      });
    }
  return result;
}

void
add_path_layer(svg::svg_element& document, const std::string& layer_id,
               const std::vector<named_path>& paths, const svg::style& style)
{
  svg::group_element layer;
  layer.start_element(layer_id);
  for (const named_path& path : paths)
    {
      generation::require(path.points.size() >= 3,
                          "geometry path has too few points: " + path.id);
      std::string path_data = svg::make_path_data_from_points(path.points);
      path_data += "Z";
      layer.add_element(svg::make_path(path_data, style, path.id));
    }
  layer.finish_element();
  document.add_element(layer);
}

std::size_t
layer_path_count(const std::string& document, const std::string& layer_id)
{
  const std::string opening = "<g id=\"" + layer_id + "\">";
  const std::size_t begin = document.find(opening);
  generation::require(begin != std::string::npos,
                      "generated SVG is missing layer " + layer_id);
  const std::size_t end = document.find("</g>", begin);
  generation::require(end != std::string::npos,
                      "generated SVG has an unterminated layer " + layer_id);
  std::size_t count = 0;
  std::size_t position = begin;
  while ((position = document.find("<path ", position)) != std::string::npos
         && position < end)
    {
      ++count;
      ++position;
    }
  return count;
}

void
generate_geometry(const projection_spec& spec)
{
  const std::string basename = generation::output_basename("geometry", spec);
  const projection_context context(spec, basename);
  std::vector<named_path> octants;
  std::vector<named_path> half_octants;
  std::vector<named_path> faces;
  switch (spec.kind)
    {
    case projection_kind::cahill_keyes:
    case projection_kind::star_x:
      faces = make_cahill_keyes_faces(context, octants, half_octants);
      break;
    case projection_kind::authagraph:
      faces = make_authagraph_faces(context);
      break;
    case projection_kind::dymaxion:
      faces = make_dymaxion_faces(context);
      break;
    case projection_kind::myriahedral:
      faces = make_myriahedral_faces(context);
      break;
    case projection_kind::voronoi:
      faces = make_voronoi_faces(context);
      break;
    }

  const svg::style face_style {
    svg::color::gray05, 0.55, svg::color::gray50, 0.60, 0.04,
  };
  const svg::style quadrant_style {
    svg::color::none, 0, svg::color::blue, 0.65, 0.08,
  };
  const svg::style octant_style {
    svg::color::none, 0, svg::color::black, 0.90, 0.12,
  };
  const svg::style half_octant_style {
    svg::color::none, 0, svg::color::red, 0.70, 0.055,
  };
  const svg::style polar_mark_style {
    svg::color::black, 1, svg::color::black, 1, 0.01,
  };

  generation::projection_document document(
    basename, std::string(spec.title) + " native projection geometry",
    context.map_frame.frame_area);
  add_path_layer(document, "triangular-faces", faces, face_style);
  add_path_layer(document, "quadrants",
                 make_quadrants(context.map_frame), quadrant_style);
  if (!octants.empty())
    {
      add_path_layer(document, "octants", octants, octant_style);
      add_path_layer(
        document, "half-octants", half_octants, half_octant_style);
    }
  if (spec.kind == projection_kind::star_x)
    add_path_layer(document, "polar-marks",
                   make_star_x_polar_marks(context.map_frame),
                   polar_mark_style);
}

} // namespace

int
main(const int argc, char** argv)
{
  const projection_spec& spec = generation::projection_from_arguments(
    argc, argv);
  const std::string basename = generation::output_basename("geometry", spec);
  const projection_context context(spec, basename);
  generate_geometry(spec);

  std::ifstream input {basename + ".svg"};
  generation::require(input.good(),
                      "failed to open generated " + basename + ".svg");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  generation::require(
    generated.find(generation::view_box_fragment(context))
      != std::string::npos,
    "generated geometry SVG does not use the requested viewBox");
  const std::size_t expected_faces
    = spec.kind == projection_kind::myriahedral ? 5120
      : spec.kind == projection_kind::dymaxion ? 23
      : spec.kind == projection_kind::voronoi ? 20 : 8;
  const std::size_t face_paths = layer_path_count(
    generated, "triangular-faces");
  if (spec.kind == projection_kind::authagraph)
    generation::require(face_paths >= 24,
                        "AuthaGraph geometry omits triangular sectors");
  else
    generation::require(face_paths == expected_faces,
                        "geometry contains the wrong number of faces");
  generation::require(layer_path_count(generated, "quadrants") == 4,
                      "quadrants layer must contain four paths");
  if (spec.kind == projection_kind::cahill_keyes
      || spec.kind == projection_kind::star_x)
    {
      generation::require(layer_path_count(generated, "octants") == 8,
                          "octants layer must contain eight paths");
      generation::require(
        layer_path_count(generated, "half-octants") == 16,
        "half-octants layer must contain sixteen paths");
    }
  if (spec.kind == projection_kind::star_x)
    generation::require(layer_path_count(generated, "polar-marks") == 1,
                        "Star-X polar marks must contain one star path");
  generation::require(generated.find("nan") == std::string::npos
                      && generated.find("inf") == std::string::npos,
                      "generated SVG contains a non-finite coordinate");
}

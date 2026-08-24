// Generate labeled graticules for the cartofreako projections.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iterator>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include <a60-io.h>
#include <izzi-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"

namespace {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;
using generation::geographic_point;
using generation::projection_context;
using generation::projection_kind;
using generation::projection_spec;

constexpr int graticule_step = 10;
constexpr double sample_step = 0.5;
constexpr double seam_epsilon = 1e-7;

struct longitude_sector
{
  double west;
  double east;
};

constexpr std::array cahill_keyes_sectors {
  longitude_sector {159, 249},
  longitude_sector {-111, -21},
  longitude_sector {-21, 69},
  longitude_sector {69, 159},
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

std::vector<geographic_point>
sample_parallel(const double latitude, const double west, const double east)
{
  std::vector<geographic_point> result;
  for (double longitude = west; longitude < east; longitude += sample_step)
    result.push_back({latitude, canonical_longitude(longitude)});
  result.push_back({latitude, canonical_longitude(east)});
  return result;
}

std::vector<geographic_point>
sample_meridian(const double longitude, const double south,
                const double north)
{
  std::vector<geographic_point> result;
  for (double latitude = south; latitude < north; latitude += sample_step)
    result.push_back({latitude, longitude});
  result.push_back({north, longitude});
  return result;
}

geographic_point
interpolate_cap_edge(const geographic_point left,
                     geographic_point right, const double fraction)
{
  if (right.longitude - left.longitude > 180)
    right.longitude -= 360;
  else if (right.longitude - left.longitude < -180)
    right.longitude += 360;
  return {
    left.latitude + fraction * (right.latitude - left.latitude),
    canonical_longitude(
      left.longitude + fraction * (right.longitude - left.longitude)),
  };
}

struct cap_path_piece
{
  bool inside = false;
  std::vector<geographic_point> points;
};

std::vector<cap_path_piece>
split_at_antarctic_cap(const natural_earth::antarctic_cap& cap,
                       const std::vector<geographic_point>& source)
{
  std::vector<cap_path_piece> result;
  if (source.empty())
    return result;
  result.push_back({cap.contains(source.front()), {source.front()}});
  for (std::size_t index = 1; index < source.size(); ++index)
    {
      const geographic_point right = source[index];
      if (cap.contains(right) == result.back().inside)
        {
          result.back().points.push_back(right);
          continue;
        }

      geographic_point same_side = source[index - 1];
      geographic_point other_side = right;
      for (int iteration = 0; iteration != 56; ++iteration)
        {
          const geographic_point middle
            = interpolate_cap_edge(same_side, other_side, 0.5);
          if (cap.contains(middle) == result.back().inside)
            same_side = middle;
          else
            other_side = middle;
        }
      result.back().points.push_back(same_side);
      result.push_back({!result.back().inside, {other_side, right}});
    }
  return result;
}

std::vector<svg::vrange>
project_cap_path(const projection_context& context,
                 const natural_earth::antarctic_cap* cap,
                 const std::vector<geographic_point>& source)
{
  if (cap == nullptr)
    return generation::project_path(context, source, false);

  std::vector<svg::vrange> result;
  for (const cap_path_piece& piece : split_at_antarctic_cap(*cap, source))
    {
      if (!piece.inside)
        {
          std::vector<svg::vrange> outside
            = generation::project_path(context, piece.points, false);
          for (svg::vrange& points : outside)
            if (points.size() >= 2)
              result.push_back(std::move(points));
          continue;
        }
      svg::vrange projected;
      projected.reserve(piece.points.size());
      for (const geographic_point point : piece.points)
        generation::append_unique(projected, cap->project(point));
      if (projected.size() >= 2)
        result.push_back(std::move(projected));
    }
  return result;
}

void
append_segments(std::vector<svg::vrange>& destination,
                std::vector<svg::vrange> source)
{
  for (svg::vrange& points : source)
    if (points.size() >= 2)
      destination.push_back(std::move(points));
}

std::vector<svg::vrange>
make_parallel_segments(const projection_context& context,
                       const double latitude,
                       const natural_earth::antarctic_cap* cap)
{
  std::vector<svg::vrange> result;
  if (context.spec.kind == projection_kind::cahill_keyes
      || context.spec.kind == projection_kind::star_x)
    {
      for (const longitude_sector sector : cahill_keyes_sectors)
        append_segments(result, project_cap_path(
          context,
          cap,
          sample_parallel(latitude, sector.west + seam_epsilon,
                          sector.east - seam_epsilon)));
    }
  else
    append_segments(result, generation::project_path(
      context, sample_parallel(latitude, -180 + seam_epsilon,
                               180 - seam_epsilon), false));
  return result;
}

std::vector<svg::vrange>
make_meridian_segments(const projection_context& context,
                       const double longitude,
                       const natural_earth::antarctic_cap* cap)
{
  std::vector<svg::vrange> result;
  if (context.spec.kind == projection_kind::cahill_keyes
      || context.spec.kind == projection_kind::star_x)
    {
      append_segments(result, project_cap_path(
        context, cap, sample_meridian(longitude, -90, 0)));
      append_segments(result, generation::project_path(
        context, sample_meridian(longitude, 0, 90), false));
    }
  else
    append_segments(result, generation::project_path(
      context, sample_meridian(longitude, -90, 90), false));
  return result;
}

void
add_antarctic_cap_boundaries(
  generation::projection_document& document,
  const projection_context& context,
  const natural_earth::antarctic_cap& cap)
{
  const svg::style style {
    svg::color::none, 0, svg::color::gray50, 0.55, 0.022,
  };
  svg::group_element layer;
  layer.start_element("antarctic-cap-boundaries");
  layer.add_title(
    "Fixed 60-degree-South source cuts and data-independent unified cap "
    "boundary; maximum projected radius=" + std::to_string(cap.radius)
    + "; bottom clearance=" + std::to_string(cap.bottom_clearance));

  svg::vrange unified;
  constexpr double longitude_step
    = 360.0 / a60::carto::star_x_antarctic_boundary_sample_count;
  for (double longitude = -180; longitude < 180;
       longitude += longitude_step)
    unified.push_back(cap.project(
      {cap.boundary_latitude(longitude), longitude}));
  unified.push_back(unified.front());
  layer.add_element(svg::make_path(
    svg::make_path_data_from_points(unified), style,
    "antarctic-unified-cap-boundary"));

  for (std::size_t index = 0; index != natural_earth::longitude_bands.size();
       ++index)
    {
      const natural_earth::longitude_band band
        = natural_earth::longitude_bands[index];
      svg::vrange source;
      for (double longitude = band.west; longitude < band.east;
           longitude += longitude_step)
        source.push_back(generation::project_point(
          context, {cap.boundary_latitude(longitude), longitude}));
      source.push_back(generation::project_point(
        context, {cap.boundary_latitude(band.east), band.east}));
      layer.add_element(svg::make_path(
        svg::make_path_data_from_points(source), style,
        "antarctic-source-cap-boundary-" + std::to_string(index + 1)));
    }
  layer.finish_element();
  document.add_element(layer);
}

std::string
coordinate_id(const std::string_view kind, const int coordinate,
              const std::string_view negative,
              const std::string_view positive)
{
  std::string id(kind);
  id += '-' + std::to_string(std::abs(coordinate));
  if (coordinate < 0)
    id += '-' + std::string(negative);
  else if (coordinate > 0)
    id += '-' + std::string(positive);
  return id;
}

std::string
coordinate_label(const int coordinate, const std::string_view negative,
                 const std::string_view positive,
                 const bool unsigned_antimeridian = false)
{
  std::string label = std::to_string(std::abs(coordinate)) + "\u00b0";
  if (unsigned_antimeridian && std::abs(coordinate) == 180)
    return label;
  if (coordinate < 0)
    label += negative;
  else if (coordinate > 0)
    label += positive;
  return label;
}

svg::typography
make_label_typography(const svg::color color)
{
  svg::typography typography = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  typography._M_size = 0.25;
  typography._M_style = {color, 0.95, svg::color::white, 0, 0};
  typography._M_anchor = svg::typography::anchor::middle;
  typography._M_align = svg::typography::align::center;
  typography._M_baseline = svg::typography::baseline::central;
  return typography;
}

double
path_length(const svg::vrange& points)
{
  double result = 0;
  for (std::size_t index = 1; index < points.size(); ++index)
    result += generation::point_distance(points[index - 1], points[index]);
  return result;
}

svg::point_2t
label_point(const std::vector<svg::vrange>& segments)
{
  generation::require(!segments.empty(),
                      "graticule line produced no projected segments");
  const auto longest = std::max_element(
    segments.begin(), segments.end(),
    [](const svg::vrange& left, const svg::vrange& right) {
      return path_length(left) < path_length(right);
    });
  return (*longest)[longest->size() / 2];
}

void
add_labeled_line(svg::group_element& layer, const std::string& id,
                 const std::string& label,
                 const std::vector<svg::vrange>& segments,
                 const svg::style& style,
                 const svg::typography& typography)
{
  generation::require(!segments.empty(),
                      "graticule line has no visible segments: " + id);
  svg::group_element line;
  line.start_element(id);
  line.add_title(label);
  for (std::size_t index = 0; index < segments.size(); ++index)
    {
      generation::require(segments[index].size() >= 2,
                          "graticule path has too few points");
      line.add_element(svg::make_path(
        svg::make_path_data_from_points(segments[index]), style,
        id + "-segment-" + std::to_string(index + 1)));
    }
  svg::styled_text(line, label, label_point(segments), typography);
  line.finish_element();
  layer.add_element(line);
}

std::string_view
layer_section(const std::string& document, const std::string& layer_id,
              const std::string& next_marker)
{
  const std::string opening = "<g id=\"" + layer_id + "\">";
  const std::size_t begin = document.find(opening);
  generation::require(begin != std::string::npos,
                      "generated SVG is missing layer " + layer_id);
  const std::size_t end = document.find(next_marker, begin + opening.size());
  generation::require(end != std::string::npos,
                      "generated SVG has an unterminated layer " + layer_id);
  return std::string_view(document).substr(begin, end - begin);
}

std::size_t
token_count(const std::string_view text, const std::string_view token)
{
  std::size_t count = 0;
  std::size_t position = 0;
  while ((position = text.find(token, position)) != std::string_view::npos)
    {
      ++count;
      position += token.size();
    }
  return count;
}

void
generate_graticules(const projection_spec& spec)
{
  const std::string basename = generation::output_basename(
    "graticules", spec);
  const projection_context context(spec, basename);
  std::optional<natural_earth::antarctic_cap> polar_cap;
  if (spec.kind == projection_kind::star_x)
    {
      natural_earth::initialize_gdal();
      polar_cap.emplace(natural_earth::make_antarctic_cap(context));
    }
  const natural_earth::antarctic_cap* cap
    = polar_cap.has_value() ? &*polar_cap : nullptr;
  const svg::style latitude_style {
    svg::color::none, 0, svg::color_qi {189, 199, 246}, 0.55, 0.025,
  };
  const svg::style latitude_major_style {
    svg::color::none, 0, svg::color_qi {168, 180, 240}, 0.80, 0.045,
  };
  const svg::style longitude_style {
    svg::color::none, 0, svg::color_qi {238, 167, 171}, 0.50, 0.025,
  };
  const svg::style longitude_major_style {
    svg::color::none, 0, svg::color_qi {224, 130, 138}, 0.75, 0.045,
  };
  const svg::typography latitude_typography
    = make_label_typography(svg::color::blue);
  const svg::typography longitude_typography
    = make_label_typography(svg::color::red);

  generation::projection_document document(
    basename, "Labeled ten-degree graticules for the "
                + std::string(spec.title) + " projection",
    context.map_frame.frame_area);

  svg::group_element latitude_layer;
  latitude_layer.start_element("latitudes");
  for (int latitude = -80; latitude <= 80; latitude += graticule_step)
    {
      const std::string id = coordinate_id(
        "latitude", latitude, "south", "north");
      add_labeled_line(
        latitude_layer, id, coordinate_label(latitude, "S", "N"),
        make_parallel_segments(context, latitude, cap),
        latitude % 30 == 0 ? latitude_major_style : latitude_style,
        latitude_typography);
    }
  latitude_layer.finish_element();
  document.add_element(latitude_layer);

  svg::group_element longitude_layer;
  longitude_layer.start_element("longitudes");
  for (int longitude = -180; longitude < 180; longitude += graticule_step)
    {
      const std::string id = coordinate_id(
        "longitude", longitude, "west", "east");
      add_labeled_line(
        longitude_layer, id,
        coordinate_label(longitude, "W", "E", true),
        make_meridian_segments(context, longitude, cap),
        longitude % 30 == 0 ? longitude_major_style : longitude_style,
        longitude_typography);
    }
  longitude_layer.finish_element();
  document.add_element(longitude_layer);

  if (cap != nullptr)
    add_antarctic_cap_boundaries(document, context, *cap);
}

} // namespace

int
main(const int argc, char** argv)
{
  const projection_spec& spec = generation::projection_from_arguments(
    argc, argv);
  const std::string basename = generation::output_basename(
    "graticules", spec);
  const projection_context context(spec, basename);
  generate_graticules(spec);

  std::ifstream input {basename + ".svg"};
  generation::require(input.good(),
                      "failed to open generated " + basename + ".svg");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  generation::require(
    generated.find(generation::view_box_fragment(context))
      != std::string::npos,
    "generated graticule SVG does not use the requested viewBox");
  const std::string_view latitudes = layer_section(
    generated, "latitudes", "<g id=\"longitudes\">");
  const std::string_view longitudes = layer_section(
    generated, "longitudes", "</svg>");
  generation::require(token_count(latitudes, "<g id=\"latitude-") == 17,
                      "latitudes layer must have seventeen line groups");
  generation::require(token_count(longitudes, "<g id=\"longitude-") == 36,
                      "longitudes layer must have thirty-six line groups");
  generation::require(token_count(latitudes, "<path ") >= 17
                      && token_count(longitudes, "<path ") >= 36,
                      "every graticule must have a visible path");
  generation::require(token_count(latitudes, "<text ") == 17
                      && token_count(longitudes, "<text ") == 36,
                      "every graticule must have one visible label");
  generation::require(token_count(generated, "\u00b0") >= 53,
                      "every graticule line must have a degree label");
  if (spec.kind == projection_kind::star_x)
    generation::require(
      generated.find("id=\"antarctic-cap-boundaries\"")
            != std::string::npos
        && generated.find("id=\"antarctic-unified-cap-boundary\"")
             != std::string::npos,
      "Star-X graticules are missing their Stage 7 Antarctic cap guides");
  generation::verify_configured_label_font(generated, "graticule SVG");
  generation::require(generated.find(" nan") == std::string::npos
                      && generated.find(" -nan") == std::string::npos
                      && generated.find(" inf") == std::string::npos
                      && generated.find(" -inf") == std::string::npos,
                      "generated SVG contains a non-finite coordinate");
}

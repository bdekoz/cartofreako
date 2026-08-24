// Projection-aware rendering for non-sparse NOAA CPC temperature fields.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_ANTHROPOCENE_TEMPERATURE_GENERATION_H
#define CART0FREAK0_ANTHROPOCENE_TEMPERATURE_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <limits>
#include <numbers>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <izzi-svg.h>
#include <h3/h3api.h>

#include "anthropocene-temperature-data.h"
#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"

namespace cart0freak0::anthropocene_temperature_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

inline std::string
temperature_xml_escape(std::string value)
{
  constexpr std::array replacements {
    std::pair {std::string_view {"&"}, std::string_view {"&amp;"}},
    std::pair {std::string_view {"\""}, std::string_view {"&quot;"}},
    std::pair {std::string_view {"<"}, std::string_view {"&lt;"}},
    std::pair {std::string_view {">"}, std::string_view {"&gt;"}},
  };
  for (const auto& [source, replacement] : replacements)
    {
      std::size_t position = 0;
      while ((position = value.find(source, position)) != std::string::npos)
        {
          value.replace(position, source.size(), replacement);
          position += replacement.size();
        }
    }
  return value;
}

inline std::string
temperature_format(const double value, const int precision = 6)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  return output.str();
}

inline svg::typography
temperature_typography(const double size = 0.11,
                       const svg::color_qi color = {58, 56, 51})
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 0.96, {249, 247, 240}, 0.88, 0.006};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline bool
temperature_same_point(const generation::geographic_point left,
                       const generation::geographic_point right)
{
  return left.latitude == right.latitude
    && left.longitude == right.longitude;
}

inline void
temperature_append_unique(
  std::vector<generation::geographic_point>& points,
  const generation::geographic_point point)
{
  if (points.empty() || !temperature_same_point(points.back(), point))
    points.push_back(point);
}

inline std::vector<generation::geographic_point>
temperature_clip_longitude(
  const std::vector<generation::geographic_point>& source,
  const double boundary, const bool keep_greater)
{
  std::vector<generation::geographic_point> result;
  if (source.empty())
    return result;
  const auto inside = [&](const generation::geographic_point point) {
    return keep_greater ? point.longitude >= boundary
                        : point.longitude <= boundary;
  };
  generation::geographic_point left = source.back();
  bool left_inside = inside(left);
  for (const generation::geographic_point right : source)
    {
      const bool right_inside = inside(right);
      if (left_inside != right_inside)
        {
          const double fraction = (boundary - left.longitude)
            / (right.longitude - left.longitude);
          temperature_append_unique(result, {
            left.latitude + fraction * (right.latitude - left.latitude),
            boundary,
          });
        }
      if (right_inside)
        temperature_append_unique(result, right);
      left = right;
      left_inside = right_inside;
    }
  if (result.size() > 1
      && temperature_same_point(result.front(), result.back()))
    result.pop_back();
  return result;
}

inline std::vector<std::vector<generation::geographic_point>>
temperature_h3_polygons(const H3Index cell)
{
  CellBoundary boundary {};
  temperature_require(cellToBoundary(cell, &boundary) == E_SUCCESS,
                      "failed to calculate temperature H3 boundary");
  std::vector<generation::geographic_point> unwrapped;
  unwrapped.reserve(static_cast<std::size_t>(boundary.numVerts));
  for (int index = 0; index < boundary.numVerts; ++index)
    {
      generation::geographic_point point {
        boundary.verts[index].lat * 180.0 / std::numbers::pi,
        boundary.verts[index].lng * 180.0 / std::numbers::pi,
      };
      if (!unwrapped.empty())
        {
          while (point.longitude - unwrapped.back().longitude > 180)
            point.longitude -= 360;
          while (point.longitude - unwrapped.back().longitude < -180)
            point.longitude += 360;
        }
      unwrapped.push_back(point);
    }

  const auto [minimum, maximum] = std::ranges::minmax_element(
    unwrapped, {}, &generation::geographic_point::longitude);
  const int first_band = static_cast<int>(
    std::floor((minimum->longitude + 180) / 360));
  const int last_band = static_cast<int>(
    std::floor((std::nextafter(maximum->longitude,
                               -std::numeric_limits<double>::infinity())
                + 180) / 360));
  std::vector<std::vector<generation::geographic_point>> result;
  for (int band = first_band; band <= last_band; ++band)
    {
      const double shift = 360.0 * band;
      std::vector<generation::geographic_point> clipped
        = temperature_clip_longitude(unwrapped, -180 + shift, true);
      clipped = temperature_clip_longitude(clipped, 180 + shift, false);
      if (clipped.size() < 3)
        continue;
      for (generation::geographic_point& point : clipped)
        point.longitude = std::clamp(point.longitude - shift, -180.0, 180.0);
      result.push_back(std::move(clipped));
    }
  temperature_require(!result.empty(),
                      "failed to split temperature H3 boundary");
  return result;
}

inline bool
temperature_local_segment(const svg::vrange& points,
                          const generation::projection_context& context)
{
  double minimum_x = std::numeric_limits<double>::infinity();
  double maximum_x = -std::numeric_limits<double>::infinity();
  double minimum_y = std::numeric_limits<double>::infinity();
  double maximum_y = -std::numeric_limits<double>::infinity();
  for (const svg::point_2t point : points)
    {
      const auto [x, y] = point;
      minimum_x = std::min(minimum_x, x);
      maximum_x = std::max(maximum_x, x);
      minimum_y = std::min(minimum_y, y);
      maximum_y = std::max(maximum_y, y);
    }
  const double maximum_span = std::max(
    context.map_frame.width(), context.map_frame.height()) / 16;
  return maximum_x - minimum_x <= maximum_span
    && maximum_y - minimum_y <= maximum_span;
}

inline void
append_temperature_fallback_hexagon(
  std::string& path_data, const generation::projection_context& context,
  const H3Index cell)
{
  LatLng center {};
  temperature_require(cellToLatLng(cell, &center) == E_SUCCESS,
                      "failed to calculate temperature H3 center");
  const auto [x, y] = generation::project_point(context, {
    radsToDegs(center.lat), radsToDegs(center.lng),
  });
  const double radius = std::max(
    context.map_frame.width(), context.map_frame.height()) / 750;
  svg::vrange points;
  points.reserve(6);
  for (int index = 0; index < 6; ++index)
    {
      const double angle = std::numbers::pi / 6
        + index * std::numbers::pi / 3;
      points.push_back({
        std::clamp(x + radius * std::cos(angle),
                   0.0, context.map_frame.width()),
        std::clamp(y + radius * std::sin(angle),
                   0.0, context.map_frame.height()),
      });
    }
  path_data += svg::make_path_data_from_points(points);
  path_data += "Z ";
}

inline bool
append_temperature_polygon(
  std::string& path_data, const generation::projection_context& context,
  const H3Index cell)
{
  try
    {
      std::string projected;
      bool nonlocal = false;
      bool appended = false;
      for (std::vector<generation::geographic_point>& polygon
           : temperature_h3_polygons(cell))
        for (const svg::vrange& segment : generation::project_path(
               context, std::move(polygon), true))
          if (segment.size() >= 3)
            {
              if (!temperature_local_segment(segment, context))
                {
                  nonlocal = true;
                  continue;
                }
              projected += svg::make_path_data_from_points(segment);
              projected += "Z ";
              appended = true;
            }
      if (nonlocal || !appended)
        {
          append_temperature_fallback_hexagon(path_data, context, cell);
          return true;
        }
      else
        path_data += projected;
      return false;
    }
  catch (const std::exception& error)
    {
      throw std::runtime_error(
        "temperature H3 " + temperature_h3_string(cell) + ": "
          + error.what());
    }
}

inline void
add_temperature_background(generation::projection_document& document,
                           const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("anthropocene-temperature-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{246, 242, 232}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"anthropocene-temperature-ground\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_temperature_land(generation::projection_document& document,
                     const generation::projection_context& context)
{
  const natural_earth::layer_spec land {
    "terrestrial-land", "Subdued Natural Earth 1:10m land",
    "ne_10m_land.shp", natural_earth::geometry_role::area,
    natural_earth::area_style({220, 216, 207}), 0.04, 0.74,
  };
  svg::group_element layer;
  layer.start_element(std::string(land.id));
  layer.add_title(std::string(land.title));
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::antarctic_cap cap
        = natural_earth::make_antarctic_cap(context);
      static_cast<void>(natural_earth::render_star_x_source(
        layer, land, context, cap));
    }
  else
    static_cast<void>(natural_earth::render_source(layer, land, context));
  layer.finish_element();
  document.add_element(layer);
}

inline unsigned
temperature_bin(const std::uint64_t count, const std::uint64_t scale)
{
  constexpr unsigned bin_count = 6;
  temperature_require(count > 0 && scale > 1,
                      "temperature count must be positive and scale must exceed one");
  const double fraction = std::min(
    1.0, std::log(static_cast<double>(count))
      / std::log(static_cast<double>(scale)));
  return std::min(bin_count - 1,
                  static_cast<unsigned>(fraction * (bin_count - 1)));
}

inline std::size_t
add_temperature_coverage(generation::projection_document& document,
                         const generation::projection_context& context,
                         const temperature_dataset& dataset)
{
  svg::group_element layer;
  layer.start_element("cpc-temperature-coverage");
  layer.add_title("NOAA CPC analyzed land cells, including zero record days");
  std::string paths;
  std::size_t count = 0;
  std::size_t fallback_count = 0;
  for (const temperature_cell& cell : dataset.cells)
    if (cell.tmax_valid_days != 0 || cell.tmin_valid_days != 0)
      {
        fallback_count += append_temperature_polygon(
          paths, context, cell.h3);
        ++count;
      }
  if (!paths.empty())
    layer.add_element(svg::make_path(
      paths, {{205, 199, 184}, 0.24, {191, 184, 169}, 0.22, 0.0015},
      "cpc-covered-cells", true,
      "data-evidence-class=\"analysis-field\" data-zero-semantics=\"analyzed-zero\""
      " data-cell-count=\"" + std::to_string(count)
        + "\" data-projection-fallback-cell-count=\""
        + std::to_string(fallback_count) + "\""));
  layer.finish_element();
  document.add_element(layer);
  return count;
}

inline std::size_t
add_temperature_records(generation::projection_document& document,
                        const generation::projection_context& context,
                        const temperature_profile& profile,
                        const temperature_dataset& dataset,
                        const bool maximum)
{
  constexpr std::size_t bin_count = 6;
  const std::string layer_id = maximum
    ? "cpc-temperature-record-high-days"
    : "cpc-temperature-record-low-days";
  svg::group_element layer;
  layer.start_element(layer_id);
  layer.add_title(maximum
    ? "Strict CPC daily maximum-temperature record days"
    : "Strict CPC daily minimum-temperature record days");
  std::array<std::string, bin_count> paths;
  std::array<std::size_t, bin_count> counts {};
  std::array<std::size_t, bin_count> fallback_counts {};
  for (const temperature_cell& cell : dataset.cells)
    {
      const std::uint64_t value = maximum
        ? cell.record_high_days : cell.record_low_days;
      if (value == 0)
        continue;
      const unsigned bin = temperature_bin(
        value, maximum ? profile.high_scale_days : profile.low_scale_days);
      fallback_counts[bin] += append_temperature_polygon(
        paths[bin], context, cell.h3);
      ++counts[bin];
    }

  std::size_t rendered = 0;
  const svg::color_qi color = maximum
    ? svg::color_qi {215, 62, 48} : svg::color_qi {48, 105, 190};
  for (std::size_t bin = 0; bin < bin_count; ++bin)
    if (!paths[bin].empty())
      {
        const double fraction = (bin + 1.0) / bin_count;
        const double opacity = profile.minimum_nonzero_opacity
          + (1 - profile.minimum_nonzero_opacity) * fraction;
        const double field_opacity = profile.data_graphic_opacity;
        const svg::style style = maximum
          ? svg::style {color, field_opacity * (0.24 + 0.62 * opacity),
                        color,
                        field_opacity * std::min(1.0, opacity + 0.08),
                        0.002}
          : svg::style {svg::color::none, 0, color,
                        field_opacity * (0.42 + 0.58 * opacity),
                        0.006 + 0.012 * fraction};
        layer.add_element(svg::make_path(
          paths[bin], style, layer_id + "-bin-" + std::to_string(bin + 1),
          true,
          "data-anthropocene-temperature-field=\"true\""
          " data-evidence-class=\"analysis-field\" data-bin=\""
            + std::to_string(bin + 1) + "\" data-cell-count=\""
            + std::to_string(counts[bin])
            + "\" data-projection-fallback-cell-count=\""
            + std::to_string(fallback_counts[bin]) + "\""));
        rendered += counts[bin];
      }
  layer.finish_element();
  document.add_element(layer);
  return rendered;
}

inline void
add_temperature_legend(generation::projection_document& document,
                       const generation::projection_context& context,
                       const temperature_profile& profile,
                       const temperature_dataset& dataset)
{
  static_cast<void>(context);
  if (!profile.show_legend)
    return;
  constexpr double panel_width = 15.0;
  constexpr double panel_height = 1.05;
  svg::group_element layer;
  layer.start_element("legend-and-provenance",
    generation::bottom_right_legend_transform(
      context, panel_width, panel_height));
  svg::rect_element panel;
  panel.start_element();
  panel.add_data({0, 0, panel_width, panel_height});
  panel.add_style({{250, 249, 244}, 0.93, {62, 61, 57}, 0.62, 0.015});
  panel.add_raw("id=\"temperature-legend-panel\"");
  panel.finish_element();
  layer.add_element(panel);
  svg::typography title = temperature_typography(0.34, {44, 42, 38});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer,
    "ANTHROPOCENE TEMPERATURE / " + std::to_string(profile.calendar_year)
      + (profile.partial_year ? " PARTIAL YEAR" : " COMPLETE YEAR"),
    {0.30, 0.21}, title);
  svg::styled_text(layer,
    temperature_xml_escape(
      "NOAA CPC 0.5 degree analysis through " + profile.data_through
        + "  |  H3 r" + std::to_string(profile.h3_resolution)
        + "  |  strict records vs " + std::to_string(profile.baseline_start)
        + "-" + std::to_string(profile.baseline_end)),
    {0.30, 0.45}, temperature_typography(0.105, {83, 79, 72}));

  svg::rect_element high;
  high.start_element();
  high.add_data({0.34, 0.61, 0.08, 0.08});
  high.add_style({{215, 62, 48}, 0.82, {215, 62, 48}, 1, 0.004});
  high.finish_element();
  layer.add_element(high);
  svg::styled_text(layer, "record-high days (filled; log-scaled)",
                   {0.47, 0.65}, temperature_typography(0.101));

  svg::rect_element low;
  low.start_element();
  low.add_data({3.37, 0.61, 0.08, 0.08});
  low.add_style({svg::color::none, 0, {48, 105, 190}, 1, 0.014});
  low.finish_element();
  layer.add_element(low);
  svg::styled_text(layer, "record-low days (outline; log-scaled)",
                   {3.50, 0.65}, temperature_typography(0.101));

  svg::rect_element zero;
  zero.start_element();
  zero.add_data({6.53, 0.61, 0.08, 0.08});
  zero.add_style({{205, 199, 184}, 0.34, {191, 184, 169}, 0.32, 0.004});
  zero.finish_element();
  layer.add_element(zero);
  svg::styled_text(layer, "covered zero / field domain",
                   {6.66, 0.65}, temperature_typography(0.101));

  svg::styled_text(layer,
    std::to_string(dataset.covered_cell_count) + " covered of "
      + std::to_string(dataset.cells.size())
      + " global H3 cells; valid-day denominators are embedded",
    {9.20, 0.65}, temperature_typography(0.101, {83, 79, 72}));
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_temperature_note(generation::projection_document& document,
                     const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("coverage-note");
  svg::typography text = temperature_typography(0.092, {72, 68, 62});
  text._M_anchor = svg::typography::anchor::middle;
  text._M_align = svg::typography::align::center;
  svg::styled_text(layer,
    "Analysis field, not station observations or attribution. Neutral means analyzed with zero strict records; blank means missing or outside the CPC land domain.",
    {context.map_frame.width() / 2, context.map_frame.height() - 0.18}, text);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
temperature_metadata(const generation::projection_spec& spec,
                     const temperature_profile& profile,
                     const temperature_dataset& dataset)
{
  return "<metadata id=\"anthropocene-temperature-metadata\""
    " data-workflow=\"Anthropocene NOAA CPC non-sparse temperature field\""
    " data-title-scale=\"2\""
    " data-profile=\"" + temperature_xml_escape(
      profile.path.filename().string()) + "\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-calendar-year=\"" + std::to_string(profile.calendar_year) + "\""
    " data-partial-year=\"" + (profile.partial_year ? "true" : "false") + "\""
    " data-data-through=\"" + profile.data_through + "\""
    " data-h3-resolution=\"" + std::to_string(profile.h3_resolution) + "\""
    " data-graphic-opacity=\""
      + temperature_format(profile.data_graphic_opacity, 2) + "\""
    " data-feature-count=\"" + std::to_string(dataset.cells.size()) + "\""
    " data-covered-cell-count=\"" + std::to_string(
      dataset.covered_cell_count) + "\""
    " data-evidence-class=\"analysis-field\""
    " data-source=\"NOAA CPC Global Unified Temperature\""
    " data-source-manifest-sha256=\"" + profile.source_manifest_sha256 + "\""
    " data-geojson-sha256=\"" + profile.geojson_sha256 + "\""
    " data-zero-semantics=\"valid-days-positive-is-analyzed-zero\""
    " data-missing-semantics=\"valid-days-zero-is-missing\""
    " data-record-high-total=\"" + std::to_string(
      dataset.totals.record_high_days) + "\""
    " data-record-low-total=\"" + std::to_string(
      dataset.totals.record_low_days) + "\"></metadata>\n";
}

inline std::string
temperature_output_basename(const generation::projection_spec& spec,
                            const temperature_profile& profile)
{
  return generation::output_basename(
    "anthropocene-temperature-" + std::to_string(profile.calendar_year), spec);
}

inline void
generate_temperature(const generation::projection_spec& spec,
                     const temperature_profile& profile,
                     const temperature_dataset& dataset)
{
  const std::string basename = temperature_output_basename(spec, profile);
  const generation::projection_context context(spec, basename);
  generation::projection_document document(
    basename, std::string(spec.title) + " Anthropocene non-sparse temperature "
      + std::to_string(profile.calendar_year), context.map_frame.frame_area);
  document.add_raw(temperature_metadata(spec, profile, dataset));
  add_temperature_background(document, context);
  natural_earth::initialize_gdal();
  add_temperature_land(document, context);
  static_cast<void>(add_temperature_coverage(document, context, dataset));
  static_cast<void>(add_temperature_records(
    document, context, profile, dataset, true));
  static_cast<void>(add_temperature_records(
    document, context, profile, dataset, false));
  add_temperature_legend(document, context, profile, dataset);
  add_temperature_note(document, context);
}

inline std::string
read_temperature_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  temperature_require(input.good(), "failed to open generated "
                                      + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline void
verify_temperature(const std::string& generated,
                   const generation::projection_context& context,
                   const temperature_profile& profile,
                   const temperature_dataset& dataset)
{
  temperature_require(generated.find(generation::view_box_fragment(context))
                        != std::string::npos,
                      "temperature SVG has the wrong viewBox");
  constexpr std::array layers {
    std::string_view {"anthropocene-temperature-background"},
    std::string_view {"terrestrial-land"},
    std::string_view {"cpc-temperature-coverage"},
    std::string_view {"cpc-temperature-record-high-days"},
    std::string_view {"cpc-temperature-record-low-days"},
    std::string_view {"legend-and-provenance"},
    std::string_view {"coverage-note"},
  };
  for (const std::string_view layer : layers)
    temperature_require(generated.find("<g id=\"" + std::string(layer)
                                         + "\"") != std::string::npos,
                        "temperature SVG is missing layer "
                          + std::string(layer));
  temperature_require(generated.find(
                        "id=\"anthropocene-temperature-metadata\"")
                         != std::string::npos
                        && generated.find("data-geojson-sha256=\""
                          + profile.geojson_sha256 + "\"")
                             != std::string::npos
                        && generated.find("data-feature-count=\""
                          + std::to_string(dataset.cells.size()) + "\"")
                             != std::string::npos
                        && generated.find(
                          "data-zero-semantics=\"valid-days-positive-is-analyzed-zero\"")
                             != std::string::npos,
                      "temperature SVG lacks field provenance");
  temperature_require(generated.find("data-title-scale=\"2\"")
                         != std::string::npos,
                      "temperature SVG lacks title-scale metadata");
  temperature_require(generated.find(
                        "data-graphic-opacity=\""
                          + temperature_format(
                              profile.data_graphic_opacity, 2) + "\"")
                         != std::string::npos,
                      "temperature SVG lacks data-graphic opacity metadata");
  temperature_require(generated.find(" nan") == std::string::npos
                        && generated.find(" -nan") == std::string::npos
                        && generated.find(" inf") == std::string::npos
                        && generated.find(" -inf") == std::string::npos,
                      "temperature SVG has non-finite data");
  generation::verify_configured_label_font(generated,
                                           "Anthropocene temperature SVG");
}

inline int
run_temperature(const int argc, char** argv)
{
  if (argc != 4)
    throw std::invalid_argument(
      "usage: generate-anthropocene-temperature PROJECTION PROFILE.json INPUT.geojson");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const temperature_profile profile = load_temperature_profile(
    std::filesystem::absolute(argv[2]));
  const temperature_dataset dataset = load_temperature_dataset(
    std::filesystem::absolute(argv[3]), profile);
  const std::string basename = temperature_output_basename(spec, profile);
  const generation::projection_context context(spec, basename);
  generate_temperature(spec, profile, dataset);
  verify_temperature(
    read_temperature_generated(basename), context, profile, dataset);
  return 0;
}

} // namespace cart0freak0::anthropocene_temperature_generation

#endif // CART0FREAK0_ANTHROPOCENE_TEMPERATURE_GENERATION_H

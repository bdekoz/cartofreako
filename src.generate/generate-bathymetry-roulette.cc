// Generate monochrome roulette-patterned Natural Earth bathymetry.
// -*- mode: C++ -*-

#include <array>
#include <cstddef>
#include <exception>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include <a60-svg.h>

#include "bathymetry-roulette-style.h"
#include "natural-earth-generation.h"

namespace cart0freak0::bathymetry_roulette_generation {

namespace catalogue = cart0freak0::bathymetry_roulette_style;
namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

using catalogue::curve_paint;
using catalogue::depth_style;

void
roulette_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
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
replace_all(std::string& text, const std::string_view source,
            const std::string_view replacement)
{
  std::size_t position = 0;
  while ((position = text.find(source, position)) != std::string::npos)
    {
      text.replace(position, source.size(), replacement);
      position += replacement.size();
    }
}

std::string
format_number(const double value, const int precision = 6)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  std::string result = output.str();
  while (result.size() > 1 && result.back() == '0')
    result.pop_back();
  if (!result.empty() && result.back() == '.')
    result.pop_back();
  return result;
}

std::string
color_text(const svg::color_qi color)
{ return svg::color_qi::to_string(color); }

std::string
pattern_markup(const depth_style& style)
{
  const std::string path = catalogue::make_pattern_curve_path(style);
  const bool filled = style.paint == curve_paint::filled;
  std::ostringstream output;
  output << "<pattern id=\"" << catalogue::pattern_id(style)
         << "\" patternUnits=\"userSpaceOnUse\" x=\"0\" y=\"0\""
         << " width=\"" << format_number(catalogue::pattern_tile_size)
         << "\" height=\"" << format_number(catalogue::pattern_tile_size)
         << "\" data-depth-metres=\"" << style.depth_metres
         << "\" data-roulette-kind=\"" << catalogue::kind_name(style.kind)
         << "\" data-fixed-radius=\"" << style.fixed_radius
         << "\" data-rolling-radius=\"" << style.rolling_radius
         << "\" data-point-distance-ratio=\""
         << catalogue::ratio_text(style.point_distance_ratio)
         << "\" data-paint=\""
         << (filled ? "fill" : "outline") << "\">\n"
         << "<title>" << catalogue::curve_title(style) << "</title>\n"
         << "<rect x=\"0\" y=\"0\" width=\""
         << format_number(catalogue::pattern_tile_size)
         << "\" height=\"" << format_number(catalogue::pattern_tile_size)
         << "\" fill=\"" << color_text(catalogue::ground_color)
         << "\"/>\n"
         << "<path d=\"" << path << "\" fill=\""
         << (filled ? color_text(catalogue::ink_color) : "none")
         << "\" fill-opacity=\"" << (filled ? "0.52" : "0")
         << "\" fill-rule=\"evenodd\" stroke=\""
         << color_text(catalogue::ink_color)
         << "\" stroke-opacity=\"0.96\" stroke-width=\""
         << format_number(catalogue::pattern_stroke_width)
         << "\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n"
         << "</pattern>\n";
  return output.str();
}

std::string
clip_path_markup(const depth_style& style, std::string geometry)
{
  replace_all(geometry, R"(fill-rule="evenodd")",
              R"(fill-rule="evenodd" clip-rule="evenodd")");
  std::ostringstream output;
  output << "<clipPath id=\"" << catalogue::clip_id(style)
         << "\" clipPathUnits=\"userSpaceOnUse\""
         << " clip-rule=\"evenodd\">\n"
         << geometry
         << "</clipPath>\n";
  return output.str();
}

std::string
metadata_markup(const generation::projection_spec& spec)
{
  std::ostringstream output;
  output << "<metadata id=\"bathymetry-roulette-metadata\""
         << " data-source=\"Natural Earth 5.1.1 1:10m physical vectors\""
         << " data-projection=\"" << spec.argument << "\""
         << " data-depth-count=\"" << catalogue::depth_styles.size() << "\""
         << " data-pattern-units=\"userSpaceOnUse\""
         << " data-curve-space=\"projected-page\""
         << " data-ground=\"" << color_text(catalogue::ground_color) << "\""
         << " data-ink=\"" << color_text(catalogue::ink_color) << "\""
         << ">Monochrome depth thresholds use progressively more variable "
            "and complex Izzi roulette curves.</metadata>\n";
  return output.str();
}

svg::style
curve_style(const depth_style& style, const double stroke_width)
{
  const bool filled = style.paint == curve_paint::filled;
  return {
    filled ? catalogue::ink_color : svg::color::none,
    filled ? 0.52 : 0,
    catalogue::ink_color, 0.96, stroke_width,
  };
}

std::string
key_text_markup(const double x, const double y, const std::string& text)
{
  std::ostringstream output;
  output << "<text x=\"" << format_number(x)
         << "\" y=\"" << format_number(y)
         << "\" font-family=\"monospace\" font-size=\"0.17\""
         << " fill=\"" << color_text(catalogue::ink_color)
         << "\">" << text << "</text>\n";
  return output.str();
}

void
add_key(generation::projection_document& document,
        const generation::projection_context& context)
{
  constexpr std::size_t columns = 4;
  constexpr double panel_width = 13.6;
  constexpr double panel_height = 3.65;
  constexpr double cell_width = 3.28;
  constexpr double cell_height = 1.02;
  constexpr double margin = 0.24;
  constexpr double motif_diameter = 0.64;
  const double left = (context.map_frame.width() - panel_width) / 2;
  const double top = context.map_frame.height() - panel_height - 0.28;

  svg::group_element key;
  key.start_element("bathymetry-roulette-key");
  key.add_title("Bathymetry depth to roulette key");

  svg::rect_element background;
  background.start_element();
  background.add_data({left, top, panel_width, panel_height});
  background.add_style(
    {catalogue::ground_color, 0.94, catalogue::ink_color, 0.72, 0.012});
  background.add_raw("id=\"bathymetry-roulette-key-background\" rx=\"0.12\"");
  background.finish_element();
  key.add_element(background);
  key.add_raw(key_text_markup(
    left + margin, top + 0.28, "DEPTH / ROULETTE (monochrome)"));

  for (std::size_t index = 0; index != catalogue::depth_styles.size(); ++index)
    {
      const depth_style& style = catalogue::depth_styles[index];
      const std::size_t row = index / columns;
      const std::size_t column = index % columns;
      const double cell_left = left + margin + column * cell_width;
      const double cell_top = top + 0.40 + row * cell_height;
      const svg::point_2t origin {
        cell_left + motif_diameter / 2,
        cell_top + motif_diameter / 2,
      };
      const std::string path
        = catalogue::make_curve_path(style, origin, motif_diameter);
      key.add_element(svg::make_path(
        path, curve_style(style, 0.014),
        "bathymetry-roulette-key-motif-" + std::to_string(index + 1),
        true, R"(fill-rule="evenodd" stroke-linecap="round" stroke-linejoin="round")"));
      const std::string label = catalogue::depth_text(style.depth_metres)
        + "  " + std::string(catalogue::kind_abbreviation(style.kind))
        + " " + std::to_string(style.fixed_radius) + ":"
        + std::to_string(style.rolling_radius) + "  d/r="
        + catalogue::ratio_text(style.point_distance_ratio);
      key.add_raw(key_text_markup(
        cell_left + motif_diameter + 0.10, cell_top + 0.39, label));
    }

  key.finish_element();
  document.add_element(key);
}

std::string
output_basename(const generation::projection_spec& spec)
{ return generation::output_basename("bathymetry-roulette", spec); }

void
generate(const generation::projection_spec& spec)
{
  catalogue::validate_catalogue();
  natural_earth::initialize_gdal();
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generation::projection_document document(
    basename, "Natural Earth 1:10m bathymetry rendered with progressively "
              "complex monochrome roulette curves in the "
              + std::string(spec.title) + " projection",
    context.map_frame.frame_area);
  document.add_raw(metadata_markup(spec));

  svg::defs_element definitions;
  definitions.start_element();
  std::vector<natural_earth::render_stats> layer_stats;
  layer_stats.reserve(catalogue::depth_styles.size());
  for (std::size_t index = 0; index != catalogue::depth_styles.size(); ++index)
    {
      const depth_style& style = catalogue::depth_styles[index];
      const natural_earth::layer_spec& source
        = natural_earth::bathymetry_specs[index];
      roulette_require(style.layer_id == source.id,
                       "roulette catalogue and Natural Earth depths differ");
      natural_earth::layer_spec clipping_source = source;
      clipping_source.style = natural_earth::area_style(svg::color::black);
      svg::group_element geometry;
      const natural_earth::render_stats stats = natural_earth::render_source(
        geometry, clipping_source, context);
      roulette_require(!geometry.empty(),
                       "bathymetry clip geometry is empty");
      definitions.add_raw(clip_path_markup(style, geometry.str()));
      definitions.add_raw(pattern_markup(style));
      layer_stats.push_back(stats);
      std::cout << source.id << ": " << stats.source_features
                << " features, " << stats.paths << " clip paths, "
                << stats.points << " points, "
                << catalogue::curve_title(style) << '\n';
    }
  definitions.finish_element();
  document.add_element(definitions);

  svg::group_element bathymetry;
  bathymetry.start_element("bathymetry-roulette");
  bathymetry.add_title(
    "Twelve nested Natural Earth depth thresholds with roulette patterns");
  for (const depth_style& style : catalogue::depth_styles)
    {
      svg::group_element layer;
      layer.start_element(std::string(style.layer_id));
      layer.add_title(catalogue::curve_title(style));
      svg::rect_element field;
      field.start_element();
      field.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
      field.add_fill(catalogue::pattern_id(style));
      field.add_raw(
        "id=\"" + std::string(style.layer_id)
          + "-roulette-field\" clip-path=\"url(#"
          + catalogue::clip_id(style) + ")\"");
      field.finish_element();
      layer.add_element(field);
      layer.finish_element();
      bathymetry.add_element(layer);
    }
  bathymetry.finish_element();
  document.add_element(bathymetry);
  add_key(document, context);

  natural_earth::render_stats total;
  for (const natural_earth::render_stats stats : layer_stats)
    total += stats;
  natural_earth::print_total(total);
}

std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  roulette_require(input.good(),
                   "failed to open generated " + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

void
verify(const std::string& generated,
       const generation::projection_context& context)
{
  roulette_require(generated.find(generation::view_box_fragment(context))
                     != std::string::npos,
                   "generated bathymetry roulette SVG has the wrong viewBox");
  roulette_require(generated.find("id=\"bathymetry-roulette-metadata\"")
                     != std::string::npos
                     && generated.find("data-curve-space=\"projected-page\"")
                          != std::string::npos,
                   "generated bathymetry roulette SVG lacks metadata");
  roulette_require(generated.find("<g id=\"bathymetry-roulette\">")
                     != std::string::npos
                     && generated.find("<g id=\"bathymetry-roulette-key\">")
                          != std::string::npos,
                   "generated bathymetry roulette SVG lacks semantic groups");
  roulette_require(
    token_count(generated, "<pattern id=\"bathymetry-roulette-pattern-")
      == catalogue::depth_styles.size()
      && token_count(generated,
                     "<clipPath id=\"bathymetry-roulette-clip-")
           == catalogue::depth_styles.size()
      && token_count(generated, "patternUnits=\"userSpaceOnUse\"")
           == catalogue::depth_styles.size(),
    "generated bathymetry roulette SVG has incomplete definitions");

  std::size_t previous_position = 0;
  for (const depth_style& style : catalogue::depth_styles)
    {
      const std::string group = "<g id=\"" + std::string(style.layer_id)
                                + "\">";
      const std::size_t position = generated.find(group);
      roulette_require(position != std::string::npos
                         && position >= previous_position,
                       "bathymetry roulette depth groups are missing or "
                       "out of paint order");
      previous_position = position;
      roulette_require(
        generated.find("fill=\"url(#" + catalogue::pattern_id(style) + ")\"")
          != std::string::npos
          && generated.find("clip-path=\"url(#" + catalogue::clip_id(style)
                            + ")\"") != std::string::npos,
        "bathymetry roulette depth does not reference its pattern and clip");
    }

  roulette_require(token_count(generated, "clip-rule=\"evenodd\"") > 100,
                   "bathymetry roulette clips do not preserve polygon holes");
  roulette_require(token_count(generated, "<path id=\"bathymetry-") > 100,
                   "bathymetry roulette SVG contains too few source paths");
  roulette_require(generated.find(" nan") == std::string::npos
                     && generated.find(" -nan") == std::string::npos
                     && generated.find(" inf") == std::string::npos
                     && generated.find(" -inf") == std::string::npos,
                   "generated bathymetry roulette SVG has non-finite data");

  for (const natural_earth::layer_spec& source
       : natural_earth::bathymetry_specs)
    roulette_require(
      generated.find(color_text(source.style._M_fill_color))
        == std::string::npos,
      "generated bathymetry roulette SVG contains the ordinary depth palette");
}

int
run(const int argc, char** argv)
{
  const generation::projection_spec& spec
    = generation::projection_from_arguments(argc, argv);
  const std::string basename = output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate(spec);
  verify(read_generated(basename), context);
  return 0;
}

} // namespace cart0freak0::bathymetry_roulette_generation

int
main(const int argc, char** argv)
{
  try
    {
      return cart0freak0::bathymetry_roulette_generation::run(argc, argv);
    }
  catch (const std::exception& error)
    {
      std::cerr << "generate-bathymetry-roulette: " << error.what() << '\n';
      return 1;
    }
}

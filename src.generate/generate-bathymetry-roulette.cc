// Generate blue-ramp roulette-field Natural Earth bathymetry.
// -*- mode: C++ -*-

#include <array>
#include <cmath>
#include <cstddef>
#include <exception>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

#include <izzi-svg.h>

#include "bathymetry-roulette-style.h"
#include "generation-typography.h"
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

struct field_grid
{
  int first_row;
  int last_row;
  int first_column;
  int last_column;

  std::size_t
  cell_count() const
  {
    return static_cast<std::size_t>(last_row - first_row + 1)
      * static_cast<std::size_t>(last_column - first_column + 1);
  }
};

field_grid
make_field_grid(const generation::projection_context& context)
{
  const int margin_cells = static_cast<int>(std::ceil(
    catalogue::field_margin / catalogue::field_cell_size)) + 1;
  return {
    -margin_cells,
    static_cast<int>(std::ceil(
      context.map_frame.height() / catalogue::field_cell_size))
      + margin_cells,
    -margin_cells,
    static_cast<int>(std::ceil(
      context.map_frame.width() / catalogue::field_cell_size))
      + margin_cells,
  };
}

double
field_voronoi_jitter(const std::size_t site_index, const std::size_t salt)
{
  const std::size_t mixed
    = site_index * (37 + salt * 18) + 11 + salt * 29;
  return (static_cast<double>(mixed % 101) / 100 - 0.5) * 0.46;
}

svg::point_2t
field_voronoi_site(const std::size_t site_index,
                   const generation::projection_context& context)
{
  roulette_require(site_index < catalogue::field_voronoi_site_count,
                   "roulette Voronoi site index is out of range");
  const std::size_t row = site_index / catalogue::field_voronoi_columns;
  const std::size_t column = site_index % catalogue::field_voronoi_columns;
  return {
    (static_cast<double>(column) + 0.5
       + field_voronoi_jitter(site_index, 0))
      * context.map_frame.width() / catalogue::field_voronoi_columns,
    (static_cast<double>(row) + 0.5
       + field_voronoi_jitter(site_index, 1))
      * context.map_frame.height() / catalogue::field_voronoi_rows,
  };
}

std::size_t
nearest_field_voronoi_site(const svg::point_2t point,
                           const generation::projection_context& context)
{
  std::size_t nearest = 0;
  double nearest_distance = std::numeric_limits<double>::infinity();
  for (std::size_t site_index = 0;
       site_index != catalogue::field_voronoi_site_count; ++site_index)
    {
      const svg::point_2t site = field_voronoi_site(site_index, context);
      const double delta_x = std::get<0>(point) - std::get<0>(site);
      const double delta_y = std::get<1>(point) - std::get<1>(site);
      const double distance = delta_x * delta_x + delta_y * delta_y;
      if (distance < nearest_distance)
        {
          nearest = site_index;
          nearest_distance = distance;
        }
    }
  return nearest;
}

struct roulette_field
{
  std::array<std::string, catalogue::field_variations.size()> paths;
  std::array<std::size_t, catalogue::field_variations.size()> counts {};
  std::size_t total = 0;
};

roulette_field
make_roulette_field(const depth_style& style,
                    const std::size_t depth_index,
                    const generation::projection_context& context)
{
  const field_grid grid = make_field_grid(context);
  roulette_field result;
  for (int row = grid.first_row; row <= grid.last_row; ++row)
    for (int column = grid.first_column;
         column <= grid.last_column; ++column)
      {
        const std::size_t row_index
          = static_cast<std::size_t>(row - grid.first_row);
        const double stagger
          = row_index % 2 == 0 ? 0 : catalogue::field_cell_size / 2;
        const svg::point_2t unshifted_origin {
          column * catalogue::field_cell_size + stagger,
          row * catalogue::field_cell_size,
        };
        const std::size_t column_count = static_cast<std::size_t>(
          grid.last_column - grid.first_column + 1);
        const std::size_t cell_index
          = static_cast<std::size_t>(row - grid.first_row) * column_count
            + static_cast<std::size_t>(column - grid.first_column);
        const std::size_t variation_index = (cell_index * 5
          + depth_index * 7) % catalogue::field_variations.size();
        const catalogue::field_variation& variation
          = catalogue::field_variations[variation_index];
        const svg::point_2t origin {
          std::get<0>(unshifted_origin)
            + variation.offset_x_cells * catalogue::field_cell_size,
          std::get<1>(unshifted_origin)
            + variation.offset_y_cells * catalogue::field_cell_size,
        };
        result.paths[variation_index]
          += catalogue::make_field_curve_path(style, origin, variation);
        ++result.counts[variation_index];
        ++result.total;
      }
  roulette_require(result.total == grid.cell_count(),
                   "roulette field mosaic has the wrong cell count");
  for (const std::size_t count : result.counts)
    roulette_require(count != 0,
                     "roulette field variation received no mosaic cells");
  return result;
}

std::string
variation_voronoi_sites(const std::size_t depth_index,
                        const std::size_t variation_index)
{
  std::string result;
  for (std::size_t site_index = 0;
       site_index != catalogue::field_voronoi_site_count; ++site_index)
    if (catalogue::field_voronoi_variation_index(depth_index, site_index)
          == variation_index)
      {
        if (!result.empty())
          result += ',';
        result += std::to_string(site_index + 1);
      }
  return result;
}

std::string
metadata_markup(const generation::projection_spec& spec,
                const generation::projection_context& context)
{
  const std::size_t cells = make_field_grid(context).cell_count();
  std::ostringstream output;
  output << "<metadata id=\"bathymetry-roulette-metadata\""
         << " data-source=\"Natural Earth 5.1.1 1:10m physical vectors\""
         << " data-projection=\"" << spec.argument << "\""
         << " data-depth-count=\"" << catalogue::depth_styles.size() << "\""
         << " data-field-mode=\"depth-filled-voronoi-groups\""
         << " data-field-space=\"projected-page\""
         << " data-field-variation-count-per-depth=\""
         << catalogue::field_variations.size() << "\""
         << " data-field-cell-size=\""
         << format_number(catalogue::field_cell_size) << "\""
         << " data-field-base-diameter=\""
         << format_number(catalogue::field_base_diameter) << "\""
         << " data-field-row-stagger-cells=\"0.5\""
         << " data-field-voronoi-assignment=\"nearest-jittered-site\""
         << " data-field-voronoi-site-columns=\""
         << catalogue::field_voronoi_columns << "\""
         << " data-field-voronoi-site-rows=\""
         << catalogue::field_voronoi_rows << "\""
         << " data-field-voronoi-site-count=\""
         << catalogue::field_voronoi_site_count << "\""
         << " data-field-voronoi-curve-clipping=\"none\""
         << " data-field-cell-count-per-depth=\"" << cells << "\""
         << " data-field-curve-instance-count=\""
         << cells * catalogue::depth_styles.size() << "\""
         << " data-minimum-d-r=\"1\""
         << " data-depth-controls-d-r=\"true\""
         << " data-paint=\"even-odd-fill\""
         << " data-graphic-opacity=\""
         << format_number(catalogue::field_graphic_opacity) << "\""
         << " data-moire=\"accepted\""
         << " data-depth-palette=\"Natural Earth bathymetry blue ramp\""
         << " data-ground=\"" << color_text(catalogue::ground_color) << "\""
         << " data-label-ink=\"" << color_text(catalogue::ink_color) << "\""
         << ">Monochrome depth thresholds use explicit overlapping filled "
            "Izzi roulette forms selected in projected-page Voronoi groups; "
            "depth alone increases d/r from the cycloid boundary.</metadata>\n";
  return output.str();
}

svg::style
curve_style(const depth_style& style, const double stroke_width)
{
  const bool filled = style.paint == curve_paint::filled;
  return {
    filled ? style.color : svg::color::none,
    filled ? catalogue::field_graphic_opacity : 0,
    style.color, catalogue::field_graphic_opacity, stroke_width,
  };
}

svg::style
field_curve_style(const depth_style& style, const std::size_t index)
{
  const double stroke_width
    = catalogue::field_stroke_width * (0.88 + 0.06 * (index % 4));
  return {
    style.color, catalogue::field_graphic_opacity,
    style.color, catalogue::field_graphic_opacity, stroke_width,
  };
}

std::string
key_text_markup(const double x, const double y, const std::string& text)
{
  std::ostringstream output;
  output << "<text x=\"" << format_number(x)
         << "\" y=\"" << format_number(y)
         << "\" font-family=\""
         << generation::configured_label_font_family()
         << "\" font-size=\"0.17\""
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
  key.add_title("Representative bathymetry depth to roulette key");

  svg::rect_element background;
  background.start_element();
  background.add_data({left, top, panel_width, panel_height});
  background.add_style(
    {catalogue::ground_color, 0.94, catalogue::ink_color, 0.72, 0.012});
  background.add_raw("id=\"bathymetry-roulette-key-background\" rx=\"0.12\"");
  background.finish_element();
  key.add_element(background);
  key.add_raw(key_text_markup(
    left + margin, top + 0.28, "DEPTH / ROULETTE / ORIGINAL BLUE RAMP"));

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
              "complex blue-hued roulette curves in the "
              + std::string(spec.title) + " projection",
    context.map_frame.frame_area);
  document.add_raw(metadata_markup(spec, context));

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
      roulette_require(color_text(style.color)
                         == color_text(source.style._M_fill_color),
                       "roulette catalogue and Natural Earth blue ramp differ");
      natural_earth::layer_spec clipping_source = source;
      clipping_source.style = natural_earth::area_style(svg::color::black);
      svg::group_element geometry;
      const natural_earth::render_stats stats = natural_earth::render_source(
        geometry, clipping_source, context);
      roulette_require(!geometry.empty(),
                       "bathymetry clip geometry is empty");
      definitions.add_raw(clip_path_markup(style, geometry.str()));
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
    "Twelve nested Natural Earth depth thresholds with filled, "
    "Voronoi-grouped roulette fields");
  for (std::size_t depth_index = 0;
       depth_index != catalogue::depth_styles.size(); ++depth_index)
    {
      const depth_style& style = catalogue::depth_styles[depth_index];
      const roulette_field field = make_roulette_field(
        style, depth_index, context);
      svg::group_element layer;
      layer.start_element(std::string(style.layer_id));
      layer.add_title(catalogue::curve_title(style));

      svg::rect_element ground;
      ground.start_element();
      ground.add_data({0, 0, context.map_frame.width(),
                       context.map_frame.height()});
      ground.add_style({catalogue::ground_color, 1,
                        svg::color::none, 0, 0});
      ground.add_raw(
        "id=\"" + std::string(style.layer_id)
          + "-roulette-ground\" clip-path=\"url(#"
          + catalogue::clip_id(style) + ")\"");
      ground.finish_element();
      layer.add_element(ground);

      for (std::size_t variation_index = 0;
           variation_index != catalogue::field_variations.size();
           ++variation_index)
        {
          const catalogue::field_variation& variation
            = catalogue::field_variations[variation_index];
          const std::string id
            = catalogue::field_variation_id(style, variation_index);
          svg::group_element variation_group;
          variation_group.start_element(id);
          variation_group.add_title(
            catalogue::field_variation_title(style, variation_index));
          const std::string attributes
            = "clip-path=\"url(#" + catalogue::clip_id(style)
              + ")\" fill-rule=\"evenodd\" stroke-linecap=\"round\""
                " stroke-linejoin=\"round\" data-instance-count=\""
              + std::to_string(field.counts[variation_index])
              + "\" data-diameter-factor=\""
              + catalogue::ratio_text(variation.diameter_factor)
              + "\" data-depth-d-r=\""
              + catalogue::ratio_text(style.point_distance_ratio)
              + "\" data-phase-turns=\""
              + catalogue::ratio_text(variation.phase_turns)
              + "\" data-offset-x-cells=\""
              + catalogue::ratio_text(variation.offset_x_cells)
              + "\" data-offset-y-cells=\""
              + catalogue::ratio_text(variation.offset_y_cells)
              + "\" data-voronoi-sites=\""
              + variation_voronoi_sites(depth_index, variation_index)
              + "\" data-voronoi-site-count=\""
              + std::to_string(catalogue::field_voronoi_site_count
                               / catalogue::field_variations.size())
              + "\" data-paint=\"even-odd-fill\""
                " data-graphic-opacity=\""
              + format_number(catalogue::field_graphic_opacity) + "\"";
          variation_group.add_element(svg::make_path(
            field.paths[variation_index],
            field_curve_style(style, variation_index), id + "-forms", true,
            attributes));
          variation_group.finish_element();
          layer.add_element(variation_group);
        }
      layer.finish_element();
      bathymetry.add_element(layer);
      std::cout << style.layer_id << ": " << field.total
                << " explicit filled field curves across "
                << catalogue::field_voronoi_site_count
                << " Voronoi regions and "
                << catalogue::field_variations.size() << " variations\n";
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
                     && generated.find(
                          "data-field-mode=\"depth-filled-voronoi-groups\"")
                          != std::string::npos,
                   "generated bathymetry roulette SVG lacks metadata");
  const std::size_t cells = make_field_grid(context).cell_count();
  roulette_require(
    generated.find("data-field-base-diameter=\""
                   + format_number(catalogue::field_base_diameter) + "\"")
        != std::string::npos
      && generated.find("data-field-row-stagger-cells=\"0.5\"")
           != std::string::npos
      && generated.find("data-field-voronoi-site-count=\""
                        + std::to_string(
                          catalogue::field_voronoi_site_count) + "\"")
           != std::string::npos
      && generated.find("data-minimum-d-r=\"1\"")
           != std::string::npos
      && generated.find("data-graphic-opacity=\""
                        + format_number(catalogue::field_graphic_opacity)
                        + "\"") != std::string::npos
      && generated.find("data-field-cell-count-per-depth=\""
                   + std::to_string(cells) + "\"") != std::string::npos
      && generated.find("data-field-curve-instance-count=\""
                        + std::to_string(
                          cells * catalogue::depth_styles.size()) + "\"")
           != std::string::npos,
    "generated bathymetry roulette SVG has incorrect field counts");
  roulette_require(generated.find("<g id=\"bathymetry-roulette\">")
                     != std::string::npos
                     && generated.find("<g id=\"bathymetry-roulette-key\">")
                          != std::string::npos,
                   "generated bathymetry roulette SVG lacks semantic groups");
  roulette_require(
    token_count(generated,
                "<clipPath id=\"bathymetry-roulette-clip-")
           == catalogue::depth_styles.size()
      && token_count(generated, "-roulette-variation-")
           == 2 * catalogue::depth_styles.size()
                * catalogue::field_variations.size()
      && token_count(generated, "data-instance-count=\"")
           == catalogue::depth_styles.size()
                * catalogue::field_variations.size()
      && token_count(generated, "data-voronoi-sites=\"")
           == catalogue::depth_styles.size()
                * catalogue::field_variations.size()
      && token_count(generated, "data-paint=\"even-odd-fill\"")
           == 1 + catalogue::depth_styles.size()
                    * catalogue::field_variations.size()
      && generated.find("<pattern") == std::string::npos,
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
        generated.find("id=\"" + std::string(style.layer_id)
                       + "-roulette-ground\"") != std::string::npos
          && generated.find("clip-path=\"url(#" + catalogue::clip_id(style)
                            + ")\"") != std::string::npos,
        "bathymetry roulette depth does not contain its ground and clip");
      for (std::size_t variation_index = 0;
           variation_index != catalogue::field_variations.size();
           ++variation_index)
        {
          const std::string id
            = catalogue::field_variation_id(style, variation_index);
          roulette_require(generated.find("<g id=\"" + id + "\">")
                             != std::string::npos
                             && generated.find("id=\"" + id + "-forms\"")
                                  != std::string::npos,
                           "bathymetry roulette field variation is missing");
        }
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
  generation::verify_configured_label_font(
    generated, "Bathymetry Roulette SVG");

  for (const natural_earth::layer_spec& source
       : natural_earth::bathymetry_specs)
    roulette_require(
      generated.find(color_text(source.style._M_fill_color))
        != std::string::npos,
      "generated bathymetry roulette SVG omits a Natural Earth depth blue");
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

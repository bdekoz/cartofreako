// Explore the radius and tracing-point parameter space of roulette curves.
// The filename preserves the requested "routlette" spelling.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <numbers>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

#include <a60-svg-curves-roulette.h>

namespace {

enum class curve_family
{
  trochoid,
  epitrochoid,
  hypotrochoid,
};

struct experiment
{
  curve_family family;
  std::size_t fixed_radius;
  std::size_t rolling_radius;
  std::string_view label;
};

// Columns move the tracing point from the rolling-circle center, through the
// cycloidal value d/r=1, and out into increasingly prolate curves. Rows vary
// the rolling geometry and include the named ratios highlighted by the source.
constexpr std::array point_distance_ratios {
  0.0, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 3.0,
};

constexpr std::array experiments {
  experiment {curve_family::trochoid, 0, 1, "line trochoid"},
  experiment {curve_family::epitrochoid, 1, 1, "epi 1:1 limacon"},
  experiment {curve_family::epitrochoid, 2, 1, "epi 2:1 nephroid"},
  experiment {curve_family::epitrochoid, 3, 1, "epi 3:1"},
  experiment {curve_family::epitrochoid, 5, 2, "epi 5:2"},
  experiment {curve_family::epitrochoid, 11, 7, "epi 11:7"},
  experiment {curve_family::hypotrochoid, 2, 1, "hypo 2:1 Tusi"},
  experiment {curve_family::hypotrochoid, 3, 1, "hypo 3:1 deltoid"},
  experiment {curve_family::hypotrochoid, 4, 1, "hypo 4:1 astroid"},
  experiment {curve_family::hypotrochoid, 5, 2, "hypo 5:2"},
  experiment {curve_family::hypotrochoid, 11, 7, "hypo 11:7"},
};

constexpr double label_width = 238;
constexpr double header_height = 54;
constexpr double cell_width = 205;
constexpr double cell_height = 205;
constexpr double cell_padding = 18;

std::string
number(const double value)
{
  std::ostringstream output;
  output.precision(3);
  output << value;
  return output.str();
}

std::string
clip_path_markup(const std::string& id, const double left, const double top)
{
  std::ostringstream output;
  output << "<clipPath id=\"" << id
         << "\" clipPathUnits=\"userSpaceOnUse\">"
         << "<rect x=\"" << left + 0.5
         << "\" y=\"" << top + 0.5
         << "\" width=\"" << cell_width - 1
         << "\" height=\"" << cell_height - 1
         << "\"/></clipPath>\n";
  return output.str();
}

std::string
cell_markup(const double left, const double top, const bool alternate)
{
  std::ostringstream output;
  output << "<rect x=\"" << left
         << "\" y=\"" << top
         << "\" width=\"" << cell_width
         << "\" height=\"" << cell_height
         << "\" fill=\"" << (alternate ? "#eef4f6" : "#f8fafb")
         << "\" stroke=\"#c8d2d7\" stroke-width=\"0.5\"/>\n";
  return output.str();
}

std::string
text_markup(const double x, const double y, const std::string_view text,
            const std::string_view anchor, const double size)
{
  std::ostringstream output;
  output << "<text x=\"" << x
         << "\" y=\"" << y
         << "\" text-anchor=\"" << anchor
         << "\" font-family=\"monospace\" font-size=\"" << size
         << "\" fill=\"#34434a\">" << text << "</text>\n";
  return output.str();
}

std::string
make_experiment_path(const experiment& value, const double distance_ratio,
                     const double left, const double top)
{
  const double center_x = left + cell_width / 2;
  const double center_y = top + cell_height / 2;
  const double inner_width = cell_width - 2 * cell_padding;
  const double inner_height = cell_height - 2 * cell_padding;

  if (value.family == curve_family::trochoid)
    {
      svg::trochoid_config config;
      config.rolling_radius = static_cast<double>(value.rolling_radius);
      config.point_distance = distance_ratio * config.rolling_radius;
      config.turns = 3;
      config.samples_per_turn = 160;

      const double maximum_t = 2 * std::numbers::pi * config.turns;
      const double x_span = config.rolling_radius * maximum_t
                            + 2 * config.point_distance;
      const double y_span = std::max(2 * config.point_distance, 0.25);
      const double scale = std::min(inner_width / x_span,
                                    inner_height / y_span);
      const svg::point_2t origin {
        left + cell_padding + scale * config.point_distance,
        center_y + scale * config.rolling_radius,
      };
      return svg::make_trochoid_path(origin, scale, config);
    }

  svg::roulette_config config;
  config.fixed_radius = value.fixed_radius;
  config.rolling_radius = value.rolling_radius;
  config.point_distance
    = distance_ratio * static_cast<double>(config.rolling_radius);
  config.samples_per_turn = 180;

  const double fixed = static_cast<double>(config.fixed_radius);
  const double rolling = static_cast<double>(config.rolling_radius);
  const double center_radius = value.family == curve_family::epitrochoid
                                 ? fixed + rolling : fixed - rolling;
  const double extent = center_radius + config.point_distance;
  const double scale = std::min(inner_width, inner_height) / (2 * extent);
  const svg::point_2t origin {center_x, center_y};
  if (value.family == curve_family::epitrochoid)
    return svg::make_epitrochoid_path(origin, scale, config);
  return svg::make_hypotrochoid_path(origin, scale, config);
}

void
validate_convenience_api()
{
  const svg::point_2t origin {0, 0};

  svg::trochoid_config trochoid;
  trochoid.rolling_radius = 2;
  trochoid.point_distance = 2;
  if (svg::make_trochoid_path(origin, 1, trochoid)
      != svg::make_cycloid_path(origin, 1, trochoid))
    throw std::runtime_error("cycloid wrapper changed the canonical curve");

  svg::roulette_config centered;
  centered.fixed_radius = 111;
  centered.rolling_radius = 70;
  centered.point_distance = 70;
  if (svg::roulette_completion_turns(centered) != 70)
    throw std::runtime_error("roulette ratio did not reduce to 111:70");
  if (svg::make_epitrochoid_path(origin, 1, centered)
      != svg::make_epicycloid_path(origin, 1, centered))
    throw std::runtime_error("epicycloid wrapper changed the canonical curve");

  centered.fixed_radius = 4;
  centered.rolling_radius = 1;
  centered.point_distance = 1;
  if (svg::make_hypotrochoid_path(origin, 1, centered)
      != svg::make_hypocycloid_path(origin, 1, centered))
    throw std::runtime_error("hypocycloid wrapper changed the canonical curve");
}

void
render_parameter_grid(const std::string& output_name)
{
  validate_convenience_api();

  const svg::area<> canvas {
    label_width + point_distance_ratios.size() * cell_width,
    header_height + experiments.size() * cell_height,
  };
  svg::svg_element document(
    output_name,
    "Trochoid, epitrochoid, and hypotrochoid parameter explorer",
    canvas);

  svg::defs_element definitions;
  definitions.start_element();
  for (std::size_t row = 0; row != experiments.size(); ++row)
    for (std::size_t column = 0;
         column != point_distance_ratios.size(); ++column)
      {
        const std::string clip_id
          = "clip-roulette-row-" + std::to_string(row)
            + "-column-" + std::to_string(column);
        definitions.add_raw(clip_path_markup(
          clip_id, label_width + column * cell_width,
          header_height + row * cell_height));
      }
  definitions.finish_element();
  document.add_element(definitions);

  const std::array ink_colors {
    svg::color_qi {44, 74, 88},
    svg::color_qi {52, 85, 130},
    svg::color_qi {68, 77, 145},
    svg::color_qi {91, 70, 143},
    svg::color_qi {117, 68, 130},
    svg::color_qi {143, 68, 108},
    svg::color_qi {151, 82, 76},
    svg::color_qi {145, 105, 55},
    svg::color_qi {112, 126, 52},
    svg::color_qi {70, 133, 72},
    svg::color_qi {39, 126, 105},
  };

  svg::group_element grid;
  grid.start_element("roulette-parameter-grid");
  grid.add_raw(text_markup(label_width - 12, header_height - 18,
                           "curve / radius ratio", "end", 12));
  for (std::size_t column = 0;
       column != point_distance_ratios.size(); ++column)
    {
      const double center_x
        = label_width + column * cell_width + cell_width / 2;
      grid.add_raw(text_markup(
        center_x, header_height - 18,
        "d/r = " + number(point_distance_ratios[column]),
        "middle", 12));
    }

  std::set<std::string> identifiers;
  std::size_t curve_count = 0;
  for (std::size_t row = 0; row != experiments.size(); ++row)
    {
      const experiment& value = experiments[row];
      const double top = header_height + row * cell_height;
      grid.add_raw(text_markup(label_width - 12,
                               top + cell_height / 2 + 5,
                               value.label, "end", 13));

      for (std::size_t column = 0;
           column != point_distance_ratios.size(); ++column)
        {
          const double ratio = point_distance_ratios[column];
          const double left = label_width + column * cell_width;
          grid.add_raw(cell_markup(left, top, (row + column) % 2 != 0));

          const std::string id
            = "roulette-row-" + std::to_string(row)
              + "-column-" + std::to_string(column);
          if (!identifiers.insert(id).second)
            throw std::runtime_error("duplicate roulette cell id: " + id);
          const std::string path_data
            = make_experiment_path(value, ratio, left, top);
          if (path_data.empty()
              || path_data.find("nan") != std::string::npos
              || path_data.find("inf") != std::string::npos)
            throw std::runtime_error(
              "invalid roulette path data in " + id);

          const svg::style curve_style {
            svg::color::none, 0, ink_colors[row], 0.92, 1.05,
          };
          const std::string clip_id
            = "clip-roulette-row-" + std::to_string(row)
              + "-column-" + std::to_string(column);
          svg::group_element cell;
          cell.start_element(id);
          cell.add_title(
            std::string(value.label) + ", tracing distance d/r="
            + number(ratio));
          cell.add_element(svg::make_path(
            path_data, curve_style, id + "-path", true,
            "clip-path=\"url(#" + clip_id
              + ")\" stroke-linecap=\"round\" "
                "stroke-linejoin=\"round\""));
          cell.finish_element();
          grid.add_element(cell);
          ++curve_count;
        }
    }

  grid.finish_element();
  document.add_element(grid);

  const std::size_t expected_count
    = experiments.size() * point_distance_ratios.size();
  if (curve_count != expected_count || identifiers.size() != expected_count)
    throw std::runtime_error("roulette parameter grid is incomplete");
}

} // namespace

int
main(const int argc, char** argv)
{
  try
    {
      const std::string output_name
        = argc == 2 ? argv[1] : "curves-routlette";
      render_parameter_grid(output_name);
      std::cout << "generated "
                << experiments.size() * point_distance_ratios.size()
                << " roulette parameter samples in "
                << output_name << ".svg\n";
      return 0;
    }
  catch (const std::exception& error)
    {
      std::cerr << "curves-routlette: " << error.what() << '\n';
      return 1;
    }
}

// Deterministic depth-to-roulette visual catalogue.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_BATHYMETRY_ROULETTE_STYLE_H
#define CART0FREAK0_BATHYMETRY_ROULETTE_STYLE_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

#include <a60-svg-curves-roulette.h>

namespace cart0freak0::bathymetry_roulette_style {

enum class curve_paint
{
  outline,
  filled,
};

struct depth_style
{
  std::string_view layer_id;
  int depth_metres;
  svg::roulette_kind kind;
  std::size_t fixed_radius;
  std::size_t rolling_radius;
  double point_distance_ratio;
  curve_paint paint;
};

// The historical ocean pass did not present one canonical motif on a regular
// symbol grid.  It assigned related motif variations to a projected mosaic.
// Bathymetry Roulette follows that model with deterministic page-space cells:
// every cell varies the base depth curve's diameter, tracing-point distance,
// phase, and origin while preserving its radius family and closure period.
struct field_variation
{
  double diameter_factor;
  double point_distance_factor;
  double phase_turns;
  double offset_x_cells;
  double offset_y_cells;
};

// Point distance grows monotonically with depth. Integer radius ratios keep
// every centered roulette exactly closed; the 5:2 and 11:7 ratios also grow
// the closure period from one orbit to two and then seven.
inline constexpr std::array depth_styles {
  depth_style {
    "bathymetry-0m", 0, svg::roulette_kind::epitrochoid,
    1, 1, 0.25, curve_paint::outline,
  },
  depth_style {
    "bathymetry-200m", -200, svg::roulette_kind::epitrochoid,
    1, 1, 0.35, curve_paint::outline,
  },
  depth_style {
    "bathymetry-1000m", -1000, svg::roulette_kind::epitrochoid,
    1, 1, 0.50, curve_paint::outline,
  },
  depth_style {
    "bathymetry-2000m", -2000, svg::roulette_kind::epitrochoid,
    2, 1, 0.65, curve_paint::outline,
  },
  depth_style {
    "bathymetry-3000m", -3000, svg::roulette_kind::epitrochoid,
    2, 1, 0.75, curve_paint::outline,
  },
  depth_style {
    "bathymetry-4000m", -4000, svg::roulette_kind::epitrochoid,
    3, 1, 0.90, curve_paint::outline,
  },
  depth_style {
    "bathymetry-5000m", -5000, svg::roulette_kind::epitrochoid,
    3, 1, 1.00, curve_paint::outline,
  },
  depth_style {
    "bathymetry-6000m", -6000, svg::roulette_kind::hypotrochoid,
    4, 1, 1.10, curve_paint::outline,
  },
  depth_style {
    "bathymetry-7000m", -7000, svg::roulette_kind::epitrochoid,
    5, 2, 1.25, curve_paint::filled,
  },
  depth_style {
    "bathymetry-8000m", -8000, svg::roulette_kind::hypotrochoid,
    5, 2, 1.50, curve_paint::filled,
  },
  depth_style {
    "bathymetry-9000m", -9000, svg::roulette_kind::hypotrochoid,
    11, 7, 2.00, curve_paint::filled,
  },
  depth_style {
    "bathymetry-10000m", -10000, svg::roulette_kind::epitrochoid,
    11, 7, 3.00, curve_paint::filled,
  },
};

inline constexpr std::array field_variations {
  field_variation {0.74, 0.960, 0.0 / 12, -0.18, -0.11},
  field_variation {0.86, 0.968, 1.0 / 12,  0.09, -0.21},
  field_variation {1.02, 0.976, 2.0 / 12,  0.20,  0.04},
  field_variation {1.18, 0.984, 3.0 / 12, -0.06,  0.19},
  field_variation {1.30, 0.992, 4.0 / 12, -0.22,  0.08},
  field_variation {0.92, 1.000, 5.0 / 12,  0.14,  0.17},
  field_variation {1.24, 1.008, 6.0 / 12,  0.03, -0.16},
  field_variation {0.80, 1.016, 7.0 / 12, -0.12,  0.22},
  field_variation {1.10, 1.024, 8.0 / 12,  0.22, -0.07},
  field_variation {1.36, 1.032, 9.0 / 12, -0.19, -0.20},
  field_variation {0.98, 1.036, 10.0 / 12, 0.08,  0.10},
  field_variation {1.16, 1.040, 11.0 / 12, -0.02, -0.02},
};

inline constexpr std::size_t samples_per_turn = 128;
inline constexpr double field_cell_size = 1.10;
inline constexpr double field_base_diameter = 2.15;
inline constexpr double field_margin = field_base_diameter * 0.75;
inline constexpr double field_stroke_width = 0.014;
inline constexpr double field_stroke_opacity = 0.90;
inline constexpr double field_fill_opacity = 0.060;
inline constexpr double pi = 3.141592653589793238462643383279502884;
inline const svg::color_qi ground_color {239, 245, 243};
inline const svg::color_qi ink_color {23, 63, 72};

inline void
style_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

inline std::string_view
kind_name(const svg::roulette_kind kind)
{
  return kind == svg::roulette_kind::epitrochoid
           ? "epitrochoid" : "hypotrochoid";
}

inline std::string_view
kind_abbreviation(const svg::roulette_kind kind)
{
  return kind == svg::roulette_kind::epitrochoid ? "epi" : "hypo";
}

inline std::string_view
paint_name(const curve_paint paint)
{ return paint == curve_paint::outline ? "outline" : "even-odd fill"; }

inline svg::roulette_config
roulette_config(const depth_style& style,
                const double point_distance_factor = 1,
                const double phase_turns = 0)
{
  svg::roulette_config result;
  result.fixed_radius = style.fixed_radius;
  result.rolling_radius = style.rolling_radius;
  result.point_distance
    = style.point_distance_ratio * point_distance_factor
      * style.rolling_radius;
  result.phase = phase_turns * 2 * pi;
  result.samples_per_turn = samples_per_turn;
  return result;
}

inline std::size_t
completion_turns(const depth_style& style)
{ return svg::roulette_completion_turns(roulette_config(style)); }

inline double
unscaled_extent(const depth_style& style,
                const double point_distance_factor = 1)
{
  const double fixed = static_cast<double>(style.fixed_radius);
  const double rolling = static_cast<double>(style.rolling_radius);
  const double center_radius
    = style.kind == svg::roulette_kind::epitrochoid
        ? fixed + rolling : fixed - rolling;
  return center_radius
    + style.point_distance_ratio * point_distance_factor * rolling;
}

inline std::string
make_curve_path(const depth_style& style, const svg::point_2t origin,
                const double diameter,
                const double point_distance_factor = 1,
                const double phase_turns = 0)
{
  style_require(std::isfinite(diameter) && diameter > 0,
                "roulette display diameter must be finite and positive");
  style_require(std::isfinite(point_distance_factor)
                  && point_distance_factor > 0,
                "roulette point-distance factor must be finite and positive");
  style_require(std::isfinite(phase_turns),
                "roulette phase must be finite");
  const double extent = unscaled_extent(style, point_distance_factor);
  style_require(std::isfinite(extent) && extent > 0,
                "roulette catalogue produced an invalid extent");
  return svg::make_roulette_path(
    origin, diameter / (2 * extent), style.kind,
    roulette_config(style, point_distance_factor, phase_turns));
}

inline std::string
make_field_curve_path(const depth_style& style,
                      const svg::point_2t origin,
                      const field_variation& variation)
{
  return make_curve_path(
    style, origin, field_base_diameter * variation.diameter_factor,
    variation.point_distance_factor, variation.phase_turns);
}

inline std::string
field_variation_id(const depth_style& style, const std::size_t index)
{
  style_require(index < field_variations.size(),
                "roulette field variation index is out of range");
  std::string number = std::to_string(index + 1);
  if (number.size() < 2)
    number.insert(number.begin(), 2 - number.size(), '0');
  return std::string(style.layer_id) + "-roulette-variation-" + number;
}

inline std::string
clip_id(const depth_style& style)
{ return "bathymetry-roulette-clip-" + std::string(style.layer_id); }

inline std::string
ratio_text(const double ratio)
{
  std::ostringstream output;
  output.precision(3);
  output << ratio;
  return output.str();
}

inline std::string
depth_text(const int depth_metres)
{
  if (depth_metres == 0)
    return "0 m";
  return std::to_string(depth_metres) + " m";
}

inline std::string
curve_title(const depth_style& style)
{
  return depth_text(style.depth_metres) + ": "
    + std::string(kind_abbreviation(style.kind)) + " "
    + std::to_string(style.fixed_radius) + ":"
    + std::to_string(style.rolling_radius) + ", d/r="
    + ratio_text(style.point_distance_ratio) + ", "
    + std::string(paint_name(style.paint)) + ", closure turns="
    + std::to_string(completion_turns(style));
}

inline std::string
field_variation_title(const depth_style& style, const std::size_t index)
{
  style_require(index < field_variations.size(),
                "roulette field variation index is out of range");
  const field_variation& variation = field_variations[index];
  return curve_title(style) + "; field variation "
    + std::to_string(index + 1) + "/"
    + std::to_string(field_variations.size()) + ", diameter factor="
    + ratio_text(variation.diameter_factor) + ", point-distance factor="
    + ratio_text(variation.point_distance_factor) + ", phase="
    + ratio_text(variation.phase_turns) + " turn";
}

inline void
validate_catalogue()
{
  style_require(depth_styles.size() == 12,
                "bathymetry roulette catalogue must contain twelve depths");
  bool filled_seen = false;
  std::size_t previous_turns = 0;
  for (std::size_t index = 0; index != depth_styles.size(); ++index)
    {
      const depth_style& style = depth_styles[index];
      style_require(!style.layer_id.empty(),
                    "bathymetry roulette layer id must not be empty");
      style_require(style.fixed_radius != 0 && style.rolling_radius != 0,
                    "bathymetry roulette radii must be positive");
      style_require(std::isfinite(style.point_distance_ratio)
                      && style.point_distance_ratio >= 0,
                    "bathymetry roulette d/r must be finite and nonnegative");
      if (style.kind == svg::roulette_kind::hypotrochoid)
        style_require(style.fixed_radius > style.rolling_radius,
                      "hypotrochoid fixed radius must exceed rolling radius");
      if (index != 0)
        {
          const depth_style& previous = depth_styles[index - 1];
          style_require(style.depth_metres < previous.depth_metres,
                        "bathymetry depths must run shallow to deep");
          style_require(style.point_distance_ratio
                          > previous.point_distance_ratio,
                        "bathymetry roulette d/r must increase with depth");
        }
      for (std::size_t prior = 0; prior != index; ++prior)
        style_require(style.layer_id != depth_styles[prior].layer_id,
                      "bathymetry roulette layer ids must be unique");

      if (style.paint == curve_paint::filled)
        filled_seen = true;
      else
        style_require(!filled_seen,
                      "outline roulette cannot follow a filled depth");

      const std::size_t turns = completion_turns(style);
      style_require(turns >= previous_turns,
                    "roulette closure period must not decrease with depth");
      previous_turns = turns;

      const std::string path = make_curve_path(style, {0, 0}, 1);
      style_require(!path.empty() && path.find("nan") == std::string::npos
                      && path.find("inf") == std::string::npos
                      && path.find('Z') != std::string::npos,
                    "bathymetry roulette catalogue produced an invalid path");
    }

  style_require(field_variations.size() == 12,
                "bathymetry roulette field must have twelve variations");
  double smallest_diameter_factor
    = field_variations.front().diameter_factor;
  for (std::size_t index = 0; index != field_variations.size(); ++index)
    {
      const field_variation& variation = field_variations[index];
      style_require(std::isfinite(variation.diameter_factor)
                      && variation.diameter_factor > 0,
                    "roulette field diameter factor must be positive");
      smallest_diameter_factor = std::min(
        smallest_diameter_factor, variation.diameter_factor);
      style_require(std::isfinite(variation.point_distance_factor)
                      && variation.point_distance_factor > 0,
                    "roulette field point-distance factor must be positive");
      if (index != 0)
        style_require(
          variation.point_distance_factor
            > field_variations[index - 1].point_distance_factor,
          "roulette field point-distance factors must increase");
      style_require(std::isfinite(variation.phase_turns)
                      && variation.phase_turns >= 0
                      && variation.phase_turns < 1,
                    "roulette field phase must be within one turn");
      style_require(std::isfinite(variation.offset_x_cells)
                      && std::abs(variation.offset_x_cells) < 0.5
                      && std::isfinite(variation.offset_y_cells)
                      && std::abs(variation.offset_y_cells) < 0.5,
                    "roulette field origin offset must stay within a cell");
      for (std::size_t prior = 0; prior != index; ++prior)
        style_require(
          make_field_curve_path(depth_styles[5], {0, 0}, variation)
            != make_field_curve_path(
              depth_styles[5], {0, 0}, field_variations[prior]),
          "roulette field variations must produce distinct curves");
    }
  style_require(field_base_diameter * smallest_diameter_factor
                  > field_cell_size,
                "roulette field curves must overlap adjacent cells");

  for (std::size_t index = 1; index != depth_styles.size(); ++index)
    style_require(
      depth_styles[index - 1].point_distance_ratio
          * field_variations.back().point_distance_factor
        < depth_styles[index].point_distance_ratio
            * field_variations.front().point_distance_factor,
      "roulette field variation families must remain ordered by depth");
}

} // namespace cart0freak0::bathymetry_roulette_style

#endif

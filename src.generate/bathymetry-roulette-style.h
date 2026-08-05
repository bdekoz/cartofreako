// Deterministic depth-to-roulette visual catalogue.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_BATHYMETRY_ROULETTE_STYLE_H
#define CART0FREAK0_BATHYMETRY_ROULETTE_STYLE_H 1

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

inline constexpr std::size_t samples_per_turn = 128;
inline constexpr double pattern_tile_size = 1.20;
inline constexpr double pattern_padding = 0.12;
inline constexpr double pattern_stroke_width = 0.018;
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
roulette_config(const depth_style& style)
{
  svg::roulette_config result;
  result.fixed_radius = style.fixed_radius;
  result.rolling_radius = style.rolling_radius;
  result.point_distance
    = style.point_distance_ratio * style.rolling_radius;
  result.samples_per_turn = samples_per_turn;
  return result;
}

inline std::size_t
completion_turns(const depth_style& style)
{ return svg::roulette_completion_turns(roulette_config(style)); }

inline double
unscaled_extent(const depth_style& style)
{
  const double fixed = static_cast<double>(style.fixed_radius);
  const double rolling = static_cast<double>(style.rolling_radius);
  const double center_radius
    = style.kind == svg::roulette_kind::epitrochoid
        ? fixed + rolling : fixed - rolling;
  return center_radius + style.point_distance_ratio * rolling;
}

inline std::string
make_curve_path(const depth_style& style, const svg::point_2t origin,
                const double diameter)
{
  style_require(std::isfinite(diameter) && diameter > 0,
                "roulette display diameter must be finite and positive");
  const double extent = unscaled_extent(style);
  style_require(std::isfinite(extent) && extent > 0,
                "roulette catalogue produced an invalid extent");
  return svg::make_roulette_path(
    origin, diameter / (2 * extent), style.kind, roulette_config(style));
}

inline std::string
make_pattern_curve_path(const depth_style& style)
{
  const svg::point_2t origin {
    pattern_tile_size / 2, pattern_tile_size / 2,
  };
  return make_curve_path(
    style, origin, pattern_tile_size - 2 * pattern_padding);
}

inline std::string
pattern_id(const depth_style& style)
{ return "bathymetry-roulette-pattern-" + std::string(style.layer_id); }

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

      const std::string path = make_pattern_curve_path(style);
      style_require(!path.empty() && path.find("nan") == std::string::npos
                      && path.find("inf") == std::string::npos
                      && path.find('Z') != std::string::npos,
                    "bathymetry roulette catalogue produced an invalid path");
    }
}

} // namespace cart0freak0::bathymetry_roulette_style

#endif

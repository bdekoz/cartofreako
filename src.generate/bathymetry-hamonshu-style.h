// Deterministic depth-to-Hamonshu visual catalogue.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_BATHYMETRY_HAMONSHU_STYLE_H
#define CART0FREAK0_BATHYMETRY_HAMONSHU_STYLE_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

#include <izzi-svg-curves-hamonshu.h>

namespace cart0freak0::bathymetry_hamonshu_style {

namespace hamonshu = svg::hamonshu;

struct depth_style
{
  std::string_view layer_id;
  int depth_metres;
  double density;
  double curvature;
  svg::color_qi color;
};

struct field_variation
{
  hamonshu::curated_motif_selection motif;
  double box_factor;
  double phase_turns;
  double rotation_turns;
  double offset_x_cells;
  double offset_y_cells;
  bool reflected;
};

// Depth controls form through two Hamonshu-native parameters. Both increase
// strictly from the 0 m threshold to the deepest Natural Earth polygon.
inline const std::array depth_styles {
  depth_style {"bathymetry-0m", 0, 0.55, 0.30, {159, 170, 195}},
  depth_style {"bathymetry-200m", -200, 0.65, 0.42, {140, 150, 185}},
  depth_style {"bathymetry-1000m", -1000, 0.75, 0.56, {116, 135, 184}},
  depth_style {"bathymetry-2000m", -2000, 0.88, 0.72, {100, 120, 175}},
  depth_style {"bathymetry-3000m", -3000, 1.02, 0.90, {84, 104, 169}},
  depth_style {"bathymetry-4000m", -4000, 1.18, 1.10, {70, 90, 160}},
  depth_style {"bathymetry-5000m", -5000, 1.35, 1.35, {57, 76, 152}},
  depth_style {"bathymetry-6000m", -6000, 1.55, 1.62, {40, 55, 136}},
  depth_style {"bathymetry-7000m", -7000, 1.78, 1.95, {34, 48, 124}},
  depth_style {"bathymetry-8000m", -8000, 2.05, 2.30, {28, 40, 110}},
  depth_style {"bathymetry-9000m", -9000, 2.35, 2.75, {22, 32, 96}},
  depth_style {"bathymetry-10000m", -10000, 2.70, 3.25, {16, 25, 82}},
};

// Twelve source-indexed wave studies form the spatial vocabulary. The
// decorative page-51 endpaper in Izzi's thirteen-entry explorer is omitted;
// every retained entry describes water, current, crest, ripple, or spray.
inline constexpr std::array field_variations {
  field_variation {{1, 1, 1}, 0.74, 0.0 / 12, -2.0 / 48,
                   -0.18, -0.11, false},
  field_variation {{2, 2, 1}, 0.86, 1.0 / 12, -1.0 / 48,
                    0.09, -0.21, true},
  field_variation {{3, 3, 1}, 1.02, 2.0 / 12, 0.0,
                    0.20, 0.04, false},
  field_variation {{3, 3, 2}, 1.18, 3.0 / 12, 1.0 / 48,
                   -0.06, 0.19, true},
  field_variation {{6, 6, 2}, 1.30, 4.0 / 12, 2.0 / 48,
                   -0.22, 0.08, false},
  field_variation {{9, 9, 1}, 0.92, 5.0 / 12, -2.0 / 48,
                    0.14, 0.17, true},
  field_variation {{17, 17, 3}, 1.24, 6.0 / 12, -1.0 / 48,
                    0.03, -0.16, false},
  field_variation {{20, 20, 4}, 0.80, 7.0 / 12, 0.0,
                   -0.12, 0.22, true},
  field_variation {{23, 23, 2}, 1.10, 8.0 / 12, 1.0 / 48,
                    0.22, -0.07, false},
  field_variation {{39, 39, 2}, 1.36, 9.0 / 12, 2.0 / 48,
                   -0.19, -0.20, true},
  field_variation {{40, 40, 1}, 0.98, 10.0 / 12, -2.0 / 48,
                    0.08, 0.10, false},
  field_variation {{46, 47, 2}, 1.16, 11.0 / 12, -1.0 / 48,
                   -0.02, -0.02, true},
};

inline constexpr double pi = 3.141592653589793238462643383279502884;
inline constexpr double field_cell_size = 1.10;
inline constexpr double field_base_diameter = 0.5375;
inline constexpr double field_margin = field_base_diameter * 0.75;
inline constexpr double field_stroke_width = 0.014;
inline constexpr double field_graphic_opacity = 0.30;
inline constexpr std::size_t field_voronoi_columns = 6;
inline constexpr std::size_t field_voronoi_rows = 4;
inline constexpr std::size_t field_voronoi_site_count
  = field_voronoi_columns * field_voronoi_rows;
inline constexpr std::size_t samples_per_curve = 24;
inline const svg::color_qi ground_color {239, 245, 243};
inline const svg::color_qi ink_color {23, 63, 72};

inline void
style_require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

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
  return depth_metres == 0 ? "0 m" : std::to_string(depth_metres) + " m";
}

inline const hamonshu::pattern_spec&
pattern(const field_variation& variation)
{ return hamonshu::curated_pattern(variation.motif); }

inline hamonshu::motif_config
motif_config(const depth_style& depth, const field_variation& variation)
{
  hamonshu::motif_config config;
  config.density = depth.density;
  config.curvature = depth.curvature;
  config.phase = variation.phase_turns * 2 * pi;
  config.rotation = variation.rotation_turns * 2 * pi;
  config.reflected = variation.reflected;
  config.samples_per_curve = samples_per_curve;
  return config;
}

inline std::string
make_field_motif_path(const depth_style& depth, const svg::point_2t origin,
                      const field_variation& variation,
                      const double diameter_factor = 1)
{
  style_require(std::isfinite(diameter_factor) && diameter_factor > 0,
                "Hamonshu display diameter factor must be positive");
  const auto [x, y] = origin;
  const double diameter
    = field_base_diameter * variation.box_factor * diameter_factor;
  const hamonshu::pattern_box box {
    x - diameter / 2, y - diameter / 2,
    x + diameter / 2, y + diameter / 2,
  };
  return hamonshu::make_motif_path(
    pattern(variation), box, motif_config(depth, variation));
}

inline constexpr std::size_t
field_voronoi_variation_index(const std::size_t depth_index,
                              const std::size_t site_index)
{
  return (site_index * 5 + depth_index * 7) % field_variations.size();
}

inline std::string
field_variation_id(const depth_style& depth, const std::size_t index)
{
  style_require(index < field_variations.size(),
                "Hamonshu field variation index is out of range");
  std::string number = std::to_string(index + 1);
  if (number.size() < 2)
    number.insert(number.begin(), 2 - number.size(), '0');
  return std::string(depth.layer_id) + "-hamonshu-variation-" + number;
}

inline std::string
clip_id(const depth_style& depth)
{ return "bathymetry-hamonshu-clip-" + std::string(depth.layer_id); }

inline std::string
depth_title(const depth_style& depth)
{
  return depth_text(depth.depth_metres) + ": Hamonshu density="
    + ratio_text(depth.density) + ", curvature="
    + ratio_text(depth.curvature) + ", opacity="
    + ratio_text(field_graphic_opacity);
}

inline std::string
field_variation_title(const depth_style& depth, const std::size_t index)
{
  style_require(index < field_variations.size(),
                "Hamonshu field variation index is out of range");
  const field_variation& variation = field_variations[index];
  return depth_title(depth) + "; " + hamonshu::pattern_title(pattern(variation))
    + "; box factor=" + ratio_text(variation.box_factor)
    + "; phase=" + ratio_text(variation.phase_turns) + " turn"
    + "; rotation=" + ratio_text(variation.rotation_turns) + " turn"
    + "; reflected=" + (variation.reflected ? "true" : "false");
}

inline void
validate_catalogue()
{
  style_require(depth_styles.size() == 12,
                "bathymetry Hamonshu catalogue must contain twelve depths");
  for (std::size_t index = 0; index != depth_styles.size(); ++index)
    {
      const depth_style& depth = depth_styles[index];
      style_require(!depth.layer_id.empty(),
                    "bathymetry Hamonshu layer id must not be empty");
      style_require(std::isfinite(depth.density)
                      && depth.density >= 0.25 && depth.density <= 4,
                    "bathymetry Hamonshu density is outside the Izzi API");
      style_require(std::isfinite(depth.curvature)
                      && depth.curvature >= 0.20 && depth.curvature <= 4,
                    "bathymetry Hamonshu curvature is outside the Izzi API");
      if (index != 0)
        {
          const depth_style& previous = depth_styles[index - 1];
          style_require(depth.depth_metres < previous.depth_metres,
                        "bathymetry Hamonshu depths must run shallow to deep");
          style_require(depth.density > previous.density,
                        "Hamonshu density must increase with depth");
          style_require(depth.curvature > previous.curvature,
                        "Hamonshu curvature must increase with depth");
        }
    }

  style_require(field_variations.size() == 12,
                "bathymetry Hamonshu field must have twelve variations");
  double smallest_box_factor = field_variations.front().box_factor;
  for (std::size_t index = 0; index != field_variations.size(); ++index)
    {
      const field_variation& variation = field_variations[index];
      hamonshu::validate_pattern_spec(pattern(variation));
      style_require(std::isfinite(variation.box_factor)
                      && variation.box_factor > 0,
                    "Hamonshu box factor must be positive");
      smallest_box_factor = std::min(
        smallest_box_factor, variation.box_factor);
      style_require(std::isfinite(variation.phase_turns)
                      && variation.phase_turns >= 0
                      && variation.phase_turns < 1,
                    "Hamonshu phase must stay within one turn");
      style_require(std::isfinite(variation.rotation_turns)
                      && std::abs(variation.rotation_turns) < 0.25,
                    "Hamonshu rotation must stay below one quarter turn");
      style_require(std::isfinite(variation.offset_x_cells)
                      && std::abs(variation.offset_x_cells) < 0.5
                      && std::isfinite(variation.offset_y_cells)
                      && std::abs(variation.offset_y_cells) < 0.5,
                    "Hamonshu origin offset must stay within a cell");
      for (std::size_t prior = 0; prior != index; ++prior)
        style_require(hamonshu::pattern_id(pattern(variation))
                        != hamonshu::pattern_id(pattern(field_variations[prior])),
                      "Hamonshu field motifs must be source-unique");
      const std::string path = make_field_motif_path(
        depth_styles[5], {0, 0}, variation);
      style_require(!path.empty() && path.find("nan") == std::string::npos
                      && path.find("inf") == std::string::npos,
                    "bathymetry Hamonshu catalogue produced invalid path data");
    }
  style_require(field_base_diameter * smallest_box_factor > 0,
                "Hamonshu field boxes must have a positive diameter");

  style_require(field_voronoi_site_count % field_variations.size() == 0,
                "Hamonshu Voronoi sites must distribute variations evenly");
  for (std::size_t depth_index = 0;
       depth_index != depth_styles.size(); ++depth_index)
    {
      std::array<std::size_t, field_variations.size()> counts {};
      for (std::size_t site_index = 0;
           site_index != field_voronoi_site_count; ++site_index)
        ++counts[field_voronoi_variation_index(depth_index, site_index)];
      for (const std::size_t count : counts)
        style_require(count == field_voronoi_site_count
                                 / field_variations.size(),
                      "Hamonshu Voronoi sites must cover every variation "
                      "equally at each depth");
    }
}

} // namespace cart0freak0::bathymetry_hamonshu_style

#endif

#include <algorithm>
#include <cassert>
#include <set>
#include <string>

#include "bathymetry-roulette-style.h"

namespace catalogue = cart0freak0::bathymetry_roulette_style;

int
main()
{
  catalogue::validate_catalogue();
  assert(catalogue::depth_styles.size() == 12);
  assert(catalogue::field_variations.size() == 12);
  assert(catalogue::depth_styles.front().depth_metres == 0);
  assert(catalogue::depth_styles.back().depth_metres == -10000);
  const auto smallest = std::min_element(
    catalogue::field_variations.begin(), catalogue::field_variations.end(),
    [](const auto& left, const auto& right) {
      return left.diameter_factor < right.diameter_factor;
    });
  assert(smallest != catalogue::field_variations.end());
  assert(catalogue::field_base_diameter * smallest->diameter_factor
         > catalogue::field_cell_size);

  std::set<std::string> paths;
  std::set<std::string> field_ids;
  std::set<std::string> clip_ids;
  std::size_t filled = 0;
  for (const catalogue::depth_style& style : catalogue::depth_styles)
    {
      const std::string path = catalogue::make_curve_path(
        style, {0, 0}, catalogue::field_base_diameter);
      assert(std::count(path.begin(), path.end(), 'L')
             == static_cast<std::ptrdiff_t>(
               catalogue::completion_turns(style)
               * catalogue::samples_per_turn));
      assert(paths.insert(path).second);
      assert(clip_ids.insert(catalogue::clip_id(style)).second);
      assert(catalogue::curve_title(style).find("d/r=")
             != std::string::npos);

      std::set<std::string> variation_paths;
      for (std::size_t index = 0;
           index != catalogue::field_variations.size(); ++index)
        {
          const std::string variation_path
            = catalogue::make_field_curve_path(
              style, {0, 0}, catalogue::field_variations[index]);
          assert(std::count(variation_path.begin(), variation_path.end(), 'L')
                 == static_cast<std::ptrdiff_t>(
                   catalogue::completion_turns(style)
                   * catalogue::samples_per_turn));
          assert(variation_paths.insert(variation_path).second);
          assert(field_ids.insert(
            catalogue::field_variation_id(style, index)).second);
          assert(catalogue::field_variation_title(style, index).find(
                   "field variation") != std::string::npos);
        }
      if (style.paint == catalogue::curve_paint::filled)
        ++filled;
    }

  assert(field_ids.size()
         == catalogue::depth_styles.size()
              * catalogue::field_variations.size());

  for (std::size_t index = 1;
       index != catalogue::depth_styles.size(); ++index)
    assert(catalogue::depth_styles[index - 1].point_distance_ratio
             * catalogue::field_variations.back().point_distance_factor
           < catalogue::depth_styles[index].point_distance_ratio
               * catalogue::field_variations.front().point_distance_factor);

  assert(filled == 4);
  assert(catalogue::completion_turns(catalogue::depth_styles[7]) == 1);
  assert(catalogue::completion_turns(catalogue::depth_styles[8]) == 2);
  assert(catalogue::completion_turns(catalogue::depth_styles[10]) == 7);
}

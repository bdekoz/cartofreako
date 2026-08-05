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
  assert(catalogue::depth_styles.front().depth_metres == 0);
  assert(catalogue::depth_styles.back().depth_metres == -10000);

  std::set<std::string> paths;
  std::set<std::string> pattern_ids;
  std::set<std::string> clip_ids;
  std::size_t filled = 0;
  for (const catalogue::depth_style& style : catalogue::depth_styles)
    {
      const std::string path = catalogue::make_pattern_curve_path(style);
      assert(std::count(path.begin(), path.end(), 'L')
             == static_cast<std::ptrdiff_t>(
               catalogue::completion_turns(style)
               * catalogue::samples_per_turn));
      assert(paths.insert(path).second);
      assert(pattern_ids.insert(catalogue::pattern_id(style)).second);
      assert(clip_ids.insert(catalogue::clip_id(style)).second);
      assert(catalogue::curve_title(style).find("d/r=")
             != std::string::npos);
      if (style.paint == catalogue::curve_paint::filled)
        ++filled;
    }

  assert(filled == 4);
  assert(catalogue::completion_turns(catalogue::depth_styles[7]) == 1);
  assert(catalogue::completion_turns(catalogue::depth_styles[8]) == 2);
  assert(catalogue::completion_turns(catalogue::depth_styles[10]) == 7);
}

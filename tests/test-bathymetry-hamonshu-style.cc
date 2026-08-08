#include <array>
#include <cassert>
#include <set>
#include <string>

#include "bathymetry-hamonshu-style.h"

namespace catalogue = cart0freak0::bathymetry_hamonshu_style;
namespace hamonshu = svg::hamonshu;

int
main()
{
  catalogue::validate_catalogue();
  assert(catalogue::depth_styles.size() == 12);
  assert(catalogue::field_variations.size() == 12);
  assert(catalogue::field_voronoi_site_count == 24);
  assert(catalogue::field_graphic_opacity == 0.30);
  assert(catalogue::depth_styles.front().depth_metres == 0);
  assert(catalogue::depth_styles.back().depth_metres == -10000);

  std::set<std::string> source_ids;
  std::set<std::string> paths;
  std::set<std::string> field_ids;
  std::set<std::string> depth_colors;
  for (const auto& depth : catalogue::depth_styles)
    assert(depth_colors.insert(svg::color_qi::to_string(depth.color)).second);
  assert(depth_colors.size() == catalogue::depth_styles.size());
  for (std::size_t index = 0;
       index != catalogue::field_variations.size(); ++index)
    {
      const auto& variation = catalogue::field_variations[index];
      const auto& pattern = catalogue::pattern(variation);
      assert(source_ids.insert(hamonshu::pattern_id(pattern)).second);
      const std::string path = catalogue::make_field_motif_path(
        catalogue::depth_styles[index], {0, 0}, variation);
      assert(!path.empty());
      assert(paths.insert(path).second);
      assert(catalogue::field_variation_title(
               catalogue::depth_styles[index], index).find("Hamonshu")
             != std::string::npos);
      for (const auto& depth : catalogue::depth_styles)
        assert(field_ids.insert(
          catalogue::field_variation_id(depth, index)).second);
    }
  assert(source_ids.size() == 12);
  assert(field_ids.size() == 144);

  for (std::size_t depth_index = 0;
       depth_index != catalogue::depth_styles.size(); ++depth_index)
    {
      std::array<std::size_t, catalogue::field_variations.size()> counts {};
      for (std::size_t site_index = 0;
           site_index != catalogue::field_voronoi_site_count; ++site_index)
        ++counts[catalogue::field_voronoi_variation_index(
          depth_index, site_index)];
      for (const std::size_t count : counts)
        assert(count == 2);
      if (depth_index != 0)
        {
          assert(catalogue::depth_styles[depth_index].density
                 > catalogue::depth_styles[depth_index - 1].density);
          assert(catalogue::depth_styles[depth_index].curvature
                 > catalogue::depth_styles[depth_index - 1].curvature);
        }
    }
}

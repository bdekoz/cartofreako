// Named constellation selection, conservation, and observer filtering.
#include <cassert>
#include <set>

#include "orbiting-generation.h"

namespace orbital = cart0freak0::orbiting_generation;

int main()
{
  const auto config = orbital::load_profile(
    "assets.static/orbital-technosphere/20261109/orbital-technosphere-profile.json");
  assert(config.calculation_time.iso_utc == "2026-11-09T01:12:00Z");
  assert(config.groups.size() == 25);
  assert(!config.display.show_satellite_names);
  const auto catalogs = orbital::load_catalogs(config);
  const auto propagated = orbital::propagate_catalog(catalogs, config);
  assert(catalogs.active_records == 16893);
  assert(propagated.objects.size() > 16000);
  std::set<std::string> input_ids;
  for (const auto& object : catalogs.objects)
    assert(input_ids.insert(object.norad_id).second);

  auto sample = catalogs.objects.front();
  sample.group_ids = {"eutelsat", "oneweb"};
  assert(orbital::display_constellation(sample, config)->id == "oneweb");
  sample.group_ids = {"iridium-next"};
  assert(orbital::display_constellation(sample, config)->id == "iridium");
  sample.group_ids = {"iridium-33-debris"};
  assert(orbital::display_constellation(sample, config) == nullptr);
  sample.group_ids = {"science", "not-a-constellation"};
  assert(orbital::display_constellation(sample, config) == nullptr);

  std::set<std::string> global_ids;
  for (const auto product : {orbital::product_kind::global, orbital::product_kind::observer})
    {
      const auto groups = orbital::group_objects(propagated, config, product);
      std::set<std::string> displayed_ids;
      std::set<std::string> named;
      for (const auto& group : groups)
        {
          if (group.constellation)
            named.insert(group.id);
          for (const auto* object : group.objects)
            {
              assert(displayed_ids.insert(object->source.norad_id).second);
              assert(orbital::visible_in_product(*object, config, product));
              const auto* selected = orbital::display_constellation(object->source, config);
              assert((selected != nullptr) == (group.constellation != nullptr));
              if (selected)
                assert(selected->id == group.id);
            }
        }
      assert(named.size() == 18);
      assert(named.contains("starlink") && named.contains("iridium"));
      assert(displayed_ids.size() == orbital::visible_count(propagated, config, product));
      if (product == orbital::product_kind::global)
        global_ids = displayed_ids;
      else
        for (const auto& id : displayed_ids)
          assert(global_ids.contains(id));
    }
}

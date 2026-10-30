// Distinct named selections from svg::izzi_hue_palette; solid classes, no tint mixing.
#ifndef CARTOFREAKO_RESOURCE_COLORS_H
#define CARTOFREAKO_RESOURCE_COLORS_H
namespace cart0freak0::resources_generation {
inline std::array<svg::color_qi, 5> resource_metric_palette(const std::string& id) {
  if (id == "wind-capacity") return generation_style::palette_wind_capacity;
  if (id == "nuclear-operating-capacity") return generation_style::palette_nuclear_operating_capacity;
  if (id == "petroleum-refinery-throughput") return generation_style::palette_petroleum_refinery_throughput;
  if (id == "food-production-index") return generation_style::palette_food_production_index;
  if (id == "fisheries-production") return generation_style::palette_fisheries_production;
  if (id == "forest-area-percent") return generation_style::palette_forest_area_percent;
  if (id == "rare-earth-mine-production") return generation_style::palette_rare_earth_mine_production;
  if (id == "population-under-30") return generation_style::palette_population_under_30;
  if (id == "population-over-60") return generation_style::palette_population_over_60;
  if (id == "upper-secondary-attainment") return generation_style::palette_upper_secondary_attainment;
  if (id == "bachelors-attainment") return generation_style::palette_bachelors_attainment;
  if (id == "resident-patent-applications-per-million") return generation_style::palette_resident_patent_applications_per_million;
  throw std::runtime_error("no izzi-hue assignment for resource metric: " + id);
}
}
#endif

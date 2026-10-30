// Distinct named selections from svg::izzi_hue_palette; solid classes, no tint mixing.
#ifndef CARTOFREAKO_RESOURCE_COLORS_H
#define CARTOFREAKO_RESOURCE_COLORS_H
namespace cart0freak0::resources_generation {
inline std::array<svg::color_qi, 5> resource_metric_palette(const std::string& id) {
  if (id == "wind-capacity") return {svg::color::lightcyan, svg::color::cyan, svg::color::crayolacerulean, svg::color::shinbashiiro, svg::color::hanada};
  if (id == "nuclear-operating-capacity") return {svg::color::lavender, svg::color::mediumpurple, svg::color::slateblue, svg::color::darkslateblue, svg::color::midnightblue};
  if (id == "petroleum-refinery-throughput") return {svg::color::duboisbrown5, svg::color::duboisbrown4, svg::color::kohakuiro, svg::color::duboisbrown2, svg::color::duboisbrown3};
  if (id == "food-production-index") return {svg::color::pink, svg::color::hotpink, svg::color::deeppink, svg::color::mediumvioletred, svg::color::peony};
  if (id == "fisheries-production") return {svg::color::lightblue, svg::color::skyblue, svg::color::deepskyblue, svg::color::dodgerblue, svg::color::navy};
  if (id == "forest-area-percent") return {svg::color::byakuroku, svg::color::usumoegi, svg::color::moegi, svg::color::midori, svg::color::duboisgreen5};
  if (id == "rare-earth-mine-production") return {svg::color::plum, svg::color::orchid, svg::color::mediumorchid, svg::color::darkviolet, svg::color::purple};
  if (id == "population-under-30") return {svg::color::greenyellow, svg::color::chartreuse, svg::color::hiwamoegi, svg::color::rokusho, svg::color::aotakeiro};
  if (id == "population-over-60") return {svg::color::coral, svg::color::salmon, svg::color::tomato, svg::color::crimson, svg::color::foreigncrimson};
  if (id == "upper-secondary-attainment") return {svg::color::atmosphericp, svg::color::dustyrose, svg::color::usuiro, svg::color::ayameiro, svg::color::murasaki};
  if (id == "bachelors-attainment") return {svg::color::navajowhite, svg::color::kanzoiro, svg::color::akebonoiro, svg::color::sohi, svg::color::benikaba};
  if (id == "resident-patent-applications-per-million") return {svg::color::lightskyblue, svg::color::cornflowerblue, svg::color::royalblue, svg::color::blueprintlight, svg::color::blueprintdark};
  throw std::runtime_error("no izzi-hue assignment for resource metric: " + id);
}
}
#endif

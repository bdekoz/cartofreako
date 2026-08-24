// Projection-aware cleaned-union submarine-fiber SVG generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_FIBER_SYNTHESIZED_GENERATION_H
#define CART0FREAK0_FIBER_SYNTHESIZED_GENERATION_H 1

#include <array>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>

#include "fiber-synthesized-data.h"
#include "network-infrastructure-generation.h"

namespace cart0freak0::fiber_synthesized_generation {

namespace natural_earth = cart0freak0::natural_earth_generation;
namespace infrastructure
  = cart0freak0::network_infrastructure_generation;

inline void
add_fiber_background(generation::projection_document& document,
                     const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("fiber-synthesized-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{242, 244, 243}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"fiber-synthesized-ocean\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
route_attributes(const fiber_route& route)
{
  return "data-fiber-route=\"true\" data-cable-id=\""
    + infrastructure::xml_escape(route.cable_id)
    + "\" data-cable-name=\"" + infrastructure::xml_escape(route.name)
    + "\" data-source-feature-id=\""
    + infrastructure::xml_escape(route.feature_id)
    + "\" data-comparison-id=\""
    + infrastructure::xml_escape(route.comparison_id)
    + "\" data-source-snapshot=\""
    + infrastructure::xml_escape(route.source_snapshot)
    + "\" data-snapshot-membership=\""
    + infrastructure::xml_escape(route.snapshot_membership)
    + "\" data-temporal-class=\""
    + infrastructure::xml_escape(route.temporal_class)
    + "\" data-planned=\"" + (route.planned ? "true" : "false")
    + "\" stroke-linecap=\"round\" stroke-linejoin=\"round\"";
}

inline void
add_fiber_routes(generation::projection_document& document,
                 const generation::projection_context& context,
                 const fiber_dataset& dataset)
{
  svg::group_element layer;
  layer.start_element("network-fiber");
  layer.add_title(
    "Cleaned union: 20260805 default network plus unmatched 2022 context");
  svg::group_element historical;
  historical.start_element("fiber-historical-2022-only");
  svg::group_element shared;
  shared.start_element("fiber-current-shared");
  svg::group_element current_only;
  current_only.start_element("fiber-current-20260805-only");
  svg::group_element planned;
  planned.start_element("fiber-current-planned");
  svg::group_element activated;
  activated.start_element("fiber-planned-to-active");

  for (const fiber_route& route : dataset.routes)
    {
      std::string path_data;
      for (const auto& part : route.paths)
        path_data += infrastructure::project_open_path(context, part);
      infrastructure::infrastructure_require(!path_data.empty(),
        "fiber route produced no projected path: " + route.feature_id);
      const bool is_historical
        = route.source_snapshot != dataset.profile.default_snapshot;
      const bool is_activated
        = !is_historical && route.temporal_class == "planned-to-active";
      const bool is_current_only = !is_historical
        && route.snapshot_membership
             == dataset.profile.default_snapshot + "-only";
      svg::style style;
      std::string attributes = route_attributes(route);
      if (is_historical)
        {
          style = {svg::color::none, 0, {0, 0, 0}, 0.80, 0.015};
          attributes += " stroke-dasharray=\"0.0225 0.025\"";
          historical.add_element(svg::make_path(
            path_data, style, "", true, attributes));
        }
      else if (route.planned)
        {
          style = {svg::color::none, 0, {0, 0, 0}, 0.80, 0.0165};
          attributes += " stroke-dasharray=\"0.0425 0.0275\"";
          planned.add_element(svg::make_path(
            path_data, style, "", true, attributes));
        }
      else if (is_activated)
        {
          style = {svg::color::none, 0, {18, 152, 12}, 0.80, 0.0165};
          activated.add_element(svg::make_path(
            path_data, style, "", true, attributes));
        }
      else if (is_current_only)
        {
          style = {svg::color::none, 0, {18, 152, 12}, 0.80, 0.015};
          current_only.add_element(svg::make_path(
            path_data, style, "", true, attributes));
        }
      else
        {
          style = {svg::color::none, 0, {18, 152, 12}, 0.80, 0.014};
          shared.add_element(svg::make_path(
            path_data, style, "", true, attributes));
        }
    }
  historical.finish_element();
  shared.finish_element();
  current_only.finish_element();
  planned.finish_element();
  activated.finish_element();
  layer.add_element(historical);
  layer.add_element(shared);
  layer.add_element(current_only);
  layer.add_element(planned);
  layer.add_element(activated);
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_fiber_landings(generation::projection_document& document,
                   const generation::projection_context& context,
                   const fiber_dataset& dataset)
{
  svg::group_element layer;
  layer.start_element("network-fiber-landings");
  layer.add_title("Landing points in the cleaned source union");
  svg::group_element historical;
  historical.start_element("fiber-historical-landings");
  svg::group_element current;
  current.start_element("fiber-current-landings");
  for (const fiber_landing& landing : dataset.landings)
    {
      const bool is_current
        = landing.source_snapshot == dataset.profile.default_snapshot;
      const std::string attributes
        = "data-fiber-landing=\"true\" data-landing-id=\""
        + infrastructure::xml_escape(landing.id)
        + "\" data-name=\"" + infrastructure::xml_escape(landing.name)
        + "\" data-source-snapshot=\""
        + infrastructure::xml_escape(landing.source_snapshot)
        + "\" data-snapshot-membership=\""
        + infrastructure::xml_escape(landing.snapshot_membership)
        + "\" data-tbd=\"" + (landing.tbd ? "true" : "false") + "\"";
      if (is_current)
        infrastructure::add_circle(current,
          generation::project_point(context, landing.point),
          {{0, 75, 96}, 0.70, {0, 55, 70}, 0.82, 0.006}, 0.022,
          attributes);
      else
        infrastructure::add_circle(historical,
          generation::project_point(context, landing.point),
          {svg::color::none, 0, {91, 108, 118}, 0.42, 0.008}, 0.018,
          attributes);
    }
  historical.finish_element();
  current.finish_element();
  layer.add_element(historical);
  layer.add_element(current);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
display_snapshot(std::string value)
{
  if (value.starts_with("v3."))
    value.erase(0, 3);
  return value;
}

inline void
add_fiber_legend(generation::projection_document& document,
                 const generation::projection_context& context,
                 const fiber_dataset& dataset)
{
  constexpr double panel_width = 22.0;
  constexpr double panel_height = 1.08;
  svg::group_element layer;
  layer.start_element("network-fiber-legend-and-provenance",
    generation::bottom_right_legend_transform(
      context, panel_width, panel_height));
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, panel_width, panel_height});
  band.add_style({{226, 230, 228}, 0.97, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);

  svg::typography title = infrastructure::infrastructure_typography(
    0.44, {61, 55, 103});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer, "NETWORK FIBER / "
    + display_snapshot(dataset.profile.default_snapshot) + " DEFAULT",
    {0.32, 0.27}, title);
  svg::styled_text(layer,
    std::to_string(dataset.current_routes) + " current route features  |  "
      + std::to_string(dataset.historical_routes)
      + " unmatched 2022-only routes  |  "
      + std::to_string(dataset.landings.size()) + " cleaned-union landings",
    {0.32, 0.61},
    infrastructure::infrastructure_typography(0.112, {55, 67, 72}));
  svg::styled_text(layer,
    "green = current/activated  ·  black dashed = planned  ·  black dotted = 2022-only",
    {0.32, 0.82},
    infrastructure::infrastructure_typography(0.103, {70, 83, 85}));
  svg::styled_text(layer,
    "snapshot-only ≠ construction or decommission",
    {0.32, 1.00},
    infrastructure::infrastructure_typography(0.095, {116, 87, 0}));
  svg::typography attribution = infrastructure::infrastructure_typography(
    0.095, {116, 87, 0});
  attribution._M_anchor = svg::typography::anchor::end;
  attribution._M_align = svg::typography::align::right;
  svg::styled_text(layer,
    "TeleGeography map data · CC BY-NC-SA 3.0",
    {panel_width - 0.32, 1.00}, attribution);
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
fiber_metadata(const generation::projection_spec& spec,
               const fiber_dataset& dataset)
{
  return "<metadata id=\"network-fiber-metadata\""
    " data-schema=\"" + std::string(fiber_schema) + "\""
    " data-kind=\"cleaned-union\" data-default-layer=\"network-fiber\""
    " data-default-snapshot=\""
      + infrastructure::xml_escape(dataset.profile.default_snapshot) + "\""
    " data-older-snapshot=\""
      + infrastructure::xml_escape(dataset.profile.older_snapshot) + "\""
    " data-projection=\"" + std::string(spec.argument) + "\""
    " data-background-color=\"#f2f4f3\" data-title-scale=\"2\""
    " data-source-repository=\""
      + infrastructure::xml_escape(dataset.profile.source_repository) + "\""
    " data-source-commit=\"" + dataset.profile.source_commit + "\""
    " data-source-license=\""
      + infrastructure::xml_escape(dataset.profile.source_license) + "\""
    " data-routes-sha256=\"" + dataset.profile.routes_sha256 + "\""
    " data-landings-sha256=\"" + dataset.profile.landings_sha256 + "\""
    " data-comparison-system-count=\""
      + std::to_string(dataset.profile.comparison_systems) + "\""
    " data-cleaned-union-route-count=\""
      + std::to_string(dataset.routes.size()) + "\""
    " data-current-route-count=\""
      + std::to_string(dataset.current_routes) + "\""
    " data-historical-route-count=\""
      + std::to_string(dataset.historical_routes) + "\""
    " data-cleaned-union-landing-count=\""
      + std::to_string(dataset.landings.size()) + "\""
    " data-snapshot-only-semantics=\"observation-only-not-construction-or-decommission\""
    "></metadata>\n";
}

inline std::string
fiber_output_basename(const generation::projection_spec& spec)
{
  return generation::output_basename("network-fiber", spec);
}

inline void
generate(const generation::projection_spec& spec,
         const fiber_dataset& dataset)
{
  const std::string basename = fiber_output_basename(spec);
  const generation::projection_context context(spec, basename);
  generation::projection_document document(
    basename, std::string(spec.title)
      + " network-fiber cleaned-union atlas",
    context.map_frame.frame_area);
  document.add_raw(fiber_metadata(spec, dataset));
  add_fiber_background(document, context);
  natural_earth::initialize_gdal();
  infrastructure::add_subdued_land(document, context);
  add_fiber_routes(document, context, dataset);
  add_fiber_landings(document, context, dataset);
  add_fiber_legend(document, context, dataset);
}

inline std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  infrastructure::infrastructure_require(input.good(),
    "failed to open generated " + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline std::size_t
token_count(const std::string_view text, const std::string_view token)
{
  std::size_t count = 0;
  for (std::size_t position = 0;
       (position = text.find(token, position)) != std::string_view::npos;
       position += token.size())
    ++count;
  return count;
}

inline void
verify(const std::string& generated,
       const generation::projection_context& context,
       const fiber_dataset& dataset)
{
  infrastructure::infrastructure_require(
    generated.find(generation::view_box_fragment(context))
      != std::string::npos,
    "generated fiber-synthesized SVG has the wrong viewBox");
  constexpr std::array layers {
    "fiber-synthesized-background", "terrestrial-land",
    "network-fiber", "fiber-historical-2022-only",
    "fiber-current-shared", "fiber-current-20260805-only",
    "fiber-current-planned", "fiber-planned-to-active",
    "network-fiber-landings", "fiber-historical-landings",
    "fiber-current-landings", "network-fiber-legend-and-provenance",
  };
  for (const std::string_view layer : layers)
    infrastructure::infrastructure_require(
      generated.find("<g id=\"" + std::string(layer) + "\"")
        != std::string::npos,
      "generated fiber-synthesized SVG is missing layer "
        + std::string(layer));
  infrastructure::infrastructure_require(
    token_count(generated, "data-fiber-route=\"true\"")
      == dataset.routes.size()
      && token_count(generated, "data-fiber-landing=\"true\"")
           == dataset.landings.size(),
    "generated fiber-synthesized SVG has the wrong feature counts");
  infrastructure::infrastructure_require(
    generated.find("id=\"network-fiber-metadata\"")
      != std::string::npos
      && generated.find("data-default-layer=\"network-fiber\"")
           != std::string::npos
      && generated.find("data-default-snapshot=\""
        + dataset.profile.default_snapshot + "\"") != std::string::npos
      && generated.find("snapshot-only ≠ construction or decommission")
           != std::string::npos
      && generated.find("CC BY-NC-SA 3.0") != std::string::npos,
    "generated fiber-synthesized SVG is missing semantics or provenance");
  infrastructure::infrastructure_require(
    generated.find(" nan") == std::string::npos
      && generated.find(" -nan") == std::string::npos
      && generated.find(" inf") == std::string::npos
      && generated.find(" -inf") == std::string::npos,
    "generated fiber-synthesized SVG has non-finite data");
  generation::verify_configured_label_font(
    generated, "Fiber-synthesized SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 3)
    throw std::invalid_argument(
      "usage: generate-fiber-synthesized PROJECTION DATA_DIRECTORY");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const fiber_dataset dataset = load_fiber_dataset(
    std::filesystem::absolute(argv[2]));
  const std::string basename = fiber_output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate(spec, dataset);
  verify(read_generated(basename), context, dataset);
  return 0;
}

} // namespace cart0freak0::fiber_synthesized_generation

#endif

// Projection-aware World Game resources SVG generation.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_RESOURCES_GENERATION_H
#define CART0FREAK0_RESOURCES_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <map>
#include <numbers>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

#include <a60-io.h>
#include <a60-svg.h>

#include "generation-typography.h"
#include "natural-earth-generation.h"
#include "projection-generation-common.h"
#include "resources-data.h"

namespace cart0freak0::resources_generation {

namespace generation = cart0freak0::generation;
namespace natural_earth = cart0freak0::natural_earth_generation;

inline std::string
resources_xml_escape(std::string value)
{
  constexpr std::array replacements {
    std::pair {std::string_view {"&"}, std::string_view {"&amp;"}},
    std::pair {std::string_view {"\""}, std::string_view {"&quot;"}},
    std::pair {std::string_view {"<"}, std::string_view {"&lt;"}},
    std::pair {std::string_view {">"}, std::string_view {"&gt;"}},
  };
  for (const auto& [source, replacement] : replacements)
    {
      std::size_t position = 0;
      while ((position = value.find(source, position)) != std::string::npos)
        {
          value.replace(position, source.size(), replacement);
          position += replacement.size();
        }
    }
  return value;
}

inline std::string
format_resource_number(const double value, const int precision = 3)
{
  std::ostringstream output;
  output << std::fixed << std::setprecision(precision) << value;
  return output.str();
}

inline std::string
format_resource_total(const std::uint64_t value)
{
  std::string result = std::to_string(value);
  for (std::ptrdiff_t position = static_cast<std::ptrdiff_t>(result.size()) - 3;
       position > 0; position -= 3)
    result.insert(static_cast<std::size_t>(position), ",");
  return result;
}

inline svg::typography
resources_typography(const double size, const svg::color_qi color)
{
  svg::typography result = generation::with_configured_label_font(
    svg::k::hyperl_typo);
  result._M_size = size;
  result._M_style = {color, 0.96, {249, 247, 240}, 0.82, 0.004};
  result._M_anchor = svg::typography::anchor::start;
  result._M_align = svg::typography::align::left;
  result._M_baseline = svg::typography::baseline::central;
  return result;
}

inline svg::color_qi
resource_color(const resource_category category)
{
  switch (category)
    {
    case resource_category::metals: return {177, 70, 48};
    case resource_category::industrial_materials: return {37, 127, 108};
    case resource_category::energy_feedstocks: return {74, 78, 130};
    }
  throw std::logic_error("unhandled resource category color");
}

inline std::string
resource_polygon_path(const svg::point_2t origin, const double radius,
                      const unsigned vertices, const double rotation_degrees)
{
  svg::vrange points;
  points.reserve(vertices + 1);
  for (unsigned index = 0; index < vertices; ++index)
    {
      const double angle = (rotation_degrees + 360.0 * index / vertices)
        * std::numbers::pi / 180.0;
      points.emplace_back(std::get<0>(origin) + std::cos(angle) * radius,
                          std::get<1>(origin) + std::sin(angle) * radius);
    }
  points.push_back(points.front());
  return svg::make_path_data_from_points(points);
}

inline void
add_resource_circle(svg::group_element& layer, const svg::point_2t point,
                    const double radius, const svg::style& style,
                    const std::string& attributes)
{
  svg::circle_element circle;
  circle.start_element();
  circle.add_data({std::get<0>(point), std::get<1>(point), radius});
  circle.add_style(style);
  if (!attributes.empty())
    circle.add_raw(attributes);
  circle.finish_element();
  layer.add_element(circle);
}

inline void
add_resource_line(svg::group_element& layer, const svg::point_2t start,
                  const svg::point_2t finish, const svg::style& style,
                  const std::string& attributes = {})
{
  svg::line_element line;
  line.start_element();
  line.add_data({std::get<0>(start), std::get<0>(finish),
                 std::get<1>(start), std::get<1>(finish)});
  line.add_style(style);
  if (!attributes.empty())
    line.add_raw(attributes);
  line.finish_element();
  layer.add_element(line);
}

inline void
add_resource_symbol(svg::group_element& layer, const svg::point_2t point,
                    const resource_category category, const double radius,
                    const std::string& attributes,
                    const bool modern = false)
{
  const svg::color_qi color = modern ? svg::color_qi {211, 151, 35}
                                     : resource_color(category);
  if (modern)
    {
      add_resource_circle(layer, point, radius,
        {svg::color::none, 0, color, 0.98, radius * 0.22}, attributes);
      add_resource_circle(layer, point, radius * 0.33,
        {color, 0.88, svg::color::none, 0, 0}, {});
      return;
    }
  const svg::style style {color, 0.86, {249, 238, 218}, 0.98,
                          radius * 0.075};
  switch (category)
    {
    case resource_category::metals:
      add_resource_circle(layer, point, radius * 0.88, style, attributes);
      break;
    case resource_category::industrial_materials:
      layer.add_element(svg::make_path(
        resource_polygon_path(point, radius, 4, 0), style, "", true,
        attributes));
      break;
    case resource_category::energy_feedstocks:
      layer.add_element(svg::make_path(
        resource_polygon_path(point, radius, 4, 45), style, "", true,
        attributes));
      break;
    }
}

struct displayed_resource_point
{
  svg::point_2t anchor;
  svg::point_2t display;
};

struct resources_layout
{
  std::vector<std::optional<displayed_resource_point>> historical;
  std::vector<std::optional<displayed_resource_point>> modern;
};

struct pending_resource_point
{
  bool modern = false;
  std::size_t index = 0;
  const producer* source = nullptr;
};

inline resources_layout
layout_resource_points(const generation::projection_context& context,
                       const resources_profile& profile)
{
  resources_layout result;
  result.historical.resize(profile.historical.size());
  result.modern.resize(profile.modern.size());
  std::map<std::string, std::vector<pending_resource_point>> groups;
  for (std::size_t index = 0; index < profile.historical.size(); ++index)
    if (profile.historical[index].leader.has_value())
      groups[profile.historical[index].leader->modern_area].push_back(
        {false, index, &*profile.historical[index].leader});
  for (std::size_t index = 0; index < profile.modern.size(); ++index)
    if (profile.modern[index].leader.has_value())
      groups[profile.modern[index].leader->modern_area].push_back(
        {true, index, &*profile.modern[index].leader});

  constexpr std::size_t ring_capacity = 8;
  for (const auto& [area, points] : groups)
    {
      resources_require(!points.empty(), "internal empty resource cluster");
      const producer& first = *points.front().source;
      const svg::point_2t anchor = generation::project_point(
        context, {first.latitude, first.longitude});
      for (const pending_resource_point point : points)
        resources_require(point.source->modern_area == area
                            && std::abs(point.source->longitude
                                        - first.longitude) < 1e-8
                            && std::abs(point.source->latitude
                                        - first.latitude) < 1e-8,
                          "resource records for '" + area
                            + "' disagree on representative coordinates");

      for (std::size_t position = 0; position < points.size(); ++position)
        {
          svg::point_2t display = anchor;
          if (points.size() > 1)
            {
              const std::size_t ring = position / ring_capacity + 1;
              const std::size_t slot = position % ring_capacity;
              const std::size_t before = (ring - 1) * ring_capacity;
              const std::size_t on_ring = std::min(
                ring_capacity, points.size() - before);
              const double angle = -std::numbers::pi / 2
                + 2 * std::numbers::pi * slot / on_ring
                + (ring % 2 == 0 ? std::numbers::pi / ring_capacity : 0);
              const double radius = profile.cluster_step * ring;
              display = {
                std::get<0>(anchor) + std::cos(angle) * radius,
                std::get<1>(anchor) + std::sin(angle) * radius,
              };
              const double margin = profile.marker_radius * 1.2;
              display = {
                std::clamp(std::get<0>(display), margin,
                           context.map_frame.width() - margin),
                std::clamp(std::get<1>(display), margin,
                           context.map_frame.height() - margin),
              };
            }
          displayed_resource_point projected {anchor, display};
          const pending_resource_point destination = points[position];
          if (destination.modern)
            result.modern[destination.index] = projected;
          else
            result.historical[destination.index] = projected;
        }
    }
  return result;
}

inline void
add_resources_background(generation::projection_document& document,
                         const generation::projection_context& context)
{
  svg::group_element layer;
  layer.start_element("resources-background");
  svg::rect_element rectangle;
  rectangle.start_element();
  rectangle.add_data({0, 0, context.map_frame.width(),
                      context.map_frame.height()});
  rectangle.add_style({{242, 239, 226}, 1, svg::color::none, 0, 0});
  rectangle.add_raw("id=\"resources-ground\"");
  rectangle.finish_element();
  layer.add_element(rectangle);
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_resources_land(generation::projection_document& document,
                   const generation::projection_context& context)
{
  const natural_earth::layer_spec land {
    "terrestrial-land", "Subdued Natural Earth 1:10m land",
    "ne_10m_land.shp", natural_earth::geometry_role::area,
    natural_earth::area_style({213, 210, 195}), 0.05, 0.82,
  };
  svg::group_element layer;
  layer.start_element(std::string(land.id));
  layer.add_title(std::string(land.title));
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      const natural_earth::antarctic_placement placement
        = natural_earth::make_antarctic_placement(context, land);
      static_cast<void>(natural_earth::render_source(
        layer, land, context,
        {a60::carto::star_x_antarctic_cutoff_latitude, 90}));
      static_cast<void>(natural_earth::render_antarctic_source(
        layer, land, context, placement));
    }
  else
    static_cast<void>(natural_earth::render_source(layer, land, context));
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_resource_tethers(generation::projection_document& document,
                     const resources_profile& profile,
                     const resources_layout& layout)
{
  svg::group_element layer;
  layer.start_element("resource-tethers");
  const svg::style style {svg::color::none, 0, {103, 98, 87}, 0.52, 0.018};
  for (std::size_t index = 0; index < layout.historical.size(); ++index)
    if (layout.historical[index].has_value()
        && generation::point_distance(layout.historical[index]->anchor,
                                      layout.historical[index]->display)
             > 1e-9)
      add_resource_line(layer, layout.historical[index]->anchor,
        layout.historical[index]->display, style,
        "data-resource-tether=\"true\" data-resource-id=\""
          + resources_xml_escape(profile.historical[index].id) + "\"");
  for (std::size_t index = 0; index < layout.modern.size(); ++index)
    if (layout.modern[index].has_value()
        && generation::point_distance(layout.modern[index]->anchor,
                                      layout.modern[index]->display) > 1e-9)
      add_resource_line(layer, layout.modern[index]->anchor,
        layout.modern[index]->display, style,
        "data-resource-tether=\"true\" data-resource-era=\"modern-context\""
          " data-resource-id=\""
          + resources_xml_escape(profile.modern[index].id) + "\"");
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
historical_marker_attributes(const historical_resource& record)
{
  resources_require(record.leader.has_value()
                      && record.world_total.has_value()
                      && record.leader_pdf_page.has_value(),
                    "cannot emit an unavailable historical marker");
  const producer& leader = *record.leader;
  return "id=\"resource-marker-" + resources_xml_escape(record.id) + "\""
    " data-resource-record=\"true\" data-resource-era=\"historical\""
    " data-resource-id=\"" + resources_xml_escape(record.id) + "\""
    " data-source-index=\"" + std::to_string(record.index) + "\""
    " data-category=\"" + std::string(category_name(record.category)) + "\""
    " data-world-total=\"" + std::to_string(*record.world_total) + "\""
    " data-source-unit=\"" + resources_xml_escape(record.source_unit) + "\""
    " data-producer=\"" + resources_xml_escape(leader.historical_label) + "\""
    " data-modern-area=\"" + resources_xml_escape(leader.modern_area) + "\""
    " data-share-percent=\"" + format_resource_number(leader.share_percent)
    + "\" data-header-pdf-page=\"" + std::to_string(record.header_pdf_page)
    + "\" data-leader-pdf-page=\"" + std::to_string(*record.leader_pdf_page)
    + "\" data-representative-geography=\"true\"";
}

inline void
add_historical_resource_layers(generation::projection_document& document,
                               const resources_profile& profile,
                               const resources_layout& layout)
{
  constexpr std::array categories {
    resource_category::metals, resource_category::industrial_materials,
    resource_category::energy_feedstocks,
  };
  for (const resource_category category : categories)
    {
      svg::group_element layer;
      layer.start_element("historical-" + std::string(category_name(category)));
      layer.add_title("1960 leading producers — "
                      + std::string(category_name(category)));
      for (std::size_t index = 0; index < profile.historical.size(); ++index)
        {
          const historical_resource& record = profile.historical[index];
          if (record.category != category || !record.leader.has_value())
            continue;
          resources_require(layout.historical[index].has_value(),
                            "historical resource has no projected point");
          const double scaled_radius = profile.marker_radius
            * (0.72 + 0.28 * std::sqrt(record.leader->share_percent / 100.0));
          add_resource_symbol(layer, layout.historical[index]->display,
            category, scaled_radius, historical_marker_attributes(record));
        }
      layer.finish_element();
      document.add_element(layer);
    }
}

inline std::string
modern_marker_attributes(const modern_resource& record)
{
  resources_require(record.leader.has_value(),
                    "cannot emit an unlocated modern context marker");
  const producer& leader = *record.leader;
  return "id=\"modern-resource-marker-" + resources_xml_escape(record.id)
    + "\" data-modern-resource-marker=\"true\""
    " data-resource-era=\"modern-context\" data-resource-id=\""
    + resources_xml_escape(record.id) + "\" data-reference-year=\""
    + std::to_string(record.reference_year) + "\" data-world-total=\""
    + std::to_string(record.world_total) + "\" data-unit=\""
    + resources_xml_escape(record.unit) + "\" data-producer=\""
    + resources_xml_escape(leader.historical_label) + "\" data-modern-area=\""
    + resources_xml_escape(leader.modern_area) + "\" data-share-percent=\""
    + format_resource_number(leader.share_percent)
    + "\" data-source-organization=\""
    + resources_xml_escape(record.source_organization)
    + "\" data-representative-geography=\"true\"";
}

inline void
add_modern_resource_layer(generation::projection_document& document,
                          const resources_profile& profile,
                          const resources_layout& layout)
{
  svg::group_element layer;
  layer.start_element("modern-resource-context");
  layer.add_title("Separate modern comparison indicators with reported leaders");
  for (std::size_t index = 0; index < profile.modern.size(); ++index)
    if (profile.modern[index].leader.has_value())
      {
        resources_require(layout.modern[index].has_value(),
                          "modern resource has no projected point");
        add_resource_symbol(layer, layout.modern[index]->display,
          resource_category::metals, profile.marker_radius * 1.05,
          modern_marker_attributes(profile.modern[index]), true);
      }
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
historical_catalog_element(const historical_resource& record)
{
  std::string result = "<rdf:Description rdf:about=\"#resource-catalog-"
    + resources_xml_escape(record.id) + "\" id=\"resource-catalog-"
    + resources_xml_escape(record.id)
    + "\" data-resource-catalog-record=\"true\" data-source-index=\""
    + std::to_string(record.index) + "\" data-label=\""
    + resources_xml_escape(record.label) + "\" data-category=\""
    + std::string(category_name(record.category)) + "\" data-world-total=\"";
  result += record.world_total.has_value()
    ? std::to_string(*record.world_total) : "N.A.";
  result += "\" data-source-unit=\"" + resources_xml_escape(record.source_unit)
    + "\" data-header-pdf-page=\"" + std::to_string(record.header_pdf_page)
    + "\" data-leader-pdf-page=\"";
  result += record.leader_pdf_page.has_value()
    ? std::to_string(*record.leader_pdf_page) : "N.A.";
  result += "\" data-leader=\"";
  result += record.leader.has_value()
    ? resources_xml_escape(record.leader->historical_label) : "N.A.";
  result += "\" data-share-percent=\"";
  result += record.leader.has_value()
    ? format_resource_number(record.leader->share_percent) : "N.A.";
  return result + "\"></rdf:Description>\n";
}

inline std::string
modern_catalog_element(const modern_resource& record)
{
  std::string result = "<rdf:Description rdf:about=\"#modern-context-catalog-"
    + resources_xml_escape(record.id)
    + "\" id=\"modern-context-catalog-"
    + resources_xml_escape(record.id)
    + "\" data-modern-context-catalog-record=\"true\" data-label=\""
    + resources_xml_escape(record.label) + "\" data-reference-year=\""
    + std::to_string(record.reference_year) + "\" data-world-total=\""
    + std::to_string(record.world_total) + "\" data-unit=\""
    + resources_xml_escape(record.unit) + "\" data-leader=\"";
  result += record.leader.has_value()
    ? resources_xml_escape(record.leader->historical_label) : "global-only";
  result += "\" data-share-percent=\"";
  result += record.leader.has_value()
    ? format_resource_number(record.leader->share_percent) : "N.A.";
  return result + "\" data-source-organization=\""
    + resources_xml_escape(record.source_organization)
    + "\" data-source-title=\"" + resources_xml_escape(record.source_title)
    + "\" data-source-url=\"" + resources_xml_escape(record.source_url)
    + "\"></rdf:Description>\n";
}

inline std::string
resources_metadata_element(const generation::projection_spec& spec,
                           const resources_profile& profile)
{
  std::string result = "<metadata id=\"resources-metadata\""
    " data-workflow=\"World Game resources / production leaders\""
    " data-profile=\"" + resources_xml_escape(profile.path.filename().string())
    + "\" data-projection=\"" + std::string(spec.argument)
    + "\" data-publication-year=\"" + std::to_string(profile.publication_year)
    + "\" data-production-year=\"" + std::to_string(profile.production_year)
    + "\" data-historical-record-count=\""
    + std::to_string(profile.historical.size())
    + "\" data-modern-context-count=\"" + std::to_string(profile.modern.size())
    + "\" data-source-page-url=\"" + resources_xml_escape(profile.source_page_url)
    + "\" data-source-pdf-url=\"" + resources_xml_escape(profile.source_pdf_url)
    + "\" data-source-pdf-sha256=\"" + profile.source_pdf_sha256
    + "\" data-source-pdf-pages=\""
    + resources_xml_escape(profile.source_pdf_pages)
    + "\" data-historical-modern-separation=\"true\""
    " data-missing-is-zero=\"false\" data-geography=\"representative-points\">\n";
  result += "<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-"
    "ns#\">\n";
  for (const historical_resource& record : profile.historical)
    result += historical_catalog_element(record);
  for (const modern_resource& record : profile.modern)
    result += modern_catalog_element(record);
  result += "</rdf:RDF>\n</metadata>\n";
  return result;
}

inline void
add_resources_legend(generation::projection_document& document,
                     const generation::projection_context& context,
                     const resources_profile& profile)
{
  if (!profile.show_legend)
    return;
  svg::group_element layer;
  layer.start_element("resource-legend");
  svg::rect_element band;
  band.start_element();
  band.add_data({0, 0, context.map_frame.width(), 2.16});
  band.add_style({{249, 247, 239}, 0.96, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);

  svg::typography title = resources_typography(0.20, {47, 44, 38});
  title._M_w = svg::typography::weight::bold;
  svg::styled_text(layer, "WORLD GAME RESOURCES / 1960 PRODUCTION LEADERS",
                   {0.30, 0.20}, title);
  svg::styled_text(layer,
    "Fuller + McHale, 1963 · 40 source columns · markers are representative "
    "country points, not extraction sites · N.A. is not zero",
    {0.30, 0.42}, resources_typography(0.095, {91, 84, 73}));

  constexpr std::size_t columns = 5;
  const double column_width = (context.map_frame.width() - 0.6) / columns;
  for (std::size_t position = 0; position < profile.historical.size(); ++position)
    {
      const historical_resource& record = profile.historical[position];
      const std::size_t row = position / columns;
      const std::size_t column = position % columns;
      const double x = 0.34 + column * column_width;
      const double y = 0.66 + row * 0.185;
      const std::string attributes = "data-resource-legend-entry=\"true\""
        " data-resource-id=\"" + resources_xml_escape(record.id) + "\"";
      if (record.leader.has_value())
        add_resource_symbol(layer, {x, y}, record.category, 0.043, attributes);
      else
        add_resource_circle(layer, {x, y}, 0.036,
          {svg::color::none, 0, {116, 111, 101}, 0.9, 0.009}, attributes);
      std::ostringstream label;
      label << std::setw(2) << std::setfill('0') << record.index << " "
            << record.label << " · ";
      if (record.leader.has_value())
        label << format_resource_number(record.leader->share_percent)
              << "% " << record.leader->historical_label;
      else
        label << "N.A.";
      svg::styled_text(layer, resources_xml_escape(label.str()), {x + 0.075, y},
                       resources_typography(0.082, {58, 55, 49}));
    }
  layer.finish_element();
  document.add_element(layer);
}

inline void
add_modern_context_legend(generation::projection_document& document,
                          const generation::projection_context& context,
                          const resources_profile& profile)
{
  if (!profile.show_legend)
    return;
  svg::group_element layer;
  layer.start_element("modern-context-legend");
  const double band_height = 0.93;
  const double top = context.map_frame.height() - band_height;
  svg::rect_element band;
  band.start_element();
  band.add_data({0, top, context.map_frame.width(), band_height});
  band.add_style({{40, 44, 48}, 0.94, svg::color::none, 0, 0});
  band.finish_element();
  layer.add_element(band);
  svg::typography heading = resources_typography(0.12, {244, 217, 150});
  heading._M_w = svg::typography::weight::bold;
  heading._M_style = {{244, 217, 150}, 1, svg::color::none, 0, 0};
  svg::styled_text(layer,
    "MODERN CONTEXT / SEPARATE INDICATORS — NOT A CONTINUATION OF THE 1960 MATRIX",
    {0.30, top + 0.17}, heading);
  const double column_width = (context.map_frame.width() - 0.6)
    / profile.modern.size();
  for (std::size_t index = 0; index < profile.modern.size(); ++index)
    {
      const modern_resource& record = profile.modern[index];
      const double x = 0.34 + index * column_width;
      add_resource_symbol(layer, {x, top + 0.45},
        resource_category::metals, 0.045,
        "data-modern-context-legend-entry=\"true\" data-resource-id=\""
          + resources_xml_escape(record.id) + "\"", true);
      svg::typography text = resources_typography(0.088, {235, 233, 223});
      text._M_style = {{235, 233, 223}, 1, svg::color::none, 0, 0};
      svg::styled_text(layer,
        resources_xml_escape(std::to_string(record.reference_year) + " "
          + record.label + " · " + format_resource_total(record.world_total)
          + " " + record.unit), {x + 0.08, top + 0.43}, text);
      std::string detail = record.source_organization + " · ";
      detail += record.leader.has_value()
        ? format_resource_number(record.leader->share_percent) + "% "
            + record.leader->historical_label
        : "global total only";
      svg::typography detail_text = resources_typography(
        0.077, {192, 196, 191});
      detail_text._M_style = {{192, 196, 191}, 1,
                              svg::color::none, 0, 0};
      svg::styled_text(layer, resources_xml_escape(detail),
                       {x + 0.08, top + 0.65}, detail_text);
    }
  layer.finish_element();
  document.add_element(layer);
}

inline std::string
resources_output_basename(const generation::projection_spec& spec)
{ return generation::output_basename("resources", spec); }

inline void
generate_resources(const generation::projection_spec& spec,
                   const resources_profile& profile)
{
  const std::string basename = resources_output_basename(spec);
  const generation::projection_context context(spec, basename);
  const resources_layout layout = layout_resource_points(context, profile);
  generation::projection_document document(
    basename, std::string(spec.title) + " World Game resources: 1960 "
      "production leaders with separate modern context",
    context.map_frame.frame_area);
  document.add_raw(resources_metadata_element(spec, profile));
  add_resources_background(document, context);
  natural_earth::initialize_gdal();
  add_resources_land(document, context);
  add_resource_tethers(document, profile, layout);
  add_historical_resource_layers(document, profile, layout);
  add_modern_resource_layer(document, profile, layout);
  add_resources_legend(document, context, profile);
  add_modern_context_legend(document, context, profile);
}

inline std::string
read_generated_resources(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  resources_require(input.good(), "failed to open generated " + basename
                                    + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

inline std::size_t
resources_token_count(const std::string_view text,
                      const std::string_view token)
{
  std::size_t count = 0;
  std::size_t position = 0;
  while ((position = text.find(token, position)) != std::string_view::npos)
    {
      ++count;
      position += token.size();
    }
  return count;
}

inline void
verify_generated_resources(const std::string& generated,
                           const generation::projection_context& context,
                           const resources_profile& profile)
{
  resources_require(generated.find(generation::view_box_fragment(context))
                      != std::string::npos,
                    "generated resources SVG has the wrong viewBox");
  constexpr std::array required_layers {
    std::string_view {"resources-background"},
    std::string_view {"terrestrial-land"},
    std::string_view {"resource-tethers"},
    std::string_view {"historical-metals"},
    std::string_view {"historical-industrial-materials"},
    std::string_view {"historical-energy-feedstocks"},
    std::string_view {"modern-resource-context"},
    std::string_view {"resource-legend"},
    std::string_view {"modern-context-legend"},
  };
  for (const std::string_view layer : required_layers)
    resources_require(generated.find("<g id=\"" + std::string(layer) + "\">")
                        != std::string::npos,
                      "generated resources SVG is missing layer "
                        + std::string(layer));
  const std::size_t mapped_historical = static_cast<std::size_t>(
    std::count_if(profile.historical.begin(), profile.historical.end(),
                  [](const historical_resource& record) {
                    return record.leader.has_value();
                  }));
  const std::size_t mapped_modern = static_cast<std::size_t>(
    std::count_if(profile.modern.begin(), profile.modern.end(),
                  [](const modern_resource& record) {
                    return record.leader.has_value();
                  }));
  resources_require(resources_token_count(
    generated, "data-resource-record=\"true\"") == mapped_historical,
    "generated resources SVG has the wrong historical marker count");
  resources_require(resources_token_count(
    generated, "data-modern-resource-marker=\"true\"") == mapped_modern,
    "generated resources SVG has the wrong modern marker count");
  resources_require(resources_token_count(
    generated, "data-resource-catalog-record=\"true\"")
      == profile.historical.size(),
    "generated resources SVG has an incomplete historical catalog");
  resources_require(resources_token_count(
    generated, "data-modern-context-catalog-record=\"true\"")
      == profile.modern.size(),
    "generated resources SVG has an incomplete modern catalog");
  for (const historical_resource& record : profile.historical)
    resources_require(generated.find("id=\"resource-catalog-" + record.id
                                      + "\"") != std::string::npos,
                      "generated resources SVG omits catalog record "
                        + record.id);
  resources_require(generated.find("id=\"resources-metadata\"")
                      != std::string::npos
                      && generated.find("data-source-pdf-sha256=\""
                        + profile.source_pdf_sha256 + "\"")
                           != std::string::npos
                      && generated.find(
                        "data-historical-modern-separation=\"true\"")
                           != std::string::npos
                      && generated.find("data-missing-is-zero=\"false\"")
                           != std::string::npos,
                    "generated resources SVG lacks provenance or semantic "
                      "metadata");
  resources_require(generated.find(" nan ") == std::string::npos
                      && generated.find(" -nan ") == std::string::npos
                      && generated.find(" inf ") == std::string::npos
                      && generated.find(" -inf ") == std::string::npos,
                    "generated resources SVG has non-finite data");
  generation::verify_configured_label_font(generated, "resources SVG");
}

inline int
run(const int argc, char** argv)
{
  if (argc != 3)
    throw std::invalid_argument(
      "usage: generate-resources PROJECTION PROFILE.json");
  const generation::projection_spec& spec
    = generation::find_projection_spec(argv[1]);
  const resources_profile profile = load_resources_profile(
    std::filesystem::absolute(argv[2]));
  const std::string basename = resources_output_basename(spec);
  const generation::projection_context context(spec, basename);
  generate_resources(spec, profile);
  verify_generated_resources(
    read_generated_resources(basename), context, profile);
  return 0;
}

} // namespace cart0freak0::resources_generation

#endif // CART0FREAK0_RESOURCES_GENERATION_H

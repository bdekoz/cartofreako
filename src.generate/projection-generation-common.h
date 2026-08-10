// Shared configuration and seam-safe path projection for SVG generators.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_TESTS_PROJECTION_GENERATION_COMMON_H
#define CART0FREAK0_TESTS_PROJECTION_GENERATION_COMMON_H 1

#include <cstddef>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <string_view>

#include <izzi-svg.h>

#include "cart0freak0-projection-runtime.h"

namespace cart0freak0::generation {

using a60::carto::frame;

/// Physical unit for print-oriented generated map documents. Projection and
/// viewBox coordinates remain unitless, with one coordinate unit per inch.
inline constexpr svg::unit projection_document_unit = svg::unit::inch;

/// Root SVG document whose frame dimensions are physical print dimensions.
struct projection_document : svg::svg_element
{
  projection_document(const std::string& name,
                      const std::string& description,
                      const frame::area& document_area,
                      const bool lifetime = true)
  : svg::svg_element(
      name, document_area, lifetime, projection_document_unit)
  {
    if (lifetime)
      add_desc(description);
  }
};

// The renderer-neutral core is authoritative for projection construction,
// native-cell classification, and seam routing. These using declarations
// preserve the established generator API while making native and browser
// clients execute the same code.
using projection_runtime::agproj;
using projection_runtime::append_unique;
using projection_runtime::authagraph_cell;
using projection_runtime::cahill_keyes_cell;
using projection_runtime::ckproj;
using projection_runtime::dymaxionproj;
using projection_runtime::find_coordinate_wrap;
using projection_runtime::find_cell_transition;
using projection_runtime::find_projection_spec;
using projection_runtime::geographic_point;
using projection_runtime::has_valid_frame;
using projection_runtime::interpolate;
using projection_runtime::make_frame;
using projection_runtime::make_projection;
using projection_runtime::myriaproj;
using projection_runtime::point_distance;
using projection_runtime::project_path;
using projection_runtime::project_path_detailed;
using projection_runtime::project_point;
using projection_runtime::projected_path_result;
using projection_runtime::projected_transition;
using projection_runtime::projection_cell;
using projection_runtime::projection_context;
using projection_runtime::projection_kind;
using projection_runtime::projection_spec;
using projection_runtime::projection_variant;
using projection_runtime::require;
using projection_runtime::starxproj;
using projection_runtime::topology_kind;
using projection_runtime::voronoiproj;

inline constexpr const auto& projection_specs
  = projection_runtime::projection_specs;

inline const projection_spec&
projection_from_arguments(const int argc, char** argv)
{
  if (argc == 1)
    return projection_specs.front();
  if (argc == 2)
    return find_projection_spec(argv[1]);
  throw std::invalid_argument(
    "generator accepts at most one projection argument");
}

inline std::string
output_basename(const std::string_view artifact,
                const projection_spec& spec)
{
  return std::string(artifact) + "-" + std::string(spec.output_tag);
}

inline std::string
view_box_fragment(const projection_context& context)
{
  char buffer[128] {};
  const int written = std::snprintf(
    buffer, sizeof(buffer), "viewBox=\"0 0 %.6f %.6f\"",
    context.map_frame.width(), context.map_frame.height());
  require(written > 0 && static_cast<std::size_t>(written) < sizeof(buffer),
          "could not format SVG viewBox");
  return buffer;
}

} // namespace cart0freak0::generation

#endif

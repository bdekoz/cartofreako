// Myriahedral projection face-group slicing support -*- mode: C++ -*-

#ifndef CART0FREAK0_MYRIAHEDRAL_SLICING_H
#define CART0FREAK0_MYRIAHEDRAL_SLICING_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60.h>
#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-myriahedral.h"

/**
 * @file cart0freak0-myriahedral-slicing.h
 * Exact terminal-face slicing for the reference Myriahedral projection.
 *
 * A depth-5 Myriahedral net has 5120 small triangular faces connected by a
 * land-aware hinge tree. The two groups implemented here form an exact,
 * complementary partition of the reference net: group 1 contains North
 * America, South America, Antarctica, Greenland, and Iceland; group 2
 * contains every remaining face. Starting at tree root 103 in group 2,
 * crossing any of five selected hinge edges toggles the group assignment.
 * This produces 2722 faces in group 1 and 2398 in group 2.
 *
 * Generated SVG wrappers use the selected terminal triangles as a clip mask
 * around the complete 44 by 24.75 inch water map. Nothing is reprojected or
 * scaled: each wrapper uses the tight carrier-coordinate bounds of its mask.
 */

namespace a60::carto::myriahedral_slicing {

using myriahedral_detail::face_count;

/// Complete carrier-coordinate rectangle enclosing one face group.
struct projected_view
{
  double x;      ///< Left edge in carrier coordinates.
  double y;      ///< Top edge in carrier coordinates.
  double width;  ///< Viewport width in carrier units.
  double height; ///< Viewport height in carrier units.
};

/// One retained tree edge intentionally cut to make the semantic partition.
struct hinge_cut
{
  std::uint16_t first;  ///< Face index on one side of the hinge.
  std::uint16_t second; ///< Face index on the other side of the hinge.
};

/// Five reference-tree hinges separating the requested land groups.
inline constexpr std::array group_boundary_hinges {
  hinge_cut {51, 273},
  hinge_cut {3929, 3924},
  hinge_cut {2026, 2025},
  hinge_cut {3601, 3602},
  hinge_cut {264, 259},
};

/// Stable face counts resulting from @c group_boundary_hinges.
inline constexpr std::array<std::size_t, 2> expected_group_face_counts {
  2722, 2398,
};

/// Geometry and descriptive metadata for one generated slice.
struct slice_descriptor
{
  int number;                   ///< One-based group number.
  std::string_view name;        ///< Short stable group name.
  std::string_view contents;    ///< Human-readable geographic contents.
  frame output_frame;           ///< Tight, arbitrary-ratio output frame.
  projected_view source_view;   ///< Rectangle on the complete carrier.
  std::size_t selected_faces;   ///< Number of terminal faces in the mask.
  std::vector<svg::vrange> clip_triangles; ///< Three points per face.
};

/// Format an SVG coordinate while retaining useful double precision.
/// @param value Coordinate or dimension to format.
/// @return Locale-independent numeric text for an SVG attribute.
inline std::string
format_number(const double value)
{
  std::ostringstream stream;
  stream << std::setprecision(12) << std::defaultfloat << value;
  return stream.str();
}

/// Escape text for use in an XML attribute or text node.
/// @param value Unescaped UTF-8 text.
/// @return Text with XML metacharacters replaced by entities.
inline std::string
xml_escape(const std::string_view value)
{
  std::string result;
  result.reserve(value.size());
  for (const char character : value)
    switch (character)
      {
      case '&': result += "&amp;"; break;
      case '<': result += "&lt;"; break;
      case '>': result += "&gt;"; break;
      case '\"': result += "&quot;"; break;
      case '\'': result += "&apos;"; break;
      default: result += character; break;
      }
  return result;
}

/// Enforce the reference projection's 16:9 complete carrier.
/// @param carrier Complete Myriahedral carrier to validate.
/// @throws std::invalid_argument if the frame is non-finite, non-positive, or
/// not 16:9.
inline void
require_valid_carrier(const frame& carrier)
{
  if (!is_myriahedral_frame(carrier))
    throw std::invalid_argument(
      "Myriahedral slice carrier must have a finite, positive 16:9 frame");
}

/// Test an unordered face pair against the configured boundary hinges.
/// @param left First terminal face index.
/// @param right Second terminal face index.
/// @return True if the pair is one of the five semantic separators.
inline constexpr bool
is_group_boundary(const std::size_t left, const std::size_t right)
{
  for (const hinge_cut edge : group_boundary_hinges)
    if ((edge.first == left && edge.second == right)
        || (edge.first == right && edge.second == left))
      return true;
  return false;
}

/// Check that an undirected tree contains one edge.
/// @param tree Decoded reference-tree adjacency.
/// @param edge Face pair to find.
/// @return True if the two faces are retained neighbors.
inline bool
contains_edge(const myriahedral_detail::tree_adjacency& tree,
              const hinge_cut edge)
{
  for (std::size_t index = 0; index < tree.degree[edge.first]; ++index)
    if (tree.neighbors[edge.first][index] == edge.second)
      return true;
  return false;
}

/// Assign every reference terminal face to requested group 1 or 2.
/// @return One-based group number for each terminal face.
/// @throws std::logic_error if a configured boundary is not a retained hinge,
/// traversal misses a face, or the resulting counts change.
inline std::array<std::uint8_t, face_count>
make_face_groups()
{
  const myriahedral_detail::tree_adjacency tree
    = myriahedral_detail::make_tree_adjacency();
  for (const hinge_cut edge : group_boundary_hinges)
    if (!contains_edge(tree, edge))
      throw std::logic_error(
        "Myriahedral semantic slice boundary is not a tree hinge");

  std::array<std::uint8_t, face_count> result {};
  std::array<std::uint16_t, face_count> stack {};
  std::size_t stack_size = 0;
  result[myriahedral_detail::tree_root] = 2;
  stack[stack_size++] = myriahedral_detail::tree_root;
  while (stack_size != 0)
    {
      const std::size_t current = stack[--stack_size];
      for (std::size_t index = 0; index < tree.degree[current]; ++index)
        {
          const std::size_t neighbor = tree.neighbors[current][index];
          if (result[neighbor] != 0)
            continue;
          result[neighbor] = is_group_boundary(current, neighbor)
                               ? static_cast<std::uint8_t>(3 - result[current])
                               : result[current];
          stack[stack_size++] = static_cast<std::uint16_t>(neighbor);
        }
    }

  std::array<std::size_t, 2> counts {};
  for (const std::uint8_t group : result)
    {
      if (group < 1 || group > 2)
        throw std::logic_error(
          "Myriahedral semantic slice traversal missed a face");
      ++counts[group - 1];
    }
  if (counts != expected_group_face_counts)
    throw std::logic_error(
      "Myriahedral semantic slice groups have unexpected face counts");
  return result;
}

/// Project one reference-layout face triangle onto a complete carrier.
/// @param face_index Terminal face index in `[0, 5120)`.
/// @param carrier Complete valid 16:9 carrier.
/// @return Three screen-oriented carrier coordinates.
inline svg::vrange
projected_face_triangle(const std::size_t face_index, const frame& carrier)
{
  const auto& projection = myriahedral_detail::layout();
  const auto& face = projection.planar[face_index];
  svg::vrange result;
  result.reserve(3);
  for (const myriahedral_detail::point_2d raw : face)
    {
      const myriahedral_detail::point_2d normalized
        = myriahedral_detail::normalize_planar_point(projection, raw);
      result.emplace_back(normalized.x * carrier.width(),
                          normalized.y * carrier.height());
    }
  return result;
}

/// Find tight carrier bounds around a nonempty set of projected triangles.
/// @param triangles Three-point carrier-space face paths.
/// @return Tight axis-aligned carrier-coordinate bounds.
/// @throws std::invalid_argument if the collection is empty.
/// @throws std::logic_error if a path is not triangular or bounds are invalid.
inline projected_view
bounding_view(const std::vector<svg::vrange>& triangles)
{
  if (triangles.empty())
    throw std::invalid_argument(
      "Myriahedral slice requires at least one face triangle");
  double minimum_x = std::numeric_limits<double>::infinity();
  double minimum_y = std::numeric_limits<double>::infinity();
  double maximum_x = -std::numeric_limits<double>::infinity();
  double maximum_y = -std::numeric_limits<double>::infinity();
  for (const svg::vrange& triangle : triangles)
    {
      if (triangle.size() != 3)
        throw std::logic_error(
          "Myriahedral slice face mask is not triangular");
      for (const auto [x, y] : triangle)
        {
          minimum_x = std::min(minimum_x, x);
          minimum_y = std::min(minimum_y, y);
          maximum_x = std::max(maximum_x, x);
          maximum_y = std::max(maximum_y, y);
        }
    }
  const projected_view result {
    minimum_x, minimum_y, maximum_x - minimum_x, maximum_y - minimum_y,
  };
  if (!std::isfinite(result.x) || !std::isfinite(result.y)
      || !std::isfinite(result.width) || !std::isfinite(result.height)
      || result.width <= 0 || result.height <= 0)
    throw std::logic_error("Myriahedral slice has invalid projected bounds");
  return result;
}

/// Construct the local frame implied by a carrier-coordinate viewport.
/// @param view Tight source rectangle on the complete carrier.
/// @return Arbitrary-ratio frame with inverse carrier-origin offsets.
inline frame
make_output_frame(const projected_view view)
{ return {view.width, view.height, -view.x, -view.y}; }

/// Validate descriptor geometry and face-mask invariants.
/// @param slice Descriptor to validate.
/// @param carrier Complete valid 16:9 carrier.
/// @throws std::runtime_error if metadata, bounds, frame offsets, or triangle
/// containment are inconsistent.
inline void
validate_slice(const slice_descriptor& slice, const frame& carrier)
{
  constexpr double tolerance = 1e-8;
  const projected_view view = slice.source_view;
  if (slice.number < 1 || slice.number > 2
      || slice.selected_faces
           != expected_group_face_counts[static_cast<std::size_t>(
             slice.number - 1)]
      || slice.clip_triangles.size() != slice.selected_faces)
    throw std::runtime_error(
      "Myriahedral slice has inconsistent group metadata");
  if (view.x < -tolerance || view.y < -tolerance
      || view.width <= 0 || view.height <= 0
      || view.x + view.width > carrier.width() + tolerance
      || view.y + view.height > carrier.height() + tolerance)
    throw std::runtime_error(
      "Myriahedral slice viewport lies outside its projection carrier");
  if (std::abs(slice.output_frame.width() - view.width) > tolerance
      || std::abs(slice.output_frame.height() - view.height) > tolerance
      || std::abs(slice.output_frame.moriginx + view.x) > tolerance
      || std::abs(slice.output_frame.moriginy + view.y) > tolerance)
    throw std::runtime_error(
      "Myriahedral slice output frame does not match its source viewport");
  for (const svg::vrange& triangle : slice.clip_triangles)
    {
      if (triangle.size() != 3)
        throw std::runtime_error(
          "Myriahedral slice mask contains a non-triangular face");
      for (const auto [x, y] : triangle)
        if (x < view.x - tolerance || x > view.x + view.width + tolerance
            || y < view.y - tolerance
            || y > view.y + view.height + tolerance)
          throw std::runtime_error(
            "Myriahedral slice face lies outside its viewport");
    }
}

/// Build both requested complementary face groups on a valid carrier.
/// @param carrier Complete Myriahedral carrier; normally 44 by 24.75.
/// @return Group 1 and group 2 descriptors in that order.
/// @throws std::invalid_argument if @p carrier is invalid.
/// @throws std::logic_error if the configured partition is inconsistent.
inline std::array<slice_descriptor, 2>
make_group_slices(const frame& carrier)
{
  require_valid_carrier(carrier);
  const auto groups = make_face_groups();
  std::array<std::vector<svg::vrange>, 2> triangles;
  triangles[0].reserve(expected_group_face_counts[0]);
  triangles[1].reserve(expected_group_face_counts[1]);
  for (std::size_t face = 0; face < face_count; ++face)
    triangles[groups[face] - 1].push_back(
      projected_face_triangle(face, carrier));

  const projected_view first_view = bounding_view(triangles[0]);
  const projected_view second_view = bounding_view(triangles[1]);
  std::array<slice_descriptor, 2> result {
    slice_descriptor {
      1, "named-land-group",
      "North America, South America, Antarctica, Greenland, and Iceland",
      make_output_frame(first_view), first_view,
      expected_group_face_counts[0], std::move(triangles[0]),
    },
    slice_descriptor {
      2, "remainder", "all remaining land and ocean faces",
      make_output_frame(second_view), second_view,
      expected_group_face_counts[1], std::move(triangles[1]),
    },
  };
  for (const slice_descriptor& slice : result)
    validate_slice(slice, carrier);
  return result;
}

/// Build the stable basename for one generated water slice.
/// @param slice Descriptor whose number determines the name.
/// @return Basename such as `water-myriahedral-adhoc-slice-1`.
inline std::string
water_slice_basename(const slice_descriptor& slice)
{
  return "water-myriahedral-adhoc-slice-"
         + std::to_string(slice.number);
}

/// Serialize a source viewport as an SVG viewBox.
/// @param view Carrier-coordinate rectangle.
/// @return Four space-separated numbers: x, y, width, and height.
inline std::string
view_box(const projected_view view)
{
  return format_number(view.x) + ' ' + format_number(view.y) + ' '
         + format_number(view.width) + ' ' + format_number(view.height);
}

/// Serialize all terminal triangles as one multi-subpath clip geometry.
/// @param triangles Three-point carrier-space face paths.
/// @return SVG path data with one closed subpath per terminal face.
inline std::string
clip_path_data(const std::vector<svg::vrange>& triangles)
{
  std::string result;
  result.reserve(triangles.size() * 96);
  for (const svg::vrange& triangle : triangles)
    {
      result += svg::make_path_data_from_points(triangle);
      result += "Z ";
    }
  return result;
}

/// Write one lightweight SVG wrapper around the master water projection.
/// @param output Destination slice SVG.
/// @param source_svg Complete reference Myriahedral water SVG.
/// @param source_fragment Root id inside @p source_svg.
/// @param slice Valid exact-face group descriptor.
/// @param carrier Complete valid 16:9 carrier.
/// @throws std::runtime_error if validation, source lookup, directory
/// creation, or output fails.
inline void
write_slice_svg(const std::filesystem::path& output,
                const std::filesystem::path& source_svg,
                const std::string_view source_fragment,
                const slice_descriptor& slice,
                const frame& carrier)
{
  require_valid_carrier(carrier);
  validate_slice(slice, carrier);
  if (!std::filesystem::is_regular_file(source_svg))
    throw std::runtime_error(
      "missing Myriahedral source SVG: " + source_svg.string());
  if (!output.parent_path().empty())
    std::filesystem::create_directories(output.parent_path());
  std::ofstream stream(output);
  if (!stream.good())
    throw std::runtime_error(
      "could not create Myriahedral slice SVG: " + output.string());

  const std::string id = output.stem().string();
  const std::string source_reference = xml_escape(
    source_svg.generic_string() + '#' + std::string(source_fragment));
  const std::string box = view_box(slice.source_view);
  const std::string width = format_number(slice.output_frame.width());
  const std::string height = format_number(slice.output_frame.height());
  const std::string unit = svg::to_string(svg::unit::inch);
  const std::string clip_id = id + "-face-clip";

  stream
    << "<svg xml:space=\"preserve\"\n"
    << "     xmlns=\"http://www.w3.org/2000/svg\"\n"
    << "     xmlns:xlink=\"http://www.w3.org/1999/xlink\"\n"
    << "     id=\"" << xml_escape(id) << "\" x=\"0" << unit
    << "\" y=\"0" << unit << "\"\n"
    << "     width=\"" << width << unit << "\" height=\"" << height
    << unit << "\"\n"
    << "     viewBox=\"" << box << "\" enable-background=\"new "
    << box << "\" overflow=\"hidden\" role=\"img\"\n"
    << "     data-slice-style=\"myriahedral-face-groups\"\n"
    << "     data-slice-group=\"" << slice.number << "\"\n"
    << "     data-slice-name=\"" << xml_escape(slice.name) << "\"\n"
    << "     data-face-count=\"" << slice.selected_faces << "\">\n"
    << "<title>Myriahedral ad-hoc face group " << slice.number
    << "</title>\n"
    << "<desc>Unscaled terminal-face mask from a "
    << format_number(carrier.width()) << " by "
    << format_number(carrier.height()) << " Myriahedral water carrier: "
    << xml_escape(slice.contents) << ".</desc>\n"
    << "<defs>\n"
    << "<clipPath id=\"" << xml_escape(clip_id)
    << "\" clipPathUnits=\"userSpaceOnUse\">\n"
    << "<path d=\"" << clip_path_data(slice.clip_triangles) << "\" />\n"
    << "</clipPath>\n"
    << "</defs>\n"
    << "<g id=\"" << xml_escape(id)
    << "-content\" clip-path=\"url(#" << xml_escape(clip_id)
    << ")\">\n"
    << "<use id=\"" << xml_escape(id) << "-source\" href=\""
    << source_reference << "\" xlink:href=\"" << source_reference
    << "\" x=\"0\" y=\"0\" width=\""
    << format_number(carrier.width()) << "\" height=\""
    << format_number(carrier.height()) << "\" />\n"
    << "</g>\n"
    << "</svg>\n";
  stream.close();
  if (!stream)
    throw std::runtime_error(
      "failed while writing Myriahedral slice SVG: " + output.string());
}

/// Read a generated text file completely.
/// @param path File to read.
/// @return Complete file contents.
/// @throws std::runtime_error if the file cannot be opened.
inline std::string
read_text(const std::filesystem::path& path)
{
  std::ifstream stream(path);
  if (!stream.good())
    throw std::runtime_error("could not read generated SVG: " + path.string());
  return {std::istreambuf_iterator<char>(stream),
          std::istreambuf_iterator<char>()};
}

/// Verify the structural invariants of one generated slice wrapper.
/// @param output Generated SVG to inspect.
/// @param source_svg Expected complete water SVG reference.
/// @param source_fragment Expected root id within @p source_svg.
/// @param slice Descriptor used to generate the wrapper.
/// @param carrier Complete valid 16:9 carrier.
/// @throws std::runtime_error on an incorrect viewport, physical size,
/// source reference, mask metadata, or unexpected scale transform.
inline void
verify_slice_svg(const std::filesystem::path& output,
                 const std::filesystem::path& source_svg,
                 const std::string_view source_fragment,
                 const slice_descriptor& slice,
                 const frame& carrier)
{
  const std::string generated = read_text(output);
  const std::string reference = source_svg.generic_string() + '#'
                                + std::string(source_fragment);
  if (generated.find("viewBox=\"" + view_box(slice.source_view) + "\"")
        == std::string::npos)
    throw std::runtime_error(
      "generated Myriahedral slice has the wrong viewBox: "
      + output.string());
  const std::string unit = svg::to_string(svg::unit::inch);
  const std::string physical_size
    = "width=\"" + format_number(slice.output_frame.width()) + unit
      + "\" height=\"" + format_number(slice.output_frame.height()) + unit
      + "\"";
  if (generated.find(physical_size) == std::string::npos)
    throw std::runtime_error(
      "generated Myriahedral slice lacks physical dimensions: "
      + output.string());
  if (generated.find("href=\"" + reference + "\"") == std::string::npos)
    throw std::runtime_error(
      "generated Myriahedral slice does not reference its source: "
      + output.string());
  const std::string source_viewport
    = "x=\"0\" y=\"0\" width=\"" + format_number(carrier.width())
      + "\" height=\"" + format_number(carrier.height()) + "\"";
  if (generated.find(source_viewport) == std::string::npos
      || generated.find("<clipPath ") == std::string::npos
      || generated.find("data-slice-name=\""
                        + xml_escape(slice.name) + "\"")
           == std::string::npos
      || generated.find("data-face-count=\""
                        + std::to_string(slice.selected_faces) + "\"")
           == std::string::npos)
    throw std::runtime_error(
      "generated Myriahedral slice has incomplete mask metadata: "
      + output.string());
  if (generated.find("scale(") != std::string::npos)
    throw std::runtime_error(
      "generated Myriahedral slice unexpectedly scales its source: "
      + output.string());
}

} // namespace a60::carto::myriahedral_slicing

#endif

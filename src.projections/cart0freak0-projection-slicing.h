// Projection-neutral slice descriptors for finite map carriers.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_PROJECTION_SLICING_H
#define CART0FREAK0_PROJECTION_SLICING_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "cart0freak0-projection-runtime.h"

namespace cart0freak0::projection_runtime {

/// The four intentionally distinct operations exposed as browser slices.
enum class slice_kind
{
  carrier_viewport,
  native_cell_mask,
  geographic_preclip,
  planar_tile,
};

/// Axis-aligned viewport measured in the full projected carrier coordinates.
struct projected_view
{
  double x;
  double y;
  double width;
  double height;
};

/// Ordered WGS 84 longitude/latitude bounds used for source preclipping.
struct geographic_bounds
{
  double west;
  double south;
  double east;
  double north;
};

/// Self-contained slice metadata in full-carrier coordinates.
struct slice_descriptor
{
  std::string id;
  std::string name;
  std::string projection;
  std::string layout;
  slice_kind kind = slice_kind::carrier_viewport;
  projected_view source_view {};
  double padding = 0;
  std::uint32_t components = 1;
  std::vector<std::uint32_t> selected_cells;
  std::optional<geographic_bounds> geographic;
  std::vector<projected_path> clip_paths;
};

inline constexpr std::string_view
slice_kind_name(const slice_kind kind)
{
  switch (kind)
    {
    case slice_kind::carrier_viewport: return "carrier-viewport";
    case slice_kind::native_cell_mask: return "native-cell-mask";
    case slice_kind::geographic_preclip: return "geographic-preclip";
    case slice_kind::planar_tile: return "planar-tile";
    }
  return "unknown";
}

inline bool
valid_view(const projection_context& context, const projected_view view)
{
  constexpr double tolerance = 1e-8;
  return std::isfinite(view.x) && std::isfinite(view.y)
         && std::isfinite(view.width) && std::isfinite(view.height)
         && view.width > 0 && view.height > 0
         && view.x >= -tolerance && view.y >= -tolerance
         && view.x + view.width <= context.map_frame.width() + tolerance
         && view.y + view.height <= context.map_frame.height() + tolerance;
}

inline projected_view
full_carrier_view(const projection_context& context)
{
  return {0, 0, context.map_frame.width(), context.map_frame.height()};
}

inline std::string
projection_layout_name(const projection_context& context)
{
  if (context.spec.kind != projection_kind::myriahedral
      || context.spec.myriahedral_perspective
           == myriahedral_generation::perspective::reference)
    return "reference";
  const std::string_view argument = myriahedral_generation::metadata(
    context.spec.myriahedral_perspective).argument;
  constexpr std::string_view prefix = "myriahedral-";
  return argument.starts_with(prefix)
    ? std::string(argument.substr(prefix.size())) : std::string(argument);
}

inline projected_view
bounding_view(const std::vector<projected_path>& paths)
{
  double minimum_x = std::numeric_limits<double>::infinity();
  double minimum_y = std::numeric_limits<double>::infinity();
  double maximum_x = -std::numeric_limits<double>::infinity();
  double maximum_y = -std::numeric_limits<double>::infinity();
  std::size_t points = 0;
  for (const projected_path& path : paths)
    for (const auto [x, y] : path)
      {
        minimum_x = std::min(minimum_x, x);
        minimum_y = std::min(minimum_y, y);
        maximum_x = std::max(maximum_x, x);
        maximum_y = std::max(maximum_y, y);
        ++points;
      }
  if (points == 0 || maximum_x <= minimum_x || maximum_y <= minimum_y)
    throw std::invalid_argument("slice mask has no finite two-dimensional extent");
  return {minimum_x, minimum_y,
          maximum_x - minimum_x, maximum_y - minimum_y};
}

inline projected_view
pad_view(const projection_context& context, projected_view view,
         const double padding)
{
  if (!std::isfinite(padding) || padding < 0)
    throw std::invalid_argument("slice padding must be finite and non-negative");
  const double right = std::min(
    context.map_frame.width(), view.x + view.width + padding);
  const double bottom = std::min(
    context.map_frame.height(), view.y + view.height + padding);
  view.x = std::max(0.0, view.x - padding);
  view.y = std::max(0.0, view.y - padding);
  view.width = right - view.x;
  view.height = bottom - view.y;
  return view;
}

inline slice_descriptor
make_full_slice(const projection_context& context)
{
  return {"full", "Complete finite carrier", std::string(context.spec.argument),
          projection_layout_name(context), slice_kind::carrier_viewport,
          full_carrier_view(context), 0, 1, {}, std::nullopt, {}};
}

inline slice_descriptor
make_viewport_slice(const projection_context& context, std::string id,
                    const projected_view view,
                    const slice_kind kind = slice_kind::carrier_viewport)
{
  if (kind != slice_kind::carrier_viewport
      && kind != slice_kind::planar_tile)
    throw std::invalid_argument(
      "a viewport descriptor must be carrier-viewport or planar-tile");
  if (!valid_view(context, view))
    throw std::invalid_argument("slice viewport lies outside the full carrier");
  return {std::move(id), kind == slice_kind::planar_tile
                          ? "Planar delivery tile" : "Carrier viewport",
          std::string(context.spec.argument), projection_layout_name(context),
          kind, view, 0, 1, {}, std::nullopt, {}};
}

inline slice_descriptor
make_geographic_slice(const projection_context& context, std::string id,
                      const geographic_bounds bounds)
{
  if (!std::isfinite(bounds.west) || !std::isfinite(bounds.south)
      || !std::isfinite(bounds.east) || !std::isfinite(bounds.north)
      || bounds.west < -180 || bounds.east > 180
      || bounds.south < -90 || bounds.north > 90
      || bounds.west >= bounds.east || bounds.south >= bounds.north)
    throw std::invalid_argument(
      "geographic slice must be an ordered WGS 84 bounding box");
  return {std::move(id), "Geographic source preclip",
          std::string(context.spec.argument), projection_layout_name(context),
          slice_kind::geographic_preclip, full_carrier_view(context), 0, 1,
          {}, bounds, {}};
}

inline double
canonical_longitude(double longitude)
{
  while (longitude > 180)
    longitude -= 360;
  while (longitude < -180)
    longitude += 360;
  return longitude;
}

inline void
append_sampled_edge(projected_path& result,
                    const projection_context& context,
                    const geographic_point start,
                    const geographic_point finish,
                    const double step = 2.5)
{
  const double span = std::max(std::abs(finish.latitude - start.latitude),
                               std::abs(finish.longitude - start.longitude));
  const int segments = std::max(1, static_cast<int>(std::ceil(span / step)));
  for (int segment = 0; segment < segments; ++segment)
    {
      const double fraction = static_cast<double>(segment) / segments;
      geographic_point point = interpolate(start, finish, fraction);
      point.longitude = canonical_longitude(point.longitude);
      append_unique(result, project_point(context, point));
    }
}

/// Longitude interval and north/south face identifiers for one Cahill-Keyes
/// source sector used while constructing runtime slice outlines.
struct ck_sector
{
  double west;
  double east;
  std::uint32_t north_octant;
  std::uint32_t south_octant;
  std::uint32_t north_cell;
  std::uint32_t south_cell;
};

inline constexpr std::array ck_sectors {
  ck_sector {159, 249, 1, 6, 0, 4},
  ck_sector {-111, -21, 2, 7, 1, 5},
  ck_sector {-21, 69, 3, 8, 2, 6},
  ck_sector {69, 159, 4, 5, 3, 7},
};

inline projected_path
make_ck_octant_outline(const projection_context& context,
                       const ck_sector sector, const bool north)
{
  constexpr double epsilon = 1e-7;
  const double west = sector.west + epsilon;
  const double east = sector.east - epsilon;
  const double pole = north ? 90 : -90;
  const double near_pole = north ? 90 - epsilon : -90 + epsilon;
  const double center = (sector.west + sector.east) / 2;
  projected_path result;
  append_sampled_edge(result, context, {0, west}, {0, east});
  append_sampled_edge(result, context, {0, east}, {near_pole, east});
  append_unique(result, project_point(
    context, {pole, canonical_longitude(center)}));
  append_sampled_edge(result, context, {near_pole, west}, {0, west});
  return result;
}

inline std::vector<slice_descriptor>
make_cahill_keyes_slices(const projection_context& context)
{
  if (context.spec.kind != projection_kind::cahill_keyes)
    throw std::invalid_argument(
      "Cahill-Keyes built-in slices require a Cahill-Keyes carrier");
  std::vector<slice_descriptor> result;
  result.reserve(12);
  const double strip_width = context.map_frame.width() / 4;
  for (std::size_t index = 0; index < ck_sectors.size(); ++index)
    {
      result.push_back({
        "ck-strip-" + std::to_string(index + 1),
        "Cahill-Keyes full-height strip " + std::to_string(index + 1),
        "cahill-keyes", "reference", slice_kind::carrier_viewport,
        {strip_width * index, 0, strip_width, context.map_frame.height()},
        0, 1,
        {ck_sectors[index].north_cell, ck_sectors[index].south_cell},
        std::nullopt, {},
      });
    }
  for (const ck_sector sector : ck_sectors)
    for (const bool north : {true, false})
      {
        projected_path outline = make_ck_octant_outline(
          context, sector, north);
        const std::uint32_t octant
          = north ? sector.north_octant : sector.south_octant;
        const std::uint32_t cell
          = north ? sector.north_cell : sector.south_cell;
        std::vector<projected_path> clips;
        clips.push_back(std::move(outline));
        result.push_back({
          "ck-octant-" + std::to_string(octant),
          "Cahill-Keyes exact octant " + std::to_string(octant),
          "cahill-keyes", "reference", slice_kind::native_cell_mask,
          bounding_view(clips), 0, 1, {cell}, std::nullopt,
          std::move(clips),
        });
      }
  std::sort(result.begin() + 4, result.end(),
            [](const slice_descriptor& left,
               const slice_descriptor& right) {
              return left.id < right.id;
            });
  return result;
}

/// Vertex pair whose shared hinge separates the two Myriahedral face groups.
struct myria_hinge_cut
{
  std::uint16_t first;
  std::uint16_t second;
};

inline constexpr std::array myria_group_boundary_hinges {
  myria_hinge_cut {51, 273},
  myria_hinge_cut {3929, 3924},
  myria_hinge_cut {2026, 2025},
  myria_hinge_cut {3601, 3602},
  myria_hinge_cut {264, 259},
};

inline constexpr std::array<std::size_t, 2> myria_group_counts {2722, 2398};

inline constexpr bool
is_myria_group_boundary(const std::size_t left, const std::size_t right)
{
  for (const myria_hinge_cut edge : myria_group_boundary_hinges)
    if ((edge.first == left && edge.second == right)
        || (edge.first == right && edge.second == left))
      return true;
  return false;
}

inline std::array<std::uint8_t,
                  a60::carto::myriahedral_detail::face_count>
make_myria_face_groups()
{
  using namespace a60::carto::myriahedral_detail;
  const tree_adjacency tree = make_tree_adjacency();
  std::array<std::uint8_t, face_count> result {};
  std::array<std::uint16_t, face_count> stack {};
  std::size_t stack_size = 0;
  result[mst_root] = 2;
  stack[stack_size++] = mst_root;
  while (stack_size != 0)
    {
      const std::size_t current = stack[--stack_size];
      for (std::size_t index = 0; index < tree.degree[current]; ++index)
        {
          const std::size_t neighbor = tree.neighbors[current][index];
          if (result[neighbor] != 0)
            continue;
          result[neighbor] = is_myria_group_boundary(current, neighbor)
                               ? static_cast<std::uint8_t>(3 - result[current])
                               : result[current];
          stack[stack_size++] = static_cast<std::uint16_t>(neighbor);
        }
    }
  std::array<std::size_t, 2> counts {};
  for (const std::uint8_t group : result)
    {
      if (group < 1 || group > 2)
        throw std::logic_error("Myriahedral slice traversal missed a face");
      ++counts[group - 1];
    }
  if (counts != myria_group_counts)
    throw std::logic_error("Myriahedral slice face counts changed");
  return result;
}

inline projected_path
myria_face_triangle(const projection_context& context,
                    const std::size_t face)
{
  using namespace a60::carto::myriahedral_detail;
  const auto& projection = std::get<myriaproj>(context.projection).layout();
  projected_path result;
  result.reserve(3);
  for (const point_2d raw : projection.planar.at(face))
    {
      const point_2d normalized = normalize_planar_point(projection, raw);
      result.emplace_back(normalized.x * context.map_frame.width(),
                          normalized.y * context.map_frame.height());
    }
  return result;
}

inline std::vector<slice_descriptor>
make_myriahedral_slices(const projection_context& context)
{
  if (context.spec.kind != projection_kind::myriahedral
      || context.spec.myriahedral_perspective
           != myriahedral_generation::perspective::reference)
    throw std::invalid_argument(
      "semantic Myriahedral slices require the reference layout");
  const auto groups = make_myria_face_groups();
  std::array<std::vector<std::uint32_t>, 2> cells;
  std::array<std::vector<projected_path>, 2> clips;
  cells[0].reserve(myria_group_counts[0]);
  cells[1].reserve(myria_group_counts[1]);
  clips[0].reserve(myria_group_counts[0]);
  clips[1].reserve(myria_group_counts[1]);
  for (std::size_t face = 0; face < groups.size(); ++face)
    {
      const std::size_t group = groups[face] - 1;
      cells[group].push_back(static_cast<std::uint32_t>(face));
      clips[group].push_back(myria_face_triangle(context, face));
    }
  std::vector<slice_descriptor> result;
  result.reserve(2);
  result.push_back({
    "myria-group-1",
    "North and South America, Antarctica, Greenland, and Iceland",
    "myriahedral", "reference", slice_kind::native_cell_mask,
    bounding_view(clips[0]), 0, 1, std::move(cells[0]), std::nullopt,
    std::move(clips[0]),
  });
  result.push_back({
    "myria-group-2", "All remaining land and ocean faces",
    "myriahedral", "reference", slice_kind::native_cell_mask,
    bounding_view(clips[1]), 0, 1, std::move(cells[1]), std::nullopt,
    std::move(clips[1]),
  });
  return result;
}

inline std::vector<slice_descriptor>
list_slices(const projection_context& context)
{
  std::vector<slice_descriptor> result;
  result.push_back(make_full_slice(context));
  if (context.spec.kind == projection_kind::cahill_keyes)
    {
      std::vector<slice_descriptor> built_in = make_cahill_keyes_slices(context);
      result.insert(result.end(), std::make_move_iterator(built_in.begin()),
                    std::make_move_iterator(built_in.end()));
    }
  else if (context.spec.kind == projection_kind::myriahedral
           && context.spec.myriahedral_perspective
                == myriahedral_generation::perspective::reference)
    {
      std::vector<slice_descriptor> built_in = make_myriahedral_slices(context);
      result.insert(result.end(), std::make_move_iterator(built_in.begin()),
                    std::make_move_iterator(built_in.end()));
    }
  return result;
}

inline slice_descriptor
find_slice(const projection_context& context, const std::string_view id)
{
  std::vector<slice_descriptor> slices = list_slices(context);
  for (slice_descriptor& slice : slices)
    if (slice.id == id)
      return std::move(slice);
  throw std::invalid_argument(
    "unknown slice '" + std::string(id) + "' for projection '"
    + std::string(context.spec.argument) + "'");
}

inline bool
slice_selects_cell(const slice_descriptor* slice, const std::uint32_t cell)
{
  if (slice == nullptr || slice->kind != slice_kind::native_cell_mask)
    return true;
  return std::find(slice->selected_cells.begin(),
                   slice->selected_cells.end(), cell)
         != slice->selected_cells.end();
}

} // namespace cart0freak0::projection_runtime

#endif

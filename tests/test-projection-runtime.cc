#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <set>
#include <string_view>

#include "cart0freak0-projection-geometry.h"

namespace runtime = cart0freak0::projection_runtime;

namespace {

runtime::geometry_input
sample_geometry()
{
  runtime::geometry_input input;
  input.coordinates = {
    {37.7749, -122.4194},
    {35, 150}, {45, -160}, {55, 170},
    {-10, -10}, {-10, 10}, {10, 10}, {10, -10},
    {-5, -5}, {5, -5}, {5, 5}, {-5, 5},
    {25, 75}, {25, 85}, {35, 85}, {35, 75},
  };
  input.part_offsets = {0, 1, 4, 8, 12, 16};
  input.part_types = {
    runtime::geometry_part_type::point,
    runtime::geometry_part_type::line,
    runtime::geometry_part_type::ring,
    runtime::geometry_part_type::ring,
    runtime::geometry_part_type::ring,
  };
  input.feature_ids = {1, 2, 10, 10, 11};
  input.ring_roles = {
    runtime::ring_role::none,
    runtime::ring_role::none,
    runtime::ring_role::exterior,
    runtime::ring_role::hole,
    runtime::ring_role::exterior,
  };
  return input;
}

void
check_buffer(const runtime::projection_context& context,
             const runtime::geometry_command_buffer& buffer)
{
  assert(buffer.part_offsets.size() == buffer.part_types.size() + 1);
  assert(buffer.part_offsets.back() * 2 == buffer.coordinates.size());
  assert(buffer.part_types.size() == buffer.feature_ids.size());
  assert(buffer.part_types.size() == buffer.native_cells.size());
  assert(buffer.part_types.size() == buffer.ring_roles.size());
  assert(buffer.part_types.size() == buffer.closed.size());
  assert(buffer.width > 0 && buffer.height > 0);
  for (const double coordinate : buffer.coordinates)
    assert(std::isfinite(coordinate));
  for (std::size_t index = 0; index < buffer.coordinates.size(); index += 2)
    {
      assert(buffer.coordinates[index] >= -1e-7);
      assert(buffer.coordinates[index] <= buffer.width + 1e-7);
      assert(buffer.coordinates[index + 1] >= -1e-7);
      assert(buffer.coordinates[index + 1] <= buffer.height + 1e-7);
    }
  for (const std::uint32_t cell : buffer.native_cells)
    assert(cell < context.spec.native_cell_count
           || cell == std::numeric_limits<std::uint32_t>::max());
  assert(buffer.diagnostics.output_parts == buffer.part_types.size());
  assert(buffer.diagnostics.output_vertices == buffer.coordinates.size() / 2);
}

} // namespace

int
main()
{
  static_assert(runtime::abi_version == 1);
  assert(runtime::reference_projection_ids.size() == 6);
  std::set<std::string_view> families;
  for (const runtime::projection_spec& spec : runtime::projection_specs)
    families.insert(runtime::projection_kind_name(spec.kind));
  assert(families.size() == 6);

  const runtime::geometry_input input = sample_geometry();
  for (const std::string_view id : runtime::reference_projection_ids)
    {
      const runtime::projection_spec& spec = runtime::find_projection_spec(id);
      const double width = spec.width * 10;
      const double height = width / (spec.width / spec.height);
      const runtime::projection_context context(
        spec, a60::carto::frame(width, height));
      const auto [x, y] = runtime::project_point(
        context, {37.7749, -122.4194});
      assert(std::isfinite(x) && std::isfinite(y));
      assert(x >= 0 && x <= width && y >= 0 && y <= height);

      const runtime::geometry_command_buffer projected
        = runtime::project_geometry(context, input);
      check_buffer(context, projected);
      assert(projected.diagnostics.input_parts == 5);
      assert(projected.diagnostics.input_points == 16);
      assert(std::find(projected.feature_ids.begin(), projected.feature_ids.end(), 10)
             != projected.feature_ids.end());
      assert(std::find(projected.feature_ids.begin(), projected.feature_ids.end(), 11)
             != projected.feature_ids.end());
      assert(std::find(projected.ring_roles.begin(), projected.ring_roles.end(),
                       runtime::ring_role::exterior)
             != projected.ring_roles.end());
      assert(std::find(projected.ring_roles.begin(), projected.ring_roles.end(),
                       runtime::ring_role::hole)
             != projected.ring_roles.end());

      const runtime::geometry_command_buffer carrier
        = runtime::carrier_geometry(context);
      check_buffer(context, carrier);
      const std::size_t expected_faces
        = spec.kind == runtime::projection_kind::authagraph
            ? 1 : spec.native_cell_count;
      assert(carrier.part_types.size() == expected_faces);
      assert(std::all_of(carrier.closed.begin(), carrier.closed.end(),
                         [](const std::uint8_t closed) { return closed == 1; }));

      const runtime::projected_view tile {
        width / 4, height / 4, width / 2, height / 2,
      };
      runtime::geometry_options tile_options;
      tile_options.slice = runtime::make_viewport_slice(
        context, "test-tile", tile, runtime::slice_kind::planar_tile);
      const runtime::geometry_command_buffer tiled
        = runtime::project_geometry(context, input, tile_options);
      check_buffer(context, tiled);
      assert(std::abs(tiled.width - width / 2) < 1e-10);
      assert(std::abs(tiled.height - height / 2) < 1e-10);
      assert(std::abs(tiled.origin_x - width / 4) < 1e-10);
    }

  const runtime::projection_context ck(
    runtime::find_projection_spec("cahill-keyes"), a60::carto::frame(44, 22));
  const std::vector<runtime::slice_descriptor> ck_slices
    = runtime::list_slices(ck);
  assert(ck_slices.size() == 13);
  const runtime::slice_descriptor strip = runtime::find_slice(ck, "ck-strip-2");
  assert(strip.kind == runtime::slice_kind::carrier_viewport);
  assert(strip.source_view.x == 11 && strip.source_view.width == 11);
  const runtime::slice_descriptor octant
    = runtime::find_slice(ck, "ck-octant-7");
  assert(octant.kind == runtime::slice_kind::native_cell_mask);
  assert(octant.selected_cells == std::vector<std::uint32_t> {5});
  assert(octant.clip_paths.size() == 1);

  const runtime::projection_context myria(
    runtime::find_projection_spec("myriahedral"),
    a60::carto::frame(44, 24.75));
  const std::vector<runtime::slice_descriptor> myria_slices
    = runtime::list_slices(myria);
  assert(myria_slices.size() == 3);
  assert(myria_slices[1].selected_cells.size() == 2722);
  assert(myria_slices[2].selected_cells.size() == 2398);
  runtime::geometry_options group_options;
  group_options.slice = runtime::find_slice(myria, "myria-group-1");
  const runtime::geometry_command_buffer group_carrier
    = runtime::carrier_geometry(myria, group_options.slice);
  assert(group_carrier.part_types.size() == 2722);
  assert(std::all_of(group_carrier.native_cells.begin(),
                     group_carrier.native_cells.end(),
                     [&](const std::uint32_t cell) {
                       return runtime::slice_selects_cell(
                         &*group_options.slice, cell);
                     }));

  runtime::geometry_input point_input;
  point_input.coordinates = {{0, 0}, {60, 120}};
  point_input.part_offsets = {0, 2};
  point_input.part_types = {runtime::geometry_part_type::point};
  runtime::geometry_options geographic_options;
  geographic_options.slice = runtime::make_geographic_slice(
    ck, "equatorial-window", {-10, -10, 10, 10});
  const runtime::geometry_command_buffer geographic
    = runtime::project_geometry(ck, point_input, geographic_options);
  assert(geographic.coordinates.size() == 2);

  bool rejected = false;
  try
    {
      const runtime::projection_context invalid(
        runtime::find_projection_spec("dymaxion"),
        a60::carto::frame(44, 22));
      static_cast<void>(invalid);
    }
  catch (const std::invalid_argument&)
    { rejected = true; }
  assert(rejected);
}

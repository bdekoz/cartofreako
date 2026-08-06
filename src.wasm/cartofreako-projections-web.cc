#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <emscripten/bind.h>
#include <emscripten/val.h>

#include "cart0freak0-projection-geometry.h"

namespace {

namespace runtime = cart0freak0::projection_runtime;
using emscripten::val;

struct browser_projected_point
{
  double x;
  double y;
  std::uint32_t native_cell;
};

bool
has(const val& object, const char* property)
{
  return object.hasOwnProperty(property);
}

bool
is_nullish(const val& value)
{
  return value.isNull() || value.isUndefined();
}

template<typename Value>
val
typed_array(const char* constructor_name, const std::vector<Value>& source)
{
  val result = val::global(constructor_name).new_(source.size());
  for (std::size_t index = 0; index < source.size(); ++index)
    result.set(index, source[index]);
  return result;
}

template<typename Enum>
val
enum_array(const std::vector<Enum>& source)
{
  std::vector<std::uint8_t> values;
  values.reserve(source.size());
  for (const Enum value : source)
    values.push_back(static_cast<std::uint8_t>(value));
  return typed_array("Uint8Array", values);
}

std::vector<double>
read_doubles(const val& source, const char* name)
{
  if (is_nullish(source))
    return {};
  const std::size_t size = source["length"].as<std::size_t>();
  std::vector<double> result;
  result.reserve(size);
  for (std::size_t index = 0; index < size; ++index)
    {
      const double value = source[index].as<double>();
      if (!std::isfinite(value))
        throw std::invalid_argument(std::string(name) + " contains non-finite data");
      result.push_back(value);
    }
  return result;
}

std::vector<std::uint32_t>
read_uint32(const val& source, const char* name)
{
  if (is_nullish(source))
    return {};
  const std::size_t size = source["length"].as<std::size_t>();
  std::vector<std::uint32_t> result;
  result.reserve(size);
  for (std::size_t index = 0; index < size; ++index)
    {
      const double value = source[index].as<double>();
      if (!std::isfinite(value) || value < 0
          || value > std::numeric_limits<std::uint32_t>::max()
          || std::floor(value) != value)
        throw std::invalid_argument(std::string(name) + " contains an invalid integer");
      result.push_back(static_cast<std::uint32_t>(value));
    }
  return result;
}

std::vector<std::uint8_t>
read_uint8(const val& source, const char* name)
{
  const std::vector<std::uint32_t> values = read_uint32(source, name);
  std::vector<std::uint8_t> result;
  result.reserve(values.size());
  for (const std::uint32_t value : values)
    {
      if (value > std::numeric_limits<std::uint8_t>::max())
        throw std::invalid_argument(std::string(name) + " contains an invalid byte");
      result.push_back(static_cast<std::uint8_t>(value));
    }
  return result;
}

val
view_value(const runtime::projected_view view)
{
  val result = val::object();
  result.set("x", view.x);
  result.set("y", view.y);
  result.set("width", view.width);
  result.set("height", view.height);
  return result;
}

runtime::projected_view
read_view(const val& source)
{
  if (is_nullish(source) || source["length"].as<std::size_t>() != 4)
    throw std::invalid_argument(
      "slice view must be [x, y, width, height]");
  return {source[0].as<double>(), source[1].as<double>(),
          source[2].as<double>(), source[3].as<double>()};
}

val
slice_value(const runtime::slice_descriptor& slice,
            const bool include_clip_geometry)
{
  val result = val::object();
  result.set("id", slice.id);
  result.set("name", slice.name);
  result.set("projection", slice.projection);
  result.set("layout", slice.layout);
  result.set("kind", std::string(runtime::slice_kind_name(slice.kind)));
  result.set("sourceView", view_value(slice.source_view));
  result.set("outputFrame", view_value(
    {0, 0, slice.source_view.width, slice.source_view.height}));
  result.set("padding", slice.padding);
  result.set("components", slice.components);
  result.set("selectedCells", typed_array("Uint32Array", slice.selected_cells));
  if (slice.geographic)
    {
      val geographic = val::object();
      geographic.set("west", slice.geographic->west);
      geographic.set("south", slice.geographic->south);
      geographic.set("east", slice.geographic->east);
      geographic.set("north", slice.geographic->north);
      result.set("geographic", geographic);
    }
  else
    result.set("geographic", val::null());

  if (include_clip_geometry && !slice.clip_paths.empty())
    {
      std::vector<double> coordinates;
      std::vector<std::uint32_t> offsets {0};
      for (const runtime::projected_path& path : slice.clip_paths)
        {
          for (const auto [x, y] : path)
            {
              coordinates.push_back(x - slice.source_view.x);
              coordinates.push_back(y - slice.source_view.y);
            }
          offsets.push_back(static_cast<std::uint32_t>(coordinates.size() / 2));
        }
      val clip = val::object();
      clip.set("coordinates", typed_array("Float64Array", coordinates));
      clip.set("partOffsets", typed_array("Uint32Array", offsets));
      result.set("clip", clip);
    }
  return result;
}

val
diagnostics_value(const runtime::geometry_diagnostics& diagnostics)
{
  val result = val::object();
  result.set("inputPoints", diagnostics.input_points);
  result.set("inputParts", diagnostics.input_parts);
  result.set("outputVertices", diagnostics.output_vertices);
  result.set("outputParts", diagnostics.output_parts);
  result.set("sampledPoints", diagnostics.sampled_points);
  result.set("cellTransitions", diagnostics.cell_transitions);
  result.set("cuts", diagnostics.cuts);
  result.set("periodicWraps", diagnostics.periodic_wraps);
  result.set("fallbackSplits", diagnostics.fallback_splits);
  result.set("clippedParts", diagnostics.clipped_parts);
  result.set("droppedParts", diagnostics.dropped_parts);
  return result;
}

val
command_buffer_value(const runtime::geometry_command_buffer& buffer)
{
  val result = val::object();
  result.set("abiVersion", runtime::abi_version);
  result.set("coordinates", typed_array("Float64Array", buffer.coordinates));
  result.set("partOffsets", typed_array("Uint32Array", buffer.part_offsets));
  result.set("partTypes", enum_array(buffer.part_types));
  result.set("featureIds", typed_array("Uint32Array", buffer.feature_ids));
  result.set("nativeCells", typed_array("Uint32Array", buffer.native_cells));
  result.set("componentIds", typed_array("Uint32Array", buffer.component_ids));
  result.set("ringRoles", enum_array(buffer.ring_roles));
  result.set("closed", typed_array("Uint8Array", buffer.closed));
  val frame = val::object();
  frame.set("originX", buffer.origin_x);
  frame.set("originY", buffer.origin_y);
  frame.set("width", buffer.width);
  frame.set("height", buffer.height);
  result.set("frame", frame);
  result.set("diagnostics", diagnostics_value(buffer.diagnostics));
  return result;
}

std::string
license_notice(const runtime::projection_spec& spec)
{
  if (spec.kind == runtime::projection_kind::cahill_keyes
      || spec.kind == runtime::projection_kind::star_x)
    return "GPL-3.0-or-later; Cahill-Keyes forward construction derives "
           "from work by Mary Jo Graca and Gene Keyes, distributed for "
           "non-commercial use with attribution; contact Gene Keyes for "
           "commercial use.";
  return "GPL-3.0-or-later";
}

val
projection_descriptor(const runtime::projection_spec& spec)
{
  val result = val::object();
  result.set("id", std::string(spec.argument));
  result.set("family", std::string(runtime::projection_kind_name(spec.kind)));
  result.set("title", std::string(spec.title));
  result.set("nativeFrameRatio", spec.width / spec.height);
  val default_frame = val::object();
  default_frame.set("width", spec.width);
  default_frame.set("height", spec.height);
  result.set("defaultFrame", default_frame);
  result.set("nativeCellCount", spec.native_cell_count);
  result.set("topology", std::string(runtime::topology_kind_name(spec.topology)));
  result.set("inverseMode", "none");
  val capabilities = val::object();
  capabilities.set("points", true);
  capabilities.set("lines", true);
  capabilities.set("polygons", true);
  capabilities.set("sphere", true);
  capabilities.set("slices", true);
  capabilities.set("planarTiles", true);
  result.set("capabilities", capabilities);
  val license = val::object();
  license.set("spdx", "GPL-3.0-or-later");
  license.set("notice", license_notice(spec));
  result.set("license", license);
  return result;
}

val
projection_manifest()
{
  val result = val::array();
  std::size_t output = 0;
  for (const runtime::projection_spec& spec : runtime::projection_specs)
    result.set(output++, projection_descriptor(spec));
  return result;
}

val
license_manifest()
{
  val result = val::object();
  result.set("runtime", "GPL-3.0-or-later");
  result.set("source", "https://github.com/alpha60/cartofreako");
  result.set("cahillKeyes", license_notice(
    runtime::find_projection_spec("cahill-keyes")));
  result.set("naturalEarth", "Public domain; applies only when that optional data asset is used.");
  return result;
}

runtime::geometry_input
read_geometry_input(const val& coordinates_value,
                    const val& offsets_value,
                    const val& types_value,
                    const val& feature_ids_value,
                    const val& ring_roles_value)
{
  const std::vector<double> coordinates = read_doubles(
    coordinates_value, "coordinates");
  if (coordinates.size() % 2 != 0)
    throw std::invalid_argument(
      "coordinates must contain interleaved longitude/latitude pairs");
  runtime::geometry_input result;
  result.coordinates.reserve(coordinates.size() / 2);
  for (std::size_t index = 0; index < coordinates.size(); index += 2)
    result.coordinates.push_back({coordinates[index + 1], coordinates[index]});
  result.part_offsets = read_uint32(offsets_value, "partOffsets");
  for (const std::uint8_t type : read_uint8(types_value, "partTypes"))
    {
      if (type > static_cast<std::uint8_t>(runtime::geometry_part_type::ring))
        throw std::invalid_argument("partTypes contains an unknown geometry type");
      result.part_types.push_back(
        static_cast<runtime::geometry_part_type>(type));
    }
  result.feature_ids = read_uint32(feature_ids_value, "featureIds");
  for (const std::uint8_t role : read_uint8(ring_roles_value, "ringRoles"))
    {
      if (role > static_cast<std::uint8_t>(runtime::ring_role::hole))
        throw std::invalid_argument("ringRoles contains an unknown ring role");
      result.ring_roles.push_back(static_cast<runtime::ring_role>(role));
    }
  return result;
}

class browser_projection
{
  runtime::projection_context context;

  runtime::slice_descriptor
  read_slice(const val& source) const
  {
    if (source.typeOf().as<std::string>() == "string")
      return runtime::find_slice(context, source.as<std::string>());
    if (source.typeOf().as<std::string>() != "object" || source.isNull())
      throw std::invalid_argument("slice must be a built-in id or descriptor");
    if (has(source, "id") && !has(source, "kind"))
      return runtime::find_slice(context, source["id"].as<std::string>());
    if (!has(source, "kind"))
      throw std::invalid_argument("custom slice is missing kind");
    const std::string kind = source["kind"].as<std::string>();
    const std::string id = has(source, "id")
      ? source["id"].as<std::string>() : "custom";
    if (kind == "carrier-viewport" || kind == "planar-tile")
      return runtime::make_viewport_slice(
        context, id, read_view(source["view"]),
        kind == "planar-tile" ? runtime::slice_kind::planar_tile
                               : runtime::slice_kind::carrier_viewport);
    if (kind == "geographic-preclip")
      {
        const val bounds = source["bounds"];
        if (is_nullish(bounds) || bounds["length"].as<std::size_t>() != 4)
          throw std::invalid_argument(
            "geographic slice bounds must be [west, south, east, north]");
        return runtime::make_geographic_slice(
          context, id,
          {bounds[0].as<double>(), bounds[1].as<double>(),
           bounds[2].as<double>(), bounds[3].as<double>()});
      }
    if (kind == "native-cell-mask")
      {
        runtime::slice_descriptor result {
          id, "Custom native-cell mask", std::string(context.spec.argument),
          runtime::projection_layout_name(context),
          runtime::slice_kind::native_cell_mask,
          has(source, "view") ? read_view(source["view"])
                              : runtime::full_carrier_view(context),
          0, 1, read_uint32(source["selectedCells"], "selectedCells"),
          std::nullopt, {},
        };
        if (result.selected_cells.empty())
          throw std::invalid_argument(
            "native-cell mask must select at least one cell");
        for (const std::uint32_t cell : result.selected_cells)
          if (cell >= context.spec.native_cell_count)
            throw std::invalid_argument(
              "native-cell mask contains an out-of-range cell");
        if (!runtime::valid_view(context, result.source_view))
          throw std::invalid_argument(
            "native-cell mask view lies outside the carrier");
        return result;
      }
    throw std::invalid_argument("unknown slice kind '" + kind + "'");
  }

  runtime::geometry_options
  read_options(const val& source) const
  {
    runtime::geometry_options result;
    if (is_nullish(source))
      return result;
    if (has(source, "tolerancePx"))
      result.tolerance_pixels = source["tolerancePx"].as<double>();
    if (has(source, "maximumAngularStep"))
      result.maximum_angular_step
        = source["maximumAngularStep"].as<double>();
    if (has(source, "maximumSubdivisionDepth"))
      result.maximum_subdivision_depth
        = source["maximumSubdivisionDepth"].as<std::uint32_t>();
    if (has(source, "slice") && !is_nullish(source["slice"]))
      result.slice = read_slice(source["slice"]);
    return result;
  }

public:
  browser_projection(const std::string& id, const double width,
                     const double height)
  : context(runtime::find_projection_spec(id),
            a60::carto::frame(width, height))
  { }

  std::string
  id() const
  { return std::string(context.spec.argument); }

  double
  width() const
  { return context.map_frame.width(); }

  double
  height() const
  { return context.map_frame.height(); }

  val
  descriptor() const
  { return projection_descriptor(context.spec); }

  browser_projected_point
  project(const double latitude, const double longitude) const
  {
    const runtime::geographic_point geographic {latitude, longitude};
    const auto [x, y] = runtime::project_point(context, geographic);
    return {x, y, static_cast<std::uint32_t>(
                    runtime::projection_cell(context, geographic))};
  }

  val
  project_points(const val& lon_lat) const
  {
    const std::vector<double> source = read_doubles(lon_lat, "points");
    if (source.size() % 2 != 0)
      throw std::invalid_argument(
        "projectPoints expects interleaved longitude/latitude pairs");
    std::vector<double> coordinates;
    std::vector<std::uint32_t> cells;
    coordinates.reserve(source.size());
    cells.reserve(source.size() / 2);
    for (std::size_t index = 0; index < source.size(); index += 2)
      {
        const runtime::geographic_point point {
          source[index + 1], source[index],
        };
        const auto [x, y] = runtime::project_point(context, point);
        coordinates.push_back(x);
        coordinates.push_back(y);
        cells.push_back(static_cast<std::uint32_t>(
          runtime::projection_cell(context, point)));
      }
    val result = val::object();
    result.set("coordinates", typed_array("Float64Array", coordinates));
    result.set("nativeCells", typed_array("Uint32Array", cells));
    return result;
  }

  val
  project_geometry(const val& coordinates, const val& part_offsets,
                   const val& part_types, const val& feature_ids,
                   const val& ring_roles, const val& options) const
  {
    return command_buffer_value(runtime::project_geometry(
      context,
      read_geometry_input(coordinates, part_offsets, part_types,
                          feature_ids, ring_roles),
      read_options(options)));
  }

  val
  carrier_geometry(const val& options) const
  {
    const runtime::geometry_options parsed = read_options(options);
    return command_buffer_value(runtime::carrier_geometry(
      context, parsed.slice));
  }

  val
  list_slices(const bool include_clip_geometry) const
  {
    val result = val::array();
    std::size_t index = 0;
    for (const runtime::slice_descriptor& slice
         : runtime::list_slices(context))
      result.set(index++, slice_value(slice, include_clip_geometry));
    return result;
  }

  val
  slice(const std::string& id, const bool include_clip_geometry) const
  {
    return slice_value(runtime::find_slice(context, id),
                       include_clip_geometry);
  }
};

std::string
implementation_name()
{ return "cartofreako C++20 all-projection/WebAssembly runtime ABI 1"; }

std::uint32_t
runtime_abi_version()
{ return runtime::abi_version; }

} // namespace

EMSCRIPTEN_BINDINGS(cartofreako_all_projection_web)
{
  emscripten::value_object<browser_projected_point>("RuntimeProjectedPoint")
    .field("x", &browser_projected_point::x)
    .field("y", &browser_projected_point::y)
    .field("nativeCell", &browser_projected_point::native_cell);

  emscripten::class_<browser_projection>("Projection")
    .constructor<std::string, double, double>()
    .function("id", &browser_projection::id)
    .function("width", &browser_projection::width)
    .function("height", &browser_projection::height)
    .function("descriptor", &browser_projection::descriptor)
    .function("project", &browser_projection::project)
    .function("projectPoints", &browser_projection::project_points)
    .function("projectGeometryFlat", &browser_projection::project_geometry)
    .function("carrierGeometry", &browser_projection::carrier_geometry)
    .function("listSlices", &browser_projection::list_slices)
    .function("slice", &browser_projection::slice);

  emscripten::function("implementationName", &implementation_name);
  emscripten::function("runtimeAbiVersion", &runtime_abi_version);
  emscripten::function("projectionManifest", &projection_manifest);
  emscripten::function("licenseManifest", &license_manifest);
}

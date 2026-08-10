// Shared Natural Earth physical-layer generation for cartofreako projections.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_TESTS_NATURAL_EARTH_GENERATION_H
#define CART0FREAK0_TESTS_NATURAL_EARTH_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <gdal_priv.h>
#include <ogrsf_frmts.h>

#include <a60-io.h>
#include <izzi-svg.h>

#include "projection-generation-common.h"
#include "projection-area-generation.h"

namespace cart0freak0::natural_earth_generation {

namespace generation = cart0freak0::generation;
using generation::geographic_point;
using generation::projection_context;
using generation::projection_spec;
constexpr std::string_view default_data_directory
  = "assets.static/natural-earth/10m-physical-vectors";

// The public projection applies a one-degree registration adjustment. These
// are its public cut meridians. Clipping source polygons before projection is
// essential: splitting only after projection would close polygons across the
// unfolded map and paint false triangles through unrelated octants.
constexpr double seam_epsilon = 1e-7;

struct longitude_band
{
  double west;
  double east;
};

struct latitude_range
{
  double south = -90;
  double north = 90;
};

constexpr std::array longitude_bands {
  longitude_band {-180, -111 - seam_epsilon},
  longitude_band {-111 + seam_epsilon, -21 - seam_epsilon},
  longitude_band {-21 + seam_epsilon, 69 - seam_epsilon},
  longitude_band {69 + seam_epsilon, 159 - seam_epsilon},
  longitude_band {159 + seam_epsilon, 180},
};

struct dataset_deleter
{
  void
  operator()(GDALDataset* dataset) const noexcept
  { GDALClose(dataset); }
};

struct feature_deleter
{
  void
  operator()(OGRFeature* feature) const noexcept
  { OGRFeature::DestroyFeature(feature); }
};

struct geometry_deleter
{
  void
  operator()(OGRGeometry* geometry) const noexcept
  { OGRGeometryFactory::destroyGeometry(geometry); }
};

using dataset_ptr = std::unique_ptr<GDALDataset, dataset_deleter>;
using feature_ptr = std::unique_ptr<OGRFeature, feature_deleter>;
using geometry_ptr = std::unique_ptr<OGRGeometry, geometry_deleter>;

enum class geometry_role
{
  area,
  line,
};

struct layer_spec
{
  std::string_view id;
  std::string_view title;
  std::string_view shapefile;
  geometry_role role;
  svg::style style;
  double simplification;
  double maximum_segment;
};

struct render_stats
{
  std::size_t source_features = 0;
  std::size_t paths = 0;
  std::size_t points = 0;

  render_stats&
  operator+=(const render_stats& other)
  {
    source_features += other.source_features;
    paths += other.paths;
    points += other.points;
    return *this;
  }
};

void
require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

svg::style
area_style(const svg::color_qi color)
{
  // Izzi's path constructor emits a path only when a stroke color is set.
  // A same-color hairline also hides sub-pixel cracks between clipped pieces.
  return {color, 1, color, 1, 0.0025};
}

svg::style
line_style(const svg::color_qi color, const double width,
           const double opacity = 1)
{ return {svg::color::none, 0, color, opacity, width}; }

const std::filesystem::path&
natural_earth_directory()
{
  static const std::filesystem::path directory = [] {
    const char* configured = std::getenv("NATURAL_EARTH_DIR");
    if (configured != nullptr && configured[0] != '\0')
      return std::filesystem::path(configured);
    return std::filesystem::path(default_data_directory);
  }();
  return directory;
}

geometry_ptr
make_clip_rectangle(const double west, const double south,
                    const double east, const double north)
{
  auto ring = std::make_unique<OGRLinearRing>();
  ring->addPoint(west, south);
  ring->addPoint(east, south);
  ring->addPoint(east, north);
  ring->addPoint(west, north);
  ring->closeRings();

  auto polygon = std::make_unique<OGRPolygon>();
  polygon->addRingDirectly(ring.release());
  return geometry_ptr(polygon.release());
}

void
append_linestring(std::string& path_data, std::size_t& point_count,
                  const OGRLineString& line,
                  const projection_context& context, const bool close)
{
  std::vector<geographic_point> source;
  const int source_point_count = line.getNumPoints();
  source.reserve(static_cast<std::size_t>(source_point_count));
  for (int index = 0; index != source_point_count; ++index)
    source.push_back({line.getY(index), line.getX(index)});

  const std::size_t minimum_points = close ? 3 : 2;
  for (const svg::vrange& points
       : generation::project_path(context, std::move(source), close))
    if (points.size() >= minimum_points)
      {
        if (close
            && context.spec.kind
                 != generation::projection_kind::cahill_keyes
            && context.spec.kind != generation::projection_kind::star_x)
          {
            const double maximum_closure
              = context.spec.kind == generation::projection_kind::myriahedral
                  ? 1.5 : 2.5;
            if (generation::point_distance(points.back(), points.front())
                > maximum_closure)
              continue;
          }
        path_data += svg::make_path_data_from_points(points);
        if (close)
          path_data += "Z ";
        point_count += points.size();
      }
}

void
append_geometry(std::string& path_data, std::size_t& point_count,
                const OGRGeometry& geometry,
                const projection_context& context,
                const geometry_role role)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbLineString:
      append_linestring(
        path_data, point_count,
        *geometry.toLineString(), context, false);
      return;

    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          append_linestring(
            path_data, point_count, *exterior, context, true);
        for (int index = 0; index != polygon->getNumInteriorRings(); ++index)
          append_linestring(
            path_data, point_count, *polygon->getInteriorRing(index),
            context, true);
        return;
      }

    case wkbMultiLineString:
    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        const OGRGeometryCollection* collection = geometry.toGeometryCollection();
        for (int index = 0; index != collection->getNumGeometries(); ++index)
          append_geometry(
            path_data, point_count, *collection->getGeometryRef(index),
            context, role);
        return;
      }

    default:
      throw std::runtime_error(
        "unsupported Natural Earth geometry type "
        + std::string(OGRGeometryTypeToName(geometry.getGeometryType())));
    }
}

dataset_ptr
open_dataset(const std::filesystem::path& path)
{
  require(std::filesystem::is_regular_file(path),
          "missing Natural Earth shapefile: " + path.string()
          + " (run `make fetch-natural-earth-10m`)");
  auto* raw = static_cast<GDALDataset*>(GDALOpenEx(
    path.c_str(), GDAL_OF_VECTOR | GDAL_OF_READONLY,
    nullptr, nullptr, nullptr));
  require(raw != nullptr,
          "GDAL could not open Natural Earth shapefile: " + path.string());
  return dataset_ptr(raw);
}

bool
envelope_overlaps(const OGREnvelope& envelope, const longitude_band band,
                  const latitude_range latitude = {})
{
  return envelope.MaxX >= band.west && envelope.MinX <= band.east
         && envelope.MaxY >= latitude.south
         && envelope.MinY <= latitude.north;
}

geometry_ptr
prepare_geometry(const OGRGeometry& source, const layer_spec& spec)
{
  geometry_ptr geometry(source.clone());
  require(geometry != nullptr,
          "GDAL could not clone a Natural Earth geometry");

  if (spec.simplification > 0)
    {
      geometry_ptr simplified(
        geometry->SimplifyPreserveTopology(spec.simplification));
      require(simplified != nullptr,
              "GDAL could not simplify a Natural Earth geometry");
      if (!simplified->IsEmpty())
        geometry = std::move(simplified);
    }
  return geometry;
}

bool
requires_area_grid(const layer_spec& spec,
                   const projection_context& context)
{
  return spec.role == geometry_role::area
         && context.spec.kind
              != generation::projection_kind::cahill_keyes
         && context.spec.kind != generation::projection_kind::star_x;
}

bool
requires_star_x_hemisphere_clipping(
  const layer_spec& spec, const projection_context& context)
{
  // Star-X turns some equatorial octant edges into exterior notches. If an
  // area ring spans both hemispheres, SVG closure can bridge one of those
  // interruptions--most visibly in the wrapped 159 E / 201 W octant.
  return spec.role == geometry_role::area
         && context.spec.kind == generation::projection_kind::star_x;
}

void
append_gridded_band(std::string& path_data, std::size_t& point_count,
                    const OGRGeometry& prepared, const OGREnvelope& envelope,
                    const longitude_band band, const layer_spec& spec,
                    const projection_context& context,
                    const std::string& error_context)
{
  constexpr double grid_step = 5;
  const int first_row = std::clamp(
    static_cast<int>(std::floor((envelope.MinY + 90) / grid_step)), 0, 35);
  const int last_row = std::clamp(
    static_cast<int>(std::floor((envelope.MaxY + 90) / grid_step)), 0, 35);
  const int first_column = std::clamp(
    static_cast<int>(std::floor((envelope.MinX + 180) / grid_step)), 0, 71);
  const int last_column = std::clamp(
    static_cast<int>(std::floor((envelope.MaxX + 180) / grid_step)), 0, 71);

  for (int row = first_row; row <= last_row; ++row)
    {
      const double south = -90 + row * grid_step;
      const double north = south + grid_step;
      for (int column = first_column; column <= last_column; ++column)
        {
          const double cell_west = -180 + column * grid_step;
          const double cell_east = cell_west + grid_step;
          const double west = std::max(cell_west, band.west);
          const double east = std::min(cell_east, band.east);
          if (east <= west)
            continue;
          geometry_ptr rectangle = make_clip_rectangle(
            west, south, east, north);
          geometry_ptr clipped(prepared.Intersection(rectangle.get()));
          require(clipped != nullptr,
                  "GDAL failed to grid-clip " + error_context);
          if (clipped->IsEmpty())
            continue;
          const int required_dimension
            = spec.role == geometry_role::area ? 2 : 1;
          if (clipped->getDimension() < required_dimension)
            continue;
          geometry_ptr dimension_filtered(
            OGRGeometryFactory::removeLowerDimensionSubGeoms(clipped.get()));
          require(dimension_filtered != nullptr,
                  "GDAL failed to remove lower-dimensional grid intersections from "
                    + error_context);
          clipped = std::move(dimension_filtered);
          if (clipped->IsEmpty())
            continue;
          clipped->segmentize(spec.maximum_segment);
          if (generation::area::uses_native_face_clipping(context))
            {
              for (const svg::vrange& points
                   : generation::area::project_native_face_area(
                       *clipped, context, west, south, east, north))
                if (points.size() >= 3)
                  {
                    path_data += svg::make_path_data_from_points(points);
                    path_data += "Z ";
                    point_count += points.size();
                  }
            }
          else
            append_geometry(
              path_data, point_count, *clipped, context, spec.role);
        }
    }
}

render_stats
render_source(svg::group_element& output, const layer_spec& spec,
              const projection_context& context,
              const latitude_range latitude = {})
{
  const std::filesystem::path path
    = natural_earth_directory() / spec.shapefile;
  dataset_ptr dataset = open_dataset(path);
  OGRLayer* layer = dataset->GetLayer(0);
  require(layer != nullptr,
          "Natural Earth shapefile has no vector layer: " + path.string());
  const OGRSpatialReference* spatial_reference = layer->GetSpatialRef();
  require(spatial_reference != nullptr && spatial_reference->IsGeographic(),
          "Natural Earth layer is not geographic WGS84: " + path.string());

  render_stats stats;
  layer->ResetReading();
  std::size_t sequential_feature = 0;
  while (feature_ptr feature {layer->GetNextFeature()})
    {
      ++stats.source_features;
      ++sequential_feature;
      const OGRGeometry* source = feature->GetGeometryRef();
      require(source != nullptr && !source->IsEmpty(),
              "Natural Earth layer contains an empty geometry: "
              + path.string() + " feature "
              + std::to_string(sequential_feature));

      geometry_ptr prepared = prepare_geometry(*source, spec);
      OGREnvelope envelope;
      prepared->getEnvelope(&envelope);
      bool rendered_feature = false;

      for (std::size_t band_index = 0;
           band_index != longitude_bands.size(); ++band_index)
        {
          const longitude_band band = longitude_bands[band_index];
          const bool split_hemispheres
            = requires_star_x_hemisphere_clipping(spec, context);
          const int latitude_piece_count = split_hemispheres ? 2 : 1;
          for (int latitude_piece = 0;
               latitude_piece != latitude_piece_count; ++latitude_piece)
            {
              latitude_range clipped_latitude = latitude;
              std::string_view hemisphere_suffix;
              if (split_hemispheres)
                {
                  const bool north = latitude_piece == 1;
                  clipped_latitude.south = std::max(
                    latitude.south, north ? 0.0 : -90.0);
                  clipped_latitude.north = std::min(
                    latitude.north, north ? 90.0 : -seam_epsilon);
                  hemisphere_suffix = north ? "-north" : "-south";
                }
              if (clipped_latitude.north <= clipped_latitude.south
                  || !envelope_overlaps(
                    envelope, band, clipped_latitude))
                continue;

              std::string path_data;
              std::size_t point_count = 0;
              const std::string error_context
                = path.string() + " feature "
                  + std::to_string(sequential_feature);
              if (requires_area_grid(spec, context))
                append_gridded_band(
                  path_data, point_count, *prepared, envelope, band, spec,
                  context, error_context);
              else
                {
                  geometry_ptr clip = make_clip_rectangle(
                    band.west, clipped_latitude.south,
                    band.east, clipped_latitude.north);
                  geometry_ptr clipped(prepared->Intersection(clip.get()));
                  require(clipped != nullptr,
                          "GDAL failed to clip " + error_context);
                  if (clipped->IsEmpty())
                    continue;
                  clipped->segmentize(spec.maximum_segment);
                  append_geometry(
                    path_data, point_count, *clipped, context, spec.role);
                }
              if (path_data.empty())
                continue;

              std::string id(spec.id);
              id += "-feature-" + std::to_string(sequential_feature);
              id += "-band-" + std::to_string(band_index + 1);
              id += hemisphere_suffix;
              const std::string attributes
                = spec.role == geometry_role::area
                  ? R"(fill-rule="evenodd")" : std::string {};
              output.add_element(svg::make_path(
                path_data, spec.style, id, true, attributes));
              rendered_feature = true;
              ++stats.paths;
              stats.points += point_count;
            }
        }
      const bool source_overlaps_latitude
        = envelope.MaxY >= latitude.south
          && envelope.MinY <= latitude.north;
      require(rendered_feature || !source_overlaps_latitude
                || requires_area_grid(spec, context),
              "Natural Earth geometry produced no projected path: "
                + path.string() + " feature "
                + std::to_string(sequential_feature));
    }

  require(stats.source_features != 0,
          "Natural Earth layer is empty: " + path.string());
  const bool complete_latitude_range
    = latitude.south <= -90 && latitude.north >= 90;
  require(stats.paths != 0 || !complete_latitude_range,
          "Natural Earth layer produced no projected paths: " + path.string());
  return stats;
}

struct antarctic_cap
{
  a60::carto::frame map_frame;
  a60::carto::star_x_layout layout;
  double cutoff_latitude = -60;
  double radius = 0;
  double bearing_offset = 0;
  a60::carto::star_x_detail::point_2d target_pole {0, 0};

  double
  source_radius(const geographic_point point) const
  {
    return a60::carto::star_x_detail::antarctic_source_radius(
      point.latitude, point.longitude, map_frame, layout);
  }

  bool
  contains(const geographic_point point) const
  {
    constexpr double tolerance = 1e-10;
    return point.latitude <= cutoff_latitude + tolerance;
  }

  svg::point_2t
  project(const geographic_point point) const
  {
    const auto projected
      = a60::carto::star_x_detail::project_antarctic_fragment(
          point.latitude, point.longitude, map_frame, target_pole,
          bearing_offset, layout);
    return {projected.x, projected.y};
  }

  double
  boundary_latitude(const double longitude) const
  {
    static_cast<void>(longitude);
    return cutoff_latitude;
  }
};

a60::carto::star_x_layout
star_x_layout_for(const projection_context& context)
{
  require(context.spec.kind == generation::projection_kind::star_x,
          "Antarctic cap requires a Star-X projection");
  const auto& projection
    = std::get<a60::carto::starxproj>(context.projection);
  return {
    .group_gap_ratio = projection.group_gap_ratio(),
    .enlargement_factor = projection.enlargement_factor(),
  };
}

struct star_x_antarctic_vertical_extent
{
  double uncut_lower_bottom = -std::numeric_limits<double>::infinity();
  double reassembled_local_bottom
    = -std::numeric_limits<double>::infinity();
};

void
include_star_x_antarctic_vertical_ring(
  star_x_antarctic_vertical_extent& extent, const OGRLineString& ring,
  const projection_context& context,
  const a60::carto::star_x_layout layout, const double cutoff_latitude)
{
  using a60::carto::star_x_detail::face_group;
  for (int index = 0; index != ring.getNumPoints(); ++index)
    {
      const double latitude = ring.getY(index);
      const double longitude = ring.getX(index);
      if (latitude > cutoff_latitude)
        continue;
      const auto projected
        = a60::carto::star_x_detail::project_to_normalized_map(
            latitude, longitude, layout);
      if (projected.group == face_group::one)
        extent.uncut_lower_bottom = std::max(
          extent.uncut_lower_bottom,
          projected.point.y * context.map_frame.height());
      const auto local
        = a60::carto::star_x_detail::project_antarctic_fragment_local(
            latitude, longitude, context.map_frame, 0, layout);
      extent.reassembled_local_bottom = std::max(
        extent.reassembled_local_bottom, local.y);
    }
}

void
include_star_x_antarctic_vertical_extent(
  star_x_antarctic_vertical_extent& extent, const OGRGeometry& geometry,
  const projection_context& context,
  const a60::carto::star_x_layout layout, const double cutoff_latitude)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        OGREnvelope envelope;
        polygon->getEnvelope(&envelope);
        // Only the polar mainland supplies the vertical alignment.  This
        // excludes sub-Antarctic islands and all other land masses.
        if (envelope.MinY > -89.999999 || envelope.MaxY > -50)
          return;
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          include_star_x_antarctic_vertical_ring(
            extent, *exterior, context, layout, cutoff_latitude);
        return;
      }

    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        const OGRGeometryCollection* collection
          = geometry.toGeometryCollection();
        for (int index = 0; index != collection->getNumGeometries(); ++index)
          include_star_x_antarctic_vertical_extent(
            extent, *collection->getGeometryRef(index), context, layout,
            cutoff_latitude);
        return;
      }

    default:
      return;
    }
}

star_x_antarctic_vertical_extent
star_x_uncut_antarctic_vertical_extent(
  const projection_context& context,
  const a60::carto::star_x_layout layout, const double cutoff_latitude)
{
  const std::filesystem::path path
    = natural_earth_directory() / "ne_10m_land.shp";
  dataset_ptr dataset = open_dataset(path);
  OGRLayer* layer = dataset->GetLayer(0);
  require(layer != nullptr,
          "Natural Earth land shapefile has no vector layer");
  star_x_antarctic_vertical_extent result;
  layer->ResetReading();
  while (feature_ptr feature {layer->GetNextFeature()})
    if (const OGRGeometry* source = feature->GetGeometryRef())
      include_star_x_antarctic_vertical_extent(
        result, *source, context, layout, cutoff_latitude);
  require(std::isfinite(result.uncut_lower_bottom)
            && std::isfinite(result.reassembled_local_bottom),
          "Natural Earth land contains no lower-quadrant Antarctic mainland");
  return result;
}

antarctic_cap
make_antarctic_cap(const projection_context& context)
{
  const a60::carto::star_x_layout layout = star_x_layout_for(context);
  constexpr double cutoff_latitude = -60;
  double radius = 0;
  constexpr double longitude_step = 0.25;
  for (double longitude = -180; longitude <= 180;
       longitude += longitude_step)
    radius = std::max(
      radius,
      a60::carto::star_x_detail::antarctic_source_radius(
        cutoff_latitude, longitude, context.map_frame, layout));
  require(std::isfinite(radius) && radius > 0,
          "Star-X 60-degree-South cap has no finite radius");

  // Align the transformed mainland's lowest point with that same mainland's
  // lowest point in the uncut lower quadrant.  The fixed 60-degree-South cut
  // changes which geometry is moved, but cannot pull Antarctica upward.
  const star_x_antarctic_vertical_extent vertical
    = star_x_uncut_antarctic_vertical_extent(
        context, layout, cutoff_latitude);
  const double target_pole_y
    = vertical.uncut_lower_bottom - vertical.reassembled_local_bottom;
  const antarctic_cap result {
    .map_frame = context.map_frame,
    .layout = layout,
    .cutoff_latitude = cutoff_latitude,
    .radius = radius,
    .bearing_offset = 0,
    .target_pole = {
      context.map_frame.width() / 2, target_pole_y,
    },
  };
  constexpr double tolerance = 1e-9;
  require(result.contains({-60, 0})
            && !result.contains({-59.999, 0}),
          "Star-X Antarctic cap must use the fixed 60-degree-South cutoff");
  require(result.boundary_latitude(-180) == -60
            && result.boundary_latitude(0) == -60
            && result.boundary_latitude(180) == -60,
          "Star-X Antarctic cap boundary is not latitude-invariant");
  require(std::abs(result.target_pole.x
                   - context.map_frame.width() / 2) < tolerance,
          "Antarctic cap is not centered on the Star-X page axis");
  require(std::abs(result.target_pole.y
                     + vertical.reassembled_local_bottom
                   - vertical.uncut_lower_bottom) < tolerance,
          "Antarctic cap does not use the uncut lower-quadrant Y extent");
  require(result.target_pole.x - result.radius >= -tolerance
            && result.target_pole.x + result.radius
                 <= context.map_frame.width() + tolerance
            && result.target_pole.y - result.radius >= -tolerance
            && vertical.uncut_lower_bottom
                 <= context.map_frame.height() + tolerance,
          "Antarctic cap anchor does not fit the Star-X frame");
  return result;
}

geometry_ptr
make_antarctic_cap_polygon(const antarctic_cap& cap,
                            const longitude_band band)
{
  auto ring = std::make_unique<OGRLinearRing>();
  ring->addPoint(band.west, -90);
  constexpr double longitude_step = 0.25;
  for (double longitude = band.west; longitude < band.east;
       longitude += longitude_step)
    ring->addPoint(
      longitude, cap.boundary_latitude(longitude));
  ring->addPoint(band.east, cap.boundary_latitude(band.east));
  ring->addPoint(band.east, -90);
  ring->closeRings();

  auto polygon = std::make_unique<OGRPolygon>();
  polygon->addRingDirectly(ring.release());
  require(polygon->IsValid(),
          "computed Antarctic cap polygon is invalid");
  return geometry_ptr(polygon.release());
}

void
append_antarctic_cap_linestring(std::string& path_data,
                                std::size_t& point_count,
                                const OGRLineString& line,
                                const antarctic_cap& cap,
                                const bool close)
{
  svg::vrange points;
  points.reserve(static_cast<std::size_t>(line.getNumPoints()));
  for (int index = 0; index != line.getNumPoints(); ++index)
    {
      generation::append_unique(
        points, cap.project({line.getY(index), line.getX(index)}));
    }
  const std::size_t minimum_points = close ? 3 : 2;
  if (points.size() < minimum_points)
    return;
  path_data += svg::make_path_data_from_points(points);
  if (close)
    path_data += "Z ";
  point_count += points.size();
}

void
append_antarctic_cap_geometry(std::string& path_data,
                              std::size_t& point_count,
                              const OGRGeometry& geometry,
                              const antarctic_cap& cap)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbLineString:
      append_antarctic_cap_linestring(
        path_data, point_count, *geometry.toLineString(), cap, false);
      return;

    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          append_antarctic_cap_linestring(
            path_data, point_count, *exterior, cap, true);
        for (int index = 0; index != polygon->getNumInteriorRings(); ++index)
          append_antarctic_cap_linestring(
            path_data, point_count, *polygon->getInteriorRing(index),
            cap, true);
        return;
      }

    case wkbMultiLineString:
    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        const OGRGeometryCollection* collection
          = geometry.toGeometryCollection();
        for (int index = 0; index != collection->getNumGeometries(); ++index)
          append_antarctic_cap_geometry(
            path_data, point_count, *collection->getGeometryRef(index), cap);
        return;
      }

    default:
      throw std::runtime_error(
        "unsupported Antarctic geometry type "
        + std::string(OGRGeometryTypeToName(geometry.getGeometryType())));
    }
}

render_stats
render_star_x_source(svg::group_element& output, const layer_spec& spec,
                     const projection_context& context,
                     const antarctic_cap& cap)
{
  const std::filesystem::path path
    = natural_earth_directory() / spec.shapefile;
  dataset_ptr dataset = open_dataset(path);
  OGRLayer* layer = dataset->GetLayer(0);
  require(layer != nullptr,
          "Natural Earth shapefile has no vector layer: " + path.string());

  std::array<geometry_ptr, longitude_bands.size()> cap_polygons;
  for (std::size_t index = 0; index != longitude_bands.size(); ++index)
    cap_polygons[index]
      = make_antarctic_cap_polygon(cap, longitude_bands[index]);

  // SVG paint order is document order. Keep the ordinary Star-X quadrant
  // paths and the reassembled Antarctic cap in separate queues, then append
  // the cap last. Emitting each cap fragment inside the feature/band loop
  // allowed later quadrant paths to paint over it and visibly clip the
  // transformed polar projection.
  std::vector<std::string> quadrant_paths;
  std::vector<std::string> antarctic_paths;
  render_stats stats;
  layer->ResetReading();
  std::size_t sequential_feature = 0;
  while (feature_ptr feature {layer->GetNextFeature()})
    {
      ++stats.source_features;
      ++sequential_feature;
      const OGRGeometry* source = feature->GetGeometryRef();
      require(source != nullptr && !source->IsEmpty(),
              "Natural Earth layer contains an empty geometry: "
                + path.string() + " feature "
                + std::to_string(sequential_feature));
      geometry_ptr prepared = prepare_geometry(*source, spec);
      bool rendered_feature = false;
      for (std::size_t band_index = 0;
           band_index != longitude_bands.size(); ++band_index)
        {
          const longitude_band band = longitude_bands[band_index];
          for (const bool north : {false, true})
            {
              geometry_ptr rectangle = make_clip_rectangle(
                band.west, north ? 0 : -90,
                band.east, north ? 90 : -seam_epsilon);
              geometry_ptr clipped(prepared->Intersection(rectangle.get()));
              require(clipped != nullptr,
                      "GDAL failed to quadrant-clip " + path.string());
              if (!north && !clipped->IsEmpty())
                {
                  geometry_ptr outside(
                    clipped->Difference(cap_polygons[band_index].get()));
                  require(outside != nullptr,
                          "GDAL failed to remove the Star-X cap from "
                            + path.string());
                  clipped = std::move(outside);
                }
              if (clipped->IsEmpty())
                continue;
              clipped->segmentize(spec.maximum_segment);
              std::string path_data;
              std::size_t point_count = 0;
              append_geometry(
                path_data, point_count, *clipped, context, spec.role);
              if (path_data.empty())
                continue;
              const std::string id
                = std::string(spec.id) + "-feature-"
                  + std::to_string(sequential_feature) + "-band-"
                  + std::to_string(band_index + 1)
                  + (north ? "-north" : "-south");
              const std::string attributes
                = spec.role == geometry_role::area
                    ? R"(fill-rule="evenodd")" : std::string {};
              quadrant_paths.push_back(svg::make_path(
                path_data, spec.style, id, true, attributes).str());
              rendered_feature = true;
              ++stats.paths;
              stats.points += point_count;
            }

          geometry_ptr clipped(
            prepared->Intersection(cap_polygons[band_index].get()));
          require(clipped != nullptr,
                  "GDAL failed to isolate the Star-X Antarctic cap from "
                    + path.string());
          if (clipped->IsEmpty())
            continue;
          clipped->segmentize(spec.maximum_segment);
          std::string path_data;
          std::size_t point_count = 0;
          append_antarctic_cap_geometry(
            path_data, point_count, *clipped, cap);
          if (path_data.empty())
            continue;
          const std::string id
            = std::string(spec.id) + "-antarctic-fragment-"
              + std::to_string(band_index + 1) + "-feature-"
              + std::to_string(sequential_feature);
          const std::string attributes
            = spec.role == geometry_role::area
                ? R"(fill-rule="evenodd")" : std::string {};
          antarctic_paths.push_back(svg::make_path(
            path_data, spec.style, id, true, attributes).str());
          rendered_feature = true;
          ++stats.paths;
          stats.points += point_count;
        }
      require(rendered_feature,
              "Natural Earth geometry produced no Star-X path: "
                + path.string() + " feature "
                + std::to_string(sequential_feature));
    }

  for (const std::string& path : quadrant_paths)
    output.add_raw(path);
  for (const std::string& path : antarctic_paths)
    output.add_raw(path);

  require(stats.source_features != 0 && stats.paths != 0,
          "Natural Earth layer produced no Star-X paths: " + path.string());
  return stats;
}

render_stats
add_layer(svg::svg_element& document, const layer_spec& spec,
          const projection_context& context,
          const antarctic_cap* cap = nullptr)
{
  svg::group_element layer;
  layer.start_element(std::string(spec.id));
  layer.add_title(std::string(spec.title));
  render_stats stats;
  if (cap == nullptr)
    stats = render_source(layer, spec, context);
  else
    stats = render_star_x_source(layer, spec, context, *cap);
  layer.finish_element();
  document.add_element(layer);
  std::cout << spec.id << ": " << stats.source_features << " features, "
            << stats.paths << " paths, " << stats.points << " points\n";
  return stats;
}

render_stats
add_nested_layer(svg::group_element& parent, const layer_spec& spec,
                 const projection_context& context,
                 const antarctic_cap* cap = nullptr)
{
  svg::group_element layer;
  layer.start_element(std::string(spec.id));
  layer.add_title(std::string(spec.title));
  render_stats stats;
  if (cap == nullptr)
    stats = render_source(layer, spec, context);
  else
    stats = render_star_x_source(layer, spec, context, *cap);
  layer.finish_element();
  parent.add_element(layer);
  std::cout << spec.id << ": " << stats.source_features << " features, "
            << stats.paths << " paths, " << stats.points << " points\n";
  return stats;
}

const std::array bathymetry_specs {
  layer_spec {
    "bathymetry-0m", "Bathymetry 0 m", "ne_10m_bathymetry_L_0.shp",
    geometry_role::area, area_style({190, 219, 235}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-200m", "Bathymetry -200 m", "ne_10m_bathymetry_K_200.shp",
    geometry_role::area, area_style({169, 207, 229}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-1000m", "Bathymetry -1,000 m",
    "ne_10m_bathymetry_J_1000.shp", geometry_role::area,
    area_style({146, 194, 221}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-2000m", "Bathymetry -2,000 m",
    "ne_10m_bathymetry_I_2000.shp", geometry_role::area,
    area_style({122, 178, 211}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-3000m", "Bathymetry -3,000 m",
    "ne_10m_bathymetry_H_3000.shp", geometry_role::area,
    area_style({99, 161, 201}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-4000m", "Bathymetry -4,000 m",
    "ne_10m_bathymetry_G_4000.shp", geometry_role::area,
    area_style({76, 142, 190}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-5000m", "Bathymetry -5,000 m",
    "ne_10m_bathymetry_F_5000.shp", geometry_role::area,
    area_style({58, 124, 176}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-6000m", "Bathymetry -6,000 m",
    "ne_10m_bathymetry_E_6000.shp", geometry_role::area,
    area_style({45, 107, 160}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-7000m", "Bathymetry -7,000 m",
    "ne_10m_bathymetry_D_7000.shp", geometry_role::area,
    area_style({35, 91, 143}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-8000m", "Bathymetry -8,000 m",
    "ne_10m_bathymetry_C_8000.shp", geometry_role::area,
    area_style({27, 76, 125}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-9000m", "Bathymetry -9,000 m",
    "ne_10m_bathymetry_B_9000.shp", geometry_role::area,
    area_style({20, 62, 107}), 0.04, 0.5,
  },
  layer_spec {
    "bathymetry-10000m", "Bathymetry -10,000 m",
    "ne_10m_bathymetry_A_10000.shp", geometry_role::area,
    area_style({15, 49, 88}), 0.04, 0.5,
  },
};

const layer_spec ocean_spec {
  "ocean", "Ocean", "ne_10m_ocean.shp", geometry_role::area,
  area_style({209, 228, 239}), 0.04, 0.5,
};

const layer_spec land_spec {
  "land", "Land", "ne_10m_land.shp", geometry_role::area,
  area_style({221, 215, 190}), 0.03, 0.5,
};

const layer_spec minor_islands_spec {
  "minor-islands", "Minor islands", "ne_10m_minor_islands.shp",
  geometry_role::area, area_style({213, 207, 181}), 0.005, 0.25,
};

const layer_spec glaciated_areas_spec {
  "glaciated-areas", "Glaciated areas", "ne_10m_glaciated_areas.shp",
  geometry_role::area, area_style({235, 246, 246}), 0.02, 0.35,
};

const layer_spec antarctic_ice_shelves_spec {
  "antarctic-ice-shelves", "Antarctic ice shelves",
  "ne_10m_antarctic_ice_shelves_polys.shp", geometry_role::area,
  area_style({218, 239, 243}), 0.02, 0.35,
};

const layer_spec lakes_spec {
  "lakes-and-reservoirs", "Lakes and reservoirs", "ne_10m_lakes.shp",
  geometry_role::area, area_style({171, 210, 229}), 0.01, 0.25,
};

const layer_spec playas_spec {
  "playas", "Playas", "ne_10m_playas.shp", geometry_role::area,
  area_style({231, 216, 171}), 0.005, 0.25,
};

const layer_spec rivers_spec {
  "rivers", "Rivers and lake centerlines",
  "ne_10m_rivers_lake_centerlines.shp", geometry_role::line,
  line_style({76, 145, 181}, 0.018, 0.85), 0.01, 0.25,
};

const layer_spec reefs_spec {
  "reefs", "Coral reefs and atolls", "ne_10m_reefs.shp",
  geometry_role::line, line_style({26, 151, 157}, 0.026, 0.95),
  0.005, 0.2,
};

const layer_spec coastline_spec {
  "coastline", "Coastline", "ne_10m_coastline.shp", geometry_role::line,
  line_style({65, 75, 75}, 0.025, 0.9), 0.02, 0.25,
};

std::size_t
token_count(const std::string_view text, const std::string_view token)
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

enum class artifact_kind
{
  earth,
  water,
};

std::string_view
artifact_name(const artifact_kind kind)
{ return kind == artifact_kind::earth ? "earth" : "water"; }

void
initialize_gdal()
{
  require(OGRGeometryFactory::haveGEOS(),
          "GDAL must be built with GEOS support for seam-safe clipping");
  GDALAllRegister();
}

void
print_total(const render_stats total)
{
  std::cout << "total: " << total.source_features << " features, "
            << total.paths << " paths, " << total.points << " points\n";
}

void
add_octahedral_ocean_background(svg::group_element& layer,
                                 const projection_context& context,
                                 const antarctic_cap* cap = nullptr)
{
  require(context.spec.kind == generation::projection_kind::cahill_keyes
            || context.spec.kind == generation::projection_kind::star_x,
          "octahedral ocean background requires Cahill-Keyes or Star-X");

  for (std::size_t band_index = 0;
       band_index != longitude_bands.size(); ++band_index)
    for (const bool north : {false, true})
      {
        const longitude_band band = longitude_bands[band_index];
        const double south = north ? 0 : -90;
        const double north_edge = north ? 90 : -seam_epsilon;
        geometry_ptr face = make_clip_rectangle(
          band.west, south, band.east, north_edge);
        face->segmentize(0.25);

        std::string path_data;
        std::size_t point_count = 0;
        if (!north && cap != nullptr)
          {
            geometry_ptr cap_polygon
              = make_antarctic_cap_polygon(*cap, band);
            geometry_ptr outside(face->Difference(cap_polygon.get()));
            geometry_ptr inside(face->Intersection(cap_polygon.get()));
            require(outside != nullptr && inside != nullptr,
                    "GDAL failed to split a Star-X ocean background cap");
            if (!outside->IsEmpty())
              append_geometry(path_data, point_count, *outside, context,
                              geometry_role::area);
            if (!inside->IsEmpty())
              append_antarctic_cap_geometry(
                path_data, point_count, *inside, *cap);
          }
        else
          append_geometry(path_data, point_count, *face, context,
                          geometry_role::area);
        require(!path_data.empty() && point_count >= 3,
                "octahedral ocean background produced no face path");
        const std::string id
          = "ocean-face-background-" + std::to_string(band_index + 1)
            + (north ? "-north" : "-south");
        layer.add_element(svg::make_path(
          path_data, ocean_spec.style, id, true,
          R"(fill-rule="evenodd")"));
      }
}

render_stats
add_ocean_layer(svg::svg_element& document,
                const projection_context& context,
                const antarctic_cap* cap = nullptr)
{
  svg::group_element layer;
  layer.start_element(std::string(ocean_spec.id));
  layer.add_title(std::string(ocean_spec.title));

  // Keep gap-hiding backgrounds inside the one public ocean layer so the
  // Earth document still has exactly the requested ocean and land groups.
  if (context.spec.kind == generation::projection_kind::authagraph)
    {
      const svg::vrange corners {
        {0, 0}, {context.map_frame.width(), 0},
        {context.map_frame.width(), context.map_frame.height()},
        {0, context.map_frame.height()},
      };
      std::string path_data = svg::make_path_data_from_points(corners);
      path_data += "Z";
      layer.add_element(svg::make_path(
        path_data, ocean_spec.style, "ocean-periodic-background"));
    }
  else if (context.spec.kind == generation::projection_kind::cahill_keyes
           || context.spec.kind == generation::projection_kind::star_x)
    add_octahedral_ocean_background(layer, context, cap);

  const render_stats stats
    = cap == nullptr
        ? render_source(layer, ocean_spec, context)
        : render_star_x_source(layer, ocean_spec, context, *cap);
  layer.finish_element();
  document.add_element(layer);
  std::cout << ocean_spec.id << ": " << stats.source_features
            << " features, " << stats.paths << " paths, " << stats.points
            << " points\n";
  return stats;
}

render_stats
add_star_x_land_layer(svg::svg_element& document,
                      const projection_context& context,
                      const antarctic_cap& cap)
{
  svg::group_element layer;
  layer.start_element(std::string(land_spec.id));
  layer.add_title(
    "Land with a unified projection-scale Antarctic polar representation");

  render_stats stats = render_star_x_source(
    layer, land_spec, context, cap);

  svg::vrange star;
  for (const auto point
       : a60::carto::star_x_detail::make_north_pole_star(
           context.map_frame))
    star.push_back({point.x, point.y});
  std::string star_path = svg::make_path_data_from_points(star);
  star_path += "Z";
  layer.add_element(svg::make_path(
    star_path, area_style(svg::color::black), "north-pole-star"));

  layer.finish_element();
  document.add_element(layer);
  std::cout << land_spec.id << ": " << stats.source_features
            << " features, " << stats.paths << " paths, " << stats.points
            << " points plus North-pole star\n";
  return stats;
}

void
add_star_x_polar_mark(svg::svg_element& document,
                      const projection_context& context)
{
  svg::group_element layer;
  layer.start_element("polar-mark");
  layer.add_title("Star-X central North-pole mark");
  svg::vrange star;
  for (const auto point
       : a60::carto::star_x_detail::make_north_pole_star(
           context.map_frame))
    star.push_back({point.x, point.y});
  std::string path = svg::make_path_data_from_points(star);
  path += "Z";
  layer.add_element(svg::make_path(
    path, area_style(svg::color::black), "north-pole-star"));
  layer.finish_element();
  document.add_element(layer);
}

void
generate_earth(const projection_spec& spec)
{
  initialize_gdal();
  const std::string basename = generation::output_basename("earth", spec);
  const projection_context context(spec, basename);
  generation::projection_document document(
    basename, "Natural Earth 1:10m ocean and land in the "
                + std::string(spec.title) + " projection",
    context.map_frame.frame_area);

  render_stats total;
  if (spec.kind == generation::projection_kind::star_x)
    {
      const antarctic_cap cap = make_antarctic_cap(context);
      total += add_ocean_layer(document, context, &cap);
      total += add_star_x_land_layer(document, context, cap);
    }
  else
    {
      total += add_ocean_layer(document, context);
      total += add_layer(document, land_spec, context);
    }
  print_total(total);
}

void
generate_water(const projection_spec& spec)
{
  initialize_gdal();
  const std::string basename = generation::output_basename("water", spec);
  const projection_context context(spec, basename);
  generation::projection_document document(
    basename, "Natural Earth 1:10m physical overlay excluding ocean and land "
                "in the " + std::string(spec.title) + " projection",
    context.map_frame.frame_area);

  render_stats total;
  std::optional<antarctic_cap> polar_cap;
  if (spec.kind == generation::projection_kind::star_x)
    polar_cap.emplace(make_antarctic_cap(context));
  const antarctic_cap* cap
    = polar_cap.has_value() ? &*polar_cap : nullptr;
  svg::group_element bathymetry;
  bathymetry.start_element("bathymetry");
  bathymetry.add_title("Bathymetry: nested Natural Earth depth polygons");
  for (const layer_spec& spec : bathymetry_specs)
    total += add_nested_layer(bathymetry, spec, context, cap);
  bathymetry.finish_element();
  document.add_element(bathymetry);

  total += add_layer(document, minor_islands_spec, context, cap);

  svg::group_element ice;
  ice.start_element("ice");
  ice.add_title("Ice: glaciated areas and Antarctic ice shelves");
  total += add_nested_layer(ice, glaciated_areas_spec, context, cap);
  total += add_nested_layer(ice, antarctic_ice_shelves_spec, context, cap);
  ice.finish_element();
  document.add_element(ice);

  total += add_layer(document, lakes_spec, context, cap);
  total += add_layer(document, playas_spec, context, cap);
  total += add_layer(document, rivers_spec, context, cap);
  total += add_layer(document, reefs_spec, context, cap);
  total += add_layer(document, coastline_spec, context, cap);
  if (spec.kind == generation::projection_kind::star_x)
    add_star_x_polar_mark(document, context);
  print_total(total);
}

std::string
read_generated(const std::string& basename)
{
  std::ifstream input {basename + ".svg"};
  require(input.good(), "failed to open generated " + basename + ".svg");
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

void
verify_common(const std::string& generated,
              const projection_context& context,
              const std::string_view artifact)
{
  require(generated.find(generation::view_box_fragment(context))
            != std::string::npos,
          "generated " + std::string(artifact)
            + " SVG does not use the requested viewBox");
  require(generated.find(" nan") == std::string::npos
          && generated.find(" -nan") == std::string::npos
          && generated.find(" inf") == std::string::npos
          && generated.find(" -inf") == std::string::npos,
          "generated " + std::string(artifact)
            + " SVG contains a non-finite coordinate");
}

void
require_layer(const std::string& generated, const std::string_view layer)
{
  require(generated.find("<g id=\"" + std::string(layer) + "\">")
            != std::string::npos,
          "generated SVG is missing layer " + std::string(layer));
}

void
reject_layer(const std::string& generated, const std::string_view layer)
{
  require(generated.find("<g id=\"" + std::string(layer) + "\">")
            == std::string::npos,
          "generated SVG unexpectedly contains layer " + std::string(layer));
}

void
require_star_x_antarctic_overlay(const std::string& generated,
                                 const std::string_view layer)
{
  const std::string quadrant_id
    = "id=\"" + std::string(layer) + "-feature-";
  const std::string antarctic_id
    = "id=\"" + std::string(layer) + "-antarctic-fragment-";
  const std::size_t last_quadrant = generated.rfind(quadrant_id);
  const std::size_t first_antarctic = generated.find(antarctic_id);
  require(first_antarctic != std::string::npos
            && (last_quadrant == std::string::npos
                || last_quadrant < first_antarctic),
          "generated Star-X " + std::string(layer)
            + " Antarctic projection must paint above every ordinary "
              "quadrant path");
}

void
verify_earth(const std::string& generated,
             const projection_context& context)
{
  require_layer(generated, "ocean");
  require_layer(generated, "land");
  constexpr std::array excluded_layers {
    "projection-background", "bathymetry", "minor-islands", "ice",
    "glaciated-areas", "antarctic-ice-shelves", "lakes-and-reservoirs",
    "playas", "rivers", "reefs", "coastline",
  };
  for (const std::string_view layer : excluded_layers)
    reject_layer(generated, layer);
  require(token_count(generated, "<g id=") == 2,
          "generated earth SVG must contain exactly ocean and land groups");
  require(token_count(generated, "<path ") > 10,
          "generated earth SVG contains too few Natural Earth paths");
  if (context.spec.kind == generation::projection_kind::cahill_keyes
      || context.spec.kind == generation::projection_kind::star_x)
    {
      require(token_count(generated, "id=\"ocean-face-background-") == 10,
              "generated octahedral earth SVG must contain ten seam-safe "
              "ocean background pieces");
      const std::size_t background_position
        = generated.find("id=\"ocean-face-background-");
      const std::size_t source_position
        = generated.find("id=\"ocean-feature-");
      require(background_position != std::string::npos
                && source_position != std::string::npos
                && background_position < source_position,
              "generated octahedral ocean backgrounds must precede the "
              "Natural Earth ocean paths");
    }
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      require(
        generated.find("id=\"ocean-feature-1-band-5-south\"")
              != std::string::npos
          && generated.find("id=\"ocean-feature-1-band-5-north\"")
               != std::string::npos,
        "generated Star-X ocean must hemisphere-clip the wrapped "
        "159-degree band so equatorial notches remain open");
      require(generated.find("id=\"north-pole-star\"")
                != std::string::npos,
              "generated Star-X earth SVG is missing its polar star");
      require(generated.find("id=\"land-antarctic-fragment-")
                != std::string::npos,
              "generated Star-X earth SVG is missing unified Antarctica");
      require_star_x_antarctic_overlay(generated, "land");
    }
}

void
verify_water(const std::string& generated,
             const projection_context& context)
{
  constexpr std::array required_layers {
    "bathymetry", "minor-islands", "ice", "glaciated-areas",
    "antarctic-ice-shelves", "lakes-and-reservoirs", "playas", "rivers",
    "reefs", "coastline",
  };
  for (const std::string_view layer : required_layers)
    require_layer(generated, layer);
  for (const layer_spec& spec : bathymetry_specs)
    require_layer(generated, spec.id);
  reject_layer(generated, "ocean");
  reject_layer(generated, "land");
  const std::size_t expected_groups
    = context.spec.kind == generation::projection_kind::star_x ? 23 : 22;
  require(token_count(generated, "<g id=") == expected_groups,
          "generated water SVG has the wrong physical overlay group count");
  require(token_count(generated, "<path ") > 100,
          "generated water SVG contains too few Natural Earth paths");
  if (context.spec.kind == generation::projection_kind::star_x)
    {
      require_layer(generated, "polar-mark");
      require(generated.find("id=\"north-pole-star\"")
                != std::string::npos,
              "generated Star-X water SVG is missing its central black star");
      require(generated.rfind("id=\"north-pole-star\"")
                > generated.rfind("id=\"coastline-"),
              "generated Star-X water polar mark must paint above the "
              "physical layers");
      require(generated.find("id=\"coastline-antarctic-fragment-")
                != std::string::npos,
              "generated Star-X water SVG is missing unified Antarctic "
              "coastline");
      require(generated.find(
                "id=\"antarctic-ice-shelves-antarctic-fragment-")
                != std::string::npos,
              "generated Star-X water SVG is missing unified ice shelves");
      require_star_x_antarctic_overlay(generated, "coastline");
      require_star_x_antarctic_overlay(generated, "antarctic-ice-shelves");
    }
}

int
run(const artifact_kind kind, const int argc, char** argv)
{
  const projection_spec& spec = generation::projection_from_arguments(
    argc, argv);
  const std::string_view artifact = artifact_name(kind);
  const std::string basename = generation::output_basename(artifact, spec);
  const projection_context context(spec, basename);
  if (kind == artifact_kind::earth)
    generate_earth(spec);
  else
    generate_water(spec);

  const std::string generated = read_generated(basename);
  verify_common(generated, context, artifact);
  if (kind == artifact_kind::earth)
    verify_earth(generated, context);
  else
    verify_water(generated, context);
  return 0;
}

} // namespace cart0freak0::natural_earth_generation

#endif

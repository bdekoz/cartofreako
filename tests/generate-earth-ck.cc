// Generate a layered Natural Earth physical map in Cahill-Keyes projection.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <gdal_priv.h>
#include <ogrsf_frmts.h>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-cahill-keyes.h"

namespace {

using a60::carto::ckproj;
using a60::carto::frame;

constexpr std::string_view output_basename = "earth-ck-44-22";
constexpr std::string_view output_filename = "earth-ck-44-22.svg";
constexpr std::string_view default_data_directory
  = "assets/natural-earth/10m-physical-vectors";

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
make_clip_polygon(const longitude_band band)
{
  auto ring = std::make_unique<OGRLinearRing>();
  ring->addPoint(band.west, -90);
  ring->addPoint(band.east, -90);
  ring->addPoint(band.east, 90);
  ring->addPoint(band.west, 90);
  ring->closeRings();

  auto polygon = std::make_unique<OGRPolygon>();
  polygon->addRingDirectly(ring.release());
  return geometry_ptr(polygon.release());
}

const std::vector<geometry_ptr>&
clip_polygons()
{
  static const std::vector<geometry_ptr> polygons = [] {
    std::vector<geometry_ptr> result;
    result.reserve(longitude_bands.size());
    for (const longitude_band band : longitude_bands)
      result.push_back(make_clip_polygon(band));
    return result;
  }();
  return polygons;
}

svg::point_2t
project_point(const ckproj& projection, const frame& map_frame,
              const double latitude, const double longitude)
{
  const auto [x, y] = projection.meridians_to_point_2d(
    std::clamp(latitude, -90.0, 90.0),
    std::clamp(longitude, -180.0, 180.0));
  constexpr double tolerance = 1e-7;
  require(std::isfinite(x) && std::isfinite(y),
          "Natural Earth projection contains a non-finite point");
  require(x >= -tolerance && x <= map_frame.width() + tolerance
          && y >= -tolerance && y <= map_frame.height() + tolerance,
          "Natural Earth projection produced a point outside its frame");
  return {
    std::clamp(x, 0.0, map_frame.width()),
    std::clamp(y, 0.0, map_frame.height()),
  };
}

void
append_linestring(std::string& path_data, std::size_t& point_count,
                  const OGRLineString& line, const ckproj& projection,
                  const frame& map_frame, const bool close)
{
  svg::vrange points;
  const int source_point_count = line.getNumPoints();
  points.reserve(static_cast<std::size_t>(source_point_count));
  for (int index = 0; index != source_point_count; ++index)
    {
      const svg::point_2t point = project_point(
        projection, map_frame, line.getY(index), line.getX(index));
      if (points.empty() || points.back() != point)
        points.push_back(point);
    }

  if (close && points.size() > 1 && points.front() == points.back())
    points.pop_back();
  const std::size_t minimum_points = close ? 3 : 2;
  if (points.size() < minimum_points)
    return;

  path_data += svg::make_path_data_from_points(points);
  if (close)
    path_data += "Z ";
  point_count += points.size();
}

void
append_geometry(std::string& path_data, std::size_t& point_count,
                const OGRGeometry& geometry, const ckproj& projection,
                const frame& map_frame, const geometry_role role)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbLineString:
      append_linestring(
        path_data, point_count,
        *geometry.toLineString(), projection, map_frame, false);
      return;

    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          append_linestring(
            path_data, point_count, *exterior, projection, map_frame, true);
        for (int index = 0; index != polygon->getNumInteriorRings(); ++index)
          append_linestring(
            path_data, point_count, *polygon->getInteriorRing(index),
            projection, map_frame, true);
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
            projection, map_frame, role);
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
envelope_overlaps(const OGREnvelope& envelope, const longitude_band band)
{
  return envelope.MaxX >= band.west && envelope.MinX <= band.east
         && envelope.MaxY >= -90 && envelope.MinY <= 90;
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

render_stats
render_source(svg::group_element& output, const layer_spec& spec,
              const ckproj& projection, const frame& map_frame)
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
          if (!envelope_overlaps(envelope, band))
            continue;

          geometry_ptr clipped(
            prepared->Intersection(clip_polygons()[band_index].get()));
          require(clipped != nullptr,
                  "GDAL failed to clip " + path.string()
                  + " feature " + std::to_string(sequential_feature));
          if (clipped->IsEmpty())
            continue;
          clipped->segmentize(spec.maximum_segment);

          std::string path_data;
          std::size_t point_count = 0;
          append_geometry(
            path_data, point_count, *clipped, projection, map_frame,
            spec.role);
          if (path_data.empty())
            continue;

          std::string id(spec.id);
          id += "-feature-" + std::to_string(sequential_feature);
          id += "-band-" + std::to_string(band_index + 1);
          const std::string attributes
            = spec.role == geometry_role::area
              ? R"(fill-rule="evenodd")" : std::string {};
          output.add_element(svg::make_path(
            path_data, spec.style, id, true, attributes));
          rendered_feature = true;
          ++stats.paths;
          stats.points += point_count;
        }
      require(rendered_feature,
              "Natural Earth geometry produced no projected path: "
              + path.string() + " feature "
              + std::to_string(sequential_feature));
    }

  require(stats.source_features != 0,
          "Natural Earth layer is empty: " + path.string());
  require(stats.paths != 0,
          "Natural Earth layer produced no projected paths: " + path.string());
  return stats;
}

render_stats
add_layer(svg::svg_element& document, const layer_spec& spec,
          const ckproj& projection, const frame& map_frame)
{
  svg::group_element layer;
  layer.start_element(std::string(spec.id));
  layer.add_title(std::string(spec.title));
  const render_stats stats = render_source(
    layer, spec, projection, map_frame);
  layer.finish_element();
  document.add_element(layer);
  std::cout << spec.id << ": " << stats.source_features << " features, "
            << stats.paths << " paths, " << stats.points << " points\n";
  return stats;
}

render_stats
add_nested_layer(svg::group_element& parent, const layer_spec& spec,
                 const ckproj& projection, const frame& map_frame)
{
  svg::group_element layer;
  layer.start_element(std::string(spec.id));
  layer.add_title(std::string(spec.title));
  const render_stats stats = render_source(
    layer, spec, projection, map_frame);
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

} // namespace

void
test_ck_earth(const frame size)
{
  require(a60::carto::is_cahill_keyes_frame(size),
          "test_ck_earth requires a finite, positive 2:1 frame");
  require(size.width() == 44 && size.height() == 22,
          "this generator writes the 44 by 22 Cahill-Keyes fixture");
  require(OGRGeometryFactory::haveGEOS(),
          "GDAL must be built with GEOS support for seam-safe clipping");

  GDALAllRegister();
  const ckproj projection = a60::carto::make_cahill_keyes_projection(
    size, std::string(output_basename));
  svg::svg_element document(
    std::string(output_basename),
    "Natural Earth 1:10m physical vectors in the Cahill-Keyes projection",
    size.frame_area);

  render_stats total;
  total += add_layer(document, ocean_spec, projection, size);

  svg::group_element bathymetry;
  bathymetry.start_element("bathymetry");
  bathymetry.add_title("Bathymetry: nested Natural Earth depth polygons");
  for (const layer_spec& spec : bathymetry_specs)
    total += add_nested_layer(bathymetry, spec, projection, size);
  bathymetry.finish_element();
  document.add_element(bathymetry);

  total += add_layer(document, land_spec, projection, size);
  total += add_layer(document, minor_islands_spec, projection, size);

  svg::group_element ice;
  ice.start_element("ice");
  ice.add_title("Ice: glaciated areas and Antarctic ice shelves");
  total += add_nested_layer(ice, glaciated_areas_spec, projection, size);
  total += add_nested_layer(ice, antarctic_ice_shelves_spec, projection, size);
  ice.finish_element();
  document.add_element(ice);

  total += add_layer(document, lakes_spec, projection, size);
  total += add_layer(document, playas_spec, projection, size);
  total += add_layer(document, rivers_spec, projection, size);
  total += add_layer(document, reefs_spec, projection, size);
  total += add_layer(document, coastline_spec, projection, size);

  std::cout << "total: " << total.source_features << " features, "
            << total.paths << " paths, " << total.points << " points\n";
}

int
main()
{
  test_ck_earth(frame {44, 22});

  std::ifstream input {std::string(output_filename)};
  require(input.good(), "failed to open generated Cahill-Keyes earth SVG");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(generated.find("viewBox=\"0 0 44.000000 22.000000\"")
            != std::string::npos,
          "generated SVG does not use the requested 44 by 22 viewBox");

  constexpr std::array required_layers {
    "ocean", "bathymetry", "land", "minor-islands", "ice",
    "glaciated-areas", "antarctic-ice-shelves", "lakes-and-reservoirs",
    "playas", "rivers", "reefs", "coastline",
  };
  for (const std::string_view layer : required_layers)
    require(generated.find("<g id=\"" + std::string(layer) + "\">")
              != std::string::npos,
            "generated SVG is missing layer " + std::string(layer));
  for (const layer_spec& spec : bathymetry_specs)
    require(generated.find("<g id=\"" + std::string(spec.id) + "\">")
              != std::string::npos,
            "generated SVG is missing layer " + std::string(spec.id));

  require(token_count(generated, "<path ") > 100,
          "generated SVG contains too few Natural Earth paths");
  require(generated.find(" nan") == std::string::npos
          && generated.find(" -nan") == std::string::npos
          && generated.find(" inf") == std::string::npos
          && generated.find(" -inf") == std::string::npos,
          "generated SVG contains a non-finite coordinate");
}

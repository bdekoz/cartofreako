// Generate layered Natural Earth physical maps for cartofreako projections.
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

#include "projection-generation-common.h"
#include "projection-area-generation.h"

namespace {

namespace generation = cart0freak0::generation;
using generation::geographic_point;
using generation::projection_context;
using generation::projection_spec;
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

geometry_ptr
make_clip_polygon(const longitude_band band)
{ return make_clip_rectangle(band.west, -90, band.east, 90); }

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

bool
requires_area_grid(const layer_spec& spec,
                   const projection_context& context)
{
  return spec.role == geometry_role::area
         && context.spec.kind
              != generation::projection_kind::cahill_keyes
         && context.spec.kind != generation::projection_kind::star_x;
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
          clipped->segmentize(spec.maximum_segment);
          if (context.spec.kind == generation::projection_kind::myriahedral
              || context.spec.kind == generation::projection_kind::voronoi)
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
              const projection_context& context)
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
              geometry_ptr clipped(
                prepared->Intersection(clip_polygons()[band_index].get()));
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
          const std::string attributes
            = spec.role == geometry_role::area
              ? R"(fill-rule="evenodd")" : std::string {};
          output.add_element(svg::make_path(
            path_data, spec.style, id, true, attributes));
          rendered_feature = true;
          ++stats.paths;
          stats.points += point_count;
        }
      require(rendered_feature || requires_area_grid(spec, context),
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
          const projection_context& context)
{
  svg::group_element layer;
  layer.start_element(std::string(spec.id));
  layer.add_title(std::string(spec.title));
  const render_stats stats = render_source(layer, spec, context);
  layer.finish_element();
  document.add_element(layer);
  std::cout << spec.id << ": " << stats.source_features << " features, "
            << stats.paths << " paths, " << stats.points << " points\n";
  return stats;
}

render_stats
add_nested_layer(svg::group_element& parent, const layer_spec& spec,
                 const projection_context& context)
{
  svg::group_element layer;
  layer.start_element(std::string(spec.id));
  layer.add_title(std::string(spec.title));
  const render_stats stats = render_source(layer, spec, context);
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
generate_earth(const projection_spec& spec)
{
  require(OGRGeometryFactory::haveGEOS(),
          "GDAL must be built with GEOS support for seam-safe clipping");

  GDALAllRegister();
  const std::string basename = generation::output_basename("earth", spec);
  const projection_context context(spec, basename);
  generation::projection_document document(
    basename, "Natural Earth 1:10m physical vectors in the "
                + std::string(spec.title) + " projection",
    context.map_frame.frame_area);

  if (spec.kind == generation::projection_kind::authagraph)
    {
      // AuthaGraph is periodic and covers its complete rectangular carrier.
      // The base color masks sub-pixel gaps where a filled ring meets the
      // left/right registration wrap; all physical layers remain above it.
      const svg::vrange corners {
        {0, 0}, {context.map_frame.width(), 0},
        {context.map_frame.width(), context.map_frame.height()},
        {0, context.map_frame.height()},
      };
      std::string path_data = svg::make_path_data_from_points(corners);
      path_data += "Z";
      svg::group_element background;
      background.start_element("projection-background");
      background.add_title("AuthaGraph periodic ocean background");
      background.add_element(svg::make_path(
        path_data, ocean_spec.style, "projection-background-shape"));
      background.finish_element();
      document.add_element(background);
    }

  render_stats total;
  total += add_layer(document, ocean_spec, context);

  svg::group_element bathymetry;
  bathymetry.start_element("bathymetry");
  bathymetry.add_title("Bathymetry: nested Natural Earth depth polygons");
  for (const layer_spec& spec : bathymetry_specs)
    total += add_nested_layer(bathymetry, spec, context);
  bathymetry.finish_element();
  document.add_element(bathymetry);

  total += add_layer(document, land_spec, context);
  total += add_layer(document, minor_islands_spec, context);

  svg::group_element ice;
  ice.start_element("ice");
  ice.add_title("Ice: glaciated areas and Antarctic ice shelves");
  total += add_nested_layer(ice, glaciated_areas_spec, context);
  total += add_nested_layer(ice, antarctic_ice_shelves_spec, context);
  ice.finish_element();
  document.add_element(ice);

  total += add_layer(document, lakes_spec, context);
  total += add_layer(document, playas_spec, context);
  total += add_layer(document, rivers_spec, context);
  total += add_layer(document, reefs_spec, context);
  total += add_layer(document, coastline_spec, context);

  std::cout << "total: " << total.source_features << " features, "
            << total.paths << " paths, " << total.points << " points\n";
}

int
main(const int argc, char** argv)
{
  const projection_spec& spec = generation::projection_from_arguments(
    argc, argv);
  const std::string basename = generation::output_basename("earth", spec);
  const projection_context context(spec, basename);
  generate_earth(spec);

  std::ifstream input {basename + ".svg"};
  require(input.good(), "failed to open generated " + basename + ".svg");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(generated.find(generation::view_box_fragment(context))
            != std::string::npos,
          "generated earth SVG does not use the requested viewBox");

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

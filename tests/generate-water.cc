// Generate Hamonshu wave-pattern Natural Earth oceans for cartofreako.
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
#include <limits>
#include <memory>
#include <sstream>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <gdal_priv.h>
#include <ogr_api.h>
#include <ogrsf_frmts.h>

#include <a60-io.h>
#include <a60-svg.h>
#include <a60-svg-curves-hamonshu.h>

#include "projection-generation-common.h"
#include "projection-area-generation.h"

namespace {

namespace generation = cart0freak0::generation;
namespace hamonshu = svg::hamonshu;
using generation::geographic_point;
using generation::projection_context;
using generation::projection_spec;
using hamonshu::pattern_id;
using hamonshu::pattern_spec;
using hamonshu::pattern_title;
using hamonshu::validate_pattern_spec;
constexpr std::string_view ocean_shapefile = "ne_10m_ocean.shp";
constexpr std::string_view default_data_directory
  = "assets/natural-earth/10m-physical-vectors";
constexpr double seam_epsilon = 1e-7;

// Preserve cartofreako's established palette choices without depending on
// Izzi's private catalogue key, which is an implementation detail of motif
// construction rather than part of the public Hamonshu API.
unsigned
pattern_style_seed(const pattern_spec& spec)
{
  unsigned seed = spec.first_page * 131U + spec.last_page * 17U
                  + spec.motif * 43U;
  for (const unsigned char character : spec.name)
    seed = seed * 33U ^ character;
  return seed;
}

struct pattern_variation
{
  const pattern_spec* spec;
  std::size_t curvature_index;
  double curvature;
};

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

struct bounds
{
  double left = std::numeric_limits<double>::infinity();
  double top = std::numeric_limits<double>::infinity();
  double right = -std::numeric_limits<double>::infinity();
  double bottom = -std::numeric_limits<double>::infinity();

  void
  include(const svg::point_2t point)
  {
    const auto [x, y] = point;
    left = std::min(left, x);
    top = std::min(top, y);
    right = std::max(right, x);
    bottom = std::max(bottom, y);
  }

  bool
  valid() const
  {
    return std::isfinite(left) && std::isfinite(top)
           && std::isfinite(right) && std::isfinite(bottom)
           && right > left && bottom > top;
  }

  double width() const { return right - left; }
  double height() const { return bottom - top; }
};

struct projected_region
{
  std::string path_data;
  bounds box;
};

void
require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
}

std::string
number(const double value)
{
  std::ostringstream output;
  output.precision(3);
  output << value;
  return output.str();
}

std::string
variation_id(const pattern_variation& variation)
{
  return pattern_id(*variation.spec)
    + "-curvature-" + std::to_string(variation.curvature_index);
}

std::string
variation_title(const pattern_variation& variation)
{
  return pattern_title(*variation.spec)
    + "; curvature=" + number(variation.curvature);
}

std::vector<pattern_variation>
make_curated_variations()
{
  std::vector<pattern_variation> variations;
  variations.reserve(hamonshu::curated_variation_count);
  std::set<std::string> identifiers;
  for (const auto selection : hamonshu::curated_motif_selections)
    {
      const pattern_spec& spec = hamonshu::curated_pattern(selection);
      for (std::size_t index = 0;
           index != hamonshu::curated_curvature_ratios.size(); ++index)
        {
          const pattern_variation variation {
            &spec, index, hamonshu::curated_curvature_ratios[index],
          };
          require(identifiers.insert(variation_id(variation)).second,
                  "duplicate curated Hamonshu variation");
          variations.push_back(variation);
        }
    }
  require(variations.size() == hamonshu::curated_variation_count,
          "curated Hamonshu variation set is incomplete");
  return variations;
}

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
make_rectangle(const double west, const double south,
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

const std::vector<geometry_ptr>&
clip_polygons()
{
  static const std::vector<geometry_ptr> polygons = [] {
    std::vector<geometry_ptr> result;
    result.reserve(longitude_bands.size());
    for (const longitude_band band : longitude_bands)
      result.push_back(make_rectangle(band.west, -90, band.east, 90));
    return result;
  }();
  return polygons;
}

void
append_ring(std::string& path_data, bounds& box,
            const OGRLineString& ring,
            const projection_context& context)
{
  std::vector<geographic_point> source;
  source.reserve(static_cast<std::size_t>(ring.getNumPoints()));
  for (int index = 0; index != ring.getNumPoints(); ++index)
    source.push_back({ring.getY(index), ring.getX(index)});
  for (const svg::vrange& points
       : generation::project_path(context, std::move(source), true))
    if (points.size() >= 3)
      {
        if (context.spec.kind != generation::projection_kind::cahill_keyes
            && context.spec.kind != generation::projection_kind::star_x)
          {
            const double maximum_closure
              = context.spec.kind == generation::projection_kind::myriahedral
                  ? 1.5 : 2.5;
            if (generation::point_distance(points.back(), points.front())
                > maximum_closure)
              continue;
          }
        for (const svg::point_2t point : points)
          box.include(point);
        path_data += svg::make_path_data_from_points(points);
        path_data += "Z ";
      }
}

void
append_area_geometry(std::string& path_data, bounds& box,
                     const OGRGeometry& geometry,
                     const projection_context& context)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          append_ring(path_data, box, *exterior, context);
        for (int index = 0; index != polygon->getNumInteriorRings(); ++index)
          append_ring(path_data, box, *polygon->getInteriorRing(index),
                      context);
        return;
      }
    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        const OGRGeometryCollection* collection
          = geometry.toGeometryCollection();
        for (int index = 0; index != collection->getNumGeometries(); ++index)
          {
            const OGRGeometry* part = collection->getGeometryRef(index);
            if (part->getDimension() == 2)
              append_area_geometry(
                path_data, box, *part, context);
          }
        return;
      }
    default:
      if (geometry.getDimension() == 2)
        throw std::runtime_error(
          "unsupported Natural Earth ocean geometry type "
          + std::string(OGRGeometryTypeToName(geometry.getGeometryType())));
    }
}

dataset_ptr
open_ocean_dataset()
{
  const std::filesystem::path path
    = natural_earth_directory() / ocean_shapefile;
  require(std::filesystem::is_regular_file(path),
          "missing Natural Earth ocean shapefile: " + path.string()
          + " (run `make fetch-natural-earth-10m`)");
  auto* raw = static_cast<GDALDataset*>(GDALOpenEx(
    path.c_str(), GDAL_OF_VECTOR | GDAL_OF_READONLY,
    nullptr, nullptr, nullptr));
  require(raw != nullptr,
          "GDAL could not open Natural Earth ocean shapefile: "
          + path.string());
  return dataset_ptr(raw);
}

geometry_ptr
load_ocean_geometry()
{
  dataset_ptr dataset = open_ocean_dataset();
  OGRLayer* layer = dataset->GetLayer(0);
  require(layer != nullptr,
          "Natural Earth ocean shapefile has no vector layer");
  const OGRSpatialReference* spatial_reference = layer->GetSpatialRef();
  require(spatial_reference != nullptr && spatial_reference->IsGeographic(),
          "Natural Earth ocean layer is not geographic WGS84");

  layer->ResetReading();
  feature_ptr feature {layer->GetNextFeature()};
  require(feature != nullptr, "Natural Earth ocean layer is empty");
  const OGRGeometry* source = feature->GetGeometryRef();
  require(source != nullptr && !source->IsEmpty(),
          "Natural Earth ocean feature has no geometry");
  geometry_ptr simplified(source->SimplifyPreserveTopology(0.04));
  require(simplified != nullptr && !simplified->IsEmpty(),
          "GDAL could not simplify the Natural Earth ocean geometry");
  feature_ptr extra_feature {layer->GetNextFeature()};
  require(extra_feature == nullptr,
          "Natural Earth 5.1.1 ocean layer should contain one feature");
  return simplified;
}

projected_region
project_area(const OGRGeometry& geometry,
             const projection_context& context)
{
  projected_region result;
  append_area_geometry(result.path_data, result.box, geometry, context);
  return result;
}

void
append_projected_paths(projected_region& destination,
                       const std::vector<svg::vrange>& paths)
{
  for (const svg::vrange& points : paths)
    if (points.size() >= 3)
      {
        for (const svg::point_2t point : points)
          destination.box.include(point);
        destination.path_data += svg::make_path_data_from_points(points);
        destination.path_data += "Z ";
      }
}

std::vector<projected_region>
make_projected_path_regions(const std::vector<svg::vrange>& paths,
                            const double minimum_projected_span)
{
  std::vector<projected_region> result;
  for (const svg::vrange& points : paths)
    if (points.size() >= 3)
      {
        projected_region region;
        append_projected_paths(region, {points});
        if (region.box.valid()
            && region.box.width() >= minimum_projected_span
            && region.box.height() >= minimum_projected_span)
          result.push_back(std::move(region));
      }
  return result;
}

projected_region
project_complete_ocean(const OGRGeometry& ocean,
                       const projection_context& context)
{
  projected_region result;
  if (context.spec.kind == generation::projection_kind::cahill_keyes
      || context.spec.kind == generation::projection_kind::star_x)
    {
      for (std::size_t index = 0; index != longitude_bands.size(); ++index)
        {
          geometry_ptr clipped(
            ocean.Intersection(clip_polygons()[index].get()));
          require(clipped != nullptr,
                  "GDAL failed to clip the ocean at a seam");
          if (clipped->IsEmpty())
            continue;
          clipped->segmentize(0.5);
          append_area_geometry(
            result.path_data, result.box, *clipped, context);
        }
    }
  else
    {
      constexpr double grid_step = 5;
      for (double south = -90; south < 90; south += grid_step)
        for (double cell_west = -180; cell_west < 180;
             cell_west += grid_step)
          for (const longitude_band band : longitude_bands)
            {
              const double west = std::max(cell_west, band.west);
              const double east = std::min(cell_west + grid_step, band.east);
              if (east <= west)
                continue;
              geometry_ptr cell = make_rectangle(
                west, south, east, south + grid_step);
              geometry_ptr clipped(ocean.Intersection(cell.get()));
              require(clipped != nullptr,
                      "GDAL failed to grid-clip the complete ocean");
              if (clipped->IsEmpty())
                continue;
              clipped->segmentize(0.5);
              if (generation::area::uses_native_face_clipping(context))
                append_projected_paths(
                  result, generation::area::project_native_face_area(
                    *clipped, context, west, south, east,
                    south + grid_step));
              else
                append_area_geometry(
                  result.path_data, result.box, *clipped, context);
            }
    }
  require(!result.path_data.empty() && result.box.valid(),
          "Natural Earth ocean produced no projected path");
  return result;
}

std::vector<projected_region>
make_ocean_tiles(const OGRGeometry& ocean,
                 const projection_context& context)
{
  constexpr double minimum_geographic_area = 1;
  constexpr double minimum_projected_span = 0.08;
  const bool small_tiles
    = context.spec.kind != generation::projection_kind::cahill_keyes
      && context.spec.kind != generation::projection_kind::star_x;
  const double tile_size = small_tiles ? 5 : 10;
  const int column_count = static_cast<int>(360 / tile_size);
  std::vector<projected_region> result;

  for (double south = -90; south < 90; south += tile_size)
    {
      const int row = static_cast<int>((south + 90) / tile_size);
      for (int column_index = 0; column_index != column_count; ++column_index)
        {
          const int column = row % 2 == 0
                               ? column_index
                               : column_count - 1 - column_index;
          const double west = -180 + column * tile_size;
          geometry_ptr tile = make_rectangle(
            west, south, west + tile_size, south + tile_size);
          geometry_ptr water(ocean.Intersection(tile.get()));
          require(water != nullptr,
                  "GDAL failed to intersect an ocean mosaic tile");
          if (water->IsEmpty())
            continue;

          for (std::size_t band_index = 0;
               band_index != longitude_bands.size(); ++band_index)
            {
              const longitude_band band = longitude_bands[band_index];
              if (west + tile_size < band.west || west > band.east)
                continue;
              geometry_ptr clipped(
                water->Intersection(clip_polygons()[band_index].get()));
              require(clipped != nullptr,
                      "GDAL failed to seam-clip an ocean mosaic tile");
              if (clipped->IsEmpty())
                continue;
              const double area = OGR_G_Area(
                reinterpret_cast<OGRGeometryH>(clipped.get()));
              if (area < minimum_geographic_area)
                continue;
              clipped->segmentize(0.4);
              if (generation::area::uses_native_face_clipping(context))
                {
                  const std::vector<svg::vrange> paths
                    = generation::area::project_native_face_area(
                        *clipped, context,
                        std::max(west, band.west), south,
                        std::min(west + tile_size, band.east),
                        south + tile_size);
                  if (context.spec.kind
                      == generation::projection_kind::myriahedral)
                    {
                      // A 5-degree cell can cross several of the 5,120 tiny
                      // faces. Keep one motif region per source cell so the
                      // catalogue remains compact while its clip path still
                      // contains every exact face fragment.
                      projected_region region;
                      append_projected_paths(region, paths);
                      if (!region.path_data.empty() && region.box.valid()
                          && region.box.width() >= minimum_projected_span
                          && region.box.height() >= minimum_projected_span)
                        result.push_back(std::move(region));
                    }
                  else
                    {
                      std::vector<projected_region> regions
                        = make_projected_path_regions(
                            paths, minimum_projected_span);
                      for (projected_region& region : regions)
                        result.push_back(std::move(region));
                    }
                }
              else
                {
                  projected_region region = project_area(*clipped, context);
                  if (!region.path_data.empty() && region.box.valid()
                      && region.box.width() >= minimum_projected_span
                      && region.box.height() >= minimum_projected_span)
                    result.push_back(std::move(region));
                }
            }
        }
    }

  require(result.size() >= hamonshu::curated_variation_count,
          "ocean mosaic produced fewer regions than curated Hamonshu "
          "variations");
  return result;
}


svg::style
area_style(const svg::color_qi color)
{ return {color, 1, color, 1, 0.0025}; }

svg::style
line_style(const svg::color_qi color, const double width)
{ return {svg::color::none, 0, color, 0.86, width}; }

const std::array background_palette {
  svg::color_qi {205, 226, 237}, svg::color_qi {192, 219, 233},
  svg::color_qi {181, 211, 228}, svg::color_qi {170, 203, 223},
  svg::color_qi {158, 195, 216}, svg::color_qi {146, 187, 210},
  svg::color_qi {137, 178, 203}, svg::color_qi {127, 169, 196},
};

const std::array ink_palette {
  svg::color_qi {20, 54, 73}, svg::color_qi {26, 67, 88},
  svg::color_qi {31, 78, 99}, svg::color_qi {37, 88, 108},
  svg::color_qi {44, 98, 116},
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
generate_ocean(const projection_spec& projection_specification)
{
  require(OGRGeometryFactory::haveGEOS(),
          "GDAL must be built with GEOS support for seam-safe clipping");

  GDALAllRegister();
  const std::string basename = generation::output_basename(
    "ocean", projection_specification);
  const projection_context context(projection_specification, basename);
  const geometry_ptr ocean = load_ocean_geometry();
  const projected_region complete_ocean = project_complete_ocean(
    *ocean, context);
  std::vector<projected_region> tiles = make_ocean_tiles(*ocean, context);
  const std::vector<pattern_variation> variations
    = make_curated_variations();

  std::vector<std::vector<projected_region>> assigned(variations.size());
  for (std::size_t index = 0; index != tiles.size(); ++index)
    assigned[index % variations.size()].push_back(
      std::move(tiles[index]));
  for (std::size_t index = 0; index != assigned.size(); ++index)
    require(!assigned[index].empty(),
            "Hamonshu variation received no visible ocean mosaic region");

  generation::projection_document document(
    basename,
    "Natural Earth ocean filled with "
      + std::to_string(variations.size())
      + " curated variations of 13 vector studies from Mori Yuzan's 1903 "
        "Hamonshu volume 2 in the "
      + std::string(projection_specification.title) + " projection",
    context.map_frame.frame_area);

  const svg::style clip_style {
    svg::color::black, 1, svg::color::black, 0, 0,
  };
  svg::defs_element definitions;
  definitions.start_element();
  for (std::size_t index = 0; index != variations.size(); ++index)
    {
      const std::string id = variation_id(variations[index]);
      const std::string clip_id = "clip-" + id;
      std::string region_data;
      for (const projected_region& region : assigned[index])
        region_data += region.path_data;
      definitions.add_raw(
        "<clipPath id=\"" + clip_id
        + "\" clipPathUnits=\"userSpaceOnUse\">\n");
      definitions.add_element(svg::make_path(
        region_data, clip_style, clip_id + "-shape", true,
        R"(fill-rule="evenodd")"));
      definitions.add_raw("</clipPath>\n");
    }
  definitions.finish_element();
  document.add_element(definitions);

  svg::group_element ocean_layer;
  ocean_layer.start_element("ocean");
  ocean_layer.add_title(
    "Natural Earth 1:10m ocean with Hamonshu volume 2 wave studies");

  svg::group_element base_layer;
  base_layer.start_element("ocean-base");
  base_layer.add_title("Natural Earth 1:10m ocean base");
  base_layer.add_element(svg::make_path(
    complete_ocean.path_data, area_style({215, 232, 240}),
    "ocean-base-shape", true, R"(fill-rule="evenodd")"));
  base_layer.finish_element();
  ocean_layer.add_element(base_layer);

  std::set<std::string> unique_ids;
  std::size_t region_count = 0;
  for (std::size_t index = 0; index != variations.size(); ++index)
    {
      const pattern_variation& variation = variations[index];
      const pattern_spec& spec = *variation.spec;
      validate_pattern_spec(spec);
      const std::string id = variation_id(variation);
      require(unique_ids.insert(id).second,
              "duplicate Hamonshu variation layer id: " + id);
      const unsigned seed = pattern_style_seed(spec);
      std::string region_data;
      std::string motif_data;
      hamonshu::motif_config config;
      config.curvature = variation.curvature;
      for (const projected_region& region : assigned[index])
        {
          region_data += region.path_data;
          motif_data += hamonshu::make_motif_path(
            spec,
            {region.box.left, region.box.top,
             region.box.right, region.box.bottom},
            config);
          ++region_count;
        }

      svg::group_element layer;
      layer.start_element(id);
      layer.add_title(variation_title(variation));
      layer.add_element(svg::make_path(
        region_data,
        area_style(background_palette[seed % background_palette.size()]),
        id + "-ocean-regions", true, R"(fill-rule="evenodd")"));
      const std::string attributes
        = "clip-path=\"url(#clip-" + id
          + ")\" stroke-linecap=\"round\" stroke-linejoin=\"round\"";
      layer.add_element(svg::make_path(
        motif_data,
        line_style(ink_palette[seed % ink_palette.size()],
                   0.012 + 0.002 * (seed % 3)),
        id + "-lines", true, attributes));
      layer.finish_element();
      ocean_layer.add_element(layer);
    }
  ocean_layer.finish_element();
  document.add_element(ocean_layer);

  std::cout << "Hamonshu variations: " << variations.size()
            << " (" << hamonshu::curated_motif_selections.size()
            << " motifs x " << hamonshu::curated_curvature_ratios.size()
            << " curvature ratios)"
            << ", ocean mosaic regions: " << region_count << '\n';
}

int
main(const int argc, char** argv)
{
  const projection_spec& spec = generation::projection_from_arguments(
    argc, argv);
  const std::string basename = generation::output_basename("ocean", spec);
  const projection_context context(spec, basename);
  const std::vector<pattern_variation> variations
    = make_curated_variations();
  generate_ocean(spec);

  std::ifstream input {basename + ".svg"};
  require(input.good(), "failed to open generated " + basename + ".svg");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(generated.find(generation::view_box_fragment(context))
            != std::string::npos,
          "generated ocean SVG does not use the requested viewBox");
  require(generated.find("<g id=\"ocean\">") != std::string::npos
          && generated.find("<g id=\"ocean-base\">") != std::string::npos,
          "generated SVG is missing the Natural Earth ocean layers");
  require(token_count(generated, "<g id=\"hamonshu-page-")
            == variations.size(),
          "generated SVG does not contain all curated Hamonshu variations");
  require(token_count(generated, "<clipPath id=\"clip-hamonshu-page-")
            == variations.size(),
          "generated SVG does not contain one clip path per variation");
  require(token_count(generated, "<path id=\"hamonshu-page-")
            == 2 * variations.size(),
          "generated SVG does not contain two paths per variation");
  for (const pattern_variation& variation : variations)
    {
      const std::string id = variation_id(variation);
      require(generated.find("<g id=\"" + id + "\">")
                != std::string::npos,
              "generated SVG is missing Hamonshu layer " + id);
      require(generated.find(variation_title(variation)) != std::string::npos,
              "generated SVG is missing Hamonshu variation title " + id);
    }
  require(generated.find(" nan") == std::string::npos
          && generated.find(" -nan") == std::string::npos
          && generated.find(" inf") == std::string::npos
          && generated.find(" -inf") == std::string::npos,
          "generated SVG contains a non-finite coordinate");
}

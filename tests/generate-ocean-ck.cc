// Generate a Hamonshu wave-pattern Natural Earth ocean in Cahill-Keyes.
// -*- mode: C++ -*-

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
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

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-cahill-keyes.h"

namespace {

using a60::carto::ckproj;
using a60::carto::frame;

constexpr std::string_view output_basename = "ocean-ck-44-22";
constexpr std::string_view output_filename = "ocean-ck-44-22.svg";
constexpr std::string_view ocean_shapefile = "ne_10m_ocean.shp";
constexpr std::string_view default_data_directory
  = "assets/natural-earth/10m-physical-vectors";
constexpr double pi = 3.141592653589793238462643383279502884;
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

struct pattern_spec
{
  unsigned first_page;
  unsigned last_page;
  unsigned motif;
  std::string_view name;
};

// The digitized volume has 28 PDF scans but 51 numbered book pages.  The
// first illustrated page is alone on scan 2; scans 3-27 hold two book pages.
// Page 50 is the colophon.  The catalogue uses book-page numbers and records
// each bounded specimen separately; the generated SVG title also records the
// corresponding PDF scan number.
const std::array pattern_specs {
#include "hamonshu-v2-patterns.inc"
};

static_assert(pattern_specs.size() == 153);

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

enum class motif_kind
{
  waterline,
  crest,
  spiral,
  spray,
  arc,
  lattice,
  bubble,
  scroll,
  fan,
  breaker,
  braid,
  cascade,
  ripple,
  fountain,
  cloud,
  cell,
};

void
require(const bool condition, const std::string& message)
{
  if (!condition)
    throw std::runtime_error(message);
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

svg::point_2t
project_point(const ckproj& projection, const frame& map_frame,
              const double latitude, const double longitude)
{
  const auto [x, y] = projection.meridians_to_point_2d(
    std::clamp(latitude, -90.0, 90.0),
    std::clamp(longitude, -180.0, 180.0));
  constexpr double tolerance = 1e-7;
  require(std::isfinite(x) && std::isfinite(y),
          "Hamonshu ocean projection contains a non-finite point");
  require(x >= -tolerance && x <= map_frame.width() + tolerance
          && y >= -tolerance && y <= map_frame.height() + tolerance,
          "Hamonshu ocean projection produced a point outside its frame");
  return {
    std::clamp(x, 0.0, map_frame.width()),
    std::clamp(y, 0.0, map_frame.height()),
  };
}

void
append_ring(std::string& path_data, bounds& box,
            const OGRLineString& ring, const ckproj& projection,
            const frame& map_frame)
{
  svg::vrange points;
  points.reserve(static_cast<std::size_t>(ring.getNumPoints()));
  for (int index = 0; index != ring.getNumPoints(); ++index)
    {
      const svg::point_2t point = project_point(
        projection, map_frame, ring.getY(index), ring.getX(index));
      if (points.empty() || points.back() != point)
        {
          points.push_back(point);
          box.include(point);
        }
    }
  if (points.size() > 1 && points.front() == points.back())
    points.pop_back();
  if (points.size() < 3)
    return;
  path_data += svg::make_path_data_from_points(points);
  path_data += "Z ";
}

void
append_area_geometry(std::string& path_data, bounds& box,
                     const OGRGeometry& geometry, const ckproj& projection,
                     const frame& map_frame)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          append_ring(path_data, box, *exterior, projection, map_frame);
        for (int index = 0; index != polygon->getNumInteriorRings(); ++index)
          append_ring(path_data, box, *polygon->getInteriorRing(index),
                      projection, map_frame);
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
                path_data, box, *part, projection, map_frame);
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
project_area(const OGRGeometry& geometry, const ckproj& projection,
             const frame& map_frame)
{
  projected_region result;
  append_area_geometry(
    result.path_data, result.box, geometry, projection, map_frame);
  return result;
}

projected_region
project_complete_ocean(const OGRGeometry& ocean, const ckproj& projection,
                       const frame& map_frame)
{
  projected_region result;
  for (std::size_t index = 0; index != longitude_bands.size(); ++index)
    {
      geometry_ptr clipped(ocean.Intersection(clip_polygons()[index].get()));
      require(clipped != nullptr, "GDAL failed to clip the ocean at a seam");
      if (clipped->IsEmpty())
        continue;
      clipped->segmentize(0.5);
      append_area_geometry(
        result.path_data, result.box, *clipped, projection, map_frame);
    }
  require(!result.path_data.empty() && result.box.valid(),
          "Natural Earth ocean produced no projected path");
  return result;
}

std::vector<projected_region>
make_ocean_tiles(const OGRGeometry& ocean, const ckproj& projection,
                 const frame& map_frame)
{
  constexpr double tile_size = 10;
  constexpr double minimum_geographic_area = 1;
  constexpr double minimum_projected_span = 0.08;
  std::vector<projected_region> result;

  for (double south = -90; south < 90; south += tile_size)
    {
      const int row = static_cast<int>((south + 90) / tile_size);
      for (int column_index = 0; column_index != 36; ++column_index)
        {
          const int column = row % 2 == 0
                               ? column_index : 35 - column_index;
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
              projected_region region = project_area(
                *clipped, projection, map_frame);
              if (!region.path_data.empty() && region.box.valid()
                  && region.box.width() >= minimum_projected_span
                  && region.box.height() >= minimum_projected_span)
                result.push_back(std::move(region));
            }
        }
    }

  require(result.size() >= pattern_specs.size(),
          "ocean mosaic produced fewer regions than Hamonshu patterns");
  return result;
}

std::string
zero_padded(const unsigned value, const unsigned width)
{
  std::string result = std::to_string(value);
  if (result.size() < width)
    result.insert(result.begin(), width - result.size(), '0');
  return result;
}

std::string
pattern_id(const pattern_spec& spec)
{
  std::string id = "hamonshu-page-" + zero_padded(spec.first_page, 3);
  if (spec.last_page != spec.first_page)
    id += "-" + zero_padded(spec.last_page, 3);
  id += "-motif-" + zero_padded(spec.motif, 2);
  id += "-" + std::string(spec.name);
  return id;
}

std::string
display_name(const std::string_view slug)
{
  std::string result(slug);
  std::replace(result.begin(), result.end(), '-', ' ');
  if (!result.empty())
    result.front() = static_cast<char>(std::toupper(
      static_cast<unsigned char>(result.front())));
  return result;
}

unsigned
pdf_scan_page(const unsigned illustrated_page)
{
  if (illustrated_page == 1)
    return 2;
  return (illustrated_page + 4) / 2;
}

std::string
pattern_title(const pattern_spec& spec)
{
  std::string title = "Hamonshu volume 2, illustrated page ";
  title += zero_padded(spec.first_page, 3);
  if (spec.last_page != spec.first_page)
    title += "-" + zero_padded(spec.last_page, 3);
  title += " (PDF scan " + std::to_string(pdf_scan_page(spec.first_page));
  if (pdf_scan_page(spec.last_page) != pdf_scan_page(spec.first_page))
    title += "-" + std::to_string(pdf_scan_page(spec.last_page));
  title += "), motif " + zero_padded(spec.motif, 2) + ": ";
  title += display_name(spec.name);
  title += " [descriptive English title; the source has no pattern caption]";
  return title;
}

void
validate_pattern_spec(const pattern_spec& spec)
{
  require(spec.first_page >= 1 && spec.first_page <= spec.last_page
          && spec.last_page <= 51,
          "Hamonshu catalogue contains an invalid illustrated-page range");
  require(!(spec.first_page <= 50 && spec.last_page >= 50),
          "Hamonshu colophon page 50 cannot contain a wave motif");
  require(spec.motif != 0 && !spec.name.empty(),
          "Hamonshu catalogue contains an incomplete motif entry");
  require(std::all_of(spec.name.begin(), spec.name.end(), [](const char value) {
            const unsigned char character
              = static_cast<unsigned char>(value);
            return (character >= 'a' && character <= 'z')
                   || (character >= '0' && character <= '9')
                   || character == '-';
          }),
          "Hamonshu catalogue motif names must be lowercase ASCII slugs");
}

bool
contains(const std::string_view text, const std::string_view token)
{ return text.find(token) != std::string_view::npos; }

motif_kind
classify_pattern(const pattern_spec& spec)
{
  const std::string_view name = spec.name;
  if (contains(name, "bubble") || contains(name, "droplet"))
    return motif_kind::bubble;
  if (contains(name, "cell"))
    return motif_kind::cell;
  if (contains(name, "fountain") || contains(name, "reed")
      || contains(name, "spear"))
    return motif_kind::fountain;
  if (contains(name, "chevron") || contains(name, "herringbone")
      || contains(name, "diamond") || contains(name, "lattice")
      || contains(name, "crosshatch"))
    return motif_kind::lattice;
  if (contains(name, "spiral") || contains(name, "eddy")
      || contains(name, "whirlpool"))
    return motif_kind::spiral;
  if (contains(name, "ripple") || contains(name, "ring")
      || contains(name, "pool"))
    return motif_kind::ripple;
  if (contains(name, "scallop") || contains(name, "scale")
      || contains(name, "arc"))
    return motif_kind::arc;
  if (contains(name, "spray") || contains(name, "foam"))
    return motif_kind::spray;
  if (contains(name, "breaking") || contains(name, "breaker"))
    return motif_kind::breaker;
  if (contains(name, "cloud"))
    return motif_kind::cloud;
  if (contains(name, "braid") || contains(name, "interwoven")
      || contains(name, "linked") || contains(name, "knot"))
    return motif_kind::braid;
  if (contains(name, "cascade") || contains(name, "folded"))
    return motif_kind::cascade;
  if (contains(name, "fan"))
    return motif_kind::fan;
  if (contains(name, "scroll") || contains(name, "curl")
      || contains(name, "hook"))
    return motif_kind::scroll;
  if (contains(name, "crest") || contains(name, "ridge")
      || contains(name, "swell") || contains(name, "wave")
      || contains(name, "sea"))
    return motif_kind::crest;
  return motif_kind::waterline;
}

unsigned
pattern_seed(const pattern_spec& spec)
{
  unsigned seed = spec.first_page * 131 + spec.last_page * 17
                  + spec.motif * 43;
  for (const unsigned char character : spec.name)
    seed = seed * 33U ^ character;
  return seed;
}

struct pattern_context
{
  bounds box;
  unsigned seed;

  svg::point_2t
  point(const double u, const double v) const
  {
    const double angle
      = (static_cast<int>(seed % 9) - 4) * (pi / 180);
    const double du = u - 0.5;
    const double dv = v - 0.5;
    const double rotated_u = 0.5 + std::cos(angle) * du
                             - std::sin(angle) * dv;
    const double rotated_v = 0.5 + std::sin(angle) * du
                             + std::cos(angle) * dv;
    return {
      box.left + rotated_u * box.width(),
      box.top + rotated_v * box.height(),
    };
  }
};

void
append_polyline(std::string& path_data, const svg::vrange& points,
                const bool close = false)
{
  if (points.size() < (close ? 3U : 2U))
    return;
  path_data += svg::make_path_data_from_points(points);
  if (close)
    path_data += "Z ";
}

template<typename Function>
void
append_curve(std::string& path_data, const pattern_context& context,
             const int samples, Function function)
{
  svg::vrange points;
  points.reserve(static_cast<std::size_t>(samples + 1));
  for (int index = 0; index <= samples; ++index)
    {
      const double t = static_cast<double>(index) / samples;
      const auto [u, v] = function(t);
      points.push_back(context.point(u, v));
    }
  append_polyline(path_data, points);
}

void
append_ellipse(std::string& path_data, const pattern_context& context,
               const double center_u, const double center_v,
               const double radius_u, const double radius_v,
               const int samples = 28)
{
  svg::vrange points;
  points.reserve(static_cast<std::size_t>(samples));
  for (int index = 0; index != samples; ++index)
    {
      const double angle = 2 * pi * index / samples;
      points.push_back(context.point(
        center_u + radius_u * std::cos(angle),
        center_v + radius_v * std::sin(angle)));
    }
  append_polyline(path_data, points, true);
}

void
append_spiral(std::string& path_data, const pattern_context& context,
              const double center_u, const double center_v,
              const double radius, const double phase,
              const double turns = 1.8)
{
  append_curve(
    path_data, context, 42,
    [=](const double t) {
      const double angle = phase + turns * 2 * pi * t;
      const double r = radius * (1 - 0.82 * t);
      return std::pair {
        center_u + r * std::cos(angle),
        center_v + r * std::sin(angle),
      };
    });
}

void
make_waterlines(std::string& data, const pattern_context& context)
{
  const int rows = 5 + static_cast<int>(context.seed % 4);
  const double phase = (context.seed % 29) * 0.19;
  for (int row = 0; row != rows; ++row)
    append_curve(
      data, context, 36,
      [=](const double t) {
        const double center = (row + 1.0) / (rows + 1.0);
        const double wave = 0.035 * std::sin((2.0 + row % 3) * 2 * pi * t
                                             + phase + row * 0.7);
        const double ripple = 0.012 * std::sin(11 * pi * t + phase);
        return std::pair {t, center + wave + ripple};
      });
}

void
make_crests(std::string& data, const pattern_context& context)
{
  const int rows = 3 + static_cast<int>(context.seed % 2);
  const int repeats = 3 + static_cast<int>((context.seed / 3) % 3);
  for (int row = 0; row != rows; ++row)
    append_curve(
      data, context, 48,
      [=](const double t) {
        const double local = std::fmod(t * repeats + 0.5 * (row % 2), 1.0);
        const double arch = std::sin(pi * local);
        const double y = 0.2 + row * 0.22 - 0.13 * arch * arch;
        return std::pair {t, y};
      });
}

void
make_spirals(std::string& data, const pattern_context& context)
{
  const double phase = (context.seed % 31) * 0.2;
  const int count = 4 + static_cast<int>(context.seed % 3);
  for (int index = 0; index != count; ++index)
    {
      const double u = 0.18 + (index % 3) * 0.32;
      const double v = 0.28 + (index / 3) * 0.42;
      append_spiral(data, context, u, v, 0.16, phase + index * 0.8,
                    1.4 + 0.2 * (index % 3));
    }
}

void
make_spray(std::string& data, const pattern_context& context)
{
  const double phase = (context.seed % 17) * 0.11;
  const int branches = 5 + static_cast<int>(context.seed % 3);
  for (int branch = 0; branch != branches; ++branch)
    {
      const double base = 0.1 + 0.8 * branch / (branches - 1.0);
      append_curve(
        data, context, 24,
        [=](const double t) {
          const double u = base + 0.10 * std::sin(pi * t + phase + branch);
          const double v = 0.88 - 0.70 * t
                           + 0.08 * std::sin(3 * pi * t + branch);
          return std::pair {u, v};
        });
      append_ellipse(data, context,
                     base + 0.08 * std::sin(phase + branch),
                     0.12 + 0.03 * (branch % 2), 0.018, 0.025, 16);
    }
}

void
make_arcs(std::string& data, const pattern_context& context)
{
  const int rows = 4 + static_cast<int>(context.seed % 2);
  const int columns = 5;
  for (int row = 0; row != rows; ++row)
    for (int column = -1; column <= columns; ++column)
      append_curve(
        data, context, 16,
        [=](const double t) {
          const double center = (column + 0.5 * (row % 2)) / columns;
          const double angle = pi + pi * t;
          return std::pair {
            center + 0.13 * std::cos(angle),
            0.12 + row * 0.21 + 0.10 * std::sin(angle),
          };
        });
}

void
make_lattice(std::string& data, const pattern_context& context)
{
  const int lines = 7 + static_cast<int>(context.seed % 3);
  for (int line = -2; line < lines; ++line)
    for (const double direction : {-1.0, 1.0})
      append_curve(
        data, context, 22,
        [=](const double t) {
          const double offset = line / static_cast<double>(lines);
          const double u = t;
          const double v = 0.5 + direction * (t - 0.5) + offset - 0.35;
          return std::pair {u, v};
        });
}

void
make_bubbles(std::string& data, const pattern_context& context)
{
  const int count = 8 + static_cast<int>(context.seed % 5);
  for (int index = 0; index != count; ++index)
    {
      const unsigned mixed = context.seed + static_cast<unsigned>(index * 97);
      const double u = 0.12 + (mixed % 73) / 73.0 * 0.76;
      const double v = 0.12 + ((mixed / 73) % 67) / 67.0 * 0.76;
      const double radius = 0.035 + ((mixed / 491) % 5) * 0.012;
      append_ellipse(data, context, u, v, radius, radius * 0.8, 20);
    }
}

void
make_scrolls(std::string& data, const pattern_context& context)
{
  const int rows = 3 + static_cast<int>(context.seed % 2);
  const double phase = (context.seed % 23) * 0.13;
  for (int row = 0; row != rows; ++row)
    {
      append_curve(
        data, context, 38,
        [=](const double t) {
          const double u = t;
          const double v = 0.2 + row * 0.25
                           + 0.09 * std::sin(2 * pi * (2 * t) + phase);
          return std::pair {u, v};
        });
      append_spiral(data, context, 0.2 + row * 0.25,
                    0.2 + row * 0.22, 0.10, phase + row, 1.25);
    }
}

void
make_fans(std::string& data, const pattern_context& context)
{
  const bool reverse = context.seed % 2 != 0;
  for (int line = 0; line != 8; ++line)
    append_curve(
      data, context, 30,
      [=](const double t) {
        double u = 0.05 + 0.9 * t;
        if (reverse)
          u = 1 - u;
        const double height = 0.10 + line * 0.045;
        const double v = 0.88 - height * std::sin(pi * t)
                         - 0.28 * t;
        return std::pair {u, v};
      });
}

void
make_breakers(std::string& data, const pattern_context& context)
{
  const bool reverse = context.seed % 2 != 0;
  const double phase = (context.seed % 19) * 0.17;
  for (int line = 0; line != 6; ++line)
    append_curve(
      data, context, 38,
      [=](const double t) {
        double u = 0.04 + 0.78 * t;
        if (reverse)
          u = 1 - u;
        const double v = 0.84 - 0.55 * std::sin(0.72 * pi * t)
                         + line * 0.025 + 0.02 * std::sin(phase + 5 * t);
        return std::pair {u, v};
      });
  append_spiral(data, context, reverse ? 0.22 : 0.78, 0.30,
                0.17, reverse ? pi : 0, 1.4);
  for (int drop = 0; drop != 4; ++drop)
    append_ellipse(data, context, 0.42 + drop * 0.10,
                   0.16 + 0.04 * (drop % 2), 0.012, 0.018, 14);
}

void
make_braids(std::string& data, const pattern_context& context)
{
  const int strands = 4 + static_cast<int>(context.seed % 3);
  const double phase = (context.seed % 13) * 0.23;
  for (int strand = 0; strand != strands; ++strand)
    append_curve(
      data, context, 44,
      [=](const double t) {
        const double v = 0.5 + 0.22 * std::sin(
          2 * pi * (1.5 + strand % 2) * t + phase
          + strand * 2 * pi / strands);
        return std::pair {t, v};
      });
}

void
make_cascade(std::string& data, const pattern_context& context)
{
  for (int line = 0; line != 9; ++line)
    append_curve(
      data, context, 32,
      [=](const double t) {
        const double u = 0.12 + line * 0.09
                         + 0.07 * std::sin(pi * t + line * 0.4);
        const double v = 0.05 + 0.9 * t;
        return std::pair {u, v};
      });
}

void
make_ripples(std::string& data, const pattern_context& context)
{
  const int centers = 2 + static_cast<int>(context.seed % 2);
  for (int center = 0; center != centers; ++center)
    for (int ring = 1; ring <= 4; ++ring)
      append_ellipse(data, context,
                     0.28 + center * 0.43,
                     0.35 + 0.25 * (center % 2),
                     0.035 * ring, 0.022 * ring, 28);
}

void
make_fountains(std::string& data, const pattern_context& context)
{
  for (int line = 0; line != 7; ++line)
    {
      const double spread = 0.12 + line * 0.055;
      for (const double direction : {-1.0, 1.0})
        append_curve(
          data, context, 28,
          [=](const double t) {
            const double u = 0.5 + direction * spread * std::sin(pi * t / 2);
            const double v = 0.92 - 0.78 * t + 0.18 * t * t;
            return std::pair {u, v};
          });
    }
  append_spiral(data, context, 0.24, 0.72, 0.10, pi, 1.1);
  append_spiral(data, context, 0.76, 0.72, 0.10, 0, 1.1);
}

void
make_clouds(std::string& data, const pattern_context& context)
{
  const double phase = (context.seed % 31) * 0.1;
  for (int index = 0; index != 7; ++index)
    {
      const double u = 0.12 + (index % 4) * 0.25;
      const double v = 0.30 + (index / 4) * 0.38;
      append_spiral(data, context, u, v, 0.13, phase + index * 0.7, 1.35);
    }
  make_waterlines(data, context);
}

void
make_cells(std::string& data, const pattern_context& context)
{
  for (int row = 0; row != 4; ++row)
    for (int column = 0; column != 5; ++column)
      {
        const double u = 0.10 + column * 0.20 + 0.10 * (row % 2);
        const double v = 0.14 + row * 0.24;
        const double r = 0.07 + 0.01 * ((context.seed + row + column) % 3);
        append_ellipse(data, context, u, v, r, r * 0.75, 22);
      }
}

std::string
make_motif_path(const pattern_spec& spec, const bounds& box)
{
  pattern_context context {box, pattern_seed(spec)};
  std::string data;
  switch (classify_pattern(spec))
    {
    case motif_kind::waterline: make_waterlines(data, context); break;
    case motif_kind::crest: make_crests(data, context); break;
    case motif_kind::spiral: make_spirals(data, context); break;
    case motif_kind::spray: make_spray(data, context); break;
    case motif_kind::arc: make_arcs(data, context); break;
    case motif_kind::lattice: make_lattice(data, context); break;
    case motif_kind::bubble: make_bubbles(data, context); break;
    case motif_kind::scroll: make_scrolls(data, context); break;
    case motif_kind::fan: make_fans(data, context); break;
    case motif_kind::breaker: make_breakers(data, context); break;
    case motif_kind::braid: make_braids(data, context); break;
    case motif_kind::cascade: make_cascade(data, context); break;
    case motif_kind::ripple: make_ripples(data, context); break;
    case motif_kind::fountain: make_fountains(data, context); break;
    case motif_kind::cloud: make_clouds(data, context); break;
    case motif_kind::cell: make_cells(data, context); break;
    }
  require(!data.empty(), "Hamonshu motif generated no SVG path data");
  return data;
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
test_ck_ocean(const frame size)
{
  require(a60::carto::is_cahill_keyes_frame(size),
          "test_ck_ocean requires a finite, positive 2:1 frame");
  require(size.width() == 44 && size.height() == 22,
          "this generator writes the 44 by 22 Cahill-Keyes fixture");
  require(OGRGeometryFactory::haveGEOS(),
          "GDAL must be built with GEOS support for seam-safe clipping");

  GDALAllRegister();
  const ckproj projection = a60::carto::make_cahill_keyes_projection(
    size, std::string(output_basename));
  const geometry_ptr ocean = load_ocean_geometry();
  const projected_region complete_ocean = project_complete_ocean(
    *ocean, projection, size);
  std::vector<projected_region> tiles = make_ocean_tiles(
    *ocean, projection, size);

  std::vector<std::vector<projected_region>> assigned(pattern_specs.size());
  for (std::size_t index = 0; index != tiles.size(); ++index)
    assigned[index % pattern_specs.size()].push_back(
      std::move(tiles[index]));
  for (std::size_t index = 0; index != assigned.size(); ++index)
    require(!assigned[index].empty(),
            "Hamonshu pattern received no visible ocean mosaic region");

  svg::svg_element document(
    std::string(output_basename),
    "Natural Earth ocean filled with 153 source-indexed vector studies from "
    "Mori Yuzan's 1903 Hamonshu volume 2",
    size.frame_area);

  const svg::style clip_style {
    svg::color::black, 1, svg::color::black, 0, 0,
  };
  svg::defs_element definitions;
  definitions.start_element();
  for (std::size_t index = 0; index != pattern_specs.size(); ++index)
    {
      const std::string id = pattern_id(pattern_specs[index]);
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
  for (std::size_t index = 0; index != pattern_specs.size(); ++index)
    {
      const pattern_spec& spec = pattern_specs[index];
      validate_pattern_spec(spec);
      const std::string id = pattern_id(spec);
      require(unique_ids.insert(id).second,
              "duplicate Hamonshu pattern layer id: " + id);
      const unsigned seed = pattern_seed(spec);
      std::string region_data;
      std::string motif_data;
      for (const projected_region& region : assigned[index])
        {
          region_data += region.path_data;
          motif_data += make_motif_path(spec, region.box);
          ++region_count;
        }

      svg::group_element layer;
      layer.start_element(id);
      layer.add_title(pattern_title(spec));
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

  std::cout << "Hamonshu patterns: " << pattern_specs.size()
            << ", ocean mosaic regions: " << region_count << '\n';
}

int
main()
{
  test_ck_ocean(frame {44, 22});

  std::ifstream input {std::string(output_filename)};
  require(input.good(), "failed to open generated Cahill-Keyes ocean SVG");
  const std::string generated {
    std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(generated.find("viewBox=\"0 0 44.000000 22.000000\"")
            != std::string::npos,
          "generated ocean SVG does not use the requested 44 by 22 viewBox");
  require(generated.find("<g id=\"ocean\">") != std::string::npos
          && generated.find("<g id=\"ocean-base\">") != std::string::npos,
          "generated SVG is missing the Natural Earth ocean layers");
  require(token_count(generated, "<g id=\"hamonshu-page-")
            == pattern_specs.size(),
          "generated SVG does not contain all Hamonshu pattern layers");
  require(token_count(generated, "<clipPath id=\"clip-hamonshu-page-")
            == pattern_specs.size(),
          "generated SVG does not contain one clip path per pattern layer");
  require(token_count(generated, "<path id=\"hamonshu-page-")
            == 2 * pattern_specs.size(),
          "generated SVG does not contain two paths per pattern layer");
  for (const pattern_spec& spec : pattern_specs)
    {
      const std::string id = pattern_id(spec);
      require(generated.find("<g id=\"" + id + "\">")
                != std::string::npos,
              "generated SVG is missing Hamonshu layer " + id);
      require(generated.find(pattern_title(spec)) != std::string::npos,
              "generated SVG is missing Hamonshu source title " + id);
    }
  require(generated.find(" nan") == std::string::npos
          && generated.find(" -nan") == std::string::npos
          && generated.find(" inf") == std::string::npos
          && generated.find(" -inf") == std::string::npos,
          "generated SVG contains a non-finite coordinate");
}

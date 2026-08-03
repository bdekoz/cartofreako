// Cahill-Keyes projection slicing support -*- mode: C++ -*-

#ifndef CART0FREAK0_CAHILL_KEYES_SLICING_H
#define CART0FREAK0_CAHILL_KEYES_SLICING_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <a60.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-cahill-keyes.h"

/**
 * @file cart0freak0-cahill-keyes-slicing.h
 * Cahill-Keyes carrier-frame slicing and standalone SVG slice generation.
 *
 * The complete Cahill-Keyes M-layout has a mandatory 2:1 carrier frame. A
 * slice is only a viewport into coordinates already projected on that
 * carrier, so its output frame has no projection aspect-ratio constraint.
 * For a 44 by 22 carrier, a four-strip slice is therefore 11 by 22. No point
 * is reprojected or scaled: local coordinates are simply
 *
 *     x_local = x_carrier - source_view.x
 *     y_local = y_carrier - source_view.y
 *
 * The SVG writer expresses the same operation with a non-zero, unitless
 * viewBox whose width and height equal the output frame, while the root width
 * and height use explicit `in` units. This preserves one carrier coordinate
 * unit per physical inch. Raster export may then enlarge a slice by assigning
 * the smaller viewport the normal output resolution.
 *
 * Two generated slicing styles are supported:
 *
 * 1. Four vertical quadrant strips. Each strip is one quarter of the carrier
 *    width and its full height. The strips form an exact rectangular partition
 *    and hold the north/south octant pairs (1,6), (2,7), (3,8), and (4,5).
 * 2. Eight semantic octants. Each output is clipped by the sampled projected
 *    face outline and receives that outline's natural rectangular bounds.
 *    Octant bounds overlap on the M-layout because north and south faces
 *    overlap vertically; a regular 4 by 2 rectangular grid is not a set of
 *    geometrically pure octants.
 *
 * On the 44 by 22 carrier, the quadrant-strip viewBoxes begin at x=0, 11,
 * 22, and 33 and are each 11 by 22. In that same order, the requested
 * contextual latitude directions are -30 to 20, 20 to -60, -50 to 30, and
 * 60 to -40 degrees. They are annotations for source-data selection or a
 * narrated enlargement; they do not alter the rectangular viewport. A hard
 * latitude restriction belongs before projection and projected-face clipping.
 *
 * `make generate-ck-slices` builds the two generators and writes all twelve
 * SVG wrappers under `assets.generated/svg`. `make all` additionally runs the shared
 * Inkscape workflow, producing self-contained vector PDFs under
 * `assets.generated/pdf` and white-background RGB PNGs under `assets.generated/png`. At the
 * default 4K long-side setting, a quadrant strip raster is 1920 by 3840. The
 * naturally bounded octants also use a 3840-pixel height; their width follows
 * the unscaled face bounds. Artifact basenames are `earth-ck-4-slice-N` and
 * `earth-ck-8-slice-N`.
 *
 * Gene Keyes's Beta-1 Megamap used both related publishing methods:
 *
 * - Four one-meter-wide by two-meter-high strips, each containing a
 *   north/south octant pair:
 *   https://www.genekeyes.com/MEGAMAP-BETA-1/Megamap-Beta-1.html
 * - Eight square printing installments cut at the central y=10,000 line.
 *   Keyes notes that this easier straight cut is not the diagonal Equator, so
 *   every installment exchanges part of an octant with its north/south
 *   neighbor. That historical installment scheme is distinct from the exact
 *   face-clipped eight-octant style implemented here.
 * - Full-size individual octants are shown at:
 *   https://www.genekeyes.com/1-DEG-GLOBE/8-octants.html
 * - The octant construction and one-octant coordinate workflow are described
 *   at:
 *   https://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-%26-coastline.html
 *
 * Slice SVGs reference the complete generated Earth SVG with an external
 * `<use>` element. Its explicit, unitless carrier width and height override
 * the source root's physical `44in` by `22in` viewport inside the slice; this
 * keeps source geometry in carrier coordinates while the wrapper page remains
 * physically sized. Inkscape keeps this reference vector during PDF and PNG
 * export, unlike an SVG `<image>` reference, while avoiding twelve copies of
 * the large master document. Consequently, the source SVG must remain beside
 * the generated slice SVGs. PDF and PNG derivatives are self-contained.
 */

namespace a60::carto::ck_slicing {

/// Small tolerance used only to select the intended side of projection seams.
inline constexpr double seam_epsilon = 1e-7;

/// Sampling interval for the curved face perimeter, in geographic degrees.
inline constexpr double outline_sample_step = 2.5;

/// Supported ways to divide the projected whole-Earth carrier.
enum class slice_style
{
  four_strip,  ///< Four full-height, equal-width rectangular viewports.
  eight_octant, ///< Eight naturally bounded, face-clipped octant viewports.
};

/// Axis-aligned viewport in coordinates of the complete projected carrier.
struct projected_view
{
  double x;      ///< Left edge in carrier coordinates.
  double y;      ///< Top edge in carrier coordinates.
  double width;  ///< Viewport width in carrier units.
  double height; ///< Viewport height in carrier units.
};

/// Ordered latitude context supplied for a four-strip presentation.
///
/// These values describe the desired narrative or filtering direction; they
/// do not size or rescale the projected viewport. Code applying them as a hard
/// geographic filter should clip source geometry before forward projection.
struct latitude_context
{
  double from; ///< First latitude in the requested ordered range.
  double to;   ///< Last latitude in the requested ordered range.
};

/// Complete geometric and descriptive information for one generated slice.
struct slice_descriptor
{
  slice_style style; ///< Slicing style used by this descriptor.
  int number;        ///< One-based output number within that style.

  /// Arbitrary-ratio output viewport. moriginx/y translate carrier to local
  /// coordinates and must not be used to construct a Cahill-Keyes projection.
  frame output_frame;

  /// Rectangle in the complete projection carrier's coordinate system.
  projected_view source_view;

  /// Official one-based Cahill-Keyes octants represented by this slice.
  std::array<int, 2> octants;
  /// Number of meaningful entries in @ref octants.
  std::size_t octant_count;

  /// Optional ordered geographic context: the requested presentation ranges
  /// for four strips, or equator-to-pole direction for an exact octant.
  std::optional<latitude_context> latitudes;

  /// Empty for rectangular strips; a closed projected face for true octants.
  svg::vrange clip_outline;
};

/// Longitude sector and official north/south octant numbers for one column.
struct longitude_sector
{
  double west;       ///< Western boundary in geographic degrees.
  double east;       ///< Eastern boundary; may exceed 180 at the seam.
  int north_octant;  ///< Official northern-hemisphere octant number.
  int south_octant;  ///< Official southern-hemisphere octant number.
};

/// Public, one-degree-registered Cahill-Keyes sectors. The first crosses the
/// antimeridian and is intentionally expressed as 159 through 249 degrees.
inline constexpr std::array longitude_sectors {
  longitude_sector {159, 249, 1, 6},
  longitude_sector {-111, -21, 2, 7},
  longitude_sector {-21, 69, 3, 8},
  longitude_sector {69, 159, 4, 5},
};

/// Official north/south octant pair represented by each rectangular strip.
inline constexpr std::array strip_octants {
  std::array {1, 6},
  std::array {2, 7},
  std::array {3, 8},
  std::array {4, 5},
};

/// Ordered contextual ranges requested for the four-strip presentation.
inline constexpr std::array strip_latitudes {
  latitude_context {-30, 20},
  latitude_context {20, -60},
  latitude_context {-50, 30},
  latitude_context {60, -40},
};

/// Format one coordinate compactly while retaining useful double precision.
/// @param value Coordinate or frame dimension to format.
/// @return Locale-independent numeric text suitable for an SVG attribute.
inline std::string
format_number(const double value)
{
  std::ostringstream stream;
  stream << std::setprecision(12) << std::defaultfloat << value;
  return stream.str();
}

/// Escape text for use in an XML attribute or text node.
/// @param value Unescaped UTF-8 text.
/// @return Text with the five XML metacharacters replaced by entities.
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

/// Enforce the 2:1 constraint on the complete projection carrier.
/// @param carrier Frame on which the whole Earth is projected.
/// @throws std::invalid_argument if the frame is non-finite, non-positive, or
/// not 2:1.
inline void
require_valid_carrier(const frame& carrier)
{
  if (!is_cahill_keyes_frame(carrier))
    throw std::invalid_argument(
      "Cahill-Keyes slice carrier must have a finite, positive 2:1 frame");
}

/// Construct a local arbitrary-ratio output frame for a carrier viewport.
/// @param view Source rectangle in carrier coordinates.
/// @return Frame with the viewport dimensions and inverse origin offset.
inline frame
make_output_frame(const projected_view view)
{
  return {view.width, view.height, -view.x, -view.y};
}

/// Wrap a longitude into the projection API's inclusive -180 to 180 domain.
/// @param longitude Longitude in degrees, possibly beyond the canonical turn.
/// @return Equivalent canonical longitude in degrees.
inline double
canonical_longitude(double longitude)
{
  while (longitude > 180)
    longitude -= 360;
  while (longitude < -180)
    longitude += 360;
  return longitude;
}

/// Append a projected point unless it exactly repeats the previous point.
/// @param points Output point sequence.
/// @param point Candidate point.
inline void
append_unique(svg::vrange& points, const svg::point_2t point)
{
  if (points.empty() || points.back() != point)
    points.push_back(point);
}

/// Project and append one geographic point to a face outline.
/// @param points Output point sequence.
/// @param projection Cahill-Keyes projection on the complete carrier.
/// @param latitude Geographic latitude in degrees.
/// @param longitude Geographic longitude in degrees.
/// @throws std::runtime_error if projection produces a non-finite point.
inline void
append_projected(svg::vrange& points, const ckproj& projection,
                 const double latitude, const double longitude)
{
  const auto [x, y] = projection.meridians_to_point_2d(
    latitude, canonical_longitude(longitude));
  if (!std::isfinite(x) || !std::isfinite(y))
    throw std::runtime_error(
      "Cahill-Keyes octant outline contains a non-finite point");
  append_unique(points, {x, y});
}

/// Sample and append a latitude-parallel section of a face perimeter.
/// @param points Output point sequence.
/// @param projection Cahill-Keyes projection on the complete carrier.
/// @param latitude Geographic latitude in degrees.
/// @param longitude_begin First longitude in degrees.
/// @param longitude_end Final longitude in degrees.
inline void
append_parallel(svg::vrange& points, const ckproj& projection,
                const double latitude, const double longitude_begin,
                const double longitude_end)
{
  const double direction = longitude_end >= longitude_begin ? 1 : -1;
  for (double longitude = longitude_begin;
       direction * (longitude_end - longitude) > 0;
       longitude += direction * outline_sample_step)
    append_projected(points, projection, latitude, longitude);
  append_projected(points, projection, latitude, longitude_end);
}

/// Sample and append a meridian section of a face perimeter.
/// @param points Output point sequence.
/// @param projection Cahill-Keyes projection on the complete carrier.
/// @param longitude Geographic longitude in degrees.
/// @param latitude_begin First latitude in degrees.
/// @param latitude_end Final latitude in degrees.
inline void
append_meridian(svg::vrange& points, const ckproj& projection,
                const double longitude, const double latitude_begin,
                const double latitude_end)
{
  const double direction = latitude_end >= latitude_begin ? 1 : -1;
  for (double latitude = latitude_begin;
       direction * (latitude_end - latitude) > 0;
       latitude += direction * outline_sample_step)
    append_projected(points, projection, latitude, longitude);
  append_projected(points, projection, latitude_end, longitude);
}

/// Build the closed geographic perimeter of one semantic octant.
/// @param projection Cahill-Keyes projection on the complete carrier.
/// @param sector Longitude sector carrying the octant.
/// @param northern True for the northern face, false for the southern face.
/// @return Sampled projected face outline; SVG closure is added by the writer.
inline svg::vrange
make_octant_outline(const ckproj& projection,
                    const longitude_sector& sector,
                    const bool northern)
{
  const double west = sector.west + seam_epsilon;
  const double east = sector.east - seam_epsilon;
  const double center = (sector.west + sector.east) / 2;
  const double hemisphere = northern ? 1 : -1;
  const double pole = hemisphere * 90;
  const double near_pole = hemisphere * (90 - seam_epsilon);

  svg::vrange points;
  append_parallel(points, projection, 0, west, east);
  append_meridian(points, projection, east, 0, near_pole);
  append_projected(points, projection, pole, center);
  append_meridian(points, projection, west, near_pole, 0);
  return points;
}

/// Find the natural axis-aligned carrier bounds of a projected outline.
/// @param points Projected perimeter points.
/// @return Tight carrier-coordinate viewport containing every point.
/// @throws std::invalid_argument if fewer than three points are supplied.
inline projected_view
bounding_view(const svg::vrange& points)
{
  if (points.size() < 3)
    throw std::invalid_argument(
      "Cahill-Keyes slice outline must have at least three points");

  auto [minimum_x, minimum_y] = points.front();
  double maximum_x = minimum_x;
  double maximum_y = minimum_y;
  for (const auto [x, y] : points)
    {
      minimum_x = std::min(minimum_x, x);
      minimum_y = std::min(minimum_y, y);
      maximum_x = std::max(maximum_x, x);
      maximum_y = std::max(maximum_y, y);
    }
  return {
    minimum_x, minimum_y, maximum_x - minimum_x, maximum_y - minimum_y,
  };
}

/// Check descriptor geometry and invariants against its complete carrier.
/// @param slice Descriptor to check.
/// @param carrier Valid 2:1 whole-Earth carrier.
/// @throws std::runtime_error if the viewport, local frame, octant count, or
/// clipping mode is inconsistent.
inline void
validate_slice(const slice_descriptor& slice, const frame& carrier)
{
  const projected_view view = slice.source_view;
  constexpr double tolerance = 1e-8;
  const bool finite = std::isfinite(view.x) && std::isfinite(view.y)
                      && std::isfinite(view.width)
                      && std::isfinite(view.height);
  if (!finite || view.width <= 0 || view.height <= 0
      || view.x < -tolerance || view.y < -tolerance
      || view.x + view.width > carrier.width() + tolerance
      || view.y + view.height > carrier.height() + tolerance)
    throw std::runtime_error(
      "Cahill-Keyes slice viewport lies outside its projection carrier");
  if (std::abs(slice.output_frame.width() - view.width) > tolerance
      || std::abs(slice.output_frame.height() - view.height) > tolerance
      || std::abs(slice.output_frame.moriginx + view.x) > tolerance
      || std::abs(slice.output_frame.moriginy + view.y) > tolerance)
    throw std::runtime_error(
      "Cahill-Keyes slice output frame does not match its source viewport");
  if (slice.octant_count == 0 || slice.octant_count > slice.octants.size())
    throw std::runtime_error("Cahill-Keyes slice has an invalid octant count");
  if (slice.style == slice_style::four_strip && !slice.clip_outline.empty())
    throw std::runtime_error("four-strip slice unexpectedly has a face mask");
  if (slice.style == slice_style::eight_octant
      && slice.clip_outline.size() < 3)
    throw std::runtime_error("eight-octant slice is missing its face mask");
}

/// Divide a valid whole-Earth carrier into four full-height viewports.
/// @param carrier Complete Cahill-Keyes carrier; for example, 44 by 22.
/// @return Four ordered descriptors, each one quarter of the carrier width.
/// @throws std::invalid_argument if @p carrier is not finite, positive, and
/// 2:1.
inline std::vector<slice_descriptor>
make_four_slices(const frame& carrier)
{
  require_valid_carrier(carrier);
  const double width = carrier.width() / 4;
  std::vector<slice_descriptor> result;
  result.reserve(4);
  for (std::size_t index = 0; index < 4; ++index)
    {
      const projected_view view {
        index * width, 0, width, carrier.height(),
      };
      result.push_back({
        slice_style::four_strip,
        static_cast<int>(index + 1),
        make_output_frame(view),
        view,
        strip_octants[index],
        2,
        strip_latitudes[index],
        {},
      });
      validate_slice(result.back(), carrier);
    }
  return result;
}

/// Construct eight exact face-clipped Cahill-Keyes octant viewports.
/// @param carrier Complete Cahill-Keyes carrier; for example, 44 by 22.
/// @return Descriptors sorted by official Cahill-Keyes octant number.
/// @throws std::invalid_argument if @p carrier is not finite, positive, and
/// 2:1.
inline std::vector<slice_descriptor>
make_eight_slices(const frame& carrier)
{
  require_valid_carrier(carrier);
  const ckproj projection(carrier);
  std::vector<slice_descriptor> result;
  result.reserve(8);
  for (const longitude_sector& sector : longitude_sectors)
    for (const bool northern : {true, false})
      {
        svg::vrange outline = make_octant_outline(
          projection, sector, northern);
        const projected_view view = bounding_view(outline);
        const int octant = northern ? sector.north_octant
                                    : sector.south_octant;
        result.push_back({
          slice_style::eight_octant,
          octant,
          make_output_frame(view),
          view,
          {octant, 0},
          1,
          latitude_context {0, northern ? 90.0 : -90.0},
          std::move(outline),
        });
        validate_slice(result.back(), carrier);
      }
  std::sort(result.begin(), result.end(),
            [](const slice_descriptor& left, const slice_descriptor& right) {
              return left.number < right.number;
            });
  return result;
}

/// Return the stable metadata spelling for a slicing style.
/// @param style Style to identify.
/// @return `four-strip` or `eight-octant`.
inline std::string
style_name(const slice_style style)
{
  return style == slice_style::four_strip ? "four-strip" : "eight-octant";
}

/// Build the artifact basename for one Earth slice.
/// @param slice Slice whose style and number determine the name.
/// @return Basename such as `earth-ck-4-slice-1`.
inline std::string
earth_slice_basename(const slice_descriptor& slice)
{
  const char* count = slice.style == slice_style::four_strip ? "4" : "8";
  return "earth-ck-" + std::string(count) + "-slice-"
         + std::to_string(slice.number);
}

/// Join the meaningful official octant numbers in a descriptor.
/// @param slice Slice carrying one or two octant numbers.
/// @return Comma-separated numbers suitable for SVG metadata.
inline std::string
octant_names(const slice_descriptor& slice)
{
  std::string result;
  for (std::size_t index = 0; index < slice.octant_count; ++index)
    {
      if (!result.empty())
        result += ',';
      result += std::to_string(slice.octants[index]);
    }
  return result;
}

/// Serialize a source viewport as an SVG viewBox value.
/// @param view Carrier-coordinate viewport.
/// @return Four space-separated numbers: x, y, width, and height.
inline std::string
view_box(const projected_view view)
{
  return format_number(view.x) + ' ' + format_number(view.y) + ' '
         + format_number(view.width) + ' ' + format_number(view.height);
}

/// Write one lightweight vector SVG viewport around the master Earth SVG.
/// @param output Destination slice SVG.
/// @param source_svg Complete Cahill-Keyes Earth SVG referenced by `<use>`.
/// @param source_fragment Root element id inside @p source_svg.
/// @param slice Valid slice descriptor.
/// @param carrier Complete 2:1 carrier used to produce the source map.
/// @throws std::runtime_error if source validation or file output fails.
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
      "missing Cahill-Keyes source SVG: " + source_svg.string());
  if (!output.parent_path().empty())
    std::filesystem::create_directories(output.parent_path());

  std::ofstream stream(output);
  if (!stream.good())
    throw std::runtime_error(
      "could not create Cahill-Keyes slice SVG: " + output.string());

  const std::string id = output.stem().string();
  const std::string source_reference
    = xml_escape(source_svg.generic_string() + '#'
                 + std::string(source_fragment));
  const std::string box = view_box(slice.source_view);
  const std::string width = format_number(slice.output_frame.width());
  const std::string height = format_number(slice.output_frame.height());
  const std::string unit = svg::to_string(svg::unit::inch);
  const std::string clip_id = id + "-face-clip";
  const bool clipped = !slice.clip_outline.empty();

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
    << "     data-slice-style=\"" << style_name(slice.style) << "\"\n"
    << "     data-slice-number=\"" << slice.number << "\"\n"
    << "     data-octants=\"" << octant_names(slice) << "\">\n"
    << "<title>Cahill-Keyes " << style_name(slice.style) << " slice "
    << slice.number << "</title>\n"
    << "<desc>Unscaled viewport from a " << format_number(carrier.width())
    << " by " << format_number(carrier.height())
    << " Cahill-Keyes whole-Earth carrier; octant"
    << (slice.octant_count == 1 ? " " : "s ") << octant_names(slice);
  if (slice.latitudes)
    stream << "; ordered latitude context "
           << format_number(slice.latitudes->from) << " to "
           << format_number(slice.latitudes->to) << " degrees";
  stream << ".</desc>\n";

  if (clipped)
    {
      std::string path_data = svg::make_path_data_from_points(
        slice.clip_outline);
      path_data += 'Z';
      stream
        << "<defs>\n"
        << "<clipPath id=\"" << xml_escape(clip_id)
        << "\" clipPathUnits=\"userSpaceOnUse\">\n"
        << "<path d=\"" << path_data << "\" />\n"
        << "</clipPath>\n"
        << "</defs>\n";
    }

  stream << "<g id=\"" << xml_escape(id) << "-content\"";
  if (clipped)
    stream << " clip-path=\"url(#" << xml_escape(clip_id) << ")\"";
  stream
    << ">\n"
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
      "failed while writing Cahill-Keyes slice SVG: " + output.string());
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
/// @param source_svg Expected complete Earth SVG reference.
/// @param source_fragment Expected root id within @p source_svg.
/// @param slice Descriptor used to generate the SVG.
/// @param carrier Complete projection carrier used by the source SVG.
/// @throws std::runtime_error on an incorrect viewport, source reference,
/// clipping mode, or unexpected scaling transform.
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
    throw std::runtime_error("generated slice has the wrong viewBox: "
                             + output.string());
  const std::string unit = svg::to_string(svg::unit::inch);
  const std::string physical_size
    = "width=\"" + format_number(slice.output_frame.width()) + unit
      + "\" height=\"" + format_number(slice.output_frame.height()) + unit
      + "\"";
  if (generated.find(physical_size) == std::string::npos)
    throw std::runtime_error(
      "generated slice does not have physical inch dimensions: "
      + output.string());
  if (generated.find("href=\"" + reference + "\"") == std::string::npos)
    throw std::runtime_error("generated slice does not reference its source: "
                             + output.string());
  const std::string source_viewport
    = "x=\"0\" y=\"0\" width=\"" + format_number(carrier.width())
      + "\" height=\"" + format_number(carrier.height()) + "\"";
  if (generated.find(source_viewport) == std::string::npos)
    throw std::runtime_error(
      "generated slice does not override the source physical viewport: "
      + output.string());
  const bool has_clip = generated.find("<clipPath ") != std::string::npos;
  if (has_clip != !slice.clip_outline.empty())
    throw std::runtime_error("generated slice has the wrong clipping mode: "
                             + output.string());
  if (generated.find("scale(") != std::string::npos)
    throw std::runtime_error("generated slice unexpectedly scales its source: "
                             + output.string());
}

} // namespace a60::carto::ck_slicing

#endif

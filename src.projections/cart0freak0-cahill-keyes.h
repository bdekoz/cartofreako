// alpha60 cartography projection Cahill-Keyes -*- mode: C++ -*-

// alpha60
// cartography projections

// Copyright (c) 2018-2026, Benjamin De Kosnik <b.dekosnik@gmail.com>
//
// The native forward projection is derived from MegamapMaker-prep9.pl by
// Mary Jo Graca and Gene Keyes. The original algorithm is distributed for
// non-commercial use with attribution; commercial users should contact
// Gene Keyes.

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

/**
 * @file cart0freak0-cahill-keyes.h
 * @brief Native scalable Cahill-Keyes forward projection and raster presets.
 */

#ifndef cart0freak0_CK_H
#define cart0freak0_CK_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <numbers>
#include <stdexcept>
#include <utility>

/// Native scalable implementation of the Cahill-Keyes construction.
namespace a60::carto::ck_native {

/// Native forward Cahill-Keyes projection in scalable Megamap units.
class forward_projection
{
  /// Two-dimensional point in the native Megamap scaffold.
  struct xy
  {
    double x = 0; ///< Horizontal Megamap coordinate.
    double y = 0; ///< Vertical Megamap coordinate.
  };

  /// Result of intersecting a finite line segment with a circle.
  struct circle_intersection
  {
    bool intersects = false; ///< Whether a segment intersection exists.
    xy point; ///< First usable intersection point on the segment.
  };

  /// Point and signed distance associated with the 73-degree parallel.
  struct parallel_73_result
  {
    xy point; ///< Constructed 73-degree point.
    double length = 0; ///< Signed distance from the flex joint.
  };

  /// Canonical half-octant coordinates and assembly metadata.
  struct meridian
  {
    double value = 0; ///< Meridian magnitude within a half-octant, in degrees.
    double parallel = 0; ///< Absolute latitude, in degrees.
    double sign = 1; ///< Sign used to reflect across the half-octant axis.
    int octant = 1; ///< One-based target octant in the complete M-layout.
  };

  static constexpr double pi = std::numbers::pi_v<double>; ///< Pi in radians.
  static constexpr double radians = pi / 180.0; ///< Radians per degree.

  double length_mg; ///< Selected scaffold altitude and primary length unit.
  double scale; ///< Scale relative to the original 10,000-unit construction.
  double length_ma; ///< Scaled distance from control point M to A.
  double latitude_degree_100; ///< Scaled 100-unit latitude increment.
  double latitude_degree_104; ///< Scaled 104-unit polar latitude increment.
  double sin_60 = std::sqrt(3.0) / 2.0; ///< Sine of 60 degrees.
  double cos_60 = 0.5; ///< Cosine of 60 degrees.
  double y_translate; ///< Vertical translation into the complete M-layout.

  xy point_m {0, 0}; ///< Native scaffold control point M.
  xy point_g; ///< Native scaffold control point G.
  xy point_a; ///< Native scaffold control point A.
  xy point_b; ///< Derived control point B.
  xy point_c; ///< Center of the 15-degree circular construction.
  xy point_d; ///< Derived control point D.
  xy point_e; ///< Derived equatorial control point E.
  xy point_f; ///< Derived equatorial control point F.
  xy point_t; ///< Derived 73-degree control point T.

  double length_ab = 0; ///< Distance between control points A and B.
  double length_gf = 0; ///< Distance between control points G and F.
  double delta_m_equator = 0; ///< Equatorial distance per meridian degree.
  double length_ap_73 = 0; ///< Radial distance from A to parallel 73.
  double length_ap_75 = 0; ///< Radial distance from A to parallel 75.
  double radius = 0; ///< Radius of the 15-degree circular construction.

  /// Compute Euclidean distance between native points.
  /// @param a First point.
  /// @param b Second point.
  /// @return Distance between the points.
  static double
  distance(const xy a, const xy b)
  {
    return std::hypot(a.x - b.x, a.y - b.y);
  }

  /// Interpolate along a finite native line segment by physical distance.
  /// @param length Distance from `start` along the segment.
  /// @param total Total segment length.
  /// @param start Segment start point.
  /// @param end Segment end point.
  /// @return Interpolated point.
  /// @throws std::domain_error if `total` is zero.
  static xy
  interpolate(const double length, const double total, const xy start,
	      const xy end)
  {
    if (total == 0)
      throw std::domain_error(
	"Cahill-Keyes interpolation over a zero-length segment");
    const double ratio = length / total;
    return {start.x + (end.x - start.x) * ratio,
	    start.y + (end.y - start.y) * ratio};
  }

  /// Intersect two infinite lines expressed as points and degree slopes.
  /// @param first Point on the first line.
  /// @param first_slope First line's slope angle in degrees.
  /// @param second Point on the second line.
  /// @param second_slope Second line's slope angle in degrees.
  /// @return Intersection of the two lines.
  static xy
  line_intersection(const xy first, const double first_slope,
		    const xy second, const double second_slope)
  {
    const double m1 = std::tan(first_slope * radians);
    const double m2 = std::tan(second_slope * radians);
    const double x = (m1 * first.x - m2 * second.x - first.y + second.y)
		     / (m1 - m2);
    return {x, m1 * (x - first.x) + first.y};
  }

  /// Intersect a circle with a finite line segment.
  /// @param center Circle center.
  /// @param r Circle radius.
  /// @param first Segment start point.
  /// @param second Segment end point.
  /// @return First intersection whose segment parameter lies in `[0, 1]`.
  static circle_intersection
  intersect_circle_line(const xy center, const double r, const xy first,
			const xy second)
  {
    const double dx = second.x - first.x;
    const double dy = second.y - first.y;
    const double a = dx * dx + dy * dy;
    if (a == 0)
      return {};

    const double b = 2 * (dx * (first.x - center.x)
			  + dy * (first.y - center.y));
    const double c = center.x * center.x + center.y * center.y
		     + first.x * first.x + first.y * first.y
		     - 2 * (center.x * first.x + center.y * first.y)
		     - r * r;
    const double determinant = b * b - 4 * a * c;
    if (determinant < 0)
      return {};

    const double root = std::sqrt(std::max(0.0, determinant));
    const std::array<double, 2> factors {
      (-b + root) / (2 * a),
      (-b - root) / (2 * a)
    };
    for (const double factor : factors)
      if (factor >= 0 && factor <= 1)
	return {true, {first.x + factor * dx, first.y + factor * dy}};
    return {};
  }

  /// Rotate a native half-octant point by a supported assembly angle.
  /// @param point Point to rotate about the origin.
  /// @param angle Rotation in degrees; must be `-60` or `-120`.
  /// @return Rotated point.
  /// @throws std::invalid_argument for any unsupported angle.
  xy
  rotate(const xy point, const int angle) const
  {
    if (angle == -60)
      return {point.x * cos_60 + point.y * sin_60,
	      -point.x * sin_60 + point.y * cos_60};
    if (angle == -120)
      return {-point.x * cos_60 + point.y * sin_60,
	      -point.x * sin_60 - point.y * cos_60};
    throw std::invalid_argument("unsupported Cahill-Keyes octant rotation");
  }

  /// Locate the equatorial point for a canonical meridian.
  /// @param m Meridian magnitude in degrees within the half-octant.
  /// @return Point on the piecewise G-F-E equatorial path.
  xy
  equator(const double m) const
  {
    double length = delta_m_equator * m;
    if (length <= length_gf)
      return {point_g.x, length};
    length -= length_gf;
    return interpolate(length, length_ab, point_f, point_e);
  }

  /// Construct the torrid/middle-zone junction for a meridian.
  /// @param m Meridian magnitude in degrees.
  /// @return Junction point T for the requested meridian.
  xy
  joint_t(const double m) const
  {
    return line_intersection(point_m, 2 * m / 3, equator(m), m / 3);
  }

  /// Construct the middle/frigid-zone junction for a meridian.
  /// @param m Meridian magnitude in degrees.
  /// @return Junction point F for the requested meridian.
  xy
  joint_f(const double m) const
  {
    if (m == 0)
      return {point_a.x + length_ab, 0};
    return line_intersection(point_a, m, point_m, 2 * m / 3);
  }

  /// Measure the torrid segment of a constructed meridian.
  /// @param m Meridian magnitude in degrees.
  /// @return Distance from the equator to the T junction.
  double
  torrid_length(const double m) const
  { return distance(equator(m), joint_t(m)); }

  /// Measure the middle segment of a constructed meridian.
  /// @param m Meridian magnitude in degrees.
  /// @return Distance from the T junction to the F junction.
  double
  middle_length(const double m) const
  { return distance(joint_t(m), joint_f(m)); }

  /// Construct the 73-degree parallel and its signed frigid-zone length.
  /// @param m Meridian magnitude in degrees.
  /// @return Parallel point and signed distance from the F junction.
  parallel_73_result
  parallel_73(const double m) const
  {
    const xy jf = joint_f(m);
    xy p73;
    double length = 0;
    if (m <= 30)
      {
	p73 = {point_a.x + length_ap_73 * std::cos(m * radians),
	       point_a.y + length_ap_73 * std::sin(m * radians)};
	length = distance(jf, p73);
      }
    else
      {
	p73 = line_intersection(point_t, -60, jf, m);
	length = distance(jf, p73);
	if (m > 44)
	  {
	    const xy middle = line_intersection(point_t, -60, jf, 2 * m / 3);
	    if (middle.x > p73.x)
	      {
		p73 = middle;
		length = -distance(jf, p73);
	      }
	  }
      }
    return {p73, length};
  }

  /// Construct the circular 75-degree parallel for a meridian.
  /// @param m Meridian magnitude in degrees.
  /// @return Point on the 75-degree parallel.
  xy
  parallel_75(const double m) const
  {
    return {point_a.x + length_ap_75 * std::cos(m * radians),
	    point_a.y + length_ap_75 * std::sin(m * radians)};
  }

  /// Reduce geographic coordinates to canonical half-octant coordinates.
  /// @param longitude Registered longitude in degrees.
  /// @param latitude Geographic latitude in degrees.
  /// @return Meridian magnitude, absolute parallel, reflection sign, and
  /// target octant.
  meridian
  longitude_latitude_to_meridian(const double longitude,
				 const double latitude) const
  {
    // This is LLtoMP from MegamapMaker-prep9.pl. Octant 1 crosses the
    // antimeridian; southern octants 5-8 mirror northern octants 4,1-3.
    int octant = static_cast<int>((longitude + 200) / 90) + 1;
    double m = longitude + 200 - 90 * (octant - 1) - 45;
    const double sign = m < 0 ? -1.0 : 1.0;
    m = std::abs(m);
    if (octant == 5)
      octant = 1;
    if (latitude < 0)
      {
	constexpr std::array<int, 5> south {0, 6, 7, 8, 5};
	octant = south.at(octant);
      }
    return {m, std::abs(latitude), sign, octant};
  }

  /// Evaluate special transition zone H near the 73-75 degree parallels.
  /// @param m Meridian magnitude in degrees.
  /// @param p Absolute parallel in degrees.
  /// @return Native half-octant point.
  xy
  zone_h(const double m, const double p) const
  {
    const xy p75 = parallel_75(45);
    const xy p73 = parallel_73(m).point;
    const double lf = distance(point_t, point_b);
    const double lf75 = distance(point_b, p75);
    double length = (75 - p) * (lf75 + lf) / 2;
    if (length <= lf75)
      return interpolate(length, lf75, p75, point_b);
    length -= lf75;
    return interpolate(length, lf, point_b, p73);
  }

  /// Evaluate zone I along the complete piecewise meridian.
  /// @param m Meridian magnitude in degrees.
  /// @param p Absolute parallel in degrees.
  /// @return Native half-octant point.
  xy
  zone_i(const double m, const double p) const
  {
    const parallel_73_result p73 = parallel_73(m);
    const double lt = torrid_length(m);
    const double lm = middle_length(m);
    double length = p * (lt + lm + p73.length) / 73;
    if (length <= lt)
      return interpolate(length, lt, equator(m), joint_t(m));
    if (length <= lt + lm)
      return interpolate(length - lt, lm, joint_t(m), joint_f(m));
    return interpolate(length - lt - lm, p73.length, joint_f(m), p73.point);
  }

  /// Evaluate transition zone J between parallels 73 and 75.
  /// @param m Meridian magnitude in degrees.
  /// @param p Absolute parallel in degrees.
  /// @return Native half-octant point.
  xy
  zone_j(const double m, const double p) const
  {
    const xy p75 = parallel_75(m);
    const parallel_73_result p73 = parallel_73(m);
    const double lf75 = distance(joint_f(m), p75);
    double length = (75 - p) * (lf75 - p73.length) / 2;
    if (length <= lf75)
      return interpolate(length, lf75, p75, joint_f(m));
    length -= lf75;
    return interpolate(length, -p73.length, joint_f(m), p73.point);
  }

  /// Evaluate low-latitude zone K relative to the 15-degree construction.
  /// @param m Meridian magnitude in degrees.
  /// @param p Absolute parallel in degrees, at most 15.
  /// @param length_15 Distance along the meridian at parallel 15.
  /// @return Native half-octant point.
  xy
  zone_k(const double m, const double p, const double length_15) const
  {
    double length = p * length_15 / 15;
    const double lt = torrid_length(m);
    if (length <= lt)
      return interpolate(length, lt, equator(m), joint_t(m));
    return interpolate(length - lt, middle_length(m), joint_t(m), joint_f(m));
  }

  /// Evaluate zone L between the 15- and 73-degree constructions.
  /// @param m Meridian magnitude in degrees.
  /// @param p Absolute parallel in degrees.
  /// @param length_15 Distance along the meridian at parallel 15.
  /// @return Native half-octant point.
  xy
  zone_l(const double m, const double p, const double length_15) const
  {
    const parallel_73_result p73 = parallel_73(m);
    const double lt = torrid_length(m);
    const double lm = middle_length(m);
    double length = length_15
		    + (p - 15) * ((lt + lm + p73.length) - length_15) / 58;
    if (length <= lt)
      return interpolate(length, lt, equator(m), joint_t(m));
    if (length <= lt + lm)
      return interpolate(length - lt, lm, joint_t(m), joint_f(m));
    return interpolate(length - lt - lm, p73.length, joint_f(m), p73.point);
  }

  /// Evaluate a canonical meridian/parallel intersection.
  /// @param m Meridian magnitude in degrees within a half-octant.
  /// @param p Absolute parallel in degrees.
  /// @return Native point before octant assembly.
  xy
  meridian_parallel_to_xy(const double m, const double p) const
  {
    if (m == 0)
      return p >= 75
	? xy {point_a.x + (90 - p) * latitude_degree_104, 0}
	: xy {point_g.x - p * latitude_degree_100, 0};

    if (p >= 75)
      {
	const double length = latitude_degree_104 * (90 - p);
	return {point_a.x + length * std::cos(m * radians),
		point_a.y + length * std::sin(m * radians)};
      }

    if (p == 0)
      return equator(m);

    if (p >= 73 && m <= 30)
      {
	const double length = length_ap_75
			      + (75 - p) * latitude_degree_100;
	return {point_a.x + length * std::cos(m * radians),
		point_a.y + length * std::sin(m * radians)};
      }

    if (m == 45)
      {
	if (p <= 15)
	  return interpolate(p, 15, point_e, point_d);
	if (p <= 73)
	  return interpolate(p - 15, 58, point_d, point_t);
	return zone_h(m, p);
      }

    if (m <= 29)
      return zone_i(m, p);
    if (p >= 73)
      return zone_j(m, p);

    const xy jt = joint_t(m);
    const xy jf = joint_f(m);
    circle_intersection p15 = intersect_circle_line(point_c, radius, jt, jf);
    const double lt = torrid_length(m);
    double length_15 = 0;
    if (p15.intersects)
      length_15 = lt + distance(jt, p15.point);
    else
      {
	p15 = intersect_circle_line(point_c, radius, equator(m), jt);
	if (!p15.intersects)
	  throw std::domain_error(
	    "Cahill-Keyes parallel 15 misses its meridian");
	length_15 = lt - distance(jt, p15.point);
      }
    return p <= 15 ? zone_k(m, p, length_15)
		   : zone_l(m, p, length_15);
  }

  /// Rotate, reflect, and translate a half-octant point into the M-layout.
  /// @param point Canonical half-octant point.
  /// @param octant One-based target octant in `[1, 8]`.
  /// @return Point in the complete centered Megamap layout.
  /// @throws std::domain_error if `octant` is outside `[1, 8]`.
  xy
  half_octant_to_megamap(xy point, const int octant) const
  {
    xy result;
    switch (octant)
      {
      case 1:
	result = rotate(point, -120);
	result.x -= length_mg;
	break;
      case 2:
	result = rotate(point, -60);
	result.x -= length_mg;
	break;
      case 3:
	result = rotate(point, -120);
	result.x += length_mg;
	break;
      case 4:
	result = rotate(point, -60);
	result.x += length_mg;
	break;
      case 5:
	point.x = 2 * length_mg - point.x;
	result = rotate(point, -60);
	result.x += length_mg;
	break;
      case 6:
	point.x = 2 * length_mg - point.x;
	result = rotate(point, -120);
	result.x -= length_mg;
	break;
      case 7:
	point.x = 2 * length_mg - point.x;
	result = rotate(point, -60);
	result.x -= length_mg;
	break;
      case 8:
	point.x = 2 * length_mg - point.x;
	result = rotate(point, -120);
	result.x += length_mg;
	break;
      default:
	throw std::domain_error("invalid Cahill-Keyes octant");
      }
    result.y += y_translate;
    return result;
  }

  /// Derive all scale-dependent control points and segment lengths.
  void
  calculate_preliminaries()
  {
    const xy point_n {length_mg, length_mg * std::tan(30 * radians)};
    point_b = line_intersection(point_m, 30, point_a, 45);
    length_ab = distance(point_a, point_b);
    const double length_mb = distance(point_m, point_b);
    const double length_mn = distance(point_m, point_n);
    point_d = interpolate(length_mb, length_mn, point_n, point_m);
    point_f = {length_mg, point_n.y - length_mb};
    point_e = {point_n.x - length_ma * std::sin(30 * radians),
	       point_n.y - length_ma * std::cos(30 * radians)};
    length_gf = distance(point_g, point_f);
    delta_m_equator = (length_gf + length_ab) / 45;

    const xy point_u {point_a.x + length_ap_73 * std::cos(30 * radians),
		      point_a.y + length_ap_73 * std::sin(30 * radians)};
    point_t = line_intersection(point_u, -60, point_b, 30);

    constexpr double m = 29;
    constexpr double p = 15;
    const parallel_73_result p73 = parallel_73(m);
    const double lt = torrid_length(m);
    const double lm = middle_length(m);
    double length = p * (lt + lm + p73.length) / 73 - lt;
    const xy point_v = interpolate(length, lm, joint_t(m), joint_f(m));
    const double root_three = std::sqrt(3.0);
    point_c.y = (point_v.x * point_v.x + point_v.y * point_v.y
		 - point_d.x * point_d.x - point_d.y * point_d.y)
		/ (2 * (root_three * point_v.x + point_v.y
			- root_three * point_d.x - point_d.y));
    point_c.x = root_three * point_c.y;
    radius = distance(point_c, point_d);
  }

public:
  /// Construct the native projection at a requested scaffold scale.
  /// @param scaffold_altitude Positive M-G scaffold altitude in output units.
  /// @throws std::invalid_argument if the altitude is non-finite or non-positive.
  explicit
  forward_projection(const double scaffold_altitude)
  : length_mg(scaffold_altitude),
    scale(scaffold_altitude / 10000.0),
    length_ma(940 * scale),
    latitude_degree_100(100 * scale),
    latitude_degree_104(104 * scale),
    y_translate(scaffold_altitude * sin_60),
    point_g {scaffold_altitude, 0},
    point_a {length_ma, 0},
    length_ap_73(1760 * scale),
    length_ap_75(1560 * scale)
  {
    if (!std::isfinite(scaffold_altitude) || scaffold_altitude <= 0)
      throw std::invalid_argument(
	"Cahill-Keyes scaffold altitude must be positive");
    calculate_preliminaries();
  }

  /// Convert `(longitude, latitude)` in degrees to centered Megamap `(x, y)`.
  /// @param longitude Registered longitude in degrees, in `[-180, 180]`.
  /// @param latitude Latitude in degrees, in `[-90, 90]`.
  /// @return Centered native Megamap coordinate.
  /// @throws std::invalid_argument if either input is non-finite or out of
  /// range.
  std::pair<double, double>
  operator()(const double longitude, const double latitude) const
  {
    if (!std::isfinite(latitude) || latitude < -90 || latitude > 90)
      throw std::invalid_argument(
	"Cahill-Keyes latitude must be within [-90, 90]");
    if (!std::isfinite(longitude) || longitude < -180 || longitude > 180)
      throw std::invalid_argument(
	"Cahill-Keyes longitude must be within [-180, 180]");

    const meridian mp = longitude_latitude_to_meridian(longitude, latitude);
    xy point = meridian_parallel_to_xy(mp.value, mp.parallel);
    point.y *= mp.sign;
    point = half_octant_to_megamap(point, mp.octant);
    return {point.x, point.y};
  }
};

} // namespace a60::carto::ck_native

namespace a60::carto {

/// Apply the one-degree longitude registration shared by the project’s
/// Cahill-Keyes raster family and rearrangements of that registered net.
/// @param longitude Geographic longitude in degrees.
/// @return Registered longitude in `(-180, 180]`.
inline double
cahill_keyes_registered_longitude(const double longitude)
{
  double adjusted = longitude + 1;
  if (adjusted > 180)
    adjusted -= 360;
  return adjusted;
}

/// Required width-to-height ratio of the complete Cahill-Keyes M-layout.
inline constexpr double cahill_keyes_width_to_height_ratio = 2.0;

/// True when a frame has finite, positive dimensions in the required 2:1
/// Cahill-Keyes aspect ratio. The tolerance admits floating-point roundoff,
/// not approximate aspect ratios.
/// @param candidate Frame to validate.
/// @return `true` when the dimensions are finite, positive, and ratio-correct.
inline bool
is_cahill_keyes_frame(const frame& candidate)
{
  const double width = candidate.width();
  const double height = candidate.height();
  if (!std::isfinite(width) || !std::isfinite(height)
      || width <= 0 || height <= 0)
    return false;

  const double expected_width = cahill_keyes_width_to_height_ratio * height;
  const double tolerance = 16 * std::numeric_limits<double>::epsilon()
			   * std::max(width, expected_width);
  return std::abs(width - expected_width) <= tolerance;
}

/// Validate generic projection state for use by Cahill-Keyes.
/// @param value Projection state to validate and return.
/// @return The validated projection state.
/// @throws std::invalid_argument if its frame does not have a 2:1 ratio.
inline projection_base
validate_cahill_keyes_projection_base(projection_base value)
{
  if (!is_cahill_keyes_frame(value.pframe))
    throw std::invalid_argument(
      "Cahill-Keyes projection frame must have finite, positive dimensions "
      "with a 2:1 width-to-height ratio");
  return value;
}

/// Construct generic projection state from a variable-size map frame.
/// The projection origin is the center of frame.frame_area.
/// @param map_frame Valid 2:1 output frame.
/// @param raster_name Optional registered raster filename.
/// @return Validated generic projection state centered in the frame.
inline projection_base
make_cahill_keyes_projection_base(const frame& map_frame, string raster_name)
{
  return validate_cahill_keyes_projection_base(
    {map_frame, map_frame.width() / 2, map_frame.height() / 2,
     cahill_keyes, std::move(raster_name)});
}

/**
   Cahill-Keyes projection.

   https://en.wikipedia.org/wiki/Gene_Keyes
   http://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-&-coastline.html
   https://gist.github.com/espinielli/4259835
   https://observablehq.com/@fil/cahill-keyes-projection
*/
struct ckproj : public projection_base, public projection_api
{
  /// Scale-specific native forward transform.
  ck_native::forward_projection forward;

  /// Construct from generic projection state.
  /// @param value State with a valid 2:1 frame.
  ckproj(const projection_base value)
  : projection_base(validate_cahill_keyes_projection_base(value)),
    forward(pframe.height() / 2)
  { }

  /// Make a projection for any valid 2:1 map frame. The raster name is kept
  /// separate from size so one projection implementation fits every scale.
  /// @param map_frame Ratio-correct output frame.
  /// @param raster_name Optional registered raster filename.
  explicit
  ckproj(const frame& map_frame, string raster_name = {})
  : ckproj(make_cahill_keyes_projection_base(map_frame,
					      std::move(raster_name)))
  { }

  /// Copy a Cahill-Keyes projection.
  /// @param other Projection to copy.
  ckproj(const ckproj& other) = default;

  /// Resolve the registered raster against the generated PNG directory.
  /// @param v Raster mode retained for projection API compatibility.
  /// @return Full path to the generated PNG.
  string
  image_filename([[maybe_unused]] const raster_mode v) const override
  {
    const string prefix = "/home/bkoz/src/cartofreako/assets.generated/png/";
    string ret = prefix + name;
    return ret + ".png";
  }

  /// Native C++20 forward projection. The one-degree longitude adjustment
  /// preserves registration with the existing visionscarto raster; the Perl
  /// octant formula itself uses its documented -20/70/160 degree boundaries.
  /// @param lt Latitude in degrees, in `[-90, 90]`.
  /// @param lng Longitude in degrees, in `[-180, 180]`.
  /// @return Output-frame coordinate in screen-axis orientation.
  /// @throws std::invalid_argument if either coordinate is non-finite or out
  /// of range.
  a60::point_2t
  meridians_to_point_2d(const double lt, const double lng) const override
  {
    const double adjusted_longitude
      = cahill_keyes_registered_longitude(lng);
    const auto [ckx, cky] = forward(adjusted_longitude, lt);
    return std::make_tuple(longitude_zero_x + ckx, latitude_zero_y - cky);
  }
};

/// Construct a variable-size Cahill-Keyes projection.
/// @param map_frame Ratio-correct output frame.
/// @param raster_name Optional registered raster filename.
/// @return Configured Cahill-Keyes projection.
inline ckproj
make_cahill_keyes_projection(const frame& map_frame,
			     string raster_name = {})
{
  return ckproj(map_frame, std::move(raster_name));
}


/**
   Cahill-Keyes-as-per visionscarto.net's Cahill-Keyes Projection.

   vc.net == visioncarto.net
   https://vc.net/carte-di-base
   https://vc.net/public/fonds-de-cartes-it/visionscarto-cahillkeyes.svg

   https://observablehq.com/@fil/cahill-keyes-projection

   In the Cahill-Keyes octant assembly, y is the distance from the
   equator to the north pole, -y is the distance from the equator to
   the south pole, and the total circumfrence of the globe is a
   distance of 4y.

   For rendering to screen with this projection, derive y via
   4y = projection.width

   Since the rendered images are full-width but not full-height (for
   the octant grid where 2y = height.
*/

/// Single-scale 1080p Cahill-Keyes raster preset.
const ckproj ck_1x1080{
  pck_1x1080, "visionscarto-cahillkeyes-1080p-1x.096"};

/// Double-scale 1080p Cahill-Keyes raster preset.
const ckproj ck_2x1080{
  pck_2x1080, "visionscarto-cahillkeyes-1080p-2x.096"};


/// ENGC

/// Single-scale 22-by-17-inch Engineering C landscape preset.
const ckproj ck_1xengc{
  frame {2112, 1056}, "visionscarto-cahillkeyes-engc-1x.096"};

/// Double-scale 44-by-17-inch Engineering C landscape preset.
const ckproj ck_2xengc{
  frame {4224, 2112}, "visionscarto-cahillkeyes-engc-2x-v3.300"};

/// Four-sheet 44-by-34-inch Engineering C landscape preset.
const ckproj ck_4xengc{
  frame {8448, 4224}, "visionscarto-cahillkeyes-engc-4x.096"};

/// 96-DPI four-slice Engineering C portrait preset.
const ckproj ck96_2bisx{
  frame {5280, 2640}, "visionscarto-cahillkeyes-engc-2.5x.096"};
/// 300-DPI four-slice Engineering C portrait preset.
const ckproj ck300_2bisx{
  frame {16500, 8250}, "visionscarto-cahillkeyes-engc-2.5x.300"};

/// 96-DPI legacy four-sheet Star-X raster preset.
const ckproj ck96_starx_engc{
  pck_7x, "visionscarto-cahillkeyes-engc-7.3x-starx.096"};
/// 300-DPI legacy four-sheet Star-X raster preset.
const ckproj ck300_starx_engc{
  pck_7x, "visionscarto-cahillkeyes-engc-7.3x-starx.300"};

/// Legacy four-sheet A5 Star-X raster preset.
const ckproj ck96_starx_a5{
  pck_3x, "visionscarto-cahillkeyes-a5-3x-starx"};

/// 44-by-22-inch Cahill-Keyes raster preset.
const ckproj ck_44x22{
  f44x22h, "visionscarto-cahillkeyes-44x22.300"};


/// Horizontal tile offsets for the double-scale Engineering C preset.
const vd tiles_ck_2xengc_h = { 0, -2112 };
/// Vertical tile offsets for the double-scale Engineering C preset.
const vd tiles_ck_2xengc_v = { -240 };

/// Horizontal tile offsets for the double-scale 1080p preset.
const vd tiles_ck_2x1080p_h = { 0, -1920 };
/// Vertical tile offsets for the double-scale 1080p preset.
const vd tiles_ck_2x1080p_v = { -280 };

/// Horizontal four-slice offsets; `xoff - n * 1320` for `n >= 1`.
const vd tiles_ck_2bisx_h = { 156, -1164, -2484, -3804 };
/// Primary vertical tile offset for the four-slice preset.
const vd tiles_ck_2bisx_v = { -265 };
/// Alternate vertical tile offsets for the four-slice preset.
const vd tiles_ck_2bisx_v2 = { -126, -886 };

/// Horizontal tile offsets for the four-sheet Engineering C preset.
const vd tiles_ck_4x_h = { -6208, -1754, -4570 };
/// Vertical tile offsets for the four-sheet Engineering C preset.
const vd tiles_ck_4x_v = { 19 };

/// Horizontal tile offsets for the 44-by-22 four-sheet preset.
const vd tiles_ck_4x44x22_h = { 0, -1056, -2112, -3168 };
/// Vertical tile offsets for the 44-by-22 four-sheet preset.
const vd tiles_ck_4x44x22_v = { 19 };

/// Horizontal tile offsets for the Engineering C Star-X raster.
const vd tiles_ck_starx_engc_h = { 378, -1254, -2098, -3728 };
/// Vertical tile offsets for the Engineering C Star-X raster.
const vd tiles_ck_starx_engc_v = { -190 };

/// Horizontal tile offsets for the A5 Star-X raster.
const vd tiles_ck_starx_a5_h = { 57, -503, -939, -1500 };
/// Vertical tile offsets for the A5 Star-X raster.
const vd tiles_ck_starx_a5_v = { -104 };

} // namespace carto

#endif

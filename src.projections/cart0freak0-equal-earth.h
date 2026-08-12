// Equal Earth experimental projection support. -*- mode: C++ -*-

// Copyright (c) 2026, Benjamin De Kosnik <b.dekosnik@gmail.com>

// This file is part of Cartofreako.  Cartofreako is free software; you can
// redistribute it and/or modify it under the terms of the GNU General Public
// License as published by the Free Software Foundation; either version 3, or
// (at your option) any later version.

/**
 * @file cart0freak0-equal-earth.h
 * @brief Spherical Equal Earth forward/reverse equations and page mapping.
 *
 * This header is deliberately independent of Cartofreako's six-family atlas
 * runtime.  Equal Earth is a Stage 16J comparison method, not a seventh
 * standard release carrier.  Angles accepted by the raw functions are in
 * radians; the page wrapper accepts longitude/latitude in degrees.
 */

#ifndef CART0FREAK0_EQUAL_EARTH_H
#define CART0FREAK0_EQUAL_EARTH_H 1

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace a60::carto::equal_earth {

inline constexpr double pi
  = 3.141592653589793238462643383279502884;
inline constexpr double radians_per_degree = pi / 180;
inline constexpr double degrees_per_radian = 180 / pi;

// Šavrič, Patterson, and Jenny (2018), spherical Equal Earth coefficients.
inline constexpr double a1 = 1.340264;
inline constexpr double a2 = -0.081106;
inline constexpr double a3 = 0.000893;
inline constexpr double a4 = 0.003796;
inline constexpr double m = 0.866025403784438646763723170752936183;
inline constexpr unsigned int inverse_iterations = 12;

struct point
{
  double x;
  double y;
};

struct geographic_coordinate
{
  double longitude_degrees;
  double latitude_degrees;
};

enum class inverse_status
{
  unique,
  outside,
};

struct inverse_result
{
  inverse_status status = inverse_status::outside;
  geographic_coordinate coordinate {
    std::numeric_limits<double>::quiet_NaN(),
    std::numeric_limits<double>::quiet_NaN(),
  };
  double forward_residual = std::numeric_limits<double>::infinity();
};

inline double
clamp_unit(const double value)
{ return std::clamp(value, -1.0, 1.0); }

inline double
canonical_longitude_degrees(double value)
{
  while (value > 180)
    value -= 360;
  while (value < -180)
    value += 360;
  return value;
}

inline double
relative_longitude_radians(const double longitude_degrees,
                           const double central_meridian_degrees)
{
  return canonical_longitude_degrees(
           longitude_degrees - central_meridian_degrees)
         * radians_per_degree;
}

inline point
forward_raw(const double longitude_radians, const double latitude_radians)
{
  const double theta = std::asin(m * std::sin(latitude_radians));
  const double theta2 = theta * theta;
  const double theta6 = theta2 * theta2 * theta2;
  const double derivative
    = a1 + 3 * a2 * theta2
      + theta6 * (7 * a3 + 9 * a4 * theta2);
  return {
    longitude_radians * std::cos(theta) / (m * derivative),
    theta * (a1 + a2 * theta2
             + theta6 * (a3 + a4 * theta2)),
  };
}

inline point
inverse_raw(const double x, const double y)
{
  double theta = y;
  for (unsigned int index = 0; index < inverse_iterations; ++index)
    {
      const double theta2 = theta * theta;
      const double theta6 = theta2 * theta2 * theta2;
      const double value
        = theta * (a1 + a2 * theta2
                   + theta6 * (a3 + a4 * theta2)) - y;
      const double derivative
        = a1 + 3 * a2 * theta2
          + theta6 * (7 * a3 + 9 * a4 * theta2);
      const double delta = value / derivative;
      theta -= delta;
      if (std::abs(delta) < 1e-12)
        break;
    }
  const double theta2 = theta * theta;
  const double theta6 = theta2 * theta2 * theta2;
  const double derivative
    = a1 + 3 * a2 * theta2
      + theta6 * (7 * a3 + 9 * a4 * theta2);
  return {
    m * x * derivative / std::cos(theta),
    std::asin(clamp_unit(std::sin(theta) / m)),
  };
}

inline const double raw_x_maximum = forward_raw(pi, 0).x;
inline const double raw_y_maximum = forward_raw(0, pi / 2).y;
inline const double native_aspect = raw_x_maximum / raw_y_maximum;

/** A full-world Equal Earth page with a top-left origin and downward y. */
class projection
{
public:
  explicit projection(const double width = 1920,
                      const double central_meridian_degrees = 0)
  : width_(width), height_(width / native_aspect),
    central_meridian_degrees_(central_meridian_degrees)
  {
    if (!std::isfinite(width_) || width_ <= 0
        || !std::isfinite(central_meridian_degrees_))
      throw std::invalid_argument(
        "Equal Earth width must be positive and parameters finite");
    central_meridian_degrees_
      = canonical_longitude_degrees(central_meridian_degrees_);
  }

  double width() const { return width_; }
  double height() const { return height_; }
  double central_meridian_degrees() const
  { return central_meridian_degrees_; }

  point
  forward(const geographic_coordinate coordinate) const
  {
    if (!std::isfinite(coordinate.longitude_degrees)
        || !std::isfinite(coordinate.latitude_degrees)
        || coordinate.latitude_degrees < -90
        || coordinate.latitude_degrees > 90)
      throw std::invalid_argument(
        "Equal Earth requires finite longitude and latitude in [-90, 90]");
    const point raw = forward_raw(
      relative_longitude_radians(coordinate.longitude_degrees,
                                 central_meridian_degrees_),
      coordinate.latitude_degrees * radians_per_degree);
    return {
      (raw.x + raw_x_maximum) * width_ / (2 * raw_x_maximum),
      (raw_y_maximum - raw.y) * height_ / (2 * raw_y_maximum),
    };
  }

  inverse_result
  inverse(const point page, const double tolerance_pixels = 1e-8) const
  {
    if (!std::isfinite(page.x) || !std::isfinite(page.y)
        || page.x < -tolerance_pixels
        || page.y < -tolerance_pixels
        || page.x > width_ + tolerance_pixels
        || page.y > height_ + tolerance_pixels)
      return {};

    const double raw_x
      = page.x * (2 * raw_x_maximum) / width_ - raw_x_maximum;
    const double raw_y
      = raw_y_maximum - page.y * (2 * raw_y_maximum) / height_;
    const point angular = inverse_raw(raw_x, raw_y);
    const double angular_tolerance
      = 64 * std::numeric_limits<double>::epsilon();
    if (!std::isfinite(angular.x) || !std::isfinite(angular.y)
        || std::abs(angular.x) > pi + angular_tolerance
        || std::abs(angular.y) > pi / 2 + angular_tolerance)
      return {};

    const geographic_coordinate coordinate {
      canonical_longitude_degrees(
        angular.x * degrees_per_radian + central_meridian_degrees_),
      angular.y * degrees_per_radian,
    };
    const point round_trip = forward(coordinate);
    const double ordinary_residual
      = std::hypot(round_trip.x - page.x, round_trip.y - page.y);
    // A canonical longitude cannot retain which duplicate antimeridian edge
    // supplied it. Accept the equivalent edge without weakening interior
    // residual checks.
    const double seam_residual
      = std::hypot(std::abs(round_trip.x - page.x) - width_,
                   round_trip.y - page.y);
    const double residual = std::abs(std::abs(angular.x) - pi)
                              <= angular_tolerance
                            ? std::min(ordinary_residual,
                                       std::abs(seam_residual))
                            : ordinary_residual;
    if (residual > std::max(tolerance_pixels, 1e-7))
      return {};
    return {inverse_status::unique, coordinate, residual};
  }

private:
  double width_;
  double height_;
  double central_meridian_degrees_;
};

} // namespace a60::carto::equal_earth

#endif // CART0FREAK0_EQUAL_EARTH_H

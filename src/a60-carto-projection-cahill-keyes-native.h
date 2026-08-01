// alpha60 native Cahill-Keyes forward projection -*- mode: C++ -*-

// Copyright (c) 2026 Benjamin De Kosnik <b.dekosnik@gmail.com>
//
// Derived from MegamapMaker-prep9.pl by Mary Jo Graca and Gene Keyes.
// The original algorithm is distributed for non-commercial use with
// attribution; commercial users should contact Gene Keyes.

#ifndef a60_CARTOGRAPHY_PROJECTION_CK_NATIVE_H
#define a60_CARTOGRAPHY_PROJECTION_CK_NATIVE_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <numbers>
#include <stdexcept>
#include <utility>

namespace a60::carto::ck_native {

/// Native forward Cahill-Keyes projection in scalable Megamap units.
class forward_projection
{
  struct xy
  {
    double x = 0;
    double y = 0;
  };

  struct circle_intersection
  {
    bool intersects = false;
    xy point;
  };

  struct parallel_73_result
  {
    xy point;
    double length = 0;
  };

  struct meridian
  {
    double value = 0;
    double parallel = 0;
    double sign = 1;
    int octant = 1;
  };

  static constexpr double pi = std::numbers::pi_v<double>;
  static constexpr double radians = pi / 180.0;

  double length_mg;
  double scale;
  double length_ma;
  double latitude_degree_100;
  double latitude_degree_104;
  double sin_60 = std::sqrt(3.0) / 2.0;
  double cos_60 = 0.5;
  double y_translate;

  xy point_m {0, 0};
  xy point_g;
  xy point_a;
  xy point_b;
  xy point_c;
  xy point_d;
  xy point_e;
  xy point_f;
  xy point_t;

  double length_ab = 0;
  double length_gf = 0;
  double delta_m_equator = 0;
  double length_ap_73 = 0;
  double length_ap_75 = 0;
  double radius = 0;

  static double
  distance(const xy a, const xy b)
  {
    return std::hypot(a.x - b.x, a.y - b.y);
  }

  static xy
  interpolate(const double length, const double total, const xy start,
              const xy end)
  {
    if (total == 0)
      throw std::domain_error("Cahill-Keyes interpolation over a zero-length segment");
    const double ratio = length / total;
    return {start.x + (end.x - start.x) * ratio,
            start.y + (end.y - start.y) * ratio};
  }

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

  xy
  equator(const double m) const
  {
    double length = delta_m_equator * m;
    if (length <= length_gf)
      return {point_g.x, length};
    length -= length_gf;
    return interpolate(length, length_ab, point_f, point_e);
  }

  xy
  joint_t(const double m) const
  {
    return line_intersection(point_m, 2 * m / 3, equator(m), m / 3);
  }

  xy
  joint_f(const double m) const
  {
    if (m == 0)
      return {point_a.x + length_ab, 0};
    return line_intersection(point_a, m, point_m, 2 * m / 3);
  }

  double
  torrid_length(const double m) const
  { return distance(equator(m), joint_t(m)); }

  double
  middle_length(const double m) const
  { return distance(joint_t(m), joint_f(m)); }

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

  xy
  parallel_75(const double m) const
  {
    return {point_a.x + length_ap_75 * std::cos(m * radians),
            point_a.y + length_ap_75 * std::sin(m * radians)};
  }

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

  xy
  zone_k(const double m, const double p, const double length_15) const
  {
    double length = p * length_15 / 15;
    const double lt = torrid_length(m);
    if (length <= lt)
      return interpolate(length, lt, equator(m), joint_t(m));
    return interpolate(length - lt, middle_length(m), joint_t(m), joint_f(m));
  }

  xy
  zone_l(const double m, const double p, const double length_15) const
  {
    const parallel_73_result p73 = parallel_73(m);
    const double lt = torrid_length(m);
    const double lm = middle_length(m);
    double length = length_15 + (p - 15) * ((lt + lm + p73.length) - length_15) / 58;
    if (length <= lt)
      return interpolate(length, lt, equator(m), joint_t(m));
    if (length <= lt + lm)
      return interpolate(length - lt, lm, joint_t(m), joint_f(m));
    return interpolate(length - lt - lm, p73.length, joint_f(m), p73.point);
  }

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
        const double length = length_ap_75 + (75 - p) * latitude_degree_100;
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
          throw std::domain_error("Cahill-Keyes parallel 15 misses its meridian");
        length_15 = lt - distance(jt, p15.point);
      }
    return p <= 15 ? zone_k(m, p, length_15)
                   : zone_l(m, p, length_15);
  }

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
      throw std::invalid_argument("Cahill-Keyes scaffold altitude must be positive");
    calculate_preliminaries();
  }

  /// Convert (longitude, latitude) in degrees to Megamap (x, y).
  std::pair<double, double>
  operator()(const double longitude, const double latitude) const
  {
    if (!std::isfinite(latitude) || latitude < -90 || latitude > 90)
      throw std::invalid_argument("Cahill-Keyes latitude must be within [-90, 90]");
    if (!std::isfinite(longitude) || longitude < -180 || longitude > 180)
      throw std::invalid_argument("Cahill-Keyes longitude must be within [-180, 180]");

    const meridian mp = longitude_latitude_to_meridian(longitude, latitude);
    xy point = meridian_parallel_to_xy(mp.value, mp.parallel);
    point.y *= mp.sign;
    point = half_octant_to_megamap(point, mp.octant);
    return {point.x, point.y};
  }
};

} // namespace a60::carto::ck_native

#endif

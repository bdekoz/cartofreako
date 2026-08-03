#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include <s2/s2latlng.h>
#include <s2/s2loop.h>
#include <s2/s2polygon.h>

struct point
{
  double x;
  double y;
  double z;
};

using face = std::array<point, 3>;

point
normalized(point value)
{
  const double magnitude = std::sqrt(value.x * value.x
                                     + value.y * value.y
                                     + value.z * value.z);
  value.x /= magnitude;
  value.y /= magnitude;
  value.z /= magnitude;
  return value;
}

point
midpoint(const point& left, const point& right)
{
  return normalized({(left.x + right.x) / 2,
                     (left.y + right.y) / 2,
                     (left.z + right.z) / 2});
}

std::vector<face>
make_faces()
{
  constexpr double tau = 0.8506508084;
  constexpr double one = 0.5257311121;
  const point za {tau, one, 0};
  const point zb {-tau, one, 0};
  const point zc {-tau, -one, 0};
  const point zd {tau, -one, 0};
  const point ya {one, 0, tau};
  const point yb {one, 0, -tau};
  const point yc {-one, 0, -tau};
  const point yd {-one, 0, tau};
  const point xa {0, tau, one};
  const point xb {0, -tau, one};
  const point xc {0, -tau, -one};
  const point xd {0, tau, -one};
  std::vector<face> faces {
    {ya, xa, yd}, {ya, yd, xb}, {yb, yc, xd}, {yb, xc, yc},
    {za, ya, zd}, {za, zd, yb}, {zc, yd, zb}, {zc, zb, yc},
    {xa, za, xd}, {xa, xd, zb}, {xb, xc, zd}, {xb, zc, xc},
    {xa, ya, za}, {xd, za, yb}, {ya, xb, zd}, {yb, zd, xc},
    {yd, xa, zb}, {yc, zb, xd}, {yd, zc, xb}, {yc, xc, zc},
  };
  for (int level = 1; level < 5; ++level)
    {
      std::vector<face> children;
      children.reserve(faces.size() * 4);
      for (const auto& value : faces)
        {
          const point a = midpoint(value[0], value[2]);
          const point b = midpoint(value[0], value[1]);
          const point c = midpoint(value[1], value[2]);
          children.push_back({value[0], b, a});
          children.push_back({b, value[1], c});
          children.push_back({a, b, c});
          children.push_back({a, c, value[2]});
        }
      faces = std::move(children);
    }
  return faces;
}

S2Point
to_s2(const point& value)
{
  return S2Point(value.x, value.y, value.z);
}

struct country
{
  std::string name;
  std::unique_ptr<S2Polygon> polygon;
  S2LatLngRect bounds;
};

std::vector<country>
read_countries(const std::string& filename)
{
  std::ifstream stream(filename);
  std::size_t count = 0;
  stream >> count;
  stream.ignore();
  std::vector<country> result;
  result.reserve(count);
  for (std::size_t country_index = 0; country_index < count; ++country_index)
    {
      std::string name;
      std::getline(stream, name);
      std::size_t polygon_count = 0;
      stream >> polygon_count;
      std::vector<S2Polygon*> polygons;
      polygons.reserve(polygon_count);
      for (std::size_t polygon_index = 0;
           polygon_index < polygon_count; ++polygon_index)
        {
          std::size_t point_count = 0;
          stream >> point_count;
          std::vector<S2Point> points;
          points.reserve(point_count);
          for (std::size_t point_index = 0;
               point_index < point_count; ++point_index)
            {
              double longitude = 0;
              double latitude = 0;
              stream >> longitude >> latitude;
              points.push_back(S2LatLng::FromDegrees(
                latitude, longitude).Normalized().ToPoint());
            }
          std::reverse(points.begin(), points.end());
          auto* loop = new S2Loop(points);
          if (loop->GetArea() > 10)
            {
              delete loop;
              std::reverse(points.begin(), points.end());
              loop = new S2Loop(points);
            }
          std::vector<S2Loop*> loops {loop};
          polygons.push_back(new S2Polygon(&loops));
        }
      std::unique_ptr<S2Polygon> value(
        S2Polygon::DestructiveUnion(&polygons));
      const S2LatLngRect bounds = value->GetRectBound();
      result.push_back({std::move(name), std::move(value), bounds});
      stream.ignore();
    }
  return result;
}

int
special_bit(const std::string& name)
{
  static const std::array<std::string, 6> names {
    "Indonesia", "Australia", "Greenland",
    "New Zealand", "Argentina", "Chile",
  };
  const auto found = std::find(names.begin(), names.end(), name);
  return found == names.end() ? 0 : 1 << (found - names.begin());
}

int
main(int argc, char** argv)
{
  if (argc != 3)
    return 2;
  const auto countries = read_countries(argv[1]);
  const auto faces = make_faces();
  std::ofstream output(argv[2]);
  output << std::setprecision(17);
  for (std::size_t index = 0; index < faces.size(); ++index)
    {
      std::vector<S2Point> vertices;
      for (const point& value : faces[index])
        vertices.push_back(to_s2(value));
      auto* loop = new S2Loop(vertices);
      std::vector<S2Loop*> loops {loop};
      S2Polygon triangle(&loops);
      const double triangle_area = triangle.GetArea();
      const S2Point centroid = triangle.GetCentroid();
      const S2LatLng center(centroid);
      const S2LatLngRect triangle_bounds = triangle.GetRectBound();
      double land_area = 0;
      int special = 0;
      for (const auto& value : countries)
        {
          if (!triangle_bounds.Intersects(value.bounds))
            continue;
          S2Polygon intersection;
          intersection.InitToIntersection(value.polygon.get(), &triangle);
          if (intersection.num_loops() == 0)
            continue;
          land_area += intersection.GetArea();
          special |= special_bit(value.name);
        }
      const double fraction = std::clamp(
        land_area / (triangle_area + 0.0000001), 0.0, 1.0);
      output << index << ' ' << fraction << ' ' << triangle_area << ' '
             << center.lng().degrees() << ' ' << center.lat().degrees()
             << ' ' << special << '\n';
      if (index % 256 == 0)
        std::cerr << index << '/' << faces.size() << '\n';
    }
}

#include <algorithm>
#include <array>
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/breadth_first_search.hpp>
#include <boost/graph/prim_minimum_spanning_tree.hpp>
#include <boost/property_map/property_map.hpp>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

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

struct vertex_data
{
  double fraction {};
  double area {};
  double longitude {};
  double latitude {};
  int special {};
};

struct edge_data
{
  double weight {};
  int shared_vertices {};
};

using graph = boost::adjacency_list<boost::listS, boost::vecS,
                                    boost::undirectedS,
                                    vertex_data, edge_data>;
using vertex = boost::graph_traits<graph>::vertex_descriptor;

std::array<long long, 3>
point_key(const point& value)
{
  constexpr double scale = 1e12;
  return {std::llround(value.x * scale),
          std::llround(value.y * scale),
          std::llround(value.z * scale)};
}

graph
make_graph(const std::vector<face>& faces)
{
  graph result(faces.size());
  std::map<std::array<long long, 3>, std::vector<vertex>> uses;
  for (vertex current = 0; current < faces.size(); ++current)
    for (const point& value : faces[current])
      {
        auto& previous = uses[point_key(value)];
        for (const vertex other : previous)
          {
            const auto existing = boost::edge(other, current, result);
            if (existing.second)
              ++result[existing.first].shared_vertices;
            else
              {
                const auto added = boost::add_edge(other, current, result);
                result[added.first].shared_vertices = 1;
              }
          }
        previous.push_back(current);
      }
  boost::remove_edge_if(
    [&](const auto& edge)
    { return result[edge].shared_vertices < 2; }, result);
  return result;
}

point
geographic_vector(const vertex_data& value)
{
  constexpr double pi = 3.141592653589793238462643383279502884;
  const double longitude = value.longitude * pi / 180;
  const double latitude = value.latitude * pi / 180;
  const double cosine = std::cos(latitude);
  return {cosine * std::cos(longitude),
          cosine * std::sin(longitude),
          std::sin(latitude)};
}

double
distance(const vertex_data& left, const vertex_data& right)
{
  const point a = geographic_vector(left);
  const point b = geographic_vector(right);
  return std::acos(std::clamp(
    a.x * b.x + a.y * b.y + a.z * b.z, -1.0, 1.0));
}

struct max_depth_reached {};

struct gaussian_visitor : boost::default_bfs_visitor
{
  const vertex_data* center;
  double* sum;
  double* weight_sum;
  double sigma;

  template<typename Vertex, typename Graph>
  void
  examine_vertex(const Vertex current, const Graph& value) const
  {
    const double separation = distance(*center, value[current]);
    if (separation > 3.141592653589793238462643383279502884 / 2)
      throw max_depth_reached {};
    const double weight = std::exp(
      -separation * separation / (sigma * sigma));
    if (weight < 1e-3)
      throw max_depth_reached {};
    *sum += weight * value[current].area * value[current].fraction;
    *weight_sum += weight * value[current].area;
  }
};

void
smooth(graph& value, const double sigma)
{
  for (const auto edge : boost::make_iterator_range(boost::edges(value)))
    value[edge].weight = 1;
  std::vector<double> result(boost::num_vertices(value));
  for (const vertex start : boost::make_iterator_range(boost::vertices(value)))
    {
      double sum = 0;
      double weight_sum = 0;
      const gaussian_visitor visitor {
        {}, &value[start], &sum, &weight_sum, sigma
      };
      try
        {
          boost::breadth_first_search(value, start,
                                      boost::visitor(visitor));
        }
      catch (const max_depth_reached&)
        { }
      result[start] = std::max(0.0, sum / (weight_sum + 0.000001));
    }
  for (vertex current = 0; current < result.size(); ++current)
    value[current].fraction = result[current];
}

void
weight_edges(graph& value, const double wlat, const double wlon,
             const double clat, const double clon)
{
  for (vertex current = 0; current < boost::num_vertices(value); ++current)
    {
      const int special = value[current].special;
      if ((special & ((1 << 0) | (1 << 1) | (1 << 2)
                      | (1 << 4) | (1 << 5))) != 0)
        value[current].fraction *= 2;
      if ((special & (1 << 3)) != 0)
        value[current].fraction *= 5;
    }
  for (const auto edge : boost::make_iterator_range(boost::edges(value)))
    {
      const vertex source = boost::source(edge, value);
      const vertex target = boost::target(edge, value);
      const double fraction
        = (value[source].fraction * value[source].area
           + value[target].fraction * value[target].area)
          / (value[source].area + value[target].area);
      const double longitude_distance
        = std::abs(value[source].longitude - clat) / 180;
      const double latitude_distance
        = std::abs(value[source].latitude - clon) / 90;
      const double norm = wlat * longitude_distance * longitude_distance
                          + wlon * latitude_distance * latitude_distance;
      value[edge].weight = std::exp(
        (1 - fraction) * (1 - fraction) * norm);
    }
}

vertex
root_vertex(const graph& value)
{
  vertex closest = 0;
  vertex_data destination;
  destination.longitude = 88;
  destination.latitude = 46;
  double closest_distance = distance(value[0], destination);
  for (vertex current = 1; current < boost::num_vertices(value); ++current)
    {
      const double candidate = distance(value[current], destination);
      if (candidate < closest_distance)
        {
          closest_distance = candidate;
          closest = current;
        }
    }
  return closest;
}

void
write_weighted_tree(graph value, const std::string& filename,
                    const double wlat, const double wlon,
                    const double clat, const double clon)
{
  weight_edges(value, wlat, wlon, clat, clon);
  const vertex root = root_vertex(value);
  std::vector<vertex> parent(boost::num_vertices(value));
  auto weight_map = boost::get(&edge_data::weight, value);
  boost::prim_minimum_spanning_tree(
    value, parent.data(), boost::root_vertex(root).weight_map(weight_map));
  std::ofstream stream(filename);
  stream << root << '\n';
  for (vertex current = 0; current < parent.size(); ++current)
    stream << current << ' ' << parent[current] << '\n';
}

void
write_tree(graph value, const std::string& filename,
           const double sigma, const double wlat, const double wlon,
           const double clat, const double clon)
{
  smooth(value, sigma);
  write_weighted_tree(value, filename, wlat, wlon, clat, clon);
}

int
main(int argc, char** argv)
{
  if (argc != 3)
    return 2;
  const auto faces = make_faces();
  graph original = make_graph(faces);
  std::ifstream input(argv[1]);
  for (vertex current = 0; current < boost::num_vertices(original); ++current)
    {
      std::size_t index = 0;
      input >> index >> original[current].fraction >> original[current].area
            >> original[current].longitude >> original[current].latitude
            >> original[current].special;
      if (index != current)
        return 3;
    }
  std::cerr << boost::num_vertices(original) << " vertices, "
            << boost::num_edges(original) << " edges\n";
  const std::string prefix(argv[2]);
  write_tree(original, prefix + "-04-origin.tree", .4, .1, .5, 0, 0);
  write_tree(original, prefix + "-04-defaults.tree", .4, .1, .5, 53, 10);
  write_tree(original, prefix + "-04-preoptions.tree", .4, .1, .5, 10, 10);
  write_tree(original, prefix + "-04-experimental.tree", .4, .1, .5, 12, 0);
  write_tree(original, prefix + "-04-readme.tree", .4, .1, 3, 313, -65);
  write_tree(original, prefix + "-07-origin.tree", .7, .1, .5, 0, 0);
  write_tree(original, prefix + "-07-defaults.tree", .7, .1, .5, 53, 10);
  write_tree(original, prefix + "-07-preoptions.tree", .7, .1, .5, 10, 10);
  write_tree(original, prefix + "-07-experimental.tree", .7, .1, .5, 12, 0);
  write_tree(original, prefix + "-07-readme.tree", .7, .1, 3, 313, -65);
  write_tree(original, prefix + "-07-search-best.tree", .7,
             .581926481779063, .1307941348522805,
             -40.33970912730919, -64.5047524340898);
  write_tree(original, prefix + "-07-simple.tree", .7, .5, .1, -40, -65);
  write_tree(original, prefix + "-07-simple-60.tree", .7, .5, .1, -40, -60);
  write_tree(original, prefix + "-07-search-second.tree", .7,
             .9999349882209708, .3736394365948595,
             -32.12116207265487, -49.60463442496487);

  graph smoothed = original;
  smooth(smoothed, .7);
  std::ofstream configs(prefix + "-grid-configs.txt");
  int grid_index = 0;
  for (const double wlat : {.3, .5, .7})
    for (const double wlon : {.05, .1, .2})
      for (const double clat : {-60.0, -40.0, -20.0})
        for (const double clon : {-75.0, -65.0, -55.0})
          {
            const std::string filename = prefix + "-grid-"
                                         + std::to_string(grid_index)
                                         + ".tree";
            write_weighted_tree(smoothed, filename,
                                wlat, wlon, clat, clon);
            configs << grid_index++ << ' ' << wlat << ' ' << wlon << ' '
                    << clat << ' ' << clon << '\n';
          }
}

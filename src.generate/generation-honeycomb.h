// Deterministic radial honeycombs shared by reviewed resource encodings.
#ifndef CARTOFREAKO_GENERATION_HONEYCOMB_H
#define CARTOFREAKO_GENERATION_HONEYCOMB_H
#include <algorithm>
#include <array>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace cart0freak0::generation_honeycomb {
inline std::pair<int, int> cell(double x, double y, double radius)
{
  const double q = (2.0 / 3.0 * x) / radius;
  const double r = (-x / 3.0 + std::sqrt(3.0) * y / 3.0) / radius;
  const double s = -q-r;
  int iq = std::nearbyint(q), ir = std::nearbyint(r), is = std::nearbyint(s);
  const double dq = std::abs(iq-q), dr = std::abs(ir-r), ds = std::abs(is-s);
  if (dq > dr && dq > ds) iq = -ir-is;
  else if (dr > ds) ir = -iq-is;
  return {iq, ir};
}

inline std::vector<std::pair<double, double>> offsets(std::size_t count, double radius)
{
  const int extent = std::ceil(std::sqrt(count)) + 2;
  std::vector<std::tuple<double, int, int, double, double>> candidates;
  for (int q = -extent; q <= extent; ++q)
    for (int r = -extent; r <= extent; ++r)
      {
        const double x = radius * 1.5 * q;
        const double y = radius * std::sqrt(3.0) * (r + q / 2.0);
        candidates.emplace_back(std::round((x*x+y*y)*1e12)/1e12, q, r, x, y);
      }
  std::sort(candidates.begin(), candidates.end());
  std::vector<std::pair<double, double>> result;
  for (std::size_t i = 0; i < count; ++i)
    result.emplace_back(std::get<3>(candidates[i]), std::get<4>(candidates[i]));
  return result;
}

inline std::array<std::size_t, 4> allocation(
  const std::array<std::size_t, 4>& counts, std::size_t cap)
{
  const std::size_t total = std::accumulate(counts.begin(), counts.end(), std::size_t{});
  if (total <= cap) return counts;
  std::array<std::size_t, 4> result {};
  for (std::size_t i = 0; i < 4; ++i) result[i] = counts[i] != 0;
  const auto present = std::accumulate(result.begin(), result.end(), std::size_t{});
  if (cap < present) throw std::invalid_argument("honeycomb cap cannot retain every present class");
  const auto available = cap - present;
  std::array<std::pair<double, std::size_t>, 4> residual;
  for (std::size_t i = 0; i < 4; ++i)
    {
      const double exact = static_cast<double>(available) * counts[i] / total;
      const auto whole = static_cast<std::size_t>(exact);
      result[i] += whole;
      residual[i] = {-(exact-whole), i};
    }
  std::sort(residual.begin(), residual.end());
  const auto left = cap - std::accumulate(result.begin(), result.end(), std::size_t{});
  for (std::size_t i = 0; i < left; ++i) ++result[residual[i].second];
  return result;
}
}
#endif

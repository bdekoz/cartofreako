// alpha60 Cahill-Keyes projected-path utilities -*- mode: C++ -*-

// alpha60
// cartography projection path functions

// Copyright (c) 2020, 2022, 2024, 2026 Benjamin De Kosnik
// <b.dekosnik@gmail.com>

// This file is part of the alpha60 library.  This library is free
// software; you can redistribute it and/or modify it under the terms
// of the GNU General Public License as published by the Free Software
// Foundation; either version 3, or (at your option) any later
// version.

// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.

#ifndef cart0freak0_CK_FUNCTIONS_H
#define cart0freak0_CK_FUNCTIONS_H 1

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <optional>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace a60::carto {

namespace cahill_keyes_path_detail {

struct edge_transition
{
  point_2t exit;
  point_2t entry;
};

inline bool
finite_point(const point_2t& point)
{
  const auto [x, y] = point;
  return std::isfinite(x) && std::isfinite(y);
}

inline std::optional<double>
intersection_parameter(const double start, const double end,
                       const double edge, const double scale)
{
  const double denominator = end - start;
  const double coordinate_tolerance
    = 32 * std::numeric_limits<double>::epsilon()
      * std::max({1.0, scale, std::abs(start), std::abs(end),
                  std::abs(edge)});
  if (std::abs(denominator) <= coordinate_tolerance)
    {
      if (std::abs(start - edge) <= coordinate_tolerance)
        return 0;
      return std::nullopt;
    }

  const double parameter = (edge - start) / denominator;
  const double parameter_tolerance
    = 32 * std::numeric_limits<double>::epsilon();
  if (parameter < -parameter_tolerance
      || parameter > 1 + parameter_tolerance)
    return std::nullopt;
  return std::clamp(parameter, 0.0, 1.0);
}

template<typename Projection>
void
validate_path_context(const cartography<Projection>& cartog)
{
  const double width = cartog.p.pframe.width();
  const double height = cartog.p.pframe.height();
  const double left = cartog.f.moriginx;
  const double top = cartog.f.moriginy;
  const double right = left + width;
  const double bottom = top + height;
  const double expected_width = 2 * height;
  const double aspect_tolerance
    = 16 * std::numeric_limits<double>::epsilon()
      * std::max(width, expected_width);
  if (!std::isfinite(width) || !std::isfinite(height)
      || !std::isfinite(left) || !std::isfinite(top)
      || !std::isfinite(right) || !std::isfinite(bottom)
      || !std::isfinite(expected_width)
      || width <= 0 || height <= 0
      || std::abs(width - expected_width) > aspect_tolerance)
    throw std::invalid_argument(
      "Cahill-Keyes path folding requires a finite, positive 2:1 "
      "projection frame and a finite frame origin");
}

/**
   Return the first rectangular frame edge crossed by the wrapped
   interpretation of an adjacent projected-point pair.

   Horizontal wrapping is limited to opposite outer quarters and a jump of at
   least half the projection width. Vertical wrapping is limited to opposite
   halves and a jump of at least one third of the projection height. Those are
   the historical Cahill-Keyes M-layout discontinuity tests.
*/
template<typename Projection>
std::optional<edge_transition>
first_edge_transition(const cartography<Projection>& cartog,
                      const point_2t& previous, const point_2t& current)
{
  if (!finite_point(previous) || !finite_point(current))
    throw std::invalid_argument(
      "Cahill-Keyes path folding requires finite projected points");

  const double width = cartog.p.pframe.width();
  const double height = cartog.p.pframe.height();
  const double left = cartog.f.moriginx;
  const double right = left + width;
  const double top = cartog.f.moriginy;
  const double bottom = top + height;
  const double quarter = width / 4;
  const double middle = top + height / 2;

  const auto [xp, yp] = previous;
  const auto [xc, yc] = current;

  const bool previous_left = xp < left + quarter;
  const bool previous_right = xp >= right - quarter;
  const bool current_left = xc < left + quarter;
  const bool current_right = xc >= right - quarter;

  double unwrapped_x = xc;
  double exit_x = 0;
  double entry_x = 0;
  std::optional<double> tx;
  if (std::abs(xc - xp) >= width / 2)
    {
      if (previous_left && current_right)
        {
          unwrapped_x -= width;
          exit_x = left;
          entry_x = right;
        }
      else if (previous_right && current_left)
        {
          unwrapped_x += width;
          exit_x = right;
          entry_x = left;
        }

      if (exit_x != entry_x)
        tx = intersection_parameter(xp, unwrapped_x, exit_x, width);
    }

  const bool previous_north = yp < middle;
  const bool previous_south = !previous_north;
  const bool current_north = yc < middle;
  const bool current_south = !current_north;

  double unwrapped_y = yc;
  double exit_y = 0;
  double entry_y = 0;
  std::optional<double> ty;
  if (std::abs(yc - yp) >= height / 3)
    {
      if (previous_north && current_south)
        {
          unwrapped_y -= height;
          exit_y = top;
          entry_y = bottom;
        }
      else if (previous_south && current_north)
        {
          unwrapped_y += height;
          exit_y = bottom;
          entry_y = top;
        }

      if (exit_y != entry_y)
        ty = intersection_parameter(yp, unwrapped_y, exit_y, height);
    }

  if (!tx && !ty)
    return std::nullopt;

  if (tx && ty)
    {
      const double simultaneous_tolerance
        = 64 * std::numeric_limits<double>::epsilon();
      if (std::abs(*tx - *ty) <= simultaneous_tolerance)
        return edge_transition {{exit_x, exit_y}, {entry_x, entry_y}};
    }

  if (tx && (!ty || *tx < *ty))
    {
      const double y = std::clamp(
        yp + *tx * (unwrapped_y - yp), top, bottom);
      return edge_transition {{exit_x, y}, {entry_x, y}};
    }

  const double x = std::clamp(
    xp + *ty * (unwrapped_x - xp), left, right);
  return edge_transition {{x, exit_y}, {x, entry_y}};
}

template<typename Projection>
vrange
extract_next_segment(const cartography<Projection>& cartog, vrange& points)
{
  if (points.empty())
    return {};

  validate_path_context(cartog);
  if (!finite_point(points.front()))
    throw std::invalid_argument(
      "Cahill-Keyes path folding requires finite projected points");

  vrange segment;
  segment.reserve(points.size() + 1);
  segment.push_back(points.front());

  for (std::size_t i = 1; i < points.size(); ++i)
    {
      const point_2t& previous = points[i - 1];
      const point_2t& current = points[i];
      const auto transition = first_edge_transition(
        cartog, previous, current);
      if (!transition)
        {
          segment.push_back(current);
          continue;
        }

      if (segment.back() != transition->exit)
        segment.push_back(transition->exit);

      vrange remainder;
      remainder.reserve(points.size() - i + 1);
      remainder.push_back(transition->entry);
      remainder.insert(remainder.end(), points.begin() + i, points.end());
      points = std::move(remainder);
      return segment;
    }

  points.clear();
  return segment;
}

} // namespace cahill_keyes_path_detail

/**
   Split an ordered path of projected Cahill-Keyes points at wrapped frame
   edges. The input is not modified. Every returned segment is nonempty and
   all original points remain in order; paired synthetic exit and entry points
   terminate and restart the path at opposite projection-frame edges.
*/
template<typename Projection>
vvranges
fold_path_edges(const cartography<Projection>& cartog, const vrange& points)
{
  vrange remaining = points;
  vvranges segments;
  while (!remaining.empty())
    segments.push_back(
      cahill_keyes_path_detail::extract_next_segment(cartog, remaining));
  return segments;
}

/**
   Extract the next continuous segment from an ordered projected path.

   This is the stateful compatibility interface used by callers that render
   one segment at a time. The returned segment ends at the first crossed frame
   edge. On a split, `points` is replaced by the unprocessed suffix beginning
   at the opposite edge; otherwise `points` is cleared. Repeated calls until
   `points.empty()` produce the same segments as `fold_path_edges()`.
*/
template<typename Projection>
vrange
minimize_path_distance(const cartography<Projection>& cartog, vrange& points)
{
  return cahill_keyes_path_detail::extract_next_segment(cartog, points);
}

} // namespace a60::carto

#endif

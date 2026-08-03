// Face-local clipping for filled Myriahedral and Voronoi generator paths.
// -*- mode: C++ -*-

#ifndef CART0FREAK0_TESTS_PROJECTION_AREA_GENERATION_H
#define CART0FREAK0_TESTS_PROJECTION_AREA_GENERATION_H 1

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

#include <ogrsf_frmts.h>

#include "projection-generation-common.h"

namespace cart0freak0::generation::area {

struct geometry_deleter
{
  void
  operator()(OGRGeometry* geometry) const noexcept
  { OGRGeometryFactory::destroyGeometry(geometry); }
};

using geometry_ptr = std::unique_ptr<OGRGeometry, geometry_deleter>;

struct raw_point
{
  double x;
  double y;
};

inline bool
uses_native_face_clipping(const projection_context& context)
{
  return context.spec.kind == projection_kind::myriahedral
         || context.spec.kind == projection_kind::voronoi;
}

inline raw_point
project_on_myriahedral_face(const std::size_t face_index,
                            const double latitude, const double longitude)
{
  using namespace a60::carto::myriahedral_detail;
  const vector_3d value = geographic_vector(latitude, longitude);
  const auto& projection = layout();
  const auto& source = projection.spherical[face_index];
  const auto& target = projection.planar[face_index];
  const vector_3d d0 = source[1] - source[0];
  const vector_3d d1 = source[2] - source[0];
  const vector_3d relative = value - source[0];
  const double a = dot(d0, d0);
  const double b = dot(d0, d1);
  const double c = dot(d1, d1);
  const double r0 = dot(relative, d0);
  const double r1 = dot(relative, d1);
  const double determinant = a * c - b * b;
  const double alpha = (r0 * c - r1 * b) / determinant;
  const double beta = (r1 * a - r0 * b) / determinant;
  const point_2d projected = target[0] + (target[1] - target[0]) * alpha
                                      + (target[2] - target[0]) * beta;
  return {projected.x, projected.y};
}

inline raw_point
project_on_voronoi_face(const std::size_t face_index,
                        const double latitude, const double longitude)
{
  using namespace a60::carto::voronoi_detail;
  const vector_3d value = geographic_vector(
    latitude, rotate_longitude(longitude));
  const face_geometry& face = layout().faces[face_index];
  const point_2d local = project_on_face(face, value);
  const point_2d transformed = apply(face.transform, local);
  return {transformed.x, -transformed.y};
}

inline raw_point
project_on_native_face(const projection_context& context,
                       const std::size_t face_index,
                       const double latitude, const double longitude)
{
  if (context.spec.kind == projection_kind::myriahedral)
    return project_on_myriahedral_face(face_index, latitude, longitude);
  if (context.spec.kind == projection_kind::voronoi)
    return project_on_voronoi_face(face_index, latitude, longitude);
  throw std::logic_error("native-face projection requested for another net");
}

inline svg::point_2t
normalize_native_face_point(const projection_context& context,
                            const raw_point point)
{
  double x = 0;
  double y = 0;
  if (context.spec.kind == projection_kind::myriahedral)
    {
      using namespace a60::carto::myriahedral_detail;
      const auto& projection = layout();
      const double extent_x = projection.maximum_x - projection.minimum_x;
      const double extent_y = projection.maximum_y - projection.minimum_y;
      const double scale = std::min(
        a60::carto::myriahedral_width_to_height_ratio / extent_x,
        1 / extent_y);
      const double left = (a60::carto::myriahedral_width_to_height_ratio
                           - extent_x * scale) / 2;
      const double bottom = (1 - extent_y * scale) / 2;
      x = (left + (point.x - projection.minimum_x) * scale)
          / a60::carto::myriahedral_width_to_height_ratio
          * context.map_frame.width();
      y = (1 - (bottom + (point.y - projection.minimum_y) * scale))
          * context.map_frame.height();
    }
  else if (context.spec.kind == projection_kind::voronoi)
    {
      using namespace a60::carto::voronoi_detail;
      static const point_2d registration = project_to_unfolded_net(
        0, registration_longitude_degrees);
      x = (source_center_x + source_scale * (point.x - registration.x))
          / a60::carto::voronoi_source_width * context.map_frame.width();
      y = (source_center_y - source_scale * (point.y - registration.y))
          / a60::carto::voronoi_source_height * context.map_frame.height();
    }
  else
    throw std::logic_error("native-face normalization for another net");

  constexpr double tolerance = 1e-6;
  require(std::isfinite(x) && std::isfinite(y)
          && x >= -tolerance
          && x <= context.map_frame.width() + tolerance
          && y >= -tolerance
          && y <= context.map_frame.height() + tolerance,
          std::string(context.spec.title)
            + " face clipping produced an invalid projected point");
  return {std::clamp(x, 0.0, context.map_frame.width()),
          std::clamp(y, 0.0, context.map_frame.height())};
}

inline void
transform_line(OGRLineString& line, const projection_context& context,
               const std::size_t face_index)
{
  for (int index = 0; index < line.getNumPoints(); ++index)
    {
      const raw_point point = project_on_native_face(
        context, face_index, line.getY(index), line.getX(index));
      line.setPoint(index, point.x, point.y);
    }
}

inline void
transform_geometry(OGRGeometry& geometry,
                   const projection_context& context,
                   const std::size_t face_index)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbLineString:
      transform_line(*geometry.toLineString(), context, face_index);
      return;
    case wkbPolygon:
      {
        OGRPolygon* polygon = geometry.toPolygon();
        if (OGRLinearRing* exterior = polygon->getExteriorRing())
          transform_line(*exterior, context, face_index);
        for (int index = 0; index < polygon->getNumInteriorRings(); ++index)
          transform_line(
            *polygon->getInteriorRing(index), context, face_index);
        return;
      }
    case wkbMultiLineString:
    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        OGRGeometryCollection* collection = geometry.toGeometryCollection();
        for (int index = 0; index < collection->getNumGeometries(); ++index)
          transform_geometry(
            *collection->getGeometryRef(index), context, face_index);
        return;
      }
    default:
      throw std::runtime_error(
        "unsupported native-face geometry type "
        + std::string(OGRGeometryTypeToName(geometry.getGeometryType())));
    }
}

inline std::array<raw_point, 3>
native_face_triangle(const projection_context& context,
                     const std::size_t face_index)
{
  if (context.spec.kind == projection_kind::myriahedral)
    {
      const auto& triangle
        = a60::carto::myriahedral_detail::layout().planar[face_index];
      return {{{triangle[0].x, triangle[0].y},
               {triangle[1].x, triangle[1].y},
               {triangle[2].x, triangle[2].y}}};
    }

  using namespace a60::carto::voronoi_detail;
  const auto& data = layout();
  const face_geometry& face = data.faces[face_index];
  std::array<raw_point, 3> result {};
  for (std::size_t index = 0; index < result.size(); ++index)
    {
      const point_2d local = project_on_face(
        face, data.vertices[face.vertices[index]]);
      const point_2d transformed = apply(face.transform, local);
      result[index] = {transformed.x, -transformed.y};
    }
  return result;
}

inline geometry_ptr
make_triangle(const std::array<raw_point, 3>& points)
{
  auto ring = std::make_unique<OGRLinearRing>();
  for (const raw_point point : points)
    ring->addPoint(point.x, point.y);
  ring->closeRings();
  auto polygon = std::make_unique<OGRPolygon>();
  polygon->addRingDirectly(ring.release());
  return geometry_ptr(polygon.release());
}

inline void
append_planar_ring(std::vector<svg::vrange>& result,
                   const OGRLineString& line,
                   const projection_context& context)
{
  svg::vrange points;
  points.reserve(static_cast<std::size_t>(line.getNumPoints()));
  for (int index = 0; index < line.getNumPoints(); ++index)
    append_unique(points, normalize_native_face_point(
      context, {line.getX(index), line.getY(index)}));
  if (points.size() > 1 && points.front() == points.back())
    points.pop_back();
  if (points.size() >= 3)
    result.push_back(std::move(points));
}

inline void
append_planar_area(std::vector<svg::vrange>& result,
                   const OGRGeometry& geometry,
                   const projection_context& context)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          append_planar_ring(result, *exterior, context);
        for (int index = 0; index < polygon->getNumInteriorRings(); ++index)
          append_planar_ring(
            result, *polygon->getInteriorRing(index), context);
        return;
      }
    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        const OGRGeometryCollection* collection
          = geometry.toGeometryCollection();
        for (int index = 0; index < collection->getNumGeometries(); ++index)
          if (collection->getGeometryRef(index)->getDimension() == 2)
            append_planar_area(
              result, *collection->getGeometryRef(index), context);
        return;
      }
    default:
      if (geometry.getDimension() == 2)
        throw std::runtime_error(
          "unsupported face-clipped result type "
          + std::string(OGRGeometryTypeToName(geometry.getGeometryType())));
    }
}

inline void
collect_line_faces(std::set<std::size_t>& result,
                   const OGRLineString& line,
                   const projection_context& context)
{
  for (int index = 0; index < line.getNumPoints(); ++index)
    result.insert(static_cast<std::size_t>(projection_cell(
      context, {line.getY(index), line.getX(index)})));
}

inline void
collect_geometry_faces(std::set<std::size_t>& result,
                       const OGRGeometry& geometry,
                       const projection_context& context)
{
  switch (wkbFlatten(geometry.getGeometryType()))
    {
    case wkbLineString:
      collect_line_faces(result, *geometry.toLineString(), context);
      return;
    case wkbPolygon:
      {
        const OGRPolygon* polygon = geometry.toPolygon();
        if (const OGRLinearRing* exterior = polygon->getExteriorRing())
          collect_line_faces(result, *exterior, context);
        for (int index = 0; index < polygon->getNumInteriorRings(); ++index)
          collect_line_faces(
            result, *polygon->getInteriorRing(index), context);
        return;
      }
    case wkbMultiLineString:
    case wkbMultiPolygon:
    case wkbGeometryCollection:
      {
        const OGRGeometryCollection* collection
          = geometry.toGeometryCollection();
        for (int index = 0; index < collection->getNumGeometries(); ++index)
          collect_geometry_faces(
            result, *collection->getGeometryRef(index), context);
        return;
      }
    default:
      return;
    }
}

inline std::vector<svg::vrange>
project_native_face_area(const OGRGeometry& geographic_geometry,
                         const projection_context& context,
                         const double west, const double south,
                         const double east, const double north)
{
  require(uses_native_face_clipping(context),
          "native-face area clipping requires Myriahedral or Voronoi");
  std::set<std::size_t> faces;
  collect_geometry_faces(faces, geographic_geometry, context);
  constexpr double candidate_step = 1;
  for (double latitude = south; latitude < north;
       latitude += candidate_step)
    for (double longitude = west; longitude < east;
         longitude += candidate_step)
      faces.insert(static_cast<std::size_t>(projection_cell(
        context, {latitude + candidate_step / 2,
                  longitude + candidate_step / 2})));

  std::vector<svg::vrange> result;
  for (const std::size_t face_index : faces)
    {
      geometry_ptr planar(geographic_geometry.clone());
      require(planar != nullptr,
              "GDAL could not clone a grid cell for native-face clipping");
      transform_geometry(*planar, context, face_index);
      geometry_ptr valid(planar->MakeValid());
      require(valid != nullptr,
              "GDAL could not repair a face-local projected polygon");
      geometry_ptr triangle = make_triangle(
        native_face_triangle(context, face_index));
      geometry_ptr clipped(valid->Intersection(triangle.get()));
      require(clipped != nullptr,
              "GDAL failed to intersect a projected native face");
      if (!clipped->IsEmpty())
        append_planar_area(result, *clipped, context);
    }
  return result;
}

} // namespace cart0freak0::generation::area

#endif

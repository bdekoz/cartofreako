#!/usr/bin/env python3

from osgeo import ogr

source = ("/tmp/myriaworld.gjlN58/natural-earth-history/10m_cultural/"
          "ne_10m_admin_0_countries.shp")
output = "/tmp/myriaworld.gjlN58/countries-rings.txt"

dataset = ogr.Open(source)
layer = dataset.GetLayer(0)
features = []
for feature in layer:
    geometry = feature.GetGeometryRef()
    polygons = []
    if geometry.GetGeometryName() == "POLYGON":
        polygon_geometries = [geometry]
    else:
        polygon_geometries = [geometry.GetGeometryRef(index)
                              for index in range(geometry.GetGeometryCount())]
    for polygon in polygon_geometries:
        ring = polygon.GetGeometryRef(0)
        points = [ring.GetPoint(index)[:2]
                  for index in range(ring.GetPointCount() - 1)]
        if len(points) >= 3:
            polygons.append(points)
    features.append((feature.GetField("NAME_LONG"), polygons))

with open(output, "w", encoding="utf-8") as stream:
    stream.write(f"{len(features)}\n")
    for name, polygons in features:
        stream.write(name + "\n")
        stream.write(f"{len(polygons)}\n")
        for points in polygons:
            stream.write(f"{len(points)}\n")
            for longitude, latitude in points:
                stream.write(f"{longitude:.17g} {latitude:.17g}\n")

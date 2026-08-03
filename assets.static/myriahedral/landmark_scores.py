#!/usr/bin/env python3

import glob
import importlib.util
import math

import numpy as np

spec = importlib.util.spec_from_file_location(
    "reconstruct", "/tmp/myriaworld.gjlN58/reconstruct.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

WIDTH = 560
HEIGHT = 315
locations = np.asarray([
    (40.7128, -74.0060),
    (34.0549, -118.2426),
    (48.8575, 2.3514),
    (-29.8587, 31.0218),
    (28.7041, 77.1025),
    (35.6895, 139.6917),
    (-33.8688, 151.2093),
    (-23.5558, -46.6396),
    (64.1470, -21.9408),
    (-62.2001, 58.9642),
])
# Manually registered to recognizable coastline positions in the source PNG.
target = np.asarray([
    (219, 99),    # New York City
    (176, 101),   # Los Angeles
    (303, 126),   # Paris
    (323, 207),   # Durban
    (389, 159),   # Delhi
    (438, 136),   # Tokyo
    (483, 226),   # Sydney
    (226, 188),   # Sao Paulo
    (288, 109),   # Reykjavik
    (171, 237),   # Villa Las Estrellas / Antarctic Peninsula
], dtype=float)

faces = r.subdivide(r.initial_faces())

def vector(latitude, longitude):
    latitude = math.radians(latitude)
    longitude = math.radians(longitude)
    cosine = math.cos(latitude)
    return np.asarray((cosine * math.cos(longitude),
                       cosine * math.sin(longitude),
                       math.sin(latitude)))

def contains(face, value):
    for index in range(3):
        first = face[index]
        second = face[(index + 1) % 3]
        opposite = face[(index + 2) % 3]
        side = np.dot(np.cross(first, second), value)
        reference = np.dot(np.cross(first, second), opposite)
        if side * reference < -1e-13:
            return False
    return True

def face_coordinates(latitude, longitude):
    value = vector(latitude, longitude)
    index = next(index for index, face in enumerate(faces)
                 if contains(face, value))
    p0, p1, p2 = faces[index]
    d0 = p1 - p0
    d1 = p2 - p0
    rhs = value - p0
    a = np.dot(d0, d0)
    b = np.dot(d0, d1)
    c = np.dot(d1, d1)
    r0 = np.dot(rhs, d0)
    r1 = np.dot(rhs, d1)
    determinant = a * c - b * b
    alpha = (r0 * c - r1 * b) / determinant
    beta = (r1 * a - r0 * b) / determinant
    return index, alpha, beta

coordinates = [face_coordinates(*location) for location in locations]

def project(planar):
    result = []
    for index, alpha, beta in coordinates:
        q0, q1, q2 = planar[index]
        result.append(q0 + alpha * (q1 - q0) + beta * (q2 - q0))
    return np.asarray(result)

def screen_points(planar, raw_points, angle):
    radians = math.radians(angle)
    rotation = np.asarray(((math.cos(radians), -math.sin(radians)),
                           (math.sin(radians), math.cos(radians))))
    rotated = planar @ rotation.T
    points = raw_points @ rotation.T
    minimum = rotated.min(axis=(0, 1))
    maximum = rotated.max(axis=(0, 1))
    extent = maximum - minimum
    scale = min((WIDTH - 2) / extent[0], (HEIGHT - 2) / extent[1])
    offset = ((WIDTH, HEIGHT) - scale * extent) / 2 - scale * minimum
    result = points * scale + offset
    result[:, 1] = HEIGHT - result[:, 1]
    return result

for filename in sorted(glob.glob("/tmp/myriaworld.gjlN58/boost-*.npz")):
    planar = np.load(filename)["planar"]
    raw_points = project(planar)
    best = (float("inf"), 0, None)
    for angle in range(360):
        points = screen_points(planar, raw_points, angle)
        rms = np.sqrt(np.mean(np.sum((points - target) ** 2, axis=1)))
        if rms < best[0]:
            best = (rms, angle, points)
    print(best[:2], filename)
    if (filename.endswith("boost-07-search-best.npz")
        or filename.endswith("boost-grid-37.npz")):
        print(np.round(best[2], 1))

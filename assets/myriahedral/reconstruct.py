#!/usr/bin/env python3

import heapq
import math
import sys
from collections import deque

import matplotlib
matplotlib.use("Agg")
import matplotlib.collections
import matplotlib.pyplot as plt
import numpy as np
from osgeo import ogr
from shapely import contains_xy, from_wkb, unary_union


TAU = 0.8506508084
ONE = 0.5257311121


def normalize(p):
    return p / np.linalg.norm(p)


def initial_faces():
    za = (TAU, ONE, 0.0)
    zb = (-TAU, ONE, 0.0)
    zc = (-TAU, -ONE, 0.0)
    zd = (TAU, -ONE, 0.0)
    ya = (ONE, 0.0, TAU)
    yb = (ONE, 0.0, -TAU)
    yc = (-ONE, 0.0, -TAU)
    yd = (-ONE, 0.0, TAU)
    xa = (0.0, TAU, ONE)
    xb = (0.0, -TAU, ONE)
    xc = (0.0, -TAU, -ONE)
    xd = (0.0, TAU, -ONE)
    return np.asarray([
        (ya, xa, yd), (ya, yd, xb), (yb, yc, xd), (yb, xc, yc),
        (za, ya, zd), (za, zd, yb), (zc, yd, zb), (zc, zb, yc),
        (xa, za, xd), (xa, xd, zb), (xb, xc, zd), (xb, zc, xc),
        (xa, ya, za), (xd, za, yb), (ya, xb, zd), (yb, zd, xc),
        (yd, xa, zb), (yc, zb, xd), (yd, zc, xb), (yc, xc, zc),
    ], dtype=float)


def subdivide(faces, levels=4):
    for _ in range(levels):
        result = []
        for p0, p1, p2 in faces:
            a = normalize((p0 + p2) * 0.5)
            b = normalize((p0 + p1) * 0.5)
            c = normalize((p1 + p2) * 0.5)
            result.extend(((p0, b, a), (b, p1, c),
                           (a, b, c), (a, c, p2)))
        faces = np.asarray(result)
    return faces


def vertex_key(p):
    return tuple(np.round(p, 12))


def topology(faces):
    vertex_ids = {}
    vertices = []
    face_vertex_ids = np.empty((len(faces), 3), dtype=np.int32)
    for fi, face in enumerate(faces):
        for vi, p in enumerate(face):
            key = vertex_key(p)
            if key not in vertex_ids:
                vertex_ids[key] = len(vertices)
                vertices.append(p)
            face_vertex_ids[fi, vi] = vertex_ids[key]

    edge_faces = {}
    for fi, vids in enumerate(face_vertex_ids):
        for j in range(3):
            edge = tuple(sorted((int(vids[j]), int(vids[(j + 1) % 3]))))
            edge_faces.setdefault(edge, []).append(fi)

    adjacency = [[] for _ in faces]
    edges = []
    for edge, pair in edge_faces.items():
        if len(pair) != 2:
            raise RuntimeError((edge, pair))
        a, b = pair
        ei = len(edges)
        edges.append((a, b, edge))
        adjacency[a].append((b, ei))
        adjacency[b].append((a, ei))
    return np.asarray(vertices), face_vertex_ids, edges, adjacency


def spherical_area(face):
    a, b, c = face
    numerator = abs(np.dot(a, np.cross(b, c)))
    denominator = 1 + np.dot(a, b) + np.dot(b, c) + np.dot(c, a)
    return 2 * math.atan2(numerator, denominator)


def face_centroids(faces):
    values = faces.sum(axis=1)
    return values / np.linalg.norm(values, axis=1)[:, None]


def lon_lat(points):
    longitude = np.degrees(np.arctan2(points[:, 1], points[:, 0]))
    latitude = np.degrees(np.arcsin(np.clip(points[:, 2], -1.0, 1.0)))
    return longitude, latitude


def load_countries(filename):
    ds = ogr.Open(filename)
    layer = ds.GetLayer(0)
    all_geometries = []
    named = {}
    wanted = {
        "Indonesia", "Australia", "Greenland", "New Zealand",
        "Argentina", "Chile"
    }
    for feature in layer:
        geometry = from_wkb(bytes(feature.GetGeometryRef().ExportToWkb()))
        all_geometries.append(geometry)
        name = feature.GetField("NAME_LONG")
        if name in wanted:
            named.setdefault(name, []).append(geometry)
    return unary_union(all_geometries), {
        name: unary_union(parts) for name, parts in named.items()
    }


def sample_faces(faces, land, named, order=10):
    # A deterministic triangular lattice samples each spherical face.
    bary = []
    for i in range(order + 1):
        for j in range(order + 1 - i):
            k = order - i - j
            bary.append((i / order, j / order, k / order))
    bary = np.asarray(bary)

    points = np.einsum("sj,fjk->fsk", bary, faces)
    points /= np.linalg.norm(points, axis=2)[:, :, None]
    longitude, latitude = lon_lat(points.reshape(-1, 3))
    land_hits = contains_xy(land, longitude, latitude).reshape(len(faces), -1)
    fraction = land_hits.mean(axis=1)

    special = {}
    for name, geometry in named.items():
        hits = contains_xy(geometry, longitude, latitude).reshape(len(faces), -1)
        special[name] = hits.any(axis=1)
    return fraction, special


def smooth_land(fraction, centroids, areas, sigma=0.4):
    result = np.empty_like(fraction)
    cutoff = 1e-3
    for start in range(0, len(fraction), 128):
        stop = min(start + 128, len(fraction))
        dots = np.clip(centroids[start:stop] @ centroids.T, -1.0, 1.0)
        distance = np.arccos(dots)
        weights = np.exp(-(distance * distance) / (sigma * sigma))
        weights[weights < cutoff] = 0
        weighted_area = weights * areas[None, :]
        result[start:stop] = (
            weighted_area @ fraction / (weighted_area.sum(axis=1) + 1e-6)
        )
    return np.maximum(0, result)


def smooth_land_bfs(fraction, centroids, areas, adjacency, sigma=0.4):
    result = np.empty_like(fraction)
    cutoff = 1e-3
    for start in range(len(fraction)):
        seen = np.zeros(len(fraction), dtype=bool)
        seen[start] = True
        queue = deque((start,))
        total = 0.0
        weight_sum = 0.0
        while queue:
            face = queue.popleft()
            distance = math.acos(float(np.clip(
                np.dot(centroids[start], centroids[face]), -1.0, 1.0)))
            if distance > math.pi / 2:
                break
            weight = math.exp(-(distance * distance) / (sigma * sigma))
            if weight < cutoff:
                break
            total += weight * areas[face] * fraction[face]
            weight_sum += weight * areas[face]
            for neighbor, _ in adjacency[face]:
                if not seen[neighbor]:
                    seen[neighbor] = True
                    queue.append(neighbor)
        result[start] = max(0.0, total / (weight_sum + 1e-6))
    return result


def edge_weights(edges, centroids, areas, fraction, special,
                 wlon=0.1, wlat=3.0, center_lon=313.0,
                 center_lat=-65.0):
    adjusted = fraction.copy()
    for name in ("Indonesia", "Australia", "Greenland", "Argentina", "Chile"):
        if name in special:
            adjusted[special[name]] *= 2
    if "New Zealand" in special:
        adjusted[special["New Zealand"]] *= 5

    longitude, latitude = lon_lat(centroids)
    weights = np.empty(len(edges))
    for ei, (a, b, _) in enumerate(edges):
        value = (adjusted[a] * areas[a] + adjusted[b] * areas[b]) \
                / (areas[a] + areas[b])
        wa = abs(longitude[a] - center_lon) / 180.0
        wb = abs(latitude[a] - center_lat) / 90.0
        norm = wlon * wa * wa + wlat * wb * wb
        weights[ei] = math.exp((1 - value) * (1 - value) * norm)
    return weights


def prim_tree(edges, adjacency, weights, centroids):
    target = normalize(np.asarray([
        math.cos(math.radians(46)) * math.cos(math.radians(88)),
        math.cos(math.radians(46)) * math.sin(math.radians(88)),
        math.sin(math.radians(46)),
    ]))
    root = int(np.argmax(centroids @ target))
    visited = np.zeros(len(adjacency), dtype=bool)
    parent = np.full(len(adjacency), -1, dtype=np.int32)
    tree_edges = set()
    queue = []

    def visit(face):
        visited[face] = True
        for neighbor, ei in adjacency[face]:
            if not visited[neighbor]:
                heapq.heappush(queue, (weights[ei], ei, face, neighbor))

    visit(root)
    while queue:
        _, ei, source, target_face = heapq.heappop(queue)
        if visited[target_face]:
            continue
        parent[target_face] = source
        tree_edges.add(ei)
        visit(target_face)
    if not visited.all():
        raise RuntimeError("disconnected mesh")
    return root, parent, tree_edges


def initial_planar_triangle(face):
    p0, p1, p2 = face
    d0 = p1 - p0
    d1 = p2 - p0
    l0 = np.linalg.norm(d0)
    l1 = np.linalg.norm(d1)
    cosine = abs(np.dot(d0 / l0, d1 / l1))
    return np.asarray(((0.0, 0.0),
                       (l0, 0.0),
                       (cosine * l0,
                        math.sin(math.acos(cosine)) * l1)))


def unfold_child(parent_face, child_face, parent_xy, parent_ids, child_ids,
                 vertices):
    shared = [value for value in parent_ids if value in set(child_ids)]
    if len(shared) != 2:
        raise RuntimeError((parent_ids, child_ids, shared))
    pa = int(np.where(parent_ids == shared[0])[0][0])
    pb = int(np.where(parent_ids == shared[1])[0][0])
    pc = int(next(i for i, value in enumerate(parent_ids) if value not in shared))
    ca = int(np.where(child_ids == shared[0])[0][0])
    cb = int(np.where(child_ids == shared[1])[0][0])
    cc = int(next(i for i, value in enumerate(child_ids) if value not in shared))

    a = parent_xy[pa]
    b = parent_xy[pb]
    parent_third = parent_xy[pc]
    child_vertex = vertices[child_ids[cc]]
    da = np.linalg.norm(child_vertex - vertices[shared[0]])
    db = np.linalg.norm(child_vertex - vertices[shared[1]])
    edge = b - a
    edge_length = np.linalg.norm(edge)
    along = (da * da - db * db + edge_length * edge_length) / (2 * edge_length)
    height = math.sqrt(max(0.0, da * da - along * along))
    unit = edge / edge_length
    perpendicular = np.asarray((-unit[1], unit[0]))
    c0 = a + along * unit + height * perpendicular
    c1 = a + along * unit - height * perpendicular

    side_parent = np.cross(edge, parent_third - a)
    side0 = np.cross(edge, c0 - a)
    chosen = c0 if side0 * side_parent < 0 else c1
    result = np.empty((3, 2))
    result[ca] = a
    result[cb] = b
    result[cc] = chosen
    return result


def unfold(faces, vertices, face_ids, adjacency, tree_edges,
           rotation_degrees=315):
    planar = np.full((len(faces), 3, 2), np.nan)
    planar[0] = initial_planar_triangle(faces[0])
    stack = [0]
    closed = set()
    while stack:
        current = stack.pop()
        closed.add(current)
        for neighbor, ei in adjacency[current]:
            if ei not in tree_edges or neighbor in closed:
                continue
            if np.isfinite(planar[neighbor]).all():
                continue
            planar[neighbor] = unfold_child(
                faces[current], faces[neighbor], planar[current],
                face_ids[current], face_ids[neighbor], vertices)
            stack.append(neighbor)
    if not np.isfinite(planar).all():
        raise RuntimeError("not all faces unfolded")

    angle = math.radians(rotation_degrees)
    rotation = np.asarray(((math.cos(angle), -math.sin(angle)),
                           (math.sin(angle), math.cos(angle))))
    return planar @ rotation.T


def render(planar, filename):
    fig, ax = plt.subplots(1, 1, figsize=(64, 36), dpi=70)
    fig.patch.set_facecolor("#909090")
    collection = matplotlib.collections.PolyCollection(
        planar, closed=False, edgecolor="white", facecolor="white",
        linewidths=0.1, antialiased=False)
    ax.add_collection(collection)
    ax.set_xlim(planar[:, :, 0].min(), planar[:, :, 0].max())
    ax.set_ylim(planar[:, :, 1].min(), planar[:, :, 1].max())
    ax.set_facecolor("#909090")
    ax.set_frame_on(False)
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())
    ax.set_aspect("equal")
    plt.tight_layout()
    fig.savefig(filename, facecolor="#909090", edgecolor="none")
    plt.close(fig)


def render_land(planar, fraction, filename):
    fig, ax = plt.subplots(1, 1, figsize=(64, 36), dpi=70)
    fig.patch.set_facecolor("#909090")
    colors = np.where(fraction[:, None] >= 0.5,
                      np.asarray((0.0, 0.0, 0.0, 1.0)),
                      np.asarray((1.0, 1.0, 1.0, 1.0)))
    collection = matplotlib.collections.PolyCollection(
        planar, closed=False, edgecolor="face", facecolors=colors,
        linewidths=0.1, antialiased=False)
    ax.add_collection(collection)
    ax.set_xlim(planar[:, :, 0].min(), planar[:, :, 0].max())
    ax.set_ylim(planar[:, :, 1].min(), planar[:, :, 1].max())
    ax.set_facecolor("#909090")
    ax.set_frame_on(False)
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())
    ax.set_aspect("equal")
    plt.tight_layout()
    fig.savefig(filename, facecolor="#909090", edgecolor="none")
    plt.close(fig)


def main():
    shapefile = sys.argv[1]
    output = sys.argv[2]
    faces = subdivide(initial_faces())
    vertices, face_ids, edges, adjacency = topology(faces)
    print("faces", len(faces), "vertices", len(vertices), "edges", len(edges))
    land, named = load_countries(shapefile)
    fraction, special = sample_faces(faces, land, named)
    centroids = face_centroids(faces)
    areas = np.asarray([spherical_area(face) for face in faces])
    smoothed = smooth_land(fraction, centroids, areas)
    weights = edge_weights(edges, centroids, areas, smoothed, special)
    root, parent, tree_edges = prim_tree(edges, adjacency, weights, centroids)
    print("root", root, "tree edges", len(tree_edges),
          "weights", weights.min(), weights.max())
    planar = unfold(faces, vertices, face_ids, adjacency, tree_edges)
    print("bounds", planar[:, :, 0].min(), planar[:, :, 0].max(),
          planar[:, :, 1].min(), planar[:, :, 1].max())
    np.savez(output + ".npz", faces=faces, vertices=vertices,
             face_ids=face_ids, planar=planar, parent=parent,
             tree_edges=np.asarray(sorted(tree_edges)), weights=weights,
             fraction=fraction, smoothed=smoothed)
    render(planar, output + ".png")
    render_land(planar, fraction, output + "-land.png")


if __name__ == "__main__":
    main()

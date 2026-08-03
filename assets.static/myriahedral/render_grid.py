#!/usr/bin/env python3

import glob
import importlib.util
import numpy as np

spec = importlib.util.spec_from_file_location(
    "reconstruct", "/tmp/myriaworld.gjlN58/reconstruct.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

faces = r.subdivide(r.initial_faces())
vertices, face_ids, edges, adjacency = r.topology(faces)
edge_by_pair = {
    tuple(sorted((first, second))): index
    for index, (first, second, _) in enumerate(edges)
}

for filename in sorted(glob.glob("/tmp/myriaworld.gjlN58/boost-grid-*.tree")):
    data = np.loadtxt(filename, skiprows=1, dtype=int)
    tree = {
        edge_by_pair[tuple(sorted((current, parent)))]
        for current, parent in data if current != parent
    }
    planar = r.unfold(faces, vertices, face_ids, adjacency, tree, 0)
    np.savez(filename.removesuffix(".tree") + ".npz", planar=planar)

#!/usr/bin/env python3
"""Check the scientific and export toolchain without installing anything."""
import ctypes.util
import importlib
import shutil
import sys
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

MODULES = ("numpy", "scipy", "pandas", "geopandas", "shapely", "matplotlib", "lxml",
           "PIL", "reportlab", "requests", "bs4")
TOOLS = ("g++", "gdalinfo", "gdal-config", "pkg-config", "inkscape", "pdfinfo", "pdfunite", "fc-match")


def check():
    missing = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append("Python module " + name)
    try:
        import cairo
        import gi
        gi.require_version('Rsvg','2.0')
        from gi.repository import Rsvg
    except (ImportError,ValueError):
        missing.append('system Python Cairo/PyGObject with Rsvg 2.0 introspection')
    for name in TOOLS:
        if shutil.which(name) is None:
            missing.append("command " + name)
    for name in ("netcdf", "h3", "cairo", "maxminddb"):
        if ctypes.util.find_library(name) is None:
            missing.append("native library " + name)
    if not any(ctypes.util.find_library(name) for name in ('gomp','omp')):
        missing.append('native OpenMP runtime (gomp or omp)')
    with tempfile.TemporaryDirectory(prefix='cartofreako-openmp-') as folder:
        target=Path(folder)/'probe'
        compiler=shlex.split(os.environ.get('CXX','g++'))
        try:
            result=subprocess.run([*compiler,'-x','c++','-fopenmp','-','-o',str(target)],
                input='#include <omp.h>\nint main(){return omp_get_max_threads()<=0;}\n',
                text=True,capture_output=True)
            if result.returncode or subprocess.run([str(target)],capture_output=True).returncode:
                missing.append('CXX compiler with working -fopenmp compile/link/runtime support')
        except OSError:
            missing.append('CXX compiler with working -fopenmp support')
    return missing


if __name__ == "__main__":
    missing = check()
    if missing:
        print("Missing atlas prerequisites:\n  " + "\n  ".join(missing), file=sys.stderr)
        print("Run make install-prerequisites INSTALL_ATLAS_PREREQUISITES=1", file=sys.stderr)
        sys.exit(1)
    print("Scientific atlas prerequisites passed")

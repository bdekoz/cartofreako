#!/usr/bin/env python3
"""Compatibility entry point for the generic Izzi mobile PDF exporter."""
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
IZZI = Path(os.environ.get('IZZI_ROOT', ROOT.parent / 'izzi'))
# Preserve the optional dependency location used by existing Cartofreako recipes.
sys.path.append(str(ROOT / 'build/setouchi-h3-python'))
script = IZZI / 'scripts/build-mobile-pdf.py'
if not script.is_file():
    raise SystemExit('Izzi mobile exporter missing: ' + str(script) + '; set IZZI_ROOT to its checkout')
if __name__ == '__main__':
    runpy.run_path(str(script), run_name='__main__')

#!/usr/bin/env python3
"""A fractional raster viewport must preserve paper color and visible marks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    folder=Path(folder);svg=folder/'sample.svg';png=folder/'sample.png'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="44in" height="19.052559in" viewBox="0 0 44 19.052559"><rect width="44" height="19.052559" fill="#240413"/><circle cx="22" cy="9.5262795" r="1" fill="#fcc553"/></svg>')
    subprocess.run([sys.executable,str(ROOT/'scripts/export-native-swarm.py'),str(svg),'--png',str(png),'--long-side','600','--background','#240413'],check=True)
    image=Image.open(png)
    assert image.mode=='RGB' and image.size==(600,260)
    assert image.crop((0,0,600,1)).getextrema()==((36,36),(4,4),(19,19))
    assert image.getpixel((300,130))==(252,197,83)
    assert json.loads(png.with_suffix('.export.json').read_text())['native_circles_retained']==1
print('Native swarm opaque-paper regression passed; circle retained')

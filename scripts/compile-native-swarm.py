#!/usr/bin/env python3
"""Compile Cartofreako's projection adapter to Alpha60's native swarm renderer."""
from pathlib import Path
import os, subprocess

ROOT=Path(__file__).resolve().parents[1]
alpha=Path(os.environ.get('ALPHA60_ROOT',ROOT.parent/'alpha60'))
izzi=Path(os.environ.get('IZZI_ROOT',ROOT.parent/'izzi'))
torrent=Path(os.environ.get('LIBTORRENT_PREFIX',Path.home()/'bin/H-libtorrent'))
geolite=Path(os.environ.get('GEOLITE2PP_PREFIX',Path.home()/'bin/H-geolite2pp'))
target=ROOT/'build/generate-native-swarm';target.parent.mkdir(exist_ok=True)
libdirs=[p/('lib64' if (p/'lib64').exists() else 'lib') for p in [torrent,geolite]]
command=[os.environ.get('CXX','g++'),'-Da60_USE_GEO=6',
    *['-I'+str(p) for p in [alpha/'src',izzi/'src',ROOT/'src.projections',ROOT/'src.generate',torrent/'include',geolite/'include']],
    '-isystem','/usr/include/rapidjson','-O2','-std=c++20','-Wall','-Wextra','-Werror','-Wno-unused-local-typedefs',
    str(ROOT/'src.generate/generate-native-swarm.cc'),'-o',str(target),
    *['-L'+str(p) for p in libdirs],'-Wl,-rpath,'+':'.join(map(str,libdirs)),
    '-ltorrent-rasterbar','-lssl','-lcrypto','-lmaxminddb','-lh3','-lgeolite2++']
subprocess.run(command,check=True)
print('Built native swarm adapter:',target)

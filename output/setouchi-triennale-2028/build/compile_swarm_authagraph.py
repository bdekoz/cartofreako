#!/usr/bin/env python3
"""Build the local AuthaGraph adapter against the installed Alpha60 sources."""
from pathlib import Path
import hashlib, json, subprocess

OUT = Path(__file__).resolve().parents[1]
USER_ROOT = Path('/home/bkoz')
ALPHA = USER_ROOT / 'src/alpha60'
REPO = OUT.parents[1]
SOURCE = OUT / 'build/render_swarm_authagraph.cc'
BINARY = OUT / 'build/render-swarm-authagraph'

def main():
    headers = [SOURCE, ALPHA / 'src/a60-carto-geo.cc']
    for directory in [ALPHA / 'src', USER_ROOT / 'src/izzi/src', REPO / 'src.projections']:
        headers += list(directory.glob('*.h')) + list(directory.glob('*.inc'))
    command = ['g++', '-Da60_USE_GEO=6', '-I' + str(ALPHA / 'src'),
        '-I' + str(USER_ROOT / 'bin/H-libtorrent/include'),
        '-I' + str(USER_ROOT / 'bin/H-geolite2pp/include'),
        '-I' + str(USER_ROOT / 'src/izzi/src'), '-I' + str(REPO / 'src.projections'),
        '-isystem', '/usr/include/rapidjson', '-O2', '-std=c++20', '-Wall',
        '-Wextra', '-Werror', '-Wno-unused-local-typedefs', str(SOURCE), '-o', str(BINARY),
        '-Wl,-rpath,/home/bkoz/bin/H-libtorrent/lib64:/home/bkoz/bin/H-geolite2pp/lib',
        '/usr/lib64/libssl.so', '/usr/lib64/libcrypto.so',
        str(USER_ROOT / 'bin/H-libtorrent/lib64/libtorrent-rasterbar.so'),
        '/usr/lib64/libmaxminddb.so', '/usr/lib64/libh3.so',
        str(USER_ROOT / 'bin/H-geolite2pp/lib/libgeolite2++.so')]
    if not BINARY.exists() or any(p.stat().st_mtime > BINARY.stat().st_mtime for p in headers):
        with (OUT / 'logs/compile-swarm-authagraph.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    def digest(path):
        with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
    receipt = dict(command=command, binary_sha256=digest(BINARY),
                   inputs=[dict(path=str(p), sha256=digest(p)) for p in sorted(set(headers))])
    (OUT / 'sources/swarm-adapter-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Native AuthaGraph adapter and source digests ready', flush=True)

if __name__ == '__main__': main()

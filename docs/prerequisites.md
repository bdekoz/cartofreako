# Prerequisites

[Documentation index](../index.md) ·
[SVG generation pipeline](generation.md) ·
[WebAssembly workflow](web-workflow.md)

## Requirement levels

Cartofreako has a small self-contained projection test suite and a larger SVG
generation workflow. They do not require the same software:

| Component | Required for | Purpose |
| --- | --- | --- |
| GNU Make | All Makefile targets | Expands the generated projection rules and coordinates builds |
| C++20 compiler and standard library | Tests and native generators | Builds the projection checks and four SVG generators |
| Alpha60 headers | SVG generation | Supplies `a60-io.h` and shared runtime-resource interfaces |
| Izzi headers | SVG generation | Supplies `a60-svg.h` and SVG document/path serialization |
| GDAL development package with OGR | Earth and ocean generation | Reads Natural Earth Shapefiles and provides vector geometry operations |
| GEOS support in GDAL | Earth and ocean generation | Performs polygon intersection, repair, and seam-safe clipping |
| Bash, `curl`, `unzip`, and `sha256sum` | Natural Earth acquisition | Downloads, verifies, and extracts the pinned input archive |
| Inkscape | Contributor visual review and SVG editing | Inspects layers, clip paths, geometry, and rendering seams |
| Emscripten, Node.js, and a browser | Optional WebAssembly example | Builds and exercises the browser-oriented Myriahedral example |

`make check` needs only GNU Make and a C++20 compiler. The tests provide small
compatibility definitions for the Alpha60 API and do not use GDAL, Natural
Earth, Izzi, Inkscape, or network access.

`make generated-projections` builds the complete 20-file SVG suite. It needs
all native build and data-acquisition dependencies through GEOS, but Make does
not invoke Inkscape. Inkscape is a workflow requirement when the generated
artwork must be inspected or edited; it may be omitted from a headless build
job that only runs the embedded structural checks.

## Install the system packages

The commands below install a full native contributor workstation, including
Inkscape. Package names may differ on older or derivative distributions.

### Fedora and related distributions

```sh
sudo dnf install \
  gcc-c++ make git bash curl unzip coreutils \
  gdal gdal-devel geos geos-devel inkscape
```

The `-devel` packages are important: the runtime-only GDAL package does not
provide the C++ headers and link metadata used by the Makefile.

### Debian and Ubuntu

```sh
sudo apt-get update
sudo apt-get install \
  build-essential git bash curl unzip coreutils \
  gdal-bin libgdal-dev libgeos-dev inkscape
```

### macOS with Homebrew

Install Apple's command-line developer tools, then the missing Unix and GIS
components:

```sh
xcode-select --install
brew install make gdal coreutils git
brew install --cask inkscape
```

Homebrew installs GNU Make as `gmake`. The fetch script requires
`sha256sum`, supplied by GNU coreutils. If it is not already available on
`PATH`, expose Homebrew's unprefixed coreutils commands:

```sh
export PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"
```

Use `gmake CXX=clang++` in place of `make` in the commands below. Homebrew's
GDAL formula includes GEOS support.

### Windows

The Makefile and acquisition script assume a POSIX shell, Unix paths, Bash,
and `gdal-config`. The least surprising Windows setup is WSL2 with a Debian or
Ubuntu distribution; use the Debian/Ubuntu package list inside WSL. Native
PowerShell or `cmd.exe` is not currently a supported execution environment.

Official installation references:

- [GDAL downloads and platform packages](https://gdal.org/en/stable/download.html)
- [GEOS](https://libgeos.org/)
- [Installing Inkscape](https://wiki.inkscape.org/wiki/Installing_Inkscape)
- [Emscripten SDK](https://emscripten.org/docs/tools_reference/emsdk.html)

## Compiler and Make requirements

The default compiler is `g++`. It must implement C++20, including the standard
library facilities used by the projection headers such as `<numbers>`,
`std::variant`, and `std::filesystem`. Strict warnings are enabled and treated
as errors:

```text
-std=c++20 -Wall -Wextra -Wpedantic -Werror
```

Select another compiler on the Make command line:

```sh
make CXX=clang++ check
```

Confirm the basic toolchain, then run the self-contained checks:

```sh
make --version
g++ --version
make check
```

Use GNU Make rather than BSD Make because the Makefile constructs the
per-projection rules with GNU Make's `call`, `eval`, and related expansion
features.

## Alpha60 and Izzi source trees

The SVG generators compile against two neighboring header trees. The default
layout is:

```text
workspace/
├── alpha60/
│   └── src/a60-io.h
├── izzi/
│   └── src/a60-svg.h
└── cartofreako/
    ├── Makefile
    ├── src/
    └── tests/
```

From the cartofreako checkout, the sibling repositories can be obtained with:

```sh
git clone https://github.com/bdekoz/alpha60.git ../alpha60
git clone https://github.com/bdekoz/izzi.git ../izzi
```

For a different checkout layout, override the include roots:

```sh
make \
  ALPHA60_SRC=/absolute/path/to/alpha60/src \
  IZZI_SRC=/absolute/path/to/izzi/src \
  generate-geometry-projections
```

The current Makefile consumes these projects as headers and does not link a
separate Alpha60 or Izzi library.

## GDAL, OGR, and GEOS

Earth and ocean generation includes `gdal_priv.h`, `ogrsf_frmts.h`, and the
OGR C API. The Makefile obtains compiler and linker arguments from:

```sh
gdal-config --cflags
gdal-config --libs
```

The installed GDAL must include OGR, the ESRI Shapefile vector driver, and
GEOS. The generators call `OGRGeometryFactory::haveGEOS()` before doing work
and stop with `GDAL must be built with GEOS support` when polygon operations
are unavailable.

Useful checks are:

```sh
gdal-config --version
gdal-config --ogr-enabled
gdal-config --dep-libs | grep geos
ogrinfo --formats | grep 'ESRI Shapefile'
```

`gdal-config --ogr-enabled` must print `yes`; the other checks should show the
GEOS library and Shapefile driver. The generator's runtime check is the final
authority because distribution builds can package GDAL features differently.

If `gdal-config` is installed outside `PATH`, identify it explicitly:

```sh
make GDAL_CONFIG=/absolute/path/to/gdal-config generate-earth-projections
```

Python GDAL bindings are not used by the active Make targets.

## Natural Earth input and network access

The Earth and ocean targets require Natural Earth 5.1.1's complete 1:10m
physical-vector bundle. The repository does not require a manual download:

```sh
make fetch-natural-earth-10m
```

[`scripts/fetch-natural-earth-10m.sh`](../scripts/fetch-natural-earth-10m.sh)
uses Bash, `curl`, `sha256sum`, and `unzip`. It downloads over HTTPS, verifies
the pinned archive digest, extracts only the required datasets, and creates a
completion stamp after every expected `.shp`, `.shx`, `.dbf`, and `.prj` file
is present.

The default data location is:

```text
assets/natural-earth/10m-physical-vectors/
```

Override it when using a shared or pre-provisioned data directory:

```sh
make NATURAL_EARTH_DIR=/absolute/path/to/10m-physical-vectors \
  generated-projections
```

Outbound network access is needed only when the pinned archive is absent.
Allow at least a few hundred megabytes for the archive and extracted inputs,
plus additional space for the generated Earth and ocean SVGs. `make clean`
removes generator binaries and `generated/`, but retains Natural Earth data.
See the [data provenance note](natural-earth-10m-physical-vectors.md) for the
archive URL, checksum, dataset list, and license.

The checked-in *Hamonshū* PDF is provenance artwork, not a runtime input. The
ocean generator uses the compiled catalogue in
[`tests/hamonshu-v2-patterns.inc`](../tests/hamonshu-v2-patterns.inc).

## Inkscape and visual review

Install Inkscape when reviewing or editing generated artifacts. It is useful
here because the SVGs preserve named layers for faces, quadrants, graticules,
physical features, bathymetry, clipping regions, and the 153 *Hamonshū*
patterns. A browser renders the final composition but is less useful for
toggling and auditing those groups.

Verify the installation and open an artifact with:

```sh
inkscape --version
inkscape generated/earth-ck-44-22.svg
```

Use Inkscape's Layers and Objects panel to inspect group IDs and toggle dense
layers. Earth and ocean files can be large, so opening and switching layers
may require substantially more memory than viewing geometry or graticules.
Saving from Inkscape can rewrite SVG formatting and metadata; avoid saving
during a read-only visual review if a serialization diff is not intended.

## Optional WebAssembly workflow

The Myriahedral browser example is separate from native SVG generation. It
requires:

- an Emscripten SDK providing `em++` and `emrun`;
- Node.js for the non-browser smoke test;
- a modern browser with WebAssembly and ES-module support; and
- a local HTTP server, provided by `emrun` in the documented workflow.

The reproducible example uses the Emscripten release identified in
[`docs/web-workflow.md`](web-workflow.md). After activating the SDK, verify:

```sh
em++ --version
emrun --help
node --version
```

This browser example does not need GDAL, GEOS, Natural Earth, Boost.Graph,
Google S2, or the historical Myriahedral preprocessing programs.

## End-to-end verification

From the repository root, a complete native setup can be checked in this
order:

```sh
test -f ../alpha60/src/a60-io.h
test -f ../izzi/src/a60-svg.h
gdal-config --ogr-enabled
make check
make fetch-natural-earth-10m
make generated-projections
inkscape --version
```

Successful generation places five geometry SVGs, five graticule SVGs, five
Earth SVGs, and five ocean SVGs in `generated/`.

## Common failures

| Symptom | Cause and remedy |
| --- | --- |
| `a60-io.h: No such file or directory` | Clone Alpha60 beside cartofreako or set `ALPHA60_SRC` |
| `a60-svg.h: No such file or directory` | Clone Izzi beside cartofreako or set `IZZI_SRC` |
| `gdal-config: command not found` | Install the GDAL development package or set `GDAL_CONFIG` |
| `gdal_priv.h: No such file or directory` | A runtime GDAL package is present without development headers |
| `GDAL must be built with GEOS support` | Install a GEOS-enabled GDAL build and its matching development package |
| Missing `ne_10m_*.shp` | Run `make fetch-natural-earth-10m` or set `NATURAL_EARTH_DIR` |
| `sha256sum: command not found` | Install GNU coreutils and ensure its binaries are on `PATH` |
| Natural Earth checksum mismatch | Remove only the corrupt downloaded archive, then rerun the fetch target; do not bypass verification |
| Inkscape is slow on an Earth or ocean SVG | Close other large documents and inspect one layer family at a time |
| `em++: command not found` | Install and activate emsdk, then source its environment script in the current shell |

## Not required by current native targets

Historical source assets and reconstruction notes mention Perl, Python,
NumPy, Boost.Graph, and Google's S2 geometry library. They document how source
rasters or fixed tables were derived; the current production headers,
`make check`, and native SVG generators do not execute those historical
pipelines.

---

[Documentation index](../index.md) ·
[SVG generation pipeline](generation.md) ·
[Natural Earth data note](natural-earth-10m-physical-vectors.md) ·
[WebAssembly workflow](web-workflow.md)

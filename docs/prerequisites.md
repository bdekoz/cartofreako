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
| C++20 compiler and standard library | Tests, profile resolution, and native generators | Builds the projection checks, generation-profile resolver, and eleven SVG-generation programs |
| RapidJSON development headers | Configured generation plus astronomy, Orbital Technosphere, and network tests and generators | Parses the generation preference, authoritative data profiles, astronomy JSON, NASA SSCWeb references, and cumulative swarm GeoJSON |
| Alpha60 headers | SVG generation | Supplies `a60-io.h` and shared runtime-resource interfaces |
| Izzi headers | SVG generation | Supplies `a60-svg.h`, roulette-curve construction, and SVG document/path serialization |
| H3 development headers and library | Network tests and generation | Validates 64-bit cells and computes configurable parent clusters with the H3 v4 API |
| GDAL development package with OGR | Earth, water, Bathymetry Roulette, global Orbital Technosphere, and network generation | Reads Natural Earth Shapefiles and provides vector geometry operations |
| GEOS support in GDAL | Natural Earth-backed generation | Performs polygon intersection, repair, and seam-safe clipping |
| Bash, `curl`, `unzip`, `rg`, `sha256sum`, and GNU coreutils including `cmp` | Natural Earth, astronomy, orbital, and network preparation | Downloads, verifies, compares, and extracts or installs bounded source data |
| Inkscape | Complete artifact generation and visual review | Exports PDF/PNG and inspects SVG layers, clipping, geometry, and seams |
| Doxygen | API reference generation | Builds the documented projection-header reference under `docs/doxygen/` |
| Emscripten, Node.js, and a browser | Optional WebAssembly builds | Builds the production Cahill-Keyes and land/ocean-only Myriahedral adapters, plus the illustrative Myriahedral overlay |

Check the complete installed toolchain from the repository root with:

```sh
make check-prerequisite
```

The underlying checker also has a no-argument mode and can be run directly:

```sh
./scripts/check-prerequisites.sh
```

That mode locates the repository from the script path, independently of the
current working directory, and uses the working project defaults: `g++`, the
local projection and generation headers, sibling `alpha60`, `izzi`, and
`emsdk` trees, `gdal-config`, Inkscape, Doxygen, Node.js, and automatic browser
discovery. Corresponding environment variables such as `CXX`, `ALPHA60_SRC`,
`EMXX`, and `WEB_BROWSER` override those defaults.

The target verifies the native commands and sibling headers, compiles and runs
C++20/RapidJSON and H3 link/runtime probes, and compiles a GDAL probe that
checks OGR, GEOS, and the ESRI Shapefile driver. Missing native prerequisites make the target fail. Optional
WebAssembly tools and a browser are always checked and reported, but do not
change the exit status. The check honors the Makefile's tool and source-tree
overrides; use `EMRUN` and `WEB_BROWSER` to identify those optional tools when
they are not discoverable at their defaults.

`make generation-plan` needs GNU Make, a C++20 compiler, and RapidJSON
headers. Bare `make` additionally needs the dependencies of the passes chosen
by the generation profile. The check suite also needs H3, the sibling
Izzi/Alpha60 headers, and the checked-in astronomy, Orbital Technosphere, and
network profiles and bounded snapshots. It does not use GDAL, Natural Earth,
Inkscape, or network access.

`make all` builds 24 production whole-earth maps, 12 astronomy maps, 12
Orbital Technosphere maps, six network maps, six Bathymetry Roulette maps, five
exploratory Myriahedral water perspectives, 12 Cahill-Keyes slices, and two
Myriahedral face-group slices, then invokes Inkscape to export all 79 SVGs as
PDFs and 3840-pixel-long-side PNGs. It needs
all native build and data-acquisition dependencies through H3 and GEOS plus Inkscape.
Inkscape may be omitted only when invoking individual SVG generation targets
or the offline `make check` suite.

## Install the system packages

The commands below install a full native contributor workstation, including
Inkscape. Package names may differ on older or derivative distributions.

### Fedora and related distributions

```sh
sudo dnf install \
  gcc-c++ make git bash curl unzip coreutils \
  gdal gdal-devel geos geos-devel rapidjson-devel h3 h3-devel inkscape doxygen
```

The `-devel` packages are important: the runtime-only GDAL package does not
provide the C++ headers and link metadata used by the Makefile.

### Debian and Ubuntu

```sh
sudo apt-get update
sudo apt-get install \
  build-essential git bash curl unzip coreutils \
  gdal-bin libgdal-dev libgeos-dev rapidjson-dev libh3-dev inkscape doxygen
```

### macOS with Homebrew

Install Apple's command-line developer tools, then the missing Unix and GIS
components:

```sh
xcode-select --install
brew install make gdal h3 rapidjson coreutils git doxygen
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
- [Installing Doxygen](https://www.doxygen.nl/manual/install.html)
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

Confirm the basic toolchain, then run the native checks:

```sh
make --version
g++ --version
make check
```

Use GNU Make rather than BSD Make because the Makefile constructs the
per-projection rules with GNU Make's `call`, `eval`, and related expansion
features.

RapidJSON is header-only; no additional linker library is required. The
generation preference, astronomy, Orbital Technosphere, and network profiles,
cumulative swarm GeoJSON, JPL small-body snapshots, and NASA SSCWeb response
use its DOM parser. Verify the
header independently when diagnosing a compiler probe failure:

```sh
test -r /usr/include/rapidjson/document.h
```

## H3 development library

Network generation uses the H3 v4 C API from C++. Both the header and linker
library are required; installing an H3 command-line program alone is not
sufficient. The build includes `h3/h3api.h`, links with `-lh3`, validates
every input cell, and calls `cellToParent()` for clustering.

Useful independent checks are:

```sh
test -r /usr/include/h3/h3api.h
ldconfig -p | grep libh3
make check-prerequisite
```

Use a development package compatible with the v4 names `getResolution`,
`isValidCell`, `h3ToString`, and `cellToParent`. The prerequisite checker
compiles, links, and runs a resolution-5 to resolution-3 parent probe, so it
detects both missing development files and an incompatible API.

## Doxygen API reference

The API reference covers every production projection header, including the
`src.projections/cart0freak0*.h` family and
`src.projections/a60-carto-projection-dymaxion.h`, plus their internal
geometric data structures and helper functions. Generate it with:

```sh
doxygen --version
make doxygen
```

Open `docs/doxygen/html/index.html` after the command completes. Documentation
warnings, including missing parameter descriptions, make the target fail.
`make clean` removes the generated `docs/doxygen/` tree.

## Alpha60 and Izzi source trees

The SVG generators compile against two neighboring header trees. The default
layout is:

```text
workspace/
├── alpha60/
│   └── src/a60-io.h
├── izzi/
│   └── src/
│       ├── a60-svg.h
│       └── a60-svg-curves-roulette.h
└── cartofreako/
    ├── Makefile
    ├── src.projections/
    ├── src.generate/
    ├── src.wasm/
    ├── assets.static/
    ├── assets.generated/
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

Earth, water, and Bathymetry Roulette generation includes `gdal_priv.h`,
`ogrsf_frmts.h`, and the OGR C API. The Makefile obtains compiler and linker
arguments from:

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

The Earth, water, and Bathymetry Roulette targets require Natural Earth
5.1.1's complete 1:10m physical-vector bundle. The repository does not
require a manual download:

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
assets.static/natural-earth/10m-physical-vectors/
```

Override it when using a shared or pre-provisioned data directory:

```sh
make NATURAL_EARTH_DIR=/absolute/path/to/10m-physical-vectors \
  all
```

Outbound network access is needed only when the pinned archive is absent.
Allow at least a few hundred megabytes for the archive and extracted inputs,
plus additional space for the generated SVG, PDF, and PNG artifacts. `make
clean` removes generator binaries and rendered build products, but retains
Natural Earth data and the checked-in WASM sources.
See the [data provenance note](natural-earth-10m-physical-vectors.md) for the
archive URL, checksum, dataset list, and license.

## Astronomy input and network access

The astronomy SVGs and `make check` run offline from the checked-in
`assets.static/astronomy/` profile and bounded catalog snapshots. The profile
is authoritative for both the timestamp and the observer point. Refresh the
external Gaia DR3, NASA Exoplanet Archive, and JPL SBDB snapshots only when an
upstream update is intended:

```sh
make fetch-astro-data
```

That target needs Bash, `curl`, `sha256sum`, standard Coreutils, and outbound
HTTPS access. It checks the expected row counts and replaces the bounded CSV
and JSON files before writing new hashes. It intentionally leaves the profile
and curated transient snapshot unchanged. See the
[astronomy implementation notes](astro-implementation-notes.md) for the data
roles and accuracy boundary.

## Orbital Technosphere input and network access

The Orbital Technosphere SVGs and `make check` run offline from the checked-in
`assets.static/orbital-technosphere/` profile, OMM CSV snapshots, NASA SSCWeb
reference, and hashes. The profile is authoritative for the SGP4 instant and
the observer point captured at make invocation. Deliberately refresh the
external inputs with:

```sh
make fetch-orbiting-data
```

That target needs Bash, `curl`, `rg`, `sha256sum`, Coreutils, and outbound
HTTPS access. It stages all CelesTrak and NASA responses, checks the OMM
header, active-catalog size, and NASA success status, and only then installs
the set and rewrites `SHA256SUMS`. It never changes the profile time or
location. A complete set less than two hours old is reused in accordance with
CelesTrak's update policy; HTTP refusals are reported without retrying or
replacing the old set. See the
[Orbital Technosphere implementation notes](orbital-technosphere-implementation-notes.md)
for source roles, SGP4 boundaries, and refresh procedure.

## Network input preparation

Network generation and its tests run offline from the checked-in
`assets.static/network/` archive and profile. Preparation requires `unzip`,
`sha256sum`, `install`, `mktemp`, `wc`, and `cmp`:

```sh
make prepare-network-data
make generate-network
```

The safe staging script accepts a local `.zip`, `.geojson`, or `.json` through
`NETWORK_SOURCE`. A ZIP must pass its CRC check, contain exactly one flat JSON
member, and expand to no more than 64 MiB. The prepared file is reproducible,
ignored, and retained across normal builds under
`assets.static/network/.prepared/`. `make check` validates the committed
archive SHA-256 and the prepared member SHA-256 before exercising dataset,
H3, clustering, and six-projection layout assertions.

Network rendering also needs H3, GDAL/GEOS, Natural Earth, Alpha60, and Izzi.
No outbound access is used or required. Override `NETWORK_SOURCE` or
`NETWORK_PROFILE` only with a deliberately reviewed, schema-compatible input;
`NETWORK_GEOJSON` controls the staging destination. See the
[network implementation notes](network-implementation-notes.md) for source
semantics, profile fields, and interpretation limits.

## Inkscape and visual review

Install Inkscape when reviewing or editing generated artifacts. It is useful
here because the SVGs preserve named layers for faces, quadrants, graticules,
physical features, bathymetry, and clipping regions. A browser renders the
final composition but is less useful for toggling and auditing those groups.

Verify the installation and open an artifact with:

```sh
inkscape --version
inkscape assets.generated/svg/earth-ck-44-22.svg
```

Use Inkscape's Layers and Objects panel to inspect group IDs and toggle dense
layers. Earth, water, and Bathymetry Roulette files can be large, so opening
and switching layers may require substantially more memory than viewing
geometry or graticules.
Saving from Inkscape can rewrite SVG formatting and metadata; avoid saving
during a read-only visual review if a serialization diff is not intended.

## Optional WebAssembly workflows

The production Cahill-Keyes and Myriahedral browser adapters, and the
documented Myriahedral overlay example, are separate from native SVG
generation. They require:

- an Emscripten SDK providing `em++` and `emrun`;
- Node.js for the non-browser smoke test;
- a modern browser with WebAssembly and ES-module support; and
- a local HTTP server, provided by `emrun` in the documented workflow.

The WASM targets default to the sibling SDK path
`../emsdk/upstream/emscripten/em++`; override `EMXX` when the checkout lives
elsewhere. Build both ES modules and WASM binaries beside the geographic input
and Node smoke tests with:

```sh
make check-wasm-cahill-keyes
make check-wasm-cahill-myriahedral
```

See the [WebAssembly renderer README](../src.wasm/README.md) for runtime SVG
architecture, data provenance, and the Myriahedral option that emits only the
`ocean` and `land` groups. The separate reproducible Myriahedral raster-overlay
example uses the Emscripten release identified in
[`docs/web-workflow.md`](web-workflow.md). After activating the SDK, verify:

```sh
em++ --version
emrun --help
node --version
```

Neither production browser build needs GDAL, GEOS, Boost.Graph, Google S2, or
the historical Myriahedral preprocessing programs. Both runtime maps read the
checked-in, seam-prepared Natural Earth GeoJSON and do not run GDAL or download
data during the WASM build. The Myriahedral adapter performs its additional
five-degree grid and terminal-face clipping directly in C++/WASM.

## End-to-end verification

From the repository root, a complete native setup can be checked in this
order:

```sh
test -f ../alpha60/src/a60-io.h
test -f ../izzi/src/a60-svg.h
test -f ../izzi/src/a60-svg-curves-roulette.h
gdal-config --ogr-enabled
make check
make fetch-natural-earth-10m
make all
inkscape --version
```

Successful generation places six geometry maps, six graticule maps, six
Earth maps, eleven water maps (six production plus five exploratory
Myriahedral perspectives), 12 astronomy maps, 12 Orbital Technosphere maps,
six network maps, six Bathymetry Roulette maps, four quadrant slices, eight
octant slices, and two Myriahedral face-group
slices in each of `assets.generated/svg/`,
`assets.generated/pdf/`, and `assets.generated/png/`. Every PNG preserves its
source aspect ratio, has a 3840-pixel longest side, and is flattened against
opaque white.

## Common failures

| Symptom | Cause and remedy |
| --- | --- |
| `a60-io.h: No such file or directory` | Clone Alpha60 beside cartofreako or set `ALPHA60_SRC` |
| `a60-svg.h: No such file or directory` | Clone Izzi beside cartofreako or set `IZZI_SRC` |
| `gdal-config: command not found` | Install the GDAL development package or set `GDAL_CONFIG` |
| `h3/h3api.h: No such file or directory` or `cannot find -lh3` | Install the H3 development package, not only an H3 runtime/CLI package |
| `gdal_priv.h: No such file or directory` | A runtime GDAL package is present without development headers |
| `GDAL must be built with GEOS support` | Install a GEOS-enabled GDAL build and its matching development package |
| Missing `ne_10m_*.shp` | Run `make fetch-natural-earth-10m` or set `NATURAL_EARTH_DIR` |
| `sha256sum: command not found` | Install GNU coreutils and ensure its binaries are on `PATH` |
| Natural Earth checksum mismatch | Remove only the corrupt downloaded archive, then rerun the fetch target; do not bypass verification |
| Network archive/member checksum mismatch | Restore the checked-in network archive or deliberately update the archive, profile provenance, hashes, tests, documentation, and all six products together |
| Inkscape is slow on an Earth, water, Bathymetry Roulette, orbital, or network SVG | Close other large documents and inspect one layer family at a time |
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

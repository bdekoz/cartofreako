# Prerequisites

[Documentation index](../../../index.md) ·
[SVG generation pipeline](generation.md) ·
[WebAssembly workflow](../runtime/myriahedral-workflow.md)

## Current data and complete optional builds

```sh
make install-prerequisites
make check-prerequisites
make data-update
make ASSET_JOBS=2 atlas-optional
```

The installer includes scientific Python dependencies by default. When they
are unavailable to the system interpreter, it creates `.venv-data/` and
uses system site packages for the OS-provided PyGObject/Pycairo/librsvg bindings,
and installs the scientific versions in
[`scripts/requirements-atlas.txt`](../../../scripts/requirements-atlas.txt).
Make selects that interpreter automatically, including recursive Python
commands. `INSTALL_ATLAS_PREREQUISITES=0` restricts installation to native
dependencies. Scientific checks cover NumPy, SciPy, pandas, GeoPandas,
Shapely, Matplotlib, lxml, Pillow, ReportLab, Requests and Beautiful Soup,
plus NetCDF, H3, Cairo, PyGObject/librsvg, a CXX OpenMP compile/link/runtime
probe and Poppler tools (`pdfinfo`, `pdfunite`).
The direct shell checker below checks the native baseline; the Make target
also runs the scientific checker.

Acquisition preflight additionally imports `osgeo.ogr` using the selected
`ATLAS_PYTHON` interpreter. Install matching GDAL Python bindings
(`python3-gdal` on Fedora); the native `gdalinfo` executable is a separate
prerequisite. Missing Python bindings stop the update before source downloads.

Before acquisition, configure an exported `FIRMS_MAP_KEY` and a private
`PTREE_NETRC` (default `~/.netrc`) with the `ftp.ptree.jaxa.jp` entry.
The FIRMS error log includes the free registration and key-recovery URLs;
see [the generation guide](generation.md#updating-all-configured-data-sources).
India observations use the existing selected reference/AirGradient monitors
from OpenAQ's public AWS archive. This does not require expanding station
selection or entering credentials into a manifest.

Provider recovery does not require reinstalling prerequisites. Use
`make data-update-resilient DATA_UPDATE_ARGS='--defer astronomy'` to acquire
independent groups during a NASA outage. All required groups must finish
before a new edition becomes buildable. See the
[update/build settings](generation.md#update-and-build-configuration) and
[particulate options](generation.md#particulate-acquisition-options) for
cache reuse, interpreter selection and intentional revision checks.

The preflight requires configured local network checkouts, the native swarm
archive selected by `generation-style.json`, its IPinfo MMDB, the corresponding Alpha60 torrent definitions, and audited
petroleum tables. `NATIVE_SWARM_CACHE_ARCHIVE` and
`NATIVE_SWARM_GEOLOCATION_DB` can identify their actual locations. These
inputs are copied with hashes and remain explicitly pinned. `NATIVE_SWARM_DATA_ROOT`
selects the Alpha60 data root. The native swarm adapter also needs the existing
libtorrent-rasterbar and GeoLite2++ development installation selected by
`LIBTORRENT_PREFIX` and `GEOLITE2PP_PREFIX`; their source/version setup remains
the Alpha60 toolchain contract. Source checkouts
must satisfy their existing commit/digest checks; they are not pulled.

Ocean preflight also requires the 1982–2024 SST and sea-ice files plus the land
mask, each with its `.nc.json` receipt: 87 local inputs in total.
`OCEAN_HISTORY_DIR` defaults to
`output/ocean-temperature-20261108/cache/oisst` under the repository root.
To reuse an archive stored elsewhere:

```sh
make data-update-resilient OCEAN_HISTORY_DIR=/path/to/verified/cache/oisst
```

The ocean adapter verifies receipt identity, byte counts, checksums and native
grids before refreshing the four 2025/2026 files. Missing or changed history
does not trigger a historical download. `DATA_ROOT` does not relocate this
configured archive. The history supplies climatology and records for the
2025/2026 products; prepared arrays are reused only when their recorded input
and implementation hashes match.

Allow substantial local storage for 1982–2026 raw OISST files, CPC baselines,
H3 working arrays, and print exports even though only 2025/2026 OISST files
are refreshed over the network. Local historical processing may still be
needed when prepared arrays are incompatible. The acquisition preflight defaults to a
160 GiB free working-space budget; final 300 dpi exports need additional
space. `DATA_ROOT` relocates inputs/cache; outputs remain in the repository's
ignored `output/data-editions/`. Adjust `DATA_UPDATE_MIN_FREE_GIB` for a
measured warm-cache run. Full builds have separate output run directories,
so failed work cannot overwrite a completed edition. See the generation
guide for update/build resume commands and explicit historical replay.

## Requirement levels

Cartofreako has a small self-contained projection test suite and a larger SVG
generation workflow. They do not require the same software:

| Component | Required for | Purpose |
| --- | --- | --- |
| GNU Make | All Makefile targets | Expands the generated projection rules and coordinates builds |
| C++20 compiler and standard library | Tests, profile resolution, and native generators | Builds the projection checks, generation-profile resolver, sixteen SVG-generation programs, and the Anthropocene and Cloud-atmosphere preparers |
| RapidJSON development headers | Configured generation plus astronomy, Cloud-atmosphere, Orbital Technosphere, resources, Anthropocene, network-swarm, and network-infrastructure tests and generators | Parses the generation preference, authoritative data profiles, astronomy JSON, NASA SSCWeb references, normalized H3 observations, cumulative swarm GeoJSON, and infrastructure source records |
| Alpha60 headers | SVG generation | Supplies `a60-io.h` and shared runtime-resource interfaces |
| Izzi headers | SVG generation | Supplies `izzi-svg.h`, roulette and Hamonshū curve construction, and SVG document/path serialization |
| H3 development headers and library | Cloud-atmosphere, Network-swarm, and Anthropocene tests, normalization, and generation | Validates 64-bit cells, aggregates raster and point observations, computes configurable parent clusters, and creates cell boundaries with the H3 v4 API |
| GDAL development package with OGR, GeoTIFF, and NetCDF drivers | Earth, water, both bathymetry-art passes, Cloud-atmosphere, resources, global Orbital Technosphere, Anthropocene, network-swarm, and network-infrastructure generation | Reads Natural Earth/HMS vectors plus JAXA COG and P-Tree NetCDF rasters |
| GEOS support in GDAL | Natural Earth-backed generation | Performs polygon intersection, repair, and seam-safe clipping |
| Fontconfig and Atkinson Hyperlegible | Graticule, astronomy, Orbital Technosphere, resources, Anthropocene, network-swarm, network-infrastructure, and both bathymetry-art families | Resolves the default accessible label face and prevents silent font substitution |
| Ripgrep (`rg`; package name `ripgrep`) | Anthropocene Storm Events discovery and source preparation or validation scripts | Searches downloaded listings and source records; must be available in the shell running Make |
| Git, Bash, Python 3, `curl`, `jq`, `unzip`, `tar`, GNU `gzip`, `find`, `sha256sum`, and GNU coreutils including `cmp`, `date`, and `realpath` | Natural Earth, astronomy, Cloud-atmosphere, orbital, resources, Anthropocene, network-swarm, and network-infrastructure preparation or validation | Resolves static STAC metadata, downloads, verifies commits and files, compares, dates, transforms JSON, extracts or installs bounded source data, and creates deterministic compressed resource SVGs |
| Inkscape | Complete artifact generation and visual review | Exports PDF/PNG and inspects SVG layers, clipping, geometry, and seams |
| Doxygen | API reference generation | Builds the documented projection-header reference under `docs/doxygen/` |
| Emscripten, Node.js, and Chrome/Chromium | Optional WebAssembly builds | Builds and tests the all-six-projection runtime, worker and adapters, the compatibility modules, and the illustrative Myriahedral overlay |

Check the complete installed toolchain from the repository root with:

```sh
make check-prerequisites
```

The underlying checker also has a no-argument mode and can be run directly:

```sh
./scripts/check-prerequisites.sh
```

That mode locates the repository from the script path, independently of the
current working directory, and uses the working project defaults: `g++`, the
local projection and generation headers, sibling `alpha60`, `izzi`, and
`emsdk` trees, `gdal-config`, Inkscape, Doxygen, Node.js, and automatic browser
discovery. It also asks Fontconfig to resolve the configured `LABEL_FONT`.
Corresponding environment variables such as `CXX`, `ALPHA60_SRC`, `EMXX`,
`WEB_BROWSER`, and `LABEL_FONT` override those defaults.

The target verifies the native commands and sibling headers, compiles and runs
C++20/RapidJSON and H3 link/runtime probes, and compiles a GDAL probe that
checks OGR, GEOS, and the ESRI Shapefile, GeoTIFF, and NetCDF drivers. It uses
`fc-match` to reject
a missing configured label family instead of accepting Fontconfig's fallback.
Missing native prerequisites make the target fail. Optional
WebAssembly tools and a browser are always checked and reported, but do not
change the exit status. The check honors the Makefile's tool and source-tree
overrides; use `EMRUN` and `WEB_BROWSER` to identify those optional tools when
they are not discoverable at their defaults.

`make generation-plan` needs GNU Make, a C++20 compiler, and RapidJSON
headers. Bare `make` additionally needs the dependencies of the passes chosen
by the generation profile. The check suite also needs H3, GDAL development
files, the sibling Izzi/Alpha60 headers, and the checked-in astronomy,
Cloud-atmosphere fixture, Orbital Technosphere, resources, Anthropocene, network-swarm,
and network-infrastructure profiles and bounded snapshots.
It does not open Natural Earth, invoke Inkscape, or use network access.

`make check-prerequisites` also verifies that the external sibling source roots
`../cloud_cdn_cache/` and `../www.submarinecablemap.com/` exist. Override those
checks with `NETWORK_INFRASTRUCTURE_CLOUD_SOURCE` and
`SUBMARINE_CABLE_SOURCE` when the repositories live elsewhere. Commit and
digest validation remains in the stricter network-infrastructure source-check
targets.

`make all` builds 24 production whole-earth maps, 18 astronomy maps, 12
Orbital Technosphere maps, 84 Stage 12 resource maps, 12 dual-year
Anthropocene particulate maps, 12 Anthropocene temperature maps, six network-swarm maps, six
network-infrastructure site maps, six Fiber Synthesized maps, six Bathymetry Roulette maps, six
Bathymetry Hamonshū maps, five
exploratory Myriahedral water perspectives, 12 Cahill-Keyes slices, and two
Myriahedral face-group slices, then invokes Inkscape to export all 217 clean
SVG products as PDFs and 3840-pixel-long-side PNGs and adds 33
lower-resolution thumbnails per projection. A recorded `jaxa-ptree`
authorization adds the six optional Cloud-atmosphere products in all three
formats and one thumbnail per projection; that authorized local graph
therefore contains 223 full-size products and 204 thumbnails. The immutable
v13 S3 release has a different 211-product composition: its legacy observation
atlas and Cloud-atmosphere products predate the current two-year particulate
pair and the Network Groundstations pass. The 84 resources SVGs are also
retained as
deterministic `.svg.gz` companions. It needs all native build
and data-acquisition dependencies through H3 and GEOS, the
profile-pinned external cloud/CDN checkout, plus Inkscape. The separately
licensed TeleGeography topology product is not part of `make all`.
Inkscape may be omitted only when invoking individual SVG generation targets
or the offline `make check` suite.

## Generated-asset hardware sizing

Hardware requirements differ sharply between consuming a release bundle and
regenerating it. The `v20260806` static asset is 846,260,036 bytes and expands
to a 2,152,698,354-byte file payload. A download-and-extract workflow therefore
needs at least 3.0 GB free while retaining both copies; reserve 4 GB for useful
filesystem headroom. No particular CPU architecture or GPU is required to
view the PDFs and opaque 3840-pixel PNGs.

The release-qualified render host for that bundle was a Framework Desktop
with an AMD Ryzen AI Max+ 395 and Radeon 8060S, 16 physical cores/32 threads,
131,150,248 kB kernel-visible memory (about 125.1 GiB from a 128 GB-class
configuration), and 8 GiB swap. It ran `make assets-resilient` with the
Makefile's `ASSET_JOBS=2` and `PNG_LONG_SIDE=3840` defaults. The graphics
processor is recorded for provenance; Inkscape and the native generators do
not require GPU acceleration.

The Makefile does not enable `-march=native`, so the reference host's AVX2 and
AVX-512 flags are not requirements. A supported 64-bit C++20/GDAL/GEOS/H3 and
Inkscape platform is the practical CPU boundary. Sixteen cores shorten the
build but are not required by the two-job workflow.

No smaller minimum RAM has been release-qualified. In particular, the largest
SVG in `v20260806` is 118,097,662 bytes and Inkscape can use much more memory
than the serialized input size. Use a 128 GB-class machine for the same
release-production envelope, or measure and document a lower-memory host.
`make assets-resilient` finishes its incomplete graph serially after a
keep-going first pass; `make ASSET_JOBS=1 assets-resilient` and `make
assets-single` avoid concurrent export peaks on smaller machines. Reserve at
least 4 GB beyond the source and input-data checkouts for generated outputs and
atomic export temporaries, plus about 0.85 GB when packaging the XZ file in the
same workspace. That is the measured `v20260806` envelope; Stage 12 adds 54
resource maps and 28 thumbnails, so its exact higher disk requirement must be
recorded from the completed release bundle rather than inferred here.

See the [`v20260806` release notes](../releases/v20260806.md) for the complete
hardware record, byte manifest, validation results, and extraction procedure.
The source-only checkout does not contain `assets.generated/`, and `make
check` therefore verifies source, checked inputs, and native behavior without
requiring a generated release. After rendering or extracting a release, run
`make check-resources-svg-archives` to require and validate all 84 deterministic
resource gzip companions in the projection-first tree.

Cloud-atmosphere generation is an opt-in workflow outside `make all`. Its
refresh step needs network access and a registered P-Tree account available
through the user's `.netrc`; its public JAXA Earth sources need no credential.
Preparation needs H3 plus GDAL's GeoTIFF and NetCDF drivers. After installing
those dependencies, use the explicit fetch, prepare, verify, and generate
targets documented in the
[Cloud-atmosphere notes](../passes/cloud-atmosphere.md).

Normal resources generation needs only the checked profile, normalized values,
compact country and reef geometry, RapidJSON, GDAL, Natural Earth, and label font. An
explicit `make refresh-resources-data` maintainer refresh additionally needs
Python 3 with GDAL/OGR bindings, `curl`, `unzip`, and Poppler's `pdftotext`;
it is never run by normal generation. See the
[resources notes](../passes/resources/implementation.md).

## Optional external authorization

After completing provider registration and reviewing the applicable external
terms, validate all optional authorization boundaries with:

```sh
make install-jaxa-certificate

FIRMS_MAP_KEY='…' \
NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
make authorize-external
```

The check requires a private `PTREE_NETRC` (default `~/.netrc`) with a P-Tree
machine entry, the verified JAXA certificate installed by the command above, a
working NASA FIRMS key, and the three pinned topology source roots. It performs
read-only live P-Tree/FIRMS checks and offline topology commit/digest checks.
The installer uses private per-user data by default; `PTREE_CACERT` selects an
explicit absolute certificate path. Use
`EXTERNAL_PASSES='jaxa-ptree nasa-firms'` or another subset when only selected
optional passes are needed. It does not register an account, accept legal
terms, fetch production data, or generate artifacts; see
the [Stage 12 authorization notes](../../development/20260815_stage-12.md#optional-external-authorization).

To authorize and then perform the mutating workflows, use the same pass
selection or let the target discover locally configured providers:

```sh
FIRMS_MAP_KEY='…' \
NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
make generate-authorized-external

# Explicit selections are strict.
make EXTERNAL_PASSES=jaxa-ptree generate-authorized-external
```

Without an `EXTERNAL_PASSES` override, the target selects P-Tree when
`PTREE_NETRC` contains its machine entry, FIRMS when `FIRMS_MAP_KEY` is set,
and topology when `NETWORK_TOPOLOGY_LICENSE_ACCEPTED` has the exact required
value. It reports each unconfigured provider that it skips. If selected
P-Tree trust is absent, it first runs the pinned, fingerprint-verified
per-user certificate installer. An explicit pass list disables discovery and
is strict.

The target authorizes the complete resulting selection before fetching
production sources or rendering. It fetches, prepares, verifies, and exports
all cloud-atmosphere formats; prepares a global FIRMS-backed Anthropocene
candidate for required human review; and exports all licensed topology
formats. The FIRMS candidate is not rendered or promoted automatically. A
failure stops the remaining sequence but does not roll back a source snapshot
or artifact that an earlier step completed.

After every selected workflow completes, the driver atomically merges its
canonical names into `.cartofreako/authorized-external-passes`, writes the
file with mode `0600`, and prints its path. No state is written after a failed
run. Subsequent `make all` invocations include Cloud-atmosphere for a recorded
`jaxa-ptree` pass and licensed topology for a recorded `network-topology`
pass. `nasa-firms` remains refresh/review-only. Override the state path with
`EXTERNAL_AUTHORIZATION_STATE`; use
`make AUTHORIZED_EXTERNAL_PASSES= all` for a one-run standard-only build.

## Install the system packages

Install missing native dependencies and verify the result with:

```sh
make install-prerequisites
make check-prerequisites
```

Both Make targets use the plural form; the previous singular target names
have been removed.

The installer supports Fedora and related distributions, Debian/Ubuntu
(including WSL), and macOS with an existing Homebrew installation. It queries
the package manager for missing packages, including development headers,
Inkscape, ripgrep, and Fontconfig. Linux package installation uses `sudo`
when needed and can prompt for your password. Run Make as your normal user.
Already installed packages are omitted from the install request; the package
manager may still update dependencies needed by the missing packages.

The original Atkinson Hyperlegible family is installed when missing. On
systems without the font package, the installer downloads the four original
faces and their license from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/atkinsonhyperlegible)
into the user's font directory and verifies the family with Fontconfig.
If `LABEL_FONT` selects another family, install that family separately.

Missing Alpha60, Izzi, cloud/CDN, and Submarine Cable Map sibling repositories
are cloned at the configured paths; a new cloud/CDN checkout uses the
documented pinned revision. Existing directories are never pulled, reset, or
switched to another revision. The final checker honors the same compiler,
source-path, and font overrides as `make check-prerequisites` and fails if any
required dependency remains unavailable. Optional WebAssembly tools remain
optional; use the [WebAssembly workflow](../runtime/myriahedral-workflow.md)
to set up Emscripten and its browser tooling.

Preview installation without changing anything:

```sh
make install-prerequisites PREREQUISITE_INSTALL_ARGS=--dry-run
```

The commands below install a full native contributor workstation, including
Inkscape. Package names may differ on older or derivative distributions.

### Fedora and related distributions

```sh
sudo dnf install \
  python3-gobject python3-cairo librsvg2 netcdf-devel libmaxminddb-devel cairo-devel pkgconf-pkg-config poppler-utils \
  gcc-c++ make git bash python3 curl jq unzip tar gzip findutils ripgrep coreutils fontconfig \
  gdal gdal-devel geos geos-devel rapidjson-devel h3 h3-devel inkscape doxygen
```

The `-devel` packages are important: the runtime-only GDAL package does not
provide the C++ headers and link metadata used by the Makefile. Some Fedora
releases package the NetCDF driver separately; install the matching GDAL
NetCDF plugin if `make check-prerequisites` reports it missing.

### Debian and Ubuntu

```sh
sudo apt-get update
sudo apt-get install \
  python3-venv python3-gi python3-gi-cairo python3-cairo gir1.2-rsvg-2.0 libnetcdf-dev libmaxminddb-dev libcairo2-dev pkg-config poppler-utils \
  build-essential git bash python3 jq curl unzip tar gzip findutils ripgrep coreutils fontconfig \
  fonts-atkinson-hyperlegible \
  gdal-bin libgdal-dev libgeos-dev rapidjson-dev libh3-dev inkscape doxygen
```

### macOS with Homebrew

Install Apple's command-line developer tools, then the missing Unix and GIS
components:

```sh
xcode-select --install
brew install make gdal h3 rapidjson coreutils git ripgrep jq python doxygen fontconfig pygobject3 py3cairo librsvg netcdf libmaxminddb cairo pkg-config poppler libomp
brew install --cask inkscape font-atkinson-hyperlegible
```

Homebrew installs GNU Make as `gmake`. The fetch script requires
`sha256sum`, supplied by GNU coreutils. If it is not already available on
`PATH`, expose Homebrew's unprefixed coreutils commands:

```sh
export PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"
```

Use `gmake CXX=clang++` in place of `make` in the commands below. Homebrew's
GDAL formula includes GEOS support.

### Label font

Every visible text element generated by the graticule, astronomy,
Cloud-atmosphere, Orbital
Technosphere, Anthropocene, network-swarm, network-infrastructure, and both
bathymetry-art passes
defaults to the original
**Atkinson Hyperlegible** family. The Make-facing identifier is
`atkinson_hyperlegible`; the SVG serializer maps it to the installed family
name `Atkinson Hyperlegible`. The font is not embedded in SVG output, so it
must also be installed when Inkscape exports PDF and PNG artifacts.

Debian and Ubuntu provide the `fonts-atkinson-hyperlegible` package shown
above. Homebrew provides the `font-atkinson-hyperlegible` cask. On systems
without a package, download and install the original OpenType family from the
[Braille Institute's official font page](https://www.brailleinstitute.org/freefont/),
then refresh Fontconfig if the desktop installer did not do so:

```sh
fc-cache -f
fc-match -f '%{family}\n' 'Atkinson Hyperlegible'
```

The second command must report `Atkinson Hyperlegible`, not a substitute.
`make check-prerequisites` performs this exact-family check. Choose another
installed family for a deliberate variant with `LABEL_FONT`; force rebuilding
existing artifacts because changing a Make variable does not alter their file
timestamps:

```sh
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-astro
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-orbiting
make -B LABEL_FONT='Atkinson Hyperlegible Next' generate-network-infrastructure-artifacts
```

Direct generator invocations use the equivalent
`CARTOFREAKO_LABEL_FONT` environment variable. Any nonempty XML-safe family
name is accepted; the special `atkinson_hyperlegible` alias remains the
default.

### Windows

The Makefile and acquisition script assume a POSIX shell, Unix paths, Bash,
and `gdal-config`. The least surprising Windows setup is WSL2 with a Debian or
Ubuntu distribution; use the Debian/Ubuntu package list inside WSL. Native
PowerShell or `cmd.exe` is not currently a supported execution environment.

Official installation references:

- [Atkinson Hyperlegible downloads and installation](https://www.brailleinstitute.org/freefont/)
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
generation preference, astronomy, Orbital Technosphere, Anthropocene,
network-swarm, and network-infrastructure profiles, normalized observation and
cumulative swarm GeoJSON, infrastructure manifests and GeoJSON, JPL small-body
snapshots, and NASA SSCWeb response use its DOM parser. Verify the
header independently when diagnosing a compiler probe failure:

```sh
test -r /usr/include/rapidjson/document.h
```

## H3 development library

Network-swarm and Anthropocene generation use the H3 v4 C API from C++. Both
the header and linker library are required; installing an H3 command-line
program alone is not sufficient. The build includes `h3/h3api.h`, links with
`-lh3`, validates every input cell, calls `cellToParent()` for network
clustering, maps points with `latLngToCell()`, and fills HMS polygons with
`polygonToCells()`.

Useful independent checks are:

```sh
test -r /usr/include/h3/h3api.h
ldconfig -p | grep libh3
make check-prerequisites
```

Use a development package compatible with the v4 names `getResolution`,
`isValidCell`, `h3ToString`, `cellToParent`, and `polygonToCells`. The prerequisite checker
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
│       ├── izzi-svg.h
│       └── izzi-svg-curves-roulette.h
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

Earth, water, both bathymetry-art passes, and Anthropocene generation includes
`gdal_priv.h`, `ogrsf_frmts.h`, and the OGR C API. The Makefile obtains
compiler and linker arguments from:

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

The Earth, water, both bathymetry-art passes, and Anthropocene targets require Natural Earth
5.1.1's complete 1:10m physical-vector bundle. The repository does not
require a manual download:

```sh
make fetch-natural-earth-10m
```

[`scripts/fetch-natural-earth-10m.sh`](../../../scripts/fetch-natural-earth-10m.sh)
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
See the [data provenance note](../data/natural-earth.md) for the
archive URL, checksum, dataset list, and license.

## Astronomy input and network access

The astronomy SVGs and `make check` run offline from the checked-in ground and
Hubble profiles, bounded astronomy catalogs, and the checked Orbital
Technosphere CelesTrak science OMM. The profiles are authoritative for the
timestamp, platform, and instrument. Normal users run `make generate-astro`
without fetching anything first. That target and `make all` never call
`fetch-astro-data` or `fetch-orbiting-data`.

Refresh the external Gaia DR3, NASA Exoplanet Archive, and JPL SBDB snapshots
only when an upstream update is intended:

```sh
make fetch-astro-data
```

That target needs Bash, `curl`, `sha256sum`, standard Coreutils, and outbound
HTTPS access. It checks the expected row counts and replaces the bounded CSV
and JSON files before writing new hashes. It intentionally leaves the profile
and curated transient snapshot unchanged, and it does not generate maps. After
reviewing the input diff, run `make generate-astro` and `make check`; neither
command is invoked automatically. See the
[astronomy implementation notes](../passes/astronomy.md) for the data
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

That target needs Bash, Python 3, Coreutils, and outbound HTTPS access. It
validates the CelesTrak OMM schemas, catalog sizes and epoch freshness, then
writes a new dated snapshot under `build/` with `SHA256SUMS` and acquisition
receipts. The candidate uses the current UTC time (or `ORBITING_TIMESTAMP`)
and preserves the template observer location. Existing snapshots and the
generation profile remain unchanged; review the candidate before selecting
it with `ORBITING_PROFILE`.

Successful downloads less than two hours old are reused in accordance with
CelesTrak's update policy; CelesTrak HTTP refusals stop the refresh without
retrying or installing an incomplete set. NASA SSCWeb is optional: if its
current query fails, `NASA current reference unavailable` is a nonfatal
warning, and the candidate retains the checked-in 2026-08-13 NASA reference
as `historical-validation-only`. It does not validate current positions.
For example, `Network is unreachable` indicates a network connection failure;
the orbital refresh can still finish with `Created ...`. See the
[Orbital Technosphere implementation notes](../passes/orbital-technosphere.md)
for source roles, SGP4 boundaries, and refresh procedure.

## Anthropocene input preparation

Explicit `DATASET=legacy` Anthropocene builds and `make check` use the checked
`assets.static/anthropocene/` profile, normalized H3 GeoJSON and checksum.
Current-edition builds use their selected validated local inputs. Rendering
requires no provider requests. A deliberate
refresh uses Bash, `curl`, `tar`, `gzip`, `unzip`, `rg`, `find`, GNU `date`,
`sha256sum`, GDAL/OGR, H3, and substantial temporary disk space:

```sh
make fetch-anthropocene-data
make prepare-anthropocene-data
```

If fetching stops with `rg: command not found`, run `make install-prerequisites`
or install the `ripgrep` package in the environment running Make
(`sudo dnf install ripgrep` on Fedora,
`sudo apt-get install ripgrep` on Debian/Ubuntu, or `brew install ripgrep`
on macOS). Verify with `rg --version`, then rerun `make fetch-anthropocene-data`.
An editor or coding agent's private copy of `rg` may not be on your shell's
`PATH`. `make check-prerequisites` checks for the command before a full build.

The fetcher stages mutable annual sources under ignored `.raw/YEAR/`, validates
containers, records raw digests, and discovers the newest year-specific Storm
Events files. It uses annual CWFIS hotspot archives for past years and daily
files for the current year, tolerating only HTTP 404 for an absent day.
A global refresh requires `FIRMS_MAP_KEY` for five-day global NASA FIRMS
chunks, including northern Russia. Request a free key at the
[NASA FIRMS map-key page](https://firms.modaps.eosdis.nasa.gov/api/map_key/);
NASA emails it to your registered address. Export the key in the shell
running Make, as shown in the
[data-update workflow](generation.md#updating-all-configured-data-sources).
The aggregate and direct particulate fetcher check for it before downloading.
For CPC HTTP 429 responses, use the documented
[NOAA download controls](generation.md#noaa-download-controls). The downloader
shares adaptive pacing and provider cooldowns across files/processes, retains
partial bytes, and exposes retry-budget settings through Make. After a code
update, start a new `make data-update` run; shared HTTP caches remain reusable.
Completed FIRMS/CWFIS periods and historical particulate archives are retained
across runs; the NOAA-20 2025 series needs a one-time acquisition when only
S-NPP exists locally. `PARTICULATE_REFRESH=1` deliberately rechecks retained
periods. Mutable current-year bulk files still require freshness checks.
The explicit
`ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1` override stages regional data for
local pipeline debugging; it must not be promoted as a global snapshot.

The preparer verifies the raw checksum manifest, expands files in a temporary
directory, compiles station records, fills smoke polygons, joins event
locations, excludes dates at or beyond the profile snapshot boundary,
aggregates unique H3 cell-days, and writes an ignored candidate under
`.prepared/`. It never overwrites the checked snapshot. Review and promote a
refresh together with its profile coverage dates, SHA-256, tests,
documentation, and all six output families. See the
[Anthropocene implementation notes](../passes/anthropocene/implementation.md) for
the exact source and metric contracts.

## Network-swarm input preparation

Network-swarm generation and its tests run offline from the checked-in
`assets.static/network-swarm/` archive and profile. Preparation requires `unzip`,
`sha256sum`, `install`, `mktemp`, `wc`, and `cmp`:

```sh
make prepare-network-swarm-data
make generate-network-swarm
```

The safe staging script accepts a local `.zip`, `.geojson`, or `.json` through
`NETWORK_SWARM_SOURCE`. A ZIP must pass its CRC check, contain exactly one
flat JSON member, and expand to no more than 64 MiB. The prepared file is reproducible,
ignored, and retained across normal builds under
`assets.static/network-swarm/.prepared/`. `make check` validates the committed
archive SHA-256 and the prepared member SHA-256 before exercising dataset,
H3, clustering, and six-projection layout assertions.

Network-swarm rendering also needs H3, GDAL/GEOS, Natural Earth, Alpha60, and Izzi.
No outbound access is used or required. Override `NETWORK_SWARM_SOURCE` or
`NETWORK_SWARM_PROFILE` only with a deliberately reviewed,
schema-compatible input;
`NETWORK_SWARM_GEOJSON` controls the staging destination. See the
[network-swarm implementation notes](../passes/network-swarm.md) for source
semantics, profile fields, and interpretation limits.

## Network-infrastructure external sources and topology opt-in

Network-infrastructure generation is offline but intentionally reads pinned
external Git checkouts instead of vendoring their datasets. The normal site
atlas needs only the cloud/CDN checkout. With the default sibling layout:

```sh
git clone https://github.com/bdekoz/cloud_cdn_cache.git ../cloud_cdn_cache
git -C ../cloud_cdn_cache checkout 2234be5c9bce123d26639e79935e54dd8f8785a8
make check-network-infrastructure-sources
make generate-network-infrastructure
```

The checker verifies the commit, the 2026-08-05 manifest digest, and clean
consumed data/schema paths. The manifest is internally consistent at 28
canonical layers and 27,378 records. It contains 12,662 coordinate-bearing
records, but the normal profile excludes observed presences, including the new
11,659-record geocoded observation layer. The rendered set therefore remains
1,003 provider-declared locations.

Override a non-sibling checkout without editing the profile:

```sh
make NETWORK_INFRASTRUCTURE_CLOUD_SOURCE=/data/cloud_cdn_cache \
  generate-network-infrastructure-artifacts
```

The topology product adds data from the TeleGeography sources, which state
CC BY-NC-SA 3.0 Unported. Place the Submarine Cable Map `v3.20260805` export
at the configured source root. That source is content-pinned and need not be a
Git checkout. The Internet Exchange Map remains revision-pinned:

```sh
git clone https://github.com/telegeography/www.internetexchangemap.com.git \
  ../www.internetexchangemap.com
git -C ../www.internetexchangemap.com checkout \
  2b9c36ad7fad083c0b4db998c4dedadc1ba89027
make EXTERNAL_PASSES=network-topology \
  NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 \
  generate-authorized-external
```

Use `SUBMARINE_CABLE_SOURCE` and `INTERNET_EXCHANGE_SOURCE` for other roots.
The topology checker validates cloud and Internet-exchange revisions, the
cable route and landing digests, and an aggregate digest of every referenced
cable detail record. It does not inspect the cable source's Git status. The
topology profile also requires the literal
`tele_geography_opt_in: true`; ordinary generation, `make all`, and
generation-profile `"all"` never select it. Generated topology images carry
visible TeleGeography attribution and the
[CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/)
notice. Review those terms before distributing a generated topology artifact.

Both products also require RapidJSON, GDAL/GEOS, Natural Earth, Alpha60, Izzi,
and Atkinson Hyperlegible. `make check` uses synthetic infrastructure fixtures
and checked profiles, so the three external checkouts are not required for the
offline unit suite. See the
[network-infrastructure implementation notes](../passes/network-infrastructure.md)
for the precise source contract and claim boundary.

## Inkscape and visual review

Install Inkscape when reviewing or editing generated artifacts. It is useful
here because the SVGs preserve named layers for faces, quadrants, graticules,
physical features, bathymetry, and clipping regions. A browser renders the
final composition but is less useful for toggling and auditing those groups.

Verify the installation and open an artifact with:

```sh
inkscape --version
inkscape assets.generated/cahill-keyes/svg/earth-ck-44-22.svg
```

Use Inkscape's Layers and Objects panel to inspect group IDs and toggle dense
layers. Earth, water, both bathymetry-art families, and Anthropocene files can be
large, so opening and switching layers may require substantially more memory
than viewing geometry or graticules.
Saving from Inkscape can rewrite SVG formatting and metadata; avoid saving
during a read-only visual review if a serialization diff is not intended.

## Optional WebAssembly workflows

The all-six-projection browser runtime, its two compatibility adapters, and
the documented Myriahedral overlay example are separate from native SVG
generation. They require:

- an Emscripten SDK providing `em++` and `emrun`;
- Node.js for the non-browser smoke test;
- a modern browser with WebAssembly and ES-module support; and
- a local HTTP server; the browser smoke runner supplies an ephemeral one and
  `emrun` remains available for interactive development.

The WASM targets default to the sibling SDK path
`../emsdk/upstream/emscripten/em++`; override `EMXX` when the checkout lives
elsewhere. Build and test the omnibus module, including its real-browser
worker check, with:

```sh
make check-wasm-projections
make check-wasm-projections-browser
```

The two Stage 4.3 compatibility modules remain available with:

```sh
make check-wasm-cahill-keyes
make check-wasm-cahill-myriahedral
```

See the [WebAssembly quick start](../runtime/webassembly-quick-start.md) and
[runtime README](../../../src.wasm/README.md) for deployment, command buffers,
slices, workers, provenance, and the compatibility Myriahedral option that
emits only the `ocean` and `land` groups. The separate reproducible Myriahedral raster-overlay
example uses the Emscripten release identified in
[Myriahedral web workflow](../runtime/myriahedral-workflow.md). After activating the SDK, verify:

```sh
em++ --version
emrun --help
node --version
```

No production browser build needs GDAL, GEOS, Boost.Graph, Google S2, or the
historical Myriahedral preprocessing programs. The checked-in Natural Earth
fixture is not downloaded during the WASM build. The omnibus runtime performs
octant, periodic-carrier, and exact terminal-face clipping directly in
C++/WASM.

## End-to-end verification

From the repository root, a complete native setup can be checked in this
order:

```sh
test -f ../alpha60/src/a60-io.h
test -f ../izzi/src/izzi-svg.h
test -f ../izzi/src/izzi-svg-curves-roulette.h
gdal-config --ogr-enabled
make check
make fetch-natural-earth-10m
make all
inkscape --version
```

If parallel generation or Inkscape export exceeds available memory, replace
`make all` with `make assets-single`. It builds the same generated assets while
forcing the complete sub-build to run one recipe at a time, even if the outer
Make inherited a `-j` setting.

Successful generation places six geometry maps, six graticule maps, six
Earth maps, thirteen water maps (six production, five Myriahedral
perspectives, and two face-group slices), 18 astronomy maps, 12 Orbital Technosphere maps,
84 Stage 12 resources maps, 12 default Anthropocene particulate maps, 12
default Anthropocene temperature maps,
six network-swarm maps, six network-cdn site maps, six network-fiber maps,
six network-groundstations maps, six Bathymetry
Roulette maps, six Bathymetry Hamonshū maps, four quadrant slices, eight
octant slices, and two Myriahedral face-group
slices in projection-first `assets.generated/PROJECTION/svg/`, `pdf/`, and
`png/` directories; resources use `.svg.gz` inside each SVG directory. The
clean graph writes 33 480-pixel-wide thumbnails per projection under the six
`thumbnail/` directories, 198 total, for 217 standard SVG/PDF/PNG products.
The credentialed JAXA Cloud-atmosphere products are optional rather than
standard; they render through the Marshall Islands speculation pipeline and
are not part of the v14 release sheets. Every full-size PNG preserves its
source aspect ratio, has a 3840-pixel longest side, and is flattened against
opaque white.

## Common failures

| Symptom | Cause and remedy |
| --- | --- |
| `a60-io.h: No such file or directory` | Clone Alpha60 beside cartofreako or set `ALPHA60_SRC` |
| `izzi-svg.h: No such file or directory` | Clone Izzi beside cartofreako or set `IZZI_SRC` |
| `gdal-config: command not found` | Install the GDAL development package or set `GDAL_CONFIG` |
| `h3/h3api.h: No such file or directory` or `cannot find -lh3` | Install the H3 development package, not only an H3 runtime/CLI package |
| `gdal_priv.h: No such file or directory` | A runtime GDAL package is present without development headers |
| `GDAL must be built with GEOS support` | Install a GEOS-enabled GDAL build and its matching development package |
| Missing `ne_10m_*.shp` | Run `make fetch-natural-earth-10m` or set `NATURAL_EARTH_DIR` |
| `sha256sum: command not found` | Install GNU coreutils and ensure its binaries are on `PATH` |
| Natural Earth checksum mismatch | Remove only the corrupt downloaded archive, then rerun the fetch target; do not bypass verification |
| Anthropocene normalized checksum or audit mismatch | Restore the checked profile/GeoJSON pair or deliberately promote a reviewed candidate with its checksum, coverage dates, tests, documentation, and all six products |
| `FIRMS_MAP_KEY` is unset | The checked/default CWFIS fire layer still works; obtain a free NASA FIRMS map key only when deliberately refreshing global and Russian coverage |
| `authorize-external` rejects P-Tree | Put the registered credentials in the `ftp.ptree.jaxa.jp` entry of `PTREE_NETRC`, restrict the file to owner-only access, run `make install-jaxa-certificate`, and retry the read-only check |
| P-Tree fetch reports `curl: (9)` for a current date directory | Update to the latest resolver; it traverses only server-advertised directories and uses the last published observation while recording its source date |
| Network-swarm archive/member checksum mismatch | Restore the checked-in network-swarm archive or deliberately update the archive, profile provenance, hashes, tests, documentation, and all six products together |
| Cloud/CDN or submarine-cable source checkout is missing | Clone the documented repository beside `cartofreako`, or set `NETWORK_INFRASTRUCTURE_CLOUD_SOURCE` or `SUBMARINE_CABLE_SOURCE`; run `make check-prerequisites` before `make all` |
| Network-infrastructure checkout, commit, or digest mismatch | Point the Make variables at the profile-pinned external checkouts, restore the consumed tracked paths, or deliberately update the profile, tests, documentation, and artifacts together |
| Network-infrastructure topology opt-in rejected | Review the source terms, set `NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0`, then run either the read-only `make EXTERNAL_PASSES=network-topology authorize-external` check or the mutating `generate-authorized-external` target |
| Inkscape is slow on an Earth, water, bathymetry-art, orbital, Anthropocene, network-swarm, or network-infrastructure SVG | Close other large documents and inspect one layer family at a time |
| `em++: command not found` | Install and activate emsdk, then source its environment script in the current shell |

## Not required by current native targets

Historical source assets and reconstruction notes mention Perl, Python,
NumPy, Boost.Graph, and Google's S2 geometry library. They document how source
rasters or fixed tables were derived; the current production headers,
`make check`, and native SVG generators do not execute those historical
pipelines.

---

[Documentation index](../../../index.md) ·
[SVG generation pipeline](generation.md) ·
[Natural Earth data note](../data/natural-earth.md) ·
[WebAssembly workflow](../runtime/myriahedral-workflow.md)

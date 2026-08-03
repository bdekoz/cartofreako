# Complete Myriahedral WebAssembly example

[Documentation index](../index.md) ·
[Web workflow](web-workflow.md) ·
[Myriahedral implementation notes](myriahedral-implementation-notes.md) ·
[Generation pipeline](generation.md)

This is a complete, copyable example for compiling the cartofreako C++20
Myriahedral projection to WebAssembly, generating a projection overlay in the
browser, and loading the checked-in projection image beneath it.

The target frame is exactly `1920 x 1080`. The source raster is `4480 x 2520`,
so both canvases are 16:9 and the browser scales the raster uniformly by
`3/7`. No aspect-ratio approximation, crop, or geometric correction is
needed.

The example deliberately consists of three small source files:

```text
generated/wasm/
├── index.html
├── myriahedral-web.cc
└── smoke.mjs
```

The build places the two Emscripten outputs beside the browser and smoke
sources here:

```text
generated/wasm/
├── index.html
├── myriahedral-web.cc
├── myriahedral.mjs
├── myriahedral.wasm
└── smoke.mjs
```

## C++ source

Save this as `generated/wasm/myriahedral-web.cc`:

```c++
#include <array>
#include <cmath>
#include <cstddef>
#include <iomanip>
#include <sstream>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <emscripten/bind.h>

#include <a60-io.h>
#include <a60-svg.h>

#include "a60-carto-frame.h"
#include "a60-carto-projection.h"
#include "cart0freak0-myriahedral.h"

namespace {

constexpr double map_width_value = 1920;
constexpr double map_height_value = 1080;
constexpr double sample_step = 0.5;

struct geographic_point
{
  double latitude;
  double longitude;
};

struct projected_point
{
  double x;
  double y;
};

using projected_path = std::vector<projected_point>;
using projected_paths = std::vector<projected_path>;

struct projected_transition
{
  projected_point left;
  projected_point right;
  bool is_cut;
};

const a60::carto::myriaproj&
projection()
{
  static const a60::carto::frame map_frame {
    map_width_value, map_height_value
  };
  static const auto value = a60::carto::make_myriahedral_projection(
    map_frame, "assets/myriahedral/black-white-downsampled.png");
  return value;
}

projected_point
project(const geographic_point point)
{
  const auto [x, y] = projection().meridians_to_point_2d(
    point.latitude, point.longitude);
  return {x, y};
}

std::size_t
face(const geographic_point point)
{
  const double longitude = point.longitude == 180 ? -180 : point.longitude;
  return a60::carto::myriahedral_detail::containing_face(
    a60::carto::myriahedral_detail::geographic_vector(
      point.latitude, longitude));
}

geographic_point
interpolate(const geographic_point left, const geographic_point right,
            const double fraction)
{
  return {
    left.latitude + fraction * (right.latitude - left.latitude),
    left.longitude + fraction * (right.longitude - left.longitude),
  };
}

double
distance(const projected_point left, const projected_point right)
{ return std::hypot(right.x - left.x, right.y - left.y); }

void
append_unique(projected_path& path, const projected_point point)
{
  if (path.empty() || path.back().x != point.x || path.back().y != point.y)
    path.push_back(point);
}

projected_transition
find_face_transition(geographic_point left, geographic_point right,
                     const std::size_t left_face)
{
  // The deliberately fine input step makes multiple transitions unlikely.
  // This example assumes at most one face edge between adjacent samples.
  for (int iteration = 0; iteration != 48; ++iteration)
    {
      const geographic_point middle = interpolate(left, right, 0.5);
      if (face(middle) == left_face)
        left = middle;
      else
        right = middle;
    }

  const projected_point projected_left = project(left);
  const projected_point projected_right = project(right);
  return {
    projected_left,
    projected_right,
    distance(projected_left, projected_right)
      > map_width_value * 1e-5,
  };
}

projected_transition
find_coordinate_wrap(geographic_point left, geographic_point right)
{
  projected_point projected_left = project(left);
  projected_point projected_right = project(right);
  for (int iteration = 0; iteration != 48; ++iteration)
    {
      const geographic_point middle = interpolate(left, right, 0.5);
      const projected_point projected_middle = project(middle);
      if (distance(projected_left, projected_middle)
          > distance(projected_middle, projected_right))
        {
          right = middle;
          projected_right = projected_middle;
        }
      else
        {
          left = middle;
          projected_left = projected_middle;
        }
    }
  return {projected_left, projected_right, true};
}

projected_paths
project_line(const std::vector<geographic_point>& source)
{
  projected_paths result;
  if (source.empty())
    return result;

  projected_path current;
  append_unique(current, project(source.front()));
  for (std::size_t index = 1; index != source.size(); ++index)
    {
      const geographic_point left = source[index - 1];
      const geographic_point right = source[index];
      const projected_point projected_right = project(right);
      const std::size_t left_face = face(left);
      const std::size_t right_face = face(right);

      if (left_face != right_face)
        {
          const projected_transition transition
            = find_face_transition(left, right, left_face);
          append_unique(current, transition.left);
          if (transition.is_cut)
            {
              if (current.size() >= 2)
                result.push_back(std::move(current));
              current.clear();
              append_unique(current, transition.right);
            }
          else
            append_unique(current, transition.right);
        }
      else if (distance(current.back(), projected_right)
               > map_width_value / 3)
        {
          const projected_transition transition
            = find_coordinate_wrap(left, right);
          append_unique(current, transition.left);
          if (current.size() >= 2)
            result.push_back(std::move(current));
          current.clear();
          append_unique(current, transition.right);
        }

      append_unique(current, projected_right);
    }

  if (current.size() >= 2)
    result.push_back(std::move(current));
  return result;
}

std::vector<geographic_point>
parallel(const double latitude)
{
  std::vector<geographic_point> result;
  const int samples = static_cast<int>(360 / sample_step);
  result.reserve(static_cast<std::size_t>(samples + 1));
  for (int index = 0; index <= samples; ++index)
    result.push_back({latitude, -180 + index * sample_step});
  return result;
}

std::vector<geographic_point>
meridian(const double longitude)
{
  std::vector<geographic_point> result;
  const int samples = static_cast<int>(180 / sample_step);
  result.reserve(static_cast<std::size_t>(samples + 1));
  for (int index = 0; index <= samples; ++index)
    result.push_back({-90 + index * sample_step, longitude});
  return result;
}

std::string
coordinate_id(const std::string& prefix, const int coordinate)
{
  return prefix + (coordinate < 0 ? "-minus-" : "-")
         + std::to_string(std::abs(coordinate));
}

void
append_svg_path(std::ostringstream& output, const std::string& id,
                const std::string& classes,
                const projected_paths& paths)
{
  output << "<path id=\"" << id << "\" class=\"" << classes
         << "\" d=\"";
  for (const projected_path& path : paths)
    {
      if (path.size() < 2)
        continue;
      output << "M " << path.front().x << ' ' << path.front().y;
      for (std::size_t index = 1; index != path.size(); ++index)
        output << " L " << path[index].x << ' ' << path[index].y;
      output << ' ';
    }
  output << "\"/>\n";
}

std::string
generate_map_svg()
{
  // Force construction here so initialization time belongs to this call.
  static_cast<void>(projection());

  std::ostringstream output;
  output << std::fixed << std::setprecision(2);
  output
    << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    << "<svg xmlns=\"http://www.w3.org/2000/svg\" "
       "viewBox=\"0 0 1920 1080\" role=\"img\" "
       "aria-labelledby=\"map-title map-description\">\n"
    << "<title id=\"map-title\">Myriahedral 1920 by 1080 graticule</title>\n"
    << "<desc id=\"map-description\">A seam-aware graticule generated by "
       "the cartofreako C++20 Myriahedral projection compiled to "
       "WebAssembly.</desc>\n"
    << "<style>"
       ".graticule{fill:none;vector-effect:non-scaling-stroke;"
       "stroke-linecap:round;stroke-linejoin:round}"
       ".latitude{stroke:#0077bb;stroke-width:1.1;opacity:.48}"
       ".longitude{stroke:#ee7733;stroke-width:1.1;opacity:.48}"
       ".major{stroke-width:1.7;opacity:.82}"
       ".anchor{fill:#cc3311;stroke:white;stroke-width:1.5;"
       "vector-effect:non-scaling-stroke}"
       ".frame{fill:none;stroke:#222;stroke-width:1;"
       "vector-effect:non-scaling-stroke}"
       "</style>\n"
    << "<g id=\"latitudes\" class=\"graticule\">\n";

  for (int latitude = -80; latitude <= 80; latitude += 10)
    append_svg_path(
      output, coordinate_id("latitude", latitude),
      latitude % 30 == 0 ? "latitude major" : "latitude",
      project_line(parallel(latitude)));
  output << "</g>\n<g id=\"longitudes\" class=\"graticule\">\n";
  for (int longitude = -180; longitude < 180; longitude += 10)
    append_svg_path(
      output, coordinate_id("longitude", longitude),
      longitude % 30 == 0 ? "longitude major" : "longitude",
      project_line(meridian(longitude)));
  output << "</g>\n<g id=\"anchors\">\n";

  struct anchor
  {
    const char* name;
    double latitude;
    double longitude;
  };
  constexpr std::array anchors {
    anchor {"New York", 40.7128, -74.0060},
    anchor {"Paris", 48.8575, 2.3514},
    anchor {"Delhi", 28.7041, 77.1025},
    anchor {"Tokyo", 35.6895, 139.6917},
    anchor {"Sydney", -33.8688, 151.2093},
    anchor {"Sao Paulo", -23.5558, -46.6396},
  };
  for (const anchor& value : anchors)
    {
      const projected_point point = project(
        {value.latitude, value.longitude});
      output << "<circle class=\"anchor\" cx=\"" << point.x
             << "\" cy=\"" << point.y << "\" r=\"4\"><title>"
             << value.name << "</title></circle>\n";
    }

  output
    << "</g>\n"
    << "<rect class=\"frame\" x=\"0.5\" y=\"0.5\" "
       "width=\"1919\" height=\"1079\"/>\n"
    << "</svg>\n";
  return output.str();
}

double
map_width()
{ return map_width_value; }

double
map_height()
{ return map_height_value; }

std::string
source_raster()
{ return "assets/myriahedral/black-white-downsampled.png"; }

} // namespace

EMSCRIPTEN_BINDINGS(cartofreako_myriahedral_web)
{
  emscripten::function("mapWidth", &map_width);
  emscripten::function("mapHeight", &map_height);
  emscripten::function("sourceRaster", &source_raster);
  emscripten::function("generateMapSvg", &generate_map_svg);
}
```

### What the wrapper exports

The Embind block makes four ordinary functions available on the initialized
JavaScript module:

| JavaScript call | Result |
| --- | --- |
| `module.mapWidth()` | `1920` |
| `module.mapHeight()` | `1080` |
| `module.sourceRaster()` | repository-relative PNG path |
| `module.generateMapSvg()` | complete SVG overlay as a JavaScript string |

The wrapper creates the projection once as a function-local static object.
Every graticule and anchor coordinate then passes through the public
`myriaproj::meridians_to_point_2d(latitude, longitude)` API.

The implementation-detail face query is used only to keep SVG paths from
bridging a cut in the unfolded mesh. When adjacent samples enter different
triangular faces, the generator bisects the geographic interval and compares
the two projected limits. Coincident limits are a retained hinge; separated
limits start a new SVG subpath.

## Browser page

Save this as `generated/wasm/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>cartofreako Myriahedral WebAssembly example</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: system-ui, sans-serif;
    }
    body {
      margin: 0;
      padding: 1.5rem;
      background: Canvas;
      color: CanvasText;
    }
    main {
      max-width: 1920px;
      margin-inline: auto;
    }
    .map-stage {
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      overflow: hidden;
      background: #eee;
      box-shadow: 0 0 0 1px color-mix(in srgb, CanvasText 30%, transparent);
    }
    .map-stage img {
      position: absolute;
      inset: 0;
      display: block;
      width: 100%;
      height: 100%;
    }
    #generated-map {
      pointer-events: none;
    }
    #status {
      min-height: 1.5em;
    }
  </style>
</head>
<body>
  <main>
    <h1>Myriahedral map generated with C++20 and WebAssembly</h1>
    <p id="status" aria-live="polite">Loading WebAssembly…</p>
    <figure>
      <div class="map-stage"
           role="img"
           aria-label="Myriahedral source raster with a generated graticule and city anchors">
        <img id="projection-raster" alt="">
        <img id="generated-map" alt="">
      </div>
      <figcaption>
        The browser scales the registered 4480×2520 raster and the
        WASM-generated 1920×1080 SVG through the same 16:9 viewport.
      </figcaption>
    </figure>
    <p><a id="download" download="myriahedral-1920x1080.svg" hidden>
      Download the generated SVG overlay
    </a></p>
  </main>

  <script type="module">
    import createMyriahedralModule from "./myriahedral.mjs";

    const status = document.querySelector("#status");
    const raster = document.querySelector("#projection-raster");
    const generatedMap = document.querySelector("#generated-map");
    const download = document.querySelector("#download");

    function loadImage(element, url) {
      return new Promise((resolve, reject) => {
        element.addEventListener("load", resolve, {once: true});
        element.addEventListener(
          "error",
          () => reject(new Error(`Could not load ${url}`)),
          {once: true}
        );
        element.src = url;
      });
    }

    try {
      const module = await createMyriahedralModule();
      const width = module.mapWidth();
      const height = module.mapHeight();
      raster.width = generatedMap.width = width;
      raster.height = generatedMap.height = height;

      // This page is deployed as generated/wasm/index.html, two levels below the
      // repository root where assets/myriahedral lives.
      const repositoryRoot = new URL("../../", window.location.href);
      const rasterUrl = new URL(module.sourceRaster(), repositoryRoot);
      const rasterReady = loadImage(raster, rasterUrl.href);

      status.textContent = "Generating the seam-aware SVG graticule…";
      const svg = module.generateMapSvg();
      const generatedUrl = URL.createObjectURL(
        new Blob([svg], {type: "image/svg+xml"})
      );
      const generatedReady = loadImage(generatedMap, generatedUrl);

      download.href = generatedUrl;
      download.hidden = false;
      await Promise.all([rasterReady, generatedReady]);
      status.textContent =
        `Ready: ${width}×${height}, ${svg.length.toLocaleString()} SVG characters.`;

      window.addEventListener(
        "pagehide",
        () => URL.revokeObjectURL(generatedUrl),
        {once: true}
      );
    } catch (error) {
      status.textContent = `Generation failed: ${error.message}`;
      console.error(error);
    }
  </script>
</body>
</html>
```

The two images are registered by construction:

- the lower image is the checked-in Myriahedral raster;
- the upper image is the transparent SVG returned by WASM; and
- both occupy the same responsive 16:9 CSS box.

The page must be served from the repository root with its build output at
`build/web`. That layout is why `../../` from the page resolves to the
repository root and makes `assets/myriahedral/black-white-downsampled.png`
available without copying it.

Do not revoke the generated Blob URL immediately after assigning it. The URL
must remain alive while the overlay image and download link use it; this page
revokes it on `pagehide`.

## Node smoke test

Save this as `generated/wasm/smoke.mjs`:

```js
import assert from "node:assert/strict";
import {statSync, writeFileSync} from "node:fs";
import createMyriahedralModule from "./myriahedral.mjs";

const module = await createMyriahedralModule();
assert.equal(module.mapWidth(), 1920);
assert.equal(module.mapHeight(), 1080);
assert.equal(
  module.sourceRaster(),
  "assets/myriahedral/black-white-downsampled.png"
);

const svg = module.generateMapSvg();
assert.match(svg, /viewBox="0 0 1920 1080"/);
assert.match(svg, /id="latitudes"/);
assert.match(svg, /id="longitudes"/);
assert.match(svg, /New York/);
assert.doesNotMatch(svg, /(?:nan|inf)/i);
assert.ok((svg.match(/<path /g) ?? []).length === 53);
assert.ok(svg.length > 500000);
const svgUrl = new URL("./myriahedral-1920x1080.svg", import.meta.url);
const wasmUrl = new URL("./myriahedral.wasm", import.meta.url);
writeFileSync(svgUrl, svg);

console.log(JSON.stringify({
  wasmBytes: statSync(wasmUrl).size,
  svgBytes: Buffer.byteLength(svg),
  paths: (svg.match(/<path /g) ?? []).length
}));
```

The Node test exercises the same ES module and WASM binary as the browser. It
checks dimensions, asset registration, stable layer IDs, finite coordinates,
and the expected 17 latitude plus 36 longitude paths. Its output SVG is
written beside the smoke script regardless of the shell's current directory.

## Build

From the repository root, activate the local SDK and prepare the output
directory:

```sh
source /home/bkoz/src/emsdk/emsdk_env.sh
mkdir -p generated/wasm
```

Copy the three source blocks above into `generated/wasm/`, then compile:

```sh
em++ generated/wasm/myriahedral-web.cc \
  -I src \
  -isystem ../alpha60/src \
  -isystem ../izzi/src \
  -std=c++20 \
  -O3 \
  -Wall -Wextra -Wpedantic -Werror \
  --bind \
  --no-entry \
  -sMODULARIZE=1 \
  -sEXPORT_ES6=1 \
  -sEXPORT_NAME=createMyriahedralModule \
  -sENVIRONMENT=web,node \
  -sALLOW_MEMORY_GROWTH=1 \
  -sFILESYSTEM=0 \
  -o generated/wasm/myriahedral.mjs
```

The neighboring Alpha60 and Izzi headers are system includes so their own
warnings do not fail this wrapper's strict `-Werror` build. The cartofreako
headers remain normal includes and therefore remain covered by those warning
flags.

If the SDK checkout is read-only to the build account, select a writable
task-specific cache before compiling:

```sh
export EM_CACHE=/tmp/cartofreako-emscripten-cache
```

## Verify without a browser

Run the smoke test from any directory:

```sh
node /absolute/path/to/cartofreako/generated/wasm/smoke.mjs
```

For Emscripten 6.0.5, the verified build reported:

```json
{"wasmBytes":270756,"svgBytes":574903,"paths":53}
```

Compiler revisions can change the byte counts. The assertions on dimensions,
IDs, finite output, and path count are the behavioral checks.

## Run in a browser

From the cartofreako repository root:

```sh
emrun \
  --no_browser \
  --serve_after_close \
  --serve_root "$PWD" \
  --port 8000 \
  generated/wasm/index.html
```

Open:

```text
http://localhost:8000/generated/wasm/index.html
```

The status first reports WASM loading and SVG generation, then shows the
intrinsic size and generated character count. The visible result is the
black-and-white Myriahedral projection image with blue latitude paths, orange
longitude paths, and six red city anchors. The download link saves the
generated SVG overlay independently of the raster.

Opening the page directly with `file://` will not work reliably because the
ES module fetches its companion `.wasm` file. A different server is fine as
long as it serves `.mjs` as JavaScript, `.wasm` as `application/wasm`, and
the build and asset paths from one origin.

## Changing the output size

For this fixed raster-compatible Myriahedral layout, keep the exact 16:9
relationship. Replace both C++ constants together, for example:

```c++
constexpr double map_width_value = 1280;
constexpr double map_height_value = 720;
```

The SVG `viewBox`, frame rectangle, and title in this compact example are
literal 1920×1080 values and must be updated at the same time. For a reusable
runtime-sized API, serialize those values from the constants and accept only
frames satisfying `width / height == 16 / 9` within the projection API's
normal floating-point tolerance.

Changing only the CSS display size does not require recompilation. The
`aspect-ratio: 16 / 9` stage scales both layers together while the generated
coordinate system remains 1920×1080.

## Production extensions

This example favors an inspectable end-to-end path. A production viewer can
build on it by:

- moving module initialization and generation into a Web Worker;
- caching the SVG by projection version, frame, and layer settings;
- replacing the fixed 0.5-degree sampling with projected chord-error
  subdivision;
- exposing layer density and visibility controls through Embind; and
- returning UTF-8 bytes instead of a JavaScript string for very large maps.

For the numeric and perceptual reasoning behind those choices, see the
[web workflow](web-workflow.md#seam-aware-graticule-generation) and the
[general generation notes](generation.md).

---

[Documentation index](../index.md) ·
[Web workflow](web-workflow.md) ·
[Myriahedral implementation notes](myriahedral-implementation-notes.md) ·
[Generation pipeline](generation.md)

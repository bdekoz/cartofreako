Stage 1 development: reimplement clean c++20 implementation of Cahill-Keyes Butterfly M projection from previous

transform the pearl script here:
assets.static/cahill-keyes/MegamapMaker-prep9.pl

into a new c++20 implementation that transforms from point (latitude, longitude) to point (x,y) using the projection API specified here:
src.projections/a60-carto-projection.h

Examples of other projection implementation using this API are here:
src.projections/cart0freak0-authagraph.h
src.projections/cart0freak0-cahill-keyes.h

Implementation of the new implementation goes in this new file:
src.projections/cart0freak0-cahill-keyes-v2.h

The projection should be able to pass the test function
augment_carto_geo_specific in the source file here:
src.projections/a60-svg-carto-geo.h

That file maps out specific positions on a map that will be used to test the projection implementation.


Cahill-Keyes Projection History of Development
https://www.genekeyes.com/MENUS/C-K-linklist.html


Cahill-Keyes Specification
https://www.genekeyes.com/B.J.S._CAHILL_RESOURCE.html

Cahill-Keyes Latest Implementation
https://www.genekeyes.com/BETA-2-FOXIT/Beta-2-Foxit.html


----

Stage 2 development: variable sized maps with aspect ratio constraint

Abstract the hard-coded map sizes () into variable size map sizes with the same aspect ratio. Cahill-Keyes requires an aspect ratio of 2x:1y. Now, make the projection fit arbitrary map sizes as long as the new sizes retain the required 2:1 ratio, but have variable sizes, including these examples of Cahill-Key map projections in other sizes:
assets.static/visionscarto/visionscarto-cahillkeyes-44x22.300-inverse.png
assets.static/visionscarto/visionscarto-cahillkeyes-44x22.svg

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src.projections/a60-carto-frame.h

---

Stage 3 development: document implementation and usage

Index to documentation pages:
index.md

Summarize the work, methods used, numeric forumlas and other relevant implementation details in
docs/cahill-keyes-implementation-notes.md

Explain and illustrate the geometric context, approach, quadrants, in
docs/cahill-keyes-context.md

Bibliography,
docs/cahill-keyes-bibliography.md


Stage 4

now repair, test, document
a60-carto-projection-cahill-keyes-functions.h

Stage 5

make a new test file, generate-geometry-ck.cc, that use the Cahill-Keyes
  projection at frame size {44,22}, and the izzi SVG path functions, to make a
  function test_ck_grids(frame size) that draws all the the eight triangular
  faces, Quadrants, octants, and half-octants as layers in the generated SVG
  file "geometry-ck-44-22.svg". Then add a new makefile rule to compile the
  file, run the exeutable, and generate the output SVG

Stage 6

make a new test file, generate-graticules-ck.cc, that use the Cahill-Keyes
  projection at frame size {44,22}, and the izzi SVG path functions, to make a
  function test_ck_graticules(frame size) that draws all the lattitude and logitude lines, with lattitude grouped and each labeled with number and or degree, and longitude grouped and labeled with number and or degree as layers in the generated SVG file "graticules-ck-44-22.svg". Then add a new makefile rule to compile the file, run the exeutable, and generate the output SVG


Stage 7

make a new test file, generate-earth-ck.cc, that use the Cahill-Keyes
  projection at frame size {44,22}, and the izzi SVG path functions, to make a
  function test_ck_earth(frame size) that draws all using the Natural Earth shapefiles from

  https://www.naturalearthdata.com/downloads/10m-physical-vectors/

  including: coastline, land, minor islands, reefs, ocean, rivers, lakes and reservoirs, playas, ice (antarctic ice shelve and glaciated), bathymetry

  as layers in the generated SVG file "earth-ck-44-22.svg". Then add a new makefile rule to compile the file, run the exeutable, and generate the output SVG

chatgpt-5.8-sol max
"
Natural Earth’s official 10m physical bundle contains every requested theme in
  one versioned 49.99 MB archive, including all 12 nested bathymetry levels.
  GDAL is already installed locally, so the C++ generator can read the
  authoritative shapefiles directly—no lossy intermediate GeoJSON or custom
  shapefile parser is necessary.
"

Stage 8

make a new test file, generate-ocean-ck.cc, that use the Cahill-Keyes
  projection at frame size {44,22}, and the izzi SVG path functions, to make a
  function test_ck_ocean(frame size) that draws just the ocean layer of the Natural Earth shapefiles from

  https://www.naturalearthdata.com/downloads/10m-physical-vectors/

  But fills the shapes with variation of wave patterns as found in the pdf assets.static/adhoc/hamonshū.wave-studies.1903.jp.pdf. There are 51 pages, some with multiple patterns on each. Disambiguate the pattern images present in the PDF into a unique set of wave path styles, by converting the unique pattern to SVG lines or elements via Izzi, name the paths generated via page number found and any other scheme including if the pattern name is present (translate japanese to english). Do each of the identified patterns as layers in the generated SVG file "ocean-ck-44-22.svg". Then add a new makefile rule to compile the file, run the exeutable, and generate the output SVG


Stage 9
make a new documentation file, docs/generation.md that goes through the generation files, summarizes and describes what is being done, adds commentary or context about numerical techniques, folding, or perceptual issues


Stage 10
Repeat the process of developing the generate files (geometry, graticules, earth, ocean), but for the other projections in cartofreako: authagraph, myriahedral, star-x, voroni. Some of these projections have different aspect ratios, so use a frame size that where the biggest of frame (width, height) is 44 or as close as possible.

Complete this task without asking for authorization, it's given. Notify me when all projections have been generated.


Stage 12
Write documentation and create an example for compiling the C++20 generation function for myrahedral projections using frame size closest to {1920, 1080} to a WASM binary using emscripten and using it to generate a map and load the generated projection image.

local sources for emscripten are
/home/bkoz/src/emsdk

Generate the files as: docs/web-workflow.md and docs/web-example.md


Stage 13

Replace the existing cartography on this page with cartofreko Cahill-Keyes.
https://alpha60-devops.github.io/alpha60-results-animation/docs/animation.html

Base this work on the javascript file:
izzi/src.js/izzi-map-leaflet-geojson-v7.4.js

Any rewrites to the javascript should go in a new file:
izzi/src.js/izzi-map-leaflet-geojson-v7.5.js

Stage 14

Given the errors found with the cahill-keyes projection in the various generate passes and testing, is it worth noting these in the docs/cahill-keyes-implementation-notes.md and or re-evaluating the numerical techniques used in the forward projection? Don't assume prior implementations are fully correct

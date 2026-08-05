Stage 1 development:
implement a new C++20 dymaxion projection in the file src.projections/a60-carto-
  projection-dymaxion.h using the same carto API as previous.

  Base on:
  - https://www.bfi.org/
  - https://en.wikipedia.org/wiki/Dymaxion_map
  - https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/fuller.html


----

Stage 2 development: variable sized maps with aspect ratio constraint

Abstract any hard-coded map sizes () into variable size map sizes with the same aspect ratio.

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src.projections/a60-carto-frame.h

Add this projection to the generate-* routines, alongside existing projections like voronoi, cahill-keyes, etc.

---

Stage 3 development: document implementation and usage


Add Dymaxion projection documentation

Index to documentation pages:
index.md

Summarize the work, methods used, numeric forumlas and other relevant implementation details in
docs/dymaxion-implementation-notes.md

Explain and illustrate the geometric context, approach, quadrants, in
docs/dymaxion-context.md

Bibliography,
docs/dymaxion-bibliography.md

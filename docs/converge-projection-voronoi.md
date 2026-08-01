Stage 1 development:
implement a new C++20 voronoi projection in the file src/a60-carto-
  projection-voronoi.h using the same carto API as previous. 
  
  Base on D3js Vornoi projection
  
----

Stage 2 development: variable sized maps with aspect ratio constraint

Abstract any hard-coded map sizes () into variable size map sizes with the same aspect ratio.

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src/a60-carto-frame.h

---

Stage 3 development: document implementation and usage


Add Voronoi projection documentation

Index to documentation pages:
index.md

Summarize the work, methods used, numeric forumlas and other relevant implementation details in
docs/voronoi-implementation-notes.md

Explain and illustrate the geometric context, approach, quadrants, in
docs/voronoi-context.md

Bibliography,
docs/voronoi-bibliography.md

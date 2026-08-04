Stage 1 development: reimplement clean c++20 implementation of Myriahedral projection from previous attempt here:
https://github.com/temporaer/myriaworld

Use the base image as
assets.static/myriahedral/black-white-downsampled.png

The new c++20 implementation transforms from point (latitude, longitude) to point (x,y) using the projection API specified here:
src.projections/a60-carto-projection.h

Examples of other projection implementation using this API are here:
src.projections/cart0freak0-authagraph.h
src.projections/cart0freak0-cahill-keyes.h

Implementation of the new implementation goes in this new file:
src.projections/cart0freak0-myriahedral.h

The projection should be able to pass the test function
augment_carto_geo_specific in the source file here:
src.projections/a60-svg-carto-geo.h

That file maps out specific positions on a map that will be used to test the projection implementation.

----

Stage 2 development: variable sized maps with aspect ratio constraint

Now, make the projection fit arbitrary map sizes as long as the new sizes retain the any required ratio.

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src.projections/a60-carto-frame.h

---

Stage 3 development: document implementation and usage

Index to documentation pages:
index.md

Summarize the work, methods used, numeric forumlas and other relevant implementation details in
docs/myriahedral-implementation-notes.md

Explain and illustrate the geometric context, approach, quadrants, in
docs/myriahedral-context.md

Bibliography,
docs/myriahedral-bibliography.md

---

Stage 4 development: explore the set configuration referenced previously that produced this input image: assets.static/myriahedral/black-white-downsampled.png

Add a new section of

docs/myriahedral-implementation-notes.md

that talks about that set of metadata required to accurately describe that particular perspective, and suggest 3-5 other perspectives that merit investigation, and generate their configuration metadata.

Generate ocean images of the suggested new perspectives and link to the implementation notes page.

---

Stage 5 development: Use what you know of quarto and octo slicing from the Cahill-Keyes projection and try to apply it to the myriahedral projection. What types of slicing would you suggest?

Implement two ad-hoc slicing groups: 
  group 1: north america, south america, antarctica, greenland, iceland
  group 2: all the rest
  
  
Generate ocean images of the suggested slices as per "make all"

Add a new section of

docs/myriahedral-implementation-notes.md

That describes this slicing



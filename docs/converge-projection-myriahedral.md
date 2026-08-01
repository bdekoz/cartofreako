Stage 1 development: reimplement clean c++20 implementation of Myriahedral projection from previous attempt here:
https://github.com/temporaer/myriaworld

Use the base image as
assets/myriahedral/black-white-downsampled.png

The new c++20 implementation transforms from point (latitude, longitude) to point (x,y) using the projection API specified here:
src/a60-carto-projection.h

Examples of other projection implementation using this API are here:
src/a60-carto-projection-cahill-keyes.h
src/a60-carto-projection-un.h

Implementation of the new implementation goes in this new file:
src/a60-carto-projection-myriahedral.h

The projection should be able to pass the test function
augment_carto_geo_specific in the source file here:
src/a60-svg-carto-geo.h

That file maps out specific positions on a map that will be used to test the projection implementation.

----

Stage 2 development: variable sized maps with aspect ratio constraint

Now, make the projection fit arbitrary map sizes as long as the new sizes retain the any required ratio.

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src/a60-carto-frame.h

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

Stage 1 development: reimplement clean c++20 implementation of Cahill-Keyes Butterfly M projection from previous

transform the pearl script here:
assets/cahill-keyes/MegamapMaker-prep9.pl

into a new c++20 implementation that transforms from point (latitude, longitude) to point (x,y) using the projection API specified here:
src/a60-carto-projection.h

Examples of other projection implementation using this API are here:
src/a60-carto-projection-cahill-keyes.h
src/a60-carto-projection-un.h

The projection should be able to pass the test function
augment_carto_geo_specific in the source file here:
src/a60-svg-carto-geo.h

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
assets/visionscarto/visionscarto-cahillkeyes-44x22.300-inverse.png
assets/visionscarto/visionscarto-cahillkeyes-44x22.svg

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src/a60-carto-frame.h

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

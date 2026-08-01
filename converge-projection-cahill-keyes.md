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

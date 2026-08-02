Stage 1 development:
implement a new C++20 projection in the file src/cart0freak0-star-x.h using
the same carto API as previous.
  
  Base on the existing Cahill-Keyes implementation, but with the following modification to the geometry: The octants are split in two, with octants 1-4 (left side) as group 1 and octants 5-8 (the right side) as group 2.
  
 Group 2 is rotated 180 degrees and placed on top of group 1 such that the geometry forms an X shape, with what would be the north pole in the middle. 
  
----

Stage 2 development: variable sized maps with aspect ratio constraint

Abstract any hard-coded map sizes () into variable size map sizes with the same aspect ratio.

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src/a60-carto-frame.h

---

Stage 3 development: document implementation and usage

Index to documentation pages:
index.md

Summarize the work, methods used, numeric forumlas and other relevant implementation details in
docs/star-x-implementation-notes.md

Explain and illustrate the geometric context, approach, quadrants, in
docs/star-x-context.md

Bibliography,
docs/star-x-bibliography.md


--

Stage 4

adjust star-x projection implementation such that the gap between octant group 1 and octant group 2 is configurable. Then, set the defaults such that for the {44,22} example in generate geometry, the bottom octant is moved 2.25" higher, and the top group is lowered 2.25" lower. The goal is for them to both touch at 22", the center of the frame. There is too much space inbetween in the current geometry-star-x-34-44.svg.


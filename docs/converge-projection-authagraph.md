Stage 1 development:
implement a new C++20 authagraph projection in the file src.projections/a60-carto-
  projection-authagraph.h using the same carto API as previous. 
  
  Base image for the authagraph projection is:
  asets/authagraph/15-SP-TESD-03-AG.pdf
  
  From:
  https://narukawa-lab.jp/archives/authagraph-map/
  
  https://www.jstage.jst.go.jp/article/jjca/60/1/60_1/_article/-char/en?novirtualissue=100253
  
  
  
  Formula in:
  Formulation of AuthaGraph Map Projection and an Evaluation of its Distortion
Hajime NARUKAWA
Map, Journal of the Japan Cartographers Association
2022 Volume 60 Issue 1 1-16
Published: March 31, 2022
Released on J-STAGE: September 14, 2023
  
  
  https://www.jstage.jst.go.jp/article/jjca/60/1/60_1/_pdf/-char/en?download=1
  
----

Stage 2 development: variable sized maps with aspect ratio constraint

Abstract any hard-coded map sizes () into variable size map sizes with the same aspect ratio.

Use the a60::carto::frame abstraction for the size of the variable projection, aka

struct area { double x, double y}; from frame.frame_area here:
src.projections/a60-carto-frame.h

---

Stage 3 development: document implementation and usage

Index to documentation pages:
index.md

Summarize the work, methods used, numeric forumlas and other relevant implementation details in
docs/authagraph-implementation-notes.md

Explain and illustrate the geometric context, approach, quadrants, in
docs/authagraph-context.md

Bibliography,
docs/authagraph-bibliography.md

This is the human review of v15 artifacts.


Those artifacts are:
/home/bkoz/src/cartofreako/assets.generated.20280815.tar.xz

Color revised resources are:
/home/bkoz/src/cartofreako/assets.generated.20260815.msp.edit/


Please revise v15, and generate v15.1 with the following changes.

1) Use the color revised resources to change generated artifacts to match. Adopt new color profiles, adjust izzi generation colors. Apply the newly-revised and updated colors to the other projections.

2) Adjust the label placement on all maps. The current legend placement (top left) is clipping the underlying cartography in the folloing projections: authagraph, dymaxion. This can be seen in any of the anthropocene-* images, including particulate and temperature for both year 2025 and 2026. Propose moving legend to Bottom Right, and make no clipping/masking a requirement for the legend. (Clipping Antartica is ok)

3) In (/home/bkoz/src/cartofreako/assets.generated.20260815.msp.edit/orbital-technosphere-global-authagraph-44-19.052559 copy.webp), remove the black background and make it white.

4) In (astro-observer-ground-multiband-authagraph-44-19.052559 copy.webp), the  ("3C 273" label is clipped, move it in so it's not clipped. Increase the line weight of that 2x and make it white, and do the same for whatever is clipping the Mercury and Sagitarius A orbits, it is too small to be seen with the visible eye. Make 2x and white.

Also, For the Stationary Items on this page (Cygnus X-1, Centaurus A, 433 Eros, etc), augment each point with izzi make_line_rays n=10



For some of the color matching and adjustment, examine if using sol-5.6 via API key would be simpler.

Write proposal to
20260823_map_msp_color_style_edit_v2_stage_1.md

CXX ?= g++
PROJECTION_SRC_DIR := src.projections
GENERATOR_SRC_DIR := src.generate
TEST_DIR := tests
STATIC_ASSET_DIR := assets.static
GENERATED_DIR := assets.generated
WEB_DIR := src.wasm
CPPFLAGS ?= -I$(PROJECTION_SRC_DIR) -I$(GENERATOR_SRC_DIR)
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Wpedantic -Werror
ALPHA60_SRC ?= ../alpha60/src
IZZI_SRC ?= ../izzi/src
GDAL_CONFIG ?= gdal-config
DOXYGEN ?= doxygen
INKSCAPE ?= inkscape
PNG_LONG_SIDE ?= 3840
PNG_EXPORT_BACKGROUND := --export-background=white \
	--export-background-opacity=255 \
	--export-png-color-mode=RGB_8
EMXX ?= ../emsdk/upstream/emscripten/em++
EMRUN ?= $(patsubst %em++,%emrun,$(EMXX))
NODE ?= node
WEB_BROWSER ?=
EM_CACHE ?= /tmp/cartofreako-emscripten-cache
GENERATION_PROFILE ?= generation-profile.json
NATURAL_EARTH_DIR ?= $(STATIC_ASSET_DIR)/natural-earth/10m-physical-vectors
NATURAL_EARTH_FETCHER := scripts/fetch-natural-earth-10m.sh
ASTRO_DATA_DIR ?= $(STATIC_ASSET_DIR)/astronomy
ASTRO_PROFILE ?= $(ASTRO_DATA_DIR)/astro-profile.json
ASTRO_FETCHER := scripts/fetch-astro-data.sh
ORBITING_DATA_DIR ?= $(STATIC_ASSET_DIR)/orbital-technosphere
ORBITING_PROFILE ?= \
	$(ORBITING_DATA_DIR)/orbital-technosphere-profile.json
ORBITING_FETCHER := scripts/fetch-orbiting-data.sh
NETWORK_DATA_DIR ?= $(STATIC_ASSET_DIR)/network
NETWORK_PROFILE ?= $(NETWORK_DATA_DIR)/network-profile.json
NETWORK_SOURCE ?= \
	$(NETWORK_DATA_DIR)/house-of-the-dragon-301-cumulative-aggregate.geojson.zip
NETWORK_PREPARED_DIR ?= $(NETWORK_DATA_DIR)/.prepared
NETWORK_GEOJSON ?= $(NETWORK_PREPARED_DIR)/$(patsubst %.zip,%,$(notdir $(NETWORK_SOURCE)))
NETWORK_PREPARER := scripts/prepare-network-data.sh
PREREQUISITE_CHECKER := scripts/check-prerequisites.sh
NATURAL_EARTH_STAMP := \
	$(NATURAL_EARTH_DIR)/.natural-earth-10m-physical-5.1.1
GENERATED_SVG_DIR := $(GENERATED_DIR)/svg
GENERATED_PNG_DIR := $(GENERATED_DIR)/png
GENERATED_PDF_DIR := $(GENERATED_DIR)/pdf
DOXYGEN_CONFIG := Doxyfile
DOXYGEN_OUTPUT_DIR := docs/doxygen
DOXYGEN_HEADERS := $(wildcard $(PROJECTION_SRC_DIR)/cart0freak0*.h) \
	$(PROJECTION_SRC_DIR)/a60-carto-projection-dymaxion.h
WEB_BUILD_DIR := $(WEB_DIR)
CK_WEB_SOURCE := $(WEB_DIR)/cahill-keyes-web.cc
CK_WEB_LAND := $(WEB_DIR)/cartofreako-cahill-keyes-land-110m.geojson
CK_WEB_SMOKE := $(WEB_DIR)/cahill-keyes-smoke.mjs
CK_WEB_MODULE := $(WEB_BUILD_DIR)/cartofreako-cahill-keyes.mjs
CK_WEB_WASM := $(WEB_BUILD_DIR)/cartofreako-cahill-keyes.wasm
MYRIA_WEB_SOURCE := $(WEB_DIR)/cahill-myriahedral.cc
MYRIA_WEB_LAND := $(CK_WEB_LAND)
MYRIA_WEB_SMOKE := $(WEB_DIR)/cahill-myriahedral-smoke.mjs
MYRIA_WEB_MODULE := $(WEB_BUILD_DIR)/cartofreako-cahill-myriahedral.mjs
MYRIA_WEB_WASM := $(WEB_BUILD_DIR)/cartofreako-cahill-myriahedral.wasm

GEOMETRY_GENERATOR := $(GENERATOR_SRC_DIR)/generate-geometry
GRATICULE_GENERATOR := $(GENERATOR_SRC_DIR)/generate-graticules
EARTH_GENERATOR := $(GENERATOR_SRC_DIR)/generate-earth
WATER_GENERATOR := $(GENERATOR_SRC_DIR)/generate-water
BATHYMETRY_ROULETTE_GENERATOR := \
	$(GENERATOR_SRC_DIR)/generate-bathymetry-roulette
FOUR_SLICE_GENERATOR := $(GENERATOR_SRC_DIR)/generate-4-slice
EIGHT_SLICE_GENERATOR := $(GENERATOR_SRC_DIR)/generate-8-slice
MYRIAHEDRAL_SLICE_GENERATOR := \
	$(GENERATOR_SRC_DIR)/generate-myriahedral-slices
ASTRO_GENERATOR := $(GENERATOR_SRC_DIR)/generate-astro
ORBITING_GENERATOR := $(GENERATOR_SRC_DIR)/generate-orbiting
NETWORK_GENERATOR := $(GENERATOR_SRC_DIR)/generate-network
GENERATION_PROFILE_RESOLVER := \
	$(GENERATOR_SRC_DIR)/resolve-generation-profile
SGP4_SOURCE := $(GENERATOR_SRC_DIR)/third_party/sgp4/SGP4.cpp
SGP4_HEADER := $(GENERATOR_SRC_DIR)/third_party/sgp4/SGP4.h
SGP4_OBJECT := $(GENERATOR_SRC_DIR)/third_party/sgp4/SGP4.o

ASTRO_PROFILE_DIR := $(dir $(ASTRO_PROFILE))
ASTRO_CATALOGS := $(filter-out $(ASTRO_PROFILE),\
	$(wildcard $(ASTRO_PROFILE_DIR)*.csv $(ASTRO_PROFILE_DIR)*.json))
ORBITING_PROFILE_DIR := $(dir $(ORBITING_PROFILE))
ORBITING_CATALOGS := $(filter-out $(ORBITING_PROFILE),\
	$(wildcard $(ORBITING_PROFILE_DIR)*.csv $(ORBITING_PROFILE_DIR)*.json \
		$(ORBITING_PROFILE_DIR)SHA256SUMS))

CK_GEOMETRY_SVG := $(GENERATED_SVG_DIR)/geometry-ck-44-22.svg
CK_GRATICULE_SVG := $(GENERATED_SVG_DIR)/graticules-ck-44-22.svg
CK_EARTH_SVG := $(GENERATED_SVG_DIR)/earth-ck-44-22.svg
CK_WATER_SVG := $(GENERATED_SVG_DIR)/water-ck-44-22.svg
CK_FOUR_SLICE_SVGS := \
	$(GENERATED_SVG_DIR)/earth-ck-4-slice-1.svg \
	$(GENERATED_SVG_DIR)/earth-ck-4-slice-2.svg \
	$(GENERATED_SVG_DIR)/earth-ck-4-slice-3.svg \
	$(GENERATED_SVG_DIR)/earth-ck-4-slice-4.svg
CK_EIGHT_SLICE_SVGS := \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-1.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-2.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-3.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-4.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-5.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-6.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-7.svg \
	$(GENERATED_SVG_DIR)/earth-ck-8-slice-8.svg
CK_SLICE_SVGS := $(CK_FOUR_SLICE_SVGS) $(CK_EIGHT_SLICE_SVGS)

AUTHAGRAPH_GEOMETRY_SVG := $(GENERATED_SVG_DIR)/geometry-authagraph-44-19.052559.svg
AUTHAGRAPH_GRATICULE_SVG := $(GENERATED_SVG_DIR)/graticules-authagraph-44-19.052559.svg
AUTHAGRAPH_EARTH_SVG := $(GENERATED_SVG_DIR)/earth-authagraph-44-19.052559.svg
AUTHAGRAPH_WATER_SVG := $(GENERATED_SVG_DIR)/water-authagraph-44-19.052559.svg

DYMAXION_GEOMETRY_SVG := $(GENERATED_SVG_DIR)/geometry-dymaxion-44-20.78461.svg
DYMAXION_GRATICULE_SVG := $(GENERATED_SVG_DIR)/graticules-dymaxion-44-20.78461.svg
DYMAXION_EARTH_SVG := $(GENERATED_SVG_DIR)/earth-dymaxion-44-20.78461.svg
DYMAXION_WATER_SVG := $(GENERATED_SVG_DIR)/water-dymaxion-44-20.78461.svg

MYRIAHEDRAL_GEOMETRY_SVG := $(GENERATED_SVG_DIR)/geometry-myriahedral-44-24.75.svg
MYRIAHEDRAL_GRATICULE_SVG := $(GENERATED_SVG_DIR)/graticules-myriahedral-44-24.75.svg
MYRIAHEDRAL_EARTH_SVG := $(GENERATED_SVG_DIR)/earth-myriahedral-44-24.75.svg
MYRIAHEDRAL_WATER_SVG := $(GENERATED_SVG_DIR)/water-myriahedral-44-24.75.svg
MYRIAHEDRAL_PERSPECTIVE_WATER_SVGS := \
	$(GENERATED_SVG_DIR)/water-myriahedral-americas-44-24.75.svg \
	$(GENERATED_SVG_DIR)/water-myriahedral-atlantic-44-24.75.svg \
	$(GENERATED_SVG_DIR)/water-myriahedral-afro-eur-asia-44-24.75.svg \
	$(GENERATED_SVG_DIR)/water-myriahedral-pacific-44-24.75.svg \
	$(GENERATED_SVG_DIR)/water-myriahedral-antarctic-44-24.75.svg
MYRIAHEDRAL_SLICE_SVGS := \
	$(GENERATED_SVG_DIR)/water-myriahedral-adhoc-slice-1.svg \
	$(GENERATED_SVG_DIR)/water-myriahedral-adhoc-slice-2.svg

STAR_X_GEOMETRY_SVG := $(GENERATED_SVG_DIR)/geometry-star-x-34-44.svg
STAR_X_GRATICULE_SVG := $(GENERATED_SVG_DIR)/graticules-star-x-34-44.svg
STAR_X_EARTH_SVG := $(GENERATED_SVG_DIR)/earth-star-x-34-44.svg
STAR_X_WATER_SVG := $(GENERATED_SVG_DIR)/water-star-x-34-44.svg

VORONOI_GEOMETRY_SVG := $(GENERATED_SVG_DIR)/geometry-voronoi-44-22.916667.svg
VORONOI_GRATICULE_SVG := $(GENERATED_SVG_DIR)/graticules-voronoi-44-22.916667.svg
VORONOI_EARTH_SVG := $(GENERATED_SVG_DIR)/earth-voronoi-44-22.916667.svg
VORONOI_WATER_SVG := $(GENERATED_SVG_DIR)/water-voronoi-44-22.916667.svg

ASTRO_ALL_SKY_SVGS := \
	$(GENERATED_SVG_DIR)/astro-all-sky-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/astro-all-sky-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/astro-all-sky-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/astro-all-sky-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/astro-all-sky-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/astro-all-sky-voronoi-44-22.916667.svg
ASTRO_OBSERVER_SVGS := \
	$(GENERATED_SVG_DIR)/astro-observer-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/astro-observer-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/astro-observer-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/astro-observer-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/astro-observer-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/astro-observer-voronoi-44-22.916667.svg
ASTRO_SVGS := $(ASTRO_ALL_SKY_SVGS) $(ASTRO_OBSERVER_SVGS)

ORBITING_GLOBAL_SVGS := \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-voronoi-44-22.916667.svg
ORBITING_OBSERVER_SVGS := \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-voronoi-44-22.916667.svg
ORBITING_SVGS := $(ORBITING_GLOBAL_SVGS) $(ORBITING_OBSERVER_SVGS)
ORBITING_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(ORBITING_SVGS))
ORBITING_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(ORBITING_SVGS))

NETWORK_SVGS := \
	$(GENERATED_SVG_DIR)/network-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/network-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/network-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/network-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/network-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/network-voronoi-44-22.916667.svg
NETWORK_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(NETWORK_SVGS))
NETWORK_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(NETWORK_SVGS))

BATHYMETRY_ROULETTE_SVGS := \
	$(GENERATED_SVG_DIR)/bathymetry-roulette-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/bathymetry-roulette-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/bathymetry-roulette-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/bathymetry-roulette-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/bathymetry-roulette-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/bathymetry-roulette-voronoi-44-22.916667.svg
BATHYMETRY_ROULETTE_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(BATHYMETRY_ROULETTE_SVGS))
BATHYMETRY_ROULETTE_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(BATHYMETRY_ROULETTE_SVGS))

REQUESTED_GEOMETRY_SVGS := \
	$(AUTHAGRAPH_GEOMETRY_SVG) \
	$(DYMAXION_GEOMETRY_SVG) \
	$(MYRIAHEDRAL_GEOMETRY_SVG) \
	$(STAR_X_GEOMETRY_SVG) \
	$(VORONOI_GEOMETRY_SVG)
REQUESTED_GRATICULE_SVGS := \
	$(AUTHAGRAPH_GRATICULE_SVG) \
	$(DYMAXION_GRATICULE_SVG) \
	$(MYRIAHEDRAL_GRATICULE_SVG) \
	$(STAR_X_GRATICULE_SVG) \
	$(VORONOI_GRATICULE_SVG)
REQUESTED_EARTH_SVGS := \
	$(AUTHAGRAPH_EARTH_SVG) \
	$(DYMAXION_EARTH_SVG) \
	$(MYRIAHEDRAL_EARTH_SVG) \
	$(STAR_X_EARTH_SVG) \
	$(VORONOI_EARTH_SVG)
REQUESTED_WATER_SVGS := \
	$(AUTHAGRAPH_WATER_SVG) \
	$(DYMAXION_WATER_SVG) \
	$(MYRIAHEDRAL_WATER_SVG) \
	$(STAR_X_WATER_SVG) \
	$(VORONOI_WATER_SVG)
REQUESTED_PROJECTION_SVGS := \
	$(REQUESTED_GEOMETRY_SVGS) \
	$(REQUESTED_GRATICULE_SVGS) \
	$(REQUESTED_EARTH_SVGS) \
	$(REQUESTED_WATER_SVGS)
GENERATED_SVGS := \
	$(CK_GEOMETRY_SVG) $(CK_GRATICULE_SVG) \
	$(CK_EARTH_SVG) $(CK_WATER_SVG) $(CK_SLICE_SVGS) \
	$(REQUESTED_PROJECTION_SVGS) \
	$(MYRIAHEDRAL_PERSPECTIVE_WATER_SVGS) $(MYRIAHEDRAL_SLICE_SVGS) \
	$(ASTRO_SVGS) $(ORBITING_SVGS) $(NETWORK_SVGS) \
	$(BATHYMETRY_ROULETTE_SVGS)
GENERATED_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(GENERATED_SVGS))
GENERATED_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(GENERATED_SVGS))
STAR_X_SVGS := $(STAR_X_GEOMETRY_SVG) $(STAR_X_GRATICULE_SVG) \
	$(STAR_X_EARTH_SVG) $(STAR_X_WATER_SVG)
STAR_X_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(STAR_X_SVGS))
CK_SLICE_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(CK_SLICE_SVGS))
ASTRO_STAR_X_SVGS := \
	$(GENERATED_SVG_DIR)/astro-all-sky-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/astro-observer-star-x-34-44.svg
ASTRO_STAR_X_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(ASTRO_STAR_X_SVGS))
ORBITING_STAR_X_SVGS := \
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-star-x-34-44.svg
ORBITING_STAR_X_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(ORBITING_STAR_X_SVGS))
NETWORK_STAR_X_PNG := $(GENERATED_PNG_DIR)/network-star-x-34-44.png
BATHYMETRY_ROULETTE_STAR_X_PNG := \
	$(GENERATED_PNG_DIR)/bathymetry-roulette-star-x-34-44.png
MYRIAHEDRAL_PORTRAIT_SLICE_PNG := \
	$(GENERATED_PNG_DIR)/water-myriahedral-adhoc-slice-1.png
PORTRAIT_PNGS := $(STAR_X_PNGS) $(ASTRO_STAR_X_PNGS) \
	$(ORBITING_STAR_X_PNGS) $(NETWORK_STAR_X_PNG) $(CK_SLICE_PNGS) \
	$(BATHYMETRY_ROULETTE_STAR_X_PNG) \
	$(MYRIAHEDRAL_PORTRAIT_SLICE_PNG)
LANDSCAPE_PNGS := $(filter-out $(PORTRAIT_PNGS),$(GENERATED_PNGS))
GENERATED_ARTIFACTS := $(GENERATED_SVGS) $(GENERATED_PDFS) \
	$(GENERATED_PNGS)

GENERATOR_BINARIES := \
	$(ASTRO_GENERATOR) \
	$(BATHYMETRY_ROULETTE_GENERATOR) \
	$(GENERATION_PROFILE_RESOLVER) \
	$(NETWORK_GENERATOR) \
	$(ORBITING_GENERATOR) \
	$(EIGHT_SLICE_GENERATOR) \
	$(EARTH_GENERATOR) \
	$(FOUR_SLICE_GENERATOR) \
	$(GEOMETRY_GENERATOR) \
	$(GRATICULE_GENERATOR) \
	$(MYRIAHEDRAL_SLICE_GENERATOR) \
	$(WATER_GENERATOR)
TEST_BINARIES := \
	$(TEST_DIR)/test-astro-generation \
	$(TEST_DIR)/test-bathymetry-roulette-style \
	$(TEST_DIR)/test-generation-profile \
	$(TEST_DIR)/test-network-generation \
	$(TEST_DIR)/test-orbiting-generation \
	$(TEST_DIR)/test-cahill-keyes-projection \
	$(TEST_DIR)/test-cahill-keyes-projection-api \
	$(TEST_DIR)/test-cahill-keyes-path-functions \
	$(TEST_DIR)/test-cahill-keyes-slicing \
	$(TEST_DIR)/test-authagraph-projection-api \
	$(TEST_DIR)/test-dymaxion-projection-api \
	$(TEST_DIR)/test-myriahedral-projection-api \
	$(TEST_DIR)/test-myriahedral-slicing \
	$(TEST_DIR)/test-projection-generation-common \
	$(TEST_DIR)/test-star-x-projection-api \
	$(TEST_DIR)/test-voronoi-projection-api

GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/projection-generation-common.h \
	$(GENERATOR_SRC_DIR)/myriahedral-perspective-generation.h \
	$(wildcard $(GENERATOR_SRC_DIR)/myriahedral-perspective-*-tree.inc) \
	$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
	$(PROJECTION_SRC_DIR)/a60-carto-projection.h \
	$(PROJECTION_SRC_DIR)/a60-carto-projection-dymaxion.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-authagraph.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes-functions.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-tree.inc \
	$(PROJECTION_SRC_DIR)/cart0freak0-star-x.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-voronoi.h
AREA_GENERATOR_HEADER := $(GENERATOR_SRC_DIR)/projection-area-generation.h
NATURAL_EARTH_GENERATOR_HEADER := \
	$(GENERATOR_SRC_DIR)/natural-earth-generation.h
BATHYMETRY_ROULETTE_STYLE_HEADER := \
	$(GENERATOR_SRC_DIR)/bathymetry-roulette-style.h
ASTRO_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/astro-data.h \
	$(GENERATOR_SRC_DIR)/astro-generation.h \
	$(GENERATOR_HEADERS)
ORBITING_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/orbiting-data.h \
	$(GENERATOR_SRC_DIR)/orbiting-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS) $(SGP4_HEADER)
NETWORK_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/network-data.h \
	$(GENERATOR_SRC_DIR)/network-clustering.h \
	$(GENERATOR_SRC_DIR)/network-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)

.DEFAULT_GOAL := configured
.DELETE_ON_ERROR:

PUBLIC_TARGETS := all check check-prerequisite clean configured doxygen \
	generation-plan list-targets \
	fetch-natural-earth-10m fetch-astro-data fetch-orbiting-data \
	prepare-network-data make-generated \
	wasm-cahill-keyes check-wasm-cahill-keyes \
	wasm-cahill-myriahedral check-wasm-cahill-myriahedral \
	generate-geometry generate-graticules-ck generate-earth-ck \
	generate-water-ck generate-4-slice generate-8-slice \
	generate-ck-slices generate-projections generated-projections \
	generate-geometry-projections generate-graticules-projections \
	generate-earth-projections generate-water-projections \
	generate-astro generate-astro-projections generate-astro-all-sky \
	generate-astro-observer generate-astro-cahill-keyes \
	generate-astro-authagraph generate-astro-dymaxion \
	generate-astro-myriahedral generate-astro-star-x \
	generate-astro-voronoi \
	generate-orbiting generate-orbiting-projections \
	generate-orbiting-artifacts \
	generate-orbiting-global generate-orbiting-observer \
	generate-orbiting-cahill-keyes generate-orbiting-authagraph \
	generate-orbiting-dymaxion generate-orbiting-myriahedral \
	generate-orbiting-star-x generate-orbiting-voronoi \
	generate-network generate-network-projections generate-network-artifacts \
	generate-network-cahill-keyes generate-network-authagraph \
	generate-network-dymaxion generate-network-myriahedral \
	generate-network-star-x generate-network-voronoi \
	generate-bathymetry-roulette generate-bathymetry-roulette-projections \
	generate-bathymetry-roulette-artifacts \
	generate-bathymetry-roulette-cahill-keyes \
	generate-bathymetry-roulette-authagraph \
	generate-bathymetry-roulette-dymaxion \
	generate-bathymetry-roulette-myriahedral \
	generate-bathymetry-roulette-star-x \
	generate-bathymetry-roulette-voronoi \
	generate-water-myriahedral-perspectives generate-myriahedral-slices \
	generate-authagraph generate-dymaxion generate-myriahedral generate-star-x \
	generate-voronoi generate-voroni \
	generate-geometry-cahill-keyes generate-graticules-cahill-keyes \
	generate-earth-cahill-keyes generate-water-cahill-keyes \
	generate-geometry-authagraph generate-graticules-authagraph \
	generate-earth-authagraph generate-water-authagraph \
	generate-geometry-dymaxion generate-graticules-dymaxion \
	generate-earth-dymaxion generate-water-dymaxion \
	generate-geometry-myriahedral generate-graticules-myriahedral \
	generate-earth-myriahedral generate-water-myriahedral \
	generate-geometry-star-x generate-graticules-star-x \
	generate-earth-star-x generate-water-star-x \
	generate-geometry-voronoi generate-graticules-voronoi \
	generate-earth-voronoi generate-water-voronoi

.PHONY: $(PUBLIC_TARGETS)

list-targets:
	@printf '%s\n' $(sort $(PUBLIC_TARGETS))

generation-plan: $(GENERATION_PROFILE_RESOLVER) $(GENERATION_PROFILE)
	@"$(GENERATION_PROFILE_RESOLVER)" --describe "$(GENERATION_PROFILE)"

configured: $(GENERATION_PROFILE_RESOLVER) $(GENERATION_PROFILE)
	@targets="$$($(GENERATION_PROFILE_RESOLVER) \
		"$(GENERATION_PROFILE)")" && \
		printf 'generation profile: %s\n' "$(GENERATION_PROFILE)" && \
		$(MAKE) --no-print-directory $$targets

check-prerequisite: $(PREREQUISITE_CHECKER)
	@MAKE_VERSION="$(MAKE_VERSION)" CXX="$(CXX)" \
		CPPFLAGS="$(CPPFLAGS)" CXXFLAGS="$(CXXFLAGS)" \
		ALPHA60_SRC="$(ALPHA60_SRC)" IZZI_SRC="$(IZZI_SRC)" \
		GDAL_CONFIG="$(GDAL_CONFIG)" INKSCAPE="$(INKSCAPE)" \
		DOXYGEN="$(DOXYGEN)" EMXX="$(EMXX)" EMRUN="$(EMRUN)" \
		NODE="$(NODE)" WEB_BROWSER="$(WEB_BROWSER)" \
		"$(PREREQUISITE_CHECKER)"

check: $(SGP4_OBJECT) $(NETWORK_GEOJSON)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-astro-generation.cc \
		-o $(TEST_DIR)/test-astro-generation
	$(TEST_DIR)/test-astro-generation
	$(CXX) $(CPPFLAGS) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-bathymetry-roulette-style.cc \
		-o $(TEST_DIR)/test-bathymetry-roulette-style
	$(TEST_DIR)/test-bathymetry-roulette-style
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-generation-profile.cc \
		-o $(TEST_DIR)/test-generation-profile
	$(TEST_DIR)/test-generation-profile
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-network-generation.cc \
		-lh3 \
		-o $(TEST_DIR)/test-network-generation
	$(TEST_DIR)/test-network-generation
	cd "$(NETWORK_DATA_DIR)" && sha256sum -c SHA256SUMS
	printf '%s  %s\n' \
		'9fbd453d174df834208718e110396c5a22bff4312aeeff3e42d0175510b0ff69' \
		'$(abspath $(NETWORK_GEOJSON))' | sha256sum -c -
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-orbiting-generation.cc $(SGP4_OBJECT) \
		-o $(TEST_DIR)/test-orbiting-generation
	$(TEST_DIR)/test-orbiting-generation
	sha256sum -c $(ORBITING_DATA_DIR)/SHA256SUMS
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-cahill-keyes-projection.cc \
		-o $(TEST_DIR)/test-cahill-keyes-projection
	$(TEST_DIR)/test-cahill-keyes-projection
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-cahill-keyes-projection-api.cc \
		-o $(TEST_DIR)/test-cahill-keyes-projection-api
	$(TEST_DIR)/test-cahill-keyes-projection-api
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-cahill-keyes-path-functions.cc \
		-o $(TEST_DIR)/test-cahill-keyes-path-functions
	$(TEST_DIR)/test-cahill-keyes-path-functions
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-cahill-keyes-slicing.cc \
		-o $(TEST_DIR)/test-cahill-keyes-slicing
	$(TEST_DIR)/test-cahill-keyes-slicing
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-authagraph-projection-api.cc \
		-o $(TEST_DIR)/test-authagraph-projection-api
	$(TEST_DIR)/test-authagraph-projection-api
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-dymaxion-projection-api.cc \
		-o $(TEST_DIR)/test-dymaxion-projection-api
	$(TEST_DIR)/test-dymaxion-projection-api
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-myriahedral-projection-api.cc \
		-o $(TEST_DIR)/test-myriahedral-projection-api
	$(TEST_DIR)/test-myriahedral-projection-api
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-myriahedral-slicing.cc \
		-o $(TEST_DIR)/test-myriahedral-slicing
	$(TEST_DIR)/test-myriahedral-slicing
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-projection-generation-common.cc \
		-o $(TEST_DIR)/test-projection-generation-common
	$(TEST_DIR)/test-projection-generation-common
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-star-x-projection-api.cc \
		-o $(TEST_DIR)/test-star-x-projection-api
	$(TEST_DIR)/test-star-x-projection-api
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-voronoi-projection-api.cc \
		-o $(TEST_DIR)/test-voronoi-projection-api
	$(TEST_DIR)/test-voronoi-projection-api

doxygen: $(DOXYGEN_CONFIG) $(DOXYGEN_HEADERS)
	$(DOXYGEN) $(DOXYGEN_CONFIG)

wasm-cahill-keyes: $(CK_WEB_MODULE) $(CK_WEB_WASM) \
	$(CK_WEB_LAND) $(CK_WEB_SMOKE)

$(CK_WEB_MODULE) $(CK_WEB_WASM) &: \
		$(CK_WEB_SOURCE) $(CK_WEB_LAND) $(CK_WEB_SMOKE) \
		$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
		$(PROJECTION_SRC_DIR)/a60-carto-projection.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes.h
	mkdir -p "$(WEB_BUILD_DIR)"
	EM_CACHE="$(EM_CACHE)" "$(EMXX)" "$(CK_WEB_SOURCE)" \
		-I "$(PROJECTION_SRC_DIR)" \
		-isystem "$(ALPHA60_SRC)" -isystem "$(IZZI_SRC)" \
		-std=c++20 -O3 -Wall -Wextra -Wpedantic -Werror \
		--bind --no-entry -fexceptions -sDISABLE_EXCEPTION_CATCHING=0 \
		-sMODULARIZE=1 -sEXPORT_ES6=1 \
		-sEXPORT_NAME=createCartofreakoCahillKeyesModule \
		-sENVIRONMENT=web,node -sALLOW_MEMORY_GROWTH=1 -sFILESYSTEM=0 \
		-o "$(CK_WEB_MODULE)"

check-wasm-cahill-keyes: wasm-cahill-keyes
	cd "$(WEB_BUILD_DIR)" && "$(NODE)" cahill-keyes-smoke.mjs

wasm-cahill-myriahedral: $(MYRIA_WEB_MODULE) $(MYRIA_WEB_WASM) \
	$(MYRIA_WEB_LAND) $(MYRIA_WEB_SMOKE)

$(MYRIA_WEB_MODULE) $(MYRIA_WEB_WASM) &: \
		$(MYRIA_WEB_SOURCE) $(MYRIA_WEB_LAND) $(MYRIA_WEB_SMOKE) \
		$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
		$(PROJECTION_SRC_DIR)/a60-carto-projection.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-tree.inc
	mkdir -p "$(WEB_BUILD_DIR)"
	EM_CACHE="$(EM_CACHE)" "$(EMXX)" "$(MYRIA_WEB_SOURCE)" \
		-I "$(PROJECTION_SRC_DIR)" \
		-isystem "$(ALPHA60_SRC)" -isystem "$(IZZI_SRC)" \
		-std=c++20 -O3 -Wall -Wextra -Wpedantic -Werror \
		--bind --no-entry -fexceptions -sDISABLE_EXCEPTION_CATCHING=0 \
		-sMODULARIZE=1 -sEXPORT_ES6=1 \
		-sEXPORT_NAME=createCartofreakoCahillMyriahedralModule \
		-sENVIRONMENT=web,node -sALLOW_MEMORY_GROWTH=1 -sFILESYSTEM=0 \
		-o "$(MYRIA_WEB_MODULE)"

check-wasm-cahill-myriahedral: wasm-cahill-myriahedral
	cd "$(WEB_BUILD_DIR)" && "$(NODE)" cahill-myriahedral-smoke.mjs

$(GEOMETRY_GENERATOR): $(GENERATOR_SRC_DIR)/generate-geometry.cc \
		$(GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(GRATICULE_GENERATOR): $(GENERATOR_SRC_DIR)/generate-graticules.cc \
		$(GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(EARTH_GENERATOR): $(GENERATOR_SRC_DIR)/generate-earth.cc \
		$(NATURAL_EARTH_GENERATOR_HEADER) $(GENERATOR_HEADERS) \
		$(AREA_GENERATOR_HEADER)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

$(WATER_GENERATOR): $(GENERATOR_SRC_DIR)/generate-water.cc \
		$(NATURAL_EARTH_GENERATOR_HEADER) $(GENERATOR_HEADERS) \
		$(AREA_GENERATOR_HEADER)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

$(BATHYMETRY_ROULETTE_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-bathymetry-roulette.cc \
		$(BATHYMETRY_ROULETTE_STYLE_HEADER) \
		$(NATURAL_EARTH_GENERATOR_HEADER) $(GENERATOR_HEADERS) \
		$(AREA_GENERATOR_HEADER)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

$(FOUR_SLICE_GENERATOR): $(GENERATOR_SRC_DIR)/generate-4-slice.cc \
		$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes-slicing.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes.h \
		$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
		$(PROJECTION_SRC_DIR)/a60-carto-projection.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(EIGHT_SLICE_GENERATOR): $(GENERATOR_SRC_DIR)/generate-8-slice.cc \
		$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes-slicing.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes.h \
		$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
		$(PROJECTION_SRC_DIR)/a60-carto-projection.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(MYRIAHEDRAL_SLICE_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-myriahedral-slices.cc \
		$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-slicing.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral.h \
		$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-tree.inc \
		$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
		$(PROJECTION_SRC_DIR)/a60-carto-projection.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(ASTRO_GENERATOR): $(GENERATOR_SRC_DIR)/generate-astro.cc \
		$(ASTRO_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(GENERATION_PROFILE_RESOLVER): \
		$(GENERATOR_SRC_DIR)/resolve-generation-profile.cc \
		$(GENERATOR_SRC_DIR)/generation-profile.h
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< -o $@

$(SGP4_OBJECT): $(SGP4_SOURCE) $(SGP4_HEADER)
	$(CXX) -std=c++20 -w -c $(SGP4_SOURCE) -o $@

$(ORBITING_GENERATOR): $(GENERATOR_SRC_DIR)/generate-orbiting.cc \
		$(ORBITING_GENERATOR_HEADERS) $(SGP4_OBJECT)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(SGP4_OBJECT) $(shell $(GDAL_CONFIG) --libs) -o $@

$(NETWORK_GENERATOR): $(GENERATOR_SRC_DIR)/generate-network.cc \
		$(NETWORK_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

fetch-astro-data: $(ASTRO_FETCHER)
	$(ASTRO_FETCHER) "$(ASTRO_DATA_DIR)"

fetch-orbiting-data: $(ORBITING_FETCHER) $(ORBITING_PROFILE)
	$(ORBITING_FETCHER) "$(ORBITING_DATA_DIR)"

fetch-natural-earth-10m: $(NATURAL_EARTH_STAMP)

prepare-network-data: $(NETWORK_GEOJSON)

$(NETWORK_PREPARED_DIR):
	mkdir -p "$@"

$(NETWORK_GEOJSON): $(NETWORK_SOURCE) $(NETWORK_PREPARER) \
		| $(NETWORK_PREPARED_DIR)
	"$(NETWORK_PREPARER)" "$(NETWORK_SOURCE)" "$@"

$(NATURAL_EARTH_STAMP): $(NATURAL_EARTH_FETCHER)
	$(NATURAL_EARTH_FETCHER) "$(NATURAL_EARTH_DIR)"

$(GENERATED_DIR) $(GENERATED_SVG_DIR) $(GENERATED_PNG_DIR) \
		$(GENERATED_PDF_DIR):
	mkdir -p "$@"

# Preserve the original Cahill-Keyes workflow and output names.
generate-geometry: $(CK_GEOMETRY_SVG)
generate-geometry-cahill-keyes: $(CK_GEOMETRY_SVG)

$(CK_GEOMETRY_SVG): $(GEOMETRY_GENERATOR) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(GEOMETRY_GENERATOR))" cahill-keyes

generate-graticules-ck: $(CK_GRATICULE_SVG)
generate-graticules-cahill-keyes: $(CK_GRATICULE_SVG)

$(CK_GRATICULE_SVG): $(GRATICULE_GENERATOR) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(GRATICULE_GENERATOR))" cahill-keyes

generate-earth-ck: $(CK_EARTH_SVG) $(CK_SLICE_SVGS)
generate-earth-cahill-keyes: $(CK_EARTH_SVG)

$(CK_EARTH_SVG): $(EARTH_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(EARTH_GENERATOR))" cahill-keyes

generate-4-slice: $(CK_FOUR_SLICE_SVGS)

$(CK_FOUR_SLICE_SVGS) &: $(FOUR_SLICE_GENERATOR) $(CK_EARTH_SVG) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(FOUR_SLICE_GENERATOR))"

generate-8-slice: $(CK_EIGHT_SLICE_SVGS)

$(CK_EIGHT_SLICE_SVGS) &: $(EIGHT_SLICE_GENERATOR) $(CK_EARTH_SVG) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(EIGHT_SLICE_GENERATOR))"

generate-ck-slices: generate-4-slice generate-8-slice

generate-water-ck: $(CK_WATER_SVG)
generate-water-cahill-keyes: $(CK_WATER_SVG)

$(CK_WATER_SVG): $(WATER_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(WATER_GENERATOR))" cahill-keyes

generate-water-myriahedral-perspectives: \
	$(MYRIAHEDRAL_PERSPECTIVE_WATER_SVGS)

$(MYRIAHEDRAL_PERSPECTIVE_WATER_SVGS): \
		$(GENERATED_SVG_DIR)/water-myriahedral-%-44-24.75.svg: \
		$(WATER_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(WATER_GENERATOR))" myriahedral-$*

generate-myriahedral-slices: $(MYRIAHEDRAL_SLICE_SVGS)

$(MYRIAHEDRAL_SLICE_SVGS) &: $(MYRIAHEDRAL_SLICE_GENERATOR) \
		$(MYRIAHEDRAL_WATER_SVG) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(MYRIAHEDRAL_SLICE_GENERATOR))"

# $(1): command-line projection name; $(2)-$(5): generated artifacts.
define PROJECTION_RULES
generate-geometry-$(1): $(2)
$(2): $(GEOMETRY_GENERATOR) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(GEOMETRY_GENERATOR))" $(1)

generate-graticules-$(1): $(3)
$(3): $(GRATICULE_GENERATOR) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(GRATICULE_GENERATOR))" $(1)

generate-earth-$(1): $(4)
$(4): $(EARTH_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(EARTH_GENERATOR))" $(1)

generate-water-$(1): $(5)
$(5): $(WATER_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(WATER_GENERATOR))" $(1)

generate-$(1): $(2) $(3) $(4) $(5)
endef

$(eval $(call PROJECTION_RULES,authagraph,\
	$(AUTHAGRAPH_GEOMETRY_SVG),$(AUTHAGRAPH_GRATICULE_SVG),\
	$(AUTHAGRAPH_EARTH_SVG),$(AUTHAGRAPH_WATER_SVG)))
$(eval $(call PROJECTION_RULES,dymaxion,\
	$(DYMAXION_GEOMETRY_SVG),$(DYMAXION_GRATICULE_SVG),\
	$(DYMAXION_EARTH_SVG),$(DYMAXION_WATER_SVG)))
$(eval $(call PROJECTION_RULES,myriahedral,\
	$(MYRIAHEDRAL_GEOMETRY_SVG),$(MYRIAHEDRAL_GRATICULE_SVG),\
	$(MYRIAHEDRAL_EARTH_SVG),$(MYRIAHEDRAL_WATER_SVG)))
$(eval $(call PROJECTION_RULES,star-x,\
	$(STAR_X_GEOMETRY_SVG),$(STAR_X_GRATICULE_SVG),\
	$(STAR_X_EARTH_SVG),$(STAR_X_WATER_SVG)))
$(eval $(call PROJECTION_RULES,voronoi,\
	$(VORONOI_GEOMETRY_SVG),$(VORONOI_GRATICULE_SVG),\
	$(VORONOI_EARTH_SVG),$(VORONOI_WATER_SVG)))

# $(1): command-line projection name; $(2)-$(3): astronomy products.
define ASTRO_PROJECTION_RULES
generate-astro-$(1): $(2) $(3)
$(2): $(ASTRO_GENERATOR) $(ASTRO_PROFILE) $(ASTRO_CATALOGS) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(ASTRO_GENERATOR))" $(1) all-sky \
		"$(abspath $(ASTRO_PROFILE))"

$(3): $(ASTRO_GENERATOR) $(ASTRO_PROFILE) $(ASTRO_CATALOGS) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(ASTRO_GENERATOR))" $(1) observer \
		"$(abspath $(ASTRO_PROFILE))"
endef

$(eval $(call ASTRO_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/astro-all-sky-ck-44-22.svg,\
	$(GENERATED_SVG_DIR)/astro-observer-ck-44-22.svg))
$(eval $(call ASTRO_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/astro-all-sky-authagraph-44-19.052559.svg,\
	$(GENERATED_SVG_DIR)/astro-observer-authagraph-44-19.052559.svg))
$(eval $(call ASTRO_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/astro-all-sky-dymaxion-44-20.78461.svg,\
	$(GENERATED_SVG_DIR)/astro-observer-dymaxion-44-20.78461.svg))
$(eval $(call ASTRO_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/astro-all-sky-myriahedral-44-24.75.svg,\
	$(GENERATED_SVG_DIR)/astro-observer-myriahedral-44-24.75.svg))
$(eval $(call ASTRO_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/astro-all-sky-star-x-34-44.svg,\
	$(GENERATED_SVG_DIR)/astro-observer-star-x-34-44.svg))
$(eval $(call ASTRO_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/astro-all-sky-voronoi-44-22.916667.svg,\
	$(GENERATED_SVG_DIR)/astro-observer-voronoi-44-22.916667.svg))

generate-astro-all-sky: $(ASTRO_ALL_SKY_SVGS)
generate-astro-observer: $(ASTRO_OBSERVER_SVGS)
generate-astro: $(ASTRO_SVGS)
generate-astro-projections: $(ASTRO_SVGS)

# $(1): command-line projection name; $(2)-$(3): Orbital Technosphere products.
define ORBITING_PROJECTION_RULES
generate-orbiting-$(1): $(2) $(3)
$(2): $(ORBITING_GENERATOR) $(ORBITING_PROFILE) $(ORBITING_CATALOGS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(ORBITING_GENERATOR))" $(1) global \
		"$(abspath $(ORBITING_PROFILE))"

$(3): $(ORBITING_GENERATOR) $(ORBITING_PROFILE) $(ORBITING_CATALOGS) \
		| $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		"$(abspath $(ORBITING_GENERATOR))" $(1) observer \
		"$(abspath $(ORBITING_PROFILE))"
endef

$(eval $(call ORBITING_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-ck-44-22.svg,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-ck-44-22.svg))
$(eval $(call ORBITING_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-authagraph-44-19.052559.svg,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-authagraph-44-19.052559.svg))
$(eval $(call ORBITING_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-dymaxion-44-20.78461.svg,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-dymaxion-44-20.78461.svg))
$(eval $(call ORBITING_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-myriahedral-44-24.75.svg,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-myriahedral-44-24.75.svg))
$(eval $(call ORBITING_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-star-x-34-44.svg,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-star-x-34-44.svg))
$(eval $(call ORBITING_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-global-voronoi-44-22.916667.svg,\
	$(GENERATED_SVG_DIR)/orbital-technosphere-observer-voronoi-44-22.916667.svg))

generate-orbiting-global: $(ORBITING_GLOBAL_SVGS)
generate-orbiting-observer: $(ORBITING_OBSERVER_SVGS)
generate-orbiting: $(ORBITING_SVGS)
generate-orbiting-projections: $(ORBITING_SVGS)
generate-orbiting-artifacts: $(ORBITING_SVGS) $(ORBITING_PDFS) \
	$(ORBITING_PNGS)

# $(1): command-line projection name; $(2): Network product.
define NETWORK_PROJECTION_RULES
generate-network-$(1): $(2)
$(2): $(NETWORK_GENERATOR) $(NETWORK_PROFILE) $(NETWORK_GEOJSON) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(NETWORK_GENERATOR))" $(1) \
		"$(abspath $(NETWORK_PROFILE))" "$(abspath $(NETWORK_GEOJSON))"
endef

$(eval $(call NETWORK_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/network-ck-44-22.svg))
$(eval $(call NETWORK_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/network-authagraph-44-19.052559.svg))
$(eval $(call NETWORK_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/network-dymaxion-44-20.78461.svg))
$(eval $(call NETWORK_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/network-myriahedral-44-24.75.svg))
$(eval $(call NETWORK_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/network-star-x-34-44.svg))
$(eval $(call NETWORK_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/network-voronoi-44-22.916667.svg))

generate-network: $(NETWORK_SVGS)
generate-network-projections: $(NETWORK_SVGS)
generate-network-artifacts: $(NETWORK_SVGS) $(NETWORK_PDFS) $(NETWORK_PNGS)

# $(1): command-line projection name; $(2): Bathymetry Roulette product.
define BATHYMETRY_ROULETTE_PROJECTION_RULES
generate-bathymetry-roulette-$(1): $(2)
$(2): $(BATHYMETRY_ROULETTE_GENERATOR) $(NATURAL_EARTH_STAMP) \
		| $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(BATHYMETRY_ROULETTE_GENERATOR))" $(1)
endef

$(eval $(call BATHYMETRY_ROULETTE_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/bathymetry-roulette-ck-44-22.svg))
$(eval $(call BATHYMETRY_ROULETTE_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/bathymetry-roulette-authagraph-44-19.052559.svg))
$(eval $(call BATHYMETRY_ROULETTE_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/bathymetry-roulette-dymaxion-44-20.78461.svg))
$(eval $(call BATHYMETRY_ROULETTE_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/bathymetry-roulette-myriahedral-44-24.75.svg))
$(eval $(call BATHYMETRY_ROULETTE_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/bathymetry-roulette-star-x-34-44.svg))
$(eval $(call BATHYMETRY_ROULETTE_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/bathymetry-roulette-voronoi-44-22.916667.svg))

generate-bathymetry-roulette: $(BATHYMETRY_ROULETTE_SVGS)
generate-bathymetry-roulette-projections: $(BATHYMETRY_ROULETTE_SVGS)
generate-bathymetry-roulette-artifacts: $(BATHYMETRY_ROULETTE_SVGS) \
	$(BATHYMETRY_ROULETTE_PDFS) $(BATHYMETRY_ROULETTE_PNGS)

generate-water-myriahedral: generate-water-myriahedral-perspectives \
	generate-myriahedral-slices
generate-myriahedral: generate-water-myriahedral-perspectives \
	generate-myriahedral-slices

$(GENERATED_PDFS): $(GENERATED_PDF_DIR)/%.pdf: \
		$(GENERATED_SVG_DIR)/%.svg | $(GENERATED_PDF_DIR)
	"$(INKSCAPE)" --export-area-page --export-filename="$@" "$<"

$(LANDSCAPE_PNGS): $(GENERATED_PNG_DIR)/%.png: \
		$(GENERATED_SVG_DIR)/%.svg Makefile | $(GENERATED_PNG_DIR)
	"$(INKSCAPE)" --export-area-page $(PNG_EXPORT_BACKGROUND) \
		--export-width=$(PNG_LONG_SIDE) \
		--export-filename="$@" "$<"

$(PORTRAIT_PNGS): $(GENERATED_PNG_DIR)/%.png: \
		$(GENERATED_SVG_DIR)/%.svg Makefile | $(GENERATED_PNG_DIR)
	"$(INKSCAPE)" --export-area-page $(PNG_EXPORT_BACKGROUND) \
		--export-height=$(PNG_LONG_SIDE) \
		--export-filename="$@" "$<"

generate-voroni: generate-voronoi

generate-geometry-projections: \
	$(CK_GEOMETRY_SVG) $(REQUESTED_GEOMETRY_SVGS)
generate-graticules-projections: \
	$(CK_GRATICULE_SVG) $(REQUESTED_GRATICULE_SVGS)
generate-earth-projections: \
	$(CK_EARTH_SVG) $(CK_SLICE_SVGS) $(REQUESTED_EARTH_SVGS)
generate-water-projections: $(CK_WATER_SVG) $(REQUESTED_WATER_SVGS) \
	$(MYRIAHEDRAL_PERSPECTIVE_WATER_SVGS) $(MYRIAHEDRAL_SLICE_SVGS)
generate-projections: $(GENERATED_ARTIFACTS)
generated-projections: $(GENERATED_ARTIFACTS)
make-generated: $(GENERATED_ARTIFACTS)
all: $(GENERATED_ARTIFACTS)

clean:
	$(RM) $(TEST_BINARIES) $(GENERATOR_BINARIES)
	$(RM) $(SGP4_OBJECT)
	$(RM) $(GENERATED_SVGS) $(CK_WEB_MODULE) $(CK_WEB_WASM) \
		$(MYRIA_WEB_MODULE) $(MYRIA_WEB_WASM)
	$(RM) -r "$(GENERATED_DIR)/svg" "$(GENERATED_DIR)/png" \
		"$(GENERATED_DIR)/pdf"
	$(RM) -r "$(DOXYGEN_OUTPUT_DIR)"

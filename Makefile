CXX ?= g++
CPPFLAGS ?= -Isrc
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Wpedantic -Werror
TEST_DIR := tests
ALPHA60_SRC ?= ../alpha60/src
IZZI_SRC ?= ../izzi/src
GDAL_CONFIG ?= gdal-config
DOXYGEN ?= doxygen
EMXX ?= ../emsdk/upstream/emscripten/em++
NODE ?= node
EM_CACHE ?= /tmp/cartofreako-emscripten-cache
NATURAL_EARTH_DIR ?= assets/natural-earth/10m-physical-vectors
NATURAL_EARTH_FETCHER := scripts/fetch-natural-earth-10m.sh
NATURAL_EARTH_STAMP := \
	$(NATURAL_EARTH_DIR)/.natural-earth-10m-physical-5.1.1
GENERATED_DIR := generated
DOXYGEN_CONFIG := Doxyfile
DOXYGEN_OUTPUT_DIR := docs/doxygen
DOXYGEN_HEADERS := $(wildcard src/cart0freak0*.h)
WEB_DIR := web
WEB_BUILD_DIR := build/web
CK_WEB_SOURCE := $(WEB_DIR)/cahill-keyes-web.cc
CK_WEB_LAND := $(WEB_DIR)/cartofreako-cahill-keyes-land-110m.geojson
CK_WEB_SMOKE := $(WEB_DIR)/cahill-keyes-smoke.mjs
CK_WEB_MODULE := $(WEB_BUILD_DIR)/cartofreako-cahill-keyes.mjs
CK_WEB_WASM := $(WEB_BUILD_DIR)/cartofreako-cahill-keyes.wasm
CK_WEB_BUILD_LAND := \
	$(WEB_BUILD_DIR)/cartofreako-cahill-keyes-land-110m.geojson
CK_WEB_BUILD_SMOKE := $(WEB_BUILD_DIR)/cahill-keyes-smoke.mjs

GEOMETRY_GENERATOR := $(TEST_DIR)/generate-geometry
GRATICULE_GENERATOR := $(TEST_DIR)/generate-graticules
EARTH_GENERATOR := $(TEST_DIR)/generate-earth
OCEAN_GENERATOR := $(TEST_DIR)/generate-ocean

CK_GEOMETRY_SVG := $(GENERATED_DIR)/geometry-ck-44-22.svg
CK_GRATICULE_SVG := $(GENERATED_DIR)/graticules-ck-44-22.svg
CK_EARTH_SVG := $(GENERATED_DIR)/earth-ck-44-22.svg
CK_OCEAN_SVG := $(GENERATED_DIR)/ocean-ck-44-22.svg

AUTHAGRAPH_GEOMETRY_SVG := $(GENERATED_DIR)/geometry-authagraph-44-19.052559.svg
AUTHAGRAPH_GRATICULE_SVG := $(GENERATED_DIR)/graticules-authagraph-44-19.052559.svg
AUTHAGRAPH_EARTH_SVG := $(GENERATED_DIR)/earth-authagraph-44-19.052559.svg
AUTHAGRAPH_OCEAN_SVG := $(GENERATED_DIR)/ocean-authagraph-44-19.052559.svg

MYRIAHEDRAL_GEOMETRY_SVG := $(GENERATED_DIR)/geometry-myriahedral-44-24.75.svg
MYRIAHEDRAL_GRATICULE_SVG := $(GENERATED_DIR)/graticules-myriahedral-44-24.75.svg
MYRIAHEDRAL_EARTH_SVG := $(GENERATED_DIR)/earth-myriahedral-44-24.75.svg
MYRIAHEDRAL_OCEAN_SVG := $(GENERATED_DIR)/ocean-myriahedral-44-24.75.svg

STAR_X_GEOMETRY_SVG := $(GENERATED_DIR)/geometry-star-x-34-44.svg
STAR_X_GRATICULE_SVG := $(GENERATED_DIR)/graticules-star-x-34-44.svg
STAR_X_EARTH_SVG := $(GENERATED_DIR)/earth-star-x-34-44.svg
STAR_X_OCEAN_SVG := $(GENERATED_DIR)/ocean-star-x-34-44.svg

VORONOI_GEOMETRY_SVG := $(GENERATED_DIR)/geometry-voronoi-44-22.916667.svg
VORONOI_GRATICULE_SVG := $(GENERATED_DIR)/graticules-voronoi-44-22.916667.svg
VORONOI_EARTH_SVG := $(GENERATED_DIR)/earth-voronoi-44-22.916667.svg
VORONOI_OCEAN_SVG := $(GENERATED_DIR)/ocean-voronoi-44-22.916667.svg

REQUESTED_GEOMETRY_SVGS := \
	$(AUTHAGRAPH_GEOMETRY_SVG) \
	$(MYRIAHEDRAL_GEOMETRY_SVG) \
	$(STAR_X_GEOMETRY_SVG) \
	$(VORONOI_GEOMETRY_SVG)
REQUESTED_GRATICULE_SVGS := \
	$(AUTHAGRAPH_GRATICULE_SVG) \
	$(MYRIAHEDRAL_GRATICULE_SVG) \
	$(STAR_X_GRATICULE_SVG) \
	$(VORONOI_GRATICULE_SVG)
REQUESTED_EARTH_SVGS := \
	$(AUTHAGRAPH_EARTH_SVG) \
	$(MYRIAHEDRAL_EARTH_SVG) \
	$(STAR_X_EARTH_SVG) \
	$(VORONOI_EARTH_SVG)
REQUESTED_OCEAN_SVGS := \
	$(AUTHAGRAPH_OCEAN_SVG) \
	$(MYRIAHEDRAL_OCEAN_SVG) \
	$(STAR_X_OCEAN_SVG) \
	$(VORONOI_OCEAN_SVG)
REQUESTED_PROJECTION_SVGS := \
	$(REQUESTED_GEOMETRY_SVGS) \
	$(REQUESTED_GRATICULE_SVGS) \
	$(REQUESTED_EARTH_SVGS) \
	$(REQUESTED_OCEAN_SVGS)
GENERATED_SVGS := \
	$(CK_GEOMETRY_SVG) $(CK_GRATICULE_SVG) \
	$(CK_EARTH_SVG) $(CK_OCEAN_SVG) \
	$(REQUESTED_PROJECTION_SVGS)

GENERATOR_BINARIES := \
	$(EARTH_GENERATOR) \
	$(GEOMETRY_GENERATOR) \
	$(GRATICULE_GENERATOR) \
	$(OCEAN_GENERATOR)
TEST_BINARIES := \
	$(GENERATOR_BINARIES) \
	$(TEST_DIR)/test-cahill-keyes-projection \
	$(TEST_DIR)/test-cahill-keyes-projection-api \
	$(TEST_DIR)/test-cahill-keyes-path-functions \
	$(TEST_DIR)/test-authagraph-projection-api \
	$(TEST_DIR)/test-myriahedral-projection-api \
	$(TEST_DIR)/test-star-x-projection-api \
	$(TEST_DIR)/test-voronoi-projection-api

GENERATOR_HEADERS := \
	$(TEST_DIR)/projection-generation-common.h \
	src/a60-carto-frame.h src/a60-carto-projection.h \
	src/cart0freak0-authagraph.h \
	src/cart0freak0-cahill-keyes.h \
	src/cart0freak0-cahill-keyes-functions.h \
	src/cart0freak0-myriahedral.h \
	src/cart0freak0-star-x.h \
	src/cart0freak0-voronoi.h
AREA_GENERATOR_HEADER := $(TEST_DIR)/projection-area-generation.h
HAMONSHU_CURVE_HEADERS := \
	$(IZZI_SRC)/a60-svg-curves-hamonshu.h \
	$(IZZI_SRC)/a60-svg-curves-hamonshu-v2.inc

.DELETE_ON_ERROR:

.PHONY: all check clean doxygen fetch-natural-earth-10m make-generated \
	wasm-cahill-keyes check-wasm-cahill-keyes \
	generate-geometry generate-graticules-ck generate-earth-ck \
	generate-ocean-ck generate-projections generated-projections \
	generate-geometry-projections generate-graticules-projections \
	generate-earth-projections generate-ocean-projections \
	generate-authagraph generate-myriahedral generate-star-x \
	generate-voronoi generate-voroni \
	generate-geometry-authagraph generate-graticules-authagraph \
	generate-earth-authagraph generate-ocean-authagraph \
	generate-geometry-myriahedral generate-graticules-myriahedral \
	generate-earth-myriahedral generate-ocean-myriahedral \
	generate-geometry-star-x generate-graticules-star-x \
	generate-earth-star-x generate-ocean-star-x \
	generate-geometry-voronoi generate-graticules-voronoi \
	generate-earth-voronoi generate-ocean-voronoi

check:
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
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-authagraph-projection-api.cc \
		-o $(TEST_DIR)/test-authagraph-projection-api
	$(TEST_DIR)/test-authagraph-projection-api
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-myriahedral-projection-api.cc \
		-o $(TEST_DIR)/test-myriahedral-projection-api
	$(TEST_DIR)/test-myriahedral-projection-api
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
	$(CK_WEB_BUILD_LAND) $(CK_WEB_BUILD_SMOKE)

$(CK_WEB_MODULE) $(CK_WEB_WASM) $(CK_WEB_BUILD_LAND) \
		$(CK_WEB_BUILD_SMOKE) &: \
		$(CK_WEB_SOURCE) $(CK_WEB_LAND) $(CK_WEB_SMOKE) \
		src/a60-carto-frame.h src/a60-carto-projection.h \
		src/cart0freak0-cahill-keyes.h
	mkdir -p "$(WEB_BUILD_DIR)"
	EM_CACHE="$(EM_CACHE)" "$(EMXX)" "$(CK_WEB_SOURCE)" \
		-I src -isystem "$(ALPHA60_SRC)" -isystem "$(IZZI_SRC)" \
		-std=c++20 -O3 -Wall -Wextra -Wpedantic -Werror \
		--bind --no-entry -fexceptions -sDISABLE_EXCEPTION_CATCHING=0 \
		-sMODULARIZE=1 -sEXPORT_ES6=1 \
		-sEXPORT_NAME=createCartofreakoCahillKeyesModule \
		-sENVIRONMENT=web,node -sALLOW_MEMORY_GROWTH=1 -sFILESYSTEM=0 \
		-o "$(CK_WEB_MODULE)"
	cp "$(CK_WEB_LAND)" "$(WEB_BUILD_DIR)/"
	cp "$(CK_WEB_SMOKE)" "$(WEB_BUILD_DIR)/"

check-wasm-cahill-keyes: wasm-cahill-keyes
	cd "$(WEB_BUILD_DIR)" && "$(NODE)" cahill-keyes-smoke.mjs

$(GEOMETRY_GENERATOR): $(TEST_DIR)/generate-geometry.cc $(GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(GRATICULE_GENERATOR): $(TEST_DIR)/generate-graticules.cc \
		$(GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(EARTH_GENERATOR): $(TEST_DIR)/generate-earth.cc $(GENERATOR_HEADERS) \
		$(AREA_GENERATOR_HEADER)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

$(OCEAN_GENERATOR): $(TEST_DIR)/generate-ocean.cc \
		$(HAMONSHU_CURVE_HEADERS) $(GENERATOR_HEADERS) \
		$(AREA_GENERATOR_HEADER)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

fetch-natural-earth-10m: $(NATURAL_EARTH_STAMP)

$(NATURAL_EARTH_STAMP): $(NATURAL_EARTH_FETCHER)
	$(NATURAL_EARTH_FETCHER) "$(NATURAL_EARTH_DIR)"

$(GENERATED_DIR):
	mkdir -p "$@"

# Preserve the original Cahill-Keyes workflow and output names.
generate-geometry: $(CK_GEOMETRY_SVG)

$(CK_GEOMETRY_SVG): $(GEOMETRY_GENERATOR) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		"$(abspath $(GEOMETRY_GENERATOR))" cahill-keyes

generate-graticules-ck: $(CK_GRATICULE_SVG)

$(CK_GRATICULE_SVG): $(GRATICULE_GENERATOR) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		"$(abspath $(GRATICULE_GENERATOR))" cahill-keyes

generate-earth-ck: $(CK_EARTH_SVG)

$(CK_EARTH_SVG): $(EARTH_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(EARTH_GENERATOR))" cahill-keyes

generate-ocean-ck: $(CK_OCEAN_SVG)

$(CK_OCEAN_SVG): $(OCEAN_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(OCEAN_GENERATOR))" cahill-keyes

# $(1): command-line projection name; $(2)-$(5): generated artifacts.
define PROJECTION_RULES
generate-geometry-$(1): $(2)
$(2): $(GEOMETRY_GENERATOR) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		"$(abspath $(GEOMETRY_GENERATOR))" $(1)

generate-graticules-$(1): $(3)
$(3): $(GRATICULE_GENERATOR) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		"$(abspath $(GRATICULE_GENERATOR))" $(1)

generate-earth-$(1): $(4)
$(4): $(EARTH_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(EARTH_GENERATOR))" $(1)

generate-ocean-$(1): $(5)
$(5): $(OCEAN_GENERATOR) $(NATURAL_EARTH_STAMP) | $(GENERATED_DIR)
	cd "$(GENERATED_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		"$(abspath $(OCEAN_GENERATOR))" $(1)

generate-$(1): $(2) $(3) $(4) $(5)
endef

$(eval $(call PROJECTION_RULES,authagraph,\
	$(AUTHAGRAPH_GEOMETRY_SVG),$(AUTHAGRAPH_GRATICULE_SVG),\
	$(AUTHAGRAPH_EARTH_SVG),$(AUTHAGRAPH_OCEAN_SVG)))
$(eval $(call PROJECTION_RULES,myriahedral,\
	$(MYRIAHEDRAL_GEOMETRY_SVG),$(MYRIAHEDRAL_GRATICULE_SVG),\
	$(MYRIAHEDRAL_EARTH_SVG),$(MYRIAHEDRAL_OCEAN_SVG)))
$(eval $(call PROJECTION_RULES,star-x,\
	$(STAR_X_GEOMETRY_SVG),$(STAR_X_GRATICULE_SVG),\
	$(STAR_X_EARTH_SVG),$(STAR_X_OCEAN_SVG)))
$(eval $(call PROJECTION_RULES,voronoi,\
	$(VORONOI_GEOMETRY_SVG),$(VORONOI_GRATICULE_SVG),\
	$(VORONOI_EARTH_SVG),$(VORONOI_OCEAN_SVG)))

generate-voroni: generate-voronoi

generate-geometry-projections: \
	$(CK_GEOMETRY_SVG) $(REQUESTED_GEOMETRY_SVGS)
generate-graticules-projections: \
	$(CK_GRATICULE_SVG) $(REQUESTED_GRATICULE_SVGS)
generate-earth-projections: $(CK_EARTH_SVG) $(REQUESTED_EARTH_SVGS)
generate-ocean-projections: $(CK_OCEAN_SVG) $(REQUESTED_OCEAN_SVGS)
generate-projections: $(GENERATED_SVGS)
generated-projections: $(GENERATED_SVGS)
make-generated: $(GENERATED_SVGS)
all: $(GENERATED_SVGS)

clean:
	$(RM) $(TEST_BINARIES)
	$(RM) -r "$(GENERATED_DIR)"
	$(RM) -r "$(DOXYGEN_OUTPUT_DIR)"
	$(RM) -r "$(WEB_BUILD_DIR)"

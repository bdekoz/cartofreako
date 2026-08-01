CXX ?= g++
CPPFLAGS ?= -Isrc
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Wpedantic -Werror
TEST_DIR := tests
ALPHA60_SRC ?= ../alpha60/src
IZZI_SRC ?= ../izzi/src
GDAL_CONFIG ?= gdal-config
NATURAL_EARTH_DIR ?= assets/natural-earth/10m-physical-vectors
NATURAL_EARTH_FETCHER := scripts/fetch-natural-earth-10m.sh
NATURAL_EARTH_STAMP := \
	$(NATURAL_EARTH_DIR)/.natural-earth-10m-physical-5.1.1
CK_GEOMETRY_GENERATOR := $(TEST_DIR)/generate-geometry
CK_GEOMETRY_SVG := geometry-ck-44-22.svg
CK_GRATICULE_GENERATOR := $(TEST_DIR)/generate-graticules-ck
CK_GRATICULE_SVG := graticules-ck-44-22.svg
CK_EARTH_GENERATOR := $(TEST_DIR)/generate-earth-ck
CK_EARTH_SVG := earth-ck-44-22.svg
CK_OCEAN_GENERATOR := $(TEST_DIR)/generate-ocean-ck
CK_OCEAN_SVG := ocean-ck-44-22.svg
TEST_BINARIES := \
	$(CK_EARTH_GENERATOR) \
	$(CK_GEOMETRY_GENERATOR) \
	$(CK_GRATICULE_GENERATOR) \
	$(CK_OCEAN_GENERATOR) \
	$(TEST_DIR)/test-cahill-keyes-projection \
	$(TEST_DIR)/test-cahill-keyes-projection-api \
	$(TEST_DIR)/test-cahill-keyes-path-functions \
	$(TEST_DIR)/test-authagraph-projection-api \
	$(TEST_DIR)/test-myriahedral-projection-api \
	$(TEST_DIR)/test-star-x-projection-api \
	$(TEST_DIR)/test-voronoi-projection-api

.PHONY: check clean fetch-natural-earth-10m generate-earth-ck \
	generate-geometry generate-graticules-ck generate-ocean-ck
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

generate-geometry: $(CK_GEOMETRY_SVG)

$(CK_GEOMETRY_SVG): $(CK_GEOMETRY_GENERATOR)
	./$(CK_GEOMETRY_GENERATOR)

$(CK_GEOMETRY_GENERATOR): $(TEST_DIR)/generate-geometry.cc \
		src/a60-carto-frame.h src/a60-carto-projection.h \
		src/cart0freak0-cahill-keyes.h \
		src/cart0freak0-cahill-keyes-functions.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

generate-graticules-ck: $(CK_GRATICULE_SVG)

$(CK_GRATICULE_SVG): $(CK_GRATICULE_GENERATOR)
	./$(CK_GRATICULE_GENERATOR)

$(CK_GRATICULE_GENERATOR): $(TEST_DIR)/generate-graticules-ck.cc \
		src/a60-carto-frame.h src/a60-carto-projection.h \
		src/cart0freak0-cahill-keyes.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

fetch-natural-earth-10m: $(NATURAL_EARTH_STAMP)

$(NATURAL_EARTH_STAMP): $(NATURAL_EARTH_FETCHER)
	$(NATURAL_EARTH_FETCHER) "$(NATURAL_EARTH_DIR)"

generate-earth-ck: $(CK_EARTH_SVG)

$(CK_EARTH_SVG): $(CK_EARTH_GENERATOR) $(NATURAL_EARTH_STAMP)
	NATURAL_EARTH_DIR="$(NATURAL_EARTH_DIR)" ./$(CK_EARTH_GENERATOR)

$(CK_EARTH_GENERATOR): $(TEST_DIR)/generate-earth-ck.cc \
		src/a60-carto-frame.h src/a60-carto-projection.h \
		src/cart0freak0-cahill-keyes.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

generate-ocean-ck: $(CK_OCEAN_SVG)

$(CK_OCEAN_SVG): $(CK_OCEAN_GENERATOR) $(NATURAL_EARTH_STAMP)
	NATURAL_EARTH_DIR="$(NATURAL_EARTH_DIR)" ./$(CK_OCEAN_GENERATOR)

$(CK_OCEAN_GENERATOR): $(TEST_DIR)/generate-ocean-ck.cc \
		$(TEST_DIR)/hamonshu-v2-patterns.inc \
		src/a60-carto-frame.h src/a60-carto-projection.h \
		src/cart0freak0-cahill-keyes.h \
		src/cart0freak0-cahill-keyes-functions.h
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

clean:
	$(RM) $(TEST_BINARIES) $(CK_EARTH_SVG) $(CK_GEOMETRY_SVG) \
		$(CK_GRATICULE_SVG) $(CK_OCEAN_SVG)

CXX ?= g++
CPPFLAGS ?= -Isrc
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Wpedantic -Werror
TEST_DIR := tests
ALPHA60_SRC ?= ../alpha60/src
IZZI_SRC ?= ../izzi/src
CK_GEOMETRY_GENERATOR := $(TEST_DIR)/generate-geometry
CK_GEOMETRY_SVG := geometry-ck-44-22.svg
CK_GRATICULE_GENERATOR := $(TEST_DIR)/generate-graticules-ck
CK_GRATICULE_SVG := graticules-ck-44-22.svg
TEST_BINARIES := \
	$(CK_GEOMETRY_GENERATOR) \
	$(CK_GRATICULE_GENERATOR) \
	$(TEST_DIR)/test-cahill-keyes-projection \
	$(TEST_DIR)/test-cahill-keyes-projection-api \
	$(TEST_DIR)/test-cahill-keyes-path-functions \
	$(TEST_DIR)/test-authagraph-projection-api \
	$(TEST_DIR)/test-myriahedral-projection-api \
	$(TEST_DIR)/test-voronoi-projection-api

.PHONY: check clean generate-geometry generate-graticules-ck
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

clean:
	$(RM) $(TEST_BINARIES) $(CK_GEOMETRY_SVG) $(CK_GRATICULE_SVG)

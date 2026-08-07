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
GZIP ?= gzip
PNG_LONG_SIDE ?= 3840
ASSET_JOBS ?= 2
LABEL_FONT ?= atkinson_hyperlegible
PNG_EXPORT_BACKGROUND := --export-background=white \
	--export-background-opacity=255 \
	--export-png-color-mode=RGB_8

.DELETE_ON_ERROR:

INKSCAPE_SUPPORTS_APP_ID_TAG := $(shell \
	"$(INKSCAPE)" --help-all 2>/dev/null | \
	grep -q -- '--app-id-tag' && printf '%s' yes)

ifeq ($(INKSCAPE_SUPPORTS_APP_ID_TAG),yes)
INKSCAPE_INSTANCE_ARGS = --app-id-tag=cartofreako_$$$$
else
INKSCAPE_INSTANCE_ARGS =
endif
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
CLOUD_ATMOSPHERE_DATA_DIR ?= $(STATIC_ASSET_DIR)/cloud-atmosphere
CLOUD_ATMOSPHERE_PROFILE ?= \
	$(CLOUD_ATMOSPHERE_DATA_DIR)/cloud-atmosphere-profile.json
CLOUD_ATMOSPHERE_GEOJSON ?= \
	$(CLOUD_ATMOSPHERE_DATA_DIR)/.prepared/cloud-atmosphere-latest.geojson
CLOUD_ATMOSPHERE_FIXTURE := \
	$(CLOUD_ATMOSPHERE_DATA_DIR)/fixtures/cloud-atmosphere-fixture.geojson
CLOUD_ATMOSPHERE_FETCHER := scripts/fetch-cloud-atmosphere-data.sh
CLOUD_ATMOSPHERE_PTREE_RESOLVER := scripts/resolve-jaxa-ptree.sh
CLOUD_ATMOSPHERE_STAC_RESOLVER := scripts/resolve-jaxa-stac.py
CLOUD_ATMOSPHERE_PREPARATION_SCRIPT := \
	scripts/prepare-cloud-atmosphere-data.sh
CLOUD_ATMOSPHERE_VERIFIER := scripts/verify-cloud-atmosphere-data.sh
ORBITING_DATA_DIR ?= $(STATIC_ASSET_DIR)/orbital-technosphere
ORBITING_PROFILE ?= \
	$(ORBITING_DATA_DIR)/orbital-technosphere-profile.json
ORBITING_FETCHER := scripts/fetch-orbiting-data.sh
ANTHROPOCENE_DATA_DIR ?= $(STATIC_ASSET_DIR)/anthropocene
ANTHROPOCENE_PROFILE ?= \
	$(ANTHROPOCENE_DATA_DIR)/anthropocene-profile.json
ANTHROPOCENE_GEOJSON ?= \
	$(ANTHROPOCENE_DATA_DIR)/anthropocene-2026.geojson
ANTHROPOCENE_FETCHER := scripts/fetch-anthropocene-data.sh
ANTHROPOCENE_PREPARATION_SCRIPT := scripts/prepare-anthropocene-data.sh
ANTHROPOCENE_VERIFIER := scripts/verify-anthropocene-data.sh
ANTHROPOCENE_TEMPERATURE_PROFILE_2025 ?= \
	$(ANTHROPOCENE_DATA_DIR)/anthropocene-temperature-2025-profile.json
ANTHROPOCENE_TEMPERATURE_PROFILE_2026 ?= \
	$(ANTHROPOCENE_DATA_DIR)/anthropocene-temperature-2026-profile.json
ANTHROPOCENE_TEMPERATURE_GEOJSON_2025 ?= \
	$(ANTHROPOCENE_DATA_DIR)/anthropocene-temperature-2025.geojson
ANTHROPOCENE_TEMPERATURE_GEOJSON_2026 ?= \
	$(ANTHROPOCENE_DATA_DIR)/anthropocene-temperature-2026.geojson
ANTHROPOCENE_CPC_FETCHER := scripts/fetch-anthropocene-cpc-data.sh
ANTHROPOCENE_TEMPERATURE_PREPARATION_SCRIPT := \
	scripts/prepare-anthropocene-temperature-data.sh
RESOURCES_DATA_DIR ?= $(STATIC_ASSET_DIR)/resources
RESOURCES_PROFILE ?= $(RESOURCES_DATA_DIR)/resources-profile.json
RESOURCES_VALUES ?= $(RESOURCES_DATA_DIR)/resources-values.json
RESOURCES_COUNTRIES ?= $(RESOURCES_DATA_DIR)/countries-110m.geojson
RESOURCES_REEFS ?= $(RESOURCES_DATA_DIR)/coral-reefs-025deg.geojson
RESOURCES_CHECKSUMS := $(RESOURCES_DATA_DIR)/SHA256SUMS
RESOURCES_FETCHER := scripts/fetch-resources-data.sh
RESOURCES_PREPARER := scripts/prepare-resources-data.py
EXTERNAL_AUTHORIZER := scripts/authorize-external.sh
EXTERNAL_GENERATOR := scripts/generate-authorized-external.sh
EXTERNAL_MAKE_COMMAND ?= $(firstword $(MAKE))
JAXA_CERTIFICATE_INSTALLER := scripts/install-jaxa-certificate.sh
EXTERNAL_PASSES ?= jaxa-ptree nasa-firms network-topology
PTREE_NETRC ?= $(HOME)/.netrc
PTREE_CACERT ?=
NETWORK_TOPOLOGY_LICENSE_ACCEPTED ?=
NETWORK_SWARM_DATA_DIR ?= $(STATIC_ASSET_DIR)/network-swarm
NETWORK_SWARM_PROFILE ?= $(NETWORK_SWARM_DATA_DIR)/network-swarm-profile.json
NETWORK_SWARM_SOURCE ?= \
	$(NETWORK_SWARM_DATA_DIR)/house-of-the-dragon-301-cumulative-aggregate.geojson.zip
NETWORK_SWARM_PREPARED_DIR ?= $(NETWORK_SWARM_DATA_DIR)/.prepared
NETWORK_SWARM_GEOJSON ?= \
	$(NETWORK_SWARM_PREPARED_DIR)/$(patsubst %.zip,%,$(notdir $(NETWORK_SWARM_SOURCE)))
NETWORK_SWARM_PREPARER := scripts/prepare-network-swarm-data.sh
NETWORK_INFRASTRUCTURE_DATA_DIR ?= \
	$(STATIC_ASSET_DIR)/network-infrastructure
NETWORK_INFRASTRUCTURE_SITES_PROFILE ?= \
	$(NETWORK_INFRASTRUCTURE_DATA_DIR)/network-infrastructure-sites-profile.json
NETWORK_INFRASTRUCTURE_TOPOLOGY_PROFILE ?= \
	$(NETWORK_INFRASTRUCTURE_DATA_DIR)/network-infrastructure-topology-profile.json
NETWORK_INFRASTRUCTURE_CLOUD_SOURCE ?= ../cloud_cdn_cache
SUBMARINE_CABLE_SOURCE ?= ../www.submarinecablemap.com
INTERNET_EXCHANGE_SOURCE ?= ../www.internetexchangemap.com
NETWORK_INFRASTRUCTURE_CLOUD_MANIFEST := \
	$(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE)/data/manifest.20260805.json
SUBMARINE_CABLE_ROUTES := \
	$(SUBMARINE_CABLE_SOURCE)/web/public/api/v3/cable/cable-geo.json
SUBMARINE_CABLE_LANDINGS := \
	$(SUBMARINE_CABLE_SOURCE)/web/public/api/v3/landing-point/landing-point-geo.json
INTERNET_EXCHANGE_BUILDINGS := \
	$(INTERNET_EXCHANGE_SOURCE)/public/api/v2/buildings.geojson
NETWORK_INFRASTRUCTURE_SOURCE_CHECKER := \
	scripts/check-network-infrastructure-sources.sh
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
PROJECTIONS_WEB_SOURCE := $(WEB_DIR)/cartofreako-projections-web.cc
PROJECTIONS_WEB_SMOKE := $(WEB_DIR)/cartofreako-projections-smoke.mjs
PROJECTIONS_WEB_BROWSER_SMOKE := $(WEB_DIR)/cartofreako-browser-smoke.html
PROJECTIONS_WEB_BROWSER_RUNNER := scripts/run-wasm-browser-smoke.py
PROJECTIONS_WEB_MODULE := $(WEB_BUILD_DIR)/cartofreako-projections.mjs
PROJECTIONS_WEB_WASM := $(WEB_BUILD_DIR)/cartofreako-projections.wasm
PROJECTIONS_WEB_JS := \
	$(WEB_DIR)/cartofreako-web.mjs \
	$(WEB_DIR)/cartofreako-svg.mjs \
	$(WEB_DIR)/cartofreako-canvas.mjs \
	$(WEB_DIR)/cartofreako-d3.mjs \
	$(WEB_DIR)/cartofreako-projections-worker.mjs \
	$(WEB_DIR)/cartofreako-worker-client.mjs
PROJECTION_RUNTIME_HEADERS := \
	$(PROJECTION_SRC_DIR)/cart0freak0-projection-runtime.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-projection-slicing.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-projection-geometry.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-perspectives.h \
	$(wildcard $(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-perspective-*-tree.inc)

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
CLOUD_ATMOSPHERE_GENERATOR := \
	$(GENERATOR_SRC_DIR)/generate-cloud-atmosphere
CLOUD_ATMOSPHERE_PREPARER := \
	$(GENERATOR_SRC_DIR)/prepare-cloud-atmosphere
ORBITING_GENERATOR := $(GENERATOR_SRC_DIR)/generate-orbiting
ANTHROPOCENE_GENERATOR := $(GENERATOR_SRC_DIR)/generate-anthropocene
ANTHROPOCENE_PREPARER := $(GENERATOR_SRC_DIR)/prepare-anthropocene
ANTHROPOCENE_TEMPERATURE_GENERATOR := \
	$(GENERATOR_SRC_DIR)/generate-anthropocene-temperature
ANTHROPOCENE_TEMPERATURE_PREPARER := \
	$(GENERATOR_SRC_DIR)/prepare-anthropocene-temperature
RESOURCES_GENERATOR := $(GENERATOR_SRC_DIR)/generate-resources
NETWORK_SWARM_GENERATOR := $(GENERATOR_SRC_DIR)/generate-network-swarm
NETWORK_INFRASTRUCTURE_GENERATOR := \
	$(GENERATOR_SRC_DIR)/generate-network-infrastructure
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

CLOUD_ATMOSPHERE_SVGS := \
	$(GENERATED_SVG_DIR)/cloud-atmosphere-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/cloud-atmosphere-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/cloud-atmosphere-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/cloud-atmosphere-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/cloud-atmosphere-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/cloud-atmosphere-voronoi-44-22.916667.svg
CLOUD_ATMOSPHERE_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(CLOUD_ATMOSPHERE_SVGS))
CLOUD_ATMOSPHERE_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(CLOUD_ATMOSPHERE_SVGS))

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

NETWORK_SWARM_SVGS := \
	$(GENERATED_SVG_DIR)/network-swarm-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/network-swarm-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/network-swarm-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/network-swarm-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/network-swarm-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/network-swarm-voronoi-44-22.916667.svg
NETWORK_SWARM_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(NETWORK_SWARM_SVGS))
NETWORK_SWARM_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(NETWORK_SWARM_SVGS))

NETWORK_INFRASTRUCTURE_SITES_SVGS := \
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-voronoi-44-22.916667.svg
NETWORK_INFRASTRUCTURE_SITES_PDFS := \
	$(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(NETWORK_INFRASTRUCTURE_SITES_SVGS))
NETWORK_INFRASTRUCTURE_SITES_PNGS := \
	$(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(NETWORK_INFRASTRUCTURE_SITES_SVGS))
NETWORK_INFRASTRUCTURE_TOPOLOGY_SVGS := \
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-voronoi-44-22.916667.svg
NETWORK_INFRASTRUCTURE_TOPOLOGY_PDFS := \
	$(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(NETWORK_INFRASTRUCTURE_TOPOLOGY_SVGS))
NETWORK_INFRASTRUCTURE_TOPOLOGY_PNGS := \
	$(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(NETWORK_INFRASTRUCTURE_TOPOLOGY_SVGS))
NETWORK_INFRASTRUCTURE_TOPOLOGY_LANDSCAPE_PNGS := \
	$(filter-out $(GENERATED_PNG_DIR)/network-infrastructure-topology-star-x-34-44.png,\
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_PNGS))

ANTHROPOCENE_SVGS := \
	$(GENERATED_SVG_DIR)/anthropocene-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/anthropocene-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/anthropocene-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/anthropocene-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/anthropocene-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/anthropocene-voronoi-44-22.916667.svg
ANTHROPOCENE_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(ANTHROPOCENE_SVGS))
ANTHROPOCENE_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(ANTHROPOCENE_SVGS))
ANTHROPOCENE_TEMPERATURE_2025_SVGS := \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-voronoi-44-22.916667.svg
ANTHROPOCENE_TEMPERATURE_2026_SVGS := \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-ck-44-22.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-authagraph-44-19.052559.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-dymaxion-44-20.78461.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-myriahedral-44-24.75.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-star-x-34-44.svg \
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-voronoi-44-22.916667.svg
ANTHROPOCENE_TEMPERATURE_SVGS := \
	$(ANTHROPOCENE_TEMPERATURE_2025_SVGS) \
	$(ANTHROPOCENE_TEMPERATURE_2026_SVGS)
ANTHROPOCENE_TEMPERATURE_PDFS := \
	$(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(ANTHROPOCENE_TEMPERATURE_SVGS))
ANTHROPOCENE_TEMPERATURE_PNGS := \
	$(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(ANTHROPOCENE_TEMPERATURE_SVGS))

RESOURCE_OUTPUT_SUFFIXES := ck-44-22 authagraph-44-19.052559 \
	dymaxion-44-20.78461 myriahedral-44-24.75 star-x-34-44 \
	voronoi-44-22.916667
resource_metric_svgs = $(addprefix $(GENERATED_SVG_DIR)/$(1)-$(2)-,\
	$(addsuffix .svg,$(RESOURCE_OUTPUT_SUFFIXES)))

RESOURCES_ENERGY_SOLAR_SVGS := $(call resource_metric_svgs,resources-energy,solar-capacity-2025)
RESOURCES_ENERGY_WIND_SVGS := $(call resource_metric_svgs,resources-energy,wind-capacity-2025)
RESOURCES_ENERGY_NUCLEAR_SVGS := $(call resource_metric_svgs,resources-energy,nuclear-operating-capacity-2024)
RESOURCES_ENERGY_PETROCHEMICAL_SVGS := $(call resource_metric_svgs,resources-energy,petrochemical-refinery-throughput-latest-2024)
RESOURCES_ENERGY_SVGS := $(RESOURCES_ENERGY_SOLAR_SVGS) \
	$(RESOURCES_ENERGY_WIND_SVGS) $(RESOURCES_ENERGY_NUCLEAR_SVGS) \
	$(RESOURCES_ENERGY_PETROCHEMICAL_SVGS)

RESOURCES_FOOD_SVGS := $(call resource_metric_svgs,resources-food,food-production-index-2022)
RESOURCES_FAUNA_FISHERIES_SVGS := $(call resource_metric_svgs,resources-fauna,fisheries-production-latest-2024)
RESOURCES_FAUNA_REEFS_SVGS := $(call resource_metric_svgs,resources-fauna,coral-reef-threat-2011)
RESOURCES_FAUNA_SVGS := $(RESOURCES_FAUNA_FISHERIES_SVGS) \
	$(RESOURCES_FAUNA_REEFS_SVGS)
RESOURCES_FLORA_SVGS := $(call resource_metric_svgs,resources-flora,forest-area-percent-2023)
RESOURCES_MINERAL_SVGS := $(call resource_metric_svgs,resources-mineral,rare-earth-mine-production-2025)

RESOURCES_HUMAN_UNDER_30_SVGS := $(call resource_metric_svgs,resources-human,population-under-30-2024)
RESOURCES_HUMAN_OVER_60_SVGS := $(call resource_metric_svgs,resources-human,population-over-60-2024)
RESOURCES_HUMAN_UPPER_SECONDARY_SVGS := $(call resource_metric_svgs,resources-human,upper-secondary-attainment-latest-2025)
RESOURCES_HUMAN_BACHELORS_SVGS := $(call resource_metric_svgs,resources-human,bachelors-attainment-latest-2024)
RESOURCES_HUMAN_PATENTS_SVGS := $(call resource_metric_svgs,resources-human,resident-patent-applications-per-million-2019-2021)
RESOURCES_HUMAN_SVGS := $(RESOURCES_HUMAN_UNDER_30_SVGS) \
	$(RESOURCES_HUMAN_OVER_60_SVGS) \
	$(RESOURCES_HUMAN_UPPER_SECONDARY_SVGS) \
	$(RESOURCES_HUMAN_BACHELORS_SVGS) $(RESOURCES_HUMAN_PATENTS_SVGS)

RESOURCES_SVGS := $(RESOURCES_ENERGY_SVGS) $(RESOURCES_FOOD_SVGS) \
	$(RESOURCES_FAUNA_SVGS) $(RESOURCES_FLORA_SVGS) \
	$(RESOURCES_MINERAL_SVGS) $(RESOURCES_HUMAN_SVGS)
RESOURCES_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(RESOURCES_SVGS))
RESOURCES_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(RESOURCES_SVGS))
RESOURCES_SVG_ARCHIVES := $(addsuffix .gz,$(RESOURCES_SVGS))

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
	$(ASTRO_SVGS) $(ORBITING_SVGS) $(NETWORK_SWARM_SVGS) \
	$(NETWORK_INFRASTRUCTURE_SITES_SVGS) \
	$(ANTHROPOCENE_SVGS) $(ANTHROPOCENE_TEMPERATURE_SVGS) \
	$(RESOURCES_SVGS) \
	$(BATHYMETRY_ROULETTE_SVGS)
GENERATED_PDFS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PDF_DIR)/%.pdf,$(GENERATED_SVGS))
GENERATED_PNGS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(GENERATED_PNG_DIR)/%.png,$(GENERATED_SVGS))
CK_SNAPSHOT_SVGS := \
	$(CK_GEOMETRY_SVG) $(CK_GRATICULE_SVG) $(CK_EARTH_SVG) $(CK_WATER_SVG) \
	$(filter %-ck-44-22.svg,$(ASTRO_SVGS) $(ORBITING_SVGS) \
		$(NETWORK_SWARM_SVGS) $(NETWORK_INFRASTRUCTURE_SITES_SVGS) \
		$(ANTHROPOCENE_SVGS) $(ANTHROPOCENE_TEMPERATURE_SVGS) \
		$(RESOURCES_SVGS) $(BATHYMETRY_ROULETTE_SVGS))
CK_SNAPSHOT_THUMBNAIL_DIR := \
	$(GENERATED_DIR)/thumbnail/cahill-keyes
CK_SNAPSHOT_WIDTH ?= 480
CK_SNAPSHOT_THUMBNAILS := $(patsubst $(GENERATED_SVG_DIR)/%.svg,\
	$(CK_SNAPSHOT_THUMBNAIL_DIR)/%.png,$(CK_SNAPSHOT_SVGS))
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
NETWORK_SWARM_STAR_X_PNG := $(GENERATED_PNG_DIR)/network-swarm-star-x-34-44.png
NETWORK_INFRASTRUCTURE_SITES_STAR_X_PNG := \
	$(GENERATED_PNG_DIR)/network-infrastructure-sites-star-x-34-44.png
NETWORK_INFRASTRUCTURE_TOPOLOGY_STAR_X_PNG := \
	$(GENERATED_PNG_DIR)/network-infrastructure-topology-star-x-34-44.png
ANTHROPOCENE_STAR_X_PNG := \
	$(GENERATED_PNG_DIR)/anthropocene-star-x-34-44.png
ANTHROPOCENE_TEMPERATURE_STAR_X_PNGS := \
	$(GENERATED_PNG_DIR)/anthropocene-temperature-2025-star-x-34-44.png \
	$(GENERATED_PNG_DIR)/anthropocene-temperature-2026-star-x-34-44.png
RESOURCES_STAR_X_PNGS := $(filter %-star-x-34-44.png,$(RESOURCES_PNGS))
BATHYMETRY_ROULETTE_STAR_X_PNG := \
	$(GENERATED_PNG_DIR)/bathymetry-roulette-star-x-34-44.png
CLOUD_ATMOSPHERE_STAR_X_PNG := \
	$(GENERATED_PNG_DIR)/cloud-atmosphere-star-x-34-44.png
MYRIAHEDRAL_PORTRAIT_SLICE_PNG := \
	$(GENERATED_PNG_DIR)/water-myriahedral-adhoc-slice-1.png
PORTRAIT_PNGS := $(STAR_X_PNGS) $(ASTRO_STAR_X_PNGS) \
	$(ORBITING_STAR_X_PNGS) $(NETWORK_SWARM_STAR_X_PNG) \
	$(NETWORK_INFRASTRUCTURE_SITES_STAR_X_PNG) \
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_STAR_X_PNG) \
	$(ANTHROPOCENE_STAR_X_PNG) $(ANTHROPOCENE_TEMPERATURE_STAR_X_PNGS) \
	$(RESOURCES_STAR_X_PNGS) $(CK_SLICE_PNGS) \
	$(BATHYMETRY_ROULETTE_STAR_X_PNG) \
	$(CLOUD_ATMOSPHERE_STAR_X_PNG) \
	$(MYRIAHEDRAL_PORTRAIT_SLICE_PNG)
LANDSCAPE_PNGS := $(filter-out $(PORTRAIT_PNGS),\
	$(GENERATED_PNGS) $(CLOUD_ATMOSPHERE_PNGS))
GENERATED_ARTIFACTS := \
	$(filter-out $(RESOURCES_SVGS),$(GENERATED_SVGS)) \
	$(RESOURCES_SVG_ARCHIVES) $(GENERATED_PDFS) $(GENERATED_PNGS) \
	$(CK_SNAPSHOT_THUMBNAILS)

GENERATOR_BINARIES := \
	$(ANTHROPOCENE_GENERATOR) \
	$(ANTHROPOCENE_PREPARER) \
	$(ANTHROPOCENE_TEMPERATURE_GENERATOR) \
	$(ANTHROPOCENE_TEMPERATURE_PREPARER) \
	$(RESOURCES_GENERATOR) \
	$(ASTRO_GENERATOR) \
	$(CLOUD_ATMOSPHERE_GENERATOR) \
	$(CLOUD_ATMOSPHERE_PREPARER) \
	$(BATHYMETRY_ROULETTE_GENERATOR) \
	$(GENERATION_PROFILE_RESOLVER) \
	$(NETWORK_INFRASTRUCTURE_GENERATOR) \
	$(NETWORK_SWARM_GENERATOR) \
	$(ORBITING_GENERATOR) \
	$(EIGHT_SLICE_GENERATOR) \
	$(EARTH_GENERATOR) \
	$(FOUR_SLICE_GENERATOR) \
	$(GEOMETRY_GENERATOR) \
	$(GRATICULE_GENERATOR) \
	$(MYRIAHEDRAL_SLICE_GENERATOR) \
	$(WATER_GENERATOR)
TEST_BINARIES := \
	$(TEST_DIR)/test-anthropocene-generation \
	$(TEST_DIR)/test-anthropocene-temperature-generation \
	$(TEST_DIR)/test-resources-generation \
	$(TEST_DIR)/test-astro-generation \
	$(TEST_DIR)/test-cloud-atmosphere-generation \
	$(TEST_DIR)/test-bathymetry-roulette-style \
	$(TEST_DIR)/test-generation-profile \
	$(TEST_DIR)/test-generation-typography \
	$(TEST_DIR)/test-network-infrastructure-generation \
	$(TEST_DIR)/test-network-swarm-generation \
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
	$(TEST_DIR)/test-projection-runtime \
	$(TEST_DIR)/test-star-x-projection-api \
	$(TEST_DIR)/test-voronoi-projection-api

GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/generation-instant.h \
	$(GENERATOR_SRC_DIR)/solar-geometry.h \
	$(GENERATOR_SRC_DIR)/generation-typography.h \
	$(GENERATOR_SRC_DIR)/projection-generation-common.h \
	$(GENERATOR_SRC_DIR)/myriahedral-perspective-generation.h \
	$(PROJECTION_RUNTIME_HEADERS) \
	$(PROJECTION_SRC_DIR)/a60-carto.h \
	$(PROJECTION_SRC_DIR)/a60-carto-frame.h \
	$(PROJECTION_SRC_DIR)/a60-carto-projection.h \
	$(PROJECTION_SRC_DIR)/a60-carto-projection-dymaxion.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-authagraph.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-cahill-keyes-functions.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-myriahedral-tree.inc \
	$(PROJECTION_SRC_DIR)/cart0freak0-star-x.h \
	$(PROJECTION_SRC_DIR)/cart0freak0-star-x-functions.h \
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
CLOUD_ATMOSPHERE_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/cloud-atmosphere-data.h \
	$(GENERATOR_SRC_DIR)/cloud-atmosphere-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)
ORBITING_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/orbiting-data.h \
	$(GENERATOR_SRC_DIR)/orbiting-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS) $(SGP4_HEADER)
NETWORK_SWARM_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/network-swarm-data.h \
	$(GENERATOR_SRC_DIR)/network-swarm-clustering.h \
	$(GENERATOR_SRC_DIR)/network-swarm-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)
NETWORK_INFRASTRUCTURE_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/network-infrastructure-data.h \
	$(GENERATOR_SRC_DIR)/network-infrastructure-clustering.h \
	$(GENERATOR_SRC_DIR)/network-infrastructure-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)
ANTHROPOCENE_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/anthropocene-data.h \
	$(GENERATOR_SRC_DIR)/anthropocene-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)
ANTHROPOCENE_TEMPERATURE_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/anthropocene-temperature-data.h \
	$(GENERATOR_SRC_DIR)/anthropocene-temperature-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)
RESOURCES_GENERATOR_HEADERS := \
	$(GENERATOR_SRC_DIR)/resources-data.h \
	$(GENERATOR_SRC_DIR)/resources-generation.h \
	$(NATURAL_EARTH_GENERATOR_HEADER) \
	$(GENERATOR_HEADERS)

.DEFAULT_GOAL := configured

RESOURCE_PROJECTION_NAMES := cahill-keyes authagraph dymaxion myriahedral \
	star-x voronoi
RESOURCE_METRIC_TARGET_STEMS := resources-energy-solar resources-energy-wind \
	resources-energy-nuclear resources-energy-petrochemical \
	resources-food-production resources-fauna-fisheries resources-fauna-reefs \
	resources-flora-forest resources-mineral-rare-earth \
	resources-human-under-30 resources-human-over-60 \
	resources-human-upper-secondary resources-human-bachelors \
	resources-human-patents
RESOURCE_METRIC_PUBLIC_TARGETS := \
	$(foreach stem,$(RESOURCE_METRIC_TARGET_STEMS),generate-$(stem) \
		$(foreach projection,$(RESOURCE_PROJECTION_NAMES),\
			generate-$(stem)-$(projection)))

PUBLIC_TARGETS := all assets-single assets-resilient check check-prerequisite \
	check-resources-svg-archives clean clean-failed-generated configured doxygen \
	generation-plan list-targets authorize-external \
	generate-authorized-external generate-snapshot-ck \
	install-jaxa-certificate \
	fetch-natural-earth-10m fetch-astro-data fetch-orbiting-data \
	fetch-cloud-atmosphere-data prepare-cloud-atmosphere-data \
	verify-cloud-atmosphere-data \
	fetch-anthropocene-data prepare-anthropocene-data \
	fetch-anthropocene-cpc-data prepare-anthropocene-temperature-data \
	refresh-resources-data \
	prepare-network-swarm-data make-generated \
	check-network-infrastructure-sources \
	check-network-infrastructure-topology-sources \
	wasm-cahill-keyes check-wasm-cahill-keyes \
	wasm-cahill-myriahedral check-wasm-cahill-myriahedral \
	wasm-projections check-wasm-projections \
	check-wasm-projections-browser wasm check-wasm \
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
	generate-cloud-atmosphere generate-cloud-atmosphere-projections \
	generate-cloud-atmosphere-artifacts \
	generate-cloud-atmosphere-cahill-keyes \
	generate-cloud-atmosphere-authagraph \
	generate-cloud-atmosphere-dymaxion \
	generate-cloud-atmosphere-myriahedral \
	generate-cloud-atmosphere-star-x \
	generate-cloud-atmosphere-voronoi \
	generate-orbiting generate-orbiting-projections \
	generate-orbiting-artifacts \
	generate-orbiting-global generate-orbiting-observer \
	generate-orbiting-cahill-keyes generate-orbiting-authagraph \
	generate-orbiting-dymaxion generate-orbiting-myriahedral \
	generate-orbiting-star-x generate-orbiting-voronoi \
	generate-anthropocene generate-anthropocene-projections \
	generate-anthropocene-artifacts \
	generate-anthropocene-atlas generate-anthropocene-atlas-projections \
	generate-anthropocene-atlas-artifacts \
	generate-anthropocene-atlas-cahill-keyes \
	generate-anthropocene-atlas-authagraph \
	generate-anthropocene-atlas-dymaxion \
	generate-anthropocene-atlas-myriahedral \
	generate-anthropocene-atlas-star-x generate-anthropocene-atlas-voronoi \
	generate-anthropocene-cahill-keyes generate-anthropocene-authagraph \
	generate-anthropocene-dymaxion generate-anthropocene-myriahedral \
	generate-anthropocene-star-x generate-anthropocene-voronoi \
	generate-anthropocene-2025 generate-anthropocene-2026 \
	generate-anthropocene-years generate-anthropocene-year-artifacts \
	generate-anthropocene-temperature-2025 \
	generate-anthropocene-temperature-2026 \
	generate-anthropocene-temperature-years \
	generate-anthropocene-temperature-artifacts \
	generate-resources generate-resources-projections \
	generate-resources-stage6b generate-resources-stage12 \
	generate-resources-artifacts \
	generate-resources-energy generate-resources-food \
	generate-resources-fauna \
	generate-resources-flora generate-resources-mineral \
	generate-resources-human \
	generate-resources-cahill-keyes generate-resources-authagraph \
	generate-resources-dymaxion generate-resources-myriahedral \
	generate-resources-star-x generate-resources-voronoi \
	generate-resources-energy-cahill-keyes \
	generate-resources-energy-authagraph generate-resources-energy-dymaxion \
	generate-resources-energy-myriahedral generate-resources-energy-star-x \
	generate-resources-energy-voronoi \
	generate-resources-food-cahill-keyes \
	generate-resources-food-authagraph generate-resources-food-dymaxion \
	generate-resources-food-myriahedral generate-resources-food-star-x \
	generate-resources-food-voronoi \
	generate-resources-fauna-cahill-keyes \
	generate-resources-fauna-authagraph generate-resources-fauna-dymaxion \
	generate-resources-fauna-myriahedral generate-resources-fauna-star-x \
	generate-resources-fauna-voronoi \
	generate-resources-flora-cahill-keyes \
	generate-resources-flora-authagraph generate-resources-flora-dymaxion \
	generate-resources-flora-myriahedral generate-resources-flora-star-x \
	generate-resources-flora-voronoi \
	generate-resources-mineral-cahill-keyes \
	generate-resources-mineral-authagraph generate-resources-mineral-dymaxion \
	generate-resources-mineral-myriahedral generate-resources-mineral-star-x \
	generate-resources-mineral-voronoi \
	generate-resources-human-cahill-keyes \
	generate-resources-human-authagraph generate-resources-human-dymaxion \
	generate-resources-human-myriahedral generate-resources-human-star-x \
	generate-resources-human-voronoi \
	generate-network-swarm generate-network-swarm-projections \
	generate-network-swarm-artifacts \
	generate-network-swarm-cahill-keyes generate-network-swarm-authagraph \
	generate-network-swarm-dymaxion generate-network-swarm-myriahedral \
	generate-network-swarm-star-x generate-network-swarm-voronoi \
	generate-network-infrastructure generate-network-infrastructure-sites \
	generate-network-infrastructure-projections \
	generate-network-infrastructure-artifacts \
	generate-network-infrastructure-cahill-keyes \
	generate-network-infrastructure-authagraph \
	generate-network-infrastructure-dymaxion \
	generate-network-infrastructure-myriahedral \
	generate-network-infrastructure-star-x \
	generate-network-infrastructure-voronoi \
	generate-network-infrastructure-topology \
	generate-network-infrastructure-topology-projections \
	generate-network-infrastructure-topology-artifacts \
	generate-network-infrastructure-topology-cahill-keyes \
	generate-network-infrastructure-topology-authagraph \
	generate-network-infrastructure-topology-dymaxion \
	generate-network-infrastructure-topology-myriahedral \
	generate-network-infrastructure-topology-star-x \
	generate-network-infrastructure-topology-voronoi \
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
	generate-earth-voronoi generate-water-voronoi \
	$(RESOURCE_METRIC_PUBLIC_TARGETS)

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
		NETWORK_INFRASTRUCTURE_CLOUD_SOURCE="$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))" \
		SUBMARINE_CABLE_SOURCE="$(abspath $(SUBMARINE_CABLE_SOURCE))" \
		LABEL_FONT="$(LABEL_FONT)" \
		"$(PREREQUISITE_CHECKER)"

check-resources-svg-archives:
	"$(GZIP)" -t $(RESOURCES_SVG_ARCHIVES)

check: $(SGP4_OBJECT) $(NETWORK_SWARM_GEOJSON) $(ANTHROPOCENE_GEOJSON) \
		$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2025) \
		$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2026) \
		$(CLOUD_ATMOSPHERE_PROFILE) $(CLOUD_ATMOSPHERE_FIXTURE) \
		$(RESOURCES_PROFILE) $(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) \
		$(RESOURCES_REEFS) \
		$(RESOURCES_CHECKSUMS) \
		check-resources-svg-archives
	$(ANTHROPOCENE_VERIFIER) "$(ANTHROPOCENE_PROFILE)" \
		"$(ANTHROPOCENE_GEOJSON)"
	$(ANTHROPOCENE_VERIFIER) "$(ANTHROPOCENE_TEMPERATURE_PROFILE_2025)" \
		"$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2025)"
	$(ANTHROPOCENE_VERIFIER) "$(ANTHROPOCENE_TEMPERATURE_PROFILE_2026)" \
		"$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2026)"
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$(TEST_DIR)/test-anthropocene-generation.cc \
		$(shell $(GDAL_CONFIG) --libs) -lh3 \
		-o $(TEST_DIR)/test-anthropocene-generation
	$(TEST_DIR)/test-anthropocene-generation
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$(TEST_DIR)/test-anthropocene-temperature-generation.cc \
		$(shell $(GDAL_CONFIG) --libs) -lh3 \
		-o $(TEST_DIR)/test-anthropocene-temperature-generation
	$(TEST_DIR)/test-anthropocene-temperature-generation
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$(TEST_DIR)/test-resources-generation.cc \
		$(shell $(GDAL_CONFIG) --libs) \
		-o $(TEST_DIR)/test-resources-generation
	$(TEST_DIR)/test-resources-generation
	cd "$(RESOURCES_DATA_DIR)" && sha256sum -c SHA256SUMS
	cd "$(ANTHROPOCENE_DATA_DIR)" && sha256sum -c SHA256SUMS
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-astro-generation.cc \
		-o $(TEST_DIR)/test-astro-generation
	$(TEST_DIR)/test-astro-generation
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$(TEST_DIR)/test-cloud-atmosphere-generation.cc \
		$(shell $(GDAL_CONFIG) --libs) -lh3 \
		-o $(TEST_DIR)/test-cloud-atmosphere-generation
	$(TEST_DIR)/test-cloud-atmosphere-generation
	$(TEST_DIR)/test-resolve-jaxa-ptree.sh
	python3 $(TEST_DIR)/test-resolve-jaxa-stac.py
	$(TEST_DIR)/test-generate-authorized-external.sh
	$(CXX) $(CPPFLAGS) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-bathymetry-roulette-style.cc \
		-o $(TEST_DIR)/test-bathymetry-roulette-style
	$(TEST_DIR)/test-bathymetry-roulette-style
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-generation-profile.cc \
		-o $(TEST_DIR)/test-generation-profile
	$(TEST_DIR)/test-generation-profile
	$(CXX) $(CPPFLAGS) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-generation-typography.cc \
		-o $(TEST_DIR)/test-generation-typography
	$(TEST_DIR)/test-generation-typography
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$(TEST_DIR)/test-network-infrastructure-generation.cc \
		$(shell $(GDAL_CONFIG) --libs) \
		-o $(TEST_DIR)/test-network-infrastructure-generation
	$(TEST_DIR)/test-network-infrastructure-generation
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-network-swarm-generation.cc \
		-lh3 \
		-o $(TEST_DIR)/test-network-swarm-generation
	$(TEST_DIR)/test-network-swarm-generation
	cd "$(NETWORK_SWARM_DATA_DIR)" && sha256sum -c SHA256SUMS
	printf '%s  %s\n' \
		'9fbd453d174df834208718e110396c5a22bff4312aeeff3e42d0175510b0ff69' \
		'$(abspath $(NETWORK_SWARM_GEOJSON))' | sha256sum -c -
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
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$(TEST_DIR)/test-projection-runtime.cc \
		-o $(TEST_DIR)/test-projection-runtime
	$(TEST_DIR)/test-projection-runtime
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

wasm-projections: $(PROJECTIONS_WEB_MODULE) $(PROJECTIONS_WEB_WASM) \
	$(PROJECTIONS_WEB_JS) $(PROJECTIONS_WEB_SMOKE)

$(PROJECTIONS_WEB_MODULE) $(PROJECTIONS_WEB_WASM) &: \
		$(PROJECTIONS_WEB_SOURCE) $(PROJECTION_RUNTIME_HEADERS)
	mkdir -p "$(WEB_BUILD_DIR)"
	EM_CACHE="$(EM_CACHE)" "$(EMXX)" "$(PROJECTIONS_WEB_SOURCE)" \
		-I "$(PROJECTION_SRC_DIR)" \
		-isystem "$(ALPHA60_SRC)" -isystem "$(IZZI_SRC)" \
		-std=c++20 -O3 -Wall -Wextra -Wpedantic -Werror \
		--bind --no-entry -fexceptions -sDISABLE_EXCEPTION_CATCHING=0 \
		-sMODULARIZE=1 -sEXPORT_ES6=1 \
		-sEXPORT_NAME=createCartofreakoProjectionModule \
		-sENVIRONMENT=web,node -sALLOW_MEMORY_GROWTH=1 -sFILESYSTEM=0 \
		-o "$(PROJECTIONS_WEB_MODULE)"

check-wasm-projections: wasm-projections
	cd "$(WEB_BUILD_DIR)" && "$(NODE)" cartofreako-projections-smoke.mjs

check-wasm-projections-browser: wasm-projections \
		$(PROJECTIONS_WEB_BROWSER_SMOKE) $(PROJECTIONS_WEB_BROWSER_RUNNER)
	python3 "$(PROJECTIONS_WEB_BROWSER_RUNNER)" \
		--browser "$(WEB_BROWSER)" "$(PROJECTIONS_WEB_BROWSER_SMOKE)"

wasm: wasm-projections wasm-cahill-keyes wasm-cahill-myriahedral
check-wasm: check-wasm-projections check-wasm-projections-browser \
	check-wasm-cahill-keyes \
	check-wasm-cahill-myriahedral

$(GEOMETRY_GENERATOR): $(GENERATOR_SRC_DIR)/generate-geometry.cc \
		$(GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) $(CXXFLAGS) \
		$< -o $@

$(GRATICULE_GENERATOR): $(GENERATOR_SRC_DIR)/generate-graticules.cc \
		$(NATURAL_EARTH_GENERATOR_HEADER) $(GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

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

$(CLOUD_ATMOSPHERE_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-cloud-atmosphere.cc \
		$(CLOUD_ATMOSPHERE_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

$(CLOUD_ATMOSPHERE_PREPARER): \
		$(GENERATOR_SRC_DIR)/prepare-cloud-atmosphere.cc \
		$(GENERATOR_SRC_DIR)/cloud-atmosphere-data.h \
		$(GENERATOR_SRC_DIR)/generation-instant.h
	$(CXX) $(CPPFLAGS) $(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

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

$(ANTHROPOCENE_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-anthropocene.cc \
		$(ANTHROPOCENE_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

$(ANTHROPOCENE_PREPARER): \
		$(GENERATOR_SRC_DIR)/prepare-anthropocene.cc
	$(CXX) $(CPPFLAGS) $(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

$(ANTHROPOCENE_TEMPERATURE_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-anthropocene-temperature.cc \
		$(ANTHROPOCENE_TEMPERATURE_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

$(ANTHROPOCENE_TEMPERATURE_PREPARER): \
		$(GENERATOR_SRC_DIR)/prepare-anthropocene-temperature.cc
	$(CXX) $(CPPFLAGS) $(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

$(RESOURCES_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-resources.cc \
		$(RESOURCES_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

$(NETWORK_SWARM_GENERATOR): $(GENERATOR_SRC_DIR)/generate-network-swarm.cc \
		$(NETWORK_SWARM_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -lh3 -o $@

$(NETWORK_INFRASTRUCTURE_GENERATOR): \
		$(GENERATOR_SRC_DIR)/generate-network-infrastructure.cc \
		$(NETWORK_INFRASTRUCTURE_GENERATOR_HEADERS)
	$(CXX) $(CPPFLAGS) -I$(ALPHA60_SRC) -I$(IZZI_SRC) \
		$(shell $(GDAL_CONFIG) --cflags) $(CXXFLAGS) \
		$< $(shell $(GDAL_CONFIG) --libs) -o $@

check-network-infrastructure-sources: \
		$(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER)
	"$(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER)" sites \
		"$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))"

check-network-infrastructure-topology-sources: \
		$(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER)
	"$(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER)" topology \
		"$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))" \
		"$(abspath $(SUBMARINE_CABLE_SOURCE))" \
		"$(abspath $(INTERNET_EXCHANGE_SOURCE))"

install-jaxa-certificate: $(JAXA_CERTIFICATE_INSTALLER)
	PTREE_CACERT="$(PTREE_CACERT)" "$(JAXA_CERTIFICATE_INSTALLER)"

authorize-external: $(EXTERNAL_AUTHORIZER) \
		$(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER)
	PTREE_NETRC="$(abspath $(PTREE_NETRC))" \
	PTREE_CACERT="$(PTREE_CACERT)" \
	NETWORK_TOPOLOGY_LICENSE_ACCEPTED="$(NETWORK_TOPOLOGY_LICENSE_ACCEPTED)" \
	NETWORK_INFRASTRUCTURE_SOURCE_CHECKER="$(abspath $(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER))" \
	NETWORK_INFRASTRUCTURE_CLOUD_SOURCE="$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))" \
	SUBMARINE_CABLE_SOURCE="$(abspath $(SUBMARINE_CABLE_SOURCE))" \
	INTERNET_EXCHANGE_SOURCE="$(abspath $(INTERNET_EXCHANGE_SOURCE))" \
		"$(EXTERNAL_AUTHORIZER)" $(EXTERNAL_PASSES)

# Mutating opt-in companion to authorize-external. With the default pass list,
# the driver reports and skips locally unconfigured providers. An explicit
# EXTERNAL_PASSES override is strict. A configured P-Tree pass installs the
# pinned per-user trust anchor when it is absent, then every selected pass is
# authorized before source fetching or rendering begins.
generate-authorized-external: $(EXTERNAL_GENERATOR) $(EXTERNAL_AUTHORIZER) \
		$(JAXA_CERTIFICATE_INSTALLER) \
		$(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER)
	PTREE_NETRC="$(abspath $(PTREE_NETRC))" \
	PTREE_CACERT="$(PTREE_CACERT)" \
	CLOUD_ATMOSPHERE_DATA_DIR="$(abspath $(CLOUD_ATMOSPHERE_DATA_DIR))" \
	CLOUD_ATMOSPHERE_PROFILE="$(abspath $(CLOUD_ATMOSPHERE_PROFILE))" \
	CLOUD_ATMOSPHERE_GEOJSON="$(abspath $(CLOUD_ATMOSPHERE_GEOJSON))" \
	ANTHROPOCENE_DATA_DIR="$(abspath $(ANTHROPOCENE_DATA_DIR))" \
	ANTHROPOCENE_PROFILE="$(abspath $(ANTHROPOCENE_PROFILE))" \
	NETWORK_TOPOLOGY_LICENSE_ACCEPTED="$(NETWORK_TOPOLOGY_LICENSE_ACCEPTED)" \
	NETWORK_INFRASTRUCTURE_CLOUD_SOURCE="$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))" \
	SUBMARINE_CABLE_SOURCE="$(abspath $(SUBMARINE_CABLE_SOURCE))" \
	INTERNET_EXCHANGE_SOURCE="$(abspath $(INTERNET_EXCHANGE_SOURCE))" \
	NETWORK_INFRASTRUCTURE_SOURCE_CHECKER="$(abspath $(NETWORK_INFRASTRUCTURE_SOURCE_CHECKER))" \
	EXTERNAL_AUTHORIZER="$(abspath $(EXTERNAL_AUTHORIZER))" \
	JAXA_CERTIFICATE_INSTALLER="$(abspath $(JAXA_CERTIFICATE_INSTALLER))" \
	EXTERNAL_SELECTION_MODE="$(if $(filter file,$(origin EXTERNAL_PASSES)),auto,strict)" \
	MAKE_COMMAND="$(EXTERNAL_MAKE_COMMAND)" \
		"$(EXTERNAL_GENERATOR)" $(EXTERNAL_PASSES)

fetch-astro-data: $(ASTRO_FETCHER)
	$(ASTRO_FETCHER) "$(ASTRO_DATA_DIR)"

fetch-cloud-atmosphere-data: $(CLOUD_ATMOSPHERE_FETCHER) \
		$(CLOUD_ATMOSPHERE_PTREE_RESOLVER) \
		$(CLOUD_ATMOSPHERE_STAC_RESOLVER) $(CLOUD_ATMOSPHERE_PROFILE)
	PTREE_NETRC="$(abspath $(PTREE_NETRC))" \
	PTREE_CACERT="$(PTREE_CACERT)" \
		$(CLOUD_ATMOSPHERE_FETCHER) "$(CLOUD_ATMOSPHERE_DATA_DIR)"

prepare-cloud-atmosphere-data: $(CLOUD_ATMOSPHERE_PREPARER) \
		$(CLOUD_ATMOSPHERE_PREPARATION_SCRIPT) \
		$(CLOUD_ATMOSPHERE_PROFILE)
	CLOUD_ATMOSPHERE_PREPARER="$(abspath $(CLOUD_ATMOSPHERE_PREPARER))" \
		$(CLOUD_ATMOSPHERE_PREPARATION_SCRIPT) \
		"$(CLOUD_ATMOSPHERE_DATA_DIR)"

verify-cloud-atmosphere-data: $(CLOUD_ATMOSPHERE_VERIFIER)
	$(CLOUD_ATMOSPHERE_VERIFIER) "$(CLOUD_ATMOSPHERE_DATA_DIR)"

$(CLOUD_ATMOSPHERE_GEOJSON):
	@printf '%s\n' \
		'missing prepared cloud-atmosphere snapshot: $@' \
		'run make fetch-cloud-atmosphere-data prepare-cloud-atmosphere-data' >&2
	@exit 1

fetch-orbiting-data: $(ORBITING_FETCHER) $(ORBITING_PROFILE)
	$(ORBITING_FETCHER) "$(ORBITING_DATA_DIR)"

fetch-anthropocene-data: $(ANTHROPOCENE_FETCHER) $(ANTHROPOCENE_PROFILE)
	$(ANTHROPOCENE_FETCHER) "$(ANTHROPOCENE_DATA_DIR)" \
		"$(ANTHROPOCENE_PROFILE)"

prepare-anthropocene-data: $(ANTHROPOCENE_PREPARER) \
		$(ANTHROPOCENE_PREPARATION_SCRIPT) $(ANTHROPOCENE_PROFILE)
	ANTHROPOCENE_PREPARER="$(abspath $(ANTHROPOCENE_PREPARER))" \
		$(ANTHROPOCENE_PREPARATION_SCRIPT) "$(ANTHROPOCENE_DATA_DIR)" \
		"$(ANTHROPOCENE_PROFILE)"

fetch-anthropocene-cpc-data: $(ANTHROPOCENE_CPC_FETCHER)
	$(ANTHROPOCENE_CPC_FETCHER) "$(ANTHROPOCENE_DATA_DIR)" 1979 2026

prepare-anthropocene-temperature-data: \
		$(ANTHROPOCENE_TEMPERATURE_PREPARER) \
		$(ANTHROPOCENE_TEMPERATURE_PREPARATION_SCRIPT) \
		$(ANTHROPOCENE_TEMPERATURE_PROFILE_2025) \
		$(ANTHROPOCENE_TEMPERATURE_PROFILE_2026)
	ANTHROPOCENE_TEMPERATURE_PREPARER="$(abspath $(ANTHROPOCENE_TEMPERATURE_PREPARER))" \
		$(ANTHROPOCENE_TEMPERATURE_PREPARATION_SCRIPT) \
		"$(ANTHROPOCENE_DATA_DIR)"

# Explicit maintainer workflow. Ordinary resources generation is offline and
# reads only the checked normalized snapshot.
refresh-resources-data: $(RESOURCES_FETCHER) $(RESOURCES_PREPARER)
	"$(RESOURCES_FETCHER)" "$(RESOURCES_DATA_DIR)"

fetch-natural-earth-10m: $(NATURAL_EARTH_STAMP)

prepare-network-swarm-data: $(NETWORK_SWARM_GEOJSON)

$(NETWORK_SWARM_PREPARED_DIR):
	mkdir -p "$@"

$(NETWORK_SWARM_GEOJSON): $(NETWORK_SWARM_SOURCE) $(NETWORK_SWARM_PREPARER) \
		| $(NETWORK_SWARM_PREPARED_DIR)
	"$(NETWORK_SWARM_PREPARER)" "$(NETWORK_SWARM_SOURCE)" "$@"

$(NETWORK_INFRASTRUCTURE_CLOUD_MANIFEST):
	@printf '%s\n' \
		'missing cloud/CDN source manifest: $@' \
		'expected a pinned checkout at $(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))' \
		'run make check-prerequisite for the complete source check' \
		'or set NETWORK_INFRASTRUCTURE_CLOUD_SOURCE to the checkout root' >&2
	@exit 1

$(NATURAL_EARTH_STAMP): $(NATURAL_EARTH_FETCHER)
	$(NATURAL_EARTH_FETCHER) "$(NATURAL_EARTH_DIR)"

$(GENERATED_DIR) $(GENERATED_SVG_DIR) $(GENERATED_PNG_DIR) \
		$(GENERATED_PDF_DIR) $(CK_SNAPSHOT_THUMBNAIL_DIR):
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
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
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
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
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
$(STAR_X_GRATICULE_SVG): $(NATURAL_EARTH_STAMP)
$(eval $(call PROJECTION_RULES,voronoi,\
	$(VORONOI_GEOMETRY_SVG),$(VORONOI_GRATICULE_SVG),\
	$(VORONOI_EARTH_SVG),$(VORONOI_WATER_SVG)))

# $(1): command-line projection name; $(2)-$(3): astronomy products.
define ASTRO_PROJECTION_RULES
generate-astro-$(1): $(2) $(3)
$(2): $(ASTRO_GENERATOR) $(ASTRO_PROFILE) $(ASTRO_CATALOGS) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(ASTRO_GENERATOR))" $(1) all-sky \
		"$(abspath $(ASTRO_PROFILE))"

$(3): $(ASTRO_GENERATOR) $(ASTRO_PROFILE) $(ASTRO_CATALOGS) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
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

# $(1): command-line projection name; $(2): cloud-atmosphere product.
define CLOUD_ATMOSPHERE_PROJECTION_RULES
generate-cloud-atmosphere-$(1): $(2)
$(2): $(CLOUD_ATMOSPHERE_GENERATOR) $(CLOUD_ATMOSPHERE_PROFILE) \
		$(CLOUD_ATMOSPHERE_GEOJSON) $(CLOUD_ATMOSPHERE_VERIFIER) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	$(CLOUD_ATMOSPHERE_VERIFIER) "$(CLOUD_ATMOSPHERE_DATA_DIR)"
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(CLOUD_ATMOSPHERE_GENERATOR))" $(1) \
		"$(abspath $(CLOUD_ATMOSPHERE_PROFILE))" \
		"$(abspath $(CLOUD_ATMOSPHERE_GEOJSON))"
endef

$(eval $(call CLOUD_ATMOSPHERE_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/cloud-atmosphere-ck-44-22.svg))
$(eval $(call CLOUD_ATMOSPHERE_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/cloud-atmosphere-authagraph-44-19.052559.svg))
$(eval $(call CLOUD_ATMOSPHERE_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/cloud-atmosphere-dymaxion-44-20.78461.svg))
$(eval $(call CLOUD_ATMOSPHERE_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/cloud-atmosphere-myriahedral-44-24.75.svg))
$(eval $(call CLOUD_ATMOSPHERE_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/cloud-atmosphere-star-x-34-44.svg))
$(eval $(call CLOUD_ATMOSPHERE_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/cloud-atmosphere-voronoi-44-22.916667.svg))

generate-cloud-atmosphere: $(CLOUD_ATMOSPHERE_SVGS)
generate-cloud-atmosphere-projections: $(CLOUD_ATMOSPHERE_SVGS)
generate-cloud-atmosphere-artifacts: $(CLOUD_ATMOSPHERE_SVGS) \
	$(CLOUD_ATMOSPHERE_PDFS) $(CLOUD_ATMOSPHERE_PNGS)

# $(1): command-line projection name; $(2)-$(3): Orbital Technosphere products.
define ORBITING_PROJECTION_RULES
generate-orbiting-$(1): $(2) $(3)
$(2): $(ORBITING_GENERATOR) $(ORBITING_PROFILE) $(ORBITING_CATALOGS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(ORBITING_GENERATOR))" $(1) global \
		"$(abspath $(ORBITING_PROFILE))"

$(3): $(ORBITING_GENERATOR) $(ORBITING_PROFILE) $(ORBITING_CATALOGS) \
		| $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
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

# $(1): command-line projection name; $(2): Anthropocene product.
define ANTHROPOCENE_PROJECTION_RULES
generate-anthropocene-atlas-$(1): $(2)
$(2): $(ANTHROPOCENE_GENERATOR) $(ANTHROPOCENE_PROFILE) \
		$(ANTHROPOCENE_GEOJSON) $(ANTHROPOCENE_VERIFIER) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	$(ANTHROPOCENE_VERIFIER) "$(ANTHROPOCENE_PROFILE)" \
		"$(ANTHROPOCENE_GEOJSON)"
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(ANTHROPOCENE_GENERATOR))" $(1) \
		"$(abspath $(ANTHROPOCENE_PROFILE))" \
		"$(abspath $(ANTHROPOCENE_GEOJSON))"
endef

$(eval $(call ANTHROPOCENE_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/anthropocene-ck-44-22.svg))
$(eval $(call ANTHROPOCENE_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/anthropocene-authagraph-44-19.052559.svg))
$(eval $(call ANTHROPOCENE_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/anthropocene-dymaxion-44-20.78461.svg))
$(eval $(call ANTHROPOCENE_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/anthropocene-myriahedral-44-24.75.svg))
$(eval $(call ANTHROPOCENE_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/anthropocene-star-x-34-44.svg))
$(eval $(call ANTHROPOCENE_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/anthropocene-voronoi-44-22.916667.svg))

generate-anthropocene-atlas: $(ANTHROPOCENE_SVGS)
generate-anthropocene-atlas-projections: $(ANTHROPOCENE_SVGS)
generate-anthropocene-atlas-artifacts: $(ANTHROPOCENE_SVGS) \
	$(ANTHROPOCENE_PDFS) $(ANTHROPOCENE_PNGS)

# $(1): projection; $(2): 2025 SVG; $(3): 2026 SVG.
define ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES
$(2): $(ANTHROPOCENE_TEMPERATURE_GENERATOR) \
		$(ANTHROPOCENE_TEMPERATURE_PROFILE_2025) \
		$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2025) \
		$(ANTHROPOCENE_VERIFIER) $(NATURAL_EARTH_STAMP) \
		| $(GENERATED_SVG_DIR)
	$(ANTHROPOCENE_VERIFIER) "$(ANTHROPOCENE_TEMPERATURE_PROFILE_2025)" \
		"$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2025)"
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(ANTHROPOCENE_TEMPERATURE_GENERATOR))" $(1) \
		"$(abspath $(ANTHROPOCENE_TEMPERATURE_PROFILE_2025))" \
		"$(abspath $(ANTHROPOCENE_TEMPERATURE_GEOJSON_2025))"
$(3): $(ANTHROPOCENE_TEMPERATURE_GENERATOR) \
		$(ANTHROPOCENE_TEMPERATURE_PROFILE_2026) \
		$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2026) \
		$(ANTHROPOCENE_VERIFIER) $(NATURAL_EARTH_STAMP) \
		| $(GENERATED_SVG_DIR)
	$(ANTHROPOCENE_VERIFIER) "$(ANTHROPOCENE_TEMPERATURE_PROFILE_2026)" \
		"$(ANTHROPOCENE_TEMPERATURE_GEOJSON_2026)"
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(ANTHROPOCENE_TEMPERATURE_GENERATOR))" $(1) \
		"$(abspath $(ANTHROPOCENE_TEMPERATURE_PROFILE_2026))" \
		"$(abspath $(ANTHROPOCENE_TEMPERATURE_GEOJSON_2026))"
endef

$(eval $(call ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-ck-44-22.svg,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-ck-44-22.svg))
$(eval $(call ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-authagraph-44-19.052559.svg,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-authagraph-44-19.052559.svg))
$(eval $(call ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-dymaxion-44-20.78461.svg,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-dymaxion-44-20.78461.svg))
$(eval $(call ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-myriahedral-44-24.75.svg,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-myriahedral-44-24.75.svg))
$(eval $(call ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-star-x-34-44.svg,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-star-x-34-44.svg))
$(eval $(call ANTHROPOCENE_TEMPERATURE_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2025-voronoi-44-22.916667.svg,\
	$(GENERATED_SVG_DIR)/anthropocene-temperature-2026-voronoi-44-22.916667.svg))

# Stage 12 defaults generate the paired 2025 and 2026 Anthropocene passes.
generate-anthropocene-cahill-keyes: $(word 1,$(ANTHROPOCENE_TEMPERATURE_2025_SVGS)) $(word 1,$(ANTHROPOCENE_TEMPERATURE_2026_SVGS))
generate-anthropocene-authagraph: $(word 2,$(ANTHROPOCENE_TEMPERATURE_2025_SVGS)) $(word 2,$(ANTHROPOCENE_TEMPERATURE_2026_SVGS))
generate-anthropocene-dymaxion: $(word 3,$(ANTHROPOCENE_TEMPERATURE_2025_SVGS)) $(word 3,$(ANTHROPOCENE_TEMPERATURE_2026_SVGS))
generate-anthropocene-myriahedral: $(word 4,$(ANTHROPOCENE_TEMPERATURE_2025_SVGS)) $(word 4,$(ANTHROPOCENE_TEMPERATURE_2026_SVGS))
generate-anthropocene-star-x: $(word 5,$(ANTHROPOCENE_TEMPERATURE_2025_SVGS)) $(word 5,$(ANTHROPOCENE_TEMPERATURE_2026_SVGS))
generate-anthropocene-voronoi: $(word 6,$(ANTHROPOCENE_TEMPERATURE_2025_SVGS)) $(word 6,$(ANTHROPOCENE_TEMPERATURE_2026_SVGS))
generate-anthropocene: $(ANTHROPOCENE_TEMPERATURE_SVGS)
generate-anthropocene-projections: $(ANTHROPOCENE_TEMPERATURE_SVGS)
generate-anthropocene-artifacts: \
	$(ANTHROPOCENE_TEMPERATURE_SVGS) $(ANTHROPOCENE_TEMPERATURE_PDFS) \
	$(ANTHROPOCENE_TEMPERATURE_PNGS)

# These year targets are the implemented Stage 8b temperature-field theme.
# Additional observation, fire/air, and ocean themes can join each dependency
# list without changing the public target names.
generate-anthropocene-temperature-2025: $(ANTHROPOCENE_TEMPERATURE_2025_SVGS)
generate-anthropocene-temperature-2026: $(ANTHROPOCENE_TEMPERATURE_2026_SVGS)
generate-anthropocene-temperature-years: $(ANTHROPOCENE_TEMPERATURE_SVGS)
generate-anthropocene-temperature-artifacts: \
	$(ANTHROPOCENE_TEMPERATURE_SVGS) $(ANTHROPOCENE_TEMPERATURE_PDFS) \
	$(ANTHROPOCENE_TEMPERATURE_PNGS)
generate-anthropocene-2025: generate-anthropocene-temperature-2025
generate-anthropocene-2026: generate-anthropocene-temperature-2026
generate-anthropocene-years: generate-anthropocene-temperature-years
generate-anthropocene-year-artifacts: \
	generate-anthropocene-temperature-artifacts

# $(1): family; $(2): profile metric id; $(3): public metric alias;
# $(4): six projection SVGs in RESOURCE_OUTPUT_SUFFIXES order.
define RESOURCES_METRIC_RULES
generate-$(1)-$(3): $(addsuffix .gz,$(4))
generate-$(1)-$(3)-cahill-keyes: $(word 1,$(4)).gz
generate-$(1)-$(3)-authagraph: $(word 2,$(4)).gz
generate-$(1)-$(3)-dymaxion: $(word 3,$(4)).gz
generate-$(1)-$(3)-myriahedral: $(word 4,$(4)).gz
generate-$(1)-$(3)-star-x: $(word 5,$(4)).gz
generate-$(1)-$(3)-voronoi: $(word 6,$(4)).gz
$(word 1,$(4)): $(RESOURCES_GENERATOR) $(RESOURCES_PROFILE) \
		$(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) $(RESOURCES_REEFS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" "$(abspath $(RESOURCES_GENERATOR))" "$(1)" cahill-keyes "$(abspath $(RESOURCES_PROFILE))" "$(2)"
$(word 2,$(4)): $(RESOURCES_GENERATOR) $(RESOURCES_PROFILE) \
		$(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) $(RESOURCES_REEFS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" "$(abspath $(RESOURCES_GENERATOR))" "$(1)" authagraph "$(abspath $(RESOURCES_PROFILE))" "$(2)"
$(word 3,$(4)): $(RESOURCES_GENERATOR) $(RESOURCES_PROFILE) \
		$(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) $(RESOURCES_REEFS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" "$(abspath $(RESOURCES_GENERATOR))" "$(1)" dymaxion "$(abspath $(RESOURCES_PROFILE))" "$(2)"
$(word 4,$(4)): $(RESOURCES_GENERATOR) $(RESOURCES_PROFILE) \
		$(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) $(RESOURCES_REEFS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" "$(abspath $(RESOURCES_GENERATOR))" "$(1)" myriahedral "$(abspath $(RESOURCES_PROFILE))" "$(2)"
$(word 5,$(4)): $(RESOURCES_GENERATOR) $(RESOURCES_PROFILE) \
		$(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) $(RESOURCES_REEFS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" "$(abspath $(RESOURCES_GENERATOR))" "$(1)" star-x "$(abspath $(RESOURCES_PROFILE))" "$(2)"
$(word 6,$(4)): $(RESOURCES_GENERATOR) $(RESOURCES_PROFILE) \
		$(RESOURCES_VALUES) $(RESOURCES_COUNTRIES) $(RESOURCES_REEFS) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" "$(abspath $(RESOURCES_GENERATOR))" "$(1)" voronoi "$(abspath $(RESOURCES_PROFILE))" "$(2)"
endef

$(eval $(call RESOURCES_METRIC_RULES,resources-energy,solar-capacity,solar,$(RESOURCES_ENERGY_SOLAR_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-energy,wind-capacity,wind,$(RESOURCES_ENERGY_WIND_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-energy,nuclear-operating-capacity,nuclear,$(RESOURCES_ENERGY_NUCLEAR_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-energy,petroleum-refinery-throughput,petrochemical,$(RESOURCES_ENERGY_PETROCHEMICAL_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-food,food-production-index,production,$(RESOURCES_FOOD_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-fauna,fisheries-production,fisheries,$(RESOURCES_FAUNA_FISHERIES_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-fauna,coral-reef-threat,reefs,$(RESOURCES_FAUNA_REEFS_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-flora,forest-area-percent,forest,$(RESOURCES_FLORA_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-mineral,rare-earth-mine-production,rare-earth,$(RESOURCES_MINERAL_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-human,population-under-30,under-30,$(RESOURCES_HUMAN_UNDER_30_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-human,population-over-60,over-60,$(RESOURCES_HUMAN_OVER_60_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-human,upper-secondary-attainment,upper-secondary,$(RESOURCES_HUMAN_UPPER_SECONDARY_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-human,bachelors-attainment,bachelors,$(RESOURCES_HUMAN_BACHELORS_SVGS)))
$(eval $(call RESOURCES_METRIC_RULES,resources-human,resident-patent-applications-per-million,patents,$(RESOURCES_HUMAN_PATENTS_SVGS)))

# $(1): family; $(2): all released family SVGs.
define RESOURCES_FAMILY_AGGREGATES
generate-$(1)-cahill-keyes: $(addsuffix .gz,$(filter %-ck-44-22.svg,$(2)))
generate-$(1)-authagraph: $(addsuffix .gz,$(filter %-authagraph-44-19.052559.svg,$(2)))
generate-$(1)-dymaxion: $(addsuffix .gz,$(filter %-dymaxion-44-20.78461.svg,$(2)))
generate-$(1)-myriahedral: $(addsuffix .gz,$(filter %-myriahedral-44-24.75.svg,$(2)))
generate-$(1)-star-x: $(addsuffix .gz,$(filter %-star-x-34-44.svg,$(2)))
generate-$(1)-voronoi: $(addsuffix .gz,$(filter %-voronoi-44-22.916667.svg,$(2)))
endef

$(eval $(call RESOURCES_FAMILY_AGGREGATES,resources-energy,$(RESOURCES_ENERGY_SVGS)))
$(eval $(call RESOURCES_FAMILY_AGGREGATES,resources-food,$(RESOURCES_FOOD_SVGS)))
$(eval $(call RESOURCES_FAMILY_AGGREGATES,resources-fauna,$(RESOURCES_FAUNA_SVGS)))
$(eval $(call RESOURCES_FAMILY_AGGREGATES,resources-flora,$(RESOURCES_FLORA_SVGS)))
$(eval $(call RESOURCES_FAMILY_AGGREGATES,resources-mineral,$(RESOURCES_MINERAL_SVGS)))
$(eval $(call RESOURCES_FAMILY_AGGREGATES,resources-human,$(RESOURCES_HUMAN_SVGS)))

generate-resources-cahill-keyes: $(addsuffix .gz,$(filter %-ck-44-22.svg,$(RESOURCES_SVGS)))
generate-resources-authagraph: $(addsuffix .gz,$(filter %-authagraph-44-19.052559.svg,$(RESOURCES_SVGS)))
generate-resources-dymaxion: $(addsuffix .gz,$(filter %-dymaxion-44-20.78461.svg,$(RESOURCES_SVGS)))
generate-resources-myriahedral: $(addsuffix .gz,$(filter %-myriahedral-44-24.75.svg,$(RESOURCES_SVGS)))
generate-resources-star-x: $(addsuffix .gz,$(filter %-star-x-34-44.svg,$(RESOURCES_SVGS)))
generate-resources-voronoi: $(addsuffix .gz,$(filter %-voronoi-44-22.916667.svg,$(RESOURCES_SVGS)))

$(RESOURCES_SVG_ARCHIVES): $(GENERATED_SVG_DIR)/%.svg.gz: \
		$(GENERATED_SVG_DIR)/%.svg
	"$(GZIP)" -n -9 -c "$<" > "$@"

generate-resources-energy: $(addsuffix .gz,$(RESOURCES_ENERGY_SVGS))
generate-resources-food: $(addsuffix .gz,$(RESOURCES_FOOD_SVGS))
generate-resources-fauna: $(addsuffix .gz,$(RESOURCES_FAUNA_SVGS))
generate-resources-flora: $(addsuffix .gz,$(RESOURCES_FLORA_SVGS))
generate-resources-mineral: $(addsuffix .gz,$(RESOURCES_MINERAL_SVGS))
generate-resources-human: $(addsuffix .gz,$(RESOURCES_HUMAN_SVGS))
generate-resources: $(RESOURCES_SVG_ARCHIVES)
generate-resources-stage6b: generate-resources
generate-resources-stage12: generate-resources
generate-resources-projections: $(RESOURCES_SVG_ARCHIVES)
generate-resources-artifacts: $(RESOURCES_SVG_ARCHIVES) \
	$(RESOURCES_PDFS) $(RESOURCES_PNGS)

# $(1): command-line projection name; $(2): Network-swarm product.
define NETWORK_SWARM_PROJECTION_RULES
generate-network-swarm-$(1): $(2)
$(2): $(NETWORK_SWARM_GENERATOR) $(NETWORK_SWARM_PROFILE) \
		$(NETWORK_SWARM_GEOJSON) \
		$(NATURAL_EARTH_STAMP) | $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(NETWORK_SWARM_GENERATOR))" $(1) \
		"$(abspath $(NETWORK_SWARM_PROFILE))" "$(abspath $(NETWORK_SWARM_GEOJSON))"
endef

$(eval $(call NETWORK_SWARM_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/network-swarm-ck-44-22.svg))
$(eval $(call NETWORK_SWARM_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/network-swarm-authagraph-44-19.052559.svg))
$(eval $(call NETWORK_SWARM_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/network-swarm-dymaxion-44-20.78461.svg))
$(eval $(call NETWORK_SWARM_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/network-swarm-myriahedral-44-24.75.svg))
$(eval $(call NETWORK_SWARM_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/network-swarm-star-x-34-44.svg))
$(eval $(call NETWORK_SWARM_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/network-swarm-voronoi-44-22.916667.svg))

generate-network-swarm: $(NETWORK_SWARM_SVGS)
generate-network-swarm-projections: $(NETWORK_SWARM_SVGS)
generate-network-swarm-artifacts: $(NETWORK_SWARM_SVGS) \
	$(NETWORK_SWARM_PDFS) $(NETWORK_SWARM_PNGS)

# $(1): projection; $(2): ordinary cloud/CDN site atlas product.
define NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES
generate-network-infrastructure-$(1): $(2)
$(2): $(NETWORK_INFRASTRUCTURE_GENERATOR) \
		$(NETWORK_INFRASTRUCTURE_SITES_PROFILE) \
		$(NETWORK_INFRASTRUCTURE_CLOUD_MANIFEST) \
		$(NATURAL_EARTH_STAMP) \
		| check-network-infrastructure-sources $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(NETWORK_INFRASTRUCTURE_GENERATOR))" $(1) \
		"$(abspath $(NETWORK_INFRASTRUCTURE_SITES_PROFILE))" \
		"$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))"
endef

$(eval $(call NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-ck-44-22.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-authagraph-44-19.052559.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-dymaxion-44-20.78461.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-myriahedral-44-24.75.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-star-x-34-44.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_SITE_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/network-infrastructure-sites-voronoi-44-22.916667.svg))

generate-network-infrastructure: $(NETWORK_INFRASTRUCTURE_SITES_SVGS)
generate-network-infrastructure-sites: $(NETWORK_INFRASTRUCTURE_SITES_SVGS)
generate-network-infrastructure-projections: \
	$(NETWORK_INFRASTRUCTURE_SITES_SVGS)
generate-network-infrastructure-artifacts: \
	$(NETWORK_INFRASTRUCTURE_SITES_SVGS) \
	$(NETWORK_INFRASTRUCTURE_SITES_PDFS) \
	$(NETWORK_INFRASTRUCTURE_SITES_PNGS)

# Explicit CC BY-NC-SA 3.0 opt-in. These products are not part of make all.
define NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES
generate-network-infrastructure-topology-$(1): $(2)
$(2): $(NETWORK_INFRASTRUCTURE_GENERATOR) \
		$(NETWORK_INFRASTRUCTURE_TOPOLOGY_PROFILE) \
		$(NETWORK_INFRASTRUCTURE_CLOUD_MANIFEST) \
		$(SUBMARINE_CABLE_ROUTES) $(SUBMARINE_CABLE_LANDINGS) \
		$(INTERNET_EXCHANGE_BUILDINGS) $(NATURAL_EARTH_STAMP) \
		| check-network-infrastructure-topology-sources $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
		"$(abspath $(NETWORK_INFRASTRUCTURE_GENERATOR))" $(1) \
		"$(abspath $(NETWORK_INFRASTRUCTURE_TOPOLOGY_PROFILE))" \
		"$(abspath $(NETWORK_INFRASTRUCTURE_CLOUD_SOURCE))" \
		"$(abspath $(SUBMARINE_CABLE_SOURCE))" \
		"$(abspath $(INTERNET_EXCHANGE_SOURCE))"
endef

$(eval $(call NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES,cahill-keyes,\
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-ck-44-22.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES,authagraph,\
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-authagraph-44-19.052559.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES,dymaxion,\
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-dymaxion-44-20.78461.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES,myriahedral,\
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-myriahedral-44-24.75.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES,star-x,\
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-star-x-34-44.svg))
$(eval $(call NETWORK_INFRASTRUCTURE_TOPOLOGY_PROJECTION_RULES,voronoi,\
	$(GENERATED_SVG_DIR)/network-infrastructure-topology-voronoi-44-22.916667.svg))

generate-network-infrastructure-topology: \
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_SVGS)
generate-network-infrastructure-topology-projections: \
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_SVGS)
generate-network-infrastructure-topology-artifacts: \
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_SVGS) \
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_PDFS) \
	$(NETWORK_INFRASTRUCTURE_TOPOLOGY_PNGS)

# $(1): command-line projection name; $(2): Bathymetry Roulette product.
define BATHYMETRY_ROULETTE_PROJECTION_RULES
generate-bathymetry-roulette-$(1): $(2)
$(2): $(BATHYMETRY_ROULETTE_GENERATOR) $(NATURAL_EARTH_STAMP) \
		| $(GENERATED_SVG_DIR)
	cd "$(GENERATED_SVG_DIR)" && \
		NATURAL_EARTH_DIR="$(abspath $(NATURAL_EARTH_DIR))" \
		CARTOFREAKO_LABEL_FONT="$(LABEL_FONT)" \
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

define EXPORT_PDF
	@tmp="$@.tmp.$$$$.pdf"; \
	rm -f "$$tmp"; \
	if "$(INKSCAPE)" $(INKSCAPE_INSTANCE_ARGS) \
		--export-area-page \
		--export-filename="$$tmp" "$<" && \
		test -s "$$tmp"; then \
		mv -f "$$tmp" "$@"; \
	else \
		status=$$?; \
		rm -f "$$tmp"; \
		exit "$$status"; \
	fi
endef

define EXPORT_PNG
	@tmp="$@.tmp.$$$$.png"; \
	rm -f "$$tmp"; \
	if "$(INKSCAPE)" $(INKSCAPE_INSTANCE_ARGS) \
		--export-area-page $(PNG_EXPORT_BACKGROUND) \
		$(1)=$(PNG_LONG_SIDE) \
		--export-filename="$$tmp" "$<" && \
		test -s "$$tmp"; then \
		mv -f "$$tmp" "$@"; \
	else \
		status=$$?; \
		rm -f "$$tmp"; \
		exit "$$status"; \
	fi
endef

$(GENERATED_PDFS) $(NETWORK_INFRASTRUCTURE_TOPOLOGY_PDFS) \
		$(CLOUD_ATMOSPHERE_PDFS): \
		$(GENERATED_PDF_DIR)/%.pdf: \
		$(GENERATED_SVG_DIR)/%.svg | $(GENERATED_PDF_DIR)
	$(EXPORT_PDF)

$(LANDSCAPE_PNGS) $(NETWORK_INFRASTRUCTURE_TOPOLOGY_LANDSCAPE_PNGS): \
		$(GENERATED_PNG_DIR)/%.png: \
		$(GENERATED_SVG_DIR)/%.svg Makefile | $(GENERATED_PNG_DIR)
	$(call EXPORT_PNG,--export-width)

$(PORTRAIT_PNGS): $(GENERATED_PNG_DIR)/%.png: \
		$(GENERATED_SVG_DIR)/%.svg Makefile | $(GENERATED_PNG_DIR)
	$(call EXPORT_PNG,--export-height)

# Recursive release targets pass PNG_LONG_SIDE on the command line. Keep the
# snapshot contract at 480 pixels even when the full-size export setting is
# inherited by assets-single or assets-resilient.
$(CK_SNAPSHOT_THUMBNAILS): override PNG_LONG_SIDE=$(CK_SNAPSHOT_WIDTH)
$(CK_SNAPSHOT_THUMBNAILS): $(CK_SNAPSHOT_THUMBNAIL_DIR)/%.png: \
		$(GENERATED_SVG_DIR)/%.svg Makefile | $(CK_SNAPSHOT_THUMBNAIL_DIR)
	$(call EXPORT_PNG,--export-width)

generate-snapshot-ck: $(CK_SNAPSHOT_THUMBNAILS)

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

# Run the complete generated-asset graph through a single-job recursive Make.
# An explicit job count here overrides a parallel outer invocation such as
# `make -j32 assets-single` while preserving ordinary variable overrides.
assets-single:
	+$(MAKE) --no-print-directory --jobs=1 all

# Finish as much of the graph as possible with moderate parallelism, then
# retry only missing or failed outputs with a single active job.
assets-resilient:
	+status=0; \
	$(MAKE) --no-print-directory \
		--keep-going \
		--jobs=$(ASSET_JOBS) \
		--output-sync=target \
		PNG_LONG_SIDE=$(PNG_LONG_SIDE) \
		all || status=$$?; \
	case "$$status" in \
	0|2) ;; \
	*) exit "$$status" ;; \
	esac
	+$(MAKE) --no-print-directory \
		--jobs=1 \
		--output-sync=target \
		PNG_LONG_SIDE=$(PNG_LONG_SIDE) \
		all

clean-failed-generated:
	@if test -d "$(GENERATED_DIR)"; then \
		find "$(GENERATED_DIR)" -type f \
			\( -name '*.png' -o -name '*.pdf' \) \
			-size 0 -print -delete; \
		find "$(GENERATED_DIR)" -type f \
			\( -name '*.tmp.*.png' -o -name '*.tmp.*.pdf' \) \
			-print -delete; \
	fi

clean:
	$(RM) $(TEST_BINARIES) $(GENERATOR_BINARIES)
	$(RM) $(SGP4_OBJECT)
	$(RM) $(GENERATED_SVGS) $(RESOURCES_SVG_ARCHIVES) \
		$(CK_WEB_MODULE) $(CK_WEB_WASM) \
		$(MYRIA_WEB_MODULE) $(MYRIA_WEB_WASM) \
		$(PROJECTIONS_WEB_MODULE) $(PROJECTIONS_WEB_WASM)
	$(RM) -r "$(GENERATED_DIR)/svg" "$(GENERATED_DIR)/png" \
		"$(GENERATED_DIR)/pdf" "$(CK_SNAPSHOT_THUMBNAIL_DIR)"
	$(RM) -r "$(DOXYGEN_OUTPUT_DIR)"

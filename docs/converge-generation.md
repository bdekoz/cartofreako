Stage 4.1 development:

Evaluate feasibility and propose a plan for a new generate pass for "space/astronomy" detailing natually-occuring stars, suns, comets, asteroids, planets, cosmic phenomena, etc, visible with instrumentation in the night sky located in
src.generate/generate-astro.cc

Assume timestamp of generative process for calculation of any astronomical property. Ask for any other info necessary to compute.

Use data sources
- https://planetary.data.nasa.gov/find-data
- https://earth.jaxa.jp/en/data/index.html
- https://www.nssdc.ac.cn/nssdc_en/html/index.html

Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.


---------

Stage 4.2 development:

Evaluate feasibility and propose a plan for a new generate pass for "orbiting" detiling superconstellations, megaconstellations, and human-made space objects, located in
src.generate/generate-orbiting.cc

Suggest some more names for "orbiting" that capture the essential nature of this workflow

Assume timestamp of generative process for calculation of any astronomical property, and location of make invocation. Save inputs to a JSON profile, same as previous work for atro.

Use NASA data sources
https://planetary.data.nasa.gov/find-data

And
https://en.wikipedia.org/wiki/Satellite_internet_constellation
https://en.wikipedia.org/wiki/Satellite_constellation
https://alpha60.co/2022/05/27/starlink-infrastructure/


Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.

After confirmation, assume authorized and proceed and finish work without prompting.

---------

Stage 4.3 development:

extend existing src.wasm/cahill-keys-web.cc to the myriahedral projection and  src.wasm/cahill-myriahedral.cc

Use just the "land" and "ocean" layers when computing myriahedral, not all possible layers

Document this option


---------

Stage 4.4 development:

Evaluate feasibility and propose a plan for a new generate pass for "network" detiling GeoJSON swarm features properties.downloaders fields in
src.generate/generate-network.cc

Prior art:
augment_swarm_features_geojson
alpha60/src/a60-carto-geo.cc

Data source should be variable, but start with cumulative GeoJSON form
https://github.com/alpha60-devops/alpha60-results-animation/blob/main/data/altered-carbon-resleeved-cumulative.geojson

Visual sources prior art for network properties layering style:

- Metropolitan World Atlas, Arjen van Susteren, 010 Publishers, Rotterdam 2005
- Lucille Tenazas "MNL to NY" graphic as from the bottom center image here: https://2023.agi-open.com/speakers/lucille-tenazas

Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.
After confirmation, assume authorized and proceed and finish work without prompting.

---------

Stage 4.5 development:

Evaluate feasibility and propose a plan for a new generate pass for "art-agua-rolette" detailing the bathymetry layers, but instead of varying colors use different routlette curves as lines or fills as per the izzi/examples/curves-roulette.cc file that explores the parameter space.

Shallow bathymetry layers get less point variation styles
Deeper bathymetry layers get more point and complex variation styles

Output file:
src.generate/generate-art-agua-roulette.cc

Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.
After confirmation, assume authorized and proceed and finish work without prompting.

---

Stage 4.1a development:

Evaluate feasibility and propose a plan for a new generate pass for "cloud/atmosphere" detailing cloud and atmospheric conditions located in
src.generate/generate-cloud-atmosphere.cc
https://aspace.lib.vt.edu/repositories/2/archival_objects/197582
Assume timestamp of generative process for calculation of any astronomical property. Ask for any other info necessary to compute.

Use data sources
- https://earth.jaxa.jp/en/data/index.html

Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.
After confirmation, assume authorized and proceed and finish work without prompting.

---------

solar/high-energy

atmosphere/cloud

small-body/mission


---

Stage 6 development:

Evaluate feasibility and propose a plan for a new generate pass for "world-game" detailing  all of Buckminister Fuller's World Game resources:

from
Inventory of World Resources, Human Trends, and Needs

at
https://www.bfi.org/about-fuller/big-ideas/world-game/

Some archival records are:
https://aspace.lib.vt.edu/repositories/2/archival_objects/197582

And Stanford has the Buckminister Fuller Archive in Special Collections:
https://archives.stanford.edu/catalog/m1378

University of California resources:
https://oac.cdlib.org/findaid/ark:/13030/tf109n9832/

Research, evaulate, and suggest plan before continuing.
Then detail plan and way for confirmation before implementing.
After confirmation, assume authorized and proceed and finish work without prompting.

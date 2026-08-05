import fs from 'node:fs/promises';

import createCartofreakoModule from './cartofreako-cahill-myriahedral.mjs';

function require(condition, message) {
    if (!condition) throw new Error(message);
}

const module = await createCartofreakoModule();
const landUrl = new URL(
    './cartofreako-cahill-keyes-land-110m.geojson', import.meta.url
);
const land = JSON.parse(await fs.readFile(landUrl, 'utf8'));
require(land.type === 'FeatureCollection', 'land input is not GeoJSON');
require(land.features.length === 142, 'unexpected land feature count');

const projection = new module.MyriahedralProjection(4480, 2520);
require(projection.width() === 4480, 'incorrect WASM projection width');
require(projection.height() === 2520, 'incorrect WASM projection height');
require(
    module.implementationName()
        === 'cartofreako C++20 Myriahedral/WebAssembly',
    'incorrect implementation identity'
);

const newYork = projection.project(40.7128, -74.006);
require(
    Math.abs(newYork.x - 1672.3958573173111) < 1e-9
        && Math.abs(newYork.y - 673.85401928773956) < 1e-9,
    `incorrect projected point: ${JSON.stringify(newYork)}`
);

const svg = projection.generateBaseMapSvg(land);
require(svg.startsWith('<svg'), 'generator did not return SVG');
require(
    svg.includes('viewBox="0 0 4480.000 2520.000"'),
    'generated SVG has the wrong frame'
);
require(
    svg.includes('data-generator="cartofreako-cahill-myriahedral-wasm"'),
    'generated SVG does not identify its WASM implementation'
);
require(
    svg.includes('data-layers="ocean land"'),
    'generated SVG does not declare its layer contract'
);
require(
    (svg.match(/<g id=/g) || []).length === 2
        && svg.includes('<g id="ocean">')
        && svg.includes('<g id="land">'),
    'generated SVG does not contain exactly the ocean and land groups'
);
for (const excludedLayer of [
    'graticules', 'bathymetry', 'rivers', 'lakes', 'ice', 'minor-islands',
    'glaciated-areas', 'antarctic-ice-shelves', 'playas', 'reefs',
    'coastline'
]) {
    require(
        !svg.includes(`id="${excludedLayer}`),
        `generated SVG unexpectedly contains ${excludedLayer}`
    );
}
require(!/(?:nan|inf)/i.test(svg), 'generated SVG has non-finite values');

const oceanPath = svg.match(/<path id="myriahedral-ocean" d="([^"]+)"/);
require(oceanPath, 'generated SVG has no ocean face path');
require(
    (oceanPath[1].match(/Z/g) || []).length === 5120,
    'ocean layer does not contain all 5,120 terminal faces'
);

const landPath = svg.match(/<path id="natural-earth-land" d="([^"]+)"/);
require(landPath, 'generated SVG has no Natural Earth land path');
const landPieceCount = (landPath[1].match(/Z/g) || []).length;
require(
    landPieceCount > 6000 && landPieceCount < 8000,
    `unexpected face-clipped land piece count: ${landPieceCount}`
);

let firstLandPoint = null;
let previousLandPoint = null;
let maximumLandSegment = 0;
const pathPointPattern
    = /([ML])(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)|Z/g;
for (const match of landPath[1].matchAll(pathPointPattern)) {
    if (match[0] === 'Z') {
        if (firstLandPoint && previousLandPoint) {
            maximumLandSegment = Math.max(
                maximumLandSegment,
                Math.hypot(
                    firstLandPoint.x - previousLandPoint.x,
                    firstLandPoint.y - previousLandPoint.y
                )
            );
        }
        firstLandPoint = null;
        previousLandPoint = null;
        continue;
    }
    const point = {x: Number(match[2]), y: Number(match[3])};
    if (match[1] === 'M') {
        firstLandPoint = point;
    } else if (previousLandPoint) {
        maximumLandSegment = Math.max(
            maximumLandSegment,
            Math.hypot(
                point.x - previousLandPoint.x,
                point.y - previousLandPoint.y
            )
        );
    }
    previousLandPoint = point;
}
require(
    maximumLandSegment < projection.width() / 32,
    `generated land contains an unfolded-face chord: ${maximumLandSegment}`
);

const smallProjection = new module.MyriahedralProjection(44, 24.75);
const smallNewYork = smallProjection.project(40.7128, -74.006);
require(
    Math.abs(smallNewYork.x - newYork.x * 44 / 4480) < 1e-11
        && Math.abs(smallNewYork.y - newYork.y * 24.75 / 2520) < 1e-11,
    'variable 16:9 frame does not scale the projection uniformly'
);

let rejectedInvalidFrame = false;
try {
    const invalidProjection = new module.MyriahedralProjection(44, 25);
    invalidProjection.delete();
} catch (error) {
    rejectedInvalidFrame = true;
}
require(rejectedInvalidFrame, 'WASM projection accepted a non-16:9 frame');

for (const [latitude, longitude] of [
    [91, 0], [-91, 0], [0, 181], [0, -181], [Number.NaN, 0], [0, Number.NaN]
]) {
    let rejectedInvalidCoordinate = false;
    try {
        projection.project(latitude, longitude);
    } catch (error) {
        rejectedInvalidCoordinate = true;
    }
    require(
        rejectedInvalidCoordinate,
        `WASM projection accepted invalid coordinates ${latitude},${longitude}`
    );
}

console.log(JSON.stringify({
    implementation: module.implementationName(),
    width: projection.width(),
    height: projection.height(),
    layers: ['ocean', 'land'],
    landFeatures: land.features.length,
    landPieces: landPieceCount,
    svgBytes: new TextEncoder().encode(svg).length,
    maximumLandSegment,
    newYork
}));

smallProjection.delete();
projection.delete();

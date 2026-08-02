import fs from 'node:fs/promises';

import createCartofreakoModule from './cartofreako-cahill-keyes.mjs';

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

const projection = new module.CahillKeyesProjection(4224, 2112);
require(projection.width() === 4224, 'incorrect WASM projection width');
require(projection.height() === 2112, 'incorrect WASM projection height');
require(
    module.implementationName()
        === 'cartofreako C++20 Cahill-Keyes/WebAssembly',
    'incorrect implementation identity'
);

const sanFrancisco = projection.project(37.7749, -122.4194);
require(
    Math.abs(sanFrancisco.x - 965.7937289075612) < 1e-9
        && Math.abs(sanFrancisco.y - 816.3795929279505) < 1e-9,
    `incorrect projected point: ${JSON.stringify(sanFrancisco)}`
);

const svg = projection.generateBaseMapSvg(land);
require(svg.startsWith('<svg'), 'generator did not return SVG');
require(
    svg.includes('viewBox="0 0 4224.000 2112.000"'),
    'generated SVG has the wrong frame'
);
require(
    svg.includes('data-generator="cartofreako-cahill-keyes-wasm"'),
    'generated SVG does not identify its WASM implementation'
);
require(
    svg.includes('id="natural-earth-land"'),
    'generated SVG has no projected land layer'
);
require(
    (svg.match(/data-latitude=/g) || []).length === 17,
    'generated SVG does not have seventeen latitude paths'
);
require(
    (svg.match(/data-longitude=/g) || []).length === 36,
    'generated SVG does not have thirty-six longitude paths'
);
require(!/(?:nan|inf)/i.test(svg), 'generated SVG has non-finite values');

const smallProjection = new module.CahillKeyesProjection(44, 22);
const smallSanFrancisco = smallProjection.project(37.7749, -122.4194);
require(
    Math.abs(smallSanFrancisco.x - sanFrancisco.x * 44 / 4224) < 1e-11
        && Math.abs(smallSanFrancisco.y - sanFrancisco.y * 22 / 2112)
            < 1e-11,
    'variable 2:1 frame does not scale the projection uniformly'
);

let rejectedInvalidFrame = false;
try {
    const invalidProjection = new module.CahillKeyesProjection(44, 23);
    invalidProjection.delete();
} catch (error) {
    rejectedInvalidFrame = true;
}
require(rejectedInvalidFrame, 'WASM projection accepted a non-2:1 frame');

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
    landFeatures: land.features.length,
    svgBytes: new TextEncoder().encode(svg).length,
    sanFrancisco
}));

smallProjection.delete();
projection.delete();

#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';
import {commandBufferToSvgPaths} from '../src.wasm/cartofreako-svg.mjs';

const workDirectory = path.resolve(process.argv[2] ?? '');
if (!process.argv[2]) {
    throw new Error('usage: render-marshall-islands-speculations-v01.mjs WORK-DIRECTORY');
}

const rmi = Object.freeze({
    longitude: 171.2,
    latitude: 7.1,
    label: 'Republic of the Marshall Islands context point'
});
const regionalBounds = Object.freeze([160, 4, 176, 15]);

function escapeXml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&apos;');
}

function number(value, precision = 2) {
    return Number(value.toFixed(precision)).toString();
}

async function readJson(name) {
    return JSON.parse(await fs.readFile(path.join(workDirectory, name), 'utf8'));
}

function mergeFeatureCollections(...collections) {
    return {
        type: 'FeatureCollection',
        features: collections.flatMap((collection) => collection.features ?? [])
    };
}

function joinedPaths(buffer, precision = 2) {
    return [...commandBufferToSvgPaths(buffer, {precision}).values()].join('');
}

function boundsOf(buffers, point) {
    const coordinates = buffers.flatMap((buffer) => [...buffer.coordinates]);
    coordinates.push(point.x, point.y);
    const xs = [];
    const ys = [];
    for (let index = 0; index < coordinates.length; index += 2) {
        const x = coordinates[index];
        const y = coordinates[index + 1];
        if (Number.isFinite(x) && Number.isFinite(y)) {
            xs.push(x);
            ys.push(y);
        }
    }
    if (xs.length === 0) throw new Error('regional preclip produced no finite geometry');
    let minimumX = Math.min(...xs);
    let maximumX = Math.max(...xs);
    let minimumY = Math.min(...ys);
    let maximumY = Math.max(...ys);
    const padding = Math.max(maximumX - minimumX, maximumY - minimumY) * 0.08;
    minimumX -= padding;
    maximumX += padding;
    minimumY -= padding;
    maximumY += padding;
    return {
        x: minimumX,
        y: minimumY,
        width: maximumX - minimumX,
        height: maximumY - minimumY
    };
}

function graticule(bounds) {
    const [west, south, east, north] = bounds;
    const features = [];
    for (let longitude = west; longitude <= east; longitude += 4) {
        const coordinates = [];
        for (let latitude = south; latitude <= north; latitude += 0.25) {
            coordinates.push([longitude, latitude]);
        }
        features.push({type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates}});
    }
    for (let latitude = south; latitude <= north; latitude += 2) {
        const coordinates = [];
        for (let longitude = west; longitude <= east; longitude += 0.25) {
            coordinates.push([longitude, latitude]);
        }
        features.push({type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates}});
    }
    return {type: 'FeatureCollection', features};
}

function regionalSvg(projection, land, reefs) {
    const slice = {
        id: 'rmi-regional-v01',
        kind: 'geographic-preclip',
        bounds: regionalBounds
    };
    const options = {slice, tolerancePx: 0.15};
    const projectedLand = projection.projectGeometry(land, options);
    const projectedReefs = projection.projectGeometry(reefs, options);
    const projectedGrid = projection.projectGeometry(graticule(regionalBounds), options);
    const marker = projection.forward([rmi.longitude, rmi.latitude]);
    const view = boundsOf([projectedLand, projectedReefs, projectedGrid], marker);
    const strokeWidth = Math.max(view.width, view.height) / 650;
    const markerRadius = Math.max(view.width, view.height) / 40;
    const title = `RMI regional geographic preclip / ${projection.metadata().title}`;
    return `<svg xmlns="http://www.w3.org/2000/svg" `
        + `viewBox="${number(view.x)} ${number(view.y)} ${number(view.width)} ${number(view.height)}" `
        + `data-experiment="marshall-islands-speculations-v01" `
        + `data-projection="${escapeXml(projection.id)}" `
        + `data-slice-kind="geographic-preclip" data-bounds="160,4,176,15">`
        + `<title>${escapeXml(title)}</title>`
        + '<desc>Speculative WGS 84 source preclip using Natural Earth 1:10m land, minor islands, and reef lines. Not an atoll-scale analytical map.</desc>'
        + `<rect x="${number(view.x)}" y="${number(view.y)}" width="${number(view.width)}" height="${number(view.height)}" fill="#dcecf2"/>`
        + `<path d="${joinedPaths(projectedGrid)}" fill="none" stroke="#91a9b1" stroke-width="${number(strokeWidth * 0.55)}" opacity="0.7"/>`
        + `<path d="${joinedPaths(projectedLand)}" fill="#e8e2c8" fill-rule="evenodd" stroke="#4a5559" stroke-width="${number(strokeWidth)}"/>`
        + `<path d="${joinedPaths(projectedReefs)}" fill="none" stroke="#6b1e7b" stroke-width="${number(strokeWidth * 2.3)}"/>`
        + `<circle cx="${number(marker.x)}" cy="${number(marker.y)}" r="${number(markerRadius)}" fill="#111820" stroke="#fff45b" stroke-width="${number(strokeWidth * 3)}"/>`
        + '</svg>';
}

function walkGeometry(geometry, visitor) {
    if (!geometry) return;
    switch (geometry.type) {
    case 'Point': visitor([geometry.coordinates], false); break;
    case 'MultiPoint': visitor(geometry.coordinates, false); break;
    case 'LineString': visitor(geometry.coordinates, false); break;
    case 'MultiLineString': geometry.coordinates.forEach((line) => visitor(line, false)); break;
    case 'Polygon': geometry.coordinates.forEach((ring) => visitor(ring, true)); break;
    case 'MultiPolygon':
        geometry.coordinates.forEach((polygon) => polygon.forEach((ring) => visitor(ring, true)));
        break;
    case 'GeometryCollection': geometry.geometries.forEach((child) => walkGeometry(child, visitor)); break;
    default: throw new Error(`unsupported local geometry ${geometry.type}`);
    }
}

function localPaths(collection) {
    const paths = [];
    for (const feature of collection.features ?? []) {
        walkGeometry(feature.geometry, (coordinates, close) => {
            if (coordinates.length === 0) return;
            const points = coordinates.map(([x, y], index) =>
                `${index === 0 ? 'M' : 'L'}${number(x, 1)} ${number(-y, 1)}`
            ).join('');
            paths.push(points + (close ? 'Z' : ''));
        });
    }
    return paths.join('');
}

function localAeqdSvg(land, reefs) {
    const view = {x: -525000, y: -525000, width: 1050000, height: 1050000};
    const rings = [100000, 250000, 500000].map((radius) =>
        `<circle cx="0" cy="0" r="${radius}" fill="none" stroke="#77939c" stroke-width="4500" stroke-dasharray="12000 10000"/>`
    ).join('');
    return `<svg xmlns="http://www.w3.org/2000/svg" `
        + `viewBox="${view.x} ${view.y} ${view.width} ${view.height}" `
        + 'data-experiment="marshall-islands-speculations-v01" '
        + 'data-projection="atoll-centered-azimuthal-equidistant" '
        + 'data-center="171.3803,7.0897" data-datum="WGS84">'
        + '<title>Majuro-centered azimuthal equidistant speculation</title>'
        + '<desc>Natural Earth 1:10m context with true radial-distance rings from the registered Majuro center. Not suitable for hazard, navigation, cadastral, or engineering decisions.</desc>'
        + `<rect x="${view.x}" y="${view.y}" width="${view.width}" height="${view.height}" fill="#dcecf2"/>`
        + rings
        + '<path d="M-525000 0H525000M0 -525000V525000" fill="none" stroke="#77939c" stroke-width="3500" opacity="0.65"/>'
        + `<path d="${localPaths(land)}" fill="#e8e2c8" fill-rule="evenodd" stroke="#4a5559" stroke-width="3500"/>`
        + `<path d="${localPaths(reefs)}" fill="none" stroke="#6b1e7b" stroke-width="7000"/>`
        + '<circle cx="0" cy="0" r="13000" fill="#111820" stroke="#fff45b" stroke-width="6000"/>'
        + '<text x="25000" y="-25000" font-family="Atkinson Hyperlegible, sans-serif" font-size="31000" fill="#111820">Majuro center</text>'
        + '<text x="-500000" y="500000" font-family="Atkinson Hyperlegible, sans-serif" font-size="25000" fill="#111820">rings: 100 / 250 / 500 km</text>'
        + '</svg>';
}

const regionLand = mergeFeatureCollections(
    await readJson('region-land.geojson'),
    await readJson('region-islands.geojson')
);
const regionReefs = await readJson('region-reefs.geojson');
const localLand = mergeFeatureCollections(
    await readJson('local-land.geojson'),
    await readJson('local-islands.geojson')
);
const localReefs = await readJson('local-reefs.geojson');

const runtime = await createCartofreako();
const coordinates = {
    schema: 'cartofreako-marshall-islands-speculation-coordinates-v1',
    rmi,
    regionalBounds,
    points: {}
};

for (const [id, width] of [['cahill-keyes', 3840], ['dymaxion', 3840], ['star-x', 2967]]) {
    const projection = runtime.createProjection({id, width});
    const point = projection.forward([rmi.longitude, rmi.latitude]);
    coordinates.points[id] = {
        x: Math.round(point.x),
        y: Math.round(point.y),
        nativeCell: point.nativeCell,
        component: point.component,
        frame: {width: Math.round(projection.width), height: Math.round(projection.height)}
    };
    if (id === 'cahill-keyes') {
        const slice = projection.slice('ck-octant-1');
        const exportWidth = 900;
        const exportHeight = Math.round(exportWidth * slice.sourceView.height / slice.sourceView.width);
        coordinates.points[id].octant1 = {
            sourceView: slice.sourceView,
            export: {
                width: exportWidth,
                height: exportHeight,
                x: Math.round((point.x - slice.sourceView.x) / slice.sourceView.width * exportWidth),
                y: Math.round((point.y - slice.sourceView.y) / slice.sourceView.height * exportHeight)
            }
        };
    }
    if (id === 'cahill-keyes' || id === 'dymaxion') {
        await fs.writeFile(
            path.join(workDirectory, `regional-${id}.svg`),
            regionalSvg(projection, regionLand, regionReefs),
            'utf8'
        );
    }
    projection.dispose();
}

await fs.writeFile(
    path.join(workDirectory, 'local-majuro-aeqd.svg'),
    localAeqdSvg(localLand, localReefs),
    'utf8'
);
await fs.writeFile(
    path.join(workDirectory, 'coordinates.json'),
    JSON.stringify(coordinates, null, 2) + '\n',
    'utf8'
);

#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';
import {commandBufferToSvgPaths} from '../src.wasm/cartofreako-svg.mjs';
import {
    distortionAt,
    forwardDegrees,
    mercatorForwardRaw,
    radiansPerDegree,
    rawXMaximum,
    rawYMaximum,
    relativeLongitudeRadians
} from './equal-earth.mjs';

const repositoryRoot = path.resolve(process.argv[2] ?? '');
const outputDirectory = path.resolve(process.argv[3] ?? '');
if (!process.argv[2] || !process.argv[3]) {
    throw new Error('usage: render-equal-earth-positioning-v01.mjs REPOSITORY-ROOT OUTPUT-DIRECTORY');
}

const width = 2560;
const height = 1440;
const africaBounds = [-25, -40, 60, 75];
const colors = Object.freeze({
    page: '#f2f2ee',
    panel: '#e5e8e7',
    water: '#d9e8ed',
    land: '#c7ceca',
    ink: '#171b1e',
    subdued: '#56646a',
    grid: '#7f949b',
    accent: '#7c2d85',
    seam: '#ce6d13',
    yellow: '#fff45b'
});

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

function walkGeometry(geometry, visitor) {
    if (!geometry) return;
    switch (geometry.type) {
    case 'Point': visitor([geometry.coordinates], false); break;
    case 'MultiPoint': visitor(geometry.coordinates, false); break;
    case 'LineString': visitor(geometry.coordinates, false); break;
    case 'MultiLineString': geometry.coordinates.forEach(line => visitor(line, false)); break;
    case 'Polygon': geometry.coordinates.forEach(ring => visitor(ring, true)); break;
    case 'MultiPolygon':
        geometry.coordinates.forEach(polygon => polygon.forEach(ring => visitor(ring, true)));
        break;
    case 'GeometryCollection': geometry.geometries.forEach(child => walkGeometry(child, visitor)); break;
    default: throw new Error(`unsupported geometry type ${geometry.type}`);
    }
}

function geometryLines(collection) {
    const result = [];
    for (const feature of collection.features ?? []) {
        walkGeometry(feature.geometry, (coordinates, close) => result.push({coordinates, close}));
    }
    return result;
}

function graticule(bounds, longitudeStep = 30, latitudeStep = 15,
    samplingStep = 2.5) {
    const [west, south, east, north] = bounds;
    const features = [];
    const longitudeStart = Math.ceil(west / longitudeStep) * longitudeStep;
    const latitudeStart = Math.ceil(south / latitudeStep) * latitudeStep;
    for (let longitude = longitudeStart; longitude <= east; longitude += longitudeStep) {
        const coordinates = [];
        for (let latitude = south; latitude <= north; latitude += samplingStep) {
            coordinates.push([longitude, latitude]);
        }
        features.push({type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates}});
    }
    for (let latitude = latitudeStart; latitude <= north; latitude += latitudeStep) {
        const coordinates = [];
        for (let longitude = west; longitude <= east; longitude += samplingStep) {
            coordinates.push([longitude, latitude]);
        }
        features.push({type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates}});
    }
    return {type: 'FeatureCollection', features};
}

function sourceInside([longitude, latitude], bounds) {
    return longitude >= bounds[0] - 1e-9 && longitude <= bounds[2] + 1e-9
        && latitude >= bounds[1] - 1e-9 && latitude <= bounds[3] + 1e-9;
}

function clippedPoints(collection, bounds) {
    const features = [];
    for (const feature of collection.features ?? []) {
        if (feature.geometry?.type === 'Point'
            && sourceInside(feature.geometry.coordinates, bounds)) features.push(feature);
    }
    return {type: 'FeatureCollection', features};
}

function customProjector(kind, centralMeridianDegrees = 0) {
    if (kind === 'equal-earth') {
        return coordinate => forwardDegrees(coordinate, centralMeridianDegrees);
    }
    if (kind === 'mercator') {
        return ([longitude, latitude]) => Math.abs(latitude) > 85.0511287798066
            ? [Number.NaN, Number.NaN]
            : mercatorForwardRaw(
                relativeLongitudeRadians(longitude, centralMeridianDegrees),
                latitude * radiansPerDegree
            );
    }
    throw new Error(`unknown custom projection ${kind}`);
}

function projectionExtent(kind) {
    return kind === 'equal-earth'
        ? [-rawXMaximum, -rawYMaximum, rawXMaximum, rawYMaximum]
        : [-Math.PI, -Math.PI, Math.PI, Math.PI];
}

function projectedBounds(collections, project) {
    const xs = [];
    const ys = [];
    for (const collection of collections) {
        for (const line of geometryLines(collection)) {
            for (const coordinate of line.coordinates) {
                const [x, y] = project(coordinate);
                if (Number.isFinite(x) && Number.isFinite(y)) {
                    xs.push(x);
                    ys.push(y);
                }
            }
        }
    }
    if (!xs.length) throw new Error('projection bounds received no finite points');
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

function fitTransform(extent, box, padding = 34) {
    const [minimumX, minimumY, maximumX, maximumY] = extent;
    const sourceWidth = maximumX - minimumX;
    const sourceHeight = maximumY - minimumY;
    const availableWidth = box.width - 2 * padding;
    const availableHeight = box.height - 2 * padding;
    const scale = Math.min(availableWidth / sourceWidth, availableHeight / sourceHeight);
    const x = box.x + (box.width - sourceWidth * scale) / 2 - minimumX * scale;
    const y = box.y + (box.height - sourceHeight * scale) / 2 + maximumY * scale;
    return {scale, x, y};
}

function customPath(collection, project, transform, centralMeridianDegrees,
    closeRings = true) {
    const commands = [];
    for (const line of geometryLines(collection)) {
        let previous = null;
        let open = false;
        let crossedSeam = false;
        for (const coordinate of line.coordinates) {
            const relative = relativeLongitudeRadians(coordinate[0],
                centralMeridianDegrees) / radiansPerDegree;
            if (previous && Math.abs(relative - previous.relative) > 180) {
                open = false;
                crossedSeam = true;
            }
            const [rawX, rawY] = project(coordinate);
            const x = transform.x + rawX * transform.scale;
            const y = transform.y - rawY * transform.scale;
            if (Number.isFinite(x) && Number.isFinite(y)) {
                commands.push(`${open ? 'L' : 'M'}${number(x)} ${number(y)}`);
                open = true;
            } else open = false;
            previous = {relative};
        }
        if (line.close && closeRings && !crossedSeam) commands.push('Z');
    }
    return commands.join('');
}

function projectionBoundary(kind, centralMeridianDegrees = 0) {
    const coordinates = [];
    const maximumLatitude = kind === 'mercator' ? 85.0511287798066 : 90;
    for (let longitude = -180; longitude <= 180; longitude += 2) {
        coordinates.push([longitude + centralMeridianDegrees, maximumLatitude]);
    }
    for (let latitude = maximumLatitude; latitude >= -maximumLatitude; latitude -= 2) {
        coordinates.push([180 + centralMeridianDegrees, latitude]);
    }
    for (let longitude = 180; longitude >= -180; longitude -= 2) {
        coordinates.push([longitude + centralMeridianDegrees, -maximumLatitude]);
    }
    for (let latitude = -maximumLatitude; latitude <= maximumLatitude; latitude += 2) {
        coordinates.push([-180 + centralMeridianDegrees, latitude]);
    }
    return {
        type: 'FeatureCollection',
        features: [{type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates}}]
    };
}

function tissotCollection() {
    const features = [];
    for (const latitude of [-60, -30, 0, 30, 60]) {
        for (const longitude of [-120, -60, 0, 60, 120]) {
            const coordinates = [];
            const radius = 7.5;
            for (let bearing = 0; bearing <= 360; bearing += 6) {
                const angle = bearing * radiansPerDegree;
                coordinates.push([
                    longitude + radius * Math.cos(angle)
                        / Math.max(0.25, Math.cos(latitude * radiansPerDegree)),
                    latitude + radius * Math.sin(angle)
                ]);
            }
            features.push({type: 'Feature', properties: {}, geometry: {type: 'LineString', coordinates}});
        }
    }
    return {type: 'FeatureCollection', features};
}

function panelFrame(box, title, subtitle) {
    return `<rect x="${box.x}" y="${box.y}" width="${box.width}" height="${box.height}" rx="18" fill="${colors.panel}" stroke="#bec6c3" stroke-width="2"/>`
        + `<text x="${box.x + 28}" y="${box.y + 48}" class="panel-title">${escapeXml(title)}</text>`
        + `<text x="${box.x + 28}" y="${box.y + 82}" class="panel-subtitle">${escapeXml(subtitle)}</text>`;
}

function customPanel({box, title, subtitle, kind, centralMeridianDegrees = 0,
    land, bounds = [-180, -85.0511287798066, 180, 85.0511287798066],
    sourceSlice = false, tissot = false}) {
    const mapBox = {x: box.x + 18, y: box.y + 104,
        width: box.width - 36, height: box.height - 126};
    const project = customProjector(kind, centralMeridianDegrees);
    const grid = graticule(bounds, sourceSlice ? 15 : 30, sourceSlice ? 10 : 15);
    const extent = sourceSlice
        ? projectedBounds([land, grid], project)
        : projectionExtent(kind);
    const transform = fitTransform(extent, mapBox);
    const gridPath = customPath(grid, project, transform, centralMeridianDegrees, false);
    const landPath = customPath(land, project, transform, centralMeridianDegrees);
    const boundary = sourceSlice ? '' : customPath(
        projectionBoundary(kind, centralMeridianDegrees), project, transform,
        centralMeridianDegrees, false);
    const seamLongitude = centralMeridianDegrees - 180;
    const seam = graticule([seamLongitude, bounds[1], seamLongitude, bounds[3]], 360, 180);
    const seamPath = customPath(seam, project, transform, centralMeridianDegrees, false);
    const indicatrices = tissot
        ? customPath(tissotCollection(), project, transform,
            centralMeridianDegrees, false) : '';
    return panelFrame(box, title, subtitle)
        + `<clipPath id="clip-${box.x}-${box.y}"><rect x="${mapBox.x}" y="${mapBox.y}" width="${mapBox.width}" height="${mapBox.height}" rx="10"/></clipPath>`
        + `<g clip-path="url(#clip-${box.x}-${box.y})">`
        + `<rect x="${mapBox.x}" y="${mapBox.y}" width="${mapBox.width}" height="${mapBox.height}" fill="${colors.water}"/>`
        + `<path d="${gridPath}" fill="none" stroke="${colors.grid}" stroke-width="1.25" opacity="0.65"/>`
        + `<path d="${landPath}" fill="${colors.land}" fill-rule="evenodd" stroke="${colors.ink}" stroke-width="1.15" opacity="0.95"/>`
        + (boundary ? `<path d="${boundary}" fill="none" stroke="${colors.ink}" stroke-width="2.4"/>` : '')
        + `<path d="${seamPath}" fill="none" stroke="${colors.seam}" stroke-width="3" stroke-dasharray="12 9"/>`
        + (indicatrices ? `<path d="${indicatrices}" fill="${colors.yellow}" fill-opacity="0.24" stroke="${colors.accent}" stroke-width="2.2"/>` : '')
        + '</g>';
}

function joinedPaths(buffer) {
    return [...commandBufferToSvgPaths(buffer, {precision: 2}).values()].join('');
}

const runtimeGeometryCache = new Map();

function runtimePanel({box, title, subtitle, projection, land, grid, options = {}}) {
    const mapBox = {x: box.x + 18, y: box.y + 104,
        width: box.width - 36, height: box.height - 126};
    const cacheKey = `${projection.id}:${options.slice ?? 'full'}`;
    let projected = runtimeGeometryCache.get(cacheKey);
    if (!projected) {
        const geometryOptions = {
            tolerancePx: 1.1,
            maximumAngularStep: 12,
            maximumSubdivisionDepth: 10,
            ...options
        };
        projected = {
            land: projection.projectGeometry(land, geometryOptions),
            grid: projection.projectGeometry(grid, geometryOptions)
        };
        runtimeGeometryCache.set(cacheKey, projected);
    }
    const projectedLand = projected.land;
    const projectedGrid = projected.grid;
    const frame = projectedLand.frame;
    const scale = Math.min(mapBox.width / frame.width, mapBox.height / frame.height);
    // Geometry coordinates are output-frame local even when `frame.originX`
    // and `frame.originY` preserve the selected slice's source-carrier view.
    const x = mapBox.x + (mapBox.width - frame.width * scale) / 2;
    const y = mapBox.y + (mapBox.height - frame.height * scale) / 2;
    const transform = `translate(${number(x)} ${number(y)}) scale(${number(scale, 6)})`;
    return panelFrame(box, title, subtitle)
        + `<clipPath id="clip-${box.x}-${box.y}"><rect x="${mapBox.x}" y="${mapBox.y}" width="${mapBox.width}" height="${mapBox.height}" rx="10"/></clipPath>`
        + `<g clip-path="url(#clip-${box.x}-${box.y})">`
        + `<rect x="${mapBox.x}" y="${mapBox.y}" width="${mapBox.width}" height="${mapBox.height}" fill="${colors.water}"/>`
        + `<path d="${joinedPaths(projectedGrid)}" transform="${transform}" fill="none" stroke="${colors.grid}" stroke-width="${number(0.75 / scale, 4)}" opacity="0.38"/>`
        + `<path d="${joinedPaths(projectedLand)}" transform="${transform}" fill="${colors.land}" fill-rule="evenodd" stroke="${colors.ink}" stroke-width="${number(0.62 / scale, 4)}"/>`
        + '</g>';
}

function page(title, subtitle, body, footer) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" data-experiment="equal-earth-positioning-speculations-v01" data-lifecycle="exploration-only">`
        + `<title>${escapeXml(title)}</title><desc>${escapeXml(subtitle)} ${escapeXml(footer)}</desc>`
        + `<style>text{font-family:'Atkinson Hyperlegible Next','Atkinson Hyperlegible',sans-serif;fill:${colors.ink}}.page-title{font-size:68px;font-weight:700}.page-subtitle{font-size:30px}.panel-title{font-size:34px;font-weight:700}.panel-subtitle{font-size:22px;fill:${colors.subdued}}.footer{font-size:21px;fill:${colors.subdued}}</style>`
        + `<rect width="${width}" height="${height}" fill="${colors.page}"/>`
        + `<text x="60" y="82" class="page-title">${escapeXml(title)}</text>`
        + `<text x="60" y="128" class="page-subtitle">${escapeXml(subtitle)}</text>`
        + body
        + `<text x="60" y="1410" class="footer">${escapeXml(footer)}</text>`
        + '</svg>';
}

function box(x, y, boxWidth, boxHeight) {
    return {x, y, width: boxWidth, height: boxHeight};
}

const world = JSON.parse(await fs.readFile(path.join(repositoryRoot,
    'src.wasm/cartofreako-cahill-keyes-land-110m.geojson'), 'utf8'));
const region = JSON.parse(await fs.readFile(path.join(repositoryRoot,
    'assets.static/resources/countries-110m.geojson'), 'utf8'));
const regionPoints = clippedPoints(region, africaBounds);
// The country fixture contains polygons; use the complete collection and the
// declared source window as a visual preclip boundary in custom panels. The
// shell wrapper supplies a GDAL-clipped regional GeoJSON when available.
const regionalLandPath = path.join(outputDirectory, 'africa-europe.geojson');
let regionalLand = regionPoints;
try {
    regionalLand = JSON.parse(await fs.readFile(regionalLandPath, 'utf8'));
} catch (error) {
    if (error.code !== 'ENOENT') throw error;
}

const runtime = await createCartofreako();
const fullGrid = graticule([-180, -84, 180, 84], 60, 30, 10);
const projections = new Map();
const projection = id => {
    if (!projections.has(id)) {
        projections.set(id, runtime.createProjection({id, width: 1600}));
    }
    return projections.get(id);
};
const diagnostics30 = distortionAt(0, 30);
const diagnostics60 = distortionAt(0, 60);

const documents = new Map();
documents.set('01-mercator-equal-earth-full-world.svg', page(
    '01 · Matched full-world baseline',
    'One source, palette, dimensions, and graticule; only the projection changes.',
    customPanel({box: box(60, 170, 1200, 1180), title: 'Web Mercator control',
        subtitle: '±85.0511288° latitude · polar omission explicit', kind: 'mercator', land: world})
    + customPanel({box: box(1300, 170, 1200, 1180), title: 'Canonical Equal Earth',
        subtitle: 'Greenwich central meridian · spherical equal-area method', kind: 'equal-earth', land: world}),
    'Exploration only · Mercator is a control, not a recommendation · Natural Earth 1:110m land context'));

documents.set('02-equal-earth-centering-and-tissot.svg', page(
    '02 · Equal Earth centering and deformation',
    'The method stays fixed; the central meridian changes from 0° to 11.5°E.',
    customPanel({box: box(60, 170, 1200, 1180), title: 'Canonical Greenwich registration',
        subtitle: `Tissot diagnostics · area scale ${number(diagnostics30.areaScale, 6)} at 30°`,
        kind: 'equal-earth', land: world, tissot: true})
    + customPanel({box: box(1300, 170, 1200, 1180), title: 'Africa-centered variant',
        subtitle: `11.5°E · not EPSG:8857 · area scale ${number(diagnostics60.areaScale, 6)} at 60°`,
        kind: 'equal-earth', centralMeridianDegrees: 11.5, land: world, tissot: true}),
    'Orange dash = antimeridian cut · indicatrices expose shape change while equal area is retained'));

documents.set('03-africa-europe-source-window.svg', page(
    '03 · Africa–Europe source-window slice',
    'Shared WGS 84 preclip: 25°W–60°E, 40°S–75°N; projected extent is fit per panel.',
    customPanel({box: box(50, 190, 800, 1140), title: 'Mercator slice',
        subtitle: 'control · conformal local shape', kind: 'mercator', land: regionalLand,
        bounds: africaBounds, sourceSlice: true})
    + customPanel({box: box(880, 190, 800, 1140), title: 'Equal Earth slice',
        subtitle: 'canonical · equal-area', kind: 'equal-earth', land: regionalLand,
        bounds: africaBounds, sourceSlice: true})
    + customPanel({box: box(1710, 190, 800, 1140), title: 'Centered Equal Earth slice',
        subtitle: '11.5°E experimental registration', kind: 'equal-earth',
        centralMeridianDegrees: 11.5, land: regionalLand, bounds: africaBounds,
        sourceSlice: true}),
    'This is a source-space comparison window, not a new registered CRS or proof of corrected perception'));

documents.set('04-cartofreako-full-carrier-alternatives.svg', page(
    '04 · Selected Cartofreako alternatives',
    'Same Natural Earth land and graticule; compare continuity, cuts, and carrier topology.',
    customPanel({box: box(60, 170, 1200, 570), title: 'Equal Earth',
        subtitle: 'uninterrupted equal-area pseudocylindrical control', kind: 'equal-earth', land: world})
    + runtimePanel({box: box(1300, 170, 1200, 570), title: 'AuthaGraph',
        subtitle: 'rectangular tetrahedral atlas carrier', projection: projection('authagraph'),
        land: world, grid: fullGrid})
    + runtimePanel({box: box(60, 770, 1200, 570), title: 'Dymaxion',
        subtitle: 'Fuller registered interrupted carrier', projection: projection('dymaxion'),
        land: world, grid: fullGrid})
    + runtimePanel({box: box(1300, 770, 1200, 570), title: 'Myriahedral Afro–Eur–Asia',
        subtitle: 'registered regional perspective', projection: projection('myriahedral-afro-eur-asia'),
        land: world, grid: fullGrid}),
    'Equal Earth remains outside the six-family standard runtime; comparison does not imply campaign compliance'));

documents.set('05-projection-and-slice-strategies.svg', page(
    '05 · Projection and slice strategies',
    'Four bounded roles: global carrier, source preclip, registered perspective, and native cell.',
    customPanel({box: box(60, 170, 1200, 570), title: 'A · Equal Earth full carrier',
        subtitle: 'global area comparison', kind: 'equal-earth', land: world})
    + customPanel({box: box(1300, 170, 1200, 570), title: 'B · Equal Earth source preclip',
        subtitle: 'Africa–Europe geographic window', kind: 'equal-earth',
        centralMeridianDegrees: 11.5, land: regionalLand, bounds: africaBounds,
        sourceSlice: true})
    + runtimePanel({box: box(60, 770, 1200, 570), title: 'C · Myriahedral registered perspective',
        subtitle: 'Afro–Eur–Asia full topology', projection: projection('myriahedral-afro-eur-asia'),
        land: world, grid: fullGrid})
    + runtimePanel({box: box(1300, 770, 1200, 570), title: 'D · Cahill–Keyes native slice',
        subtitle: 'ck-octant-3 · northern Africa/Europe cell', projection: projection('cahill-keyes'),
        land: world, grid: fullGrid, options: {slice: 'ck-octant-3'}}),
    'Select by research purpose; retain a full-carrier locator and explicit seam/cell identity with every slice'));

await fs.mkdir(outputDirectory, {recursive: true});
for (const [filename, document] of documents) {
    await fs.writeFile(path.join(outputDirectory, filename), document);
}
console.log(`rendered ${documents.size} Stage 16J SVG intermediates`);

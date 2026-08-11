#!/usr/bin/env node

import {execFile} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {promisify} from 'node:util';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const exec = promisify(execFile);
const root = path.resolve(new URL('..', import.meta.url).pathname);
const preparedDirectory = path.join(root, 'assets.static/atoll-evidence/prepared');
const fixturePath = path.join(root, 'fixtures/atoll-evidence/v1/coordinates.json');
const sourceManifestPath = path.join(root, 'fixtures/atoll-evidence/v1/manifest.json');

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function relative(value) {
    return path.relative(root, value).split(path.sep).join('/');
}

async function sha256(value) {
    const digest = createHash('sha256');
    digest.update(await fs.readFile(value));
    return digest.digest('hex');
}

async function fileRecord(value) {
    const stats = await fs.stat(value);
    return {path: relative(value), sha256: await sha256(value), bytes: stats.size};
}

async function rasterRecord(value) {
    const {stdout} = await exec('gdalinfo', ['-json', value], {maxBuffer: 16 * 1024 * 1024});
    const info = JSON.parse(stdout);
    requireCondition(info.bands.length === 1, `${relative(value)} is not single-band`);
    const wkt = info.coordinateSystem?.wkt ?? '';
    requireCondition(wkt.includes('ITRF2008')
        && (wkt.includes('UTM zone 59N') || wkt.includes('UTM_Zone_59N')),
        `${relative(value)} lost its ITRF2008 / UTM zone 59N CRS`);
    const transform = info.geoTransform;
    requireCondition(Array.isArray(transform) && transform.length === 6,
        `${relative(value)} has no affine geotransform`);
    const wgs84Footprint = info.wgs84Extent?.coordinates?.[0];
    requireCondition(Array.isArray(wgs84Footprint) && wgs84Footprint.length === 5,
        `${relative(value)} has no WGS84 footprint`);
    return {
        width: info.size[0],
        height: info.size[1],
        bandType: info.bands[0].type,
        noDataValue: info.bands[0].noDataValue,
        geoTransform: transform,
        crsName: 'ITRF2008 / UTM zone 59N',
        crsWktSha256: createHash('sha256').update(wkt).digest('hex'),
        effectiveCellMeters: [Math.abs(transform[1]), Math.abs(transform[5])],
        wgs84Footprint
    };
}

function qualifiedTrace(projection, geographic) {
    const forward = projection.forward([geographic.longitude, geographic.latitude]);
    const inverse = projection.inverse([forward.x, forward.y], {
        nativeCell: forward.nativeCell,
        component: forward.component,
        tolerancePixels: 1e-7
    });
    requireCondition(inverse.status === 'unique' && inverse.candidates.length === 1,
        'qualified atoll fixture did not produce one reverse candidate');
    const candidate = inverse.candidates[0];
    requireCondition(Math.abs(candidate.longitude - geographic.longitude) <= 2e-8
        && Math.abs(candidate.latitude - geographic.latitude) <= 2e-8,
    'qualified atoll fixture exceeded its geographic round-trip tolerance');
    return {
        forward,
        qualifiedInverse: {
            status: inverse.status,
            candidate,
            tolerancePixels: inverse.tolerancePx,
            truncated: inverse.truncated
        }
    };
}

const preparedDefinitions = [
    {
        id: 'majuro-tbdem-observation-10m',
        filename: 'majuro-tbdem-observation-10m.tif',
        evidenceType: 'observation',
        sourceId: 'usgs-majuro-tbdem-1944-2016'
    },
    {
        id: 'majuro-marine-inundation-30in-deterministic-10m',
        filename: 'majuro-marine-inundation-30in-deterministic-10m.tif',
        evidenceType: 'scenario',
        sourceId: 'usgs-majuro-inundation-2016'
    },
    {
        id: 'majuro-marine-inundation-30in-probability-10m',
        filename: 'majuro-marine-inundation-30in-probability-10m.tif',
        evidenceType: 'scenario',
        sourceId: 'usgs-majuro-inundation-2016'
    }
];

const prepared = [];
for (const definition of preparedDefinitions) {
    const value = path.join(preparedDirectory, definition.filename);
    prepared.push({
        id: definition.id,
        file: await fileRecord(value),
        evidenceType: definition.evidenceType,
        sourceId: definition.sourceId,
        raster: await rasterRecord(value)
    });
}

const runtime = await createCartofreako();
const projection = runtime.projection({name: 'myriahedral-pacific', frame: [3840, 2160]});
const anchors = [
    ['tbdem-center', 171.230319, 7.1226005],
    ['tbdem-northwest-envelope', 171.021037, 7.230342],
    ['tbdem-northeast-envelope', 171.439601, 7.230342],
    ['tbdem-southeast-envelope', 171.439601, 7.014859],
    ['tbdem-southwest-envelope', 171.021037, 7.014859]
];
const points = anchors.map(([id, longitude, latitude]) => {
    const geographic = {
        longitude, latitude, datum: 'WGS84', status: 'source-metadata-envelope'
    };
    return {
        id,
        geographic,
        evidenceRecord: 'usgs-majuro-tbdem-1944-2016',
        ...qualifiedTrace(projection, geographic)
    };
});

const observation = prepared[0];
const pixelCenter = [observation.raster.width / 2, observation.raster.height / 2];
const transform = observation.raster.geoTransform;
const sourceProjected = {
    crs: 'ITRF2008 / UTM zone 59N',
    eastingMeters: transform[0] + pixelCenter[0] * transform[1]
        + pixelCenter[1] * transform[2],
    northingMeters: transform[3] + pixelCenter[0] * transform[4]
        + pixelCenter[1] * transform[5]
};
const footprintCorners = observation.raster.wgs84Footprint.slice(0, 4);
const pixelGeographic = {
    longitude: footprintCorners.reduce((sum, value) => sum + value[0], 0) / 4,
    latitude: footprintCorners.reduce((sum, value) => sum + value[1], 0) / 4,
    datum: 'WGS84',
    status: 'gdal-itrf2008-to-wgs84-approximation'
};
const pixelTrace = {
    preparedId: observation.id,
    pixelCenter,
    sourceProjected,
    geographic: pixelGeographic,
    evidenceRecord: observation.sourceId,
    ...qualifiedTrace(projection, pixelGeographic)
};

projection.dispose();

const fixture = {
    schemaVersion: 'cartofreako-atoll-coordinate-fixtures-v1',
    lifecycle: 'exploration-only',
    studyAreaId: 'majuro-atoll-canary',
    sourceManifest: await fileRecord(sourceManifestPath),
    prepared,
    pixelTrace,
    projectionTrace: {
        projection: 'myriahedral-pacific',
        frame: {width: 3840, height: 2160},
        points
    }
};

await fs.mkdir(path.dirname(fixturePath), {recursive: true});
await fs.writeFile(fixturePath, `${JSON.stringify(fixture, null, 2)}\n`, 'utf8');
console.log(`Built ${relative(fixturePath)} with ${points.length} qualified forward/reverse anchors.`);

#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {pathToFileURL} from 'node:url';

import {
    coefficients,
    inverseDegrees,
    normalizedForward,
    rawXMaximum,
    rawYMaximum,
    relativeLongitudeRadians
} from './equal-earth.mjs';

const outputDirectory = path.resolve(process.argv[2] ?? '');
if (!process.argv[2]) {
    throw new Error('usage: generate-equal-earth-fixtures.mjs OUTPUT-DIRECTORY');
}
const d3Root = path.resolve(process.env.D3_GEO_ROOT
    ?? '/home/bkoz/src/node_modules/d3-geo');
const projOracleDirectory = path.resolve(process.env.PROJ_ORACLE_DIRECTORY ?? '');
const projOracleVersion = process.env.PROJ_ORACLE_VERSION ?? '';
if (!process.env.PROJ_ORACLE_DIRECTORY || !projOracleVersion) {
    throw new Error('PROJ_ORACLE_DIRECTORY and PROJ_ORACLE_VERSION are required; use scripts/refresh-equal-earth-fixtures.sh');
}

function hash(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
}

async function projRaw(coordinates, centralMeridianDegrees) {
    const filename = centralMeridianDegrees === 0 ? 'canonical.txt' : 'africa.txt';
    const output = await fs.readFile(path.join(projOracleDirectory, filename), 'utf8');
    return output.trim().split('\n').map(line => {
        const values = line.trim().split(/\s+/).map(Number);
        if (values.length !== 2 || !values.every(Number.isFinite)) {
            throw new Error(`invalid PROJ output: ${line}`);
        }
        return values;
    }).map((value, index, values) => {
        if (values.length !== coordinates.length) {
            throw new Error(`${filename} has ${values.length} cases, expected ${coordinates.length}`);
        }
        return value;
    });
}

function longitudeDistance(left, right) {
    let distance = Math.abs(left - right) % 360;
    if (distance > 180) distance = 360 - distance;
    return distance;
}

const d3Package = JSON.parse(await fs.readFile(path.join(d3Root, 'package.json'), 'utf8'));
const d3 = await import(pathToFileURL(path.join(d3Root, 'src/index.js')).href);
if (typeof d3.geoEqualEarthRaw !== 'function') {
    throw new Error(`${d3Root} does not export geoEqualEarthRaw`);
}

const coordinates = [
    [0, 0], [12.5, 41.9], [-73.9857, 40.7484], [171.2, 7.1],
    [15, 30], [-120, -60], [90, 60], [-45, 80], [30, -80],
    [180, 0], [-180, 0], [0, 90], [0, -90], [-168.5, 0], [60, -30]
];
const layoutDefinitions = [
    {
        layoutId: 'equal-earth/canonical-greenwich',
        centralMeridianDegrees: 0,
        registration: 'EPSG:8857 spherical method comparison'
    },
    {
        layoutId: 'equal-earth/africa-centered-11.5e',
        centralMeridianDegrees: 11.5,
        registration: 'Cartofreako experimental centered variant'
    }
];

const layouts = [];
for (const definition of layoutDefinitions) {
    const projValues = await projRaw(coordinates, definition.centralMeridianDegrees);
    const cases = coordinates.map((geographic, index) => {
        const lambda = relativeLongitudeRadians(geographic[0],
            definition.centralMeridianDegrees);
        const d3Raw = d3.geoEqualEarthRaw(lambda, geographic[1] * Math.PI / 180);
        const proj = projValues[index];
        const normalizedPage = [
            (proj[0] + rawXMaximum) / (2 * rawXMaximum),
            (rawYMaximum - proj[1]) / (2 * rawYMaximum)
        ];
        const inverse = inverseDegrees(proj, definition.centralMeridianDegrees);
        if (!inverse || longitudeDistance(inverse[0], geographic[0]) > 1e-9
            || Math.abs(inverse[1] - geographic[1]) > 1e-9) {
            throw new Error(`inverse generation failed for ${definition.layoutId} ${geographic}`);
        }
        const relativeDegrees = lambda * 180 / Math.PI;
        const boundaryClass = Math.abs(geographic[1]) === 90 ? 'pole'
            : Math.abs(Math.abs(relativeDegrees) - 180) < 1e-10 ? 'seam'
                : 'interior';
        return {
            caseId: `${definition.layoutId.split('/')[1]}-${index.toString().padStart(2, '0')}`,
            geographic,
            boundaryClass,
            expected: {
                raw: proj,
                normalizedPage,
                inverseGeographic: inverse,
                sphericalAreaScale: boundaryClass === 'pole' ? null : 1
            },
            oracles: {'PROJ': proj, 'd3-geo': d3Raw},
            tolerances: {
                raw: 2e-14,
                normalized: 5e-15,
                angularDegrees: 2e-10,
                areaScale: 2e-7
            }
        };
    });
    layouts.push({...definition, cases});
}

const fixture = {
    schemaVersion: 'cartofreako-equal-earth-fixtures-v1',
    method: {
        name: 'Equal Earth',
        model: 'unit sphere',
        coefficients: {
            A1: coefficients.a1,
            A2: coefficients.a2,
            A3: coefficients.a3,
            A4: coefficients.a4,
            M: coefficients.m
        },
        reference: 'https://doi.org/10.1080/13658816.2018.1504949'
    },
    coordinateContract: {
        geographic: '[longitude, latitude] degrees',
        raw: '[x, y] on a unit sphere, y up',
        normalized: '[u, v] full-carrier page coordinates',
        origin: 'top-left',
        axes: '+u right, +v down'
    },
    implementations: [
        {
            id: 'PROJ',
            version: projOracleVersion,
            role: 'cross-implementation oracle',
            source: 'https://proj.org/en/stable/operations/projections/eqearth.html'
        },
        {
            id: 'd3-geo',
            version: d3Package.version,
            role: 'cross-implementation oracle',
            source: 'https://github.com/d3/d3-geo/blob/v2.0.1/src/projection/equalEarth.js'
        }
    ],
    layouts
};

await fs.mkdir(outputDirectory, {recursive: true});
const fixtureBytes = Buffer.from(`${JSON.stringify(fixture, null, 2)}\n`);
await fs.writeFile(path.join(outputDirectory, 'fixtures.json'), fixtureBytes);
const schemaBytes = await fs.readFile(new URL('../contracts/equal-earth-projection-fixtures-v1.schema.json', import.meta.url));
const generatorBytes = await fs.readFile(new URL(import.meta.url));
const manifest = {
    schemaVersion: 'cartofreako-equal-earth-fixture-manifest-v1',
    bundleVersion: 1,
    license: 'GPL-3.0-or-later',
    lifecycle: 'exploration-only',
    standardRuntimeFamily: false,
    fixture: {file: 'fixtures.json', sha256: hash(fixtureBytes), caseCount: 30},
    schema: {
        file: '../../../contracts/equal-earth-projection-fixtures-v1.schema.json',
        sha256: hash(schemaBytes)
    },
    producer: {
        file: '../../../scripts/generate-equal-earth-fixtures.mjs',
        sha256: hash(generatorBytes),
        refreshTarget: 'make refresh-equal-earth-fixtures'
    },
    sourceBoundary: 'PROJ and d3-geo are comparison oracles; the published equations remain the method authority.'
};
const manifestBytes = Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`);
await fs.writeFile(path.join(outputDirectory, 'manifest.json'), manifestBytes);
await fs.writeFile(path.join(outputDirectory, 'SHA256SUMS'),
    `${hash(fixtureBytes)}  fixtures.json\n${hash(manifestBytes)}  manifest.json\n`);
console.log(`generated Equal Earth fixture bundle: 30 cases at ${outputDirectory}`);

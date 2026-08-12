#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import {
    distortionAt,
    forwardDegrees,
    inverseDegrees,
    mercatorForwardRaw,
    normalizedForward,
    normalizedInverse
} from '../scripts/equal-earth.mjs';

const root = path.resolve(import.meta.dirname, '..');
const fixtureRoot = path.join(root, 'fixtures/projections/equal-earth-v1');
const reportPath = process.argv[2] ? path.resolve(process.argv[2]) : null;

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function hash(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
}

function distance(left, right) {
    return Math.hypot(left[0] - right[0], left[1] - right[1]);
}

function angularDistance(left, right) {
    let longitude = Math.abs(left[0] - right[0]) % 360;
    if (longitude > 180) longitude = 360 - longitude;
    return Math.max(longitude, Math.abs(left[1] - right[1]));
}

const checksumText = await fs.readFile(path.join(fixtureRoot, 'SHA256SUMS'), 'utf8');
for (const line of checksumText.trim().split('\n')) {
    const match = /^([0-9a-f]{64})  (.+)$/.exec(line);
    requireCondition(match, `malformed checksum: ${line}`);
    const bytes = await fs.readFile(path.join(fixtureRoot, match[2]));
    requireCondition(hash(bytes) === match[1], `checksum mismatch: ${match[2]}`);
}
const manifest = JSON.parse(await fs.readFile(path.join(fixtureRoot, 'manifest.json')));
const fixtureBytes = await fs.readFile(path.join(fixtureRoot, manifest.fixture.file));
requireCondition(hash(fixtureBytes) === manifest.fixture.sha256, 'manifest fixture hash mismatch');
const schemaBytes = await fs.readFile(path.join(root,
    'contracts/equal-earth-projection-fixtures-v1.schema.json'));
const producerBytes = await fs.readFile(path.join(root,
    'scripts/generate-equal-earth-fixtures.mjs'));
requireCondition(hash(schemaBytes) === manifest.schema.sha256,
    'fixture manifest schema hash mismatch; review and refresh explicitly');
requireCondition(hash(producerBytes) === manifest.producer.sha256,
    'fixture manifest producer hash mismatch; review and refresh explicitly');
requireCondition(manifest.lifecycle === 'exploration-only'
    && manifest.standardRuntimeFamily === false, 'fixture crossed its lifecycle boundary');
const fixture = JSON.parse(fixtureBytes);
requireCondition(fixture.schemaVersion === 'cartofreako-equal-earth-fixtures-v1',
    'wrong fixture schema');

let maximumRawOracleDifference = 0;
let maximumForwardDifference = 0;
let maximumNormalizedDifference = 0;
let maximumReverseAngularDifference = 0;
let count = 0;
for (const layout of fixture.layouts) {
    const caseIds = new Set();
    for (const testCase of layout.cases) {
        ++count;
        requireCondition(!caseIds.has(testCase.caseId), `duplicate case ${testCase.caseId}`);
        caseIds.add(testCase.caseId);
        const tolerance = testCase.tolerances;
        const oracleDifference = distance(testCase.oracles.PROJ,
            testCase.oracles['d3-geo']);
        maximumRawOracleDifference = Math.max(maximumRawOracleDifference,
            oracleDifference);
        requireCondition(oracleDifference <= tolerance.raw,
            `${testCase.caseId}: PROJ/D3 disagreement ${oracleDifference}`);
        const forward = forwardDegrees(testCase.geographic,
            layout.centralMeridianDegrees);
        const forwardDifference = distance(forward, testCase.expected.raw);
        maximumForwardDifference = Math.max(maximumForwardDifference,
            forwardDifference);
        requireCondition(forwardDifference <= tolerance.raw,
            `${testCase.caseId}: forward disagreement ${forwardDifference}`);
        const normalized = normalizedForward(testCase.geographic,
            layout.centralMeridianDegrees);
        const normalizedDifference = distance(normalized,
            testCase.expected.normalizedPage);
        maximumNormalizedDifference = Math.max(maximumNormalizedDifference,
            normalizedDifference);
        requireCondition(normalizedDifference <= tolerance.normalized,
            `${testCase.caseId}: normalized disagreement ${normalizedDifference}`);
        const reverse = inverseDegrees(forward, layout.centralMeridianDegrees);
        requireCondition(reverse, `${testCase.caseId}: inverse returned outside`);
        const reverseDifference = angularDistance(reverse,
            testCase.expected.inverseGeographic);
        maximumReverseAngularDifference = Math.max(maximumReverseAngularDifference,
            reverseDifference);
        requireCondition(reverseDifference <= tolerance.angularDegrees,
            `${testCase.caseId}: reverse disagreement ${reverseDifference}`);
        const pageReverse = normalizedInverse(normalized,
            layout.centralMeridianDegrees);
        requireCondition(pageReverse
            && angularDistance(pageReverse, testCase.geographic)
                <= tolerance.angularDegrees,
        `${testCase.caseId}: normalized reverse disagreement`);
    }
}
requireCondition(count === manifest.fixture.caseCount, 'fixture case count mismatch');
requireCondition(normalizedInverse([-0.01, 0.5]) === null
    && normalizedInverse([1.01, 0.5]) === null,
'outside-page classification failed');

const diagnostics = [];
let maximumAreaScaleError = 0;
for (const latitude of [-80, -60, -30, 0, 30, 60, 80]) {
    for (const longitude of [-150, -90, 0, 90, 150]) {
        const equalEarth = distortionAt(longitude, latitude);
        const mercator = distortionAt(longitude, latitude, mercatorForwardRaw);
        requireCondition(equalEarth && mercator, 'diagnostic point unexpectedly singular');
        maximumAreaScaleError = Math.max(maximumAreaScaleError,
            Math.abs(equalEarth.areaScale - 1));
        diagnostics.push({longitude, latitude, equalEarth, mercator});
    }
}
requireCondition(maximumAreaScaleError <= 2e-7,
    `Equal Earth area-scale error ${maximumAreaScaleError}`);
const mercatorAt60 = diagnostics.find(value => value.longitude === 0
    && value.latitude === 60).mercator;
requireCondition(Math.abs(mercatorAt60.areaScale - 4) < 2e-6,
    'Mercator 60-degree area diagnostic is wrong');

const report = {
    schemaVersion: 'cartofreako-stage-16j-equal-earth-diagnostics-v1',
    generatedAt: new Date().toISOString(),
    lifecycle: 'exploration-only',
    fixtureCaseCount: count,
    crossImplementation: {
        implementations: fixture.implementations,
        maximumRawOracleDifference,
        maximumForwardDifference,
        maximumNormalizedDifference,
        maximumReverseAngularDifference
    },
    areaAndShape: {maximumAreaScaleError, samples: diagnostics},
    limitations: [
        'Finite differences diagnose a spherical method; they are not an ellipsoidal geodetic accuracy claim.',
        'The Africa-centered layout is an experimental central-meridian variant and is not labeled EPSG:8857.',
        'No diagnostic establishes a human-perception or decolonial-outcome claim.'
    ]
};
if (reportPath) {
    await fs.mkdir(path.dirname(reportPath), {recursive: true});
    await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
}
console.log(`Equal Earth checks passed: ${count} fixtures, `
    + `oracle ${maximumRawOracleDifference}, area ${maximumAreaScaleError}`);

#!/usr/bin/env node

import {createHash} from 'node:crypto';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {pathToFileURL} from 'node:url';

function argument(name) {
    const index = process.argv.indexOf(name);
    if (index < 0 || index + 1 >= process.argv.length) {
        throw new Error(`missing ${name}`);
    }
    return path.resolve(process.argv[index + 1]);
}

function sha256(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
}

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

const sourceRoot = argument('--source-root');
const legacyRoot = argument('--legacy-root');
const outputRoot = argument('--output');
const packageBytes = await readFile(path.join(sourceRoot, 'package.json'));
const packageDocument = JSON.parse(packageBytes);
requireCondition(packageDocument.version === '2.0.1',
    `expected d3-geo-polygon 2.0.1, got ${packageDocument.version}`);
const module = await import(pathToFileURL(path.join(sourceRoot, 'src/index.js')));
const d3Geo = await import(pathToFileURL(path.join(
    sourceRoot, 'node_modules/d3-geo/src/index.js')));
await mkdir(outputRoot, {recursive: true});

const commonProvenance = {
    implementation: 'd3-geo-polygon',
    version: '2.0.1',
    commit: '45d62833536fde08053a0675a488b937d41cde07',
    license: 'ISC',
    packageSha256: sha256(packageBytes),
    dependencyLock: 'd3-geo-polygon-v2.0.1-yarn.lock',
    dependencyLockSha256: sha256(await readFile(path.join(sourceRoot, 'yarn.lock'))),
    producer: 'tests/oracles/generate-d3-reverse-oracles.mjs'
};

const voronoiProjection = module.geoIcosahedral();
const voronoiCases = [];
for (let y = 25; y <= 475 && voronoiCases.length < 96; y += 25) {
    for (let x = 24; x <= 936 && voronoiCases.length < 96; x += 24) {
        const geographic = voronoiProjection.invert([x, y]);
        if (!geographic || !geographic.every(Number.isFinite)) continue;
        if (Math.abs(geographic[1]) > 90 + 1e-10) continue;
        const roundTrip = voronoiProjection(geographic);
        const residual = Math.hypot(roundTrip[0] - x, roundTrip[1] - y);
        if (residual > 2e-7) continue;
        voronoiCases.push({
            caseId: `d3-page-${String(voronoiCases.length).padStart(3, '0')}`,
            selectedProjected: [x / 960, y / 500],
            expectedGeographic: geographic,
            upstreamRoundTripResidualPixels: residual,
            boundaryClass: 'interior',
            angularToleranceDegrees: 2e-7
        });
    }
}
requireCondition(voronoiCases.length === 96,
    `only ${voronoiCases.length} valid Voronoi oracle cases`);
await writeFile(path.join(outputRoot, 'voronoi-d3-v2.0.1.json'), `${JSON.stringify({
    schemaVersion: 'cartofreako-reverse-oracle-v1',
    family: 'voronoi',
    evidenceGrade: 'upstream-implementation',
    coordinateContract: {
        projected: '[u, v] normalized 960x500 top-left page space',
        geographic: '[longitude, latitude] degrees'
    },
    selectionMethod: 'fixed 24-pixel by 25-pixel page lattice; first 96 interior points with an upstream inverse/forward residual no greater than 2e-7 pixels',
    provenance: commonProvenance,
    cases: voronoiCases
}, null, 2)}\n`);

const airocean = module.geoAirocean();
requireCondition(airocean.faces.length >= 23, 'upstream Airocean has fewer than 23 faces');
const airoceanRotation = d3Geo.geoRotation(airocean.rotate());
const weightSets = [
    [0.60, 0.20, 0.20],
    [0.20, 0.60, 0.20],
    [0.20, 0.20, 0.60],
    [1 / 3, 1 / 3, 1 / 3]
];
function refineFaceInverse(face, target, initial) {
    const value = [...initial];
    const step = 1e-5;
    for (let iteration = 0; iteration < 20; ++iteration) {
        const projected = face.project(value);
        const residual = [target[0] - projected[0], target[1] - projected[1]];
        if (Math.hypot(...residual) <= 2e-13) break;
        const longitudePlus = face.project([value[0] + step, value[1]]);
        const longitudeMinus = face.project([value[0] - step, value[1]]);
        const latitudePlus = face.project([value[0], value[1] + step]);
        const latitudeMinus = face.project([value[0], value[1] - step]);
        const a = (longitudePlus[0] - longitudeMinus[0]) / (2 * step);
        const c = (longitudePlus[1] - longitudeMinus[1]) / (2 * step);
        const b = (latitudePlus[0] - latitudeMinus[0]) / (2 * step);
        const d = (latitudePlus[1] - latitudeMinus[1]) / (2 * step);
        const determinant = a * d - b * c;
        requireCondition(Number.isFinite(determinant) && Math.abs(determinant) > 1e-14,
            'singular D3 Gray refinement Jacobian');
        value[0] += (d * residual[0] - b * residual[1]) / determinant;
        value[1] += (-c * residual[0] + a * residual[1]) / determinant;
    }
    return value;
}
const dymaxionCases = [];
// The first 23 upstream registrations are frozen here. Upstream's additional
// face-19 cut has no exact Cartofreako/PROJ topology counterpart; the offline
// verifier retains and classifies that registration difference explicitly.
for (let faceIndex = 0; faceIndex < 23; ++faceIndex) {
    const face = airocean.faces[faceIndex];
    const projectedVertices = face.face.map(coordinate => face.project(coordinate));
    for (let weightIndex = 0; weightIndex < weightSets.length; ++weightIndex) {
        const weights = weightSets[weightIndex];
        const projected = [0, 1].map(axis => weights.reduce((sum, weight, index) =>
            sum + weight * projectedVertices[index][axis], 0));
        const upstreamApproximation = face.project.invert(projected);
        requireCondition(upstreamApproximation && upstreamApproximation.every(Number.isFinite),
            `Airocean face ${faceIndex} inverse failed`);
        const internalGeographic = refineFaceInverse(
            face, projected, upstreamApproximation);
        const geographic = airoceanRotation.invert(internalGeographic);
        const roundTrip = face.project(internalGeographic);
        dymaxionCases.push({
            caseId: `fuller-face-${String(faceIndex).padStart(2, '0')}-weights-${weightIndex}`,
            topologyKey: `fuller-registered-face:${String(faceIndex).padStart(2, '0')}`,
            upstreamFace: faceIndex,
            faceVerticesGeographic: face.face.map(vertex =>
                airoceanRotation.invert(vertex)),
            selectedProjectedBarycentricWeights: weights,
            expectedGeographic: geographic,
            upstreamApproximateGeographic: airoceanRotation.invert(upstreamApproximation),
            upstreamRoundTripResidual: Math.hypot(
                roundTrip[0] - projected[0], roundTrip[1] - projected[1]),
            boundaryClass: 'interior',
            angularToleranceDegrees: 3e-4
        });
    }
}
await writeFile(path.join(outputRoot, 'dymaxion-d3-gray-v2.0.1.json'), `${JSON.stringify({
    schemaVersion: 'cartofreako-reverse-oracle-v1',
    family: 'dymaxion',
    evidenceGrade: 'upstream-implementation',
    coordinateContract: {
        selectedProjected: 'barycentric weights in the independently projected Gray/Fuller face',
        geographic: '[longitude, latitude] degrees'
    },
    selectionMethod: 'four fixed interior projected barycentric coordinates in each of the first 23 upstream Airocean registrations; any non-common topology is retained as a classified registration difference',
    provenance: {...commonProvenance,
        upstreamModule: 'src/airocean.js and src/grayfuller.js',
        refinement: 'dependency-free central-difference Newton solve against the pinned upstream Gray forward transform; the upstream approximate inverse is retained per case'},
    registrationBound: '3e-4 degrees covers the independently observed rounded D3 rotation versus PROJ/Cartofreako Fuller vertex registration; it is not used by the Voronoi or Myriahedral oracles',
    cases: dymaxionCases
}, null, 2)}\n`);

const legacySource = await readFile(path.join(legacyRoot, 'src/icosahedral.js'));
const currentSource = await readFile(path.join(sourceRoot, 'src/icosahedral.js'));
const definingTokens = [
    'atan(0.5)', '[0, 90]', '[0, -90]', '[0, 3, 11]', '[1, 10, 2]',
    '-1, // 0', '13, // 14', '.rotate([108,0])', '.scale(131.777)',
    '.center([162, 0])'
];
for (const token of definingTokens) {
    requireCondition(legacySource.includes(Buffer.from(token)),
        `v1.12.1 source lacks ${token}`);
    requireCondition(currentSource.includes(Buffer.from(token)),
        `v2.0.1 source lacks ${token}`);
}
await writeFile(path.join(outputRoot, 'd3-version-delta-v1.12.1-v2.0.1.json'),
    `${JSON.stringify({
        schemaVersion: 'cartofreako-oracle-version-delta-v1',
        package: 'd3-geo-polygon',
        from: {
            version: '1.12.1',
            sourceSha256: sha256(legacySource),
            dependencyLockSha256: sha256(await readFile(path.join(legacyRoot, 'yarn.lock')))
        },
        to: {
            version: '2.0.1',
            commit: commonProvenance.commit,
            sourceSha256: sha256(currentSource),
            dependencyLockSha256: commonProvenance.dependencyLockSha256
        },
        audit: {
            projectionDefiningTokens: definingTokens,
            result: 'registration-preserving',
            observation: 'The icosahedron vertices, 20 face triples, parent tree, 108-degree rotation, 131.777 scale, and 162-degree center are retained. The inspected changes modernize JavaScript syntax and GeoJSON Feature declarations.',
            scope: 'Source-level registration delta; numeric reverse cases are generated only by pinned v2.0.1.'
        }
    }, null, 2)}\n`);

console.log(`generated ${voronoiCases.length} Voronoi and `
    + `${dymaxionCases.length} Dymaxion upstream reverse cases`);

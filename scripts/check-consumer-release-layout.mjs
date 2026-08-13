#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const fixturePath = path.join(root, 'fixtures/consumer-release-layout/v1/manifest.json');
let output = path.join(root, 'build/consumer-release-layout-v1');
if (process.argv.length > 2) {
    if (process.argv.length !== 4 || process.argv[2] !== '--output') {
        throw new Error('usage: check-consumer-release-layout.mjs [--output PATH]');
    }
    output = path.resolve(process.argv[3]);
}

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function sha256(file) {
    return createHash('sha256').update(await fs.readFile(file)).digest('hex');
}

async function readJson(file) {
    return JSON.parse(await fs.readFile(file));
}

function safeRelative(value) {
    return typeof value === 'string' && value.length > 0
        && !value.startsWith('/') && !value.includes('..') && !value.includes('\\');
}

const fixture = await readJson(fixturePath);
const release = await readJson(path.join(output, 'release-layout.json'));
requireCondition(release.schemaVersion === 'cartofreako-consumer-release-candidate-v1'
    && release.lifecycle === 'exploration-only'
    && release.candidateRelease.id === 'proposed-v14'
    && release.candidateRelease.published === false
    && release.candidateRelease.uploadAuthorized === false,
'candidate release identity or boundary changed');
requireCondition(release.releaseBoundary.builderNetworkAccess === false
    && release.releaseBoundary.builderS3Access === false
    && release.releaseBoundary.completionMarkerBuilt === false
    && release.releaseBoundary.humanInvocationRequired === true,
'local builder acquired release authority');
requireCondition(release.artifactCount === 211 && release.passCount === 32
    && release.layoutCount === 11 && release.sliceCount === 14,
'consumer layout corpus counts changed');
requireCondition(release.indexes.length === 44,
    'consumer layout must have one primary, 32 pass, and 11 layout indexes');
requireCondition(release.excludedExperiments.includes('gpu-control-2k-landscape-v1')
    && release.excludedExperiments.includes('gpu-control-2k-portrait-v1'),
'unpromoted 2K controls entered the candidate release');
requireCondition(!await fs.stat(path.join(output, fixture.candidateRelease.completionMarker))
    .then(() => true, error => {
        if (error.code === 'ENOENT') return false;
        throw error;
    }), 'local consumer layout contains a release completion marker');

for (const record of [...release.indexes, release.runtimeManifest]) {
    requireCondition(safeRelative(record.path), `unsafe layout path: ${record.path}`);
    const file = path.join(output, record.path);
    const stat = await fs.stat(file);
    requireCondition(stat.isFile() && stat.size === record.bytes
        && await sha256(file) === record.sha256,
    `layout hash mismatch: ${record.path}`);
}
const artifactIndex = await readJson(path.join(output, 'indexes/artifacts-v1.json'));
requireCondition(artifactIndex.artifactCount === 211
    && artifactIndex.artifacts.length === 211
    && new Set(artifactIndex.artifacts.map(value => value.id)).size === 211,
'primary artifact index is incomplete');
const productPaths = [];
for (const artifact of artifactIndex.artifacts) {
    requireCondition(artifact.lifecycle === 'standard',
        `${artifact.id} is not in the standard lifecycle partition`);
    requireCondition(artifact.v13.screenPng === null && artifact.v13.screenWebp === null,
        `${artifact.id} invents a v13 screen derivative`);
    for (const [key, value] of Object.entries(artifact.proposedV14)) {
        if (value === null) continue;
        requireCondition(safeRelative(value)
            && value.startsWith(`products/standard/${artifact.projectionId}/`),
        `${artifact.id} has an unsafe proposed path for ${key}`);
        productPaths.push(value);
    }
}
requireCondition(new Set(productPaths).size === productPaths.length,
    'proposed v14 product paths are not unique');

const runtimeManifest = await readJson(path.join(output, release.runtimeManifest.path));
requireCondition(runtimeManifest.runtimeApi === 3 && runtimeManifest.geometryAbi === 1
    && runtimeManifest.files.length === fixture.runtime.core.length
        + fixture.runtime.optional.length,
'runtime release manifest changed');
const runtimeNames = new Set(runtimeManifest.files.map(value => path.basename(value.path)));
for (const required of [
    'cartofreako-projections.mjs', 'cartofreako-projections.wasm',
    'cartofreako-web.mjs'
]) requireCondition(runtimeNames.has(required), `runtime is missing ${required}`);
for (const record of runtimeManifest.files) {
    const destination = path.join(output, record.path);
    const source = path.join(root, record.source);
    const [destinationHash, sourceHash, stat] = await Promise.all([
        sha256(destination), sha256(source), fs.stat(destination)
    ]);
    requireCondition(destinationHash === record.sha256
        && destinationHash === sourceHash && stat.size === record.bytes,
    `runtime copy differs from source: ${record.path}`);
    requireCondition(record.cacheControl === 'public,max-age=31536000,immutable',
        `runtime cache policy changed: ${record.path}`);
}
const webModule = await fs.readFile(path.join(output,
    'runtime/api-3/cartofreako-web.mjs'), 'utf8');
requireCondition(webModule.includes("from './cartofreako-projections.mjs'"),
    'versioned runtime no longer preserves the loader import pair');
const loader = await fs.readFile(path.join(output,
    'runtime/api-3/cartofreako-projections.mjs'), 'utf8');
requireCondition(loader.includes('cartofreako-projections.wasm'),
    'versioned runtime no longer preserves the WASM companion name');
requireCondition(release.precompression.status === 'deferred'
    && release.cachePolicy.completionMarker === 'no-store',
'precompression or marker caching was silently promoted');

console.log('Stage 15I consumer layout passed: local-only candidate, 211 artifacts, 44 indexes, versioned WASM pair, no completion marker, no promoted 2K controls.');

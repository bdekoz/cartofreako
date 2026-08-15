#!/usr/bin/env node

import {createHash} from 'node:crypto';
import {createReadStream} from 'node:fs';
import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const catalogPath = path.join(root, 'assets.generated/catalog/artifacts-v1.json');
const manifestPath = path.join(root, 'contracts/standard-artifact-manifest-v1.json');
const outputPath = path.join(root, 'fixtures/gpu-benchmark/v1/stage-14-inputs.json');
const frozenCommit = '737ea6f7698dce810c3334dee713a497d7e389aa';
const mode = process.argv[2] ?? '--check';

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function sha256(file) {
    const hash = createHash('sha256');
    for await (const chunk of createReadStream(file)) hash.update(chunk);
    return hash.digest('hex');
}

function relative(file) {
    return path.relative(root, file).split(path.sep).join('/');
}

function retainFileRecord(value) {
    const keys = [
        'path', 'mediaType', 'bytes', 'sha256', 'authorityClass', 'dimensions',
        'lossless', 'colorSpace', 'transparency', 'contentMediaType',
        'contentEncoding'
    ];
    return Object.fromEntries(keys.filter(key => value[key] !== undefined)
        .map(key => [key, value[key]]));
}

async function mapLimit(values, limit, callback) {
    let next = 0;
    async function worker() {
        while (true) {
            const index = next++;
            if (index >= values.length) return;
            await callback(values[index], index);
        }
    }
    await Promise.all(Array.from({length: Math.min(limit, values.length)}, worker));
}

requireCondition(['--check', '--refresh'].includes(mode),
    'usage: freeze-stage-15-inputs.mjs [--check|--refresh]');
if (mode === '--check') {
    // Stage 15A is re-frozen from the current clean corpus so every retained
    // parent remains buildable from the standard graph at the frozen commit.
    // Validate its retained records and parents directly so later standard
    // passes do not rewrite or invalidate the benchmark baseline.
    const frozen = JSON.parse(await fs.readFile(outputPath));
    requireCondition(frozen.schemaVersion === 'cartofreako-gpu-benchmark-v1'
        && frozen.documentType === 'input-freeze'
        && frozen.lifecycle === 'exploration-only'
        && frozen.frozenStage14.sourceCommit === frozenCommit
        && frozen.frozenStage14.workingTree === 'clean'
        && frozen.frozenStage14.runtimeApi === 3
        && frozen.frozenStage14.geometryAbi === 1
        && frozen.frozenStage14.artifactCount === 211
        && frozen.cases.length === 211,
    'Stage 15A retained Stage 14 identity changed');
    requireCondition(new Set(frozen.cases.map(value => value.id)).size === 211,
        'Stage 15A retained cases are not unique');
    const retainedFiles = [];
    for (const value of frozen.cases) {
        for (const file of [value.parents.svg, value.parents.pdf,
            value.parents.fullPng, value.screen.png, value.screen.webp]) {
            retainedFiles.push({id: value.id, value: file});
        }
    }
    requireCondition(retainedFiles.length === 1055,
        'Stage 15A retained file-record count changed');
    const retainedPaths = new Set();
    for (const {id, value} of retainedFiles) {
        requireCondition(typeof value.path === 'string'
            && value.path.startsWith('assets.generated/')
            && Number.isInteger(value.bytes) && value.bytes > 0
            && /^[0-9a-f]{64}$/.test(value.sha256),
        `${id} has an invalid retained file record`);
        requireCondition(!retainedPaths.has(value.path),
            `${id} repeats retained path ${value.path}`);
        retainedPaths.add(value.path);
    }
    // The fixture is historical evidence. Do not compare its SVG, PDF, or
    // screen records with a mutable live assets.generated tree: a current
    // render can legitimately differ, and PDF encoder bytes are not the print
    // geometry contract. Consumers that actually derive a control validate
    // the required full-PNG parent hash at use time.
    console.log(`Stage 15A input freeze passed: 211 retained clean Stage 14 artifact records at ${frozenCommit}; current generated files are independent.`);
    process.exit(0);
}
const [catalogBytes, manifestBytes] = await Promise.all([
    fs.readFile(catalogPath), fs.readFile(manifestPath)
]);
const catalog = JSON.parse(catalogBytes);
const manifest = JSON.parse(manifestBytes);
requireCondition(catalog.schema === 'cartofreako-artifacts-v1',
    'wrong Stage 14 artifact catalog');
requireCondition(catalog.sourceRevision.gitCommit === frozenCommit,
    `Stage 14 catalog is not frozen at ${frozenCommit}`);
requireCondition(catalog.sourceRevision.workingTree === 'clean',
    'Stage 14 catalog was not generated from a clean tree');
requireCondition(catalog.sourceRevision.runtimeApi === 3
    && catalog.sourceRevision.geometryAbi === 1,
'Stage 14 runtime identity changed');
requireCondition(manifest.schemaVersion === 'cartofreako-standard-artifact-manifest-v1'
    && manifest.artifactCount === 211 && catalog.artifacts.length === 211,
'Stage 14 corpus is incomplete');
const manifestHash = createHash('sha256').update(manifestBytes).digest('hex');
requireCondition(catalog.sourceRevision.standardManifestSha256 === manifestHash,
    'catalog and standard manifest hashes differ');
const catalogIds = catalog.artifacts.map(({id}) => id).sort();
const manifestIds = manifest.artifacts.map(({id}) => id).sort();
requireCondition(JSON.stringify(catalogIds) === JSON.stringify(manifestIds),
    'catalog and standard manifest artifact IDs differ');

const sourceFiles = [];
for (const artifact of catalog.artifacts) {
    for (const value of [artifact.parents.svg, artifact.parents.pdf,
        artifact.parents.fullPng, artifact.screen.png, artifact.screen.webp]) {
        sourceFiles.push({id: artifact.id, value});
    }
}
await mapLimit(sourceFiles, 12, async ({id, value}) => {
    const file = path.join(root, value.path);
    const stat = await fs.stat(file);
    requireCondition(stat.isFile() && stat.size === value.bytes,
        `${id} size mismatch for ${value.path}`);
    requireCondition(await sha256(file) === value.sha256,
        `${id} hash mismatch for ${value.path}`);
});

const controlRecipes = [
    {
        id: 'gpu-control-2k-landscape-v1',
        canvas: {width: 2048, height: 1024},
        fit: 'contain',
        background: '#f4f5f5',
        filter: 'Lanczos',
        sourceRole: 'full-raster-parent',
        authorityClass: 'exploration-control',
        mediaType: 'image/png',
        colorSpace: 'sRGB',
        alpha: 'opaque',
        depth: 8,
        lossless: true
    },
    {
        id: 'gpu-control-2k-portrait-v1',
        canvas: {width: 1024, height: 2048},
        fit: 'contain',
        background: '#f4f5f5',
        filter: 'Lanczos',
        sourceRole: 'full-raster-parent',
        authorityClass: 'exploration-control',
        mediaType: 'image/png',
        colorSpace: 'sRGB',
        alpha: 'opaque',
        depth: 8,
        lossless: true
    }
];
const cases = catalog.artifacts.map(artifact => ({
    id: artifact.id,
    passId: artifact.pass.id,
    projectionId: artifact.projection.id,
    layoutId: artifact.projection.layoutId,
    sliceId: artifact.slice?.id ?? null,
    lifecycle: artifact.pass.lifecycle,
    sourcePeriod: artifact.evidence.sourcePeriod,
    artifactFrame: artifact.projection.artifactFrame,
    parents: {
        svg: retainFileRecord(artifact.parents.svg),
        pdf: retainFileRecord(artifact.parents.pdf),
        fullPng: retainFileRecord(artifact.parents.fullPng)
    },
    screen: {
        canvas: artifact.screen.canvas,
        fit: artifact.screen.fit,
        background: artifact.screen.background,
        contentRectangle: artifact.screen.contentRectangle,
        projectedToScreen: artifact.screen.projectedToScreen,
        screenToProjected: artifact.screen.screenToProjected,
        png: retainFileRecord(artifact.screen.png),
        webp: retainFileRecord(artifact.screen.webp)
    }
})).sort((left, right) => left.id.localeCompare(right.id, 'en'));
const fixture = {
    schemaVersion: 'cartofreako-gpu-benchmark-v1',
    documentType: 'input-freeze',
    lifecycle: 'exploration-only',
    frozenStage14: {
        sourceCommit: frozenCommit,
        workingTree: 'clean',
        runtimeApi: 3,
        geometryAbi: 1,
        artifactCatalog: {
            path: relative(catalogPath),
            sha256: createHash('sha256').update(catalogBytes).digest('hex'),
            sourceCommit: frozenCommit,
            artifactCount: cases.length
        },
        standardManifest: {
            path: relative(manifestPath),
            sha256: manifestHash
        },
        artifactCount: cases.length,
        passCount: new Set(cases.map(value => value.passId)).size,
        layoutCount: new Set(cases.map(value => value.layoutId)).size,
        sliceCount: cases.filter(value => value.sliceId !== null).length
    },
    controlRecipes,
    cases
};
const serialized = `${JSON.stringify(fixture, null, 2)}\n`;
if (mode === '--refresh') {
    await fs.mkdir(path.dirname(outputPath), {recursive: true});
    await fs.writeFile(outputPath, serialized, 'utf8');
    console.log(`Frozen ${cases.length} Stage 14 inputs at ${relative(outputPath)}.`);
} else {
    const existing = await fs.readFile(outputPath, 'utf8');
    requireCondition(existing === serialized,
        `${relative(outputPath)} is stale; run make refresh-stage-15-inputs`);
    console.log(`Stage 15A input freeze passed: ${cases.length} clean Stage 14 artifacts at ${frozenCommit}.`);
}

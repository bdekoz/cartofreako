#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const fixturePath = path.join(root, 'fixtures/consumer-release-layout/v1/manifest.json');
let output = path.join(root, 'build/consumer-release-layout-v1');
let replace = false;

for (let index = 2; index < process.argv.length; ++index) {
    const argument = process.argv[index];
    if (argument === '--replace') replace = true;
    else if (argument === '--output' && process.argv[index + 1]) {
        output = path.resolve(process.argv[++index]);
    } else {
        throw new Error('usage: build-consumer-release-layout.mjs [--replace] [--output PATH]');
    }
}

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function relative(file, base = root) {
    return path.relative(base, file).split(path.sep).join('/');
}

function sha256Bytes(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
}

async function fileRecord(file, base, extra = {}) {
    const bytes = await fs.readFile(file);
    return {
        path: relative(file, base),
        bytes: bytes.length,
        sha256: sha256Bytes(bytes),
        ...extra
    };
}

async function writeJson(file, value, base) {
    const bytes = Buffer.from(`${JSON.stringify(value, null, 2)}\n`);
    await fs.mkdir(path.dirname(file), {recursive: true});
    await fs.writeFile(file, bytes);
    return {
        path: relative(file, base),
        mediaType: 'application/json',
        bytes: bytes.length,
        sha256: sha256Bytes(bytes)
    };
}

function fill(template, values) {
    return Object.entries(values).reduce((result, [key, value]) =>
        result.replaceAll(`{${key}}`, value), template);
}

function safeId(value) {
    requireCondition(/^[a-z0-9][a-z0-9.-]*$/.test(value), `unsafe index ID: ${value}`);
    return value;
}

async function exists(file) {
    try {
        return (await fs.stat(file)).isFile();
    } catch (error) {
        if (error.code === 'ENOENT') return false;
        throw error;
    }
}

const resolvedBuildRoot = path.resolve(root, 'build');
requireCondition(output === resolvedBuildRoot || output.startsWith(`${resolvedBuildRoot}${path.sep}`),
    'consumer layout output must remain inside the repository build directory');
if (await exists(output) || await fs.stat(output).then(() => true, error => {
    if (error.code === 'ENOENT') return false;
    throw error;
})) {
    requireCondition(replace, `output exists: ${relative(output)}; pass --replace`);
    await fs.rm(output, {recursive: true, force: true});
}
const temporary = path.join(resolvedBuildRoot, `.consumer-release-layout-v1.${process.pid}`);
await fs.rm(temporary, {recursive: true, force: true});
await fs.mkdir(temporary, {recursive: true});

try {
    const fixture = JSON.parse(await fs.readFile(fixturePath));
    requireCondition(fixture.schemaVersion === 'cartofreako-consumer-release-layout-v1'
        && fixture.lifecycle === 'exploration-only'
        && fixture.candidateRelease.published === false
        && fixture.candidateRelease.uploadAuthorized === false
        && fixture.releaseBoundary.builderNetworkAccess === false
        && fixture.releaseBoundary.builderS3Access === false
        && fixture.releaseBoundary.completionMarkerBuilt === false,
    'consumer layout fixture crosses its local-only boundary');
    const inputPath = path.join(root, fixture.sourceInput.path);
    const inputBytes = await fs.readFile(inputPath);
    requireCondition(sha256Bytes(inputBytes) === fixture.sourceInput.sha256,
        'consumer layout source input hash changed');
    const input = JSON.parse(inputBytes);
    requireCondition(input.documentType === 'input-freeze'
        && input.frozenStage14.sourceCommit === fixture.sourceInput.sourceCommit
        && input.cases.length === fixture.sourceInput.artifactCount,
    'consumer layout source input identity changed');

    const artifactRecords = [];
    for (const value of input.cases) {
        const projection = safeId(value.projectionId);
        const lifecycle = value.lifecycle;
        const svgName = path.basename(value.parents.svg.path).endsWith('.svg.gz')
            ? path.basename(value.parents.svg.path)
            : `${path.basename(value.parents.svg.path)}.gz`;
        const pdfName = path.basename(value.parents.pdf.path);
        const pngName = path.basename(value.parents.fullPng.path);
        const screenPngName = path.basename(value.screen.png.path);
        const screenWebpName = path.basename(value.screen.webp.path);
        const thumbnailName = pngName;
        const localThumbnail = path.join(root, 'assets.generated', projection,
            'thumbnail', thumbnailName);
        const hasThumbnail = await exists(localThumbnail);
        const substitutions = {lifecycle, projection};
        artifactRecords.push({
            id: value.id,
            lifecycle,
            passId: value.passId,
            projectionId: value.projectionId,
            layoutId: value.layoutId,
            sliceId: value.sliceId,
            authority: {
                master: value.parents.svg.authorityClass,
                print: value.parents.pdf.authorityClass,
                fullRaster: value.parents.fullPng.authorityClass,
                screen: value.screen.png.authorityClass
            },
            hashes: {
                master: value.parents.svg.sha256,
                print: value.parents.pdf.sha256,
                fullRaster: value.parents.fullPng.sha256,
                screenPng: value.screen.png.sha256,
                screenWebp: value.screen.webp.sha256
            },
            v13: {
                masterSvgGzip: `tree/${projection}/svg/${svgName}`,
                printPdf: `tree/${projection}/pdf/${pdfName}`,
                fullPng: `tree/${projection}/png/${pngName}`,
                thumbnailPng: hasThumbnail
                    ? `tree/${projection}/thumbnail/${thumbnailName}` : null,
                screenPng: null,
                screenWebp: null
            },
            proposedV14: {
                masterSvgGzip: fill(fixture.productPaths.masterSvgGzip,
                    {...substitutions, filename: svgName}),
                printPdf: fill(fixture.productPaths.printPdf,
                    {...substitutions, filename: pdfName}),
                fullPng: fill(fixture.productPaths.fullPng,
                    {...substitutions, filename: pngName}),
                thumbnailPng: hasThumbnail ? fill(fixture.productPaths.thumbnailPng,
                    {...substitutions, filename: thumbnailName}) : null,
                screenPng: fill(fixture.productPaths.screenPng,
                    {...substitutions, filename: screenPngName}),
                screenWebp: fill(fixture.productPaths.screenWebp,
                    {...substitutions, filename: screenWebpName})
            }
        });
    }
    artifactRecords.sort((left, right) => left.id.localeCompare(right.id, 'en'));
    const artifactIndex = {
        schemaVersion: 'cartofreako-consumer-artifact-index-v1',
        lifecycle: 'exploration-only-layout',
        candidateRelease: fixture.candidateRelease.id,
        sourceInput: fixture.sourceInput,
        artifactCount: artifactRecords.length,
        artifacts: artifactRecords
    };
    const indexRecords = [];
    indexRecords.push(await writeJson(path.join(temporary, 'indexes/artifacts-v1.json'),
        artifactIndex, temporary));

    const groups = [
        ['by-pass', 'passId'],
        ['by-projection', 'projectionId']
    ];
    for (const [directory, key] of groups) {
        const values = new Map();
        for (const artifact of artifactRecords) {
            if (!values.has(artifact[key])) values.set(artifact[key], []);
            values.get(artifact[key]).push(artifact.id);
        }
        for (const [id, artifactIds] of [...values].sort(([left], [right]) =>
            left.localeCompare(right, 'en'))) {
            indexRecords.push(await writeJson(
                path.join(temporary, 'indexes', directory, `${safeId(id)}.json`),
                {
                    schemaVersion: 'cartofreako-consumer-secondary-index-v1',
                    key,
                    value: id,
                    artifactCount: artifactIds.length,
                    artifactIds,
                    primaryIndex: '../artifacts-v1.json'
                }, temporary));
        }
    }

    const runtimeDirectory = path.join(temporary, fixture.runtime.versionDirectory);
    await fs.mkdir(runtimeDirectory, {recursive: true});
    const runtimeRecords = [];
    for (const [classification, files] of [
        ['core', fixture.runtime.core], ['optional', fixture.runtime.optional]
    ]) {
        for (const value of files) {
            const source = path.join(root, value.source);
            const destination = path.join(runtimeDirectory, path.basename(value.source));
            await fs.copyFile(source, destination);
            runtimeRecords.push(await fileRecord(destination, temporary, {
                source: value.source,
                classification,
                role: value.role,
                mediaType: value.mediaType,
                cacheControl: fixture.cachePolicy.immutablePayload
            }));
        }
    }
    runtimeRecords.sort((left, right) => left.path.localeCompare(right.path, 'en'));
    const runtimeManifestRecord = await writeJson(
        path.join(runtimeDirectory, 'runtime-manifest.json'),
        {
            schemaVersion: 'cartofreako-runtime-release-manifest-v1',
            runtimeApi: 3,
            geometryAbi: 1,
            identityRule: fixture.runtime.identityRule,
            files: runtimeRecords
        }, temporary);

    indexRecords.sort((left, right) => left.path.localeCompare(right.path, 'en'));
    const releaseLayout = {
        schemaVersion: 'cartofreako-consumer-release-candidate-v1',
        lifecycle: 'exploration-only',
        referenceRelease: fixture.referenceRelease,
        candidateRelease: fixture.candidateRelease,
        sourceInput: fixture.sourceInput,
        partitions: fixture.partitions,
        artifactCount: artifactRecords.length,
        passCount: new Set(artifactRecords.map(value => value.passId)).size,
        layoutCount: new Set(artifactRecords.map(value => value.layoutId)).size,
        sliceCount: artifactRecords.filter(value => value.sliceId !== null).length,
        indexes: indexRecords,
        runtimeManifest: runtimeManifestRecord,
        delivery: fixture.delivery,
        cachePolicy: fixture.cachePolicy,
        precompression: fixture.precompression,
        excludedExperiments: [
            'gpu-control-2k-landscape-v1',
            'gpu-control-2k-portrait-v1'
        ],
        releaseBoundary: fixture.releaseBoundary
    };
    await writeJson(path.join(temporary, 'release-layout.json'), releaseLayout, temporary);
    requireCondition(!await exists(path.join(temporary,
        fixture.candidateRelease.completionMarker)),
    'local candidate must not contain a completion marker');
    await fs.rename(temporary, output);
    console.log(`Built local consumer layout: ${artifactRecords.length} artifacts, ${indexRecords.length} indexes, ${runtimeRecords.length} runtime files at ${relative(output)}.`);
} catch (error) {
    await fs.rm(temporary, {recursive: true, force: true});
    throw error;
}

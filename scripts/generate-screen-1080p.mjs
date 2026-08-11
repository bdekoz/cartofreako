#!/usr/bin/env node

import {execFile} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createReadStream} from 'node:fs';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {promisify} from 'node:util';
import {createGunzip} from 'node:zlib';

import {containTransform} from '../src.wasm/cartofreako-screen.mjs';

const execFileAsync = promisify(execFile);
const root = path.resolve(new URL('..', import.meta.url).pathname);
const generated = path.join(root, 'assets.generated');
const manifestPath = path.join(root, 'contracts/standard-artifact-manifest-v1.json');
const canvas = Object.freeze({width: 1920, height: 1080});
const background = '#f4f5f5';
const recipeVersion = 2;
const defaultJobs = Math.min(4, os.availableParallelism?.() ?? os.cpus().length ?? 1);
const jobs = Number(process.env.SCREEN_JOBS ?? defaultJobs);

const projectionDefinitions = Object.freeze({
    'cahill-keyes': {family: 'cahill-keyes', frame: {x: 0, y: 0, width: 44, height: 22}, cutTopology: 'folded', inverseMode: 'face-qualified', nativeCellCount: 8, componentCount: 1},
    authagraph: {family: 'authagraph', frame: {x: 0, y: 0, width: 44, height: 19.052559}, cutTopology: 'periodic', inverseMode: 'face-qualified', nativeCellCount: 24, componentCount: 1},
    dymaxion: {family: 'dymaxion', frame: {x: 0, y: 0, width: 44, height: 20.78461}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 23, componentCount: 1},
    myriahedral: {family: 'myriahedral', frame: {x: 0, y: 0, width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 5120, componentCount: 1},
    'myriahedral-americas': {family: 'myriahedral', frame: {x: 0, y: 0, width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 5120, componentCount: 1},
    'myriahedral-atlantic': {family: 'myriahedral', frame: {x: 0, y: 0, width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 5120, componentCount: 1},
    'myriahedral-afro-eur-asia': {family: 'myriahedral', frame: {x: 0, y: 0, width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 5120, componentCount: 1},
    'myriahedral-pacific': {family: 'myriahedral', frame: {x: 0, y: 0, width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 5120, componentCount: 1},
    'myriahedral-antarctic': {family: 'myriahedral', frame: {x: 0, y: 0, width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 5120, componentCount: 1},
    'star-x': {family: 'star-x', frame: {x: 0, y: 0, width: 34, height: 44}, cutTopology: 'folded', inverseMode: 'candidates', nativeCellCount: 8, componentCount: 2},
    voronoi: {family: 'voronoi', frame: {x: 0, y: 0, width: 44, height: 22.916667}, cutTopology: 'polyhedral', inverseMode: 'face-qualified', nativeCellCount: 20, componentCount: 1}
});

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function command(program, args, {acceptDifference = false} = {}) {
    try {
        const result = await execFileAsync(program, args, {
            cwd: root,
            encoding: 'utf8',
            maxBuffer: 16 * 1024 * 1024
        });
        return `${result.stdout ?? ''}${result.stderr ?? ''}`.trim();
    } catch (error) {
        if (acceptDifference && error.code === 1) {
            return `${error.stdout ?? ''}${error.stderr ?? ''}`.trim();
        }
        throw new Error(`${program} failed (${error.code ?? 'unknown'}): ${error.stderr ?? error.message}`);
    }
}

async function sha256(file) {
    const hash = createHash('sha256');
    for await (const chunk of createReadStream(file)) hash.update(chunk);
    return hash.digest('hex');
}

function relative(file) {
    return path.relative(root, file).split(path.sep).join('/');
}

async function fileRecord(file, mediaType, authorityClass, extra = {}) {
    const stat = await fs.stat(file);
    return {
        path: relative(file),
        mediaType,
        bytes: stat.size,
        sha256: await sha256(file),
        authorityClass,
        ...extra
    };
}

async function imageDimensions(file) {
    const output = await command('identify', ['-format', '%w %h', file]);
    const [width, height] = output.split(/\s+/).map(Number);
    requireCondition(Number.isInteger(width) && Number.isInteger(height),
        `could not identify ${file}`);
    return {width, height};
}

async function resizedDimensions(file) {
    const output = await command('magick', [
        file, '-filter', 'Lanczos', '-resize', `${canvas.width}x${canvas.height}`,
        '-format', '%w %h', 'info:'
    ]);
    const [width, height] = output.split(/\s+/).map(Number);
    requireCondition(Number.isInteger(width) && Number.isInteger(height),
        `could not calculate resized dimensions for ${file}`);
    return {width, height};
}

async function verifyLossless(png, webp) {
    const difference = await command('compare', ['-metric', 'AE', png, webp, 'null:'], {
        acceptDifference: true
    });
    const absoluteError = Number(difference.match(/^\s*([0-9]+)/)?.[1] ?? 0);
    requireCondition(absoluteError === 0,
        `lossless WebP pixel mismatch for ${webp}: ${difference}`);
}

function xmlText(value) {
    return value.replace(/<[^>]+>/g, ' ').replace(/&quot;/g, '"')
        .replace(/&apos;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
}

function attribute(tag, name) {
    const match = new RegExp(`(?:^|\\s)${name}="([^"]*)"`).exec(tag);
    return match ? xmlText(match[1]) : null;
}

async function readXmlPrefix(file, maximum = 256 * 1024) {
    const source = createReadStream(file);
    const stream = file.endsWith('.gz') ? source.pipe(createGunzip()) : source;
    const chunks = [];
    let length = 0;
    try {
        for await (const chunk of stream) {
            chunks.push(chunk);
            length += chunk.length;
            if (length >= maximum) break;
        }
    } finally {
        stream.destroy();
        source.destroy();
    }
    return Buffer.concat(chunks, length).subarray(0, maximum).toString('utf8');
}

function svgMetadata(prefix, file) {
    const svgTag = /<svg\b[\s\S]*?>/.exec(prefix)?.[0];
    requireCondition(svgTag, `missing SVG root tag in ${file}`);
    const viewBox = attribute(svgTag, 'viewBox')?.split(/[ ,]+/).map(Number);
    requireCondition(viewBox?.length === 4 && viewBox.every(Number.isFinite)
        && viewBox[2] > 0 && viewBox[3] > 0, `invalid viewBox in ${file}`);
    const title = xmlText(/<title\b[^>]*>([\s\S]*?)<\/title>/.exec(prefix)?.[1] ?? '');
    const description = xmlText(/<desc\b[^>]*>([\s\S]*?)<\/desc>/.exec(prefix)?.[1] ?? '');
    const metadataTag = /<metadata\b[^>]*>/.exec(prefix)?.[0] ?? '';
    const sourcePeriod = attribute(metadataTag, 'data-reference-period')
        ?? attribute(metadataTag, 'data-timestamp')
        ?? attribute(metadataTag, 'data-source-date')
        ?? attribute(metadataTag, 'data-snapshot-as-of')
        ?? 'UNAVAILABLE';
    const opacityValue = Number(attribute(metadataTag, 'data-graphic-opacity'));
    const missingIsZero = attribute(metadataTag, 'data-missing-is-zero');
    return {
        frame: {x: viewBox[0], y: viewBox[1], width: viewBox[2], height: viewBox[3]},
        title,
        description,
        sourcePeriod,
        graphicOpacity: Number.isFinite(opacityValue) ? opacityValue : 'UNAVAILABLE',
        missingData: missingIsZero === null ? 'UNAVAILABLE'
            : (missingIsZero === 'true' ? 'missing-is-zero' : 'missing-is-not-zero')
    };
}

function displayName(value) {
    return value.split('-').map(word => word === 'ck' ? 'CK'
        : `${word.slice(0, 1).toUpperCase()}${word.slice(1)}`).join(' ');
}

function passYear(passId) {
    const values = [...passId.matchAll(/(?:^|-)((?:19|20)\d{2})(?=-|$)/g)];
    return values.length ? Number(values.at(-1)[1]) : null;
}

async function existingSvg(entry) {
    const source = path.join(root, entry.sourceSvg);
    const archive = `${source}.gz`;
    if (entry.passId.startsWith('resources-')) {
        await fs.access(archive);
        return {file: archive, mediaType: 'application/gzip',
            extra: {contentMediaType: 'image/svg+xml', contentEncoding: 'gzip'}};
    }
    await fs.access(source);
    return {file: source, mediaType: 'image/svg+xml', extra: {}};
}

function parentPath(entry, kind, extension) {
    return path.join(root, entry.sourceSvg.replace('/svg/', `/${kind}/`)
        .replace(/\.svg$/, extension));
}

async function processArtifact(entry, index, total) {
    const definition = projectionDefinitions[entry.projectionId];
    requireCondition(definition && definition.family === entry.family,
        `projection definition missing for ${entry.id}`);
    const svg = await existingSvg(entry);
    const parentPng = parentPath(entry, 'png', '.png');
    const parentPdf = parentPath(entry, 'pdf', '.pdf');
    const projectionDirectory = entry.sourceSvg.split('/')[1];
    const outputPng = path.join(generated, projectionDirectory, 'screen-1080p', `${entry.stem}.png`);
    const outputWebp = path.join(generated, projectionDirectory, 'screen-1080p-webp', `${entry.stem}.webp`);
    const [prefix, sourceHashes, sourceDimensions, contentSize] = await Promise.all([
        readXmlPrefix(svg.file),
        Promise.all([parentPng, svg.file, parentPdf].map(sha256)),
        imageDimensions(parentPng),
        resizedDimensions(parentPng)
    ]);
    const metadata = svgMetadata(prefix, svg.file);
    const transform = containTransform(metadata.frame, canvas, {background, contentSize});

    await command('magick', [
        parentPng,
        '-filter', 'Lanczos',
        '-resize', `${contentSize.width}x${contentSize.height}!`,
        '-gravity', 'center',
        '-background', background,
        '-alpha', 'remove',
        '-extent', `${canvas.width}x${canvas.height}`,
        '-colorspace', 'sRGB',
        '-strip',
        '-depth', '8',
        '-define', 'png:compression-level=9',
        '-define', 'png:exclude-chunks=date,time',
        outputPng
    ]);
    await command('magick', [
        outputPng,
        '-define', 'webp:lossless=true',
        '-quality', '100',
        '-strip',
        outputWebp
    ]);
    const [pngDimensions, webpDimensions] = await Promise.all([
        imageDimensions(outputPng), imageDimensions(outputWebp)
    ]);
    requireCondition(pngDimensions.width === canvas.width && pngDimensions.height === canvas.height
        && webpDimensions.width === canvas.width && webpDimensions.height === canvas.height,
    `wrong screen dimensions for ${entry.stem}`);
    await verifyLossless(outputPng, outputWebp);
    const afterHashes = await Promise.all([parentPng, svg.file, parentPdf].map(sha256));
    requireCondition(sourceHashes.every((value, hashIndex) => value === afterHashes[hashIndex]),
        `consumer generation modified an authoritative parent for ${entry.stem}`);

    const year = passYear(entry.passId);
    const title = metadata.title && metadata.title !== entry.stem
        ? metadata.title : `${displayName(entry.passId)} — ${displayName(entry.projectionId)}`;
    const altText = metadata.description || `${displayName(entry.passId)} plate in the ${displayName(entry.projectionId)} projection.`;
    const parents = await Promise.all([
        fileRecord(svg.file, svg.mediaType, 'archive-art-master', svg.extra),
        fileRecord(parentPdf, 'application/pdf', 'print-presentation', {role: 'print-master'}),
        fileRecord(parentPng, 'image/png', 'full-raster', {
            dimensions: sourceDimensions, colorSpace: 'sRGB', transparency: 'UNAVAILABLE', role: 'full-raster-parent'
        }),
        fileRecord(outputPng, 'image/png', 'access-derivative', {
            dimensions: canvas, lossless: true, colorSpace: 'sRGB', transparency: 'opaque', role: 'screen'
        }),
        fileRecord(outputWebp, 'image/webp', 'access-derivative', {
            dimensions: canvas, lossless: true, colorSpace: 'sRGB', transparency: 'opaque', role: 'screen'
        })
    ]);
    if ((index + 1) % 10 === 0 || index + 1 === total) {
        console.log(`[screen ${index + 1}/${total}] ${entry.id}`);
    }
    return {
        id: entry.id,
        title,
        altText,
        pass: {
            id: entry.passId,
            lifecycle: entry.lifecycle,
            sourcePeriod: metadata.sourcePeriod,
            ...(year ? {year} : {})
        },
        projection: {
            id: entry.projectionId,
            family: entry.family,
            layoutId: entry.layoutId,
            nativeFrame: definition.frame,
            artifactFrame: metadata.frame,
            cutTopology: definition.cutTopology,
            inverseMode: definition.inverseMode,
            nativeCellCount: definition.nativeCellCount,
            componentCount: definition.componentCount
        },
        slice: entry.sliceId ? {id: entry.sliceId, approval: 'standard-approved'} : null,
        evidence: {
            sourcePeriod: metadata.sourcePeriod,
            licenseSpdx: 'UNAVAILABLE',
            attribution: 'UNAVAILABLE',
            graphicOpacity: metadata.graphicOpacity,
            missingData: metadata.missingData,
            governance: 'UNAVAILABLE'
        },
        accessibility: {
            altTextStatus: 'deterministic-source-metadata',
            visualReviewStatus: 'pending-human-review'
        },
        parents: {svg: parents[0], pdf: parents[1], fullPng: parents[2]},
        screen: {
            authorityClass: 'access-derivative',
            recipeVersion,
            parentFullPngSha256: parents[2].sha256,
            canvas,
            fit: 'contain',
            background,
            contentRectangle: transform.contentRectangle,
            projectedToScreen: transform.projectedToScreen,
            screenToProjected: transform.screenToProjected,
            png: parents[3],
            webp: parents[4]
        },
        limitations: [
            'Access derivative only; the layered SVG and physical-size PDF remain authoritative.',
            'Interrupted flat map; do not wrap as an equirectangular globe texture.',
            'Inverse picking may return cut or ambiguous candidates and must preserve native-cell/component semantics.',
            ...(entry.sliceId ? ['Slice picking uses the original carrier coordinates; the catalog does not provide a per-pixel topology mask.'] : [])
        ]
    };
}

async function mapLimit(values, limit, callback) {
    const result = new Array(values.length);
    let next = 0;
    async function worker() {
        while (true) {
            const index = next++;
            if (index >= values.length) return;
            result[index] = await callback(values[index], index, values.length);
        }
    }
    await Promise.all(Array.from({length: Math.min(limit, values.length)}, worker));
    return result;
}

requireCondition(Number.isInteger(jobs) && jobs > 0 && jobs <= 32,
    'SCREEN_JOBS must be an integer from 1 through 32');
const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
requireCondition(manifest.schemaVersion === 'cartofreako-standard-artifact-manifest-v1'
    && manifest.lifecycle === 'standard'
    && manifest.artifactCount === manifest.artifacts.length,
'invalid standard artifact manifest');
for (const directory of [
    ...new Set(manifest.artifacts.map(entry => path.join(generated,
        entry.sourceSvg.split('/')[1], 'screen-1080p'))),
    ...new Set(manifest.artifacts.map(entry => path.join(generated,
        entry.sourceSvg.split('/')[1], 'screen-1080p-webp'))),
    path.join(generated, 'catalog')
]) await fs.mkdir(directory, {recursive: true});

const artifacts = await mapLimit(manifest.artifacts, jobs, processArtifact);
artifacts.sort((left, right) => left.id.localeCompare(right.id, 'en'));
const status = await command('git', ['status', '--short']);
const catalog = {
    schema: 'cartofreako-artifacts-v1',
    catalogVersion: 1,
    consumerProfile: {
        id: 'screen-1080p-lossless-v1',
        canvas,
        fit: 'contain',
        background,
        recipeVersion
    },
    sourceRevision: {
        gitCommit: await command('git', ['rev-parse', 'HEAD']),
        workingTree: status === '' ? 'clean' : 'modified',
        runtimeApi: 3,
        geometryAbi: 1,
        standardManifest: relative(manifestPath),
        standardManifestSha256: await sha256(manifestPath)
    },
    artifacts
};
const catalogPath = path.join(generated, 'catalog', 'artifacts-v1.json');
await fs.writeFile(catalogPath, `${JSON.stringify(catalog, null, 2)}\n`, 'utf8');
console.log(`Generated ${artifacts.length} checked 1080p PNG/WebP pairs with ${jobs} workers and ${relative(catalogPath)}.`);

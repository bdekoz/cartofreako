#!/usr/bin/env node

import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

import {containTransform} from '../src.wasm/cartofreako-screen.mjs';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const generated = path.join(root, 'assets.generated');
const canvas = Object.freeze({width: 1920, height: 1080});
const background = '#f4f5f5';
const recipeVersion = 1;

const projections = Object.freeze([
    {id: 'cahill-keyes', suffix: 'ck-44-22', frame: {width: 44, height: 22}, cutTopology: 'folded', inverseMode: 'face-qualified'},
    {id: 'authagraph', suffix: 'authagraph-44-19.052559', frame: {width: 44, height: 19.052559}, cutTopology: 'periodic', inverseMode: 'face-qualified'},
    {id: 'dymaxion', suffix: 'dymaxion-44-20.78461', frame: {width: 44, height: 20.78461}, cutTopology: 'polyhedral', inverseMode: 'face-qualified'},
    {id: 'myriahedral', suffix: 'myriahedral-44-24.75', frame: {width: 44, height: 24.75}, cutTopology: 'polyhedral', inverseMode: 'face-qualified'},
    {id: 'star-x', suffix: 'star-x-34-44', frame: {width: 34, height: 44}, cutTopology: 'folded', inverseMode: 'candidates'},
    {id: 'voronoi', suffix: 'voronoi-44-22.916667', frame: {width: 44, height: 22.916667}, cutTopology: 'polyhedral', inverseMode: 'face-qualified'}
]);

const passDefinitions = Object.freeze({
    water: {title: 'Water', lifecycle: 'standard'},
    'anthropocene-temperature-2026': {title: 'Anthropocene Temperature / 2026 Partial Year', lifecycle: 'standard', year: 2026},
    'network-infrastructure-sites': {title: 'Network Infrastructure Sites', lifecycle: 'standard'},
    'bathymetry-roulette': {title: 'Bathymetry Roulette', lifecycle: 'standard'}
});

function command(program, args, {acceptDifference = false} = {}) {
    const result = spawnSync(program, args, {cwd: root, encoding: 'utf8'});
    if (result.error) throw result.error;
    if (result.status !== 0 && !(acceptDifference && result.status === 1)) {
        throw new Error(`${program} failed (${result.status}): ${result.stderr || result.stdout}`);
    }
    return `${result.stdout ?? ''}${result.stderr ?? ''}`.trim();
}

async function sha256(file) {
    const hash = createHash('sha256');
    hash.update(await fs.readFile(file));
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

function imageDimensions(file) {
    const output = command('identify', ['-format', '%w %h', file]);
    const [width, height] = output.split(/\s+/).map(Number);
    if (!Number.isInteger(width) || !Number.isInteger(height)) {
        throw new Error(`could not identify ${file}`);
    }
    return {width, height};
}

function resizedDimensions(file) {
    const output = command('magick', [
        file, '-filter', 'Lanczos', '-resize', `${canvas.width}x${canvas.height}`,
        '-format', '%w %h', 'info:'
    ]);
    const [width, height] = output.split(/\s+/).map(Number);
    return {width, height};
}

function verifyLossless(png, webp) {
    const difference = command('compare', ['-metric', 'AE', png, webp, 'null:'], {
        acceptDifference: true
    });
    const absoluteError = Number(difference.match(/^\s*([0-9]+)/)?.[1]);
    if (absoluteError !== 0) {
        throw new Error(`lossless WebP pixel mismatch for ${webp}: ${difference}`);
    }
}

function gitOutput(args) {
    return command('git', args);
}

const requestedPasses = (() => {
    const argument = process.argv.find((value) => value.startsWith('--passes='));
    const values = argument ? argument.slice('--passes='.length).split(',') : Object.keys(passDefinitions);
    for (const value of values) {
        if (!passDefinitions[value]) throw new Error(`unknown v1 screen pass: ${value}`);
    }
    return values;
})();

const artifacts = [];
for (const projection of projections) {
    const pngDirectory = path.join(generated, projection.id, 'png');
    const svgDirectory = path.join(generated, projection.id, 'svg');
    const pdfDirectory = path.join(generated, projection.id, 'pdf');
    const screenPngDirectory = path.join(generated, projection.id, 'screen-1080p');
    const screenWebpDirectory = path.join(generated, projection.id, 'screen-1080p-webp');
    await fs.mkdir(screenPngDirectory, {recursive: true});
    await fs.mkdir(screenWebpDirectory, {recursive: true});

    for (const passId of requestedPasses) {
        const stem = `${passId}-${projection.suffix}`;
        const parentPng = path.join(pngDirectory, `${stem}.png`);
        const parentSvg = path.join(svgDirectory, `${stem}.svg`);
        const parentPdf = path.join(pdfDirectory, `${stem}.pdf`);
        const outputPng = path.join(screenPngDirectory, `${stem}.png`);
        const outputWebp = path.join(screenWebpDirectory, `${stem}.webp`);
        const sourceHashes = await Promise.all([parentPng, parentSvg, parentPdf].map(sha256));
        const sourceDimensions = imageDimensions(parentPng);
        const contentSize = resizedDimensions(parentPng);
        const transform = containTransform(projection.frame, canvas, {background, contentSize});

        command('magick', [
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
        command('magick', [
            outputPng,
            '-define', 'webp:lossless=true',
            '-quality', '100',
            '-strip',
            outputWebp
        ]);
        const pngDimensions = imageDimensions(outputPng);
        const webpDimensions = imageDimensions(outputWebp);
        if (pngDimensions.width !== canvas.width || pngDimensions.height !== canvas.height
            || webpDimensions.width !== canvas.width || webpDimensions.height !== canvas.height) {
            throw new Error(`wrong screen dimensions for ${stem}`);
        }
        verifyLossless(outputPng, outputWebp);
        const afterHashes = await Promise.all([parentPng, parentSvg, parentPdf].map(sha256));
        if (sourceHashes.some((value, index) => value !== afterHashes[index])) {
            throw new Error(`consumer generation modified an authoritative parent for ${stem}`);
        }

        const pass = passDefinitions[passId];
        artifacts.push({
            id: `${passId}.${projection.id}.whole-map`,
            title: `${pass.title} — ${projection.id}`,
            altText: `${pass.title} plate in the ${projection.id} projection, contain-fit without cropping on a 1920 by 1080 light-gray canvas.`,
            pass: {id: passId, lifecycle: pass.lifecycle, ...(pass.year ? {year: pass.year} : {})},
            projection: {
                id: projection.id,
                nativeFrame: projection.frame,
                cutTopology: projection.cutTopology,
                inverseMode: projection.inverseMode
            },
            parents: {
                svg: await fileRecord(parentSvg, 'image/svg+xml', 'archive-art-master'),
                pdf: await fileRecord(parentPdf, 'application/pdf', 'print-presentation'),
                fullPng: await fileRecord(parentPng, 'image/png', 'full-raster', {dimensions: sourceDimensions})
            },
            screen: {
                authorityClass: 'access-derivative',
                canvas,
                fit: 'contain',
                background,
                contentRectangle: transform.contentRectangle,
                projectedToScreen: transform.projectedToScreen,
                screenToProjected: transform.screenToProjected,
                png: await fileRecord(outputPng, 'image/png', 'access-derivative', {dimensions: canvas, lossless: true}),
                webp: await fileRecord(outputWebp, 'image/webp', 'access-derivative', {dimensions: canvas, lossless: true})
            },
            limitations: [
                'Access derivative only; the layered SVG and physical-size PDF remain authoritative.',
                'Interrupted flat map; do not wrap as an equirectangular globe texture.',
                'Inverse picking may return cut or ambiguous candidates and must preserve native-cell/component semantics.'
            ]
        });
    }
}

artifacts.sort((left, right) => left.id.localeCompare(right.id));
const status = gitOutput(['status', '--short']);
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
        gitCommit: gitOutput(['rev-parse', 'HEAD']),
        workingTree: status === '' ? 'clean' : 'modified',
        runtimeApi: 3,
        geometryAbi: 1
    },
    artifacts
};
const catalogDirectory = path.join(generated, 'catalog');
await fs.mkdir(catalogDirectory, {recursive: true});
const catalogPath = path.join(catalogDirectory, 'artifacts-v1.json');
await fs.writeFile(catalogPath, JSON.stringify(catalog, null, 2) + '\n', 'utf8');
console.log(`Generated ${artifacts.length} checked 1080p PNG/WebP pairs and ${relative(catalogPath)}.`);

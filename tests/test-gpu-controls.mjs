#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

import {projectedToScreen, screenToProjected} from '../src.wasm/cartofreako-screen.mjs';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const inputPath = path.join(root, 'fixtures/gpu-benchmark/v1/stage-14-inputs.json');
const catalogPath = path.join(root, 'assets.generated/catalog/gpu-controls-v1.json');

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function sha256(file) {
    const bytes = await fs.readFile(file);
    return createHash('sha256').update(bytes).digest('hex');
}

async function pngDimensions(file) {
    const handle = await fs.open(file, 'r');
    try {
        const bytes = Buffer.alloc(24);
        const {bytesRead} = await handle.read(bytes, 0, bytes.length, 0);
        requireCondition(bytesRead === 24
            && bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex')),
        `${file} is not a PNG`);
        return {width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20)};
    } finally {
        await handle.close();
    }
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

const inputBytes = await fs.readFile(inputPath);
const input = JSON.parse(inputBytes);
const catalog = JSON.parse(await fs.readFile(catalogPath));
requireCondition(catalog.schemaVersion === 'cartofreako-gpu-benchmark-v1'
    && catalog.documentType === 'control-catalog'
    && catalog.lifecycle === 'exploration-only',
'wrong GPU control catalog identity');
requireCondition(catalog.inputFreeze.sha256
    === createHash('sha256').update(inputBytes).digest('hex'),
'GPU controls refer to the wrong input freeze');
requireCondition(catalog.inputFreeze.sourceCommit
    === input.frozenStage14.sourceCommit
    && catalog.artifacts.length === 211,
'GPU controls do not preserve the Stage 14 handoff');
requireCondition(JSON.stringify(catalog.recipes) === JSON.stringify(input.controlRecipes),
    'GPU control recipes changed');
requireCondition(new Set(catalog.artifacts.map(value => value.id)).size === 211,
    'GPU control artifact IDs are not unique');
requireCondition(new Set(catalog.artifacts.map(value => value.layoutId)).size === 11,
    'GPU controls do not cover all eleven approved layouts');
requireCondition(catalog.artifacts.filter(value => value.sliceId !== null).length === 14,
    'GPU controls do not cover all fourteen approved slices');

const inputs = new Map(input.cases.map(value => [value.id, value]));
const fileChecks = [];
for (const artifact of catalog.artifacts) {
    const source = inputs.get(artifact.id);
    requireCondition(source && artifact.controls.length === 2,
        `${artifact.id} does not have both controls`);
    requireCondition(artifact.passId === source.passId
        && artifact.projectionId === source.projectionId
        && artifact.layoutId === source.layoutId
        && artifact.sliceId === source.sliceId,
    `${artifact.id} source identity changed`);
    for (const [index, control] of artifact.controls.entries()) {
        const recipe = input.controlRecipes[index];
        requireCondition(control.recipeId === recipe.id
            && control.canvas.width === recipe.canvas.width
            && control.canvas.height === recipe.canvas.height,
        `${artifact.id} recipe order or canvas changed`);
        requireCondition(control.parentFullPngSha256 === source.parents.fullPng.sha256,
            `${artifact.id} was not derived from its authoritative full PNG`);
        const box = control.contentRectangle;
        requireCondition(box.x >= 0 && box.y >= 0
            && box.x + box.width <= control.canvas.width
            && box.y + box.height <= control.canvas.height,
        `${artifact.id} ${control.recipeId} crops its projection`);
        const center = [
            source.artifactFrame.x + source.artifactFrame.width / 2,
            source.artifactFrame.y + source.artifactFrame.height / 2
        ];
        const screen = projectedToScreen(center, control);
        const roundTrip = screenToProjected(screen, control);
        requireCondition(Math.hypot(roundTrip[0] - center[0], roundTrip[1] - center[1]) < 1e-10,
            `${artifact.id} ${control.recipeId} affine round trip failed`);
        fileChecks.push({artifact, control});
    }
}
await mapLimit(fileChecks, 12, async ({artifact, control}) => {
    const file = path.join(root, control.png.path);
    const [hash, dimensions, stat] = await Promise.all([
        sha256(file), pngDimensions(file), fs.stat(file)
    ]);
    requireCondition(hash === control.png.sha256 && stat.size === control.png.bytes,
        `${artifact.id} hash or size mismatch for ${control.recipeId}`);
    requireCondition(dimensions.width === control.canvas.width
        && dimensions.height === control.canvas.height
        && control.png.dimensions.width === control.canvas.width
        && control.png.dimensions.height === control.canvas.height,
    `${artifact.id} PNG dimensions mismatch for ${control.recipeId}`);
    requireCondition(control.png.mediaType === 'image/png'
        && control.png.authorityClass === 'exploration-control'
        && control.png.lossless === true
        && control.png.colorSpace === 'sRGB'
        && control.png.transparency === 'opaque',
    `${artifact.id} delivery metadata changed for ${control.recipeId}`);
});

console.log('Stage 15B controls passed: 422 lossless PNGs, 211 artifacts, 11 layouts, 14 slices, both orientations, no crop, and frozen-parent linkage.');

#!/usr/bin/env node

import {execFile} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createReadStream} from 'node:fs';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {promisify} from 'node:util';

import {containTransform} from '../src.wasm/cartofreako-screen.mjs';

const execFileAsync = promisify(execFile);
const root = path.resolve(new URL('..', import.meta.url).pathname);
const generated = path.join(root, 'assets.generated');
const inputPath = path.join(root, 'fixtures/gpu-benchmark/v1/stage-14-inputs.json');
const catalogPath = path.join(generated, 'catalog/gpu-controls-v1.json');
const defaultJobs = Math.min(4, os.availableParallelism?.() ?? os.cpus().length ?? 1);
const jobs = Number(process.env.GPU_CONTROL_JOBS ?? defaultJobs);

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function command(program, args) {
    try {
        return await execFileAsync(program, args, {
            cwd: root,
            encoding: 'utf8',
            maxBuffer: 16 * 1024 * 1024
        });
    } catch (error) {
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

async function imageDimensions(file) {
    const {stdout} = await command('identify', ['-format', '%w %h', file]);
    const [width, height] = stdout.trim().split(/\s+/).map(Number);
    requireCondition(Number.isInteger(width) && Number.isInteger(height),
        `could not identify ${relative(file)}`);
    return {width, height};
}

async function resizedDimensions(file, canvas) {
    const {stdout} = await command('magick', [
        file, '-filter', 'Lanczos', '-resize', `${canvas.width}x${canvas.height}`,
        '-format', '%w %h', 'info:'
    ]);
    const [width, height] = stdout.trim().split(/\s+/).map(Number);
    requireCondition(Number.isInteger(width) && Number.isInteger(height),
        `could not calculate resized dimensions for ${relative(file)}`);
    return {width, height};
}

async function fileRecord(file, dimensions) {
    const stat = await fs.stat(file);
    return {
        path: relative(file),
        mediaType: 'image/png',
        bytes: stat.size,
        sha256: await sha256(file),
        authorityClass: 'exploration-control',
        dimensions,
        lossless: true,
        colorSpace: 'sRGB',
        transparency: 'opaque'
    };
}

async function mapLimit(values, limit, callback) {
    const output = new Array(values.length);
    let next = 0;
    async function worker() {
        while (true) {
            const index = next++;
            if (index >= values.length) return;
            output[index] = await callback(values[index], index, values.length);
        }
    }
    await Promise.all(Array.from({length: Math.min(limit, values.length)}, worker));
    return output;
}

function outputDirectory(recipe) {
    return recipe.id.replace(/-v1$/, '');
}

async function generateControl(input, recipe) {
    const parent = path.join(root, input.parents.fullPng.path);
    const projectionDirectory = input.parents.fullPng.path.split('/')[1];
    const basename = path.basename(input.parents.fullPng.path);
    const output = path.join(generated, projectionDirectory,
        outputDirectory(recipe), basename);
    const temporary = `${output}.tmp-${process.pid}.png`;
    const [parentHash, contentSize] = await Promise.all([
        sha256(parent), resizedDimensions(parent, recipe.canvas)
    ]);
    requireCondition(parentHash === input.parents.fullPng.sha256,
        `${input.id} authoritative parent hash changed`);
    const transform = containTransform(input.artifactFrame, recipe.canvas, {
        background: recipe.background,
        contentSize
    });
    await command('magick', [
        parent,
        '-filter', recipe.filter,
        '-resize', `${contentSize.width}x${contentSize.height}!`,
        '-gravity', 'center',
        '-background', recipe.background,
        '-alpha', 'remove',
        '-extent', `${recipe.canvas.width}x${recipe.canvas.height}`,
        '-colorspace', recipe.colorSpace,
        '-strip',
        '-depth', String(recipe.depth),
        '-define', 'png:compression-level=9',
        '-define', 'png:exclude-chunks=date,time',
        temporary
    ]);
    await fs.rename(temporary, output);
    const dimensions = await imageDimensions(output);
    requireCondition(dimensions.width === recipe.canvas.width
        && dimensions.height === recipe.canvas.height,
    `${input.id} ${recipe.id} dimensions are wrong`);
    requireCondition(await sha256(parent) === parentHash,
        `${input.id} generation modified its authoritative parent`);
    return {
        recipeId: recipe.id,
        parentFullPngSha256: parentHash,
        canvas: recipe.canvas,
        contentRectangle: transform.contentRectangle,
        projectedToScreen: transform.projectedToScreen,
        screenToProjected: transform.screenToProjected,
        png: await fileRecord(output, dimensions)
    };
}

requireCondition(Number.isInteger(jobs) && jobs > 0 && jobs <= 32,
    'GPU_CONTROL_JOBS must be an integer from 1 through 32');
const inputBytes = await fs.readFile(inputPath);
const input = JSON.parse(inputBytes);
requireCondition(input.schemaVersion === 'cartofreako-gpu-benchmark-v1'
    && input.documentType === 'input-freeze'
    && input.lifecycle === 'exploration-only'
    && input.frozenStage14.workingTree === 'clean'
    && input.cases.length === input.frozenStage14.artifactCount,
'invalid Stage 15A input freeze');
for (const directory of new Set(input.cases.flatMap(value =>
    input.controlRecipes.map(recipe => path.join(generated,
        value.parents.fullPng.path.split('/')[1], outputDirectory(recipe)))))) {
    await fs.mkdir(directory, {recursive: true});
}
await fs.mkdir(path.dirname(catalogPath), {recursive: true});

const artifacts = await mapLimit(input.cases, jobs, async (value, index, total) => {
    const controls = [];
    for (const recipe of input.controlRecipes) {
        controls.push(await generateControl(value, recipe));
    }
    if ((index + 1) % 10 === 0 || index + 1 === total) {
        console.log(`[gpu-control ${index + 1}/${total}] ${value.id}`);
    }
    return {
        id: value.id,
        passId: value.passId,
        projectionId: value.projectionId,
        layoutId: value.layoutId,
        sliceId: value.sliceId,
        controls
    };
});
artifacts.sort((left, right) => left.id.localeCompare(right.id, 'en'));
const catalog = {
    schemaVersion: 'cartofreako-gpu-benchmark-v1',
    documentType: 'control-catalog',
    lifecycle: 'exploration-only',
    inputFreeze: {
        path: relative(inputPath),
        sha256: createHash('sha256').update(inputBytes).digest('hex'),
        sourceCommit: input.frozenStage14.sourceCommit,
        artifactCount: input.cases.length
    },
    recipes: input.controlRecipes,
    artifacts
};
await fs.writeFile(catalogPath, `${JSON.stringify(catalog, null, 2)}\n`, 'utf8');
console.log(`Generated ${artifacts.length * input.controlRecipes.length} lossless 2K controls with ${jobs} workers and ${relative(catalogPath)}.`);

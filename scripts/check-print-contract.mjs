#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const contractPath = path.resolve(root, process.argv[2] ?? 'contracts/print-products-v1.json');
const contract = JSON.parse(await fs.readFile(contractPath, 'utf8'));

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function close(left, right, tolerance) {
    return Number.isFinite(left) && Number.isFinite(right)
        && Math.abs(left - right) <= tolerance;
}

async function prefix(file, bytes = 16384) {
    const handle = await fs.open(file, 'r');
    try {
        const buffer = Buffer.alloc(bytes);
        const {bytesRead} = await handle.read(buffer, 0, bytes, 0);
        return buffer.subarray(0, bytesRead).toString('utf8');
    } finally {
        await handle.close();
    }
}

requireCondition(contract.schema === 'cartofreako-print-products-v1', 'wrong print contract schema');
requireCondition(contract.units === 'inches', 'print contract units must be inches');
requireCondition(Array.isArray(contract.projections) && contract.projections.length === 6,
    'print contract must contain six reference projections');
requireCondition(contract.a0?.widthMillimeters === 841
    && contract.a0?.heightMillimeters === 1189
    && contract.a0?.imposition === 'contain-centered', 'A0 dimension contract changed');

const a0Portrait = {
    width: contract.a0.widthMillimeters / 25.4,
    height: contract.a0.heightMillimeters / 25.4
};
const a0Landscape = {width: a0Portrait.height, height: a0Portrait.width};
const ids = new Set();
for (const projection of contract.projections) {
    requireCondition(!ids.has(projection.id), `duplicate projection ${projection.id}`);
    ids.add(projection.id);
    requireCondition(projection[projection.leadingEdge] === 44,
        `${projection.id} no longer has a 44-inch leading edge`);
    requireCondition(projection.outputTag && projection.representativeStem,
        `${projection.id} lacks a stable output tag or representative`);

    const svg = path.join(root, 'assets.generated', projection.id, 'svg',
        `${projection.representativeStem}.svg`);
    const header = await prefix(svg);
    const tag = header.match(/<svg\b[\s\S]*?>/)?.[0];
    requireCondition(tag, `${svg} has no opening SVG element in its header`);
    const width = Number(tag.match(/\bwidth="([0-9.]+)in"/)?.[1]);
    const height = Number(tag.match(/\bheight="([0-9.]+)in"/)?.[1]);
    const viewBox = tag.match(/\bviewBox="0 0 ([0-9.]+) ([0-9.]+)"/);
    requireCondition(close(width, projection.width, contract.svgToleranceInches),
        `${svg} width ${width} does not match ${projection.width}`);
    requireCondition(close(height, projection.height, contract.svgToleranceInches),
        `${svg} height ${height} does not match ${projection.height}`);
    requireCondition(viewBox
        && close(Number(viewBox[1]), projection.width, contract.svgToleranceInches)
        && close(Number(viewBox[2]), projection.height, contract.svgToleranceInches),
    `${svg} viewBox does not match its physical page`);

    const a0 = projection.width >= projection.height ? a0Landscape : a0Portrait;
    const scale = Math.min(a0.width / projection.width, a0.height / projection.height);
    requireCondition(projection.width * scale <= a0.width + 1e-12
        && projection.height * scale <= a0.height + 1e-12,
    `${projection.id} cannot be contained on the declared A0 orientation`);
}

const makefile = await fs.readFile(path.join(root, 'Makefile'), 'utf8');
const generatedBlock = makefile.match(/GENERATED_ARTIFACTS := \\\n([\s\S]*?)\n\nGENERATOR_BINARIES/);
requireCondition(generatedBlock && !generatedBlock[0].includes('screen-1080p'),
    'screen derivatives entered the authoritative generated-artifact graph');
requireCondition(/all: \$\(GENERATED_ARTIFACTS\)/.test(makefile),
    'make all no longer resolves through the authoritative artifact inventory');

console.log('print contract: six exact-ratio SVG products, 44-inch leading edges, A0 contain geometry, and derivative separation passed');

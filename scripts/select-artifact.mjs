#!/usr/bin/env node

import fs from 'node:fs/promises';
import process from 'node:process';

import {selectArtifact} from '../src.wasm/cartofreako-catalog.mjs';

function usage() {
    console.error('usage: scripts/select-artifact.mjs REQUEST.json CATALOG.json [RECEIPT.json]');
    process.exit(2);
}

if (process.argv.length < 4 || process.argv.length > 5) usage();
const [requestPath, catalogPath, outputPath] = process.argv.slice(2);
const [requestBytes, catalogBytes] = await Promise.all([
    fs.readFile(requestPath), fs.readFile(catalogPath)
]);
const receipt = await selectArtifact(JSON.parse(requestBytes), JSON.parse(catalogBytes), {
    catalogBytes
});
const output = `${JSON.stringify(receipt, null, 2)}\n`;
if (outputPath) await fs.writeFile(outputPath, output);
else process.stdout.write(output);

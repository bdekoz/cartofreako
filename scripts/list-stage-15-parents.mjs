#!/usr/bin/env node

// Print the authoritative Stage 14 full-PNG parent paths retained by the
// frozen GPU benchmark fixture.  The Makefile consumes this list as real
// prerequisites so a host with an empty or partial assets.generated tree
// builds every required parent before rendering GPU controls.
import fs from 'node:fs/promises';
import path from 'node:path';

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

const root = path.resolve(new URL('..', import.meta.url).pathname);
const fixturePath = path.join(root, 'fixtures/gpu-benchmark/v1/stage-14-inputs.json');
const fixture = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
requireCondition(fixture.documentType === 'input-freeze'
    && fixture.frozenStage14.artifactCount === fixture.cases.length,
'invalid Stage 15A input freeze');

for (const value of fixture.cases) {
    process.stdout.write(`${value.parents.fullPng.path}\n`);
}

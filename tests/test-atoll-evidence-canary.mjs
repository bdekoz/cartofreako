#!/usr/bin/env node

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const fixture = JSON.parse(await fs.readFile(
    new URL('../fixtures/atoll-evidence/v1/coordinates.json', import.meta.url),
    'utf8'));

assert.equal(fixture.lifecycle, 'exploration-only');
assert.equal(fixture.projectionTrace.projection, 'myriahedral-pacific');

const runtime = await createCartofreako();
const projection = runtime.projection({
    name: fixture.projectionTrace.projection,
    frame: [fixture.projectionTrace.frame.width, fixture.projectionTrace.frame.height]
});

function checkTrace(trace) {
    const geographic = trace.geographic;
    const expectedForward = trace.forward;
    const actualForward = projection.forward([
        geographic.longitude, geographic.latitude
    ]);
    assert.ok(Math.abs(actualForward.x - expectedForward.x) <= 1e-7);
    assert.ok(Math.abs(actualForward.y - expectedForward.y) <= 1e-7);
    assert.equal(actualForward.nativeCell, expectedForward.nativeCell);
    assert.equal(actualForward.component, expectedForward.component);

    const actualInverse = projection.inverse(
        [actualForward.x, actualForward.y],
        {
            nativeCell: actualForward.nativeCell,
            component: actualForward.component,
            tolerancePixels: trace.qualifiedInverse.tolerancePixels
        });
    assert.equal(actualInverse.status, 'unique');
    assert.equal(actualInverse.candidates.length, 1);
    assert.equal(actualInverse.truncated, false);
    const candidate = actualInverse.candidates[0];
    assert.equal(candidate.nativeCell, actualForward.nativeCell);
    assert.equal(candidate.component, actualForward.component);
    assert.ok(Math.abs(candidate.longitude - geographic.longitude) <= 2e-8);
    assert.ok(Math.abs(candidate.latitude - geographic.latitude) <= 2e-8);
    assert.ok(candidate.forwardResidual <= actualInverse.tolerancePx);
}

for (const trace of fixture.projectionTrace.points) checkTrace(trace);
checkTrace(fixture.pixelTrace);
projection.dispose();

console.log('Atoll evidence canary projection trace passed: 6 face-qualified forward/reverse anchors.');

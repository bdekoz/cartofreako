#!/usr/bin/env node

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const root = new URL('../', import.meta.url);
const manifest = JSON.parse(await fs.readFile(new URL(
    'fixtures/atoll-evidence/v1/pass-manifest.json', root), 'utf8'));
const expectedLayers = [
    'atoll-evidence-background', 'planetary-context',
    'observation-topobathymetry', 'scenario-inundation-probability',
    'scenario-inundation-deterministic', 'evidence-provenance',
    'unavailable-evidence'
];
const exactFrames = {
    'cahill-keyes': [4400, 2200],
    authagraph: [4400, 1100 * Math.sqrt(3)],
    dymaxion: [4400, 1200 * Math.sqrt(3)],
    'myriahedral-pacific': [4400, 2475],
    'star-x': [3400, 4400],
    voronoi: [4400, 27500 / 12]
};

function local(relative) {
    return new URL(relative, root);
}

function attribute(svg, name) {
    const match = svg.match(new RegExp(`\\b${name}="([^"]+)"`));
    assert.ok(match, `missing ${name}`);
    return match[1];
}

function pngDimensions(bytes) {
    assert.deepEqual(bytes.subarray(0, 8),
        Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
    return [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
}

function expectedPngDimensions(layout) {
    if (layout.page.orientation === 'portrait') {
        return [Math.round(3840 * layout.page.widthInches
            / layout.page.heightInches), 3840];
    }
    return [3840, Math.round(3840 * layout.page.heightInches
        / layout.page.widthInches)];
}

assert.equal(manifest.lifecycle, 'exploration-only');
assert.equal(manifest.layouts.length, 6);
assert.equal(manifest.artifactContract.expectedArtifactCount, 24);
assert.equal(manifest.promotion.standardLifecycleAuthorized, false);
assert.equal(manifest.promotion.publicReleaseAuthorized, false);

const runtime = await createCartofreako();
let artifactCount = 0;
for (const layout of manifest.layouts) {
    const svg = await fs.readFile(local(layout.artifacts.svg), 'utf8');
    artifactCount += 1;
    assert.ok(svg.includes('data-lifecycle="exploration-only"'));
    assert.ok(svg.includes('data-standard-promotion-authorized="false"'));
    assert.ok(svg.includes('data-community-regional-review="UNAVAILABLE"'));
    assert.equal((svg.match(/data:image\/png;base64,/g) ?? []).length, 4);
    assert.ok(!svg.includes('/home/'));
    for (const layer of expectedLayers) {
        assert.ok(svg.includes(`id="${layer}"`),
            `${layout.id} missing ${layer}`);
    }

    const frame = exactFrames[layout.runtimeProjection];
    assert.ok(frame, `missing exact frame for ${layout.runtimeProjection}`);
    const projection = runtime.projection({
        name: layout.runtimeProjection,
        frame
    });
    const geographic = [
        Number(attribute(svg, 'data-source-longitude')),
        Number(attribute(svg, 'data-source-latitude'))
    ];
    const expectedForward = [
        Number(attribute(svg, 'data-forward-x')),
        Number(attribute(svg, 'data-forward-y'))
    ];
    const forward = projection.forward(geographic);
    assert.ok(Math.abs(forward.x - expectedForward[0]) <= 1e-7);
    assert.ok(Math.abs(forward.y - expectedForward[1]) <= 1e-7);
    assert.equal(forward.nativeCell,
        Number(attribute(svg, 'data-native-cell')));
    assert.equal(forward.component,
        Number(attribute(svg, 'data-component')));
    const inverse = projection.inverse([forward.x, forward.y], {
        nativeCell: forward.nativeCell,
        component: forward.component,
        tolerancePixels: 1e-7
    });
    assert.equal(inverse.status, 'unique');
    assert.equal(inverse.candidates.length, 1);
    assert.ok(Math.abs(inverse.candidates[0].longitude - geographic[0]) <= 2e-8);
    assert.ok(Math.abs(inverse.candidates[0].latitude - geographic[1]) <= 2e-8);
    projection.dispose();

    const png = await fs.readFile(local(layout.artifacts.png));
    artifactCount += 1;
    assert.deepEqual(pngDimensions(png), expectedPngDimensions(layout));
    const thumbnail = await fs.readFile(local(layout.artifacts.thumbnail));
    artifactCount += 1;
    assert.equal(pngDimensions(thumbnail)[0], 480);
    const pdf = await fs.readFile(local(layout.artifacts.pdf));
    artifactCount += 1;
    assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
    const pdfText = pdf.toString('latin1');
    const mediaBox = pdfText.match(
        /\/MediaBox \[0 0 ([0-9.]+) ([0-9.]+)\]/);
    assert.ok(mediaBox, `${layout.id} PDF has no readable MediaBox`);
    // Chromium quantizes CSS print dimensions to 1/96 inch before expressing
    // the PDF MediaBox in points.  The error must stay within that one-pixel
    // physical bound; the declared SVG retains the exact inch dimensions.
    assert.ok(Math.abs(Number(mediaBox[1]) - layout.page.widthInches * 72)
        <= 0.75);
    assert.ok(Math.abs(Number(mediaBox[2]) - layout.page.heightInches * 72)
        <= 0.75);
}

assert.equal(artifactCount, manifest.artifactContract.expectedArtifactCount);
console.log('Majuro full evidence pass passed: 6 reversible layouts and 24 exploration artifacts.');

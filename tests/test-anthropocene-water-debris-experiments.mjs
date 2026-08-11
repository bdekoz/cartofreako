#!/usr/bin/env node

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const root = new URL('../', import.meta.url);
const manifest = JSON.parse(await fs.readFile(new URL(
    'fixtures/anthropocene-water-debris/v1/manifest.json', root), 'utf8'));

function attribute(fragment, name) {
    const match = fragment.match(new RegExp(`\\b${name}="([^"]+)"`));
    assert.ok(match, `missing ${name}`);
    return match[1];
}

assert.equal(manifest.lifecycle, 'exploration-only');
assert.deepEqual(manifest.years.map((value) => value.editionStatus),
    ['complete', 'partial']);
assert.equal(manifest.layouts.length, 6);
assert.equal(manifest.depthStations.length, 5);
assert.equal(manifest.evidenceClasses.length, 6);
assert.equal(manifest.sources.length, 5);
assert.equal(manifest.style.observedFieldMaximumOpacity, 0.6);
assert.equal(manifest.promotion.standardLifecycleAuthorized, false);
assert.equal(manifest.promotion.publicReleaseAuthorized, false);

const runtime = await createCartofreako();
let count = 0;
for (const layout of manifest.layouts) {
    const projection = runtime.projection({
        name: layout.runtimeProjection,
        frame: layout.frame
    });
    for (const edition of manifest.years) {
        const name = `anthropocene-water-debris-${edition.year}-${layout.suffix}.svg`;
        const value = await fs.readFile(new URL(
            `assets.generated/${layout.projectionDirectory}/svg/${name}`, root),
        'utf8');
        assert.ok(value.includes('id="anthropocene-water-debris-experiment"'));
        assert.ok(value.includes('id="depth-profile-observations"'));
        assert.ok(value.includes('style="display:inline;opacity:0.6"'));
        assert.ok(value.includes('data-default-visible="true"'));
        assert.ok(value.includes('data-lifecycle="exploration-only"'));
        assert.ok(value.includes('data-unavailable-depth-rule="UNAVAILABLE-not-zero"'));
        assert.ok(value.includes('data-standard-promotion-authorized="false"'));
        assert.ok(value.includes('data-public-release-authorized="false"'));
        assert.ok(value.includes('No garbage-patch polygon or invented thickness'));
        assert.ok(!value.includes('/home/'));
        const records = [...value.matchAll(/<g data-water-debris-record="true"[^>]*>/g)]
            .map((match) => match[0]);
        assert.equal(records.length, 5);
        for (const record of records) {
            const geographic = [
                Number(attribute(record, 'data-longitude')),
                Number(attribute(record, 'data-latitude'))
            ];
            const forward = projection.forward(geographic);
            assert.ok(Math.abs(forward.x
                - Number(attribute(record, 'data-forward-x'))) <= 1e-7);
            assert.ok(Math.abs(forward.y
                - Number(attribute(record, 'data-forward-y'))) <= 1e-7);
            const inverse = projection.inverse([forward.x, forward.y], {
                nativeCell: Number(attribute(record, 'data-native-cell')),
                component: Number(attribute(record, 'data-component')),
                tolerancePixels: 1e-7
            });
            assert.equal(inverse.status, 'unique');
            assert.equal(inverse.candidates.length, 1);
            assert.ok(Math.abs(inverse.candidates[0].longitude
                - geographic[0]) <= 2e-8);
            assert.ok(Math.abs(inverse.candidates[0].latitude
                - geographic[1]) <= 2e-8);
        }
        count += 1;
    }
    projection.dispose();
}

assert.equal(count, 12);
console.log('Water-debris experiment passed: 12 reversible exploration plates, five observed depth stations, and four context-only source families.');

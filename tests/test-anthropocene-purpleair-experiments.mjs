#!/usr/bin/env node

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const manifest = JSON.parse(await fs.readFile(new URL(
    'fixtures/anthropocene-purpleair/v1/manifest.json', root), 'utf8'));

assert.equal(manifest.lifecycle, 'exploration-only');
assert.equal(manifest.dataBoundary.kind, 'synthetic-interface-fixture');
assert.equal(manifest.dataBoundary.containsObservations, false);
assert.equal(manifest.dataBoundary.measurement, 'UNAVAILABLE');
assert.equal(manifest.style.defaultVisible, true);
assert.equal(manifest.style.maximumOpacity, 0.6);
assert.equal(manifest.layouts.length, 6);
assert.equal(manifest.anchors.length, 12);
assert.equal(manifest.promotion.standardLifecycleAuthorized, false);
assert.equal(manifest.promotion.publicReleaseAuthorized, false);

let count = 0;
for (const layout of manifest.layouts) {
    for (const year of [2025, 2026]) {
        const name = `anthropocene-particulate-purpleair-${year}-${layout.suffix}.svg`;
        const value = await fs.readFile(new URL(
            `assets.generated/${layout.projectionDirectory}/svg/${name}`, root),
        'utf8');
        assert.ok(value.includes(`id="${manifest.style.layerId}"`));
        assert.ok(value.includes('style="display:inline;opacity:0.6"'));
        assert.ok(value.includes('data-default-visible="true"'));
        assert.ok(value.includes('data-lifecycle="exploration-only"'));
        assert.ok(value.includes('data-contains-observations="false"'));
        assert.ok(value.includes('data-measurement="UNAVAILABLE"'));
        assert.ok(value.includes('data-standard-promotion-authorized="false"'));
        assert.ok(value.includes('data-public-release-authorized="false"'));
        assert.ok(value.includes('SYNTHETIC INTERFACE ANCHORS ONLY'));
        assert.ok(!value.includes('/home/'));
        assert.equal((value.match(/data-purpleair-anchor="true"/g) ?? []).length,
            manifest.anchors.length);
        assert.equal((value.match(/data-anchor-role="rendering-qa-anchor-not-a-sensor"/g) ?? []).length,
            manifest.anchors.length);
        count += 1;
    }
}

assert.equal(count, 12);
console.log('PurpleAir interface experiment passed: 12 default-visible, 60%-opacity synthetic overlays with no observation claim.');

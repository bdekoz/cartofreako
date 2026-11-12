#!/usr/bin/env node
import assert from 'node:assert/strict';
import path from 'node:path';
import {artifactPaths, generatedDirectory} from '../scripts/generate-screen-1080p.mjs';

const repository = '/tmp/cartofreako-path-fixture';
const entry = {id: 'earth.authagraph.whole-map', stem: 'earth-authagraph-44-19.052559',
    sourceSvg: 'assets.generated/authagraph/svg/earth-authagraph-44-19.052559.svg'};
assert.equal(generatedDirectory({}, repository), path.join(repository, 'assets.generated'));
assert.equal(generatedDirectory({GENERATED_DIR: 'custom-native'}, repository), path.join(repository, 'custom-native'));
const build = path.join(repository, 'output/data-editions/edition/builds/run');
const native = path.join(build, 'native');
assert.equal(generatedDirectory({DATASET_OUTPUT_ROOT: build}, repository), native);
assert.equal(generatedDirectory({DATASET_OUTPUT_ROOT: build, GENERATED_DIR: native}, repository), native);
assert.throws(() => generatedDirectory({DATASET_OUTPUT_ROOT: build, GENERATED_DIR: 'assets.generated'}, repository), /conflicts/);
const selected = artifactPaths(entry, native);
for (const filename of Object.values(selected)) assert.ok(filename.startsWith(native + path.sep));
assert.equal(selected.svg, path.join(native, 'authagraph/svg/' + entry.stem + '.svg'));
assert.equal(selected.pdf, path.join(native, 'authagraph/pdf/' + entry.stem + '.pdf'));
assert.equal(selected.png, path.join(native, 'authagraph/png/' + entry.stem + '.png'));
assert.equal(selected.screenPng, path.join(native, 'authagraph/screen-1080p/' + entry.stem + '.png'));
assert.equal(selected.screenWebp, path.join(native, 'authagraph/screen-1080p-webp/' + entry.stem + '.webp'));
assert.throws(() => artifactPaths({...entry, sourceSvg: '../private.svg'}, native), /canonical/);
assert.throws(() => artifactPaths({...entry, sourceSvg: 'assets.generated/authagraph/svg/../../private.svg'}, native), /canonical/);
assert.throws(() => artifactPaths({...entry, stem: '../private'}, native), /stem/);
console.log('screen output paths: legacy, custom, bound edition, conflict and traversal checks passed');

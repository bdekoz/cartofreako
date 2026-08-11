#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

import {
    canonicalJson,
    overrideArtifactDecision,
    selectArtifact,
    sha256Hex
} from '../src.wasm/cartofreako-catalog.mjs';

const root = path.resolve(import.meta.dirname, '..');
const fixtureRoot = path.join(root, 'tests/fixtures/artifact-selection');
const catalogBytes = await fs.readFile(path.join(fixtureRoot, 'catalog.json'));
const requestBytes = await fs.readFile(path.join(fixtureRoot, 'request.json'));
const catalog = JSON.parse(catalogBytes);
const request = JSON.parse(requestBytes);

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

const first = await selectArtifact(request, catalog, {
    catalogBytes,
    createdAt: '2026-08-10T00:00:00Z'
});
const second = await selectArtifact(request, catalog, {
    catalogBytes,
    createdAt: '2030-01-01T00:00:00Z'
});
requireCondition(first.decisionCore.outcome === 'selected', 'golden request was not selected');
requireCondition(first.decisionCore.selection.artifactId === 'water.myriahedral.whole-map'
    && first.decisionCore.selection.variantId === 'screen-webp', 'wrong golden selection');
requireCondition(first.decisionCoreSha256 === second.decisionCoreSha256,
    'run envelope changed deterministic decision core');
requireCondition(first.decisionCoreSha256
    === await sha256Hex(canonicalJson(first.decisionCore)), 'decision hash is invalid');

const reordered = {...catalog, artifacts: [...catalog.artifacts].reverse()};
const reorderedReceipt = await selectArtifact(request, reordered,
    {createdAt: '2026-08-10T00:00:00Z'});
requireCondition(reorderedReceipt.decisionCore.selection.artifactId
    === first.decisionCore.selection.artifactId
    && reorderedReceipt.decisionCore.selection.variantId
        === first.decisionCore.selection.variantId,
'catalog order changed the choice');

const noMatch = await selectArtifact({...request, requestId: 'no-match',
    passIds: ['does-not-exist']}, catalog, {catalogBytes});
requireCondition(noMatch.decisionCore.outcome === 'no-match'
    && noMatch.decisionCore.selection === null, 'no-match receipt is invalid');
requireCondition(noMatch.decisionCore.evaluatedCandidates.every(value =>
    value.rejectionReasonCodes.includes('SUBJECT_MISMATCH')),
'no-match lacks rejection reasons');

const metadata = await selectArtifact({...request, requestId: 'metadata',
    licenses: ['CC-BY-4.0']}, catalog, {catalogBytes});
requireCondition(metadata.decisionCore.outcome === 'no-match'
    && metadata.decisionCore.evaluatedCandidates.some(value =>
        value.rejectionReasonCodes.includes('METADATA_UNAVAILABLE')),
'missing metadata was treated as permissive');

const standardDefault = await selectArtifact({
    schemaVersion: request.schemaVersion,
    requestId: 'standard-default',
    purpose: 'preview',
    formats: ['webp']
}, catalog, {catalogBytes});
requireCondition(standardDefault.decisionCore.selection.lifecycle === 'standard',
    'default request selected an optional artifact');

const fallback = await selectArtifact({...request,
    requestId: 'explicit-fallback',
    projectionIds: ['projection-not-in-catalog'],
    fallbackSequence: ['projectionIds']
}, catalog, {catalogBytes});
requireCondition(fallback.decisionCore.outcome === 'selected'
    && fallback.decisionCore.selection.artifactId === 'water.myriahedral.whole-map'
    && fallback.decisionCore.relaxations.length === 1
    && fallback.decisionCore.relaxations[0].field === 'projectionIds'
    && fallback.decisionCore.relaxations[0].before[0] === 'projection-not-in-catalog'
    && fallback.decisionCore.relaxations[0].after.length === 0,
'explicit fallback was not applied or recorded');

const lifecycleBoundary = await selectArtifact({...request,
    requestId: 'lifecycle-boundary',
    allowedLifecycles: ['standard'],
    passIds: ['optional-cloud'],
    projectionIds: ['projection-not-in-catalog'],
    fallbackSequence: ['projectionIds', 'formats', 'maxBytes', 'viewport',
        'authorityClasses']
}, catalog, {catalogBytes});
requireCondition(lifecycleBoundary.decisionCore.outcome === 'no-match'
    && lifecycleBoundary.decisionCore.evaluatedCandidates.some(value =>
        value.rejectionReasonCodes.includes('LIFECYCLE_DISALLOWED')),
'fallback crossed the standard lifecycle boundary');

let tamperRejected = false;
try {
    await selectArtifact({...request, expectedCatalogSha256: '0'.repeat(64)},
        catalog, {catalogBytes});
} catch (error) {
    tamperRejected = error instanceof TypeError;
}
requireCondition(tamperRejected, 'tampered catalog hash was accepted');

const priorHash = first.decisionCoreSha256;
const override = await overrideArtifactDecision(first,
    {...first.decisionCore.selection, artifactId: 'water.cahill-keyes.whole-map'}, {
        reason: 'Operator chose an alternate interrupted layout for comparison.',
        actorLabel: 'human-reviewer',
        createdAt: '2026-08-10T00:01:00Z'
    });
requireCondition(first.decisionCoreSha256 === priorHash
    && override.decisionCore.priorReceiptSha256 === priorHash
    && override.decisionCoreSha256 !== priorHash, 'override was not append-only');

const expectedPath = path.join(fixtureRoot, 'expected-receipt.json');
if (process.argv.includes('--refresh')) {
    await fs.writeFile(expectedPath, `${JSON.stringify(first, null, 2)}\n`);
} else {
    const expected = JSON.parse(await fs.readFile(expectedPath));
    requireCondition(expected.decisionCoreSha256 === first.decisionCoreSha256
        && canonicalJson(expected.decisionCore) === canonicalJson(first.decisionCore),
    'golden receipt changed');
}
console.log(`artifact selector passed: ${first.decisionCore.selection.artifactId} / `
    + `${first.decisionCore.selection.variantId} / ${first.decisionCoreSha256}`);

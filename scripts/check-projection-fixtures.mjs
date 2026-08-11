#!/usr/bin/env node

import {createHash} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(import.meta.dirname, '..');
const fixtureRoot = path.join(root, 'fixtures/projections/v1');
const familyNames = [
    'cahill-keyes', 'authagraph', 'dymaxion',
    'myriahedral', 'star-x', 'voronoi'
];
const fixtureSchema = 'cartofreako-projection-fixtures-v1';
const evidenceGrades = new Set([
    'published-anchor', 'upstream-implementation',
    'independent-reimplementation', 'structural-invariant',
    'cartofreako-compatibility'
]);
const statuses = new Set(['unique', 'ambiguous', 'outside', 'cut', 'unsupported']);
const boundaries = new Set(['interior', 'edge', 'vertex', 'cut', 'pole', 'overlap']);

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function hash(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
}

function isPair(value) {
    return Array.isArray(value) && value.length === 2
        && value.every(Number.isFinite);
}

function candidateKey(candidate) {
    return `${candidate.topologyKey}\u0000${candidate.component}\u0000`
        + `${candidate.geographic[0]}\u0000${candidate.geographic[1]}`;
}

function validateFixture(document, expectedFamily) {
    requireCondition(document.schemaVersion === fixtureSchema,
        `${expectedFamily}: wrong schema version`);
    requireCondition(document.family === expectedFamily,
        `${expectedFamily}: wrong family`);
    requireCondition(document.coordinateContract?.geographic
        === '[longitude, latitude] degrees', `${expectedFamily}: wrong geographic order`);
    requireCondition(document.coordinateContract?.projected
        === '[u, v] normalized page coordinates', `${expectedFamily}: wrong page space`);
    requireCondition(document.coordinateContract?.origin === 'top-left'
        && document.coordinateContract?.xAxis === 'right'
        && document.coordinateContract?.yAxis === 'down',
    `${expectedFamily}: wrong axes`);
    requireCondition(Array.isArray(document.layouts) && document.layouts.length > 0,
        `${expectedFamily}: no layouts`);

    let count = 0;
    const layoutIds = new Set();
    for (const layout of document.layouts) {
        requireCondition(typeof layout.layoutId === 'string' && layout.layoutId,
            `${expectedFamily}: invalid layout ID`);
        requireCondition(!layoutIds.has(layout.layoutId),
            `${expectedFamily}: duplicate layout ${layout.layoutId}`);
        layoutIds.add(layout.layoutId);
        requireCondition(Number.isFinite(layout.nativeAspect) && layout.nativeAspect > 0,
            `${layout.layoutId}: invalid aspect`);
        requireCondition(typeof layout.componentModel === 'string'
            && typeof layout.cutTopology === 'string', `${layout.layoutId}: missing topology`);
        requireCondition(Array.isArray(layout.cases) && layout.cases.length > 0,
            `${layout.layoutId}: no cases`);
        const caseIds = new Set();
        for (const fixture of layout.cases) {
            ++count;
            requireCondition(typeof fixture.caseId === 'string' && fixture.caseId,
                `${layout.layoutId}: invalid case ID`);
            requireCondition(!caseIds.has(fixture.caseId),
                `${layout.layoutId}: duplicate case ${fixture.caseId}`);
            caseIds.add(fixture.caseId);
            requireCondition(fixture.operation === 'forward-reverse',
                `${fixture.caseId}: invalid operation`);
            requireCondition(isPair(fixture.input?.geographic),
                `${fixture.caseId}: invalid geographic input`);
            requireCondition(Math.abs(fixture.input.geographic[0]) <= 180
                && Math.abs(fixture.input.geographic[1]) <= 90,
            `${fixture.caseId}: geographic input outside canonical domain`);
            requireCondition(isPair(fixture.expected?.projected)
                && fixture.expected.projected.every(value => value >= -1e-12
                    && value <= 1 + 1e-12), `${fixture.caseId}: invalid page point`);
            requireCondition(typeof fixture.expected.topologyKey === 'string'
                && fixture.expected.topologyKey, `${fixture.caseId}: missing topology key`);
            requireCondition(Number.isInteger(fixture.expected.component)
                && fixture.expected.component >= 0, `${fixture.caseId}: invalid component`);
            requireCondition(statuses.has(fixture.expected.reverseStatus),
                `${fixture.caseId}: invalid reverse status`);
            requireCondition(Array.isArray(fixture.expected.reverseCandidates)
                && fixture.expected.reverseCandidates.length > 0,
            `${fixture.caseId}: missing reverse candidates`);
            const keys = fixture.expected.reverseCandidates.map(candidate => {
                requireCondition(isPair(candidate.geographic)
                    && typeof candidate.topologyKey === 'string'
                    && Number.isInteger(candidate.component)
                    && typeof candidate.boundary === 'boolean',
                `${fixture.caseId}: invalid candidate`);
                return candidateKey(candidate);
            });
            requireCondition(keys.every((value, index) => index === 0
                || keys[index - 1] <= value), `${fixture.caseId}: candidates not canonical`);
            requireCondition(new Set(keys).size === keys.length,
                `${fixture.caseId}: duplicate candidate`);
            requireCondition(boundaries.has(fixture.boundaryClass),
                `${fixture.caseId}: invalid boundary class`);
            requireCondition(Number.isFinite(fixture.tolerances?.angularDegrees)
                && fixture.tolerances.angularDegrees > 0
                && Number.isFinite(fixture.tolerances?.normalizedPlanar)
                && fixture.tolerances.normalizedPlanar > 0,
            `${fixture.caseId}: invalid tolerance`);
            requireCondition(evidenceGrades.has(fixture.evidence?.grade)
                && typeof fixture.evidence?.source === 'string'
                && Number.isInteger(fixture.evidence?.revision),
            `${fixture.caseId}: invalid evidence`);
        }
    }
    return {count, layouts: [...layoutIds]};
}

async function loadFamilies() {
    const records = [];
    for (const family of familyNames) {
        const file = `${family}.json`;
        const bytes = await readFile(path.join(fixtureRoot, file));
        const document = JSON.parse(bytes);
        const validation = validateFixture(document, family);
        records.push({family, file, sha256: hash(bytes), ...validation});
    }
    return records;
}

function stableJson(value) {
    if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
    if (value && typeof value === 'object') return `{${Object.keys(value).sort()
        .map(key => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
    return JSON.stringify(value);
}

async function refresh(records) {
    const producer = await readFile(path.join(root, 'tests/generate-projection-fixtures.cc'));
    const schema = await readFile(path.join(root, 'contracts/projection-fixtures-v1.schema.json'));
    const crosswalk = await readFile(path.join(fixtureRoot,
        'topology-crosswalk-cartofreako.json'));
    const manifest = {
        schemaVersion: 'cartofreako-projection-fixture-manifest-v1',
        bundleVersion: 1,
        coordinateSemantics: 'implementation-neutral normalized top-left page space',
        license: 'GPL-3.0-or-later',
        sourceIdentity: 'Cartofreako runtime API 3, Stage 14 fixture revision 1',
        fixtureSchema: {
            file: '../../../contracts/projection-fixtures-v1.schema.json',
            sha256: hash(schema)
        },
        producer: {
            file: '../../../tests/generate-projection-fixtures.cc',
            sha256: hash(producer),
            refreshTarget: 'make refresh-projection-fixtures'
        },
        crosswalk: {
            file: 'topology-crosswalk-cartofreako.json',
            sha256: hash(crosswalk),
            normative: false
        },
        families: records,
        totalCaseCount: records.reduce((total, record) => total + record.count, 0),
        revisionHistory: [{revision: 1, change: 'Initial six-family Stage 14 bundle'}]
    };
    await writeFile(path.join(fixtureRoot, 'manifest.json'),
        `${JSON.stringify(manifest, null, 2)}\n`);
    const checksumFiles = [
        ...records.map(record => record.file),
        'manifest.json',
        'topology-crosswalk-cartofreako.json'
    ];
    const checksumLines = [];
    for (const file of checksumFiles) {
        const bytes = await readFile(path.join(fixtureRoot, file));
        checksumLines.push(`${hash(bytes)}  ${file}`);
    }
    await writeFile(path.join(fixtureRoot, 'SHA256SUMS'), `${checksumLines.join('\n')}\n`);
    return manifest;
}

async function checkManifest(records) {
    const manifestBytes = await readFile(path.join(fixtureRoot, 'manifest.json'));
    const manifest = JSON.parse(manifestBytes);
    requireCondition(manifest.schemaVersion
        === 'cartofreako-projection-fixture-manifest-v1', 'invalid manifest version');
    requireCondition(stableJson(manifest.families) === stableJson(records),
        'fixture manifest does not match checked family bytes');
    requireCondition(manifest.totalCaseCount
        === records.reduce((total, record) => total + record.count, 0),
    'fixture manifest total is wrong');
    const checksumText = await readFile(path.join(fixtureRoot, 'SHA256SUMS'), 'utf8');
    for (const line of checksumText.trim().split('\n')) {
        const match = /^([0-9a-f]{64})  (.+)$/.exec(line);
        requireCondition(match, `malformed checksum line: ${line}`);
        const bytes = await readFile(path.join(fixtureRoot, match[2]));
        requireCondition(hash(bytes) === match[1], `checksum mismatch: ${match[2]}`);
    }
    return manifest;
}

const records = await loadFamilies();
const refreshing = process.argv.includes('--refresh');
const manifest = refreshing ? await refresh(records) : await checkManifest(records);
console.log(`${refreshing ? 'refreshed' : 'validated'} projection fixtures: `
    + `${manifest.totalCaseCount} cases in ${records.length} families`);

#!/usr/bin/env node

import {createHash} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(import.meta.dirname, '..');
const oracleRoot = path.join(root, 'fixtures/projections/v1/oracles');
const payloads = [
    ['voronoi-d3-v2.0.1.json', 'voronoi', 'upstream-implementation', 96],
    ['dymaxion-d3-gray-v2.0.1.json', 'dymaxion', 'upstream-implementation', 92],
    ['myriahedral-clean-room.json', 'myriahedral', 'independent-reimplementation', 1920]
];
const supportFiles = [
    'd3-version-delta-v1.12.1-v2.0.1.json',
    'd3-geo-polygon-v2.0.1-yarn.lock',
    'myriahedral-declared-topology.json'
];

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function sha256(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
}

async function inspectPayloads() {
    const records = [];
    for (const [file, family, grade, minimumCases] of payloads) {
        const bytes = await readFile(path.join(oracleRoot, file));
        const document = JSON.parse(bytes);
        requireCondition(document.schemaVersion === 'cartofreako-reverse-oracle-v1',
            `${file}: wrong schema`);
        requireCondition(document.family === family, `${file}: wrong family`);
        requireCondition(document.evidenceGrade === grade, `${file}: wrong evidence grade`);
        requireCondition(Array.isArray(document.cases)
            && document.cases.length >= minimumCases, `${file}: incomplete case set`);
        const ids = new Set(document.cases.map(value => value.caseId));
        requireCondition(ids.size === document.cases.length, `${file}: duplicate case ID`);
        records.push({file, family, evidenceGrade: grade,
            caseCount: document.cases.length, sha256: sha256(bytes)});
    }
    return records;
}

async function refresh(records) {
    const support = [];
    for (const file of supportFiles) {
        const bytes = await readFile(path.join(oracleRoot, file));
        support.push({file, sha256: sha256(bytes)});
    }
    const manifest = {
        schemaVersion: 'cartofreako-reverse-oracle-manifest-v1',
        bundleVersion: 1,
        resultPolicy: 'Every disagreement is retained and classified before production changes.',
        evidenceClaim: 'Two direct-upstream families and one independent mathematical inverse over shared declared topology.',
        normalCheckNetworkPolicy: 'offline',
        refreshTarget: 'make refresh-reverse-oracle-fixtures',
        records,
        support,
        totalCaseCount: records.reduce((total, record) => total + record.caseCount, 0)
    };
    await writeFile(path.join(oracleRoot, 'manifest.json'),
        `${JSON.stringify(manifest, null, 2)}\n`);
    const files = [...records.map(record => record.file), ...supportFiles, 'manifest.json'];
    const lines = [];
    for (const file of files) {
        const bytes = await readFile(path.join(oracleRoot, file));
        lines.push(`${sha256(bytes)}  ${file}`);
    }
    await writeFile(path.join(oracleRoot, 'SHA256SUMS'), `${lines.join('\n')}\n`);
    return manifest;
}

async function check(records) {
    const manifest = JSON.parse(await readFile(path.join(oracleRoot, 'manifest.json')));
    requireCondition(manifest.schemaVersion
        === 'cartofreako-reverse-oracle-manifest-v1', 'wrong oracle manifest');
    requireCondition(JSON.stringify(manifest.records) === JSON.stringify(records),
        'oracle manifest records do not match payload bytes');
    const checksumLines = (await readFile(path.join(oracleRoot, 'SHA256SUMS'), 'utf8'))
        .trim().split('\n');
    for (const line of checksumLines) {
        const match = /^([0-9a-f]{64})  (.+)$/.exec(line);
        requireCondition(match, `malformed checksum: ${line}`);
        requireCondition(sha256(await readFile(path.join(oracleRoot, match[2]))) === match[1],
            `oracle checksum mismatch: ${match[2]}`);
    }
    const delta = JSON.parse(await readFile(path.join(oracleRoot,
        'd3-version-delta-v1.12.1-v2.0.1.json')));
    requireCondition(delta.from.version === '1.12.1' && delta.to.version === '2.0.1'
        && delta.audit.result === 'registration-preserving', 'D3 delta audit is incomplete');
    requireCondition(manifest.records.filter(record =>
        ['upstream-implementation', 'independent-reimplementation']
            .includes(record.evidenceGrade)).length >= 2,
    'fewer than two independent oracle families');
    return manifest;
}

const records = await inspectPayloads();
const refreshing = process.argv.includes('--refresh');
const manifest = refreshing ? await refresh(records) : await check(records);
console.log(`${refreshing ? 'refreshed' : 'validated'} reverse-oracle bundle: `
    + `${manifest.totalCaseCount} cases across ${records.length} families`);

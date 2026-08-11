#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function wholeProjection(stem) {
    const definitions = [
        ['cahill-keyes', 'cahill-keyes', 'ck-44-22'],
        ['authagraph', 'authagraph', 'authagraph-44-19.052559'],
        ['dymaxion', 'dymaxion', 'dymaxion-44-20.78461'],
        ['myriahedral', 'myriahedral', 'myriahedral-44-24.75'],
        ['star-x', 'star-x', 'star-x-34-44'],
        ['voronoi', 'voronoi', 'voronoi-44-22.916667']
    ];
    for (const [projectionId, family, suffix] of definitions) {
        const token = `-${suffix}`;
        if (stem.endsWith(token)) {
            return {
                passId: stem.slice(0, -token.length),
                projectionId,
                layoutId: projectionId,
                family,
                sliceId: null
            };
        }
    }
    return null;
}

function classify(stem) {
    let match = /^earth-ck-(4|8)-slice-([1-8])$/.exec(stem);
    if (match) {
        const four = match[1] === '4';
        const number = Number(match[2]);
        requireCondition(!four || number <= 4, `invalid four-strip slice ${stem}`);
        return {
            passId: 'earth',
            projectionId: 'cahill-keyes',
            layoutId: 'cahill-keyes',
            family: 'cahill-keyes',
            sliceId: four ? `ck-strip-${number}` : `ck-octant-${number}`
        };
    }
    match = /^water-myriahedral-adhoc-slice-([12])$/.exec(stem);
    if (match) {
        return {
            passId: 'water',
            projectionId: 'myriahedral',
            layoutId: 'myriahedral',
            family: 'myriahedral',
            sliceId: `myria-group-${match[1]}`
        };
    }
    match = /^water-myriahedral-(americas|atlantic|afro-eur-asia|pacific|antarctic)-44-24\.75$/.exec(stem);
    if (match) {
        return {
            passId: 'water',
            projectionId: `myriahedral-${match[1]}`,
            layoutId: `myriahedral-${match[1]}`,
            family: 'myriahedral',
            sliceId: null
        };
    }
    return wholeProjection(stem);
}

function relative(value) {
    const absolute = path.resolve(root, value);
    requireCondition(absolute.startsWith(`${root}${path.sep}`),
        `inventory path escapes repository: ${value}`);
    return path.relative(root, absolute).split(path.sep).join('/');
}

function build(paths) {
    const uniquePaths = [...new Set(paths.map(relative))].sort();
    requireCondition(uniquePaths.length === paths.length,
        'standard artifact inventory contains duplicate paths');
    const artifacts = uniquePaths.map(sourceSvg => {
        requireCondition(/^assets\.generated\/[a-z-]+\/svg\/[a-z0-9.-]+\.svg$/.test(sourceSvg),
            `invalid generated SVG path ${sourceSvg}`);
        const stem = path.posix.basename(sourceSvg, '.svg');
        const classification = classify(stem);
        requireCondition(classification, `unclassified standard artifact ${stem}`);
        const directoryProjection = sourceSvg.split('/')[1];
        requireCondition(directoryProjection === classification.family
            || (classification.family === 'cahill-keyes'
                && directoryProjection === 'cahill-keyes'),
        `projection directory disagrees for ${sourceSvg}`);
        const sliceToken = classification.sliceId ?? 'whole-map';
        return {
            id: `${classification.passId}.${classification.projectionId}.${sliceToken}`,
            stem,
            sourceSvg,
            lifecycle: 'standard',
            ...classification
        };
    });
    requireCondition(new Set(artifacts.map(({id}) => id)).size === artifacts.length,
        'standard artifact IDs are not unique');
    return {
        schemaVersion: 'cartofreako-standard-artifact-manifest-v1',
        inventorySource: 'Makefile:GENERATED_SVGS',
        lifecycle: 'standard',
        artifactCount: artifacts.length,
        artifacts
    };
}

const input = await new Promise((resolve, reject) => {
    let value = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { value += chunk; });
    process.stdin.on('end', () => resolve(value));
    process.stdin.on('error', reject);
});
const paths = input.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
requireCondition(paths.length > 0, 'standard artifact path list is empty');
const manifest = build(paths);
const rendered = `${JSON.stringify(manifest, null, 2)}\n`;
const mode = process.argv[2] ?? '--print';
const destination = process.argv[3]
    ? path.resolve(root, process.argv[3]) : null;
if (mode === '--refresh') {
    requireCondition(destination, '--refresh requires a destination');
    await fs.writeFile(destination, rendered, 'utf8');
    console.log(`Refreshed ${path.relative(root, destination)} with ${manifest.artifactCount} standard artifacts.`);
} else if (mode === '--check') {
    requireCondition(destination, '--check requires a destination');
    const checked = await fs.readFile(destination, 'utf8');
    requireCondition(checked === rendered,
        `${path.relative(root, destination)} is stale; run make refresh-standard-artifact-manifest`);
    console.log(`Standard artifact manifest passed: ${manifest.artifactCount} artifacts.`);
} else if (mode === '--print') {
    process.stdout.write(rendered);
} else {
    throw new Error(`unknown mode ${mode}`);
}

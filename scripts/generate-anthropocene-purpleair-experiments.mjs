#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const manifestPath = path.join(root,
    'fixtures/anthropocene-purpleair/v1/manifest.json');

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function xml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&apos;');
}

function n(value) {
    return Number(value.toFixed(6)).toString();
}

function marker(anchor, forward) {
    const x = forward.x / 100;
    const y = forward.y / 100;
    return `<g data-purpleair-anchor="true" data-anchor-id="${xml(anchor.id)}" data-anchor-role="${anchor.role}" data-longitude="${anchor.longitude}" data-latitude="${anchor.latitude}" data-measurement="UNAVAILABLE"><circle cx="${n(x)}" cy="${n(y)}" r="0.105" fill="#7f3c8d" stroke="#2d1233" stroke-width="0.026"/><circle cx="${n(x)}" cy="${n(y)}" r="0.035" fill="#f4f5f5" stroke="none"/><title>${xml(anchor.label)} — rendering QA anchor, not a PurpleAir sensor or observation</title></g>`;
}

function overlay(manifest, projection) {
    const markers = manifest.anchors.map((anchor) =>
        marker(anchor, projection.forward([anchor.longitude, anchor.latitude])))
        .join('\n');
    return `<g id="${manifest.style.layerId}" style="display:inline;opacity:${manifest.style.maximumOpacity}" data-default-visible="true" data-lifecycle="exploration-only" data-source-role="synthetic-interface-fixture" data-contains-observations="false" data-measurement="UNAVAILABLE" data-maximum-opacity="${manifest.style.maximumOpacity}"><title>PurpleAir speculative interface — synthetic QA anchors, no sensor observations</title>\n${markers}\n</g>`;
}

function transformSvg(source, manifest, layout, year, layer) {
    const sourceBase = `anthropocene-particulate-${year}-${layout.suffix}`;
    const outputBase = `anthropocene-particulate-purpleair-${year}-${layout.suffix}`;
    let value = source.replaceAll(sourceBase, outputBase);
    value = value.replace(
        `ANTHROPOCENE PARTICULATE / ${year}`,
        `ANTHROPOCENE PARTICULATE + PURPLEAIR QA / ${year}`);
    value = value.replace(
        /<metadata id="anthropocene-particulate-metadata"/,
        `<metadata id="anthropocene-purpleair-experiment-metadata" data-lifecycle="exploration-only" data-default-visible="true" data-contains-observations="false" data-measurement="UNAVAILABLE" data-standard-promotion-authorized="false" data-public-release-authorized="false" data-interface-fixture="fixtures/anthropocene-purpleair/v1/manifest.json"></metadata>\n<metadata id="anthropocene-particulate-metadata"`);
    const insertion = '<g id="legend-and-provenance">';
    requireCondition(value.includes(insertion),
        `${sourceBase} has no legend insertion boundary`);
    value = value.replace(insertion, `${layer}\n${insertion}`);
    value = value.replace('</svg>',
        `<g id="purpleair-experiment-disclaimer"><text x="${n(layout.frame[0] / 200)}" y="${n(layout.frame[1] / 100 - 0.34)}" font-family="Atkinson Hyperlegible" font-size="0.12pt" text-anchor="middle" style="fill:#3e2743;fill-opacity:0.96;stroke:#f4f5f5;stroke-opacity:0.9;stroke-width:0.008">PURPLEAIR EXPERIMENT: SYNTHETIC INTERFACE ANCHORS ONLY — NO SENSOR VALUES OR OBSERVATIONS</text></g>\n</svg>`);
    requireCondition(value.includes('data-default-visible="true"')
        && value.includes('style="display:inline;opacity:0.6"')
        && value.includes('data-contains-observations="false"'),
    `${outputBase} lost its experiment boundary`);
    return {outputBase, value};
}

const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
requireCondition(manifest.lifecycle === 'exploration-only'
    && manifest.dataBoundary.containsObservations === false
    && manifest.style.defaultVisible === true
    && manifest.style.maximumOpacity === 0.6
    && manifest.promotion.standardLifecycleAuthorized === false
    && manifest.promotion.publicReleaseAuthorized === false,
'PurpleAir experiment manifest attempts an unsupported claim or promotion');

const runtime = await createCartofreako();
for (const layout of manifest.layouts) {
    const projection = runtime.projection({
        name: layout.runtimeProjection,
        frame: layout.frame
    });
    const layer = overlay(manifest, projection);
    projection.dispose();
    for (const year of [2025, 2026]) {
        const source = path.join(root, 'assets.generated',
            layout.projectionDirectory, 'svg',
            `anthropocene-particulate-${year}-${layout.suffix}.svg`);
        const value = await fs.readFile(source, 'utf8');
        const transformed = transformSvg(value, manifest, layout, year, layer);
        const output = path.join(root, 'assets.generated',
            layout.projectionDirectory, 'svg', `${transformed.outputBase}.svg`);
        await fs.mkdir(path.dirname(output), {recursive: true});
        await fs.writeFile(output, transformed.value, 'utf8');
        console.log(`Generated ${path.relative(root, output)}`);
    }
}

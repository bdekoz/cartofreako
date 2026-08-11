#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const manifestPath = path.join(root,
    'fixtures/anthropocene-water-debris/v1/manifest.json');

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

function stationMarker(station, forward) {
    const x = forward.x / 100;
    const y = forward.y / 100;
    const radius = 0.18 + station.maximumSampleDepthM / 25000;
    return `<g data-water-debris-record="true" data-record-id="${station.id}" data-evidence-class="depth-profile" data-source-id="${station.sourceId}" data-observation-date="${station.date}" data-longitude="${station.longitude}" data-latitude="${station.latitude}" data-maximum-sample-depth-m="${station.maximumSampleDepthM}" data-forward-x="${forward.x}" data-forward-y="${forward.y}" data-native-cell="${forward.nativeCell}" data-component="${forward.component}"><circle cx="${n(x)}" cy="${n(y)}" r="${n(radius)}" fill="#174a7e" stroke="#f4f5f5" stroke-width="0.055"/><circle cx="${n(x)}" cy="${n(y)}" r="0.07" fill="#74c9e8" stroke="#102c46" stroke-width="0.018"/><title>${station.id}: observed 2018 water-column sampling to ${station.maximumSampleDepthM} m</title></g>`;
}

function titleAndProvenance(manifest, layout, edition, stationLayer) {
    const width = layout.frame[0] / 100;
    const height = layout.frame[1] / 100;
    const editionLabel = edition.editionStatus === 'partial'
        ? `${edition.year} PARTIAL EDITION`
        : `${edition.year} COMPLETE EDITION`;
    const classes = manifest.evidenceClasses.map((value) =>
        `${value.id}: ${value.renderDisposition}`).join('  ·  ');
    return `<g id="anthropocene-water-debris-experiment" data-lifecycle="exploration-only" data-edition-year="${edition.year}" data-edition-status="${edition.editionStatus}" data-data-through="${edition.dataThrough}" data-observed-field-maximum-opacity="0.6" data-title-scale="2" data-standard-promotion-authorized="false" data-public-release-authorized="false">
${stationLayer}
<g id="water-debris-title-and-provenance">
<rect x="0" y="0" width="${n(width)}" height="1.58" fill="#f4f5f5" fill-opacity="0.95"/>
<text x="0.32" y="0.43" font-family="Atkinson Hyperlegible" font-size="0.42" font-weight="700" fill="#15252e">ANTHROPOCENE WATER DEBRIS / ${editionLabel}</text>
<text x="0.32" y="0.76" font-family="Atkinson Hyperlegible" font-size="0.15" fill="#334b58">Five observed 2018 North Pacific depth stations; all other source families are context-only or unavailable.</text>
<text x="0.32" y="1.03" font-family="Atkinson Hyperlegible" font-size="0.125" fill="#4a5961">Sources used: NOAA MDMAP · NOAA 2024 survey design · Ocean Cleanup overview · 2015–2022 surface study · 2018 depth study</text>
<text x="0.32" y="1.30" font-family="Atkinson Hyperlegible" font-size="0.105" fill="#59656b">${xml(classes)}</text>
<circle cx="${n(width - 3.7)}" cy="0.43" r="0.12" fill="#174a7e" fill-opacity="0.6" stroke="#f4f5f5" stroke-width="0.025"/>
<text x="${n(width - 3.45)}" y="0.47" font-family="Atkinson Hyperlegible" font-size="0.13" fill="#334b58">observed depth-profile station</text>
</g>
<g id="water-debris-claim-boundary">
<rect x="0" y="${n(height - 0.62)}" width="${n(width)}" height="0.62" fill="#f4f5f5" fill-opacity="0.94"/>
<text x="${n(width / 2)}" y="${n(height - 0.38)}" text-anchor="middle" font-family="Atkinson Hyperlegible" font-size="0.12" fill="#334b58">Surface observations, model fields, shoreline surveys, cleanup operations, and depth profiles remain separate evidence classes.</text>
<text x="${n(width / 2)}" y="${n(height - 0.16)}" text-anchor="middle" font-family="Atkinson Hyperlegible" font-size="0.11" fill="#5a4a58">No garbage-patch polygon or invented thickness: unknown depth is UNAVAILABLE, not zero.</text>
</g>
</g>`;
}

function transformSvg(source, manifest, layout, edition, overlay) {
    const outputBase = `anthropocene-water-debris-${edition.year}-${layout.suffix}`;
    let value = source.replaceAll(layout.sourceBase, outputBase);
    value = value.replace(/<title>[\s\S]*?<\/title>/,
        `<title>${outputBase}</title>`);
    value = value.replace(/<desc>[\s\S]*?<\/desc>/,
        `<desc>Exploration-only ${edition.year} water-debris evidence edition. Only five 2018 depth-profile stations are rendered as observations; every other listed source remains context-only or unavailable.</desc>`);
    const firstGroup = value.indexOf('<g ');
    requireCondition(firstGroup >= 0, `${layout.sourceBase} has no group boundary`);
    const metadata = `<metadata id="anthropocene-water-debris-metadata" data-pass-id="anthropocene-water-debris-${edition.year}" data-lifecycle="exploration-only" data-edition-status="${edition.editionStatus}" data-data-through="${edition.dataThrough}" data-source-manifest="fixtures/anthropocene-water-debris/v1/manifest.json" data-rendered-observation-source="ocean-cleanup-depth-2020" data-rendered-observation-period="2018-11-01/2018-12-04" data-context-only-source-count="4" data-unavailable-depth-rule="UNAVAILABLE-not-zero" data-standard-promotion-authorized="false" data-default-generation-authorized="false" data-public-release-authorized="false"></metadata>\n`;
    value = value.slice(0, firstGroup) + metadata + value.slice(firstGroup);
    value = value.replace('</svg>', `${overlay}\n</svg>`);
    requireCondition(value.includes('data-lifecycle="exploration-only"')
        && value.includes('data-observed-field-maximum-opacity="0.6"')
        && value.includes('No garbage-patch polygon or invented thickness'),
    `${outputBase} lost its claim boundary`);
    return {outputBase, value};
}

const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
requireCondition(manifest.lifecycle === 'exploration-only'
    && manifest.depthStations.length === 5
    && manifest.sources.length >= 5
    && manifest.style.observedFieldMaximumOpacity === 0.6
    && manifest.promotion.standardLifecycleAuthorized === false
    && manifest.promotion.publicReleaseAuthorized === false,
'Water-debris manifest attempts an unsupported claim or promotion');
requireCondition(manifest.sources.filter((value) =>
    value.renderRole === 'observed-geometry').length === 1,
'The first water-debris experiment may render exactly one reviewed source family');

const runtime = await createCartofreako();
for (const layout of manifest.layouts) {
    const projection = runtime.projection({
        name: layout.runtimeProjection,
        frame: layout.frame
    });
    const markers = manifest.depthStations.map((station) =>
        stationMarker(station,
            projection.forward([station.longitude, station.latitude])))
        .join('\n');
    projection.dispose();
    const stationLayer = `<g id="depth-profile-observations" style="display:inline;opacity:${manifest.style.observedFieldMaximumOpacity}" data-default-visible="true" data-evidence-class="depth-profile" data-observation-count="${manifest.depthStations.length}" data-source-id="ocean-cleanup-depth-2020"><title>Observed 2018 water-column depth-profile stations</title>\n${markers}\n</g>`;
    const sourcePath = path.join(root, 'assets.generated',
        layout.projectionDirectory, 'svg', `${layout.sourceBase}.svg`);
    const source = await fs.readFile(sourcePath, 'utf8');
    for (const edition of manifest.years) {
        const overlay = titleAndProvenance(
            manifest, layout, edition, stationLayer);
        const transformed = transformSvg(
            source, manifest, layout, edition, overlay);
        const output = path.join(root, 'assets.generated',
            layout.projectionDirectory, 'svg', `${transformed.outputBase}.svg`);
        await fs.mkdir(path.dirname(output), {recursive: true});
        await fs.writeFile(output, transformed.value, 'utf8');
        console.log(`Generated ${path.relative(root, output)}`);
    }
}

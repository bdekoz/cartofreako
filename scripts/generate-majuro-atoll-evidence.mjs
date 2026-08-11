#!/usr/bin/env node

import {execFile} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {promisify} from 'node:util';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';

const exec = promisify(execFile);
const root = path.resolve(new URL('..', import.meta.url).pathname);
const passManifestPath = path.join(
    root, 'fixtures/atoll-evidence/v1/pass-manifest.json');
const preparedDirectory = path.join(root, 'assets.static/atoll-evidence/prepared');
const dataDirectory = path.join(root, 'assets.static/atoll-evidence');
const center = {longitude: 171.230319, latitude: 7.1226005};

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

function number(value) {
    return Number(value.toFixed(6)).toString();
}

async function sha256(value) {
    const digest = createHash('sha256');
    digest.update(await fs.readFile(value));
    return digest.digest('hex');
}

async function verifyFile(record) {
    const value = path.join(root, record.path);
    const stat = await fs.stat(value);
    requireCondition(stat.size === record.bytes,
        `${record.path} byte size does not match its manifest`);
    requireCondition(await sha256(value) === record.sha256,
        `${record.path} SHA-256 does not match its manifest`);
    return value;
}

async function pngRecord(value) {
    const data = await fs.readFile(value);
    requireCondition(data.subarray(0, 8).equals(
        Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
    `${value} is not a PNG`);
    return {
        width: data.readUInt32BE(16),
        height: data.readUInt32BE(20),
        sha256: createHash('sha256').update(data).digest('hex'),
        bytes: data.length,
        href: `data:image/png;base64,${data.toString('base64')}`
    };
}

function containRect(image, box) {
    const scale = Math.min(box.width / image.width, box.height / image.height);
    const width = image.width * scale;
    const height = image.height * scale;
    return {
        x: box.x + (box.width - width) / 2,
        y: box.y + (box.height - height) / 2,
        width,
        height
    };
}

function rect({x, y, width, height}, options = {}) {
    const fill = options.fill ?? '#dfe8ec';
    const stroke = options.stroke ?? '#35454d';
    const strokeWidth = options.strokeWidth ?? 0.035;
    const radius = options.radius ?? 0;
    return `<rect x="${number(x)}" y="${number(y)}" width="${number(width)}" height="${number(height)}" rx="${number(radius)}" fill="${fill}" stroke="${stroke}" stroke-width="${number(strokeWidth)}"/>`;
}

function imageElement(image, geometry, opacity = 1) {
    return `<image x="${number(geometry.x)}" y="${number(geometry.y)}" width="${number(geometry.width)}" height="${number(geometry.height)}" preserveAspectRatio="none" opacity="${number(opacity)}" href="${xml(image.href)}"/>`;
}

function textLine(x, y, value, options = {}) {
    const size = options.size ?? 0.28;
    const weight = options.weight ?? 400;
    const fill = options.fill ?? '#151b1f';
    const anchor = options.anchor ?? 'start';
    const letterSpacing = options.letterSpacing ?? 0;
    return `<text x="${number(x)}" y="${number(y)}" font-family="Atkinson Hyperlegible" font-size="${number(size)}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="${number(letterSpacing)}">${xml(value)}</text>`;
}

function textBlock(x, y, lines, options = {}) {
    const size = options.size ?? 0.25;
    const lineHeight = options.lineHeight ?? size * 1.35;
    const weight = options.weight ?? 400;
    const fill = options.fill ?? '#526169';
    const spans = lines.map((line, index) =>
        `<tspan x="${number(x)}" y="${number(y + index * lineHeight)}">${xml(line)}</tspan>`).join('');
    return `<text font-family="Atkinson Hyperlegible" font-size="${number(size)}" font-weight="${weight}" fill="${fill}">${spans}</text>`;
}

function layer(id, label, content) {
    return `<g id="${id}" inkscape:groupmode="layer" inkscape:label="${xml(label)}" style="display:inline"><title>${xml(label)}</title>${content.join('')}</g>`;
}

function panelLayer(id, label, box, image, extra = []) {
    const imageGeometry = containRect(image, box);
    return {
        geometry: imageGeometry,
        svg: layer(id, label, [
            rect(box, {fill: '#dfe8ec'}),
            imageElement(image, imageGeometry),
            rect(box, {fill: 'none', stroke: '#35454d', strokeWidth: 0.035}),
            ...extra
        ])
    };
}

function markerElements(contextGeometry, layout, trace) {
    const [logicalWidth, logicalHeight] = trace.runtimeFrame;
    const x = contextGeometry.x
        + contextGeometry.width * trace.forward.x / logicalWidth;
    const y = contextGeometry.y
        + contextGeometry.height * trace.forward.y / logicalHeight;
    const radius = Math.max(0.13, Math.min(layout.page.widthInches,
        layout.page.heightInches) * 0.0065);
    return [
        `<circle cx="${number(x)}" cy="${number(y)}" r="${number(radius)}" fill="#111820" stroke="#fff45b" stroke-width="${number(radius * 0.34)}"/>`,
        `<circle cx="${number(x)}" cy="${number(y)}" r="${number(radius * 1.55)}" fill="none" stroke="#fff45b" stroke-width="${number(radius * 0.16)}" opacity="0.92"/>`
    ];
}

function landscapeComposition(layout, images, trace) {
    const width = layout.page.widthInches;
    const height = layout.page.heightInches;
    const margin = 0.78;
    const gap = 0.62;
    const columnWidth = (width - 2 * margin - 2 * gap) / 3;
    const panelTop = 2.72;
    const panelHeight = Math.min(7.25, height * 0.38);
    const boxes = [0, 1, 2].map(index => ({
        x: margin + index * (columnWidth + gap),
        y: panelTop,
        width: columnWidth,
        height: panelHeight
    }));

    const contextGeometry = containRect(images.context, boxes[0]);
    const context = layer('planetary-context', 'Planetary context', [
        rect(boxes[0], {fill: '#ffffff'}),
        imageElement(images.context, contextGeometry),
        ...markerElements(contextGeometry, layout, trace),
        rect(boxes[0], {fill: 'none', stroke: '#35454d', strokeWidth: 0.035})
    ]);
    const observation = panelLayer(
        'observation-topobathymetry', 'Observation — topobathymetry',
        boxes[1], images.topobathy).svg;
    const probabilityGeometry = containRect(images.probability, boxes[2]);
    const probability = layer(
        'scenario-inundation-probability',
        'Scenario — inundation probability', [
            rect(boxes[2], {fill: '#e7ecee'}),
            imageElement(images.probability, probabilityGeometry),
            rect(boxes[2], {fill: 'none', stroke: '#35454d', strokeWidth: 0.035})
        ]);
    const deterministic = layer(
        'scenario-inundation-deterministic',
        'Scenario — deterministic inundation extent', [
            imageElement(images.deterministicEdge, probabilityGeometry)
        ]);

    const textTop = panelTop + panelHeight;
    const provenance = [
        textLine(margin, 1.08, 'MAJURO ATOLL — EVIDENCE PASS',
            {size: 0.74, weight: 700}),
        textLine(margin, 1.67,
            `EXPLORATION ONLY · ${layout.label} planetary carrier · observation and scenario remain separate · not navigation or engineering`,
            {size: 0.255, fill: '#526169'}),
        textLine(boxes[0].x, 2.35, 'PLANETARY CONTEXT',
            {size: 0.29, weight: 700, fill: '#155b78', letterSpacing: 0.012}),
        textLine(boxes[1].x, 2.35, 'OBSERVATION / DERIVED SURFACE',
            {size: 0.29, weight: 700, fill: '#236346', letterSpacing: 0.012}),
        textLine(boxes[2].x, 2.35, 'SCENARIO / NOT OBSERVATION',
            {size: 0.29, weight: 700, fill: '#713b88', letterSpacing: 0.012}),
        textLine(boxes[0].x, textTop + 0.56, `${layout.label} water carrier`,
            {size: 0.39, weight: 700}),
        textBlock(boxes[0].x, textTop + 1.05, [
            'Yellow ring: USGS TBDEM metadata-envelope center',
            `Forward + qualified reverse: cell ${trace.forward.nativeCell}, component ${trace.forward.component}`,
            'The carrier locates Majuro; it is not the analytical grid.'
        ], {size: 0.235, lineHeight: 0.32}),
        textLine(boxes[1].x, textTop + 0.56, 'USGS 1 m Majuro TBDEM',
            {size: 0.39, weight: 700}),
        textBlock(boxes[1].x, textTop + 1.05, [
            '1944–2016 multi-source composite · LMSL heights',
            'ITRF2008 / UTM zone 59N · checked ~10 m derivative',
            'Land RMSE 0.197 m; bathymetry RMSE varies by source.',
            'The 1 m source remains authoritative and local-only.'
        ], {size: 0.235, lineHeight: 0.32}),
        textLine(boxes[2].x, textTop + 0.56, 'USGS marine inundation · 30 in',
            {size: 0.39, weight: 700}),
        textBlock(boxes[2].x, textTop + 1.05, [
            '0.762 m above Mean Higher High Water',
            'Color: Monte Carlo inundation probability, 0–1',
            'White outline: deterministic static-water extent',
            'Vertical RMSE 0.192 m; 30 in supports 95% confidence.',
            'Source surface 2016 · analysis 2018 · release 2019.'
        ], {size: 0.225, lineHeight: 0.305}),
        textLine(margin, height - 4.25,
            'SOURCE-GOVERNED FULL PASS · VISUAL APPROVAL DOES NOT AUTHORIZE LIFECYCLE PROMOTION',
            {size: 0.245, weight: 700, fill: '#713b88'})
    ];

    const unavailableBox = {
        x: margin,
        y: height - 3.75,
        width: width - 2 * margin,
        height: 3.05
    };
    const unavailable = layer('unavailable-evidence',
        'Unavailable and not asserted', [
            rect(unavailableBox, {fill: '#e3e7e8', stroke: '#aeb8bc', radius: 0.18}),
            textLine(unavailableBox.x + 0.42, unavailableBox.y + 0.62,
                'UNAVAILABLE / NOT ASSERTED',
                {size: 0.31, weight: 700, fill: '#762d36'}),
            textBlock(unavailableBox.x + 0.42, unavailableBox.y + 1.13, [
                'Freshwater spatial field · authoritative infrastructure · current independent shoreline · reviewed benthic reef geometry',
                'Ocean heat is not rendered · community/regional review is not established · no standard, release, or publication decision exists'
            ], {size: 0.235, lineHeight: 0.41, fill: '#151b1f'}),
            textLine(unavailableBox.x + 0.42, unavailableBox.y + 2.52,
                'LIFECYCLE: EXPLORATION ONLY',
                {size: 0.26, weight: 700, fill: '#713b88'})
        ]);

    return {context, observation, probability, deterministic,
        provenance: layer('evidence-provenance', 'Evidence provenance', provenance),
        unavailable};
}

function portraitComposition(layout, images, trace) {
    const width = layout.page.widthInches;
    const height = layout.page.heightInches;
    const contextBox = {x: 1.0, y: 3.3, width: 12.9, height: 16.7};
    const observationBox = {x: 15.0, y: 3.3, width: 18.0, height: 9.25};
    const scenarioBox = {x: 15.0, y: 16.25, width: 18.0, height: 5.76};
    const contextGeometry = containRect(images.context, contextBox);
    const probabilityGeometry = containRect(images.probability, scenarioBox);

    const context = layer('planetary-context', 'Planetary context', [
        rect(contextBox, {fill: '#ffffff'}),
        imageElement(images.context, contextGeometry),
        ...markerElements(contextGeometry, layout, trace),
        rect(contextBox, {fill: 'none', stroke: '#35454d', strokeWidth: 0.035})
    ]);
    const observation = panelLayer(
        'observation-topobathymetry', 'Observation — topobathymetry',
        observationBox, images.topobathy).svg;
    const probability = layer(
        'scenario-inundation-probability',
        'Scenario — inundation probability', [
            rect(scenarioBox, {fill: '#e7ecee'}),
            imageElement(images.probability, probabilityGeometry),
            rect(scenarioBox, {fill: 'none', stroke: '#35454d', strokeWidth: 0.035})
        ]);
    const deterministic = layer(
        'scenario-inundation-deterministic',
        'Scenario — deterministic inundation extent', [
            imageElement(images.deterministicEdge, probabilityGeometry)
        ]);

    const provenance = [
        textLine(1.0, 1.18, 'MAJURO ATOLL — EVIDENCE PASS',
            {size: 0.76, weight: 700}),
        textLine(1.0, 1.82,
            'EXPLORATION ONLY · STAR-X VERTICAL CARRIER · OBSERVATION AND SCENARIO REMAIN SEPARATE',
            {size: 0.25, fill: '#526169'}),
        textLine(1.0, 2.88, 'PLANETARY CONTEXT',
            {size: 0.3, weight: 700, fill: '#155b78'}),
        textLine(15.0, 2.88, 'OBSERVATION / DERIVED SURFACE',
            {size: 0.3, weight: 700, fill: '#236346'}),
        textLine(15.0, 15.82, 'SCENARIO / NOT OBSERVATION',
            {size: 0.3, weight: 700, fill: '#713b88'}),
        textLine(1.0, 20.68, 'Star-X water carrier',
            {size: 0.42, weight: 700}),
        textBlock(1.0, 21.25, [
            'Yellow ring: USGS TBDEM envelope center',
            `Forward + reverse: cell ${trace.forward.nativeCell}, component ${trace.forward.component}`,
            'Carrier only; not the analytical grid.'
        ], {size: 0.245, lineHeight: 0.34}),
        textLine(15.0, 13.2, 'USGS 1 m Majuro TBDEM',
            {size: 0.42, weight: 700}),
        textBlock(15.0, 13.78, [
            '1944–2016 composite · LMSL heights',
            'ITRF2008 / UTM zone 59N · checked ~10 m derivative',
            'Land RMSE 0.197 m; bathymetry varies by source.',
            'The 1 m source remains authoritative and local-only.'
        ], {size: 0.245, lineHeight: 0.34}),
        textLine(15.0, 22.7, 'USGS marine inundation · 30 in',
            {size: 0.42, weight: 700}),
        textBlock(15.0, 23.28, [
            '0.762 m above Mean Higher High Water',
            'Color: probability, 0–1 · white: deterministic outline',
            'Vertical RMSE 0.192 m · 750 Monte Carlo realizations',
            'Scenario source 2016 · analysis 2018 · release 2019.'
        ], {size: 0.245, lineHeight: 0.34}),
        textLine(1.0, 25.5, 'EVIDENCE RELATIONSHIP',
            {size: 0.32, weight: 700, fill: '#236346'}),
        textBlock(1.0, 26.08, [
            'The high-resolution panels remain in the source analytical CRS.',
            'Star-X supplies planetary relation and a reversible locator.',
            'No global carrier cell inherits the TBDEM resolution or certainty.',
            'This plate is visual/research exploration, not navigation or engineering.'
        ], {size: 0.255, lineHeight: 0.39, fill: '#151b1f'}),
        textLine(17.2, 25.5, 'TRACE AND LIFECYCLE',
            {size: 0.32, weight: 700, fill: '#713b88'}),
        textBlock(17.2, 26.08, [
            `Forward pixel: ${trace.forward.x.toFixed(4)}, ${trace.forward.y.toFixed(4)}`,
            `Qualified reverse: ${trace.qualifiedInverse.status}; residual ${trace.qualifiedInverse.candidate.forwardResidual.toExponential(2)}`,
            'Visual approval authorizes the six-layout artifact implementation.',
            'It does not authorize standard/default generation, release, or S3.'
        ], {size: 0.255, lineHeight: 0.39, fill: '#151b1f'})
    ];

    const unavailableBox = {x: 1.0, y: 36.2, width: 32.0, height: 6.7};
    const unavailable = layer('unavailable-evidence',
        'Unavailable and not asserted', [
            rect(unavailableBox, {fill: '#e3e7e8', stroke: '#aeb8bc', radius: 0.22}),
            textLine(1.55, 37.1, 'UNAVAILABLE / NOT ASSERTED',
                {size: 0.36, weight: 700, fill: '#762d36'}),
            textBlock(1.55, 37.85, [
                'Freshwater spatial field · authoritative infrastructure',
                'Current independent shoreline · reviewed benthic reef geometry',
                'Ocean heat · Marshall Islands community/regional review',
                'No missing field is encoded as zero, certainty, or implied absence.'
            ], {size: 0.285, lineHeight: 0.48, fill: '#151b1f'}),
            textLine(1.55, 40.4, 'LIFECYCLE: EXPLORATION ONLY',
                {size: 0.32, weight: 700, fill: '#713b88'}),
            textBlock(1.55, 41.05, [
                'The Antarctic 60°S Star-X component remains part of the context carrier.',
                'This pass makes no claim about a current shoreline, observed flood, forecast, or engineering suitability.'
            ], {size: 0.25, lineHeight: 0.44})
        ]);

    return {context, observation, probability, deterministic,
        provenance: layer('evidence-provenance', 'Evidence provenance', provenance),
        unavailable};
}

function svgDocument(layout, images, trace, sourceManifest, panelHashes) {
    const page = layout.page;
    const composition = layout.composition === 'portrait-star-x'
        ? portraitComposition(layout, images, trace)
        : landscapeComposition(layout, images, trace);
    const metadata = `<metadata id="majuro-atoll-evidence-metadata" data-pass-id="majuro-atoll-evidence" data-lifecycle="exploration-only" data-maturity="visual-approved-full-pass-implementation" data-visual-approval="approved" data-standard-promotion-authorized="false" data-projection="${xml(layout.runtimeProjection)}" data-context-source-sha256="${layout.context.sourceSha256}" data-context-sha256="${layout.context.sha256}" data-source-manifest-sha256="${sourceManifest.sha256}" data-topobathymetry-sha256="${panelHashes.topobathy}" data-inundation-probability-sha256="${panelHashes.probability}" data-inundation-deterministic-edge-sha256="${panelHashes.deterministicEdge}" data-source-longitude="${center.longitude}" data-source-latitude="${center.latitude}" data-forward-x="${trace.forward.x}" data-forward-y="${trace.forward.y}" data-native-cell="${trace.forward.nativeCell}" data-component="${trace.forward.component}" data-reverse-status="${trace.qualifiedInverse.status}" data-reverse-residual="${trace.qualifiedInverse.candidate.forwardResidual}" data-observation-period="1944/2016 composite" data-scenario-water-level-m="0.762" data-scenario-datum="Mean Higher High Water" data-community-regional-review="UNAVAILABLE"></metadata>`;
    return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" role="img" aria-labelledby="majuro-atoll-title majuro-atoll-desc" id="majuro-atoll-evidence-${xml(layout.id)}" width="${page.widthInches}in" height="${page.heightInches}in" viewBox="0 0 ${page.widthInches} ${page.heightInches}">
<title id="majuro-atoll-title">Majuro Atoll evidence pass — ${xml(layout.label)}</title>
<desc id="majuro-atoll-desc">Exploration-only source-governed Majuro topobathymetry observation and separately labeled 30-inch marine-inundation scenario with a reversible ${xml(layout.label)} planetary locator.</desc>
${metadata}
${layer('atoll-evidence-background', 'Atoll evidence background', [rect({x: 0, y: 0, width: page.widthInches, height: page.heightInches}, {fill: '#f4f5f5', stroke: 'none', strokeWidth: 0})])}
${composition.context}
${composition.observation}
${composition.probability}
${composition.deterministic}
${composition.provenance}
${composition.unavailable}
</svg>
`;
}

function validateSvg(value, layout) {
    const withoutEmbeddedPng = value.replace(
        /data:image\/png;base64,[A-Za-z0-9+/=]+/g, '');
    requireCondition(!/\b(?:nan|inf(?:inity)?)\b/i.test(withoutEmbeddedPng),
        `${layout.id} SVG contains a non-finite token`);
    for (const id of [
        'atoll-evidence-background', 'planetary-context',
        'observation-topobathymetry', 'scenario-inundation-probability',
        'scenario-inundation-deterministic', 'evidence-provenance',
        'unavailable-evidence']) {
        requireCondition(value.includes(`id="${id}"`),
            `${layout.id} SVG is missing layer ${id}`);
    }
    requireCondition((value.match(/data:image\/png;base64,/g) ?? []).length === 4,
        `${layout.id} SVG must embed exactly four hash-pinned PNG inputs`);
    requireCondition(value.includes('data-lifecycle="exploration-only"')
        && value.includes('data-standard-promotion-authorized="false"')
        && value.includes('data-community-regional-review="UNAVAILABLE"'),
    `${layout.id} SVG lost its lifecycle boundary`);
    requireCondition(value.includes(`width="${layout.page.widthInches}in"`)
        && value.includes(`height="${layout.page.heightInches}in"`),
    `${layout.id} SVG lost its print frame`);
}

async function preparePanels(workDirectory) {
    const topobathy = path.join(workDirectory, 'topobathy.png');
    const probability = path.join(workDirectory, 'probability.png');
    const deterministic = path.join(workDirectory, 'deterministic.png');
    const edgeMask = path.join(workDirectory, 'deterministic-edge-mask.png');
    const deterministicEdge = path.join(workDirectory, 'deterministic-edge.png');
    await exec('gdaldem', ['color-relief', '-q', '-of', 'PNG', '-alpha',
        path.join(preparedDirectory, 'majuro-tbdem-observation-10m.tif'),
        path.join(dataDirectory, 'topobathy-colors.txt'), topobathy]);
    await exec('gdaldem', ['color-relief', '-q', '-of', 'PNG', '-alpha',
        path.join(preparedDirectory,
            'majuro-marine-inundation-30in-probability-10m.tif'),
        path.join(dataDirectory, 'inundation-probability-colors.txt'), probability]);
    await exec('gdaldem', ['color-relief', '-q', '-of', 'PNG', '-alpha',
        '-nearest_color_entry',
        path.join(preparedDirectory,
            'majuro-marine-inundation-30in-deterministic-10m.tif'),
        path.join(dataDirectory, 'inundation-deterministic-colors.txt'), deterministic]);
    await exec('magick', [deterministic, '-alpha', 'extract',
        '-morphology', 'EdgeOut', 'Diamond:8', '-threshold', '1', edgeMask]);
    await exec('magick', ['-size', '3973x1272', 'xc:#ffffff', edgeMask,
        '-alpha', 'off', '-compose', 'CopyOpacity', '-composite', deterministicEdge]);
    return {
        topobathy: await pngRecord(topobathy),
        probability: await pngRecord(probability),
        deterministicEdge: await pngRecord(deterministicEdge)
    };
}

function runtimeFrame(layout) {
    const width = layout.page.widthInches * 100;
    const exactHeight = {
        'cahill-keyes': 2200,
        authagraph: 1100 * Math.sqrt(3),
        dymaxion: 1200 * Math.sqrt(3),
        'myriahedral-pacific': 2475,
        'star-x': 4400,
        voronoi: 27500 / 12
    }[layout.runtimeProjection];
    requireCondition(Number.isFinite(exactHeight),
        `No exact runtime frame is defined for ${layout.runtimeProjection}`);
    return [width, exactHeight];
}

function qualifiedTrace(projection, frame) {
    const forward = projection.forward([center.longitude, center.latitude]);
    const inverse = projection.inverse([forward.x, forward.y], {
        nativeCell: forward.nativeCell,
        component: forward.component,
        tolerancePixels: 1e-7
    });
    requireCondition(inverse.status === 'unique' && inverse.candidates.length === 1,
        'Majuro full-pass locator did not produce one qualified reverse candidate');
    const candidate = inverse.candidates[0];
    requireCondition(Math.abs(candidate.longitude - center.longitude) <= 2e-8
        && Math.abs(candidate.latitude - center.latitude) <= 2e-8,
    'Majuro full-pass locator exceeded its geographic round-trip tolerance');
    return {
        forward,
        runtimeFrame: frame,
        qualifiedInverse: {
            status: inverse.status,
            candidate,
            tolerancePixels: inverse.tolerancePx,
            truncated: inverse.truncated
        }
    };
}

const passManifest = JSON.parse(await fs.readFile(passManifestPath, 'utf8'));
requireCondition(passManifest.schemaVersion
    === 'cartofreako-majuro-atoll-evidence-pass-v1',
'Unexpected Majuro pass manifest schema');
requireCondition(passManifest.lifecycle === 'exploration-only'
    && passManifest.promotion.standardLifecycleAuthorized === false
    && passManifest.promotion.publicReleaseAuthorized === false,
'Majuro pass manifest attempts an unauthorized promotion');
const sourceManifestPath = await verifyFile(passManifest.sourceManifest);
await verifyFile(passManifest.coordinateFixture);
await verifyFile(passManifest.visualApproval.artifact);
const sourceManifest = {
    ...passManifest.sourceManifest,
    value: JSON.parse(await fs.readFile(sourceManifestPath, 'utf8'))
};
requireCondition(sourceManifest.value.promotionAuthorized === false,
    'Source canary manifest unexpectedly authorizes promotion');

const workDirectory = await fs.mkdtemp(
    path.join(os.tmpdir(), 'cartofreako-majuro-pass.'));
try {
    const panelImages = await preparePanels(workDirectory);
    const panelHashes = {
        topobathy: panelImages.topobathy.sha256,
        probability: panelImages.probability.sha256,
        deterministicEdge: panelImages.deterministicEdge.sha256
    };
    const runtime = await createCartofreako();
    for (const layout of passManifest.layouts) {
        const contextPath = await verifyFile(layout.context);
        const context = await pngRecord(contextPath);
        requireCondition(context.width === layout.context.width
            && context.height === layout.context.height,
        `${layout.id} context dimensions do not match the pass manifest`);
        const frame = runtimeFrame(layout);
        const projection = runtime.projection({
            name: layout.runtimeProjection,
            frame
        });
        const trace = qualifiedTrace(projection, frame);
        projection.dispose();
        const output = path.join(root, layout.artifacts.svg);
        const value = svgDocument(layout, {
            context,
            topobathy: panelImages.topobathy,
            probability: panelImages.probability,
            deterministicEdge: panelImages.deterministicEdge
        }, trace, sourceManifest, panelHashes);
        validateSvg(value, layout);
        await fs.mkdir(path.dirname(output), {recursive: true});
        await fs.writeFile(output, value, 'utf8');
        console.log(`Generated ${path.relative(root, output)} (${Buffer.byteLength(value)} bytes)`);
    }
} finally {
    await fs.rm(workDirectory, {recursive: true, force: true});
}

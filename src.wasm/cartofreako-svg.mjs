import {GeometryPart} from './cartofreako-web.mjs';

function number(value, precision) {
    return Number(value.toFixed(precision)).toString();
}

function escapeXml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&apos;');
}

function partPath(buffer, part, precision) {
    const begin = buffer.partOffsets[part];
    const end = buffer.partOffsets[part + 1];
    let result = '';
    for (let point = begin; point < end; ++point) {
        const x = number(buffer.coordinates[point * 2], precision);
        const y = number(buffer.coordinates[point * 2 + 1], precision);
        result += `${point === begin ? 'M' : 'L'}${x} ${y}`;
    }
    if (buffer.closed[part]) result += 'Z';
    return result;
}

/** Convert line/ring commands to SVG path data, optionally by feature. */
export function commandBufferToSvgPaths(buffer, {precision = 3} = {}) {
    const paths = new Map();
    for (let part = 0; part < buffer.partTypes.length; ++part) {
        if (buffer.partTypes[part] === GeometryPart.point) continue;
        const featureId = buffer.featureIds[part];
        paths.set(featureId, (paths.get(featureId) ?? '') + partPath(buffer, part, precision));
    }
    return paths;
}

/** Render a command buffer as a standalone, inspectable SVG document. */
export function renderSvg(buffer, {
    title = 'Cartofreako projected geometry',
    description = 'Projected by the Cartofreako WebAssembly runtime.',
    fill = '#deddd4',
    stroke = '#4f5b5f',
    strokeWidth = Math.max(buffer.frame.width, buffer.frame.height) / 2500,
    pointRadius = Math.max(buffer.frame.width, buffer.frame.height) / 500,
    precision = 3,
    className = 'cartofreako-geometry',
    attributes = {}
} = {}) {
    const attributeText = Object.entries(attributes)
        .map(([name, value]) => ` ${escapeXml(name)}="${escapeXml(value)}"`)
        .join('');
    const paths = commandBufferToSvgPaths(buffer, {precision});
    const body = [];
    for (const [featureId, path] of paths) {
        body.push(
            `<path data-feature-id="${featureId}" d="${path}" `
            + `fill="${escapeXml(fill)}" fill-rule="evenodd" `
            + `stroke="${escapeXml(stroke)}" stroke-width="${number(strokeWidth, precision)}"/>`
        );
    }
    for (let part = 0; part < buffer.partTypes.length; ++part) {
        if (buffer.partTypes[part] !== GeometryPart.point) continue;
        for (let point = buffer.partOffsets[part]; point < buffer.partOffsets[part + 1]; ++point) {
            body.push(
                `<circle data-feature-id="${buffer.featureIds[part]}" `
                + `cx="${number(buffer.coordinates[point * 2], precision)}" `
                + `cy="${number(buffer.coordinates[point * 2 + 1], precision)}" `
                + `r="${number(pointRadius, precision)}" fill="${escapeXml(fill)}" `
                + `stroke="${escapeXml(stroke)}"/>`
            );
        }
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" `
        + `viewBox="0 0 ${number(buffer.frame.width, precision)} ${number(buffer.frame.height, precision)}" `
        + `class="${escapeXml(className)}" data-cartofreako-abi="${buffer.abiVersion}"${attributeText}>`
        + `<title>${escapeXml(title)}</title><desc>${escapeXml(description)}</desc>`
        + body.join('')
        + '</svg>';
}

/** Layer exact carrier/ocean geometry behind projected feature geometry. */
export function renderBaseMapSvg(carrier, features, options = {}) {
    if (carrier.frame.width !== features.frame.width
        || carrier.frame.height !== features.frame.height) {
        throw new RangeError('Carrier and feature buffers must use the same slice frame');
    }
    const oceanPaths = [...commandBufferToSvgPaths(carrier, options).values()].join('');
    const landPaths = commandBufferToSvgPaths(features, options);
    const precision = options.precision ?? 3;
    const ocean = options.ocean ?? '#e8f2f5';
    const land = options.land ?? '#deddd4';
    const stroke = options.stroke ?? '#747b78';
    const bodies = [
        `<path d="${oceanPaths}" fill="${escapeXml(ocean)}" stroke="${escapeXml(ocean)}"/>`
    ];
    for (const [featureId, path] of landPaths) {
        bodies.push(
            `<path data-feature-id="${featureId}" d="${path}" fill="${escapeXml(land)}" `
            + `fill-rule="evenodd" stroke="${escapeXml(stroke)}" `
            + `stroke-width="${number(carrier.frame.width / 4000, precision)}"/>`
        );
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 `
        + `${number(carrier.frame.width, precision)} ${number(carrier.frame.height, precision)}" `
        + `data-generator="cartofreako-all-projection-wasm" data-layers="ocean land">`
        + `<title>${escapeXml(options.title ?? 'Cartofreako base map')}</title>`
        + `<g id="ocean">${bodies[0]}</g><g id="land">${bodies.slice(1).join('')}</g></svg>`;
}

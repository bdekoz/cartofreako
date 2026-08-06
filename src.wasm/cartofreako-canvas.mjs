import {GeometryPart} from './cartofreako-web.mjs';

/** Replay the shared geometry command buffer to Canvas or OffscreenCanvas. */
export function drawCommandBuffer(context, buffer, {
    fillStyle = '#deddd4',
    strokeStyle = '#4f5b5f',
    lineWidth = Math.max(buffer.frame.width, buffer.frame.height) / 2500,
    pointRadius = Math.max(buffer.frame.width, buffer.frame.height) / 500,
    clear = false,
    fill = true,
    stroke = true
} = {}) {
    if (clear) context.clearRect(0, 0, buffer.frame.width, buffer.frame.height);
    context.fillStyle = fillStyle;
    context.strokeStyle = strokeStyle;
    context.lineWidth = lineWidth;

    const featureParts = new Map();
    for (let part = 0; part < buffer.partTypes.length; ++part) {
        const featureId = buffer.featureIds[part];
        if (!featureParts.has(featureId)) featureParts.set(featureId, []);
        featureParts.get(featureId).push(part);
    }
    for (const parts of featureParts.values()) {
        context.beginPath();
        let hasPath = false;
        for (const part of parts) {
            const begin = buffer.partOffsets[part];
            const end = buffer.partOffsets[part + 1];
            if (buffer.partTypes[part] === GeometryPart.point) {
                for (let point = begin; point < end; ++point) {
                    const x = buffer.coordinates[point * 2];
                    const y = buffer.coordinates[point * 2 + 1];
                    context.moveTo(x + pointRadius, y);
                    context.arc(x, y, pointRadius, 0, Math.PI * 2);
                    hasPath = true;
                }
                continue;
            }
            for (let point = begin; point < end; ++point) {
                const x = buffer.coordinates[point * 2];
                const y = buffer.coordinates[point * 2 + 1];
                if (point === begin) context.moveTo(x, y);
                else context.lineTo(x, y);
            }
            if (buffer.closed[part]) context.closePath();
            hasPath = hasPath || end > begin;
        }
        if (!hasPath) continue;
        if (fill) context.fill('evenodd');
        if (stroke) context.stroke();
    }
}

/** Draw exact carrier faces and then arbitrary projected features. */
export function drawBaseMap(context, carrier, features, options = {}) {
    drawCommandBuffer(context, carrier, {
        fillStyle: options.ocean ?? '#e8f2f5',
        strokeStyle: options.ocean ?? '#e8f2f5',
        clear: options.clear ?? true,
        lineWidth: options.oceanSeamWidth ?? carrier.frame.width / 2500
    });
    drawCommandBuffer(context, features, {
        fillStyle: options.land ?? '#deddd4',
        strokeStyle: options.stroke ?? '#747b78',
        clear: false,
        lineWidth: options.lineWidth ?? carrier.frame.width / 4000
    });
}

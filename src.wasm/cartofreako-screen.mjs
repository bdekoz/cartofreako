function requireFinitePositive(value, label) {
    const number = Number(value);
    if (!Number.isFinite(number) || number <= 0) {
        throw new TypeError(`${label} must be finite and greater than zero`);
    }
    return number;
}

function dimensions(value, label) {
    if (!value || typeof value !== 'object') {
        throw new TypeError(`${label} must contain width and height`);
    }
    return Object.freeze({
        width: requireFinitePositive(value.width, `${label}.width`),
        height: requireFinitePositive(value.height, `${label}.height`)
    });
}

function pair(value, label) {
    if (!(Array.isArray(value) || ArrayBuffer.isView(value)) || value.length !== 2) {
        throw new TypeError(`${label} must be a two-coordinate array`);
    }
    const x = Number(value[0]);
    const y = Number(value[1]);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
        throw new TypeError(`${label} coordinates must be finite`);
    }
    return [x, y];
}

function matrix(value, label) {
    if (!Array.isArray(value) || value.length !== 9
        || value.some((entry) => !Number.isFinite(entry))) {
        throw new TypeError(`${label} must be a finite row-major 3-by-3 matrix`);
    }
    return value;
}

/** Create a pixel-snapped contain transform without cropping the source frame. */
export function containTransform(sourceFrame, canvas = {width: 1920, height: 1080}, {
    background = '#f4f5f5',
    contentSize = null
} = {}) {
    const source = dimensions(sourceFrame, 'sourceFrame');
    const target = dimensions(canvas, 'canvas');
    const scale = Math.min(target.width / source.width, target.height / source.height);
    const content = contentSize == null
        ? {width: Math.round(source.width * scale), height: Math.round(source.height * scale)}
        : dimensions(contentSize, 'contentSize');
    if (content.width > target.width || content.height > target.height) {
        throw new RangeError('contain content exceeds its canvas');
    }
    const x = (target.width - content.width) / 2;
    const y = (target.height - content.height) / 2;
    const scaleX = content.width / source.width;
    const scaleY = content.height / source.height;
    const projectedToScreen = Object.freeze([
        scaleX, 0, x,
        0, scaleY, y,
        0, 0, 1
    ]);
    const screenToProjected = Object.freeze([
        1 / scaleX, 0, -x / scaleX,
        0, 1 / scaleY, -y / scaleY,
        0, 0, 1
    ]);
    return Object.freeze({
        fit: 'contain',
        background,
        sourceFrame: source,
        canvas: target,
        contentRectangle: Object.freeze({x, y, ...content}),
        projectedToScreen,
        screenToProjected
    });
}

/** Apply an artifact's projected-to-screen affine matrix. */
export function projectedToScreen(projected, contract) {
    const [x, y] = pair(projected, 'projected coordinate');
    const transform = matrix(contract?.projectedToScreen, 'projectedToScreen');
    return Object.freeze([
        transform[0] * x + transform[1] * y + transform[2],
        transform[3] * x + transform[4] * y + transform[5]
    ]);
}

/** Convert a screen point to projection units, rejecting letterbox padding by default. */
export function screenToProjected(screen, contract, {allowPadding = false} = {}) {
    const [x, y] = pair(screen, 'screen coordinate');
    const rectangle = contract?.contentRectangle;
    if (!rectangle || !Number.isFinite(rectangle.x) || !Number.isFinite(rectangle.y)
        || !Number.isFinite(rectangle.width) || !Number.isFinite(rectangle.height)) {
        throw new TypeError('contentRectangle must be finite');
    }
    const inside = x >= rectangle.x && x <= rectangle.x + rectangle.width
        && y >= rectangle.y && y <= rectangle.y + rectangle.height;
    if (!inside && !allowPadding) {
        throw new RangeError('screen coordinate is in contain-fit padding');
    }
    const transform = matrix(contract?.screenToProjected, 'screenToProjected');
    return Object.freeze([
        transform[0] * x + transform[1] * y + transform[2],
        transform[3] * x + transform[4] * y + transform[5]
    ]);
}

/** Convert a screen pick into the runtime's candidate-aware geographic result. */
export function screenToGeographic(projection, screen, artifact, inverseOptions = {}) {
    if (!projection || typeof projection.inverse !== 'function') {
        throw new TypeError('projection must provide inverse()');
    }
    const contract = artifact?.screen ?? artifact;
    return projection.inverse(screenToProjected(screen, contract), inverseOptions);
}

/** Return a dependency-free plane description usable by Three.js or WebGL. */
export function flatTexturePlane(contract) {
    const canvas = dimensions(contract?.canvas, 'canvas');
    return Object.freeze({
        primitive: 'triangle-strip',
        positions: Object.freeze([
            -canvas.width / 2, -canvas.height / 2, 0,
             canvas.width / 2, -canvas.height / 2, 0,
            -canvas.width / 2,  canvas.height / 2, 0,
             canvas.width / 2,  canvas.height / 2, 0
        ]),
        textureCoordinates: Object.freeze([0, 1, 1, 1, 0, 0, 1, 0]),
        warning: 'Interrupted flat map; do not wrap as an equirectangular globe texture.'
    });
}

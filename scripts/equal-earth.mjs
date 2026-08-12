// Spherical Equal Earth equations used by Stage 16J tools.

export const coefficients = Object.freeze({
    a1: 1.340264,
    a2: -0.081106,
    a3: 0.000893,
    a4: 0.003796,
    m: Math.sqrt(3) / 2
});

export const radiansPerDegree = Math.PI / 180;
export const degreesPerRadian = 180 / Math.PI;

export function canonicalLongitudeDegrees(value) {
    while (value > 180) value -= 360;
    while (value < -180) value += 360;
    return value;
}

export function relativeLongitudeRadians(longitudeDegrees,
    centralMeridianDegrees = 0) {
    return canonicalLongitudeDegrees(longitudeDegrees - centralMeridianDegrees)
        * radiansPerDegree;
}

export function forwardRaw(longitudeRadians, latitudeRadians) {
    const {a1, a2, a3, a4, m} = coefficients;
    const theta = Math.asin(m * Math.sin(latitudeRadians));
    const theta2 = theta * theta;
    const theta6 = theta2 * theta2 * theta2;
    const derivative = a1 + 3 * a2 * theta2
        + theta6 * (7 * a3 + 9 * a4 * theta2);
    return [
        longitudeRadians * Math.cos(theta) / (m * derivative),
        theta * (a1 + a2 * theta2 + theta6 * (a3 + a4 * theta2))
    ];
}

export function inverseRaw(x, y) {
    const {a1, a2, a3, a4, m} = coefficients;
    let theta = y;
    for (let index = 0; index < 12; ++index) {
        const theta2 = theta * theta;
        const theta6 = theta2 * theta2 * theta2;
        const value = theta * (a1 + a2 * theta2
            + theta6 * (a3 + a4 * theta2)) - y;
        const derivative = a1 + 3 * a2 * theta2
            + theta6 * (7 * a3 + 9 * a4 * theta2);
        const delta = value / derivative;
        theta -= delta;
        if (Math.abs(delta) < 1e-12) break;
    }
    const theta2 = theta * theta;
    const theta6 = theta2 * theta2 * theta2;
    const derivative = a1 + 3 * a2 * theta2
        + theta6 * (7 * a3 + 9 * a4 * theta2);
    return [
        coefficients.m * x * derivative / Math.cos(theta),
        Math.asin(Math.max(-1, Math.min(1, Math.sin(theta) / coefficients.m)))
    ];
}

export const rawXMaximum = forwardRaw(Math.PI, 0)[0];
export const rawYMaximum = forwardRaw(0, Math.PI / 2)[1];
export const nativeAspect = rawXMaximum / rawYMaximum;

export function forwardDegrees([longitude, latitude],
    centralMeridianDegrees = 0) {
    if (!Number.isFinite(longitude) || !Number.isFinite(latitude)
        || latitude < -90 || latitude > 90) {
        throw new RangeError('Equal Earth requires finite longitude and latitude in [-90, 90]');
    }
    return forwardRaw(
        relativeLongitudeRadians(longitude, centralMeridianDegrees),
        latitude * radiansPerDegree
    );
}

export function inverseDegrees([x, y], centralMeridianDegrees = 0) {
    const [longitude, latitude] = inverseRaw(x, y);
    if (Math.abs(longitude) > Math.PI + 1e-12
        || Math.abs(latitude) > Math.PI / 2 + 1e-12) return null;
    return [
        canonicalLongitudeDegrees(longitude * degreesPerRadian
            + centralMeridianDegrees),
        latitude * degreesPerRadian
    ];
}

export function normalizedForward(coordinate, centralMeridianDegrees = 0) {
    const [x, y] = forwardDegrees(coordinate, centralMeridianDegrees);
    return [
        (x + rawXMaximum) / (2 * rawXMaximum),
        (rawYMaximum - y) / (2 * rawYMaximum)
    ];
}

export function normalizedInverse([u, v], centralMeridianDegrees = 0) {
    if (![u, v].every(Number.isFinite) || u < 0 || u > 1 || v < 0 || v > 1) {
        return null;
    }
    return inverseDegrees([
        u * 2 * rawXMaximum - rawXMaximum,
        rawYMaximum - v * 2 * rawYMaximum
    ], centralMeridianDegrees);
}

function jacobianRaw(forward, longitudeRadians, latitudeRadians) {
    const step = 2 ** -21;
    const east0 = forward(longitudeRadians - step, latitudeRadians);
    const east1 = forward(longitudeRadians + step, latitudeRadians);
    const north0 = forward(longitudeRadians, latitudeRadians - step);
    const north1 = forward(longitudeRadians, latitudeRadians + step);
    const cosine = Math.cos(latitudeRadians);
    return [
        [(east1[0] - east0[0]) / (2 * step * cosine),
            (north1[0] - north0[0]) / (2 * step)],
        [(east1[1] - east0[1]) / (2 * step * cosine),
            (north1[1] - north0[1]) / (2 * step)]
    ];
}

export function distortionAt(longitudeDegrees, latitudeDegrees,
    forward = forwardRaw) {
    if (Math.abs(latitudeDegrees) >= 89.999999) return null;
    const matrix = jacobianRaw(forward,
        longitudeDegrees * radiansPerDegree,
        latitudeDegrees * radiansPerDegree);
    const [a, b] = matrix[0];
    const [c, d] = matrix[1];
    const trace = a * a + b * b + c * c + d * d;
    const determinant = a * d - b * c;
    const discriminant = Math.sqrt(Math.max(0,
        trace * trace - 4 * determinant * determinant));
    const major = Math.sqrt(Math.max(0, (trace + discriminant) / 2));
    const minor = Math.sqrt(Math.max(0, (trace - discriminant) / 2));
    const angularDeformationDegrees = 2 * Math.asin(Math.min(1,
        Math.abs(major - minor) / (major + minor))) * degreesPerRadian;
    return {
        areaScale: determinant,
        majorScale: major,
        minorScale: minor,
        angularDeformationDegrees
    };
}

export function mercatorForwardRaw(longitudeRadians, latitudeRadians) {
    const maximumLatitude = 85.0511287798066 * radiansPerDegree;
    const latitude = Math.max(-maximumLatitude,
        Math.min(maximumLatitude, latitudeRadians));
    return [longitudeRadians, Math.asinh(Math.tan(latitude))];
}

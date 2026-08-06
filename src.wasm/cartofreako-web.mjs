import createWasmModule from './cartofreako-projections.mjs';

export const GeometryPart = Object.freeze({point: 0, line: 1, ring: 2});
export const RingRole = Object.freeze({none: 0, exterior: 1, hole: 2});

function requireCondition(condition, message) {
    if (!condition) throw new TypeError(message);
}

function appendPosition(state, position) {
    requireCondition(
        Array.isArray(position) || ArrayBuffer.isView(position),
        'GeoJSON position must be an array'
    );
    requireCondition(position.length >= 2, 'GeoJSON position needs longitude and latitude');
    const longitude = Number(position[0]);
    const latitude = Number(position[1]);
    requireCondition(
        Number.isFinite(longitude) && longitude >= -180 && longitude <= 180,
        'GeoJSON longitude must be finite and within [-180, 180]'
    );
    requireCondition(
        Number.isFinite(latitude) && latitude >= -90 && latitude <= 90,
        'GeoJSON latitude must be finite and within [-90, 90]'
    );
    state.coordinates.push(longitude, latitude);
}

function appendPart(state, positions, type, featureId, role = RingRole.none) {
    requireCondition(Array.isArray(positions), 'GeoJSON coordinate part must be an array');
    for (const position of positions) appendPosition(state, position);
    state.partOffsets.push(state.coordinates.length / 2);
    state.partTypes.push(type);
    state.featureIds.push(featureId);
    state.ringRoles.push(role);
}

function appendGeometry(state, geometry, featureId) {
    if (geometry == null) return;
    requireCondition(typeof geometry.type === 'string', 'GeoJSON geometry is missing type');
    switch (geometry.type) {
    case 'Point':
        appendPart(state, [geometry.coordinates], GeometryPart.point, featureId);
        break;
    case 'MultiPoint':
        appendPart(state, geometry.coordinates, GeometryPart.point, featureId);
        break;
    case 'LineString':
        appendPart(state, geometry.coordinates, GeometryPart.line, featureId);
        break;
    case 'MultiLineString':
        for (const line of geometry.coordinates) {
            appendPart(state, line, GeometryPart.line, featureId);
        }
        break;
    case 'Polygon':
        geometry.coordinates.forEach((ring, index) => appendPart(
            state,
            ring,
            GeometryPart.ring,
            featureId,
            index === 0 ? RingRole.exterior : RingRole.hole
        ));
        break;
    case 'MultiPolygon':
        for (const polygon of geometry.coordinates) {
            polygon.forEach((ring, index) => appendPart(
                state,
                ring,
                GeometryPart.ring,
                featureId,
                index === 0 ? RingRole.exterior : RingRole.hole
            ));
        }
        break;
    case 'GeometryCollection':
        for (const child of geometry.geometries) appendGeometry(state, child, featureId);
        break;
    case 'Sphere':
        state.sphere = true;
        break;
    default:
        throw new TypeError(`Unsupported GeoJSON geometry type: ${geometry.type}`);
    }
}

/** Flatten GeoJSON once before crossing the JS/WASM boundary. */
export function flattenGeoJSON(value) {
    requireCondition(value && typeof value === 'object', 'GeoJSON input must be an object');
    const state = {
        coordinates: [],
        partOffsets: [0],
        partTypes: [],
        featureIds: [],
        ringRoles: [],
        features: [],
        sphere: false
    };
    if (value.type === 'FeatureCollection') {
        value.features.forEach((feature, featureId) => {
            state.features.push({id: feature.id ?? featureId, properties: feature.properties ?? {}});
            appendGeometry(state, feature.geometry, featureId);
        });
    } else if (value.type === 'Feature') {
        state.features.push({id: value.id ?? 0, properties: value.properties ?? {}});
        appendGeometry(state, value.geometry, 0);
    } else {
        state.features.push({id: 0, properties: {}});
        appendGeometry(state, value, 0);
    }
    return {
        coordinates: new Float64Array(state.coordinates),
        partOffsets: new Uint32Array(state.partOffsets),
        partTypes: new Uint8Array(state.partTypes),
        featureIds: new Uint32Array(state.featureIds),
        ringRoles: new Uint8Array(state.ringRoles),
        features: state.features,
        sphere: state.sphere
    };
}

function normalizeFlatGeometry(input) {
    if (!input || !ArrayBuffer.isView(input.coordinates)) return flattenGeoJSON(input);
    return {
        coordinates: input.coordinates instanceof Float64Array
            ? input.coordinates : new Float64Array(input.coordinates),
        partOffsets: input.partOffsets instanceof Uint32Array
            ? input.partOffsets : new Uint32Array(input.partOffsets),
        partTypes: input.partTypes instanceof Uint8Array
            ? input.partTypes : new Uint8Array(input.partTypes),
        featureIds: input.featureIds == null
            ? new Uint32Array(0)
            : input.featureIds instanceof Uint32Array
                ? input.featureIds : new Uint32Array(input.featureIds),
        ringRoles: input.ringRoles == null
            ? new Uint8Array(0)
            : input.ringRoles instanceof Uint8Array
                ? input.ringRoles : new Uint8Array(input.ringRoles),
        features: input.features ?? [],
        sphere: input.sphere === true
    };
}

function descriptorFor(manifest, id) {
    const aliases = {ck: 'cahill-keyes', starx: 'star-x', voroni: 'voronoi'};
    const canonical = aliases[id] ?? id;
    const descriptor = manifest.find((entry) => entry.id === canonical);
    if (!descriptor) throw new RangeError(`Unknown Cartofreako projection: ${id}`);
    return descriptor;
}

export class CartofreakoProjection {
    #raw;
    #descriptor;
    #disposed = false;

    constructor(raw, descriptor) {
        this.#raw = raw;
        this.#descriptor = descriptor;
    }

    get id() { return this.#descriptor.id; }
    get descriptor() { return this.#descriptor; }
    get width() { this.#assertLive(); return this.#raw.width(); }
    get height() { this.#assertLive(); return this.#raw.height(); }

    #assertLive() {
        if (this.#disposed) throw new Error('Cartofreako projection has been disposed');
    }

    project(longitude, latitude) {
        this.#assertLive();
        const result = this.#raw.project(latitude, longitude);
        return {x: result.x, y: result.y, nativeCell: result.nativeCell};
    }

    projectPoints(lonLat) {
        this.#assertLive();
        const source = lonLat instanceof Float64Array ? lonLat : new Float64Array(lonLat);
        return this.#raw.projectPoints(source);
    }

    projectGeometry(input, options = {}) {
        this.#assertLive();
        const flat = normalizeFlatGeometry(input);
        if (flat.sphere && flat.partTypes.length === 0) {
            const result = this.#raw.carrierGeometry(options);
            result.features = flat.features;
            return result;
        }
        const result = this.#raw.projectGeometryFlat(
            flat.coordinates,
            flat.partOffsets,
            flat.partTypes,
            flat.featureIds,
            flat.ringRoles,
            options
        );
        result.features = flat.features;
        return result;
    }

    carrierGeometry(options = {}) {
        this.#assertLive();
        return this.#raw.carrierGeometry(options);
    }

    listSlices({includeClipGeometry = false} = {}) {
        this.#assertLive();
        return this.#raw.listSlices(includeClipGeometry);
    }

    slice(id, {includeClipGeometry = true} = {}) {
        this.#assertLive();
        return this.#raw.slice(id, includeClipGeometry);
    }

    dispose() {
        if (!this.#disposed) {
            this.#raw.delete();
            this.#disposed = true;
        }
    }

    [Symbol.dispose]() { this.dispose(); }
}

export class CartofreakoRuntime {
    #module;
    #manifest;

    constructor(module) {
        this.#module = module;
        this.#manifest = Object.freeze(module.projectionManifest());
        if (module.runtimeAbiVersion() !== 1) {
            throw new Error(`Unsupported Cartofreako WASM ABI ${module.runtimeAbiVersion()}`);
        }
    }

    get abiVersion() { return this.#module.runtimeAbiVersion(); }
    get implementationName() { return this.#module.implementationName(); }
    get manifest() { return this.#manifest; }
    get licenses() { return this.#module.licenseManifest(); }

    createProjection({id = 'cahill-keyes', width = 1200, height} = {}) {
        const descriptor = descriptorFor(this.#manifest, id);
        requireCondition(Number.isFinite(width) && width > 0, 'Projection width must be positive');
        const resolvedHeight = height ?? width / descriptor.nativeFrameRatio;
        requireCondition(
            Number.isFinite(resolvedHeight) && resolvedHeight > 0,
            'Projection height must be positive'
        );
        const raw = new this.#module.Projection(descriptor.id, width, resolvedHeight);
        return new CartofreakoProjection(raw, descriptor);
    }
}

/** Instantiate the all-projection ES-module build. */
export async function createCartofreako(moduleOptions = {}) {
    return new CartofreakoRuntime(await createWasmModule(moduleOptions));
}

export default createCartofreako;

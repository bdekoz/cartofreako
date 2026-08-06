import createCartofreako from './cartofreako-web.mjs';

const runtimePromise = createCartofreako();
const projections = new Map();

function projectionKey(config) {
    return `${config.id ?? 'cahill-keyes'}:${config.width ?? 1200}:${config.height ?? 'auto'}`;
}

async function projection(config = {}) {
    const key = projectionKey(config);
    if (!projections.has(key)) {
        const runtime = await runtimePromise;
        projections.set(key, runtime.createProjection(config));
    }
    return projections.get(key);
}

function transferList(value) {
    const result = [];
    for (const key of [
        'coordinates', 'partOffsets', 'partTypes', 'featureIds',
        'nativeCells', 'componentIds', 'ringRoles', 'closed'
    ]) {
        if (ArrayBuffer.isView(value?.[key])) result.push(value[key].buffer);
    }
    return result;
}

async function dispatch(message) {
    switch (message.type) {
    case 'manifest': {
        const runtime = await runtimePromise;
        return {
            abiVersion: runtime.abiVersion,
            implementationName: runtime.implementationName,
            manifest: runtime.manifest,
            licenses: runtime.licenses
        };
    }
    case 'projectGeometry':
        return (await projection(message.projection)).projectGeometry(
            message.geometry,
            message.options
        );
    case 'carrierGeometry':
        return (await projection(message.projection)).carrierGeometry(message.options);
    case 'listSlices':
        return (await projection(message.projection)).listSlices(message.options);
    case 'slice':
        return (await projection(message.projection)).slice(message.sliceId, message.options);
    case 'dispose': {
        const key = projectionKey(message.projection ?? {});
        projections.get(key)?.dispose();
        projections.delete(key);
        return {disposed: key};
    }
    default:
        throw new TypeError(`Unknown Cartofreako worker message: ${message.type}`);
    }
}

self.addEventListener('message', async ({data}) => {
    const {requestId} = data;
    try {
        const value = await dispatch(data);
        self.postMessage({requestId, ok: true, value}, transferList(value));
    } catch (error) {
        self.postMessage({
            requestId,
            ok: false,
            error: {
                name: error?.name ?? 'Error',
                message: error?.message ?? String(error),
                stack: error?.stack
            }
        });
    }
});

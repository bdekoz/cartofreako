import createCartofreako from './cartofreako-web.mjs';

const runtimePromise = createCartofreako();
const projections = new Map();
const cancelled = new Set();

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
        'nativeCells', 'componentIds', 'ringRoles', 'closed', 'statuses',
        'candidateOffsets', 'forwardResiduals', 'boundaries', 'truncated'
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
            apiVersion: runtime.apiVersion,
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
    case 'forward':
        return (await projection(message.projection)).forward(message.coordinate);
    case 'forwardMany':
        return (await projection(message.projection)).forwardMany(message.coordinates);
    case 'inverse':
        return (await projection(message.projection)).inverse(
            message.coordinate,
            message.options
        );
    case 'inverseMany':
        return (await projection(message.projection)).inverseMany(
            message.coordinates,
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
    if (data.type === 'cancel') {
        cancelled.add(requestId);
        setTimeout(() => cancelled.delete(requestId), 60000);
        return;
    }
    try {
        // Yield once so an AbortSignal cancellation queued immediately after a
        // request can be observed before entering a synchronous WASM call.
        await new Promise(resolve => setTimeout(resolve, 0));
        if (cancelled.delete(requestId)) return;
        const value = await dispatch(data);
        if (cancelled.delete(requestId)) return;
        self.postMessage({requestId, ok: true, value}, transferList(value));
    } catch (error) {
        if (cancelled.delete(requestId)) return;
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

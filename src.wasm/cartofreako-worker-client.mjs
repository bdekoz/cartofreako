/** Promise-based browser client for the Cartofreako projection worker. */
function abortError(signal) {
    const message = signal?.reason instanceof Error
        ? signal.reason.message : 'Cartofreako worker request aborted';
    if (typeof DOMException === 'function') return new DOMException(message, 'AbortError');
    const error = new Error(message);
    error.name = 'AbortError';
    return error;
}

export class CartofreakoWorkerClient {
    #worker;
    #nextRequest = 1;
    #pending = new Map();

    constructor({
        url = new URL('./cartofreako-projections-worker.mjs', import.meta.url),
        worker = new Worker(url, {type: 'module', name: 'cartofreako-projections'})
    } = {}) {
        this.#worker = worker;
        worker.addEventListener('message', ({data}) => {
            const request = this.#pending.get(data.requestId);
            if (!request) return;
            this.#pending.delete(data.requestId);
            request.cleanup();
            if (data.ok) request.resolve(data.value);
            else {
                const error = new Error(data.error.message);
                error.name = data.error.name;
                if (data.error.stack) error.stack = data.error.stack;
                request.reject(error);
            }
        });
        worker.addEventListener('error', (event) => {
            for (const request of this.#pending.values()) {
                request.cleanup();
                request.reject(event.error ?? event);
            }
            this.#pending.clear();
        });
    }

    request(type, payload = {}, {signal} = {}) {
        const requestId = this.#nextRequest++;
        return new Promise((resolve, reject) => {
            if (signal?.aborted) {
                reject(abortError(signal));
                return;
            }
            const abort = () => {
                const request = this.#pending.get(requestId);
                if (!request) return;
                this.#pending.delete(requestId);
                request.cleanup();
                this.#worker.postMessage({requestId, type: 'cancel'});
                reject(abortError(signal));
            };
            const cleanup = () => signal?.removeEventListener('abort', abort);
            signal?.addEventListener('abort', abort, {once: true});
            this.#pending.set(requestId, {resolve, reject, cleanup});
            this.#worker.postMessage({requestId, type, ...payload});
        });
    }

    manifest(requestOptions = {}) { return this.request('manifest', {}, requestOptions); }

    forward(projection, coordinate, requestOptions = {}) {
        return this.request('forward', {projection, coordinate}, requestOptions);
    }

    forwardMany(projection, coordinates, requestOptions = {}) {
        return this.request('forwardMany', {projection, coordinates}, requestOptions);
    }

    inverse(projection, coordinate, options = {}, requestOptions = {}) {
        return this.request('inverse', {projection, coordinate, options}, requestOptions);
    }

    inverseMany(projection, coordinates, options = {}, requestOptions = {}) {
        return this.request('inverseMany', {projection, coordinates, options}, requestOptions);
    }

    projectGeometry(projection, geometry, options = {}, requestOptions = {}) {
        return this.request('projectGeometry', {projection, geometry, options}, requestOptions);
    }

    carrierGeometry(projection, options = {}, requestOptions = {}) {
        return this.request('carrierGeometry', {projection, options}, requestOptions);
    }

    listSlices(projection, options = {}, requestOptions = {}) {
        return this.request('listSlices', {projection, options}, requestOptions);
    }

    slice(projection, sliceId, options = {}, requestOptions = {}) {
        return this.request('slice', {projection, sliceId, options}, requestOptions);
    }

    disposeProjection(projection, requestOptions = {}) {
        return this.request('dispose', {projection}, requestOptions);
    }

    terminate() {
        this.#worker.terminate();
        for (const request of this.#pending.values()) {
            request.cleanup();
            request.reject(new Error('Cartofreako worker terminated'));
        }
        this.#pending.clear();
    }
}

export default CartofreakoWorkerClient;

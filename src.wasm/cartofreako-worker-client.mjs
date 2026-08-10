/** Promise-based browser client for the Cartofreako projection worker. */
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
            if (data.ok) request.resolve(data.value);
            else {
                const error = new Error(data.error.message);
                error.name = data.error.name;
                if (data.error.stack) error.stack = data.error.stack;
                request.reject(error);
            }
        });
        worker.addEventListener('error', (event) => {
            for (const request of this.#pending.values()) request.reject(event.error ?? event);
            this.#pending.clear();
        });
    }

    request(type, payload = {}) {
        const requestId = this.#nextRequest++;
        return new Promise((resolve, reject) => {
            this.#pending.set(requestId, {resolve, reject});
            this.#worker.postMessage({requestId, type, ...payload});
        });
    }

    manifest() { return this.request('manifest'); }

    forward(projection, coordinate) {
        return this.request('forward', {projection, coordinate});
    }

    forwardMany(projection, coordinates) {
        return this.request('forwardMany', {projection, coordinates});
    }

    inverse(projection, coordinate, options = {}) {
        return this.request('inverse', {projection, coordinate, options});
    }

    inverseMany(projection, coordinates, options = {}) {
        return this.request('inverseMany', {projection, coordinates, options});
    }

    projectGeometry(projection, geometry, options = {}) {
        return this.request('projectGeometry', {projection, geometry, options});
    }

    carrierGeometry(projection, options = {}) {
        return this.request('carrierGeometry', {projection, options});
    }

    listSlices(projection, options = {}) {
        return this.request('listSlices', {projection, options});
    }

    slice(projection, sliceId, options = {}) {
        return this.request('slice', {projection, sliceId, options});
    }

    disposeProjection(projection) {
        return this.request('dispose', {projection});
    }

    terminate() {
        this.#worker.terminate();
        for (const request of this.#pending.values()) {
            request.reject(new Error('Cartofreako worker terminated'));
        }
        this.#pending.clear();
    }
}

export default CartofreakoWorkerClient;

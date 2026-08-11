import type {
    Coordinate,
    ForwardBatch,
    ForwardResult,
    InverseBatch,
    InverseOptions,
    InverseResult,
    ProjectionOptions
} from './cartofreako-web.mjs';

export interface WorkerRequestOptions {signal?: AbortSignal}

export class CartofreakoWorkerClient {
    constructor(options?: {url?: URL; worker?: Worker});
    request(type: string, payload?: Record<string, unknown>,
        options?: WorkerRequestOptions): Promise<unknown>;
    manifest(options?: WorkerRequestOptions): Promise<unknown>;
    forward(projection: ProjectionOptions, coordinate: Coordinate,
        options?: WorkerRequestOptions): Promise<ForwardResult>;
    forwardMany(projection: ProjectionOptions, coordinates: ArrayLike<number>,
        options?: WorkerRequestOptions): Promise<ForwardBatch>;
    inverse(projection: ProjectionOptions, coordinate: Coordinate,
        inverseOptions?: InverseOptions,
        requestOptions?: WorkerRequestOptions): Promise<InverseResult>;
    inverseMany(projection: ProjectionOptions, coordinates: ArrayLike<number>,
        inverseOptions?: InverseOptions,
        requestOptions?: WorkerRequestOptions): Promise<InverseBatch>;
    projectGeometry(projection: ProjectionOptions, geometry: unknown,
        options?: Record<string, unknown>,
        requestOptions?: WorkerRequestOptions): Promise<unknown>;
    carrierGeometry(projection: ProjectionOptions,
        options?: Record<string, unknown>,
        requestOptions?: WorkerRequestOptions): Promise<unknown>;
    listSlices(projection: ProjectionOptions,
        options?: Record<string, unknown>,
        requestOptions?: WorkerRequestOptions): Promise<unknown[]>;
    slice(projection: ProjectionOptions, sliceId: string,
        options?: Record<string, unknown>,
        requestOptions?: WorkerRequestOptions): Promise<unknown>;
    disposeProjection(projection: ProjectionOptions,
        options?: WorkerRequestOptions): Promise<unknown>;
    terminate(): void;
}

export default CartofreakoWorkerClient;

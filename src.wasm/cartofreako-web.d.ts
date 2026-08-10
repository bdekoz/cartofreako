export const GeometryPart: Readonly<{point: 0; line: 1; ring: 2}>;
export const RingRole: Readonly<{none: 0; exterior: 1; hole: 2}>;
export const InverseStatus: Readonly<{
    unique: 0;
    ambiguous: 1;
    outside: 2;
    cut: 3;
    unsupported: 4;
}>;

export type Coordinate = readonly [number, number] | Float64Array;
export type InverseStatusName =
    | 'unique' | 'ambiguous' | 'outside' | 'cut' | 'unsupported';
export type InverseMode = 'none' | 'face-qualified' | 'candidates';

export interface ProjectionDescriptor {
    apiVersion: 2;
    geometryAbiVersion: 1;
    id: string;
    family: string;
    title: string;
    nativeFrameRatio: number;
    defaultFrame: {width: number; height: number};
    nativeCellCount: number;
    topology: 'folded' | 'periodic' | 'polyhedral';
    geographicCoordinateOrder: 'longitude-latitude';
    geographicUnits: 'degrees';
    longitudeDomain: '[-180,180]';
    latitudeDomain: '[-90,90]';
    projectedUnits: 'pixels';
    axisOrigin: 'top-left';
    xAxisDirection: 'right';
    yAxisDirection: 'down';
    framePolicy: 'exact-native-aspect';
    cutTopology: 'folded' | 'periodic' | 'polyhedral';
    inverseMode: InverseMode;
    capabilities: {
        points: true;
        lines: true;
        polygons: true;
        sphere: true;
        slices: true;
        planarTiles: true;
        forward: true;
        inverse: boolean;
        inverseCandidates: boolean;
        headless: true;
    };
    license: {spdx: string; notice: string};
}

export interface ForwardResult {
    x: number;
    y: number;
    nativeCell: number;
    component: number;
}

export interface ForwardBatch {
    coordinates: Float64Array;
    nativeCells: Uint32Array;
    componentIds: Uint32Array;
}

export interface InverseOptions {
    tolerancePx?: number;
    nativeCell?: number | null;
    maximumCandidates?: number;
}

export interface InverseCandidate {
    longitude: number;
    latitude: number;
    nativeCell: number;
    component: number;
    forwardResidual: number;
    boundary: boolean;
}

export interface InverseResult {
    status: InverseStatusName;
    candidates: InverseCandidate[];
    tolerancePx: number;
    truncated: boolean;
}

export interface InverseBatch {
    statuses: Uint8Array;
    candidateOffsets: Uint32Array;
    coordinates: Float64Array;
    nativeCells: Uint32Array;
    componentIds: Uint32Array;
    forwardResiduals: Float64Array;
    boundaries: Uint8Array;
    truncated: Uint8Array;
    tolerancePx: number;
}

export interface ProjectionOptions {
    id?: string;
    width?: number;
    height?: number;
}

export class CartofreakoProjection {
    readonly id: string;
    readonly descriptor: ProjectionDescriptor;
    readonly width: number;
    readonly height: number;
    metadata(): ProjectionDescriptor;
    project(longitude: number, latitude: number): ForwardResult;
    forward(longitudeLatitude: Coordinate): ForwardResult;
    projectPoints(longitudeLatitude: ArrayLike<number>): ForwardBatch;
    forwardMany(longitudeLatitude: ArrayLike<number>): ForwardBatch;
    inverse(xy: Coordinate, options?: InverseOptions): InverseResult;
    inverseMany(xy: ArrayLike<number>, options?: InverseOptions): InverseBatch;
    projectGeometry(input: unknown, options?: unknown): unknown;
    projectGeoJSON(input: unknown, options?: unknown): unknown;
    carrierGeometry(options?: unknown): unknown;
    listSlices(options?: {includeClipGeometry?: boolean}): unknown[];
    slice(id: string, options?: {includeClipGeometry?: boolean}): unknown;
    dispose(): void;
}

export class CartofreakoRuntime {
    readonly abiVersion: 1;
    readonly apiVersion: 2;
    readonly implementationName: string;
    readonly manifest: readonly ProjectionDescriptor[];
    readonly licenses: Readonly<Record<string, string>>;
    listProjections(): readonly ProjectionDescriptor[];
    projection(options?: ProjectionOptions & {
        name?: string;
        frame?: readonly [number, number];
    }): CartofreakoProjection;
    createProjection(options?: ProjectionOptions): CartofreakoProjection;
}

export function flattenGeoJSON(value: unknown): unknown;
export function createCartofreako(moduleOptions?: Record<string, unknown>):
    Promise<CartofreakoRuntime>;
export default createCartofreako;

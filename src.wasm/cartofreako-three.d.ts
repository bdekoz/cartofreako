import type {CartofreakoProjection, InverseOptions, InverseResult} from './cartofreako-web.mjs';
import type {ScreenContract} from './cartofreako-screen.mjs';

export interface ThreeIntersectionLike {uv: {x: number; y: number}}
export interface ScreenArtifactLike {id?: string; screen: ScreenContract}

export function createThreeFlatMap(
    THREE: Record<string, unknown>,
    texture: unknown,
    artifact: ScreenArtifactLike | ScreenContract,
    options?: {worldWidth?: number; material?: Record<string, unknown>}
): unknown;
export function threeIntersectionToScreen(
    intersection: ThreeIntersectionLike,
    artifact: ScreenArtifactLike | ScreenContract
): readonly [number, number];
export function threeIntersectionToGeographic(
    projection: CartofreakoProjection,
    intersection: ThreeIntersectionLike,
    artifact: ScreenArtifactLike | ScreenContract,
    inverseOptions?: InverseOptions
): InverseResult;

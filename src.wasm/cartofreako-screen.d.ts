import type {CartofreakoProjection, InverseOptions, InverseResult} from './cartofreako-web.mjs';

export interface Dimensions {width: number; height: number}
export interface ContentRectangle extends Dimensions {x: number; y: number}
export type Matrix3 = readonly [
    number, number, number,
    number, number, number,
    number, number, number
];
export interface ScreenContract {
    fit: 'contain';
    background: string;
    canvas: Dimensions;
    contentRectangle: ContentRectangle;
    projectedToScreen: Matrix3;
    screenToProjected: Matrix3;
}
export interface ContainTransform extends ScreenContract {sourceFrame: Dimensions}

export function containTransform(
    sourceFrame: Dimensions,
    canvas?: Dimensions,
    options?: {background?: string; contentSize?: Dimensions | null}
): ContainTransform;
export function projectedToScreen(
    projected: readonly [number, number] | Float64Array,
    contract: ScreenContract
): readonly [number, number];
export function screenToProjected(
    screen: readonly [number, number] | Float64Array,
    contract: ScreenContract,
    options?: {allowPadding?: boolean}
): readonly [number, number];
export function screenToGeographic(
    projection: CartofreakoProjection,
    screen: readonly [number, number] | Float64Array,
    artifact: ScreenContract | {screen: ScreenContract},
    inverseOptions?: InverseOptions
): InverseResult;
export function flatTexturePlane(contract: ScreenContract): Readonly<{
    primitive: 'triangle-strip';
    positions: readonly number[];
    textureCoordinates: readonly number[];
    warning: string;
}>;

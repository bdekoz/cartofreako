import {screenToGeographic} from './cartofreako-screen.mjs';

function requireCondition(condition, message) {
    if (!condition) throw new TypeError(message);
}

/** Build a Three.js Mesh for an interrupted 1080p catalog texture on a flat plane. */
export function createThreeFlatMap(THREE, texture, artifact, {
    worldWidth = 16,
    material = {}
} = {}) {
    requireCondition(THREE?.PlaneGeometry && THREE?.MeshBasicMaterial && THREE?.Mesh,
        'THREE must provide PlaneGeometry, MeshBasicMaterial, and Mesh');
    requireCondition(texture, 'texture is required');
    const canvas = artifact?.screen?.canvas ?? artifact?.canvas;
    requireCondition(Number.isFinite(canvas?.width) && Number.isFinite(canvas?.height),
        'artifact screen canvas is required');
    requireCondition(Number.isFinite(worldWidth) && worldWidth > 0,
        'worldWidth must be finite and positive');
    const geometry = new THREE.PlaneGeometry(worldWidth,
        worldWidth * canvas.height / canvas.width);
    const surface = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide,
        transparent: false,
        ...material
    });
    const mesh = new THREE.Mesh(geometry, surface);
    mesh.name = `cartofreako:${artifact.id ?? 'flat-map'}`;
    mesh.userData.cartofreako = Object.freeze({
        artifactId: artifact.id ?? null,
        canvas: Object.freeze({...canvas}),
        warning: 'Interrupted flat map; do not wrap as an equirectangular globe texture.'
    });
    return mesh;
}

/** Convert a Three.js raycast UV into top-left-origin screen pixels. */
export function threeIntersectionToScreen(intersection, artifact) {
    const uv = intersection?.uv;
    const canvas = artifact?.screen?.canvas ?? artifact?.canvas;
    requireCondition(Number.isFinite(uv?.x) && Number.isFinite(uv?.y),
        'Three.js intersection must contain finite UV coordinates');
    requireCondition(Number.isFinite(canvas?.width) && Number.isFinite(canvas?.height),
        'artifact screen canvas is required');
    return Object.freeze([uv.x * canvas.width, (1 - uv.y) * canvas.height]);
}

/** Preserve Cartofreako inverse candidates for a Three.js flat-plane hit. */
export function threeIntersectionToGeographic(projection, intersection, artifact,
    inverseOptions = {}) {
    return screenToGeographic(projection,
        threeIntersectionToScreen(intersection, artifact), artifact, inverseOptions);
}

import * as THREE from '../third_party/three-0.185.1/build/three.module.min.js';

import createCartofreako from '../cartofreako-web.mjs';
import {
    createThreeFlatMap,
    threeIntersectionToGeographic,
    threeIntersectionToScreen
} from '../cartofreako-three.mjs';

const artifactId = new URL(location.href).searchParams.get('artifact')
    ?? 'water.myriahedral.whole-map';
const catalog = await fetch('../../assets.generated/catalog/artifacts-v1.json')
    .then(response => {
        if (!response.ok) throw new Error(`catalog request failed: ${response.status}`);
        return response.json();
    });
const artifact = catalog.artifacts.find(({id}) => id === artifactId);
if (!artifact) throw new Error(`catalog artifact not found: ${artifactId}`);
const runtime = await createCartofreako();
const projection = runtime.createProjection({
    id: artifact.projection.id,
    width: artifact.projection.nativeFrame.width
});

const viewport = document.querySelector('#viewport');
const metadata = document.querySelector('#metadata');
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setSize(960, 540, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewport.append(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(artifact.screen.background);
const camera = new THREE.OrthographicCamera(-8, 8, 4.5, -4.5, 0.1, 20);
camera.position.z = 10;
const texture = await new THREE.TextureLoader().loadAsync(`../../${artifact.screen.webp.path}`);
texture.colorSpace = THREE.SRGBColorSpace;
const mesh = createThreeFlatMap(THREE, texture, artifact);
scene.add(mesh);
renderer.render(scene, camera);

const raycaster = new THREE.Raycaster();
renderer.domElement.addEventListener('pointerdown', event => {
    const bounds = renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2(
        (event.clientX - bounds.left) / bounds.width * 2 - 1,
        -((event.clientY - bounds.top) / bounds.height * 2 - 1)
    );
    raycaster.setFromCamera(ndc, camera);
    const hit = raycaster.intersectObject(mesh)[0];
    if (!hit) return;
    try {
        const screen = threeIntersectionToScreen(hit, artifact);
        const inverse = threeIntersectionToGeographic(projection, hit, artifact);
        metadata.textContent = JSON.stringify({artifactId, screen, inverse}, null, 2);
    } catch (error) {
        metadata.textContent = JSON.stringify({artifactId, status: 'padding',
            message: error.message}, null, 2);
    }
});
metadata.textContent = JSON.stringify({
    artifactId,
    threeRevision: THREE.REVISION,
    screen: artifact.screen,
    warning: mesh.userData.cartofreako.warning
}, null, 2);

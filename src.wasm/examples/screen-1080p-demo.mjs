import createCartofreako from '../cartofreako-web.mjs';
import {drawBaseMap} from '../cartofreako-canvas.mjs';
import {
    containTransform,
    flatTexturePlane,
    screenToGeographic
} from '../cartofreako-screen.mjs';

const runtime = await createCartofreako();
const land = await fetch('../cartofreako-cahill-keyes-land-110m.geojson').then((response) => {
    if (!response.ok) throw new Error(`Natural Earth request failed: ${response.status}`);
    return response.json();
});
const select = document.querySelector('#projection');
const canvas = document.querySelector('#map');
const metadata = document.querySelector('#metadata');
let projection;
let transform;

function render() {
    projection?.dispose();
    const descriptor = runtime.manifest.find(({id}) => id === select.value);
    const frame = descriptor.defaultFrame;
    projection = runtime.createProjection({id: descriptor.id, width: frame.width});
    transform = containTransform(frame);
    const context = canvas.getContext('2d');
    context.save();
    context.fillStyle = transform.background;
    context.fillRect(0, 0, canvas.width, canvas.height);
    const matrix = transform.projectedToScreen;
    context.setTransform(matrix[0], matrix[3], matrix[1], matrix[4], matrix[2], matrix[5]);
    drawBaseMap(context, projection.carrierGeometry(), projection.projectGeometry(land), {
        clear: false
    });
    context.restore();
    metadata.textContent = JSON.stringify({
        projection: descriptor.id,
        runtimeApi: runtime.apiVersion,
        geometryAbi: runtime.abiVersion,
        transform,
        texturePlane: flatTexturePlane(transform)
    }, null, 2);
}

canvas.addEventListener('pointerdown', (event) => {
    const bounds = canvas.getBoundingClientRect();
    const screen = [
        (event.clientX - bounds.left) * canvas.width / bounds.width,
        (event.clientY - bounds.top) * canvas.height / bounds.height
    ];
    try {
        const inverse = screenToGeographic(projection, screen, transform);
        metadata.textContent = JSON.stringify({screen, inverse, transform}, null, 2);
    } catch (error) {
        metadata.textContent = JSON.stringify({screen, status: 'padding', message: error.message}, null, 2);
    }
});
select.addEventListener('change', render);
render();

import createCartofreako from '../cartofreako-web.mjs';
import {drawBaseMap} from '../cartofreako-canvas.mjs';

const runtime = await createCartofreako();
const land = await fetch('../cartofreako-cahill-keyes-land-110m.geojson').then((response) => {
    if (!response.ok) throw new Error(`Natural Earth request failed: ${response.status}`);
    return response.json();
});
const projectionSelect = document.querySelector('#projection');
const sliceSelect = document.querySelector('#slice');
const canvas = document.querySelector('#map');
const metadata = document.querySelector('#metadata');
let projection;

function setProjection() {
    projection?.dispose();
    projection = runtime.createProjection({id: projectionSelect.value, width: 960});
    const slices = projection.listSlices();
    sliceSelect.replaceChildren(...slices.map((slice) => {
        const option = document.createElement('option');
        option.value = slice.id;
        option.textContent = `${slice.id} — ${slice.kind}`;
        return option;
    }));
    render();
}

function render() {
    const slice = sliceSelect.value;
    const options = {slice};
    const carrier = projection.carrierGeometry(options);
    const features = projection.projectGeometry(land, options);
    canvas.width = Math.max(1, Math.ceil(features.frame.width));
    canvas.height = Math.max(1, Math.ceil(features.frame.height));
    drawBaseMap(canvas.getContext('2d'), carrier, features);
    const descriptor = projection.slice(slice, {includeClipGeometry: false});
    metadata.textContent = JSON.stringify({
        projection: projection.id,
        slice: descriptor.id,
        kind: descriptor.kind,
        sourceView: descriptor.sourceView,
        outputFrame: features.frame,
        selectedCells: descriptor.selectedCells.length,
        diagnostics: features.diagnostics
    }, null, 2);
}

projectionSelect.addEventListener('change', setProjection);
sliceSelect.addEventListener('change', render);
setProjection();

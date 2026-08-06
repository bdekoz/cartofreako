import fs from 'node:fs/promises';

import createCartofreako from '../cartofreako-web.mjs';
import {renderBaseMapSvg} from '../cartofreako-svg.mjs';

const sliceId = process.argv[2] ?? 'ck-octant-7';
const projectionId = sliceId.startsWith('myria-') ? 'myriahedral' : 'cahill-keyes';
const runtime = await createCartofreako();
const projection = runtime.createProjection({id: projectionId, width: 960});
const slice = projection.slice(sliceId);
const land = JSON.parse(await fs.readFile(
    new URL('../cartofreako-cahill-keyes-land-110m.geojson', import.meta.url),
    'utf8'
));

const options = {slice: sliceId};
const carrier = projection.carrierGeometry(options);
const features = projection.projectGeometry(land, options);
const svg = renderBaseMapSvg(carrier, features, {
    title: `${projectionId} / ${sliceId}`
});

console.log(JSON.stringify({
    projection: projection.id,
    slice: {
        id: slice.id,
        kind: slice.kind,
        sourceView: slice.sourceView,
        selectedCells: slice.selectedCells.length
    },
    outputFrame: features.frame,
    outputParts: features.partTypes.length,
    svgBytes: new TextEncoder().encode(svg).length,
    svgStart: svg.slice(0, 120)
}, null, 2));

projection.dispose();

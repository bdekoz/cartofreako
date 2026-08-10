import fs from 'node:fs/promises';

import createCartofreako, {
    GeometryPart,
    RingRole,
    flattenGeoJSON
} from './cartofreako-web.mjs';
import {drawCommandBuffer} from './cartofreako-canvas.mjs';
import {cartofreakoD3Projection} from './cartofreako-d3.mjs';
import {renderBaseMapSvg, renderSvg} from './cartofreako-svg.mjs';

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function checkBuffer(buffer, projection) {
    requireCondition(buffer.abiVersion === 1, 'geometry buffer has the wrong ABI');
    requireCondition(buffer.coordinates instanceof Float64Array, 'coordinates are not Float64Array');
    requireCondition(buffer.partOffsets instanceof Uint32Array, 'offsets are not Uint32Array');
    requireCondition(buffer.partTypes instanceof Uint8Array, 'types are not Uint8Array');
    requireCondition(
        buffer.partOffsets.length === buffer.partTypes.length + 1,
        'geometry buffer offsets do not delimit every part'
    );
    requireCondition(
        buffer.partOffsets.at(-1) * 2 === buffer.coordinates.length,
        'geometry buffer final offset is wrong'
    );
    requireCondition(
        [...buffer.coordinates].every(Number.isFinite),
        'geometry buffer contains non-finite coordinates'
    );
    for (let index = 0; index < buffer.coordinates.length; index += 2) {
        requireCondition(
            buffer.coordinates[index] >= -1e-6
                && buffer.coordinates[index] <= buffer.frame.width + 1e-6
                && buffer.coordinates[index + 1] >= -1e-6
                && buffer.coordinates[index + 1] <= buffer.frame.height + 1e-6,
            `${projection.id} output leaves its slice frame`
        );
    }
    requireCondition(
        buffer.diagnostics.outputParts === buffer.partTypes.length,
        'diagnostic part count does not match output'
    );
}

function maximumSegment(buffer) {
    let maximum = 0;
    for (let part = 0; part < buffer.partTypes.length; ++part) {
        if (buffer.partTypes[part] === GeometryPart.point) continue;
        const begin = buffer.partOffsets[part];
        const end = buffer.partOffsets[part + 1];
        for (let point = begin + 1; point < end; ++point) {
            maximum = Math.max(maximum, Math.hypot(
                buffer.coordinates[point * 2] - buffer.coordinates[(point - 1) * 2],
                buffer.coordinates[point * 2 + 1] - buffer.coordinates[(point - 1) * 2 + 1]
            ));
        }
    }
    return maximum;
}

const fixture = {
    type: 'FeatureCollection',
    features: [
        {
            type: 'Feature',
            id: 'polygon-with-hole',
            properties: {kind: 'polygon'},
            geometry: {
                type: 'Polygon',
                coordinates: [
                    [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                    [[-5, -5], [-5, 5], [5, 5], [5, -5], [-5, -5]]
                ]
            }
        },
        {
            type: 'Feature',
            properties: {kind: 'multi'},
            geometry: {
                type: 'MultiPolygon',
                coordinates: [
                    [[[75, 25], [85, 25], [85, 35], [75, 35], [75, 25]]],
                    [[[-80, 30], [-70, 30], [-70, 40], [-80, 40], [-80, 30]]]
                ]
            }
        },
        {
            type: 'Feature',
            properties: {kind: 'line'},
            geometry: {type: 'LineString', coordinates: [[150, 35], [-160, 45], [170, 55]]}
        },
        {
            type: 'Feature',
            properties: {kind: 'points'},
            geometry: {type: 'MultiPoint', coordinates: [[-122.4194, 37.7749], [139.6917, 35.6895]]}
        }
    ]
};

const flat = flattenGeoJSON(fixture);
requireCondition(flat.partTypes.length === 6, 'GeoJSON flattening lost parts');
requireCondition(flat.ringRoles[0] === RingRole.exterior, 'exterior role missing');
requireCondition(flat.ringRoles[1] === RingRole.hole, 'hole role missing');

const runtime = await createCartofreako();
requireCondition(runtime.abiVersion === 1, 'incorrect runtime ABI');
requireCondition(runtime.apiVersion === 2, 'incorrect runtime API');
requireCondition(Object.isFrozen(runtime.manifest), 'projection manifest is mutable');
requireCondition(
    runtime.manifest.every((entry) => Object.isFrozen(entry)
        && entry.geographicCoordinateOrder === 'longitude-latitude'
        && entry.projectedUnits === 'pixels'
        && entry.axisOrigin === 'top-left'
        && entry.framePolicy === 'exact-native-aspect'),
    'projection metadata omits coordinate or frame policy'
);
requireCondition(
    runtime.implementationName.includes('all-projection/WebAssembly'),
    'incorrect runtime implementation identity'
);
const families = new Set(runtime.manifest.map(({family}) => family));
requireCondition(families.size === 6, 'manifest does not contain all six projection families');
requireCondition(runtime.manifest.length === 11, 'manifest lost checked Myriahedral layouts');
requireCondition(
    runtime.licenses.cahillKeyes.includes('Gene Keyes'),
    'runtime omits Cahill-Keyes attribution metadata'
);
const documentedApi = runtime.projection({
    name: 'myriahedral-pacific',
    frame: [1920, 1080]
});
requireCondition(documentedApi.metadata().apiVersion === 2, 'metadata API version is wrong');
const documentedForward = documentedApi.forward([171.2, 7.1]);
const documentedReverse = documentedApi.inverse(
    [documentedForward.x, documentedForward.y],
    {nativeCell: documentedForward.nativeCell}
);
requireCondition(documentedReverse.candidates.length === 1, 'documented API reverse failed');
documentedApi.dispose();

const summaries = [];
const reversible = new Set(['cahill-keyes', 'myriahedral', 'voronoi']);
for (const id of [
    'cahill-keyes', 'authagraph', 'dymaxion', 'myriahedral', 'star-x', 'voronoi'
]) {
    const projection = runtime.createProjection({id, width: 440});
    const point = projection.project(-122.4194, 37.7749);
    requireCondition(
        Number.isFinite(point.x) && Number.isFinite(point.y),
        `${id} point projection is not finite`
    );
    requireCondition(
        point.nativeCell >= 0 && point.nativeCell < projection.descriptor.nativeCellCount,
        `${id} point has an invalid native cell`
    );
    const forward = projection.forward([-122.4194, 37.7749]);
    requireCondition(
        Math.hypot(forward.x - point.x, forward.y - point.y) < 1e-12,
        `${id} forward alias disagrees with project`
    );
    requireCondition(
        projection.descriptor.inverseMode === (reversible.has(id) ? 'face-qualified' : 'none'),
        `${id} inverse capability is wrong`
    );
    const reversed = projection.inverse([point.x, point.y]);
    if (reversible.has(id)) {
        requireCondition(
            ['unique', 'ambiguous', 'cut'].includes(reversed.status),
            `${id} reverse status is wrong`
        );
        const candidate = reversed.candidates.find(
            ({nativeCell}) => nativeCell === point.nativeCell
        );
        requireCondition(candidate, `${id} reverse omitted the forward face`);
        requireCondition(
            Math.abs(candidate.latitude - 37.7749) < 2e-8
                && Math.abs(candidate.longitude - -122.4194) < 2e-8,
            `${id} reverse coordinate is inaccurate`
        );
        const qualified = projection.inverse([point.x, point.y], {
            nativeCell: point.nativeCell
        });
        requireCondition(qualified.candidates.length === 1, `${id} qualified reverse is not unique`);
        const reverseBatch = projection.inverseMany(new Float64Array([
            point.x, point.y, forward.x, forward.y
        ]));
        requireCondition(reverseBatch.statuses.length === 2, `${id} reverse batch lost inputs`);
        requireCondition(reverseBatch.candidateOffsets.length === 3, `${id} reverse offsets are wrong`);
    } else {
        requireCondition(reversed.status === 'unsupported', `${id} reverse should be unsupported`);
        requireCondition(reversed.candidates.length === 0, `${id} unsupported reverse returned data`);
    }
    const batched = projection.projectPoints(new Float64Array([
        -122.4194, 37.7749, 139.6917, 35.6895
    ]));
    requireCondition(batched.coordinates.length === 4, `${id} batched point result is wrong`);
    const geometry = projection.projectGeometry(flat, {tolerancePx: 0.2});
    checkBuffer(geometry, projection);
    requireCondition(
        [...geometry.ringRoles].includes(RingRole.exterior)
            && [...geometry.ringRoles].includes(RingRole.hole),
        `${id} did not preserve polygon exterior/hole roles`
    );
    requireCondition(
        [...geometry.featureIds].includes(0) && [...geometry.featureIds].includes(1),
        `${id} did not preserve multipolygon feature IDs`
    );
    requireCondition(
        maximumSegment(geometry) < Math.hypot(projection.width, projection.height) / 2,
        `${id} output contains a page-spanning false chord`
    );

    const carrier = projection.carrierGeometry();
    checkBuffer(carrier, projection);
    const expectedFaces = id === 'authagraph' ? 1 : projection.descriptor.nativeCellCount;
    requireCondition(carrier.partTypes.length === expectedFaces, `${id} carrier face count changed`);

    const tile = projection.projectGeometry(fixture, {
        slice: {
            id: 'center-tile',
            kind: 'planar-tile',
            view: [projection.width / 4, projection.height / 4,
                projection.width / 2, projection.height / 2]
        }
    });
    checkBuffer(tile, projection);
    requireCondition(tile.frame.width === projection.width / 2, `${id} tile width is wrong`);

    const svg = renderSvg(geometry, {title: `${id} fixture`});
    requireCondition(svg.startsWith('<svg'), `${id} SVG adapter did not return SVG`);
    requireCondition(svg.includes('fill-rule="evenodd"'), `${id} SVG lost hole fill semantics`);

    const canvasCalls = [];
    const canvas = new Proxy({}, {
        get(target, property) {
            if (property in target) return target[property];
            if (['fillStyle', 'strokeStyle', 'lineWidth'].includes(property)) return target[property];
            return (...args) => canvasCalls.push([property, ...args]);
        },
        set(target, property, value) { target[property] = value; return true; }
    });
    drawCommandBuffer(canvas, geometry);
    requireCondition(canvasCalls.some(([call]) => call === 'fill'), `${id} Canvas adapter did not fill`);
    requireCondition(
        canvasCalls.some(([call, rule]) => call === 'fill' && rule === 'evenodd'),
        `${id} Canvas adapter lost hole fill semantics`
    );

    summaries.push({
        id,
        width: projection.width,
        height: projection.height,
        outputParts: geometry.partTypes.length,
        outputVertices: geometry.coordinates.length / 2,
        cuts: geometry.diagnostics.cuts,
        inverseMode: projection.descriptor.inverseMode
    });
    projection.dispose();
}

const ck = runtime.createProjection({id: 'cahill-keyes', width: 440});
const ckSlices = ck.listSlices();
requireCondition(ckSlices.length === 13, 'Cahill-Keyes common slice catalogue is incomplete');
const strip = ck.slice('ck-strip-2');
requireCondition(strip.sourceView.x === 110 && strip.outputFrame.width === 110, 'strip slice view is wrong');
requireCondition(strip.clip === undefined, 'viewport slice unexpectedly has clip paths');
const octant = ck.slice('ck-octant-7');
requireCondition(octant.selectedCells.length === 1, 'octant slice does not select one cell');
requireCondition(octant.clip.partOffsets.length === 2, 'octant slice has no exact clip path');

const ckD3Adapter = cartofreakoD3Projection(ck);
const ckD3Forward = ck.forward([171.2, 7.1]);
const ckD3Reverse = ckD3Adapter.invert([ckD3Forward.x, ckD3Forward.y]);
requireCondition(
    ckD3Reverse && Math.abs(ckD3Reverse[0] - 171.2) < 2e-8
        && Math.abs(ckD3Reverse[1] - 7.1) < 2e-8,
    'D3 Cahill-Keyes inverse adapter failed'
);
const ckD3Candidates = ckD3Adapter.invertCandidates(
    [ckD3Forward.x, ckD3Forward.y],
    {nativeCell: ckD3Forward.nativeCell}
);
requireCondition(
    ckD3Candidates.status === 'unique'
        && ckD3Candidates.candidates.length === 1,
    'D3 Cahill-Keyes candidate adapter failed'
);

const geographic = ck.projectGeometry(fixture, {
    slice: {kind: 'geographic-preclip', bounds: [-20, -20, 20, 20]}
});
checkBuffer(geographic, ck);
requireCondition(
    ![...geographic.featureIds].includes(3),
    'geographic preclip retained out-of-bounds points'
);

const d3Events = [];
const stream = cartofreakoD3Projection(ck).stream({
    point: (x, y) => d3Events.push(['point', x, y]),
    lineStart: () => d3Events.push(['lineStart']),
    lineEnd: () => d3Events.push(['lineEnd']),
    polygonStart: () => d3Events.push(['polygonStart']),
    polygonEnd: () => d3Events.push(['polygonEnd'])
});
stream.polygonStart();
stream.lineStart();
for (const [longitude, latitude] of fixture.features[0].geometry.coordinates[0]) {
    stream.point(longitude, latitude);
}
stream.lineEnd();
stream.lineStart();
for (const [longitude, latitude] of fixture.features[0].geometry.coordinates[1]) {
    stream.point(longitude, latitude);
}
stream.lineEnd();
stream.polygonEnd();
requireCondition(d3Events[0][0] === 'polygonStart', 'D3 adapter did not replay polygon start');
requireCondition(d3Events.at(-1)[0] === 'polygonEnd', 'D3 adapter did not replay polygon end');
ck.dispose();

const d3Myria = runtime.createProjection({id: 'myriahedral', width: 440});
const d3MyriaAdapter = cartofreakoD3Projection(d3Myria);
const d3Forward = d3Myria.forward([171.2, 7.1]);
const d3Reverse = d3MyriaAdapter.invert([d3Forward.x, d3Forward.y]);
requireCondition(
    d3Reverse && Math.abs(d3Reverse[0] - 171.2) < 2e-8
        && Math.abs(d3Reverse[1] - 7.1) < 2e-8,
    'D3 unique inverse adapter failed'
);
d3Myria.dispose();

const myria = runtime.createProjection({id: 'myriahedral', width: 440});
const myriaSlices = myria.listSlices();
requireCondition(myriaSlices.length === 3, 'Myriahedral common slice catalogue is incomplete');
requireCondition(myriaSlices[1].selectedCells.length === 2722, 'Myriahedral group 1 changed');
requireCondition(myriaSlices[2].selectedCells.length === 2398, 'Myriahedral group 2 changed');
const groupCarrier = myria.carrierGeometry({slice: 'myria-group-1'});
requireCondition(groupCarrier.partTypes.length === 2722, 'Myriahedral slice carrier mask is wrong');
myria.dispose();

const pacific = runtime.createProjection({id: 'myriahedral-pacific', width: 440});
requireCondition(pacific.carrierGeometry().partTypes.length === 5120, 'alternate layout is incomplete');
requireCondition(pacific.listSlices().length === 1, 'reference-only semantic slices leaked to alternate layout');
pacific.dispose();

const landUrl = new URL('./cartofreako-cahill-keyes-land-110m.geojson', import.meta.url);
const land = JSON.parse(await fs.readFile(landUrl, 'utf8'));
for (const id of ['cahill-keyes', 'myriahedral']) {
    const projection = runtime.createProjection({id, width: 440});
    const carrier = projection.carrierGeometry();
    const projectedLand = projection.projectGeometry(land, {tolerancePx: 0.35});
    const svg = renderBaseMapSvg(carrier, projectedLand, {title: `${id} Natural Earth`});
    requireCondition(svg.includes('<g id="ocean">'), `${id} common base map has no ocean`);
    requireCondition(svg.includes('<g id="land">'), `${id} common base map has no land`);
    requireCondition(!/(?:nan|inf)/i.test(svg), `${id} common base map is non-finite`);
    summaries.find((summary) => summary.id === id).naturalEarthParts
        = projectedLand.partTypes.length;
    projection.dispose();
}

let rejectedFrame = false;
try {
    const invalid = runtime.createProjection({id: 'voronoi', width: 440, height: 440});
    invalid.dispose();
} catch {
    rejectedFrame = true;
}
requireCondition(rejectedFrame, 'all-projection runtime accepted an invalid frame ratio');

console.log(JSON.stringify({
    implementation: runtime.implementationName,
    abiVersion: runtime.abiVersion,
    apiVersion: runtime.apiVersion,
    projectionFamilies: [...families],
    manifestEntries: runtime.manifest.length,
    summaries
}));

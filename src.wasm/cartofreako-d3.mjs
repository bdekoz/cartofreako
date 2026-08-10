import {GeometryPart, RingRole} from './cartofreako-web.mjs';

function replayLines(buffer, sink) {
    for (let part = 0; part < buffer.partTypes.length; ++part) {
        const begin = buffer.partOffsets[part];
        const end = buffer.partOffsets[part + 1];
        if (buffer.partTypes[part] === GeometryPart.point) {
            for (let point = begin; point < end; ++point) {
                sink.point(buffer.coordinates[point * 2], buffer.coordinates[point * 2 + 1]);
            }
            continue;
        }
        sink.lineStart();
        for (let point = begin; point < end; ++point) {
            sink.point(buffer.coordinates[point * 2], buffer.coordinates[point * 2 + 1]);
        }
        sink.lineEnd();
    }
}

function replayPolygon(buffer, sink) {
    sink.polygonStart();
    replayLines(buffer, sink);
    sink.polygonEnd();
}

/**
 * D3-compatible projection stream. Load d3-geo separately and pass this
 * object to `d3.geoPath(adapter)`.
 */
export function cartofreakoD3Projection(projection, options = {}) {
    const adapter = {
        invertCandidates(point, inverseOptions = {}) {
            return projection.inverse(point, inverseOptions);
        },
        invert(point) {
            const result = projection.inverse(point);
            if (result.status !== 'unique') return null;
            const candidate = result.candidates[0];
            return [candidate.longitude, candidate.latitude];
        },
        stream(sink) {
            let line = null;
            let polygon = null;
            let rings = null;
            return {
                point(longitude, latitude) {
                    if (line) {
                        line.push([longitude, latitude]);
                    } else {
                        const point = projection.project(longitude, latitude);
                        sink.point(point.x, point.y);
                    }
                },
                lineStart() {
                    line = [];
                },
                lineEnd() {
                    if (polygon) {
                        rings.push(line);
                    } else {
                        const buffer = projection.projectGeometry({
                            coordinates: new Float64Array(line.flat()),
                            partOffsets: new Uint32Array([0, line.length]),
                            partTypes: new Uint8Array([GeometryPart.line]),
                            featureIds: new Uint32Array([0]),
                            ringRoles: new Uint8Array([RingRole.none])
                        }, options);
                        replayLines(buffer, sink);
                    }
                    line = null;
                },
                polygonStart() {
                    polygon = true;
                    rings = [];
                },
                polygonEnd() {
                    const coordinates = [];
                    const offsets = [0];
                    const roles = [];
                    for (let index = 0; index < rings.length; ++index) {
                        coordinates.push(...rings[index].flat());
                        offsets.push(coordinates.length / 2);
                        roles.push(index === 0 ? RingRole.exterior : RingRole.hole);
                    }
                    const buffer = projection.projectGeometry({
                        coordinates: new Float64Array(coordinates),
                        partOffsets: new Uint32Array(offsets),
                        partTypes: new Uint8Array(rings.length).fill(GeometryPart.ring),
                        featureIds: new Uint32Array(rings.length),
                        ringRoles: new Uint8Array(roles)
                    }, options);
                    replayPolygon(buffer, sink);
                    polygon = null;
                    rings = null;
                },
                sphere() {
                    replayPolygon(projection.carrierGeometry(options), sink);
                }
            };
        }
    };
    return adapter;
}

export default cartofreakoD3Projection;

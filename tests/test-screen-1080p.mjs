#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

import createCartofreako from '../src.wasm/cartofreako-web.mjs';
import {
    flatTexturePlane,
    projectedToScreen,
    screenToGeographic,
    screenToProjected
} from '../src.wasm/cartofreako-screen.mjs';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const catalog = JSON.parse(await fs.readFile(
    path.join(root, 'assets.generated/catalog/artifacts-v1.json'), 'utf8'
));
const manifestBytes = await fs.readFile(
    path.join(root, 'contracts/standard-artifact-manifest-v1.json'));
const manifest = JSON.parse(manifestBytes);
const schema = JSON.parse(await fs.readFile(
    path.join(root, 'contracts/artifacts-v1.schema.json'), 'utf8'
));

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function sha256(file) {
    const hash = createHash('sha256');
    hash.update(await fs.readFile(path.join(root, file)));
    return hash.digest('hex');
}

async function mapLimit(values, limit, callback) {
    let next = 0;
    async function worker() {
        while (true) {
            const index = next++;
            if (index >= values.length) return;
            await callback(values[index], index);
        }
    }
    await Promise.all(Array.from({length: Math.min(limit, values.length)}, worker));
}

function inside(point, frame, epsilon = 1e-9) {
    return point.x >= frame.x - epsilon && point.x <= frame.x + frame.width + epsilon
        && point.y >= frame.y - epsilon && point.y <= frame.y + frame.height + epsilon;
}

function representativeForSlice(projection, artifact) {
    const selected = new Set(projection.slice(artifact.slice.id).selectedCells);
    for (let latitude = -87.5; latitude <= 87.5; latitude += 2.5) {
        for (let longitude = -177.5; longitude < 180; longitude += 2.5) {
            const forward = projection.forward([longitude, latitude]);
            if (selected.has(forward.nativeCell)
                && inside(forward, artifact.projection.artifactFrame, 0)) {
                return {geographic: [longitude, latitude], forward};
            }
        }
    }
    throw new Error(`${artifact.id} has no representative slice point`);
}

requireCondition(schema.$id.endsWith('/contracts/artifacts-v1.schema.json'), 'wrong schema ID');
requireCondition(catalog.schema === 'cartofreako-artifacts-v1', 'wrong catalog schema');
requireCondition(catalog.consumerProfile.id === 'screen-1080p-lossless-v1'
    && catalog.consumerProfile.recipeVersion === 2, 'wrong screen profile');
requireCondition(catalog.artifacts.length === manifest.artifactCount
    && catalog.artifacts.length === 217, 'standard catalog must contain 217 artifacts');
requireCondition(new Set(catalog.artifacts.map(({id}) => id)).size === 217,
    'artifact IDs are not unique');
requireCondition(new Set(catalog.artifacts.map(({projection}) => projection.id)).size === 11,
    'catalog does not cover all eleven approved layouts');
requireCondition(catalog.artifacts.filter(({slice}) => slice).length === 14,
    'catalog does not cover all fourteen approved slices');
requireCondition(catalog.artifacts.every(({pass}) => pass.lifecycle === 'standard'),
    'non-standard artifact entered the standard catalog');
requireCondition(new Set(catalog.artifacts.map(({pass}) => pass.id)).size === 33,
    'catalog does not cover all thirty-three standard whole-map pass IDs');
requireCondition(catalog.artifacts.filter(({parents}) =>
    parents.svg.path.endsWith('.svg.gz')).length === 84,
'catalog does not use explicit gzip masters for all resource plates');
const manifestIds = [...manifest.artifacts.map(({id}) => id)].sort();
requireCondition(JSON.stringify(catalog.artifacts.map(({id}) => id).sort())
    === JSON.stringify(manifestIds), 'catalog and standard manifest IDs differ');
requireCondition(catalog.sourceRevision.standardManifestSha256
    === createHash('sha256').update(manifestBytes).digest('hex'),
'catalog standard-manifest hash is invalid');

const fileChecks = [];
for (const artifact of catalog.artifacts) {
    const {screen, parents} = artifact;
    requireCondition(screen.canvas.width === 1920 && screen.canvas.height === 1080,
        `${artifact.id} canvas is not 1080p`);
    const box = screen.contentRectangle;
    requireCondition(box.x >= 0 && box.y >= 0
        && box.x + box.width <= 1920 && box.y + box.height <= 1080,
    `${artifact.id} content is cropped`);
    requireCondition(screen.fit === 'contain' && screen.background === '#f4f5f5',
        `${artifact.id} fit/background contract changed`);
    requireCondition(screen.parentFullPngSha256 === parents.fullPng.sha256,
        `${artifact.id} parent linkage changed`);
    requireCondition(screen.png.transparency === 'opaque'
        && screen.webp.transparency === 'opaque'
        && screen.png.colorSpace === 'sRGB' && screen.webp.colorSpace === 'sRGB',
    `${artifact.id} screen delivery metadata is incomplete`);
    for (const value of [parents.svg, parents.pdf, parents.fullPng,
        screen.png, screen.webp]) fileChecks.push({artifactId: artifact.id, value});
}
await mapLimit(fileChecks, 12, async ({artifactId, value}) => {
    requireCondition(await sha256(value.path) === value.sha256,
        `${artifactId} hash mismatch for ${value.path}`);
});

const runtime = await createCartofreako();
const projections = new Map();
for (const artifact of catalog.artifacts) {
    const {screen, projection} = artifact;
    if (!projections.has(projection.id)) {
        projections.set(projection.id, runtime.createProjection({
            id: projection.id,
            width: projection.nativeFrame.width
        }));
    }
    const instance = projections.get(projection.id);
    const sample = artifact.slice ? representativeForSlice(instance, artifact) : (() => {
        const geographic = [171.2, 7.1];
        return {geographic, forward: instance.forward(geographic)};
    })();
    requireCondition(inside(sample.forward, projection.artifactFrame),
        `${artifact.id} test point is outside the artifact frame`);
    const screenPoint = projectedToScreen([sample.forward.x, sample.forward.y], screen);
    const projected = screenToProjected(screenPoint, screen);
    requireCondition(Math.hypot(projected[0] - sample.forward.x,
        projected[1] - sample.forward.y) < 1e-10,
    `${artifact.id} affine round trip failed`);
    const inverse = screenToGeographic(instance, screenPoint, artifact, {
        nativeCell: sample.forward.nativeCell,
        component: sample.forward.component
    });
    requireCondition(inverse.candidates.length === 1, `${artifact.id} inverse pick failed`);
    requireCondition(Math.abs(inverse.candidates[0].longitude - sample.geographic[0]) < 2e-8
        && Math.abs(inverse.candidates[0].latitude - sample.geographic[1]) < 2e-8,
    `${artifact.id} geographic pick is inaccurate`);
    requireCondition(flatTexturePlane(screen).positions.length === 12,
        `${artifact.id} flat texture plane is malformed`);
    const box = screen.contentRectangle;
    if (box.y > 0) {
        let rejected = false;
        try { screenToProjected([960, box.y / 2], screen); } catch (error) {
            rejected = error instanceof RangeError;
        }
        requireCondition(rejected, `${artifact.id} accepted letterbox padding as map data`);
    } else if (box.x > 0) {
        let rejected = false;
        try { screenToProjected([box.x / 2, 540], screen); } catch (error) {
            rejected = error instanceof RangeError;
        }
        requireCondition(rejected, `${artifact.id} accepted pillarbox padding as map data`);
    }
}
for (const projection of projections.values()) projection.dispose();

console.log('screen-1080p: 217 standard artifacts, 11 layouts, 14 slices, lossless files, affine/geographic picking, and no-crop checks passed');

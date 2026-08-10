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

requireCondition(schema.$id.endsWith('/contracts/artifacts-v1.schema.json'), 'wrong schema ID');
requireCondition(catalog.schema === 'cartofreako-artifacts-v1', 'wrong catalog schema');
requireCondition(catalog.consumerProfile.id === 'screen-1080p-lossless-v1', 'wrong profile');
requireCondition(catalog.artifacts.length === 24, 'v1 audit catalog must contain 24 artifacts');
requireCondition(new Set(catalog.artifacts.map(({id}) => id)).size === 24, 'artifact IDs are not unique');
requireCondition(new Set(catalog.artifacts.map(({projection}) => projection.id)).size === 6,
    'catalog does not cover all six projections');
requireCondition(new Set(catalog.artifacts.map(({pass}) => pass.id)).size === 4,
    'catalog does not cover all four audit passes');

const runtime = await createCartofreako();
const geographic = [171.2, 7.1];
for (const artifact of catalog.artifacts) {
    const {screen, projection, parents} = artifact;
    requireCondition(screen.canvas.width === 1920 && screen.canvas.height === 1080,
        `${artifact.id} canvas is not 1080p`);
    const box = screen.contentRectangle;
    requireCondition(box.x >= 0 && box.y >= 0
        && box.x + box.width <= 1920 && box.y + box.height <= 1080,
    `${artifact.id} content is cropped`);
    requireCondition(screen.fit === 'contain' && screen.background === '#f4f5f5',
        `${artifact.id} fit/background contract changed`);
    for (const value of [parents.svg, parents.pdf, parents.fullPng, screen.png, screen.webp]) {
        requireCondition(await sha256(value.path) === value.sha256,
            `${artifact.id} hash mismatch for ${value.path}`);
    }

    const instance = runtime.createProjection({
        id: projection.id,
        width: projection.nativeFrame.width
    });
    const forward = instance.forward(geographic);
    const screenPoint = projectedToScreen([forward.x, forward.y], screen);
    const projected = screenToProjected(screenPoint, screen);
    requireCondition(Math.hypot(projected[0] - forward.x, projected[1] - forward.y) < 1e-10,
        `${artifact.id} affine round trip failed`);
    const inverse = screenToGeographic(instance, screenPoint, artifact, {
        nativeCell: forward.nativeCell,
        component: forward.component
    });
    requireCondition(inverse.candidates.length === 1, `${artifact.id} inverse pick failed`);
    requireCondition(Math.abs(inverse.candidates[0].longitude - geographic[0]) < 2e-8
        && Math.abs(inverse.candidates[0].latitude - geographic[1]) < 2e-8,
        `${artifact.id} geographic pick is inaccurate`);
    requireCondition(flatTexturePlane(screen).positions.length === 12,
        `${artifact.id} flat texture plane is malformed`);
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
    instance.dispose();
}

console.log('screen-1080p: 24 artifacts, six projections, lossless files, affine picking, and no-crop checks passed');

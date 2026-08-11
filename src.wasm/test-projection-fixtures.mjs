import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import createCartofreako from './cartofreako-web.mjs';

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

function longitudeDistance(left, right) {
    const difference = ((left - right + 540) % 360) - 180;
    return Math.abs(difference);
}

const fixtureRoot = path.resolve(process.argv[2] ?? '../../fixtures/projections/v1');
const runtime = await createCartofreako();
let checked = 0;
for (const family of [
    'cahill-keyes', 'authagraph', 'dymaxion',
    'myriahedral', 'star-x', 'voronoi'
]) {
    const document = JSON.parse(await fs.readFile(path.join(fixtureRoot,
        `${family}.json`), 'utf8'));
    for (const layout of document.layouts) {
        const id = family === 'myriahedral' ? layout.layoutId : family;
        const projection = runtime.createProjection({id, width: 440});
        const samples = [layout.cases[0], layout.cases.at(-1)];
        for (const fixture of samples) {
            const [longitude, latitude] = fixture.input.geographic;
            const forward = projection.forward([longitude, latitude]);
            const [u, v] = fixture.expected.projected;
            requireCondition(Math.abs(forward.x / projection.width - u)
                <= fixture.tolerances.normalizedPlanar,
            `${layout.layoutId}/${fixture.caseId}: WebAssembly x mismatch`);
            requireCondition(Math.abs(forward.y / projection.height - v)
                <= fixture.tolerances.normalizedPlanar,
            `${layout.layoutId}/${fixture.caseId}: WebAssembly y mismatch`);
            const reverse = projection.inverse([forward.x, forward.y]);
            requireCondition(reverse.status === fixture.expected.reverseStatus,
                `${layout.layoutId}/${fixture.caseId}: WebAssembly status mismatch`);
            requireCondition(reverse.candidates.some(candidate =>
                candidate.component === forward.component
                    && Math.abs(candidate.latitude - latitude)
                        <= fixture.tolerances.angularDegrees
                    && longitudeDistance(candidate.longitude, longitude)
                        <= fixture.tolerances.angularDegrees),
            `${layout.layoutId}/${fixture.caseId}: WebAssembly candidate missing`);
            ++checked;
        }
        projection.dispose();
    }
}
console.log(`WebAssembly projection fixture adapter passed: ${checked} samples`);

#!/usr/bin/env node

import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const vendor = path.join(root, 'src.wasm/third_party/three-0.185.1');
const expected = new Map([
    ['build/three.module.min.js', '86bcee248b64f44bcfc23c331ae74619061957d59cab040171dcb6fb5900beb6'],
    ['build/three.core.min.js', '05b2609338c76cd65daf74f3ac515bc9a5045e1b3b33edc07d8c9bd55250fa90'],
    ['LICENSE', '8b378ebe60e2fe500158cb0ac71cb5e8b7d92953c2abcc63a0eb90499653b5bc'],
    ['package.json', '1d5c438acdc1fe5a52fb8ede2e417afd91fec91d22275c40f7b739591b24e4df']
]);
for (const [file, digest] of expected) {
    const bytes = await fs.readFile(path.join(vendor, file));
    const actual = createHash('sha256').update(bytes).digest('hex');
    if (actual !== digest) throw new Error(`Three.js vendor hash changed: ${file}`);
}
const packageJson = JSON.parse(await fs.readFile(path.join(vendor, 'package.json')));
if (packageJson.name !== 'three' || packageJson.version !== '0.185.1'
    || packageJson.license !== 'MIT') {
    throw new Error('Three.js vendor identity changed');
}
console.log('Three.js vendor passed: npm three@0.185.1 / r185 / MIT / four files');

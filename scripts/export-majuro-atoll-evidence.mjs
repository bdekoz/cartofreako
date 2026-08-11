#!/usr/bin/env node

import {execFile} from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {promisify} from 'node:util';

const exec = promisify(execFile);
const root = path.resolve(new URL('..', import.meta.url).pathname);
const manifest = JSON.parse(await fs.readFile(path.join(
    root, 'fixtures/atoll-evidence/v1/pass-manifest.json'), 'utf8'));
const browser = process.env.WEB_BROWSER || 'google-chrome';

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

async function command(program, commandArguments) {
    try {
        return await exec(program, commandArguments, {
            cwd: root,
            encoding: 'utf8',
            maxBuffer: 16 * 1024 * 1024
        });
    } catch (error) {
        throw new Error(`${program} failed (${error.code ?? 'unknown'}): ${error.stderr ?? error.message}`);
    }
}

function rasterDimensions(page) {
    if (page.orientation === 'portrait') {
        return {
            width: Math.round(3840 * page.widthInches / page.heightInches),
            height: 3840
        };
    }
    return {
        width: 3840,
        height: Math.round(3840 * page.heightInches / page.widthInches)
    };
}

function html(svg, page) {
    const source = pathToFileURL(svg).href;
    return `<!doctype html>
<meta charset="utf-8">
<style>
@page { size: ${page.widthInches}in ${page.heightInches}in; margin: 0; }
html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: #f4f5f5; }
img { display: block; width: 100%; height: 100%; object-fit: fill; }
</style>
<img src="${source}" alt="">
`;
}

function pngDimensions(data) {
    requireCondition(data.subarray(0, 8).equals(
        Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
    'Chromium export did not produce a PNG');
    return {width: data.readUInt32BE(16), height: data.readUInt32BE(20)};
}

const temporary = await fs.mkdtemp(
    path.join(os.tmpdir(), 'cartofreako-majuro-export.'));
try {
    for (const layout of manifest.layouts) {
        const svg = path.join(root, layout.artifacts.svg);
        const png = path.join(root, layout.artifacts.png);
        const pdf = path.join(root, layout.artifacts.pdf);
        const thumbnail = path.join(root, layout.artifacts.thumbnail);
        const dimensions = rasterDimensions(layout.page);
        const page = path.join(temporary, `${layout.id}.html`);
        const temporaryPng = path.join(temporary, `${layout.id}.png`);
        const temporaryPdf = path.join(temporary, `${layout.id}.pdf`);
        const temporaryThumbnail = path.join(temporary,
            `${layout.id}-thumbnail.png`);
        const profile = path.join(temporary, `profile-${layout.id}`);
        await fs.writeFile(page, html(svg, layout.page), 'utf8');
        await command(browser, [
            '--headless=new', '--no-sandbox', '--disable-gpu',
            '--hide-scrollbars', '--allow-file-access-from-files',
            '--force-device-scale-factor=1',
            '--run-all-compositor-stages-before-draw',
            '--virtual-time-budget=2500', `--user-data-dir=${profile}`,
            `--window-size=${dimensions.width},${dimensions.height}`,
            `--screenshot=${temporaryPng}`, pathToFileURL(page).href
        ]);
        const actual = pngDimensions(await fs.readFile(temporaryPng));
        requireCondition(actual.width === dimensions.width
            && actual.height === dimensions.height,
        `${layout.id} PNG dimensions are ${actual.width}x${actual.height}`);
        await fs.rm(profile, {recursive: true, force: true});
        await command(browser, [
            '--headless=new', '--no-sandbox', '--disable-gpu',
            '--allow-file-access-from-files', '--no-pdf-header-footer',
            '--run-all-compositor-stages-before-draw',
            '--virtual-time-budget=2500', `--user-data-dir=${profile}`,
            `--print-to-pdf=${temporaryPdf}`, pathToFileURL(page).href
        ]);
        const pdfBytes = await fs.readFile(temporaryPdf);
        requireCondition(pdfBytes.subarray(0, 5).toString() === '%PDF-',
            `${layout.id} export did not produce a PDF`);
        await command('magick', [temporaryPng, '-filter', 'Lanczos',
            '-resize', '480x', '-strip', '-depth', '8',
            '-define', 'png:compression-level=9',
            '-define', 'png:exclude-chunks=date,time', temporaryThumbnail]);
        await Promise.all([
            fs.mkdir(path.dirname(png), {recursive: true}),
            fs.mkdir(path.dirname(pdf), {recursive: true}),
            fs.mkdir(path.dirname(thumbnail), {recursive: true})
        ]);
        await Promise.all([
            fs.copyFile(temporaryPng, png),
            fs.copyFile(temporaryPdf, pdf),
            fs.copyFile(temporaryThumbnail, thumbnail)
        ]);
        console.log(`Exported ${layout.id}: ${dimensions.width}x${dimensions.height} PNG, PDF, and 480px thumbnail`);
    }
} finally {
    await fs.rm(temporary, {recursive: true, force: true});
}

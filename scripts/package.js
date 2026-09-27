#!/usr/bin/env node
const archiver = require('archiver');
const fs = require('fs');
const manifest = require('../manifest.json');
const outputFile = `dist/cineforge-v${manifest.version}.zip`;
fs.mkdirSync('dist', { recursive: true });
const output = fs.createWriteStream(outputFile);
const archive = archiver('zip', { zlib: { level: 9 } });
output.on('close', () => console.log(`✓ ${outputFile}`));
archive.on('error', err => { throw err; });
archive.pipe(output);
archive.file('manifest.json', { name: 'manifest.json' });
archive.directory('src', 'src');
archive.glob('icons/*.png');
archive.finalize();

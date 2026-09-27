#!/usr/bin/env node
/**
 * Packages the extension into a .zip for Chrome Web Store submission
 */
const archiver = require('archiver');
const fs = require('fs');
const path = require('path');

const manifest = require('../manifest.json');
const version = manifest.version;
const outputFile = `dist/cineforge-v${version}.zip`;

fs.mkdirSync('dist', { recursive: true });

const output = fs.createWriteStream(outputFile);
const archive = archiver('zip', { zlib: { level: 9 } });

output.on('close', () => {
  console.log(`✓ ${outputFile} (${(archive.pointer() / 1024).toFixed(1)} KB)`);
});

archive.on('error', err => { throw err; });
archive.pipe(output);

// Include all required files
const INCLUDE = ['manifest.json', 'src/**', 'icons/*.png'];
const EXCLUDE = ['**/*.test.js', '**/node_modules/**', '**/.DS_Store', 'icons/generate-icons.js'];

INCLUDE.forEach(pattern => {
  if (pattern.includes('**')) {
    const base = pattern.split('/**')[0];
    archive.directory(base, base, entry => {
      const rel = entry.name;
      return EXCLUDE.some(ex => {
        const simple = ex.replace('**/','').replace('/**','');
        return rel.includes(simple);
      }) ? false : entry;
    });
  } else {
    archive.file(pattern, { name: pattern });
  }
});

archive.finalize();

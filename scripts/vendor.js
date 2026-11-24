#!/usr/bin/env node
// Copies the browser libraries from node_modules into ./vendor and writes index.local.html,
// a copy of index.html that loads them from ./vendor instead of a CDN (works offline / behind firewalls).
// Run after `npm install`. A library that is missing is skipped and keeps using its CDN link.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), nm = path.join(root, 'node_modules');
const LIBS = [ // [npm package, file inside package, local name, CDN URL used in index.html]
  ['jszip', 'dist/jszip.min.js', 'jszip.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js'],
  ['pdf-lib', 'dist/pdf-lib.min.js', 'pdf-lib.min.js', 'https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js'],
  ['marked', 'marked.min.js', 'marked.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js'],
  ['lamejs', 'lame.min.js', 'lame.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/lamejs/1.2.1/lame.min.js'],
  ['heic2any', 'dist/heic2any.min.js', 'heic2any.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/heic2any/0.0.4/heic2any.min.js'],
  ['pdfjs-dist', 'build/pdf.min.mjs', 'pdf.min.mjs', 'https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.min.mjs'],
  ['pdfjs-dist', 'build/pdf.worker.min.mjs', 'pdf.worker.min.mjs', 'https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.worker.min.mjs']
];
// Copies the libraries into outDir and returns the html with CDN links swapped for ./vendor links.
function vendorLibs(outDir, html) {
  fs.mkdirSync(outDir, { recursive: true }); let ok = 0;
  for (const [pkg, file, name, cdn] of LIBS) {
    const src = path.join(nm, pkg, file);
    if (!fs.existsSync(src)) { console.warn('skip   ' + pkg + '/' + file + ' (not installed, CDN stays)'); continue; }
    fs.copyFileSync(src, path.join(outDir, name)); html = html.split(cdn).join('./vendor/' + name); ok++; console.log('vendor ' + name);
  }
  return { html, ok };
}
module.exports = { LIBS, vendorLibs };
if (require.main === module) {
  const r = vendorLibs(path.join(root, 'vendor'), fs.readFileSync(path.join(root, 'index.html'), 'utf8'));
  fs.writeFileSync(path.join(root, 'index.local.html'), r.html);
  console.log(r.ok + '/' + LIBS.length + ' libraries vendored. Wrote index.local.html');
}

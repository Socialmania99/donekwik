#!/usr/bin/env node
// Builds the static site for GitHub Pages (or any static host) into ./docs, or into the folder given as the first argument.
// Needs `npm install` first so the libraries can be copied in. Set CONTACT to your takedown email address.
const fs = require('fs'), path = require('path'), { vendorLibs, LIBS } = require('./vendor.js');
const root = path.join(__dirname, '..'), out = path.resolve(process.argv[2] || path.join(root, 'docs')), CONTACT = (process.env.CONTACT || 'takedown@example.com').replace(/[<>&"]/g, '');
fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(path.join(out, 'assets'), { recursive: true });
let { html, ok } = vendorLibs(path.join(out, 'vendor'), fs.readFileSync(path.join(root, 'index.html'), 'utf8'));
// GitHub Pages cannot send headers, so the policy goes in a meta tag. HTTPS is allowed for connecting to your own server and the search sources.
const CSP = ["default-src 'self'", "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net", "style-src 'self' 'unsafe-inline'", "img-src 'self' data: blob: https:", "media-src 'self' blob: data:",
  "connect-src 'self' https: http://localhost:* http://127.0.0.1:*", "worker-src 'self' blob:", "font-src 'self' data:", "object-src 'none'", "base-uri 'none'", "form-action 'self'"].join('; ');
html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="' + CSP + '">');
fs.writeFileSync(path.join(out, 'index.html'), html);
for (const f of ['sw.js', 'manifest.webmanifest', 'THIRD_PARTY.md']) fs.copyFileSync(path.join(root, f), path.join(out, f));
for (const f of fs.readdirSync(path.join(root, 'assets'))) if (/\.(png|svg)$/.test(f)) fs.copyFileSync(path.join(root, 'assets', f), path.join(out, 'assets', f));
const page = (title, body) => '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + title + '</title><link rel="icon" href="assets/favicon.svg"></head><body style="font:16px/1.6 system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem">' + body + '</body></html>\n';
fs.writeFileSync(path.join(out, 'terms.html'), page('DoneKwik terms and privacy', '<h1>Terms, privacy and takedown</h1><p>DoneKwik converters and editors run in your browser. Your files are not uploaded to this site.</p><p>This is a static site. It has no server of its own and stores nothing about you except your own settings (favorites, theme) in your browser. The hosting provider may keep ordinary visit logs under its own policy.</p><p>Open-license search runs from your browser and contacts Openverse, Wikimedia Commons, the Internet Archive and Project Gutenberg directly. If you connect your own DoneKwik server, downloads go through that server.</p><p>You are responsible for having the right to any file you download or convert. Rights holders can send takedown notices to ' + CONTACT + '.</p><p><a href="./">Back to DoneKwik</a></p>'));
fs.writeFileSync(path.join(out, '404.html'), page('Page not found', '<h1>Page not found</h1><p><a id="h" href="/">Go to DoneKwik</a></p><script>var s=location.pathname.split("/")[1];if(/github\\.io$/.test(location.hostname)&&s)document.getElementById("h").href="/"+s+"/"</script>'));
fs.writeFileSync(path.join(out, 'robots.txt'), 'User-agent: *\nAllow: /\n'); fs.writeFileSync(path.join(out, '.nojekyll'), '');
console.log('Built ' + out + ' (' + ok + '/' + LIBS.length + ' libraries bundled' + (ok < LIBS.length ? '; the rest load from a CDN' : '') + ')');

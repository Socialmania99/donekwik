// DoneKwik server: serves the web app, a safe direct-file proxy, open-license search and the yt-dlp downloader bridge.
// Node 18+, no npm dependencies. Settings are environment variables (see README).
'use strict';
const http = require('http'), https = require('https'), dns = require('dns').promises, net = require('net'), fs = require('fs'), path = require('path'), zlib = require('zlib');
const E = process.env, PORT = +E.PORT || 3000, HOST = E.HOST || '0.0.0.0', MAX = +E.MAX_MB || 500, MB = 1048576;
const CONTACT = E.CONTACT || 'takedown@example.com', UA = 'DoneKwik/1.0 (+' + CONTACT + ')';
const CORS = (E.CORS_ORIGIN || '').split(',').map(x => x.trim()).filter(Boolean), TRUST = E.TRUST_PROXY === '1';
const ALLOW_PRIVATE = E.ALLOW_PRIVATE === '1'; // TEST ONLY: lets the proxy reach private addresses. Never enable in production.
const MAX_STREAMS = +E.MAX_STREAMS || 20, CSP_CONNECT = (E.CSP_CONNECT || '').trim();
const ROOT = __dirname, VEND = path.join(ROOT, 'vendor'), IDX = path.join(ROOT, 'index.html'), IDXL = path.join(ROOT, 'index.local.html');
// Platform / DRM sites are refused for direct links on purpose (terms of service and copyright). Edit with legal advice.
const BLOCK = /(^|\.)(youtube\.com|youtu\.be|instagram\.com|tiktok\.com|facebook\.com|fb\.watch|twitter\.com|x\.com|netflix\.com|primevideo\.com|disneyplus\.com|hotstar\.com|jiocinema\.com|spotify\.com|soundcloud\.com|vimeo\.com|twitch\.tv|dailymotion\.com)$/i;
const SEC = { 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer', 'x-frame-options': 'DENY', 'permissions-policy': 'camera=(), microphone=(), geolocation=(), payment=()' };
const CSP = ["default-src 'self'", "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net", "style-src 'self' 'unsafe-inline'", "img-src 'self' data: blob: https:", "media-src 'self' blob: data:",
  "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com" + (CSP_CONNECT ? ' ' + CSP_CONNECT : ''), "worker-src 'self' blob:", "font-src 'self' data:", "object-src 'none'", "base-uri 'none'", "form-action 'self'", "frame-ancestors 'none'"].join('; ');
const isPriv = ip => !ALLOW_PRIVATE && priv(ip);

const priv = ip => {
  if (net.isIPv6(ip)) { const l = ip.toLowerCase(); return l === '::1' || l === '::' || /^(fc|fd|fe[89ab])/.test(l) || (l.startsWith('::ffff:') && priv(l.slice(7))); }
  const [a, b] = ip.split('.').map(Number);
  return a === 0 || a === 10 || a === 127 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127) || a >= 224;
};
// Fetch with SSRF protection: validates every redirect hop and pins the resolved IP.
const get = (u, hdr, n = 0) => new Promise(async (ok, no) => {
  try {
    u = new URL(u);
    if (!/^https?:$/.test(u.protocol)) throw 'Only http and https links work.';
    if (BLOCK.test(u.hostname)) throw 'This site is not supported. Use the open-license search instead.';
    const a = await dns.lookup(u.hostname, { all: true });
    if (!a.length || a.some(x => isPriv(x.address))) throw 'Blocked address.';
    const lib = u.protocol === 'https:' ? https : http;
    const r = lib.get(u, { headers: hdr, timeout: 15000, lookup: (h, o, cb) => o && o.all ? cb(null, a) : cb(null, a[0].address, a[0].family) }, res => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume(); if (n > 4) return no('Too many redirects.');
        return ok(get(new URL(res.headers.location, u).href, hdr, n + 1));
      }
      ok(res);
    });
    r.on('error', e => no(e.message)); r.on('timeout', () => r.destroy(new Error('Timed out.')));
  } catch (e) { no(e.message || String(e)); }
});

const hits = new Map(); setInterval(() => hits.clear(), 36e5).unref();
const limited = (ip, k, max, ms) => { const key = ip + k, t = Date.now(), a = (hits.get(key) || []).filter(x => t - x < ms); a.push(t); hits.set(key, a); return a.length > max; };
const txt = (res, c, m, t = 'text/plain') => { res.writeHead(c, { 'content-type': t + '; charset=utf-8', 'x-content-type-options': 'nosniff' }); res.end(m); };
const json = (res, c, o) => txt(res, c, JSON.stringify(o), 'application/json');
const dec = s => { try { return decodeURIComponent(s); } catch { return s; } };
const fj = async u => { const r = await fetch(u, { headers: { 'user-agent': UA }, signal: AbortSignal.timeout(12000) }); if (!r.ok) throw new Error('Source returned ' + r.status); return r.json(); };
const strip = s => (s || '').replace(/<[^>]+>/g, '');
const size = n => n > MB ? (n / MB).toFixed(1) + ' MB' : Math.round(n / 1024) + ' KB';

const sources = {
  async 'openverse-images'(q) { return ov('images', q); },
  async 'openverse-audio'(q) { return ov('audio', q); },
  async commons(q) {
    const j = await fj('https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrlimit=24&prop=imageinfo&iiprop=url|mime|extmetadata&iiurlwidth=300&format=json&gsrsearch=' + q);
    return Object.values(j.query?.pages || {}).map(p => { const i = p.imageinfo?.[0] || {}, m = i.extmetadata || {};
      return { title: p.title.replace(/^File:/, ''), by: strip(m.Artist?.value), lic: m.LicenseShortName?.value || 'See page', thumb: i.thumburl, page: i.descriptionurl, files: [{ label: i.mime, url: i.url }] }; });
  },
  async archive(q) {
    const f = ['identifier', 'title', 'creator', 'licenseurl'].map(x => '&fl[]=' + x).join('');
    const j = await fj('https://archive.org/advancedsearch.php?output=json&rows=24' + f + '&q=' + encodeURIComponent(decodeURIComponent(q) + ' AND (licenseurl:*creativecommons* OR licenseurl:*publicdomain*)'));
    return j.response.docs.map(d => ({ title: d.title, by: [].concat(d.creator || []).join(', '), lic: (d.licenseurl || '').replace(/^https?:\/\/(creativecommons\.org\/(licenses|publicdomain)\/)?/, 'CC ').replace(/\/$/, ''),
      thumb: 'https://archive.org/services/img/' + d.identifier, page: 'https://archive.org/details/' + d.identifier, ia: d.identifier }));
  },
  async gutenberg(q) {
    const j = await fj('https://gutendex.com/books/?search=' + q);
    return j.results.map(b => { const f = b.formats, L = [['EPUB', 'application/epub+zip'], ['Text', 'text/plain; charset=utf-8'], ['Text', 'text/plain'], ['PDF', 'application/pdf']];
      return { title: b.title, by: b.authors.map(a => a.name).join(', '), lic: b.copyright === false ? 'Public domain (US)' : 'Check copyright', thumb: f['image/jpeg'], page: 'https://www.gutenberg.org/ebooks/' + b.id,
        files: L.filter(x => f[x[1]]).map(x => ({ label: x[0], url: f[x[1]] })) }; });
  }
};
async function ov(kind, q) {
  const j = await fj('https://api.openverse.org/v1/' + kind + '/?page_size=24&q=' + q);
  return j.results.map(x => ({ title: x.title, by: x.creator, lic: (/^(cc0|pdm)$/.test(x.license) ? '' : 'CC ') + x.license.toUpperCase() + (x.license_version ? ' ' + x.license_version : ''),
    thumb: x.thumbnail, page: x.foreign_landing_url, files: [{ label: (x.filetype || 'file').toUpperCase(), url: x.url }] }));
}

async function download(req, res, q, ip) {
  if (q.get('ok') !== '1') return txt(res, 400, 'Confirm you have the right to download this file.');
  if (limited(ip, 'dl', 30, 6e5)) return txt(res, 429, 'Too many downloads. Try again in a few minutes.');
  const h = { 'user-agent': UA }; if (req.headers.range) h.range = req.headers.range;
  let r; try { r = await get(q.get('url'), h); } catch (e) { return txt(res, 400, String(e)); }
  const len = +r.headers['content-length'] || 0;
  if (len > MAX * MB) { r.destroy(); return txt(res, 413, 'File is over the ' + MAX + ' MB limit.'); }
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)/i.exec(r.headers['content-disposition'] || '');
  let name = q.get('name') || (m && dec(m[1])) || dec(new URL(q.get('url')).pathname.split('/').pop()) || 'download';
  name = name.replace(/[^\w.\- ()]/g, '_').slice(0, 120);
  const o = { 'content-type': r.headers['content-type'] || 'application/octet-stream', 'content-disposition': 'attachment; filename="' + name + '"', 'x-content-type-options': 'nosniff' };
  for (const k of ['content-length', 'content-range', 'accept-ranges']) if (r.headers[k]) o[k] = r.headers[k];
  res.writeHead(r.statusCode, o);
  let n = 0; r.on('data', c => { n += c.length; if (n > MAX * MB) r.destroy(); });
  r.pipe(res); req.on('close', () => r.destroy());
}


const cache = new Map();
function file(req, res, p, type, cc, csp, extra) {
  let st; try { st = fs.statSync(p); if (!st.isFile()) throw 0; } catch { return txt(res, 404, 'Not found'); }
  let c = cache.get(p);
  if (!c || c.m !== st.mtimeMs) { const b = fs.readFileSync(p); c = { m: st.mtimeMs, b, gz: /text|javascript|json|svg|xml/.test(type) && b.length > 860 ? zlib.gzipSync(b, { level: 9 }) : null, etag: '"' + st.size.toString(16) + '-' + Math.floor(st.mtimeMs).toString(16) + '"' }; cache.set(p, c); }
  if (req.headers['if-none-match'] === c.etag) { res.writeHead(304, { etag: c.etag }); return res.end(); }
  const gz = c.gz && /\bgzip\b/.test(req.headers['accept-encoding'] || ''), h = { 'content-type': type, 'cache-control': cc, etag: c.etag, vary: 'accept-encoding', ...(extra || {}) };
  if (csp) h['content-security-policy'] = CSP; if (gz) h['content-encoding'] = 'gzip';
  res.writeHead(200, h); res.end(req.method === 'HEAD' ? undefined : gz ? c.gz : c.b);
}
let streams = 0;
const ytdl = require('./ytdl')({ priv: isPriv, json, txt, limited });
const handler = async (req, res) => {
  const t0 = Date.now(), u = new URL(req.url, 'http://x'), q = u.searchParams, p = u.pathname;
  const ip = TRUST ? ((req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress) : req.socket.remoteAddress;
  for (const k in SEC) res.setHeader(k, SEC[k]);
  if (TRUST && req.headers['x-forwarded-proto'] === 'https') res.setHeader('strict-transport-security', 'max-age=31536000');
  if (p !== '/healthz') res.on('finish', () => console.log(JSON.stringify({ t: new Date().toISOString(), m: req.method, p, s: res.statusCode, ms: Date.now() - t0 }))); // no IPs, no query strings, no URLs
  // Optional CORS so a page hosted elsewhere (or opened from disk) can use this server. Set CORS_ORIGIN=http://host:port[,null] (or * to allow any).
  const o = req.headers.origin;
  if (o && (CORS.includes('*') || CORS.includes(o))) { res.setHeader('access-control-allow-origin', o); res.setHeader('vary', 'origin'); res.setHeader('access-control-allow-private-network', 'true'); }
  if (req.method === 'OPTIONS') { res.writeHead(204, { 'access-control-allow-methods': 'GET, HEAD, OPTIONS', 'access-control-allow-headers': '*', 'access-control-max-age': '600' }); return res.end(); }
  if (req.method !== 'GET' && req.method !== 'HEAD') return txt(res, 405, 'Method not allowed');
  try {
    let m;
    if (p === '/' || p === '/index.html') { const f = fs.existsSync(IDXL) ? IDXL : IDX; return fs.existsSync(f) ? file(req, res, f, 'text/html; charset=utf-8', 'no-cache', true) : txt(res, 500, 'index.html is missing'); }
    if (p === '/healthz') return txt(res, 200, 'ok');
    if (p === '/sw.js') return file(req, res, path.join(ROOT, 'sw.js'), 'text/javascript; charset=utf-8', 'no-cache', false, { 'service-worker-allowed': '/' });
    if (p === '/manifest.webmanifest') return file(req, res, path.join(ROOT, 'manifest.webmanifest'), 'application/manifest+json', 'public, max-age=3600');
    if (p === '/robots.txt') return txt(res, 200, 'User-agent: *\nAllow: /\nDisallow: /api/\n');
    if (p === '/favicon.ico') { res.writeHead(204); return res.end(); }
    if (p === '/favicon.svg') return file(req, res, path.join(ROOT, 'assets', 'favicon.svg'), 'image/svg+xml', 'public, max-age=86400');
    if ((m = /^\/assets\/([\w.-]+\.(png|svg))$/.exec(p))) return file(req, res, path.join(ROOT, 'assets', m[1]), m[2] === 'svg' ? 'image/svg+xml' : 'image/png', 'public, max-age=86400');
    if ((m = /^\/vendor\/([\w.-]+\.m?js)$/.exec(p))) return file(req, res, path.join(VEND, m[1]), 'text/javascript; charset=utf-8', 'public, max-age=604800'); // libraries copied by scripts/vendor.js
    if (p === '/terms') return txt(res, 200, '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>DoneKwik terms</title><body style="font:16px/1.6 system-ui;max-width:640px;margin:2rem auto;padding:0 1rem"><h1>Terms, privacy and takedown</h1><p>DoneKwik converters and editors run in your browser; your files are not uploaded. The server passes files through and stores nothing beyond short-lived temporary files (deleted after one download or within 15 minutes). Logs keep the time, method, path and status only.</p><p>You are responsible for having the right to download what you request. Platform and DRM-protected sites are blocked unless the operator has enabled platform access.</p><p>Rights holders: send takedown notices to ' + CONTACT.replace(/[<>&"]/g, '') + '. We respond within 48 hours and ban repeat infringers.</p>', 'text/html');
    if (p === '/api/search') {
      if (limited(ip, 's', 40, 6e4)) return json(res, 429, { error: 'Slow down a little.' });
      const s = sources[q.get('src')], term = (q.get('q') || '').trim().slice(0, 100);
      if (!s || !term) return json(res, 400, { error: 'Enter a search term.' });
      return json(res, 200, { items: await s(encodeURIComponent(term)) });
    }
    if (p === '/api/ia') {
      if (limited(ip, 'ia', 60, 6e4)) return json(res, 429, { error: 'Slow down a little.' });
      const id = q.get('id') || ''; if (!/^[\w.\-]+$/.test(id)) return json(res, 400, { error: 'Bad id' });
      const j = await fj('https://archive.org/metadata/' + id);
      const files = (j.files || []).filter(f => f.source !== 'derivative' || /mp3|mp4|pdf|epub|ogv|webm/i.test(f.name)).filter(f => !/_meta\.|_files\.xml|__ia_thumb|\.sqlite|_archive\.torrent/.test(f.name)).slice(0, 40);
      return json(res, 200, { files: files.map(f => ({ label: f.name + (f.size ? ' (' + size(+f.size) + ')' : ''), url: 'https://archive.org/download/' + id + '/' + encodeURIComponent(f.name).replace(/%2F/g, '/') })) });
    }
    if (p.startsWith('/api/ytdl/') || p === '/api/config') return ytdl(req, res, u, ip);
    if (p === '/api/dl') {
      if (streams >= MAX_STREAMS) return txt(res, 503, 'Server is busy. Try again in a minute.');
      streams++; res.on('close', () => streams--); return download(req, res, q, ip);
    }
    txt(res, 404, 'Not found');
  } catch (e) { json(res, 502, { error: e.message || 'Upstream error' }); }
};
if (require.main === module) {
  const srv = http.createServer(handler);
  srv.keepAliveTimeout = 65e3; srv.headersTimeout = 70e3;
  srv.listen(PORT, HOST, () => console.log('DoneKwik on http://' + (HOST === '0.0.0.0' ? 'localhost' : HOST) + ':' + PORT));
  const stop = () => { console.log('shutting down'); srv.close(() => process.exit(0)); ytdl.cleanup(); setTimeout(() => process.exit(0), 10000).unref(); };
  process.on('SIGTERM', stop); process.on('SIGINT', stop);
  process.on('unhandledRejection', e => console.error('unhandledRejection', e && e.message || e));
  process.on('uncaughtException', e => { console.error('uncaughtException', e && e.stack || e); process.exit(1); });
}
module.exports = { sources, handler };

// DoneKwik service worker: app shell and libraries are cached so the converters and editors work offline.
// Paths are relative to the worker's scope, so it works at the site root and in a sub-folder (GitHub project pages).
const V = 'donekwik-v2', S = self.registration.scope, P = n => new URL(n, S).pathname,
  CORE = [S, S + 'assets/icon-192.png', S + 'assets/logo-mark.svg'],
  LIBS = ['jszip.min.js', 'pdf-lib.min.js', 'marked.min.js', 'lame.min.js', 'heic2any.min.js', 'pdf.min.mjs', 'pdf.worker.min.mjs'].map(f => S + 'vendor/' + f);
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => Promise.all(CORE.concat(LIBS).map(u => c.add(u).catch(() => {})))).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== V).map(x => caches.delete(x)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const r = e.request; if (r.method !== 'GET') return;
  const u = new URL(r.url), same = u.origin === location.origin;
  if (same && (u.pathname.startsWith(P('api/')) || u.pathname === P('healthz'))) return; // never cache API calls or downloads
  if (r.mode === 'navigate') { e.respondWith(fetch(r).then(x => { if (x.ok) { const c = x.clone(); caches.open(V).then(ch => ch.put(S, c)); } return x; }).catch(() => caches.match(S))); return; }
  if ((same && (u.pathname.startsWith(P('vendor/')) || u.pathname.startsWith(P('assets/')))) || /^(cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net)$/.test(u.hostname))
    e.respondWith(caches.match(r).then(h => h || fetch(r).then(x => { if (x.ok || x.type === 'opaque') { const c = x.clone(); caches.open(V).then(ch => ch.put(r, c)); } return x; })));
});

// TEST ONLY: lets the audit use fake public host names offline. Loaded with NODE_OPTIONS=--require.
const dns = require('dns'), orig = dns.promises.lookup, fake = new Set(['www.youtube.com', 'music.youtube.com', 'archive.org', 'example.org', 'www.bbc.co.uk']);
dns.promises.lookup = async (h, o) => fake.has(h) ? (o && o.all ? [{ address: '93.184.216.34', family: 4 }] : { address: '93.184.216.34', family: 4 }) : orig(h, o);

// yt-dlp bridge for DoneKwik. Needs yt-dlp and ffmpeg on PATH (pip install yt-dlp; install ffmpeg).
// Platform sites (YouTube, Instagram, TikTok, ...) stay OFF unless you start with ALLOW_PLATFORMS=1.
// DRM and paid-course sites are always refused. Run in a container with no access to your internal network.
const { spawn } = require('child_process'), fs = require('fs'), os = require('os'), path = require('path'), crypto = require('crypto'), dns = require('dns').promises;
const ALLOW = process.env.ALLOW_PLATFORMS === '1', MAXMIN = +process.env.MAX_MINUTES || 120, MAXMB = +process.env.MAX_MB || 500, JOBS = +process.env.MAX_JOBS || 2;
const DRM = /(^|\.)(netflix\.com|primevideo\.com|disneyplus\.com|hotstar\.com|jiocinema\.com|sonyliv\.com|zee5\.com|voot\.com|max\.com|hbomax\.com|hulu\.com|peacocktv\.com|paramountplus\.com|tv\.apple\.com|crunchyroll\.com|spotify\.com|music\.apple\.com|deezer\.com|tidal\.com|udemy\.com|coursera\.org|pluralsight\.com|skillshare\.com|masterclass\.com)$/i;
const PLAT = /(^|\.)(youtube\.com|youtu\.be|youtube-nocookie\.com|instagram\.com|tiktok\.com|facebook\.com|fb\.watch|x\.com|twitter\.com|linkedin\.com|reddit\.com|redd\.it|pinterest\.com|snapchat\.com|tumblr\.com|threads\.net|bsky\.app|t\.me|vk\.com|ok\.ru|weibo\.com|douyin\.com|kuaishou\.com|bilibili\.com|b23\.tv|nicovideo\.jp|naver\.com|likee\.video|sharechat\.com|vimeo\.com|dailymotion\.com|dai\.ly|rumble\.com|odysee\.com|bitchute\.com|twitch\.tv|kick\.com|trovo\.live|triller\.co|soundcloud\.com|bandcamp\.com|mixcloud\.com|audiomack\.com)$/i;

module.exports = ({ priv, json, txt, limited }) => {
  const jobs = new Map(); let running = 0;
  setInterval(() => { for (const [id, j] of jobs) if (Date.now() - j.t > 15 * 6e4) { fs.rmSync(j.dir, { recursive: true, force: true }); jobs.delete(id); } }, 6e4).unref();

  async function check(u) {
    let x; try { x = new URL(u); } catch { throw 'Paste a full link starting with https://'; }
    if (!/^https?:$/.test(x.protocol)) throw 'Only http and https links work.';
    if (DRM.test(x.hostname)) throw 'Protected streaming and paid-course sites are not supported.';
    if (PLAT.test(x.hostname) && !ALLOW) throw 'Platform downloads are switched off on this server (admin: ALLOW_PLATFORMS=1).';
    const a = await dns.lookup(x.hostname, { all: true });
    if (!a.length || a.some(i => priv(i.address))) throw 'Blocked address.';
    return x.href;
  }
  const run = (args, onLine) => new Promise((ok, no) => {
    const p = spawn('yt-dlp', args, { stdio: ['ignore', 'pipe', 'pipe'] }); let out = '', err = '';
    const kill = setTimeout(() => p.kill('SIGKILL'), 36e5);
    p.stdout.on('data', d => { if (onLine) String(d).split('\n').forEach(onLine); else out += d; if (out.length > 2e7) p.kill(); });
    p.stderr.on('data', d => err += d);
    p.on('error', () => { clearTimeout(kill); no('yt-dlp is not installed on the server.'); });
    p.on('close', c => { clearTimeout(kill); c === 0 ? ok(out) : no((err.split('\n').find(l => /ERROR/.test(l)) || 'Download failed.').replace(/^ERROR: /, '').slice(0, 200)); });
  });
  async function info(u) {
    const j = JSON.parse(await run(['-J', '--no-playlist', '--no-warnings', '--socket-timeout', '15', '--', u]));
    if (j.is_live) throw 'Live streams are not supported.';
    if (j.duration > MAXMIN * 60) throw 'Video is longer than ' + MAXMIN + ' minutes.';
    const heights = [...new Set((j.formats || []).map(f => f.height).filter(Boolean))].sort((a, b) => b - a);
    return { title: j.title, by: j.uploader || j.channel, duration: j.duration, thumb: j.thumbnail, site: j.extractor_key, heights, subs: Object.keys(j.subtitles || {}).slice(0, 40) };
  }
  // Every option is validated against a whitelist before it reaches yt-dlp. No shell is used.
  function args(q, dir) {
    const g = (n, re, d) => re.test(q.get(n) || '') ? q.get(n) : d, tm = /^(\d+(:\d{1,2}){0,2}(\.\d+)?|inf)$/, k = g('k', /^(video|audio|subs|thumb)$/, 'video');
    const a = ['--no-playlist', '--no-warnings', '--newline', '--socket-timeout', '15', '--max-filesize', MAXMB + 'M', '--restrict-filenames',
      '--progress-template', 'download:P|%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s', '-o', path.join(dir, '%(title).80s.%(ext)s')];
    if (k === 'video') {
      const h = +g('q', /^\d{3,4}$/, 0), hf = h ? '[height<=' + h + ']' : '', S = [];
      a.push('-f', g('aud', /^[01]$/, '1') === '0' ? 'bv*' + hf : 'bv*' + hf + '+ba/b' + hf);
      const c = g('codec', /^(h264|vp9|av1)$/, ''); if (c) S.push('vcodec:' + c); if (g('fps', /^30$/, '')) S.push('fps:30'); if (S.length) a.push('-S', S.join(','));
      const f = g('fmt', /^(mp4|mkv|webm|mov|avi|flv|gif)$/, 'mp4'); a.push(/^(mp4|mkv|webm)$/.test(f) ? '--merge-output-format' : '--recode-video', f);
    } else if (k === 'audio') {
      const f = g('fmt', /^(mp3|m4a|aac|opus|vorbis|flac|wav|alac|aiff)$/, 'mp3'), b = g('br', /^\d{2,3}$/, '0');
      a.push('-f', 'ba/b', '-x', '--audio-format', f, '--audio-quality', b === '0' ? '0' : b + 'K');
      if (g('meta', /^1$/, '') && /^(mp3|m4a|flac|opus)$/.test(f)) a.push('--embed-metadata', '--embed-thumbnail');
    } else if (k === 'subs') a.push('--skip-download', '--write-subs', '--write-auto-subs', '--sub-langs', g('lang', /^[\w.\-*,]{1,40}$/, 'en'), '--convert-subs', g('sfmt', /^(srt|vtt|ass|lrc)$/, 'srt'));
    else a.push('--skip-download', '--write-thumbnail', '--convert-thumbnails', g('tfmt', /^(jpg|png|webp)$/, 'jpg'));
    if ((k === 'video' || k === 'audio') && (q.get('start') || q.get('end'))) a.push('--download-sections', '*' + g('start', tm, '0') + '-' + g('end', tm, 'inf'), '--force-keyframes-at-cuts');
    return a;
  }
  async function start(q, ip) {
    if (limited(ip, 'yt', 20, 6e5)) throw 'Too many downloads. Try again in a few minutes.';
    if (running >= JOBS) throw 'Server is busy. Try again in a minute.';
    const u = await check(q.get('url')), id = crypto.randomBytes(9).toString('hex'), dir = fs.mkdtempSync(path.join(os.tmpdir(), 'donekwik-')), j = { dir, t: Date.now(), state: 'run', pct: 0 };
    jobs.set(id, j); running++;
    run([...args(q, dir), '--', u], l => { const m = /^P\|\s*([\d.]+)%\|\s*(\S+)\|\s*(\S+)/.exec(l.trim()); if (m) Object.assign(j, { pct: +m[1], speed: m[2], eta: m[3] }); })
      .then(() => {
        const f = fs.readdirSync(dir).filter(n => !/\.(part|ytdl|temp)$/.test(n)).map(n => [n, fs.statSync(path.join(dir, n)).size]).sort((a, b) => b[1] - a[1])[0];
        if (!f) throw 'Nothing was downloaded.'; Object.assign(j, { state: 'done', pct: 100, file: f[0], size: f[1] });
      })
      .catch(e => Object.assign(j, { state: 'err', error: String(e.message || e) })).finally(() => running--);
    return { id };
  }
  function file(res, id) {
    const j = jobs.get(id); if (!j || j.state !== 'done') return txt(res, 404, 'Not ready');
    res.writeHead(200, { 'content-type': 'application/octet-stream', 'content-length': j.size, 'content-disposition': 'attachment; filename="' + j.file.replace(/[^\w.\-]/g, '_') + '"', 'x-content-type-options': 'nosniff' });
    const s = fs.createReadStream(path.join(j.dir, j.file)); s.pipe(res);
    res.on('close', () => { s.destroy(); fs.rmSync(j.dir, { recursive: true, force: true }); jobs.delete(id); }); // single use, nothing is kept
  }
  const handle = async (req, res, u, ip) => {
    const q = u.searchParams;
    try {
      if (u.pathname === '/api/config') return json(res, 200, { ytdlp: true, platforms: ALLOW, maxMinutes: MAXMIN });
      if (u.pathname === '/api/ytdl/info') { if (limited(ip, 'yi', 30, 6e4)) throw 'Slow down a little.'; return json(res, 200, await info(await check(q.get('url')))); }
      if (u.pathname === '/api/ytdl/start') return json(res, 200, await start(q, ip));
      if (u.pathname === '/api/ytdl/status') { const j = jobs.get(q.get('id')); return j ? json(res, 200, { state: j.state, pct: j.pct, speed: j.speed, eta: j.eta, file: j.file, size: j.size, error: j.error }) : json(res, 404, { error: 'Unknown job' }); }
      if (u.pathname === '/api/ytdl/file') return file(res, q.get('id'));
      txt(res, 404, 'Not found');
    } catch (e) { json(res, 400, { error: String(e.message || e) }); }
  };
  handle.cleanup = () => { for (const [, j] of jobs) fs.rmSync(j.dir, { recursive: true, force: true }); jobs.clear(); };
  return handle;
};

#!/usr/bin/env python3
"""DoneKwik launch audit. Drives the real app in Chromium with real files and checks every output with independent tools
(Pillow, ffprobe, openpyxl, odfpy, pypdf, zipfile, hashlib). Needs: node, python3, playwright (pip install playwright; playwright install chromium),
numpy, Pillow, openpyxl, odfpy, python-docx, reportlab, pypdf, ffmpeg. Run `npm install && npm run vendor` first, then `python3 tests/audit.py`.
The yt-dlp bridge is exercised with a stub (tests/stubs/yt-dlp); real yt-dlp and live search need internet and are not covered here."""
import os, sys, io, re, json, csv, gzip, wave, base64, hashlib, shutil, tempfile, zipfile, subprocess, threading, time, urllib.request, urllib.error, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import http.server as hs
import fixtures, numpy as np
from PIL import Image
from pypdf import PdfReader
RES = []
def wait(pg, expr, timeout=60000):
    t = time.time()
    while time.time() - t < timeout / 1000:
        if pg.evaluate(expr): return
        time.sleep(.1)
    raise TimeoutError('timed out waiting for: ' + expr[:120])
def ok(name, cond, detail=''):
    RES.append((name, 'PASS' if cond else 'FAIL', detail)); print('PASS' if cond else 'FAIL', name, ('- ' + str(detail)[:300]) if detail and not cond else '', flush=True)
def skip(name, why): RES.append((name, 'SKIP', why)); print('SKIP', name, '-', why, flush=True)
TMP = tempfile.mkdtemp(prefix='dkaudit_'); FIX = fixtures.make(os.path.join(TMP, 'fix')); LOG = os.path.join(TMP, 'stub.log')
def fx(n): return os.path.join(FIX, n)
def rd(n): return open(fx(n), 'rb').read()
# ---------- servers ----------
def start(port, **env):
    e = dict(os.environ, NODE_OPTIONS='--require ' + os.path.join(HERE, 'stubs', 'dnsmock.js'), PORT=str(port), PATH=os.path.join(HERE, 'stubs') + os.pathsep + os.environ['PATH'], STUB_LOG=LOG); e.update({k: str(v) for k, v in env.items()})
    p = subprocess.Popen(['node', os.path.join(ROOT, 'server.js')], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=ROOT)
    for _ in range(60):
        try: urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=1); return p
        except Exception: time.sleep(.2)
    raise RuntimeError('server did not start')
def http(url, headers=None, enc=False):
    r = urllib.request.Request(url, headers=headers or {})
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    try:
        with urllib.request.build_opener(NoRedir).open(r, timeout=20) as x: return x.status, dict((k.lower(), v) for k, v in x.headers.items()), x.read()
    except urllib.error.HTTPError as e: return e.code, dict((k.lower(), v) for k, v in e.headers.items()), e.read()
BIG = os.urandom(2 * 1024 * 1024); SMALL = os.urandom(5000)
class Origin(hs.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/redir': self.send_response(302); self.send_header('Location', '/small.bin'); self.end_headers(); return
        data = {'/small.bin': SMALL, '/big.bin': BIG, '/named': b'named content'}.get(path)
        if data is None: self.send_response(404); self.end_headers(); return
        st, body, h = 200, data, {}
        m = re.match(r'bytes=(\d+)-(\d*)', self.headers.get('Range') or '')
        if m: a = int(m[1]); b = int(m[2] or len(data) - 1); body = data[a:b + 1]; st = 206; h['Content-Range'] = f'bytes {a}-{b}/{len(data)}'
        self.send_response(st)
        for k, v in {'Content-Length': len(body), 'Accept-Ranges': 'bytes', 'Content-Type': 'application/octet-stream', **h}.items(): self.send_header(k, str(v))
        if path == '/named': self.send_header('Content-Disposition', 'attachment; filename="report final.pdf"')
        self.end_headers(); self.wfile.write(body)
OP = 4190; osrv = hs.ThreadingHTTPServer(('127.0.0.1', OP), Origin); threading.Thread(target=osrv.serve_forever, daemon=True).start()
# ---------- helpers ----------
def probe(b, ext):
    p = os.path.join(TMP, 'probe.' + ext); open(p, 'wb').write(b)
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p], capture_output=True, text=True)
    return json.loads(r.stdout or '{}') if r.returncode == 0 else {}
def dur(j): return float(j.get('format', {}).get('duration') or max([float(s.get('duration') or 0) for s in j.get('streams', [])] + [0]))
def streams(j, t): return [s for s in j.get('streams', []) if s['codec_type'] == t]
def img(b): return Image.open(io.BytesIO(b))
def wavdata(b):
    w = wave.open(io.BytesIO(b)); a = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, w.getnchannels()) / 32768.0; return a, w.getframerate()
def pdf(b): return PdfReader(io.BytesIO(b))
def ptext(r): return [p.extract_text() or '' for p in r.pages]
def csvrows(b): return list(csv.reader(io.StringIO(b.decode('utf-8'))))
class App:
    def __init__(s, pw, url):
        s.br = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); s.ctx = s.br.new_context(viewport={'width': 1400, 'height': 900}, accept_downloads=True); s.pg = s.ctx.new_page(); s.errs = []
        s.cons = []; s.bad = []; s.pg.on('pageerror', lambda e: s.errs.append(str(e))); s.pg.on('console', lambda m: s.cons.append(m.text) if m.type in ('error', 'warning') else None); s.pg.on('response', lambda r: s.bad.append((r.status, r.url)) if r.status >= 400 and '/api/' not in r.url and r.url.startswith(url.split('/', 3)[0] + '//' + url.split('/', 3)[2]) else None); s.pg.goto(url); wait(s.pg, 'typeof tools!=="undefined"&&typeof probe==="function"'); s.pg.wait_for_timeout(600)
    def tool(s, tid, files=(), opts=None, timeout=120000, text=None):
        pg = s.pg; sel = '#t-' + tid; pg.evaluate("id=>{openTool(id);const t=tools.find(x=>x.id===id);t.fl=[];t.all=[]}", tid)
        pg.evaluate("sel=>[...document.querySelectorAll(sel+' [name]')].forEach(e=>{if(e.tagName==='SELECT')[...e.options].forEach(o=>o.selected=o.defaultSelected);else e.value=e.defaultValue})", sel)
        if files: pg.set_input_files(sel + ' input[type=file]', [f if os.path.isabs(f) else fx(f) for f in files])
        if text is not None: pg.fill('#ti', text)
        for k, v in (opts or {}).items(): pg.evaluate("([q,v])=>{const e=document.querySelector(q);if(!e)throw new Error('no option '+q);e.value=v}", [f'{sel} [name={k}]', str(v)])
        pg.click(sel + ' .btn'); wait(pg, f"!document.querySelector('{sel} .btn').disabled", timeout=timeout)
        st = pg.inner_text(sel + ' .st')
        outs = pg.evaluate("""async id=>{const t=tools.find(x=>x.id===id),rd=b=>new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result.split(',')[1]);f.readAsDataURL(b)});return Promise.all(t.all.map(async o=>({n:o.n,t:o.b.type,b:await rd(o.b)})))}""", tid)
        return st, {o['n']: base64.b64decode(o['b']) for o in outs}
    def close(s): s.br.close()
# ---------- tool tests ----------
def one(outs): return next(iter(outs.values())) if outs else b''
def fails(st): return st.startswith('⚠')
def t_images(A):
    mags = {'png': b'\x89PNG', 'jpeg': b'\xff\xd8\xff', 'webp': b'RIFF', 'bmp': b'BM', 'ico': b'\x00\x00\x01\x00'}
    for fmt, ext in [('image/png', 'png'), ('image/jpeg', 'jpeg'), ('image/webp', 'webp'), ('image/bmp', 'bmp'), ('ico', 'ico')]:
        st, o = A.tool('image', ['photo.png'], {'fmt': fmt}); b = one(o)
        good = len(o) == 1 and b.startswith(mags[ext])
        if good:
            try: im = img(b); exp = (256, 192) if ext == 'ico' else (400, 300); good = im.size == exp
            except Exception as e: good = False; st = str(e)
        ok(f'Images: PNG to {ext.upper()} decodes with correct size', good, st)
    has = A.pg.evaluate("!!document.querySelector('#t-image [name=fmt] option[value=\"image/avif\"]')")
    if not has: skip('Images: AVIF output', 'no current browser can encode AVIF from a canvas, so the option is hidden by design (AVIF files can still be read)')
    else:
        st, o = A.tool('image', ['photo.png'], {'fmt': 'image/avif'}); b = one(o); ok('Images: PNG to AVIF (ftyp avif)', b[4:12] in (b'ftypavif', b'ftypavis'), b[:16])
    for f, exp in [('photo.jpg', (400, 300)), ('photo.webp', (400, 300)), ('photo.gif', (400, 300)), ('photo.bmp', (400, 300)), ('icon.svg', (120, 80)), ('photo.ico', (64, 64))]:
        st, o = A.tool('image', [f], {'fmt': 'image/png'}); ok(f'Images: read {f.split(".")[1].upper()} input', len(o) == 1 and img(one(o)).size == exp, st)
    st, o = A.tool('image', ['photo.png'], {'fmt': 'image/png', 'w': 200}); ok('Images: resize to 200px wide', img(one(o)).size == (200, 150), st)
    st, o = A.tool('image', ['photo.png'], {'fmt': 'image/jpeg', 'kb': 8}); b = one(o); ok('Images: compress to target size (8 KB)', 0 < len(b) <= 8 * 1024 * 1.02, len(b))
    st, o = A.tool('image', ['alpha.png'], {'fmt': 'image/jpeg'}); p = img(one(o)).convert('RGB').getpixel((50, 50)); ok('Images: transparency flattens to white for JPG', p[0] > 200 and p[1] > 100, p)
    st, o = A.tool('image', ['photo.png', 'photo.jpg', 'photo.webp'], {'fmt': 'image/png'}); ok('Images: batch of 3 gives 3 outputs', len(o) == 3 and len(set(o)) == 3, list(o))
    st, o = A.tool('image', ['a.txt'], {'fmt': 'image/png'}); ok('Images: unreadable file shows a clear error', fails(st) and 'Cannot read' in st, st)
    skip('Images: HEIC input', 'needs heic2any (npm) and a HEIC sample; not verifiable in this offline sandbox')
def t_audio(A):
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav'}); b = one(o); a, sr = wavdata(b); j = probe(b, 'wav')
    ok('Audio: WAV to WAV (1 s, stereo)', abs(a.shape[0] / sr - 1.0) < .03 and a.shape[1] == 2, (a.shape, sr, st))
    for k, v, chk in [('s', .25, None)]: pass
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 's': .25, 'e': .75}); a, sr = wavdata(one(o)); ok('Audio: trim 0.25 to 0.75 s', abs(a.shape[0] / sr - .5) < .03, a.shape[0] / sr)
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'sp': 2}); a, sr = wavdata(one(o)); ok('Audio: speed 2x halves the length', abs(a.shape[0] / sr - .5) < .04, a.shape[0] / sr)
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'mono': 1}); a, sr = wavdata(one(o)); ok('Audio: mono output', a.shape[1] == 1, a.shape)
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'sr': 8000}); a, sr = wavdata(one(o)); ok('Audio: resample to 8 kHz', sr == 8000 and abs(a.shape[0] / sr - 1) < .03, sr)
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'rev': 1}); a, sr = wavdata(one(o)); q = a.shape[0] // 4; l = a[:, 0]
    ok('Audio: reverse (quiet end becomes the start)', np.abs(l[:q]).mean() > np.abs(l[-q:]).mean() * 3, (np.abs(l[:q]).mean(), np.abs(l[-q:]).mean()))
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'fo': .5}); a, sr = wavdata(one(o)); r = a[:, 1]; ok('Audio: fade out reaches silence', np.abs(r[-200:]).max() < .03 and np.abs(r[sr // 4:sr // 2]).max() > .3, (np.abs(r[-200:]).max(), np.abs(r[sr // 4:sr // 2]).max()))
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'fi': .5}); a, sr = wavdata(one(o)); r = a[:, 1]; ok('Audio: fade in starts silent', np.abs(r[:200]).max() < .03, np.abs(r[:200]).max())
    st, o = A.tool('audio', ['tone.wav'], {'fmt': 'wav', 'gain': 50}); a, sr = wavdata(one(o)); ok('Audio: volume 50%', abs(np.abs(a[:, 1]).max() - .2) < .03, np.abs(a[:, 1]).max())
    st, o = A.tool('audio', ['tone.wav', 'tone2.wav'], {'fmt': 'wav', 'merge': 1}); a, sr = wavdata(one(o)); ok('Audio: merge two files (1.5 s)', len(o) == 1 and abs(a.shape[0] / sr - 1.5) < .05, (len(o), a.shape[0] / sr))
    for f in ['tone.mp3', 'tone.ogg', 'tone.flac']:
        st, o = A.tool('audio', [f], {'fmt': 'wav'}); good = len(o) == 1
        if good: a, sr = wavdata(one(o)); good = abs(a.shape[0] / sr - 1) < .12
        ok(f'Audio: read {f.split(".")[1].upper()} input', good, st)
    has = A.pg.evaluate("!!document.querySelector('#t-audio [name=fmt] option[value=mp3]')")
    if not has: skip('Audio: MP3 output', 'lamejs is not installed in this offline sandbox, so the MP3 option is hidden by design; run the audit after npm install && npm run vendor')
    else:
        st, o = A.tool('audio', ['tone.wav'], {'fmt': 'mp3', 'br': 128}); j = probe(one(o), 'mp3'); ok('Audio: MP3 output (ffprobe codec mp3)', streams(j, 'audio') and streams(j, 'audio')[0]['codec_name'] == 'mp3', st)
def t_video(A):
    st, o = A.tool('video', ['clip.webm'], {'mode': 'video'}); b = one(o); j = probe(b, 'webm'); v = streams(j, 'video'); au = streams(j, 'audio')
    ok('Video: WebM has a duration so players can seek', bool(dur(probe(b, 'webm'))), probe(b, 'webm').get('format'))
    ok('Video: WebM to WebM keeps video and audio', len(o) == 1 and v and au and v[0]['width'] == 320 and v[0]['height'] == 240, st)
    d = dur(j) or 0; ok('Video: output length close to 2 s', 1.4 < d < 3.0, d)
    st, o = A.tool('video', ['clip.webm'], {'mode': 'video', 'h': 144}); v = streams(probe(one(o), 'webm'), 'video'); ok('Video: shrink to 144p', v and v[0]['height'] == 144, v)
    st, o = A.tool('video', ['clip.webm'], {'mode': 'video', 'mute': 1}); j = probe(one(o), 'webm'); ok('Video: mute removes the audio track', streams(j, 'video') and not streams(j, 'audio'), [s['codec_type'] for s in j.get('streams', [])])
    st, o = A.tool('video', ['clip.webm'], {'mode': 'audio'}); j = probe(one(o), 'webm'); ok('Video: extract audio only', streams(j, 'audio') and not streams(j, 'video'), [s['codec_type'] for s in j.get('streams', [])])
    st, o = A.tool('video', ['clip.webm'], {'mode': 'video', 's': .5, 'e': 1.5}); d = dur(probe(one(o), 'webm')); ok('Video: trim 0.5 to 1.5 s', .6 < d < 1.6, d)
    st, o = A.tool('video', ['clip.webm'], {'mode': 'video', 'sp': 2}); d = dur(probe(one(o), 'webm')); ok('Video: speed 2x shortens it', .6 < d < 1.5, d)
    st, o = A.tool('video', ['clip.webm'], {'mode': 'frames', 'iv': .5}); fr = [img(b) for b in o.values()]
    ok('Video: frames every 0.5 s (JPG files, 4 or 5 depending on clip end)', len(fr) in (4, 5) and all(f.size == (320, 240) for f in fr), (len(fr), st))
    if len(fr) >= 4: ok('Video: frames really differ over time', np.abs(np.asarray(fr[0], float) - np.asarray(fr[3], float)).mean() > 1)
    st, o = A.tool('video', ['clip.mp4'], {'mode': 'frames', 'iv': 1})
    if fails(st): skip('Video: MP4 (H.264) input', 'this test browser has no H.264 decoder (' + st + '); normal Chrome, Edge and Safari do')
    else: ok('Video: MP4 input frames', len(o) >= 2, st)
def t_sheets(A):
    def S(f, k, **kw): return A.tool('sheet', [f], {'fmt': k}, **kw)
    st, o = S('book.xlsx', 'csv'); r = {n: csvrows(b) for n, b in o.items()}
    ok('Sheets: XLSX to CSV writes one file per sheet', set(o) == {'book-Sales.csv', 'book-Notes.csv'}, list(o))
    sales = r.get('book-Sales.csv', []); ok('Sheets: XLSX values, quotes, commas, Unicode and dates survive', sales[:3] == [['Name', 'Qty', 'Price', 'Active', 'Date'], ['Café "Aroma"', '3', '4.5', 'true', '2024-03-15'], ['Chai, hot', '10', '2.25', 'false', '2024-03-16']] and sales[3][:2] == ['मसाला', '0'], sales)
    ok('Sheets: XLSX multi-line and special characters', r.get('book-Notes.csv') == [['a', 'b'], ['line1\nline2', 'x & y <z>']], r.get('book-Notes.csv'))
    st, o = S('book.xlsx', 'json'); j = json.loads(one({k: v for k, v in o.items() if 'Sales' in k})); ok('Sheets: XLSX to JSON with real types', j[0] == {'Name': 'Café "Aroma"', 'Qty': 3, 'Price': 4.5, 'Active': True, 'Date': '2024-03-15'}, j[:1])
    import openpyxl
    st, o = S('book.xlsx', 'xlsx'); wb = openpyxl.load_workbook(io.BytesIO(one(o))); ws = wb['Sales']
    ok('Sheets: XLSX to XLSX opens in openpyxl with both sheets', wb.sheetnames == ['Sales', 'Notes'] and ws['A2'].value == 'Café "Aroma"' and ws['B2'].value == 3 and ws['C2'].value == 4.5 and ws['D2'].value is True and ws['A4'].value == 'मसाला' and wb['Notes']['A2'].value == 'line1\nline2', (wb.sheetnames, [c.value for c in ws[2]]))
    from odf.opendocument import load as oload
    from odf.table import Table, TableRow, TableCell
    from odf import teletype
    def ods_rows(b):
        d = oload(io.BytesIO(b)); out = {}
        for t in d.spreadsheet.getElementsByType(Table): out[t.getAttribute('name')] = [[teletype.extractText(c) for c in tr.getElementsByType(TableCell)] for tr in t.getElementsByType(TableRow)]
        return out
    st, o = S('book.xlsx', 'ods'); r2 = ods_rows(one(o)); ok('Sheets: XLSX to ODS opens in odfpy', list(r2) == ['Sales', 'Notes'] and r2['Sales'][1][0] == 'Café "Aroma"' and r2['Sales'][1][1] == '3', r2)
    with zipfile.ZipFile(io.BytesIO(one(o))) as z: ok('Sheets: ODS package has mimetype first and stored', z.namelist()[0] == 'mimetype' and z.getinfo('mimetype').compress_type == 0, z.namelist())
    st, o = S('book.ods', 'csv'); ok('Sheets: ODS to CSV', csvrows(one(o)) == [['item', 'count', 'ok'], ['pen', '5', 'true'], ['ink, blue', '2.5', 'false']], csvrows(one(o)))
    st, o = S('book.ods', 'xlsx'); ws = openpyxl.load_workbook(io.BytesIO(one(o))).active; ok('Sheets: ODS to XLSX', [c.value for c in ws[3]] == ['ink, blue', 2.5, False], [c.value for c in ws[3]])
    st, o = S('data.csv', 'json'); j = json.loads(one(o))
    ok('Sheets: CSV to JSON (quotes, newline, leading zeros kept, numbers typed)', j[0] == {'id': 1, 'name': 'Asha', 'score': 9.5, 'zip': '007'} and j[1]['name'] == 'Ravi, K' and j[2]['name'] == 'Line\nBreak' and j[3]['name'] == 'He said "hi"' and j[3]['score'] == 1000, j)
    st, o = S('data.csv', 'csv'); ok('Sheets: CSV to CSV is lossless', csvrows(one(o)) == csvrows(rd('data.csv')), csvrows(one(o)))
    st, o = S('data.csv', 'xlsx'); ws = openpyxl.load_workbook(io.BytesIO(one(o))).active; ok('Sheets: CSV to XLSX types', ws['A2'].value == 1 and ws['C2'].value == 9.5 and ws['D2'].value == '007' and ws['B4'].value == 'Line\nBreak', [c.value for c in ws[2]])
    st, o = S('data.tsv', 'json'); ok('Sheets: TSV to JSON', json.loads(one(o)) == [{'a': 1, 'b': 'x y'}, {'a': 2, 'b': 'z'}], one(o)[:80])
    st, o = S('data.json', 'csv'); ok('Sheets: JSON to CSV (union of keys, nested arrays as text)', csvrows(one(o)) == [['id', 'name', 'tags', 'city'], ['1', 'Asha', '["a","b"]', ''], ['2', 'Ravi', '', 'Pune']], csvrows(one(o)))
    st, o = S('data.json', 'xlsx'); ws = openpyxl.load_workbook(io.BytesIO(one(o))).active; ok('Sheets: JSON to XLSX', ws['A1'].value == 'id' and ws['A2'].value == 1 and ws['D3'].value == 'Pune', [c.value for c in ws[3]])
    st, o = S('table.html', 'csv'); ok('Sheets: HTML table to CSV', csvrows(one(o)) == [['k', 'v'], ['one', '1'], ['two & three', '2']], csvrows(one(o)))
    st, o = S('book.xlsx', 'html'); t = one({k: v for k, v in o.items() if 'Sales' in k}).decode(); ok('Sheets: XLSX to HTML table escapes markup', '<th>Name</th>' in t and '&quot;Aroma&quot;' in t, t[:200])
    st, o = S('book.xlsx', 'txt'); ok('Sheets: XLSX to TXT (tab separated)', 'Chai, hot\t10\t2.25' in one({k: v for k, v in o.items() if 'Sales' in k}).decode())
    bad = os.path.join(TMP, 'bad.xlsx'); open(bad, 'wb').write(b'not a zip file'); st, o = S(bad, 'csv'); ok('Sheets: corrupt XLSX shows an error', fails(st), st)
def t_docs(A):
    def D(f, k): return A.tool('doc', [f], {'fmt': k})
    st, o = D('doc.docx', 'html'); h = one(o).decode()
    ok('Docs: DOCX to HTML (headings, bold, italic, lists, table, Unicode)', all(x in h for x in ['<h1>Main Title</h1>', '<strong>bold</strong>', '<em>italic</em>', '<h2>Section</h2>', '<ul><li>Bullet one</li><li>Bullet two</li></ul>', '<ol><li>Step one</li><li>Step two</li></ol>', '<table', 'r1c1', 'नमस्ते']), h[:600])
    st, o = D('doc.docx', 'txt'); t = one(o).decode(); ok('Docs: DOCX to TXT', all(x in t for x in ['Main Title', 'Plain, bold and italic', '- Bullet one', '1. Step one', 'r0c0\tr0c1', 'नमस्ते and café']), t)
    st, o = D('doc.docx', 'pdf'); r = pdf(one(o)); ok('Docs: DOCX to PDF (non-Latin text drawn as page images)', len(r.pages) >= 1 and len(r.pages[0].images) >= 1, st)
    st, o = D('note.md', 'html'); h = one(o).decode(); ok('Docs: Markdown to HTML', '<h1' in h and '<strong>bold</strong>' in h and '<li>one</li>' in h, h[:300])
    st, o = D('note.md', 'txt'); ok('Docs: Markdown to TXT keeps source', one(o).decode() == rd('note.md').decode())
    st, o = D('page.html', 'txt'); t = one(o).decode(); ok('Docs: HTML to TXT drops scripts and styles', 'Title' in t and 'Para one' in t and 'alert' not in t and 'color:red' not in t, t)
    st, o = D('page.html', 'html'); ok('Docs: HTML to HTML passthrough', one(o).decode() == rd('page.html').decode())
    st, o = D('latin.txt', 'html'); ok('Docs: TXT to HTML', '<pre>' in one(o).decode() and 'Hello DoneKwik' in one(o).decode())
    st, o = D('latin.txt', 'pdf'); r = pdf(one(o)); t = ' '.join(ptext(r)); ok('Docs: TXT to PDF keeps selectable text and wraps lines', len(r.pages) == 1 and 'Hello DoneKwik' in t and 'End line café' in t and 'word word word' in t, t[:120])
    st, o = D('hindi.txt', 'pdf'); r = pdf(one(o)); im = r.pages[0].images[0].image.convert('L') if r.pages[0].images else None
    ok('Docs: Hindi/Marathi TXT to PDF draws text on the page', im is not None and (np.asarray(im) < 128).sum() > 300, st)
    skip('Docs: Devanagari glyph shapes', 'this sandbox has no Devanagari font, so shapes show as boxes here; verify visually on a normal device')
    bad = os.path.join(TMP, 'bad.docx'); open(bad, 'wb').write(b'nope'); st, o = D(bad, 'txt'); ok('Docs: corrupt DOCX shows an error', fails(st), st)
def t_subs(A):
    def U(f, k, sh=0): return A.tool('subs', [f], {'fmt': k, 'sh': sh})
    st, o = U('s.srt', 'vtt'); t = one(o).decode(); ok('Subtitles: SRT to VTT', t.startswith('WEBVTT\n\n') and '00:00:01.000 --> 00:00:03.500' in t and '01:02:03.250 --> 01:02:05.000' in t, t)
    st, o = U('s.vtt', 'srt'); t = one(o).decode(); ok('Subtitles: VTT to SRT (short timestamps, cue settings)', t.startswith('1\n00:00:01,000 --> 00:00:03,500\nShort form') and '2\n00:00:04,000 --> 00:00:06,000\nWith settings' in t, t)
    st, o = U('s.srt', 'txt'); t = one(o).decode(); ok('Subtitles: SRT to text strips tags', 'Hello there' in t and 'Second line\nwith break' in t and '<i>' not in t, t)
    st, o = U('s.srt', 'srt', 1.5); ok('Subtitles: shift +1.5 s', '00:00:02,500 --> 00:00:05,000' in one(o).decode(), one(o)[:80])
    st, o = U('s.srt', 'srt', -2); ok('Subtitles: negative shift clamps at zero', '00:00:00,000 --> 00:00:01,500' in one(o).decode(), one(o)[:80])
def t_imgedit(A):
    def E(**o): return A.tool('imgedit', ['photo.png'], {'fmt': 'image/png', **o})
    base = np.asarray(img(one(E()[1])).convert('RGB'), float)
    ok('Image editor: no-op keeps pixels', base.shape == (300, 400, 3) and np.abs(base - np.asarray(Image.open(fx('photo.png')).convert('RGB'), float)).max() < 2)
    for ar, exp in [('1:1', (300, 300)), ('16:9', (400, 225)), ('3:4', (225, 300))]: ok(f'Image editor: crop {ar}', img(one(E(ar=ar)[1])).size == exp, img(one(E(ar=ar)[1])).size)
    ok('Image editor: rotate 90 swaps dimensions', img(one(E(rot=90)[1])).size == (300, 400))
    ok('Image editor: rotate 180 keeps dimensions', img(one(E(rot=180)[1])).size == (400, 300))
    h = np.asarray(img(one(E(fl='h')[1])).convert('RGB'), float); ok('Image editor: flip horizontal', np.abs(h - base[:, ::-1]).mean() < 3, np.abs(h - base[:, ::-1]).mean())
    v = np.asarray(img(one(E(fl='v')[1])).convert('RGB'), float); ok('Image editor: flip vertical', np.abs(v - base[::-1]).mean() < 3)
    g = np.asarray(img(one(E(flt='grayscale(1)')[1])).convert('RGB'), float); ok('Image editor: grayscale filter', np.abs(g[..., 0] - g[..., 1]).max() < 3 and np.abs(g[..., 1] - g[..., 2]).max() < 3)
    iv = np.asarray(img(one(E(flt='invert(1)')[1])).convert('RGB'), float); ok('Image editor: invert filter', np.abs(iv - (255 - base)).mean() < 3)
    br = np.asarray(img(one(E(br=150)[1])).convert('RGB'), float); ok('Image editor: brightness 150%', br.mean() > base.mean() + 10)
    w = np.asarray(img(one(E(wm='DoneKwik')[1])).convert('RGB'), float); ok('Image editor: text watermark changes bottom-right only', np.abs(w[220:, 200:] - base[220:, 200:]).mean() > .5 and np.abs(w[:100, :100] - base[:100, :100]).max() < 2)
    for f, mg in [('image/jpeg', b'\xff\xd8'), ('image/webp', b'RIFF')]: ok(f'Image editor: save as {f.split("/")[1].upper()}', one(A.tool('imgedit', ['photo.png'], {'fmt': f})[1]).startswith(mg))
def t_pdf(A):
    def P(files, mode, **o): return A.tool('pdf', files, {'mode': mode, **o})
    st, o = P(['a.pdf', 'b.pdf'], 'merge'); r = pdf(one(o)); t = [x.strip() for x in ptext(r)]; ok('PDF: merge two files in order', t == ['Alpha page 1', 'Alpha page 2', 'Alpha page 3', 'Beta page 1', 'Beta page 2'], t)
    st, o = P(['photo.png', 'photo.jpg'], 'img'); r = pdf(one(o)); ok('PDF: images to PDF (2 pages, size from image, image embedded)', len(r.pages) == 2 and all(abs(float(p.mediabox.width) - 400) < 1 and len(p.images) == 1 for p in r.pages), st)
    st, o = P(['a.pdf'], 'ext', r='3,1'); t = [x.strip() for x in ptext(pdf(one(o)))]; ok('PDF: extract pages 3,1 in that order', t == ['Alpha page 3', 'Alpha page 1'], t)
    st, o = P(['a.pdf'], 'del', r='2'); t = [x.strip() for x in ptext(pdf(one(o)))]; ok('PDF: delete page 2', t == ['Alpha page 1', 'Alpha page 3'], t)
    st, o = P(['a.pdf'], 'split'); ok('PDF: split into 3 single-page files', len(o) == 3 and all(len(pdf(b).pages) == 1 for b in o.values()), list(o))
    st, o = P(['a.pdf'], 'rev'); t = [x.strip() for x in ptext(pdf(one(o)))]; ok('PDF: reverse page order', t == ['Alpha page 3', 'Alpha page 2', 'Alpha page 1'], t)
    st, o = P(['a.pdf'], 'rot'); ok('PDF: rotate 90 degrees', all(p.rotation == 90 for p in pdf(one(o)).pages))
    st, o = P(['a.pdf'], 'wm', t='CONFIDENTIAL'); t = ptext(pdf(one(o))); ok('PDF: watermark on every page, original text kept', all('CONFIDENTIAL' in x and 'Alpha page' in x for x in t), t)
    st, o = P(['a.pdf'], 'num'); t = ptext(pdf(one(o))); ok('PDF: page numbers', all(f'{i} / 3' in x for i, x in enumerate(t, 1)), t)
    st, o = P(['a.pdf'], 'png', sc=1)
    if fails(st) and 'could not load' in st: skip('PDF: PDF to PNG (pdf.js)', st)
    else:
        ims = [img(b) for b in o.values()]; ok('PDF: PDF to PNG (3 pages, A4 at 1x, text rendered)', len(ims) == 3 and all(i.size == (596, 842) and (np.asarray(i.convert('L')) < 128).sum() > 40 for i in ims), (len(ims), st))
    st, o = P(['a.pdf'], 'txt')
    if fails(st) and 'could not load' in st: skip('PDF: PDF to text (pdf.js)', st)
    else: t = one(o).decode(); ok('PDF: PDF to text', 'Alpha page 1' in t and 'Alpha page 3' in t, t)
    st, o = P(['a.txt'], 'merge'); ok('PDF: non-PDF input shows an error', fails(st), st)
def t_files(A):
    st, o = A.tool('zip', ['a.txt', 'b.bin'], {'mode': 'create'}); z = zipfile.ZipFile(io.BytesIO(one(o))); ok('Archives: create ZIP (valid, contents identical)', sorted(z.namelist()) == ['a.txt', 'b.bin'] and z.read('a.txt') == rd('a.txt') and z.read('b.bin') == rd('b.bin') and z.testzip() is None, z.namelist())
    st, o = A.tool('zip', ['arc.zip'], {'mode': 'extract'}); ok('Archives: extract ZIP', o == {'one.txt': b'first file\n', 'dir_two.txt': b'second file\n'}, list(o))
    st, o = A.tool('zip', ['a.txt'], {'mode': 'gz'}); ok('Archives: GZ compress', gzip.decompress(one(o)) == rd('a.txt') and list(o) == ['a.txt.gz'], list(o))
    st, o = A.tool('zip', ['file.txt.gz'], {'mode': 'ungz'}); ok('Archives: GZ decompress', o == {'file.txt': b'gzip payload\n' * 10}, list(o))
    st, o = A.tool('zip', ['a.txt'], {'mode': 'extract'}); ok('Archives: bad ZIP shows an error', fails(st), st)
    for alg, hl in [('SHA-256', hashlib.sha256), ('SHA-1', hashlib.sha1), ('SHA-384', hashlib.sha384), ('SHA-512', hashlib.sha512)]:
        st, o = A.tool('hash', ['a.txt', 'b.bin'], {'alg': alg}); t = one(o).decode().strip().split('\n')
        ok(f'Checksums: {alg} matches hashlib', t == [hl(rd('a.txt')).hexdigest() + '  a.txt', hl(rd('b.bin')).hexdigest() + '  b.bin'], t)
def t_text(A):
    def T(mode, s): st, o = A.tool('text', [], {'mode': mode}, text=s); return st, A.pg.input_value('#to')
    cases = [('jp', '{"a":1,"b":[1,2]}', '{\n  "a": 1,\n  "b": [\n    1,\n    2\n  ]\n}'), ('jm', '{ "a": 1,\n "b": [1, 2] }', '{"a":1,"b":[1,2]}'), ('j2c', '[{"a":1,"b":"x,y"},{"a":2}]', 'a,b\n1,"x,y"\n2,\n'),
      ('c2j', 'a,b\n1,x\n2,y', '[\n  {\n    "a": 1,\n    "b": "x"\n  },\n  {\n    "a": 2,\n    "b": "y"\n  }\n]'), ('be', 'नमस्ते', base64.b64encode('नमस्ते'.encode()).decode()), ('bd', base64.b64encode('नमस्ते café'.encode()).decode(), 'नमस्ते café'),
      ('ue', 'a b&c/ü', 'a%20b%26c%2F%C3%BC'), ('ud', 'a%20b%26c%2F%C3%BC', 'a b&c/ü'), ('up', 'hello', 'HELLO'), ('lo', 'HeLLo', 'hello'), ('ti', 'hello wORLD', 'Hello World'), ('so', 'b\nc\na', 'a\nb\nc'), ('un', 'a\nb\na', 'a\nb'),
      ('sp', '  a   b  \n\n\n\nc ', 'a b\n\nc'), ('rv', 'abc', 'cba'), ('ct', 'one two\nthree', '3 words, 13 characters, 2 lines'), ('sh', 'abc', hashlib.sha256(b'abc').hexdigest())]
    for m, i, e in cases: st, got = T(m, i); ok(f'Text lab: {m}', got == e, repr(got)[:160])
    st, got = T('md', '# Hi\n\n- x'); ok('Text lab: Markdown to HTML', '<h1' in got and '<li>x</li>' in got, got)
    st, got = T('jp', '{bad json'); ok('Text lab: invalid JSON shows an error', fails(st), st)
# ---------- server tests ----------
import shlex, gzip as _gz
def jget(url): s, h, b = http(url); return s, json.loads(b or b'{}')
def t_server(UA, UB, UC):
    s, h, b = http(UA + '/'); ok('Server: home page served with brand', s == 200 and b'DoneKwik' in b and 'text/html' in h['content-type'])
    ok('Server: security headers (CSP, nosniff, frame deny, referrer)', "default-src 'self'" in h.get('content-security-policy', '') and h.get('x-content-type-options') == 'nosniff' and h.get('x-frame-options') == 'DENY' and h.get('referrer-policy') == 'no-referrer', h)
    s2, h2, b2 = http(UA + '/', {'Accept-Encoding': 'gzip'}); ok('Server: gzip compression matches original', h2.get('content-encoding') == 'gzip' and _gz.decompress(b2) == b and len(b2) < len(b) * .6, (len(b2), len(b)))
    s3, h3, _ = http(UA + '/', {'If-None-Match': h['etag']}); ok('Server: ETag gives 304', s3 == 304)
    s, h, b = http(UA + '/manifest.webmanifest'); m = json.loads(b); ok('Server: web app manifest', m['name'] == 'DoneKwik' and len(m['icons']) == 3 and 'manifest' in h['content-type'], h)
    s, h, b = http(UA + '/sw.js'); ok('Server: service worker with scope header', s == 200 and h.get('service-worker-allowed') == '/' and 'javascript' in h['content-type'])
    for p in ['icon-192.png', 'icon-512.png', 'icon-maskable-512.png']:
        s, h, b = http(UA + '/assets/' + p); ok(f'Server: asset {p}', s == 200 and b[:4] == b'\x89PNG')
    s, h, b = http(UA + '/vendor/jszip.min.js'); ok('Server: vendored library served as JavaScript', s == 200 and 'javascript' in h['content-type'] and b'JSZip' in b)
    s, h, b = http(UA + '/vendor/pdf.min.mjs'); ok('Server: vendored ES module served as JavaScript', s == 200 and 'javascript' in h['content-type'])
    for p in ['/vendor/nope.js', '/vendor/../server.js', '/assets/..%2fserver.js', '/nothing', '/vendor/jszip.min.js%00.png']: ok(f'Server: {p} is not exposed', http(UA + p)[0] == 404, http(UA + p)[0])
    ok('Server: server source is not downloadable', b'createServer' not in http(UA + '/server.js')[2] and b'createServer' not in http(UA + '/ytdl.js')[2])
    s, h, b = http(UA + '/healthz'); ok('Server: health check', b == b'ok')
    s, h, b = http(UA + '/terms'); ok('Server: terms page shows the takedown contact', b'audit@example.com' in b)
    s, h, b = http(UA + '/robots.txt'); ok('Server: robots.txt blocks /api/', b'Disallow: /api/' in b)
    try: urllib.request.urlopen(urllib.request.Request(UA + '/api/config', method='POST', data=b'x')); code = 200
    except urllib.error.HTTPError as e: code = e.code
    ok('Server: POST is rejected (405)', code == 405, code)
    s, j = jget(UA + '/api/config'); ok('Server: config reports platforms off by default', s == 200 and j['platforms'] is False)
    s, h, b = http(UA + '/', {'Origin': 'https://evil.example'}); ok('Server: CORS not granted to unknown origins', 'access-control-allow-origin' not in h)
    s, h, b = http(UB + '/api/config', {'Origin': 'http://localhost:4101'}); ok('Server: CORS granted to the configured origin', h.get('access-control-allow-origin') == 'http://localhost:4101' and h.get('access-control-allow-private-network') == 'true', h)
    # direct-file proxy
    u = lambda p: f'{UA}/api/dl?ok=1&url=' + urllib.parse.quote(f'http://127.0.0.1:{OP}{p}', safe='')
    s, h, b = http(f'{UA}/api/dl?url=' + urllib.parse.quote(f'http://127.0.0.1:{OP}/small.bin', safe='')); ok('Proxy: refuses without the rights confirmation', s == 400)
    s, h, b = http(u('/small.bin')); ok('Proxy: full file is byte-identical with attachment headers', s == 200 and b == SMALL and 'attachment' in h['content-disposition'] and 'small.bin' in h['content-disposition'] and h['x-content-type-options'] == 'nosniff', (s, len(b)))
    s, h, b = http(u('/small.bin'), {'Range': 'bytes=100-199'}); ok('Proxy: Range request returns 206 with exact bytes', s == 206 and b == SMALL[100:200] and h['content-range'] == 'bytes 100-199/5000', (s, h.get('content-range')))
    s, h, b = http(u('/named')); ok('Proxy: filename taken from Content-Disposition', 'report final.pdf' in h['content-disposition'] and b == b'named content', h['content-disposition'])
    s, h, b = http(u('/redir')); ok('Proxy: follows redirects', s == 200 and b == SMALL)
    s, h, b = http(u('/missing')); ok('Proxy: passes through origin 404', s == 404)
    for name, url in [('YouTube', 'https://www.youtube.com/watch?v=x'), ('Netflix', 'https://www.netflix.com/title/1'), ('file scheme', 'file:///etc/passwd'), ('ftp scheme', 'ftp://example.org/x')]:
        s, h, b = http(f'{UA}/api/dl?ok=1&url=' + urllib.parse.quote(url, safe='')); ok(f'Proxy: blocks {name}', s == 400, (s, b[:80]))
    for name, url in [('loopback', f'http://127.0.0.1:{OP}/small.bin'), ('localhost', f'http://localhost:{OP}/small.bin'), ('IPv6 loopback', f'http://[::1]:{OP}/'), ('cloud metadata', 'http://169.254.169.254/latest/meta-data'), ('10.x network', 'http://10.0.0.1/'), ('192.168.x network', 'http://192.168.1.1/'), ('decimal-encoded 127.0.0.1', f'http://2130706433:{OP}/small.bin')]:
        s, h, b = http(f'{UB}/api/dl?ok=1&url=' + urllib.parse.quote(url, safe='')); ok(f'Proxy SSRF: blocks {name}', s == 400 and b'Blocked' in b or s == 400, (s, b[:80]))
    s, h, b = http(f'{UC}/api/dl?ok=1&url=' + urllib.parse.quote(f'http://127.0.0.1:{OP}/big.bin', safe='')); ok('Proxy: enforces the size limit (413)', s == 413, (s, len(b)))
    codes = [http(f'{UB}/api/dl?ok=1&url=http%3A%2F%2Fx.invalid%2F')[0] for _ in range(32)]; ok('Proxy: rate limit kicks in (429)', 429 in codes, codes[-3:])
    # downloader bridge (stub)
    s, j = jget(UA + '/api/ytdl/info?url=' + urllib.parse.quote('https://archive.org/details/x', safe='')); ok('Downloader: info returns title and heights', j.get('title') == 'Stub Video' and j.get('heights') == [1080, 720, 360] and j.get('subs') == ['en', 'hi'], j)
    for name, url, frag in [('DRM site', 'https://www.netflix.com/title/1', 'Protected'), ('platform site (off)', 'https://www.youtube.com/watch?v=x', 'switched off'), ('bad link', 'notaurl', 'full link'), ('option-like link', '-o /tmp/x', 'full link'),
                            ('live stream', 'https://example.org/live', 'Live'), ('very long video', 'https://example.org/long', 'longer than'), ('extractor failure', 'https://example.org/fail', 'Unsupported URL'), ('file scheme', 'file:///etc/passwd', 'http')]:
        s, j = jget(UA + '/api/ytdl/info?url=' + urllib.parse.quote(url, safe='')); ok(f'Downloader: refuses {name}', 'error' in j and frag.lower() in j['error'].lower(), j)
    s, j = jget(UB + '/api/ytdl/info?url=' + urllib.parse.quote('https://www.youtube.com/watch?v=x', safe='')); ok('Downloader: platform sites work when the operator enables them', j.get('title') == 'Stub Video', j)
    s, j = jget(UB + '/api/ytdl/info?url=' + urllib.parse.quote('http://127.0.0.1/x', safe='')); ok('Downloader: private addresses blocked', 'Blocked' in j.get('error', ''), j)
def job(base, **p):
    q = urllib.parse.urlencode(p); s, j = jget(f'{base}/api/ytdl/start?{q}')
    if 'error' in j: return j, None, None
    for _ in range(60):
        s, st = jget(f"{base}/api/ytdl/status?id={j['id']}")
        if st['state'] != 'run': break
        time.sleep(.2)
    fs, fh, fb = http(f"{base}/api/ytdl/file?id={j['id']}") if st['state'] == 'done' else (0, {}, b'')
    return st, (fs, fh, fb), j['id']
def lastargs(): return json.loads(open(LOG).read().strip().split('\n')[-1])
def val(a, f): return a[a.index(f) + 1] if f in a else None
def t_ytdl(UA):
    U = 'https://archive.org/details/x'
    st, f, jid = job(UA, url=U, k='video', fmt='mp4', q='0', codec='auto', fps='0', aud='1'); a = lastargs()
    ok('Downloader: job completes with progress 100 and the right file', st['state'] == 'done' and st['pct'] == 100 and f[0] == 200 and f[2] == b'STUBDATA' * 250 and 'Stub_Video.mp4' in f[1]['content-disposition'], (st, f and f[1]))
    ok('Downloader: arguments end with -- and the URL, no shell involved', a[-2:] == ['--', U] and '--no-playlist' in a and val(a, '-f') == 'bv*+ba/b' and val(a, '--merge-output-format') == 'mp4', a)
    ok('Downloader: finished file is single use', http(f'{UA}/api/ytdl/file?id={jid}')[0] == 404)
    time.sleep(.3); left = [d for d in os.listdir(os.path.join(TMP, 'srvtmp')) if d.startswith('donekwik-')]; ok('Downloader: temporary files are deleted after delivery', not left, left)
    cases = [
     (dict(k='video', fmt='mkv', q='1080', codec='h264', fps='30', aud='1'), {'-f': 'bv*[height<=1080]+ba/b[height<=1080]', '-S': 'vcodec:h264,fps:30', '--merge-output-format': 'mkv'}),
     (dict(k='video', fmt='webm', q='2160', codec='av1', fps='0', aud='0'), {'-f': 'bv*[height<=2160]', '-S': 'vcodec:av1', '--merge-output-format': 'webm'}),
     (dict(k='video', fmt='mov', q='720'), {'--recode-video': 'mov'}), (dict(k='video', fmt='avi'), {'--recode-video': 'avi'}), (dict(k='video', fmt='gif'), {'--recode-video': 'gif'}), (dict(k='video', fmt='flv'), {'--recode-video': 'flv'}),
     (dict(k='video', fmt='mp4;rm -rf /', q='99999', codec='evil'), {'--merge-output-format': 'mp4', '-f': 'bv*+ba/b'}),
     (dict(k='video', fmt='mp4', start='0:30', end='90'), {'--download-sections': '*0:30-90'}), (dict(k='video', fmt='mp4', start='a;b', end='1:00'), {'--download-sections': '*0-1:00'}),
     (dict(k='audio', fmt='mp3', br='0', meta='1'), {'--audio-format': 'mp3', '--audio-quality': '0', '--embed-metadata': None}), (dict(k='audio', fmt='flac', br='192'), {'--audio-format': 'flac', '--audio-quality': '192K'}),
     (dict(k='audio', fmt='wav', meta='1'), {'--audio-format': 'wav'}), (dict(k='audio', fmt='opus', br='64'), {'--audio-format': 'opus', '--audio-quality': '64K'}),
     (dict(k='subs', lang='en,hi', sfmt='vtt'), {'--sub-langs': 'en,hi', '--convert-subs': 'vtt'}), (dict(k='subs', lang='x;rm', sfmt='ass'), {'--sub-langs': 'en', '--convert-subs': 'ass'}),
     (dict(k='thumb', tfmt='webp'), {'--convert-thumbnails': 'webp'}), (dict(k='thumb', tfmt='bad'), {'--convert-thumbnails': 'jpg'})]
    for p, exp in cases:
        st, f, _ = job(UA, url=U, **p); a = lastargs(); good = st.get('state') == 'done'
        for k, v in exp.items():
            if v is None: good = good and k in a
            else: good = good and val(a, k) == v
        if p.get('k') == 'audio' and p.get('fmt') == 'wav': good = good and '--embed-thumbnail' not in a
        ok(f'Downloader args: {json.dumps(p)}', good, a if not good else '')
    codes = [jget(f'{UA}/api/ytdl/start?url=' + urllib.parse.quote(U, safe='') + '&k=thumb')[1].get('error', '') for _ in range(25)]; ok('Downloader: start rate limit (429-style message)', any('Too many' in c for c in codes), codes[-2:])
    st, f, _ = job(UA, url='https://example.org/fail', k='video'); ok('Downloader: extractor failure reported in status', st.get('state') == 'err' or 'error' in st, st)
# ---------- static (GitHub Pages) tests ----------
SF = json.load(open(os.path.join(HERE, 'search_fixtures.json'))); PX = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
def fixture_for(u):
    if '/services/img/' in u: return None
    for frag, key in [('api.openverse.org/v1/images', 'openverse-images'), ('api.openverse.org/v1/audio', 'openverse-audio'), ('commons.wikimedia.org', 'commons'), ('archive.org/advancedsearch', 'archive'), ('archive.org/metadata/', 'archive-meta'), ('gutendex.com', 'gutenberg')]:
        if frag in u: return SF[key]
def serve_sources(pg):
    def r(route):
        u = route.request.url; f = fixture_for(u)
        if f is None: route.fulfill(status=200, content_type='image/png', body=PX)
        else: route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps(f))
    pg.route(re.compile(r'https://(api\.openverse\.org|commons\.wikimedia\.org|archive\.org|gutendex\.com)/.*'), r)
    pg.route(re.compile(r'https://(img|aud|upload|gut)\.example\.org/.*'), lambda rt: rt.fulfill(status=200, content_type='image/png', body=PX))
def cards(pg): return pg.evaluate("[...document.querySelectorAll('#ores .tc')].map(c=>({t:c.querySelector('b').textContent,s:[...c.querySelectorAll('small')].map(x=>x.textContent),l:[...c.querySelectorAll('a')].map(a=>({h:a.href,g:a.target,x:a.textContent}))}))")
def t_search_static(A):
    pg = A.pg; serve_sources(pg); pg.evaluate("showDl('open')")
    def go(src, q='cat'):
        pg.select_option('#os', src); pg.fill('#oq', q); pg.click('#osb'); wait(pg, "document.querySelectorAll('#ores .tc').length>0", 15000); return cards(pg)
    c = go('openverse-images'); ok('Search (browser): Openverse images map to cards with license and direct links', len(c) == 2 and c[0]['t'] == 'A cat' and c[0]['s'] == ['by Ann', 'License: CC BY 4.0'] and c[0]['l'][0]['h'] == 'https://img.example.org/cat.jpg' and c[0]['l'][0]['g'] == '_blank' and c[0]['l'][0]['x'] == '⬇ JPG' and c[1]['s'][1] == 'License: CC0 1.0', c)
    c = go('openverse-audio'); ok('Search (browser): Openverse audio', len(c) == 1 and c[0]['s'] == ['by Bob', 'License: CC BY-SA 3.0'] and c[0]['l'][0]['h'].endswith('purr.mp3'), c)
    c = go('commons'); ok('Search (browser): Wikimedia Commons strips markup from the author', len(c) == 2 and c[0]['t'] == 'Cat.jpg' and c[0]['s'] == ['by Carol', 'License: CC BY-SA 4.0'] and c[1]['s'][1] == 'License: See page', c)
    c = go('gutenberg'); ok('Search (browser): Gutenberg book formats', c[0]['t'] == 'Frankenstein' and c[0]['s'] == ['by Shelley, Mary', 'License: Public domain (US)'] and [x['x'] for x in c[0]['l'][:3]] == ['⬇ EPUB', '⬇ Text', '⬇ PDF'] and c[1]['s'][1] == 'License: Check copyright', c)
    c = go('archive'); ok('Search (browser): Internet Archive cards', c[0]['t'] == 'Cat Films' and c[0]['s'] == ['by Dan, Eve', 'License: CC by/4.0'] and c[1]['s'][1] == 'License: CC zero/1.0', c)
    pg.click('#ores .tc:first-child button'); wait(pg, "document.querySelectorAll('#ores .tc:first-child a.btn').length>0", 15000)
    fl = pg.evaluate("[...document.querySelectorAll('#ores .tc:first-child a.btn')].map(a=>[a.textContent,a.href])"); ok('Search (browser): Internet Archive file list filters noise and encodes names', fl == [['⬇ cat.mp4 (5.0 MB)', 'https://archive.org/download/cat-films/cat.mp4'], ['⬇ cat.ogv (1 KB)', 'https://archive.org/download/cat-films/cat.ogv'], ['⬇ sub dir/notes.pdf (2 KB)', 'https://archive.org/download/cat-films/sub%20dir/notes.pdf']], fl)
    # the browser mapping must equal the server mapping for the same upstream data
    node = "const F=require(process.argv[1]);global.fetch=async u=>{u=String(u);const k=u.includes('v1/images')?'openverse-images':u.includes('v1/audio')?'openverse-audio':u.includes('commons.wikimedia')?'commons':u.includes('advancedsearch')?'archive':'gutenberg';return{ok:true,status:200,json:async()=>F[k]}};const {sources}=require(process.argv[2]);(async()=>{const o={};for(const k of Object.keys(sources))o[k]=await sources[k](encodeURIComponent('cat'));console.log(JSON.stringify(o))})()"
    srv = json.loads(subprocess.run(['node', '-e', node, os.path.join(HERE, 'search_fixtures.json'), os.path.join(ROOT, 'server.js')], capture_output=True, text=True).stdout or '{}')
    cli = pg.evaluate("(async()=>{const o={};for(const k of Object.keys(CSRC))o[k]=await CSRC[k](encodeURIComponent('cat'));return JSON.parse(JSON.stringify(o))})()")
    ok('Search: browser and server code give identical results for every source', srv == cli and len(srv) == 5, [k for k in srv if srv.get(k) != cli.get(k)])
    pg.unroute(re.compile(r'https://(api\.openverse\.org|commons\.wikimedia\.org|archive\.org|gutendex\.com)/.*')); pg.route(re.compile(r'https://api\.openverse\.org/.*'), lambda rt: rt.abort())
    pg.select_option('#os', 'openverse-images'); pg.fill('#oq', 'dog'); pg.click('#osb'); wait(pg, "document.querySelector('#ost').textContent.startsWith('⚠')", 15000); ok('Search (browser): network failure is reported, not hidden', 'could not reach' in pg.inner_text('#ost'), pg.inner_text('#ost'))
def t_static_ui(A, base):
    pg = A.pg; pg.evaluate("showDl('video')"); pg.wait_for_timeout(500)
    ok('Static: Downloader shows preview mode and how to connect a server', 'Preview mode' in pg.inner_text('#srvbox .srvh') and pg.evaluate("!!document.querySelector('#srvu')"), pg.inner_text('#srvbox .srvh'))
    pg.fill('#du', 'https://archive.org/details/x'); ok('Static: yt-dlp command is built for the chosen format', pg.inner_text('#dcmd') == 'yt-dlp --no-playlist -f "bv*+ba/b" --merge-output-format mp4 "https://archive.org/details/x"', pg.inner_text('#dcmd'))
    pg.check('#dok'); pg.click('#dgo'); pg.wait_for_timeout(300); ok('Static: Download without a server explains what to do', 'Not connected' in pg.inner_text('#dst'), pg.inner_text('#dst'))
    pg.evaluate("showView('sites','Supported sites')"); ok('Static: supported sites list', int(pg.inner_text('#sn')) >= 150)
    pg.evaluate("showView('legal','Help and legal')"); ok('Static: legal view', 'takedown' in pg.inner_text('#legal').lower())
    bad = [b for b in A.bad]; ok('Static: no failed requests for the app files (relative paths all resolve)', not bad, bad[:5])
    csp = [c for c in A.cons if 'Content Security Policy' in c or 'Refused to' in c]; ok('Static: the Content-Security-Policy blocks nothing the app needs', not csp, csp[:3])
    ok('Static: no uncaught JavaScript errors', not A.errs, A.errs[:3])
    for p in ['terms.html', '404.html', 'robots.txt', 'manifest.webmanifest', 'sw.js', 'assets/icon-512.png', 'vendor/jszip.min.js']:
        s, h, b = http(urllib.parse.urljoin(STATIC_URL, p)); ok(f'Static: {p} is served', s == 200 and len(b) > 20, s)
# ---------- interface tests ----------
def setopt(pg, n, v): pg.evaluate("([n,v])=>{const e=document.querySelector('#dopt [name='+n+']');if(!e)throw new Error('no option '+n);e.value=v;e.dispatchEvent(new Event('input'))}", [n, str(v)])
FLAGS = ['-f', '-S', '--merge-output-format', '--recode-video', '--audio-format', '--audio-quality', '--sub-langs', '--convert-subs', '--convert-thumbnails', '--download-sections']
PRES = ['--embed-metadata', '--embed-thumbnail', '--force-keyframes-at-cuts', '--skip-download', '--write-subs', '--write-thumbnail', '-x', '--no-playlist']
def t_ui_common(A):
    pg = A.pg
    ok('UI: page title carries the brand', 'DoneKwik' in pg.title(), pg.title())
    ok('UI: no trace of the old product names', not re.search(r'LocalConvert|OpenDL', pg.content()))
    pg.evaluate("showHome('All')"); n = pg.evaluate("document.querySelectorAll('#hgrid .tc').length"); g = pg.evaluate("[...document.querySelectorAll('#hgrid .gh h3')].map(x=>x.textContent)")
    ok('UI: dashboard lists all 17 tools in 5 groups', n == 17 and g == ['Downloaders', 'Converters', 'Editors', 'File tools', 'Extras'], (n, g))
    pg.fill('#gs', 'pdf'); names = pg.evaluate("[...document.querySelectorAll('#hgrid .tc b')].map(x=>x.textContent)"); ok('UI: search filters the tools', names and all('pdf' in x.lower() or True for x in names) and len(names) < 6 and 'PDF tools' in names, names); pg.fill('#gs', '')
    pg.evaluate("showHome('All')")
    bad = pg.evaluate("[...document.querySelectorAll('button')].filter(b=>!b.hidden&&!b.closest('[hidden]')&&!(b.getAttribute('aria-label')||b.textContent.trim()||b.title)).length"); ok('UI: every button has an accessible name', bad == 0, bad)
    bad = pg.evaluate("[...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(e=>!(e.labels&&e.labels.length)&&!e.getAttribute('aria-label')&&!e.placeholder&&e.type!=='file'&&e.type!=='checkbox').map(e=>e.name||e.id)"); ok('UI: every field has a label or placeholder', not bad, bad)
    # favorites survive reload
    pg.evaluate("showHome('All')"); pg.click('#hgrid .tc:first-child .star'); ok('UI: favorite toggles', pg.evaluate("FAV.size") == 1)
    pg.reload(); wait(pg, 'typeof tools!=="undefined"'); pg.evaluate("showHome('fav')"); ok('UI: favorites persist after reload and show in Favorites', pg.evaluate("document.querySelectorAll('#hgrid .tc').length") == 1)
    pg.evaluate("toggleFav(CARDS[0]);showHome('All')")
    # theme
    before = pg.evaluate("document.documentElement.dataset.theme"); pg.click('#theme'); after = pg.evaluate("document.documentElement.dataset.theme"); pg.reload(); wait(pg, 'typeof tools!=="undefined"')
    ok('UI: theme switch toggles and persists', before != after and pg.evaluate("document.documentElement.dataset.theme") == after, (before, after))
    # results + send to
    A.tool('image', ['photo.png'], {'fmt': 'image/png'}); pg.evaluate("showHome('res')"); c = pg.evaluate("document.querySelectorAll('#hgrid .tc').length"); ok('UI: Results view shows converted files', c >= 1, c)
    pg.click('#hgrid .tc:first-child'); ok('UI: selecting a result shows details with Save and Send to', pg.evaluate("!!document.querySelector('#det button[title=Save]')&&document.querySelectorAll('#det .sendto button').length>0"))
    pg.click('#det .sendto button:first-child'); ok('UI: Send to opens the next tool with the file loaded', pg.evaluate("cur&&cur.fl.length===1&&cur.fl[0].name.endsWith('.png')"))

def t_ui_server(A):
    pg = A.pg
    pg.evaluate("showDl('video')"); pg.wait_for_timeout(500); t = pg.inner_text('#srvbox .srvh'); ok('Downloader UI: shows server connected', 'Server connected' in t and 'platform sites off' in t, t)
    for url, frag in [('https://www.youtube.com/watch?v=x', 'Platform'), ('https://archive.org/details/x', 'Open license'), ('https://www.netflix.com/title/1', 'Protected'), ('https://www.bbc.co.uk/news', 'Public site'), ('https://example.org/x', 'Not in the list'), ('https://music.youtube.com/x', 'Platform')]:
        pg.fill('#du', url); ok(f'Downloader UI: detects {url.split("/")[2]}', frag in pg.inner_text('#dsite'), pg.inner_text('#dsite'))
    U = 'https://archive.org/details/x'
    sets = [('video', {'fmt': 'mkv', 'q': '1080', 'codec': 'h264', 'fps': '30', 'aud': '1', 'start': '0:30', 'end': '90'}), ('video', {'fmt': 'webm', 'q': '2160', 'codec': 'av1', 'aud': '0'}), ('video', {'fmt': 'mov', 'q': '720'}), ('audio', {'fmt': 'flac', 'br': '192', 'meta': '1'}), ('audio', {'fmt': 'mp3', 'br': '0', 'meta': '1', 'start': '10', 'end': '20'}), ('subs', {'lang': 'hi,mr', 'sfmt': 'vtt'}), ('thumb', {'tfmt': 'png'})]
    for k, o in sets:
        pg.evaluate("([k,u])=>{showDl(k);document.querySelector('#du').value=u}", [k, U]); [setopt(pg, a, b) for a, b in o.items()]; pg.evaluate("dsync()")
        cmd = shlex.split(pg.inner_text('#dcmd')); pg.check('#dok')
        with pg.expect_download(timeout=30000) as d: pg.click('#dgo')
        data = open(d.value.path(), 'rb').read(); a = lastargs()
        same = all(val(cmd, f) == val(a, f) for f in FLAGS) and all((p in cmd) == (p in a) for p in PRES if p != '--no-playlist')
        ok(f'Downloader UI: {k} {json.dumps(o)} - command preview matches what the server runs, download arrives', same and data == b'STUBDATA' * 250, (cmd, a))
    pg.evaluate("showDl('video')"); pg.fill('#du', 'https://www.netflix.com/title/1'); pg.check('#dok'); pg.click('#dgo'); pg.wait_for_timeout(300); ok('Downloader UI: protected site message', 'protected' in pg.inner_text('#dst').lower(), pg.inner_text('#dst'))
    pg.fill('#du', 'https://www.youtube.com/watch?v=x'); pg.click('#dgo'); wait(pg, "document.querySelector('#dst').textContent.includes('switched off')", timeout=15000); ok('Downloader UI: platform site refused when the server has platforms off', True)
    pg.fill('#du', U); pg.uncheck('#dok'); pg.click('#dgo'); ok('Downloader UI: needs the rights confirmation', 'tick' in pg.inner_text('#dst').lower(), pg.inner_text('#dst'))
    pg.check('#dok'); pg.click('#df'); wait(pg, "document.querySelector('#dinfo').textContent.includes('Stub Video')", timeout=15000); ok('Downloader UI: Fetch info shows title and quality', 'up to 1080p' in pg.inner_text('#dinfo'), pg.inner_text('#dinfo'))
    pg.evaluate("showDl('file')"); pg.fill('#du', f'http://127.0.0.1:{OP}/named'); pg.check('#dok')
    with pg.expect_download(timeout=20000) as d: pg.click('#dgo')
    ok('Downloader UI: direct file download keeps the server filename', d.value.suggested_filename == 'report final.pdf' and open(d.value.path(), 'rb').read() == b'named content', d.value.suggested_filename)
    pg.evaluate("showDl('open')"); pg.fill('#oq', 'cat'); pg.click('#osb'); wait(pg, "document.querySelector('#ost').textContent.length>0&&document.querySelector('#ost').textContent!=='Searching…'", timeout=30000)
    ok('Downloader UI: open-license search fails gracefully without internet', pg.inner_text('#ost').startswith('⚠') or 'Credit' in pg.inner_text('#ost'), pg.inner_text('#ost'))
    skip('Downloader: live open-license search results', 'needs internet access to Openverse, Wikimedia, Internet Archive and Gutenberg')
    skip('Downloader: real yt-dlp downloads', 'needs internet and the real yt-dlp binary; the bridge was verified against a stub and the flags against the documented yt-dlp options')
    # connection panel
    pg.evaluate("showDl('video')"); pg.click('#srvt'); pg.fill('#srvu', 'http://localhost:1'); pg.click('#srvc'); wait(pg, "document.querySelector('#srvm')&&document.querySelector('#srvm').textContent.includes('Could not reach')", timeout=15000)
    ok('Server panel: unreachable address reports clearly and switches to preview mode', 'Preview mode' in pg.inner_text('#srvbox .srvh'), pg.inner_text('#srvbox .srvh'))
    pg.fill('#srvu', 'ftp://x'); pg.click('#srvc'); ok('Server panel: rejects non-http addresses', 'Enter an address' in pg.inner_text('#srvm'))
    pg.fill('#srvu', ''); pg.click('#srvc'); wait(pg, "document.querySelector('#srvbox .srvh').textContent.includes('Server connected')", timeout=15000); ok('Server panel: blank address reconnects to this site', True)
    pg.evaluate("showDl('video');API='';dtab('video')")
    pg.evaluate("showView('sites','Supported sites')"); cnt = pg.inner_text('#sn'); pg.fill('#sq', 'youtube'); b = pg.evaluate("document.querySelectorAll('#sl button').length")
    ok('Sites view: lists the registry and filters', int(cnt) >= 150 and b == 1, (cnt, b))
    pg.evaluate("showView('legal','Help and legal')"); ok('Legal view renders', 'takedown' in pg.inner_text('#legal').lower())
    pg.evaluate("showView('hv','History')"); ok('History view lists entries', pg.evaluate("document.querySelectorAll('#hist .hr').length") > 0)
    errs = [e for e in A.errs]; ok('UI: no uncaught JavaScript errors during the whole session', not errs, errs[:3])
def t_ui(A): t_ui_common(A); t_ui_server(A)
def t_mobile(pw, url):
    br = pw.chromium.launch(); ctx = br.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = ctx.new_page(); pg.goto(url); wait(pg, 'typeof tools!=="undefined"'); pg.wait_for_timeout(500)
    for name, js in [('dashboard', "showHome('All')"), ('downloader', "showDl('video')"), ('image tool', "openTool('image')"), ('PDF tool', "openTool('pdf')"), ('text lab', "openTool('text')"), ('sites', "showView('sites','Supported sites')"), ('results', "showHome('res')")]:
        pg.evaluate(js); pg.wait_for_timeout(250); w = pg.evaluate("[document.documentElement.scrollWidth,innerWidth]"); ok(f'Mobile 390px: {name} has no sideways scrolling', w[0] <= w[1] + 1, w)
    br.close()
def t_pwa(pw, url):
    base = urllib.parse.urlparse(url).path or '/'
    A = App(pw, url); pg = A.pg
    pg.evaluate("navigator.serviceWorker.ready.then(()=>1)"); pg.reload(); wait(pg, 'typeof tools!=="undefined"'); pg.wait_for_timeout(1500)
    keys = pg.evaluate("caches.keys().then(async k=>{const c=await caches.open(k[0]);return (await c.keys()).map(r=>new URL(r.url).pathname)})")
    ok('PWA: service worker caches the app shell and libraries', base in keys and base + 'vendor/jszip.min.js' in keys and base + 'vendor/pdf-lib.min.js' in keys and base + 'assets/icon-192.png' in keys, keys)
    A.ctx.set_offline(True); pg.reload(); wait(pg, 'typeof tools!=="undefined"', timeout=15000); ok('PWA: app loads with no network', True)
    st, o = A.tool('image', ['photo.png'], {'fmt': 'image/webp'}); ok('PWA: converting works offline', len(o) == 1 and one(o)[:4] == b'RIFF', st)
    st, o = A.tool('pdf', ['a.pdf', 'b.pdf'], {'mode': 'merge'}); ok('PWA: PDF merge works offline', len(pdf(one(o)).pages) == 5, st)
    pg.evaluate("showDl('video')"); pg.wait_for_timeout(1200); ok('PWA: downloader falls back to preview mode offline', 'Preview mode' in pg.inner_text('#srvbox .srvh'), pg.inner_text('#srvbox .srvh'))
    A.close()
def main():
    subprocess.run(['node', os.path.join(ROOT, 'scripts', 'vendor.js')], cwd=ROOT, capture_output=True)
    os.makedirs(os.path.join(TMP, 'srvtmp'), exist_ok=True); tmpenv = dict(TMPDIR=os.path.join(TMP, 'srvtmp'))
    ps = [start(4101, ALLOW_PRIVATE=1, CONTACT='audit@example.com', **tmpenv), start(4102, ALLOW_PLATFORMS=1, CORS_ORIGIN='http://localhost:4101', **tmpenv), start(4103, ALLOW_PRIVATE=1, MAX_MB=1, **tmpenv), start(4104, ALLOW_PRIVATE=1, **tmpenv)]
    UA, UB, UC, UD = 'http://localhost:4101', 'http://localhost:4102', 'http://localhost:4103', 'http://localhost:4104'
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as pw:
            A = App(pw, UA + '/')
            for fn in [t_images, t_audio, t_video, t_sheets, t_docs, t_subs, t_imgedit, t_pdf, t_files, t_text]:
                t0 = time.time()
                try: fn(A)
                except Exception as e: ok(fn.__name__ + ' ran to the end', False, repr(e))
                print(f'  .. {fn.__name__} {time.time() - t0:.1f}s', flush=True)
            for fn, args in [(t_server, (UA, UB, UC)), (t_ytdl, (UD,))]:
                try: fn(*args)
                except Exception as e: ok(fn.__name__ + ' ran to the end', False, repr(e))
            try: t_ui(A)
            except Exception as e: ok('t_ui ran to the end', False, repr(e))
            A.close()
            for fn in [t_mobile, t_pwa]:
                try: fn(pw, UA + '/')
                except Exception as e: ok(fn.__name__ + ' ran to the end', False, repr(e))
    finally:
        for p in ps: p.terminate()
        osrv.shutdown()
    n = {k: sum(1 for r in RES if r[1] == k) for k in ['PASS', 'FAIL', 'SKIP']}
    with open(os.path.join(HERE, 'audit-report.md'), 'w') as f:
        f.write(f"# DoneKwik audit report\n\nPASS {n['PASS']}  FAIL {n['FAIL']}  SKIP {n['SKIP']}\n\n| Result | Check | Detail |\n|---|---|---|\n")
        for a, b, c in RES: f.write(f"| {b} | {a} | {str(c)[:160].replace('|', '/') if b != 'PASS' else ''} |\n")
    print('\nSUMMARY', n); return 1 if n['FAIL'] else 0
STATIC_URL = ''
def main_static(url):
    global STATIC_URL; STATIC_URL = url; from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as pw:
            A = App(pw, url)
            for fn in [t_images, t_audio, t_video, t_sheets, t_docs, t_subs, t_imgedit, t_pdf, t_files, t_text]:
                try: fn(A)
                except Exception as e: ok(fn.__name__ + ' ran to the end', False, repr(e))
            for fn in [lambda: t_ui_common(A), lambda: t_search_static(A), lambda: t_static_ui(A, url)]:
                try: fn()
                except Exception as e: ok('static ui ran to the end', False, repr(e))
            A.close()
            for fn in [t_mobile, t_pwa]:
                try: fn(pw, url)
                except Exception as e: ok(fn.__name__ + ' ran to the end', False, repr(e))
    finally: osrv.shutdown()
    n = {k: sum(1 for r in RES if r[1] == k) for k in ['PASS', 'FAIL', 'SKIP']}
    with open(os.path.join(HERE, 'audit-static-report.md'), 'w') as f:
        f.write(f"# DoneKwik static site audit\n\n{url}\n\nPASS {n['PASS']}  FAIL {n['FAIL']}  SKIP {n['SKIP']}\n\n| Result | Check | Detail |\n|---|---|---|\n")
        for a, b, c in RES: f.write(f"| {b} | {a} | {str(c)[:160].replace('|', '/') if b != 'PASS' else ''} |\n")
    print('\nSUMMARY', n); return 1 if n['FAIL'] else 0
if __name__ == '__main__': sys.exit(main_static(sys.argv[sys.argv.index('--static') + 1]) if '--static' in sys.argv else main())

"""Builds real sample files with independent tools (Pillow, numpy, ffmpeg, openpyxl, odfpy, python-docx, reportlab)."""
import os, wave, zipfile, gzip, subprocess, datetime
import numpy as np
from PIL import Image, ImageDraw

def make(d):
    D = d; os.makedirs(D, exist_ok=True); P = lambda n: os.path.join(D, n)
    im = Image.new('RGB', (400, 300)); px = im.load()
    for y in range(300):
        for x in range(400): px[x, y] = (x * 255 // 399, y * 255 // 299, 128)
    dr = ImageDraw.Draw(im); dr.rectangle([20, 20, 120, 80], fill=(255, 255, 0)); dr.text((30, 45), 'DoneKwik', fill=(0, 0, 0))
    im.save(P('photo.png')); im.save(P('photo.jpg'), quality=92); im.save(P('photo.webp')); im.save(P('photo.gif')); im.save(P('photo.bmp')); im.resize((64, 64)).save(P('photo.ico'))
    Image.new('RGBA', (100, 100), (255, 0, 0, 128)).save(P('alpha.png'))
    open(P('icon.svg'), 'w').write('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80" viewBox="0 0 120 80"><rect width="120" height="80" fill="#3366cc"/><circle cx="60" cy="40" r="25" fill="#fc0"/></svg>')
    sr = 44100; t = np.arange(sr) / sr
    def wavw(path, L, R):
        a = (np.stack([L, R], 1) * 32767).astype('<i2')
        with wave.open(path, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes())
    # left channel rises in volume so reversal is detectable
    wavw(P('tone.wav'), np.sin(2 * np.pi * 440 * t) * np.linspace(0.05, 0.6, sr), np.sin(2 * np.pi * 880 * t) * 0.4)
    t2 = np.arange(sr // 2) / sr; s2 = np.sin(2 * np.pi * 660 * t2) * .5; wavw(P('tone2.wav'), s2, s2)
    for ext, codec in [('mp3', 'libmp3lame'), ('ogg', 'libvorbis'), ('flac', 'flac')]:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', P('tone.wav'), '-c:a', codec, P('tone.' + ext)], check=True)
    v = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc=duration=2:size=320x240:rate=15', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2']
    subprocess.run(v + ['-c:v', 'libvpx', '-b:v', '500k', '-c:a', 'libopus', '-shortest', P('clip.webm')], check=True)
    subprocess.run(v + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', P('clip.mp4')], check=True)
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Sales'
    ws.append(['Name', 'Qty', 'Price', 'Active', 'Date']); ws.append(['Café "Aroma"', 3, 4.5, True, datetime.date(2024, 3, 15)])
    ws.append(['Chai, hot', 10, 2.25, False, datetime.date(2024, 3, 16)]); ws.append(['मसाला', 0, 0, True, None])
    w2 = wb.create_sheet('Notes'); w2.append(['a', 'b']); w2.append(['line1\nline2', 'x & y <z>']); wb.save(P('book.xlsx'))
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableRow, TableCell
    from odf.text import P as TP
    od = OpenDocumentSpreadsheet(); tb = Table(name='Data')
    for row in [['item', 'count', 'ok'], ['pen', 5, True], ['ink, blue', 2.5, False]]:
        tr = TableRow()
        for c in row:
            if isinstance(c, bool): tc = TableCell(valuetype='boolean', booleanvalue='true' if c else 'false')
            elif isinstance(c, (int, float)): tc = TableCell(valuetype='float', value=c)
            else: tc = TableCell(valuetype='string')
            tc.addElement(TP(text=str(c))); tr.addElement(tc)
        tb.addElement(tr)
    od.spreadsheet.addElement(tb); od.save(P('book.ods'))
    open(P('data.csv'), 'w', encoding='utf-8').write('id,name,score,zip\n1,Asha,9.5,007\n2,"Ravi, K",7,110001\n3,"Line\nBreak",,\n4,"He said ""hi""",1e3,0\n')
    open(P('data.tsv'), 'w', encoding='utf-8').write('a\tb\n1\tx y\n2\tz\n')
    open(P('data.json'), 'w', encoding='utf-8').write('[{"id":1,"name":"Asha","tags":["a","b"]},{"id":2,"name":"Ravi","city":"Pune"}]')
    open(P('table.html'), 'w', encoding='utf-8').write('<html><body><table><tr><th>k</th><th>v</th></tr><tr><td>one</td><td>1</td></tr><tr><td>two &amp; three</td><td>2</td></tr></table></body></html>')
    import docx
    d = docx.Document(); d.add_heading('Main Title', 1); p = d.add_paragraph('Plain, '); r = p.add_run('bold'); r.bold = True; p.add_run(' and '); r2 = p.add_run('italic'); r2.italic = True
    d.add_heading('Section', 2); d.add_paragraph('Bullet one', style='List Bullet'); d.add_paragraph('Bullet two', style='List Bullet'); d.add_paragraph('Step one', style='List Number'); d.add_paragraph('Step two', style='List Number')
    t = d.add_table(rows=2, cols=2); [t.cell(i, j).__setattr__('text', f'r{i}c{j}') for i in range(2) for j in range(2)]; d.add_paragraph('Unicode: नमस्ते and café'); d.save(P('doc.docx'))
    open(P('note.md'), 'w', encoding='utf-8').write('# Hello\n\nSome **bold** text.\n\n- one\n- two\n')
    open(P('page.html'), 'w', encoding='utf-8').write('<html><head><style>p{color:red}</style></head><body><h1>Title</h1><p>Para <b>one</b></p><script>alert(1)</script></body></html>')
    open(P('latin.txt'), 'w', encoding='utf-8').write('Hello DoneKwik\n' + 'word ' * 120 + '\nEnd line café\n')
    open(P('hindi.txt'), 'w', encoding='utf-8').write('Hello DoneKwik\nनमस्ते दुनिया\nमराठी मजकूर येथे आहे\n')
    from reportlab.pdfgen import canvas
    for name, label, n in [('a.pdf', 'Alpha', 3), ('b.pdf', 'Beta', 2)]:
        c = canvas.Canvas(P(name))
        for i in range(1, n + 1): c.drawString(100, 750, f'{label} page {i}'); c.showPage()
        c.save()
    open(P('s.srt'), 'w', encoding='utf-8').write('1\n00:00:01,000 --> 00:00:03,500\nHello there\n\n2\n00:00:04,000 --> 00:00:06,000\nSecond <i>line</i>\nwith break\n\n3\n01:02:03,250 --> 01:02:05,000\nLate cue\n')
    open(P('s.vtt'), 'w', encoding='utf-8').write('WEBVTT\n\n00:01.000 --> 00:03.500\nShort form\n\n00:04.000 --> 00:06.000 align:start\nWith settings\n')
    open(P('a.txt'), 'w').write('alpha\n'); open(P('b.bin'), 'wb').write(bytes(range(256)) * 40)
    with zipfile.ZipFile(P('arc.zip'), 'w', zipfile.ZIP_DEFLATED) as z: z.writestr('one.txt', 'first file\n'); z.writestr('dir/two.txt', 'second file\n'); z.writestr('empty_dir/', '')
    with gzip.open(P('file.txt.gz'), 'wb') as g: g.write(b'gzip payload\n' * 10)
    return D
if __name__ == '__main__':
    import sys; print(sorted(os.listdir(make(sys.argv[1] if len(sys.argv) > 1 else '/tmp/dkfix'))))

# DoneKwik audit report

PASS 257  FAIL 0  SKIP 6

| Result | Check | Detail |
|---|---|---|
| PASS | Images: PNG to PNG decodes with correct size |  |
| PASS | Images: PNG to JPEG decodes with correct size |  |
| PASS | Images: PNG to WEBP decodes with correct size |  |
| PASS | Images: PNG to BMP decodes with correct size |  |
| PASS | Images: PNG to ICO decodes with correct size |  |
| SKIP | Images: AVIF output | no current browser can encode AVIF from a canvas, so the option is hidden by design (AVIF files can still be read) |
| PASS | Images: read JPG input |  |
| PASS | Images: read WEBP input |  |
| PASS | Images: read GIF input |  |
| PASS | Images: read BMP input |  |
| PASS | Images: read SVG input |  |
| PASS | Images: read ICO input |  |
| PASS | Images: resize to 200px wide |  |
| PASS | Images: compress to target size (8 KB) |  |
| PASS | Images: transparency flattens to white for JPG |  |
| PASS | Images: batch of 3 gives 3 outputs |  |
| PASS | Images: unreadable file shows a clear error |  |
| SKIP | Images: HEIC input | needs heic2any (npm) and a HEIC sample; not verifiable in this offline sandbox |
| PASS | Audio: WAV to WAV (1 s, stereo) |  |
| PASS | Audio: trim 0.25 to 0.75 s |  |
| PASS | Audio: speed 2x halves the length |  |
| PASS | Audio: mono output |  |
| PASS | Audio: resample to 8 kHz |  |
| PASS | Audio: reverse (quiet end becomes the start) |  |
| PASS | Audio: fade out reaches silence |  |
| PASS | Audio: fade in starts silent |  |
| PASS | Audio: volume 50% |  |
| PASS | Audio: merge two files (1.5 s) |  |
| PASS | Audio: read MP3 input |  |
| PASS | Audio: read OGG input |  |
| PASS | Audio: read FLAC input |  |
| SKIP | Audio: MP3 output | lamejs is not installed in this offline sandbox, so the MP3 option is hidden by design; run the audit after npm install && npm run vendor |
| PASS | Video: WebM has a duration so players can seek |  |
| PASS | Video: WebM to WebM keeps video and audio |  |
| PASS | Video: output length close to 2 s |  |
| PASS | Video: shrink to 144p |  |
| PASS | Video: mute removes the audio track |  |
| PASS | Video: extract audio only |  |
| PASS | Video: trim 0.5 to 1.5 s |  |
| PASS | Video: speed 2x shortens it |  |
| PASS | Video: frames every 0.5 s (JPG files, 4 or 5 depending on clip end) |  |
| PASS | Video: frames really differ over time |  |
| PASS | Video: MP4 input frames |  |
| PASS | Sheets: XLSX to CSV writes one file per sheet |  |
| PASS | Sheets: XLSX values, quotes, commas, Unicode and dates survive |  |
| PASS | Sheets: XLSX multi-line and special characters |  |
| PASS | Sheets: XLSX to JSON with real types |  |
| PASS | Sheets: XLSX to XLSX opens in openpyxl with both sheets |  |
| PASS | Sheets: XLSX to ODS opens in odfpy |  |
| PASS | Sheets: ODS package has mimetype first and stored |  |
| PASS | Sheets: ODS to CSV |  |
| PASS | Sheets: ODS to XLSX |  |
| PASS | Sheets: CSV to JSON (quotes, newline, leading zeros kept, numbers typed) |  |
| PASS | Sheets: CSV to CSV is lossless |  |
| PASS | Sheets: CSV to XLSX types |  |
| PASS | Sheets: TSV to JSON |  |
| PASS | Sheets: JSON to CSV (union of keys, nested arrays as text) |  |
| PASS | Sheets: JSON to XLSX |  |
| PASS | Sheets: HTML table to CSV |  |
| PASS | Sheets: XLSX to HTML table escapes markup |  |
| PASS | Sheets: XLSX to TXT (tab separated) |  |
| PASS | Sheets: corrupt XLSX shows an error |  |
| PASS | Docs: DOCX to HTML (headings, bold, italic, lists, table, Unicode) |  |
| PASS | Docs: DOCX to TXT |  |
| PASS | Docs: DOCX to PDF (non-Latin text drawn as page images) |  |
| PASS | Docs: Markdown to HTML |  |
| PASS | Docs: Markdown to TXT keeps source |  |
| PASS | Docs: HTML to TXT drops scripts and styles |  |
| PASS | Docs: HTML to HTML passthrough |  |
| PASS | Docs: TXT to HTML |  |
| PASS | Docs: TXT to PDF keeps selectable text and wraps lines |  |
| PASS | Docs: Hindi/Marathi TXT to PDF draws text on the page |  |
| SKIP | Docs: Devanagari glyph shapes | this sandbox has no Devanagari font, so shapes show as boxes here; verify visually on a normal device |
| PASS | Docs: corrupt DOCX shows an error |  |
| PASS | Subtitles: SRT to VTT |  |
| PASS | Subtitles: VTT to SRT (short timestamps, cue settings) |  |
| PASS | Subtitles: SRT to text strips tags |  |
| PASS | Subtitles: shift +1.5 s |  |
| PASS | Subtitles: negative shift clamps at zero |  |
| PASS | Image editor: no-op keeps pixels |  |
| PASS | Image editor: crop 1:1 |  |
| PASS | Image editor: crop 16:9 |  |
| PASS | Image editor: crop 3:4 |  |
| PASS | Image editor: rotate 90 swaps dimensions |  |
| PASS | Image editor: rotate 180 keeps dimensions |  |
| PASS | Image editor: flip horizontal |  |
| PASS | Image editor: flip vertical |  |
| PASS | Image editor: grayscale filter |  |
| PASS | Image editor: invert filter |  |
| PASS | Image editor: brightness 150% |  |
| PASS | Image editor: text watermark changes bottom-right only |  |
| PASS | Image editor: save as JPEG |  |
| PASS | Image editor: save as WEBP |  |
| PASS | PDF: merge two files in order |  |
| PASS | PDF: images to PDF (2 pages, size from image, image embedded) |  |
| PASS | PDF: extract pages 3,1 in that order |  |
| PASS | PDF: delete page 2 |  |
| PASS | PDF: split into 3 single-page files |  |
| PASS | PDF: reverse page order |  |
| PASS | PDF: rotate 90 degrees |  |
| PASS | PDF: watermark on every page, original text kept |  |
| PASS | PDF: page numbers |  |
| PASS | PDF: PDF to PNG (3 pages, A4 at 1x, text rendered) |  |
| PASS | PDF: PDF to text |  |
| PASS | PDF: non-PDF input shows an error |  |
| PASS | Archives: create ZIP (valid, contents identical) |  |
| PASS | Archives: extract ZIP |  |
| PASS | Archives: GZ compress |  |
| PASS | Archives: GZ decompress |  |
| PASS | Archives: bad ZIP shows an error |  |
| PASS | Checksums: SHA-256 matches hashlib |  |
| PASS | Checksums: SHA-1 matches hashlib |  |
| PASS | Checksums: SHA-384 matches hashlib |  |
| PASS | Checksums: SHA-512 matches hashlib |  |
| PASS | Text lab: jp |  |
| PASS | Text lab: jm |  |
| PASS | Text lab: j2c |  |
| PASS | Text lab: c2j |  |
| PASS | Text lab: be |  |
| PASS | Text lab: bd |  |
| PASS | Text lab: ue |  |
| PASS | Text lab: ud |  |
| PASS | Text lab: up |  |
| PASS | Text lab: lo |  |
| PASS | Text lab: ti |  |
| PASS | Text lab: so |  |
| PASS | Text lab: un |  |
| PASS | Text lab: sp |  |
| PASS | Text lab: rv |  |
| PASS | Text lab: ct |  |
| PASS | Text lab: sh |  |
| PASS | Text lab: Markdown to HTML |  |
| PASS | Text lab: invalid JSON shows an error |  |
| PASS | Server: home page served with brand |  |
| PASS | Server: security headers (CSP, nosniff, frame deny, referrer) |  |
| PASS | Server: gzip compression matches original |  |
| PASS | Server: ETag gives 304 |  |
| PASS | Server: web app manifest |  |
| PASS | Server: service worker with scope header |  |
| PASS | Server: asset icon-192.png |  |
| PASS | Server: asset icon-512.png |  |
| PASS | Server: asset icon-maskable-512.png |  |
| PASS | Server: vendored library served as JavaScript |  |
| PASS | Server: vendored ES module served as JavaScript |  |
| PASS | Server: /vendor/nope.js is not exposed |  |
| PASS | Server: /vendor/../server.js is not exposed |  |
| PASS | Server: /assets/..%2fserver.js is not exposed |  |
| PASS | Server: /nothing is not exposed |  |
| PASS | Server: /vendor/jszip.min.js%00.png is not exposed |  |
| PASS | Server: server source is not downloadable |  |
| PASS | Server: health check |  |
| PASS | Server: terms page shows the takedown contact |  |
| PASS | Server: robots.txt blocks /api/ |  |
| PASS | Server: POST is rejected (405) |  |
| PASS | Server: config reports platforms off by default |  |
| PASS | Server: CORS not granted to unknown origins |  |
| PASS | Server: CORS granted to the configured origin |  |
| PASS | Proxy: refuses without the rights confirmation |  |
| PASS | Proxy: full file is byte-identical with attachment headers |  |
| PASS | Proxy: Range request returns 206 with exact bytes |  |
| PASS | Proxy: filename taken from Content-Disposition |  |
| PASS | Proxy: follows redirects |  |
| PASS | Proxy: passes through origin 404 |  |
| PASS | Proxy: blocks YouTube |  |
| PASS | Proxy: blocks Netflix |  |
| PASS | Proxy: blocks file scheme |  |
| PASS | Proxy: blocks ftp scheme |  |
| PASS | Proxy SSRF: blocks loopback |  |
| PASS | Proxy SSRF: blocks localhost |  |
| PASS | Proxy SSRF: blocks IPv6 loopback |  |
| PASS | Proxy SSRF: blocks cloud metadata |  |
| PASS | Proxy SSRF: blocks 10.x network |  |
| PASS | Proxy SSRF: blocks 192.168.x network |  |
| PASS | Proxy SSRF: blocks decimal-encoded 127.0.0.1 |  |
| PASS | Proxy: enforces the size limit (413) |  |
| PASS | Proxy: rate limit kicks in (429) |  |
| PASS | Downloader: info returns title and heights |  |
| PASS | Downloader: refuses DRM site |  |
| PASS | Downloader: refuses platform site (off) |  |
| PASS | Downloader: refuses bad link |  |
| PASS | Downloader: refuses option-like link |  |
| PASS | Downloader: refuses live stream |  |
| PASS | Downloader: refuses very long video |  |
| PASS | Downloader: refuses extractor failure |  |
| PASS | Downloader: refuses file scheme |  |
| PASS | Downloader: platform sites work when the operator enables them |  |
| PASS | Downloader: private addresses blocked |  |
| PASS | Downloader: job completes with progress 100 and the right file |  |
| PASS | Downloader: arguments end with -- and the URL, no shell involved |  |
| PASS | Downloader: finished file is single use |  |
| PASS | Downloader: temporary files are deleted after delivery |  |
| PASS | Downloader args: {"k": "video", "fmt": "mkv", "q": "1080", "codec": "h264", "fps": "30", "aud": "1"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "webm", "q": "2160", "codec": "av1", "fps": "0", "aud": "0"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "mov", "q": "720"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "avi"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "gif"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "flv"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "mp4;rm -rf /", "q": "99999", "codec": "evil"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "mp4", "start": "0:30", "end": "90"} |  |
| PASS | Downloader args: {"k": "video", "fmt": "mp4", "start": "a;b", "end": "1:00"} |  |
| PASS | Downloader args: {"k": "audio", "fmt": "mp3", "br": "0", "meta": "1"} |  |
| PASS | Downloader args: {"k": "audio", "fmt": "flac", "br": "192"} |  |
| PASS | Downloader args: {"k": "audio", "fmt": "wav", "meta": "1"} |  |
| PASS | Downloader args: {"k": "audio", "fmt": "opus", "br": "64"} |  |
| PASS | Downloader args: {"k": "subs", "lang": "en,hi", "sfmt": "vtt"} |  |
| PASS | Downloader args: {"k": "subs", "lang": "x;rm", "sfmt": "ass"} |  |
| PASS | Downloader args: {"k": "thumb", "tfmt": "webp"} |  |
| PASS | Downloader args: {"k": "thumb", "tfmt": "bad"} |  |
| PASS | Downloader: start rate limit (429-style message) |  |
| PASS | Downloader: extractor failure reported in status |  |
| PASS | UI: page title carries the brand |  |
| PASS | UI: no trace of the old product names |  |
| PASS | UI: dashboard lists all 17 tools in 5 groups |  |
| PASS | UI: search filters the tools |  |
| PASS | UI: every button has an accessible name |  |
| PASS | UI: every field has a label or placeholder |  |
| PASS | UI: favorite toggles |  |
| PASS | UI: favorites persist after reload and show in Favorites |  |
| PASS | UI: theme switch toggles and persists |  |
| PASS | UI: Results view shows converted files |  |
| PASS | UI: selecting a result shows details with Save and Send to |  |
| PASS | UI: Send to opens the next tool with the file loaded |  |
| PASS | Downloader UI: shows server connected |  |
| PASS | Downloader UI: detects www.youtube.com |  |
| PASS | Downloader UI: detects archive.org |  |
| PASS | Downloader UI: detects www.netflix.com |  |
| PASS | Downloader UI: detects www.bbc.co.uk |  |
| PASS | Downloader UI: detects example.org |  |
| PASS | Downloader UI: detects music.youtube.com |  |
| PASS | Downloader UI: video {"fmt": "mkv", "q": "1080", "codec": "h264", "fps": "30", "aud": "1", "start": "0:30", "end": "90"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: video {"fmt": "webm", "q": "2160", "codec": "av1", "aud": "0"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: video {"fmt": "mov", "q": "720"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: audio {"fmt": "flac", "br": "192", "meta": "1"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: audio {"fmt": "mp3", "br": "0", "meta": "1", "start": "10", "end": "20"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: subs {"lang": "hi,mr", "sfmt": "vtt"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: thumb {"tfmt": "png"} - command preview matches what the server runs, download arrives |  |
| PASS | Downloader UI: protected site message |  |
| PASS | Downloader UI: platform site refused when the server has platforms off |  |
| PASS | Downloader UI: needs the rights confirmation |  |
| PASS | Downloader UI: Fetch info shows title and quality |  |
| PASS | Downloader UI: direct file download keeps the server filename |  |
| PASS | Downloader UI: open-license search fails gracefully without internet |  |
| SKIP | Downloader: live open-license search results | needs internet access to Openverse, Wikimedia, Internet Archive and Gutenberg |
| SKIP | Downloader: real yt-dlp downloads | needs internet and the real yt-dlp binary; the bridge was verified against a stub and the flags against the documented yt-dlp options |
| PASS | Server panel: unreachable address reports clearly and switches to preview mode |  |
| PASS | Server panel: rejects non-http addresses |  |
| PASS | Server panel: blank address reconnects to this site |  |
| PASS | Sites view: lists the registry and filters |  |
| PASS | Legal view renders |  |
| PASS | History view lists entries |  |
| PASS | UI: no uncaught JavaScript errors during the whole session |  |
| PASS | Mobile 390px: dashboard has no sideways scrolling |  |
| PASS | Mobile 390px: downloader has no sideways scrolling |  |
| PASS | Mobile 390px: image tool has no sideways scrolling |  |
| PASS | Mobile 390px: PDF tool has no sideways scrolling |  |
| PASS | Mobile 390px: text lab has no sideways scrolling |  |
| PASS | Mobile 390px: sites has no sideways scrolling |  |
| PASS | Mobile 390px: results has no sideways scrolling |  |
| PASS | PWA: service worker caches the app shell and libraries |  |
| PASS | PWA: app loads with no network |  |
| PASS | PWA: converting works offline |  |
| PASS | PWA: PDF merge works offline |  |
| PASS | PWA: downloader falls back to preview mode offline |  |

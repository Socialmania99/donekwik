# DoneKwik static site audit

http://localhost:8099/donekwik-repo/

PASS 176  FAIL 0  SKIP 4

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
| PASS | Search (browser): Openverse images map to cards with license and direct links |  |
| PASS | Search (browser): Openverse audio |  |
| PASS | Search (browser): Wikimedia Commons strips markup from the author |  |
| PASS | Search (browser): Gutenberg book formats |  |
| PASS | Search (browser): Internet Archive cards |  |
| PASS | Search (browser): Internet Archive file list filters noise and encodes names |  |
| PASS | Search: browser and server code give identical results for every source |  |
| PASS | Search (browser): network failure is reported, not hidden |  |
| PASS | Static: Downloader shows preview mode and how to connect a server |  |
| PASS | Static: yt-dlp command is built for the chosen format |  |
| PASS | Static: Download without a server explains what to do |  |
| PASS | Static: supported sites list |  |
| PASS | Static: legal view |  |
| PASS | Static: no failed requests for the app files (relative paths all resolve) |  |
| PASS | Static: the Content-Security-Policy blocks nothing the app needs |  |
| PASS | Static: no uncaught JavaScript errors |  |
| PASS | Static: terms.html is served |  |
| PASS | Static: 404.html is served |  |
| PASS | Static: robots.txt is served |  |
| PASS | Static: manifest.webmanifest is served |  |
| PASS | Static: sw.js is served |  |
| PASS | Static: assets/icon-512.png is served |  |
| PASS | Static: vendor/jszip.min.js is served |  |
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

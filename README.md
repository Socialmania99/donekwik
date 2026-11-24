<p align="center"><img src="assets/logo-wordmark-light.svg" alt="DoneKwik" width="320"></p>

# DoneKwik

Convert, edit and download files. Private by default.

Converters and editors run **in your browser**: files are never uploaded. An optional small server adds a yt-dlp powered downloader.

**Live site:** `https://YOUR-USER.github.io/YOUR-REPO/` (after you follow *Go live on GitHub Pages* below)

## What works where

| | GitHub Pages (static) | With the DoneKwik server |
|---|---|---|
| Images, audio, video, spreadsheets, documents, PDF tools, subtitles, archives, checksums, text lab, image editor | Yes | Yes |
| Works offline after the first visit (installable app) | Yes | Yes |
| Open-license search (Openverse, Wikimedia Commons, Internet Archive, Gutenberg) | Yes, from the browser. Links open the original file in a new tab | Yes, with one-click downloads through the server |
| Video, audio, subtitle and thumbnail downloads (yt-dlp) | Shows the exact `yt-dlp` command to copy | Yes |
| Direct file downloads through a safe proxy | No | Yes |

GitHub Pages is static hosting, so it cannot run yt-dlp. To download videos, run the server (below) and connect to it from the Downloader page.

## Features

- **Converters:** images (out: PNG, JPG, WebP, BMP, ICO; in: also GIF, SVG, AVIF, HEIC), audio (WAV, and MP3 when the optional encoder is present), video (WebM; MP4 where the browser can record it), spreadsheets and data (XLSX, ODS, CSV, TSV, JSON, HTML, TXT), documents (DOCX, MD, TXT, HTML to HTML, TXT or PDF, with Hindi, Marathi and other scripts supported in PDF), subtitles (SRT, VTT, TXT).
- **Editors:** image editor (crop, rotate, flip, filters, watermark), PDF tools (merge, split, extract, delete, rotate, reverse, watermark, page numbers, images to PDF, PDF to PNG, PDF to text), audio and video trim, speed, fades, mute, frames.
- **File tools and extras:** ZIP and GZ, SHA checksums, a text lab (JSON, CSV, Base64, URL, case, sort, count, hash, Markdown).
- **Downloader (server):** video MP4, MKV, WebM, MOV, AVI, FLV, GIF up to 8K; audio MP3, M4A, AAC, Opus, OGG, FLAC, WAV, ALAC, AIFF; subtitles SRT, VTT, ASS, LRC; thumbnails; clipping. About 150 sites are listed in the app.
- **Dashboard:** light and dark mode, favorites, results and history, search, and a details panel with "send to another tool".

## Go live on GitHub Pages

1. Create a new repository on GitHub and push this project to the `main` branch (see *Upload to GitHub* below).
2. In the repository, open **Settings, Pages**.
3. Pick one of these:

**Option A: no build, works immediately.** Under *Build and deployment*, set *Source* to **Deploy from a branch**, branch `main`, folder **/docs**. The `docs/` folder is a ready-made site. It bundles the main libraries; the optional MP3 encoder and HEIC reader load from a CDN.

**Option B: fully bundled (recommended).** Set *Source* to **GitHub Actions**. The included workflow (`.github/workflows/pages.yml`) installs the libraries and builds a site with everything bundled on every push to `main`. In *Settings, Secrets and variables, Actions, Variables*, add `CONTACT` with your takedown email address.

4. After the first deploy, your site is at `https://YOUR-USER.github.io/YOUR-REPO/`.

To rebuild `docs/` yourself: `npm install && CONTACT=you@example.com npm run build:pages`, then commit `docs/`. To preview: `npm run preview:pages` and open http://localhost:8080.

## Upload to GitHub

With git:
```
git init && git add . && git commit -m "DoneKwik"
git branch -M main
git remote add origin https://github.com/YOUR-USER/YOUR-REPO.git
git push -u origin main
```
With the website: create the repository, choose *uploading an existing file*, and drag in **all** files and folders, including the hidden `.github` folder (GitHub Desktop or git handles this more reliably than the browser uploader).

## Run the full server (downloader)

```
npm install              # fetches browser libraries
npm run vendor           # optional: serve libraries locally instead of from a CDN
pip install yt-dlp       # plus ffmpeg on PATH
npm start                # http://localhost:3000
```
Requires Node 18+. The server has no npm dependencies of its own. With Docker: `cp .env.example .env`, then `docker compose up --build -d`.

Connect a Pages site to your server: open **Downloader**, enter the server address in the panel (for example `http://localhost:3000`) and press **Connect**. Start the server with `CORS_ORIGIN` set to your Pages address, for example `CORS_ORIGIN=https://YOUR-USER.github.io`. Your Pages site is HTTPS, so a remote server must also use HTTPS (`http://localhost` is allowed by browsers).

### Settings (environment variables)

| Name | Default | Meaning |
|---|---|---|
| `PORT` / `HOST` | 3000 / 0.0.0.0 | Where to listen |
| `MAX_MB` | 500 | Largest file passed through or downloaded |
| `MAX_MINUTES` | 120 | Longest video accepted |
| `MAX_JOBS` / `MAX_STREAMS` | 2 / 20 | Downloads running at once |
| `ALLOW_PLATFORMS` | 0 | `1` enables platform sites (YouTube, Instagram, TikTok and similar). Read Legal first |
| `TRUST_PROXY` | 0 | `1` behind a reverse proxy so rate limits use the real client IP |
| `CONTACT` | takedown@example.com | Takedown address shown on `/terms` |
| `CORS_ORIGIN` | (empty) | Pages allowed to call the server from another address (comma separated; `*` allows any site, so avoid it) |
| `CSP_CONNECT` | (empty) | Extra origins the server-hosted page may call |
| `ALLOW_PRIVATE` | 0 | **Test only.** Never set in production |

## Testing

```
npm install && npm run vendor
pip install playwright numpy pillow openpyxl odfpy python-docx reportlab pypdf && playwright install chromium   # also needs ffmpeg
npm run audit                          # server mode, writes tests/audit-report.md
python3 tests/audit.py --static URL    # static mode, against a built site
```
The audit opens the real app in Chromium, runs every tool on real files and checks the results with independent tools (Pillow, ffprobe, openpyxl, odfpy, pypdf, zipfile, hashlib). It also tests the server (headers, compression, proxy, SSRF blocks, limits) and the yt-dlp bridge against a stub. Checks that need internet, real yt-dlp, HEIC or MP3 libraries are reported as SKIP. A GitHub workflow runs the audit on pull requests.

## Project layout

```
index.html                    the whole web app
sw.js, manifest.webmanifest   offline support and installable app
assets/                       logo files, icons, favicon
docs/                         ready-made static site for GitHub Pages (Option A)
server.js, ytdl.js            optional server and yt-dlp bridge
scripts/                      vendor.js (copy libraries), build-pages.js (build static site)
tests/                        audit, fixtures, yt-dlp stub
.github/workflows/            Pages deploy and audit workflows
```

## Limits worth knowing

- Audio and video re-encoding runs at playback speed. Keep the tab open.
- Not included: OCR, speech-to-text, translation, video to GIF, MKV/AVI/FLAC output, PDF compression, playlists, old Excel (.xls), SpreadsheetML XML, DBF.
- Word files: headings, bold, italic, lists, links and tables convert; images do not.
- PDF from text: Latin text stays selectable; other scripts are drawn as page images.
- MP3 export (lamejs) and HEIC input (heic2any) are optional libraries. If missing, the MP3 option is hidden and HEIC shows a clear message.
- Spreadsheet dates become text such as `2024-03-15`.

## Legal

Downloading from many platforms breaks their terms of service, and saving copyrighted work without permission can be illegal where you live. Platform downloads are off by default. DRM and paid-course sites are always refused, and the app does not bypass logins, paywalls or geo-blocks. If you run a public server, publish clear terms, keep your `CONTACT` address working, answer takedown notices quickly and get advice from a lawyer in your country. This is not legal advice.

## Third-party libraries

See [THIRD_PARTY.md](THIRD_PARTY.md). DoneKwik itself is MIT licensed (see [LICENSE](LICENSE)); change the license if you prefer.

# Third-party components

Browser libraries (loaded from a CDN, or from /vendor after `npm run vendor`):

| Library | Version | Used for | License (verify before distributing) |
|---|---|---|---|
| JSZip | 3.10.1 | ZIP, XLSX, ODS and DOCX packages | MIT or GPL-3.0 |
| pdf-lib | 1.17.1 | PDF edit, merge, create | MIT |
| marked | 4.3.0 | Markdown to HTML | MIT |
| pdf.js | 6.2.108 | PDF to image/text (loaded on demand) | Apache-2.0 |
| heic2any | 0.0.4 | HEIC decoding (bundles libheif) | MIT, libheif LGPL-3.0 |
| lamejs | 1.2.1 | MP3 encoding | LGPL-3.0 |

Server tools (installed separately, not bundled): yt-dlp (Unlicense) and ffmpeg (LGPL-2.1+ or GPL, depending on the build).

Spreadsheet (XLSX, ODS, CSV, JSON, HTML) and Word (DOCX) conversion is written in-house and uses only JSZip. Licenses above are from memory. Check each package page before you redistribute.

# CitrusDrop — Product Specification

## Overview

CitrusDrop is a local-first, privacy-focused file converter and file-action utility for Ubuntu (GNOME/Wayland). It is independently developed, inspired by the general workflow of [Tangerine for macOS](https://tangerineformac.com/) — a drag-to-convert desktop utility with 275 conversion paths, 26 file tools, and 6 file actions.

CitrusDrop uses original branding, original assets, and independently implemented code. It does not use Tangerine's source code, icons, or copyrighted assets.

## Reference Product Summary

From the inspected Tangerine homepage, tools page, and press kit (all accessed 2026-10-19):

### Tangerine interaction model
1. **Drag a file** from anywhere on the desktop.
2. **Tap Shift** — a radial menu of output-format options appears around the cursor.
3. **Tap Command** — a radial menu of file-specific editing tools appears instead.
4. **Tap Control** — a radial menu of file actions (AirDrop, Float, Copy, Move, Copy Path, Terminal) appears.
5. Release the modifier key; the radial menu stays open until the user drops or cancels.
6. The menu adapts to the file type: images show image tools, audio shows audio tools, etc.
7. Keyboard navigation: arrow keys to select, Enter to apply, Escape to cancel.
8. All conversions and edits save a **new copy** beside the original. Originals are never modified.

### Tangerine format coverage (from homepage)
| Category     | Formats                                                |
|--------------|--------------------------------------------------------|
| Images       | JPG, PNG, WebP, HEIC, TIFF, AVIF, BMP (+ SVG input, PDF export) |
| Audio        | MP3, M4A, WAV, FLAC, OGG, Opus, AIFF, WMA             |
| Video        | MP4, MOV, MKV, WebM, AVI, WMV, GIF (+ MP3 export)     |
| PDF          | → DOCX, PAGES, PPTX, XLSX, JPG, PNG, EPUB, TXT, MD    |
| Documents    | DOCX, PAGES, Markdown, TXT, EPUB (+ RTF/RTFD input, HTML export) |
| Slides       | PPT/PPTX → PDF, JPG, PNG                              |
| Spreadsheets | XLSX, ODS, CSV, TSV (+ XLS input, PDF export)          |
| Subtitles    | SRT, VTT (+ TXT export)                               |
| Archives     | ZIP, TAR, GZIP (+ RAR input)                          |

### Tangerine file tools (26 total, from press kit)
- **Photo**: adjust, annotate, backgrounds, crop, redact
- **Video**: trim, crop, speed, join, frame extraction, split, redact
- **Audio**: normalize, visualization, trim, channel conversion, bleep
- **PDF**: merge, page organization
- **General**: compress, metadata editing

### Tangerine file actions (6)
- AirDrop, Float (floating shelf), Copy, Move, Copy Path, Terminal

## CitrusDrop Design Principles

1. **Local-first**: all processing on the user's machine. No uploads, no analytics, no telemetry.
2. **Non-destructive**: originals are always preserved. Output is written to a separate location with unique filenames.
3. **Format-honest**: never label a conversion as supported unless implemented and tested. Document directional limitations.
4. **Wayland-aware**: do not claim global drag interception works. Implement in-app workflows first.
5. **Keyboard-driven**: support keyboard navigation throughout.
6. **Privacy-focused**: no network calls, no crash reporting, no usage tracking.

## CitrusDrop Feature Inventory

### Milestone 1: Foundation (current)
- [x] Dark desktop interface with CitrusDrop branding
- [x] File selection via drag-and-drop and file dialog
- [x] Image conversion: PNG, JPG, WEBP, BMP, TIFF (Pillow)
- [x] Audio/video conversion: MP3, WAV, OGG, MP4, WEBM, MKV (FFmpeg)
- [x] Radial quick-format picker (in-app, grid-based prototype)
- [x] Safe output naming (unique_path, no silent overwrites)
- [x] Background worker thread for conversions
- [x] Input validation (image → audio rejected, etc.)
- [x] Output to `~/CitrusDrop`
- [x] Progress bar and error reporting
- [x] Basic test suite

### Milestone 2: Expanded Formats
- [ ] HEIC, AVIF input (via pillow-heif / pillow-avif-plugin)
- [ ] SVG input (via cairosvg or librsvg)
- [ ] Additional audio: M4A, FLAC, Opus, AIFF, WMA
- [ ] Additional video: MOV, AVI, WMV, GIF output
- [ ] Audio extraction from video (MP3 export)

### Milestone 3: PDF & Documents
- [ ] PDF merge and page organization (pypdf)
- [ ] PDF to images (pdf2image / poppler)
- [ ] Document conversions via LibreOffice headless (DOCX, TXT, Markdown, EPUB)
- [ ] Spreadsheet conversions (XLSX, ODS, CSV, TSV)
- [ ] Subtitle conversions (SRT ↔ VTT)

### Milestone 4: Radial Menu & Interaction
- [ ] True radial/fan menu with arc layout
- [ ] Modifier-key switching (Shift → convert, Ctrl → tools, Alt → actions)
- [ ] File-type-adaptive menu (show only applicable formats/tools)
- [ ] Keyboard navigation in radial menu (arrow keys, Enter, Escape)
- [ ] Animation and visual polish

### Milestone 5: File Tools
- [ ] Image compression (quality slider + Pillow/FFmpeg)
- [ ] Image crop, resize
- [ ] Video trim, crop, speed adjustment
- [ ] Audio trim, normalization
- [ ] Metadata viewer/editor

### Milestone 6: File Actions
- [ ] Copy / Move with folder picker
- [ ] Copy full file path to clipboard
- [ ] Open containing folder in Nautilus
- [ ] Open directory in terminal
- [ ] Floating file shelf (if technically practical on Wayland)

### Milestone 7: Archives & Settings
- [ ] ZIP, TAR, GZIP creation and extraction
- [ ] Settings window (output folder, keyboard bindings, conversion preferences)
- [ ] Batch processing improvements
- [ ] Operation log and history

### Milestone 8: Desktop Integration
- [ ] `.desktop` file for Ubuntu launcher
- [ ] Nautilus file-manager integration (right-click actions)
- [ ] XDG Desktop Portal integration where applicable
- [ ] System notifications for completed conversions

## Acceptance Criteria (All Milestones)

- Application launches with documented commands
- Existing working features remain available after each milestone
- Output files are never silently overwritten
- Errors are displayed clearly to non-expert users
- Tests pass; no regressions
- No unrelated features or speculative dependencies added
- Wayland limitations documented honestly

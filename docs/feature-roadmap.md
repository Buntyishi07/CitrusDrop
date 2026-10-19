# CitrusDrop — Feature Roadmap

## Implementation Order and Dependencies

Each milestone builds on the previous one. A milestone is complete when its features are tested, documented, and do not regress prior milestones.

---

## Milestone 1: Foundation ✅ (current)

**Goal**: Working vertical slice — launch, add files, convert images and media, safe output.

| Feature | Status | Dependencies |
|---------|--------|--------------|
| Dark desktop UI with CitrusDrop branding | ✅ Done | PySide6 |
| File selection (drag-and-drop + dialog) | ✅ Done | PySide6 |
| Image conversion (PNG, JPG, WEBP, BMP, TIFF) | ✅ Done | Pillow |
| Audio/video conversion (MP3, WAV, OGG, MP4, WEBM, MKV) | ✅ Done | FFmpeg |
| Grid-based radial format picker | ✅ Done | PySide6 |
| Safe output naming (no overwrites) | ✅ Done | — |
| Background worker thread | ✅ Done | QThread |
| Input format validation | ✅ Done | — |
| Unit & integration tests | ✅ Done | pytest, Pillow |
| README with setup instructions | ✅ Done | — |

**Acceptance**: App launches, converts a PNG to JPG, output appears in ~/CitrusDrop without overwriting existing files, tests pass.

---

## Milestone 2: Expanded Format Coverage

**Goal**: Match the core conversion breadth across image, audio, and video categories.

| Feature | Dependency | Risk |
|---------|-----------|------|
| HEIC/HEIF input | `pillow-heif` | Needs libheif system library |
| AVIF input | `pillow-avif-plugin` or Pillow 10.1+ | May need libaom |
| SVG input (rasterize) | `cairosvg` | Needs libcairo2-dev |
| M4A, FLAC, Opus, AIFF, WMA audio | FFmpeg (already present) | Codec-dependent |
| MOV, AVI, WMV video | FFmpeg | Codec-dependent |
| GIF output from video | FFmpeg | Quality/size tradeoffs |
| Audio extraction from video (MP3 export) | FFmpeg | — |

**Acceptance**: Each new format has a test. Unsupported codecs produce clear errors. No false claims.

---

## Milestone 3: PDF & Document Conversion

**Goal**: Add document-format conversions using reliable local tools.

| Feature | Dependency | Risk |
|---------|-----------|------|
| PDF merge / split / page reorder | `pypdf` | Pure Python, low risk |
| PDF → images (PNG, JPG) | `pdf2image` + poppler-utils | System dependency |
| Image → PDF export | Pillow + `pypdf` | — |
| DOCX / TXT / Markdown / EPUB conversions | LibreOffice headless | Heavy system dependency |
| XLSX / ODS / CSV / TSV conversions | LibreOffice headless | — |
| PPT/PPTX → PDF / images | LibreOffice headless | — |
| SRT ↔ VTT subtitle conversion | Pure Python parser | Low risk |

**Acceptance**: PDF merge works with 2+ files. Each conversion direction tested. LibreOffice is optional — app gracefully degrades if not installed.

---

## Milestone 4: Radial Menu Evolution

**Goal**: Replace the grid picker with a true radial/arc menu inspired by Tangerine's interaction model.

| Feature | Dependency | Risk |
|---------|-----------|------|
| Arc layout with format items around center | QPainter custom widget | Complex custom painting |
| File-type-adaptive menu | Classification from converter.py | — |
| Modifier key switching (Shift/Ctrl/Alt) | Qt key events | Wayland modifier restrictions |
| Keyboard navigation (arrows, Enter, Escape) | — | — |
| Smooth open/close animation | QPropertyAnimation | — |
| Three menu modes: Convert / Tools / Actions | — | UX design needed |

**Acceptance**: Radial menu opens, shows only relevant formats for the file type, supports keyboard navigation.

---

## Milestone 5: File Tools

**Goal**: Add focused editing tools that open in separate dialog windows.

| Feature | Dependency | Risk |
|---------|-----------|------|
| Image compress (quality slider) | Pillow | — |
| Image crop / resize | Pillow | Custom crop widget |
| Image annotation (text, arrows) | QPainter overlay | Complex UI |
| Video trim (start/end time) | FFmpeg `-ss` / `-to` | — |
| Video crop | FFmpeg crop filter | — |
| Video speed adjustment | FFmpeg `setpts` filter | — |
| Audio trim | FFmpeg | — |
| Audio normalization | FFmpeg `loudnorm` filter | — |
| Metadata viewer/editor | Pillow EXIF / FFprobe | — |
| Image redaction (blur region) | Pillow | — |

**Acceptance**: Each tool opens with preview, saves a new copy, preserves original.

---

## Milestone 6: File Actions

**Goal**: Provide quick file operations accessible from the radial menu.

| Feature | Dependency | Risk |
|---------|-----------|------|
| Copy file to chosen folder | `shutil.copy2` | — |
| Move file to chosen folder | `shutil.move` | — |
| Copy full file path to clipboard | Qt clipboard API | — |
| Open containing folder in Nautilus | `xdg-open` | — |
| Open directory in terminal | `gnome-terminal` / `xterm` | Terminal detection |
| Floating file shelf | QWidget popup | Wayland window constraints |

**Acceptance**: Each action works from the radial menu. No macOS-specific features claimed.

---

## Milestone 7: Archives & Settings

| Feature | Dependency | Risk |
|---------|-----------|------|
| ZIP creation and extraction | `zipfile` (stdlib) | Path traversal prevention |
| TAR / GZIP creation | `tarfile` (stdlib) | Path traversal prevention |
| Settings dialog | PySide6 | — |
| Configurable output folder | — | — |
| Keyboard binding customization | — | — |
| Operation log / history | — | — |
| Batch processing improvements | — | — |

---

## Milestone 8: Desktop Integration

| Feature | Dependency | Risk |
|---------|-----------|------|
| `.desktop` file for launcher | — | — |
| Nautilus right-click actions | `nautilus-python` or script actions | Nautilus version-dependent |
| XDG Desktop Portal integration | `python-dbus` / Portal API | Compositor-dependent |
| System tray / notification area | PySide6 QSystemTrayIcon | May not work on all DEs |
| System notifications on completion | `notify-send` or Qt | — |

---

## Technical Risks Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wayland blocks global drag interception | High | In-app DnD first; assess portal APIs later |
| LibreOffice headless is heavy and slow | Medium | Make it optional; graceful degradation |
| HEIC/AVIF require system libraries | Medium | Document optional dependencies; skip if unavailable |
| Radial menu custom painting is complex | Medium | Iterate from grid → arc; don't block other features |
| FFmpeg codec support varies by build | Low | Test common codecs; surface FFmpeg errors clearly |
| Archive path traversal | Medium | Use `zipfile` with path validation; never extract blindly |

# CitrusDrop — Current Project Status

Last updated: 2026-10-19

## 1. Architecture & Important File Paths

- **Repository Root**: `/home/bunty/Downloads/CitrusDrop_Ubuntu_Prototype/CitrusDrop`
- **UI Layer**: [`main.py`](../main.py) — `MainWindow`, `DropZone`, `RadialPicker` (modal grid), `ConvertWorker` (`QThread`)
- **Conversion Engine**: [`converter.py`](../converter.py) — Pure Python / Pillow / FFmpeg CLI utilities. No Qt dependencies.
- **Dependencies**: [`requirements.txt`](../requirements.txt) — PySide6, Pillow
- **Test Suite**: [`tests/test_converter.py`](../tests/test_converter.py) — 37 automated tests
- **Project Guidance**: [`AGENTS.md`](../AGENTS.md), [`README.md`](../README.md)
- **Detailed Specifications**:
  - [Product Specification](product-spec.md)
  - [System Architecture](architecture.md)
  - [Feature Roadmap](feature-roadmap.md)
  - [Wayland Compatibility Analysis](wayland-compatibility.md)

## 2. Working Features

- **Desktop UI**: Dark-themed PySide6 application window with drop zone, file list, and progress indicator.
- **File Input**: In-app drag-and-drop from Nautilus/GNOME and "Choose files" standard dialog.
- **Image Conversion**: PNG, JPG, WEBP, BMP, TIFF (via Pillow with RGBA alpha flattening for JPEG).
- **Audio/Video Conversion**: MP3, WAV, OGG, MP4, WEBM, MKV (via FFmpeg CLI subprocess).
- **Format Picker**: Modal 2x3 grid picker dialog (PNG, JPG, WEBP, WAV, MP3, MP4).
- **Collision-Safe Outputs**: Writes to `~/CitrusDrop/` using `unique_path()` (auto-appends `_1`, `_2`, …) and FFmpeg `-n` flag to prevent overwrites.
- **Async Execution**: `ConvertWorker` runs file jobs on a background `QThread` without freezing the Qt main loop.
- **Validation**: `validate_conversion()` checks category matching (e.g., blocks image → video conversion).

## 3. Incomplete & Planned Features

- Extended media format coverage (FLAC, M4A, Opus, AVI, MOV, HEIC, AVIF, SVG) (Milestone 2).
- PDF operations and document conversion (Milestone 3).
- Custom `QPainter` radial/arc menu widget with keyboard modifier switching (Milestone 4).
- Dedicated file editing tools: compression slider, crop/resize, video/audio trimmer (Milestone 5).
- Batch presets and action macros (Milestone 6).
- Packaging and desktop distribution (Flatpak / .deb) (Milestone 7).

## 4. Commands

### Environment Setup
```bash
cd /home/bunty/Downloads/CitrusDrop_Ubuntu_Prototype/CitrusDrop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

### Running Tests
```bash
cd /home/bunty/Downloads/CitrusDrop_Ubuntu_Prototype/CitrusDrop
source .venv/bin/activate
python -m pytest tests/ -v
```

### Syntax Validation
```bash
cd /home/bunty/Downloads/CitrusDrop_Ubuntu_Prototype/CitrusDrop
source .venv/bin/activate
python -m py_compile main.py converter.py tests/test_converter.py
```

### Launching the Application
```bash
cd /home/bunty/Downloads/CitrusDrop_Ubuntu_Prototype/CitrusDrop
source .venv/bin/activate
python main.py
```

## 5. Latest Test Results

- **Executed during this task (2026-10-19 14:39:35)**:
  - `37 passed in 0.05s` (`pytest tests/ -v`)
  - Syntax check: `main.py`, `converter.py`, and `tests/test_converter.py` passed compilation with zero warnings or errors.
- **Historical baseline**: 37 tests passing since Milestone 1 completion.

## 6. Known Technical Limitations

- **Wayland Security Constraints**: Global desktop drag interception and global hotkey capture are blocked by Wayland compositor security; drag-and-drop is confined to the application window.
- **Format Picker UI**: Currently a grid dialog rather than a true animated radial arc menu.
- **External CLI Dependency**: FFmpeg must be installed locally on Ubuntu (`sudo apt install ffmpeg`).
- **No Document Support Yet**: PDF and office documents cannot yet be converted or processed.

## 7. Current Milestone & Next Single Task

- **Current Milestone**: Milestone 1 (Foundation) — complete.
- **Next Task**: Milestone 2, Task 2.1 — Add expanded audio format support (`flac`, `m4a`, `opus`) to `converter.py`.
- **Acceptance Criteria**:
  1. `converter.py` recognizes `.flac`, `.m4a`, and `.opus` in `AUDIO_EXTENSIONS` and `AUDIO_FORMATS`.
  2. Input validation permits valid media conversions to/from these formats.
  3. Tests added to `tests/test_converter.py` verifying classification, validation, and FFmpeg conversion.
  4. All existing and new tests pass without regressions.

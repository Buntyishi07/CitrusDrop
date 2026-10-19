# CitrusDrop — Architecture

## System Context

```
┌──────────────────────────────────────────────────┐
│                  Ubuntu Desktop                   │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │              CitrusDrop (PySide6)            │  │
│  │                                              │  │
│  │  ┌──────────┐  ┌───────────┐  ┌───────────┐ │  │
│  │  │   UI     │  │  Converter │  │  Workers  │ │  │
│  │  │  Layer   │→ │   Layer    │← │  (QThread)│ │  │
│  │  └──────────┘  └─────┬─────┘  └───────────┘ │  │
│  │                      │                        │  │
│  │           ┌──────────┼──────────┐             │  │
│  │           ▼          ▼          ▼             │  │
│  │       ┌──────┐  ┌────────┐  ┌──────────┐    │  │
│  │       │Pillow│  │ FFmpeg │  │ Future:  │    │  │
│  │       │      │  │  (CLI) │  │ pypdf,   │    │  │
│  │       └──────┘  └────────┘  │ LO, etc. │    │  │
│  │                              └──────────┘    │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  Output: ~/CitrusDrop/                            │
└──────────────────────────────────────────────────┘
```

## Module Responsibilities

### `main.py` — UI Layer
- **MainWindow**: application chrome, file list, format picker, progress, status
- **DropZone**: drag-and-drop target and file browser button
- **RadialPicker**: grid-based format picker dialog (prototype; will evolve to arc layout)
- **ConvertWorker** (QThread): runs conversion jobs off the main thread
- Owns all Qt widget code. Does not contain conversion logic.

### `converter.py` — Conversion Layer
- Format classification: `classify_input()`, `classify_output()`
- Validation: `validate_conversion()` — rejects nonsensical conversions (image → audio)
- Safe output naming: `unique_path()` — never overwrites existing files
- Image conversion: `convert_image()` — wraps Pillow
- Media conversion: `convert_media()` — wraps FFmpeg CLI (no `shell=True`)
- Utilities: `human_size()` — human-readable file sizes
- **No Qt dependency.** Independently testable.

### `tests/test_converter.py` — Test Suite
- Unit tests for pure functions (human_size, unique_path, classify, validate)
- Integration tests for image conversion (Pillow)
- Run with: `python -m pytest tests/ -v`

## Key Design Decisions

### 1. Separation of conversion from UI
The converter module has zero Qt imports. This enables:
- Independent unit testing without a display server
- Future reuse from CLI tools or other interfaces
- Clear responsibility boundaries

### 2. Worker thread via QThread
Conversion runs in a `ConvertWorker(QThread)` to avoid blocking the UI.
Communication uses Qt signals:
- `progress(current, total)` — updates progress bar
- `file_done(name, success, message)` — per-file status
- `finished(succeeded, failed_list)` — final summary

Why not `QRunnable`/`QThreadPool`: a single sequential worker is simpler and sufficient for the current use case. Parallel conversion can be added later by spawning multiple workers or using a pool.

### 3. Safe output naming
`unique_path(dest)` appends `_1`, `_2`, etc. if the target exists. FFmpeg is called with `-n` (never overwrite). This is a deliberate choice to prevent data loss at the cost of accumulating numbered copies.

### 4. Input validation
Files are classified by extension before conversion. Incompatible combinations (e.g., `.png` → MP3) are rejected with a clear message before any processing begins.

### 5. FFmpeg invocation
- Uses `subprocess.run()` with a list of arguments (no `shell=True`)
- Passes `-n` (refuse to overwrite)
- Captures stderr for error reporting
- 600-second timeout prevents hangs on corrupt files
- FFmpeg path resolved via `shutil.which("ffmpeg")`

### 6. No global drag interception
The in-app drag-and-drop uses Qt's built-in DnD mechanism, which works on Wayland. Global drag interception (intercepting drags from Nautilus to other apps) is not possible on Wayland compositors without compositor-level extensions. See `docs/wayland-compatibility.md`.

## Dependency Graph

```
CitrusDrop
├── Python 3.10+
├── PySide6 >= 6.5      (Qt Widgets, signals, QThread)
├── Pillow >= 10.0       (image conversion)
├── FFmpeg               (system package, audio/video)
└── pytest               (dev dependency, testing)

Future:
├── pypdf                (PDF merge/split)
├── pdf2image + poppler  (PDF → images)
├── cairosvg             (SVG → raster)
├── pillow-heif          (HEIC support)
├── LibreOffice headless (document conversions)
└── python-magic         (MIME-based file identification)
```

## File System Layout

```
CitrusDrop/
├── main.py              # UI layer (PySide6 application)
├── converter.py         # Conversion logic (no Qt dependency)
├── requirements.txt     # Python dependencies
├── README.md            # Setup and usage instructions
├── tests/
│   └── test_converter.py
├── docs/
│   ├── product-spec.md
│   ├── architecture.md
│   ├── feature-roadmap.md
│   └── wayland-compatibility.md
└── .venv/               # Python virtual environment (not committed)
```

## Data Flow

```
User drops files
       │
       ▼
DropZone.dropEvent() → MainWindow.add_files()
       │                      │
       │              stores paths in self.files[]
       │              updates file list widget
       │
User clicks "Convert files"
       │
       ▼
MainWindow.convert_files()
       │
       ├── Validates: files selected? worker idle?
       ├── Creates output directory ~/CitrusDrop/
       ├── Disables UI controls
       └── Spawns ConvertWorker(QThread)
              │
              ├── For each file:
              │   ├── validate_conversion(src, fmt)
              │   ├── unique_path(output_dir / stem.fmt)
              │   ├── convert_image() or convert_media()
              │   └── emit progress signal
              │
              └── emit finished signal
                     │
                     ▼
              MainWindow._on_finished()
              Re-enables controls, shows summary dialog
```

## Security Considerations

- **No shell injection**: all subprocess calls use argument lists
- **No silent overwrites**: unique_path + FFmpeg `-n` flag
- **No network access**: no HTTP calls, no telemetry, no crash reporting
- **No arbitrary file writes**: output is always within `~/CitrusDrop/`
- **Timeout on FFmpeg**: 600 seconds prevents infinite hangs
- **Future archives**: must use safe extraction (no path traversal via `zipfile` extractall with checks)

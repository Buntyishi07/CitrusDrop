# CitrusDrop — Ubuntu desktop file converter

CitrusDrop is an original, local-first file converter for Ubuntu, inspired by the general workflow of [Tangerine for macOS](https://tangerineformac.com/). It uses original branding and independently implemented code. It does not contain Tangerine's source code or assets.

All processing happens locally on your machine. Nothing is uploaded.

## Quick start

### 1. Check your environment

```bash
echo "$XDG_SESSION_TYPE"   # expected: wayland
python3 --version           # expected: Python 3.10+
```

### 2. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg
```

### 3. Set up and launch

Open a terminal in the `CitrusDrop` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

> If Ubuntu reports that the system Python environment is *externally managed*, that is expected. Use the virtual-environment commands above rather than `sudo pip`.

### 4. Run tests

```bash
source .venv/bin/activate
python -m pip install pytest
python -m pytest tests/ -v
```

## Current features

- **Dark desktop interface** with original CitrusDrop branding
- **Drag-and-drop files** into the app, or use the "Choose files" button
- **Image conversion**: PNG, JPG, WEBP, BMP, TIFF, HEIC/HEIF, AVIF (via Pillow and pillow-heif)
- **Audio/video conversion**: MP3, WAV, OGG, MP4, WEBM, MKV (via FFmpeg)
- **Radial quick-format picker** — select a format quickly from a grid dialog
- **Safe output naming** — files are never silently overwritten; `_1`, `_2`, etc. are appended
- **Input validation** — image-to-audio and similar mismatches are caught before conversion
- **Background worker thread** — the UI stays responsive during conversion
- **Progress bar and error reporting** — clear feedback on success and failure
- Output saved to `~/CitrusDrop/`

## Supported formats

### Image (via Pillow & pillow-heif)

| Input | Output |
|-------|--------|
| PNG, JPG/JPEG, WEBP, BMP, TIFF, GIF, HEIC, HEIF, HEIFS, HIF, AVIF, AVIFS | PNG, JPG, WEBP, BMP, TIFF |

> HEIC/HEIF decoding is powered by `pillow-heif`. AVIF decoding is supported natively via Pillow. All image inputs convert to any of the 5 supported image output formats with proper transparency handling when converting to JPEG.

### Audio/Video (via FFmpeg)

| Input | Output |
|-------|--------|
| MP3, WAV, OGG, FLAC, AAC, M4A, and others FFmpeg supports | MP3, WAV, OGG |
| MP4, WEBM, MKV, AVI, MOV, and others FFmpeg supports | MP4, WEBM, MKV |

> Actual codec support depends on your FFmpeg build. The app will show a clear error if a specific conversion fails.

## Project structure

```
CitrusDrop/
├── main.py              # UI layer (PySide6 application)
├── converter.py         # Conversion logic (no Qt dependency)
├── requirements.txt     # Python dependencies (PySide6, Pillow, pillow-heif)
├── README.md            # This file
├── tests/
│   └── test_converter.py
└── docs/
    ├── current-status.md
    ├── product-spec.md
    ├── architecture.md
    ├── feature-roadmap.md
    └── wayland-compatibility.md
```

## Current limitations

- **PDF, document, spreadsheet, and subtitle conversions** are not yet implemented.
- **Advanced file tools** (crop, trim, compress, etc.) are planned but not yet available.
- **The radial picker** is an in-app grid-based prototype, not a global overlay.
- **Global drag interception** is not possible on Wayland. The app uses in-app drag-and-drop. See `docs/wayland-compatibility.md`.
- **SVG input** requires CairoSVG, not yet integrated.
- Conversion success depends on the input codec and your FFmpeg build.

## Troubleshooting

### `ModuleNotFoundError: No module named 'PySide6'`

Activate the virtual environment and install dependencies:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### `ModuleNotFoundError: No module named 'PIL'`

```bash
source .venv/bin/activate
python -m pip install Pillow
```

### FFmpeg conversion fails

Verify FFmpeg is installed:

```bash
ffmpeg -version
```

The input file may use a codec that cannot be converted to the selected output format. Read the error message shown by the app.

### App does not open

Run it from a terminal to see the full traceback:

```bash
source .venv/bin/activate
python main.py
```

### Wayland issues

```bash
# Force Wayland backend
QT_QPA_PLATFORM=wayland python main.py

# Force X11 backend (fallback)
QT_QPA_PLATFORM=xcb python main.py
```

## Development

### Running tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

### Syntax check

```bash
python -m py_compile main.py
python -m py_compile converter.py
```

## License

This project is independently developed. It is not affiliated with or endorsed by Tangerine or Leap Studio.

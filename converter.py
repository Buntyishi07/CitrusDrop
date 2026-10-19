"""
CitrusDrop — converter utilities.

All file-conversion logic lives here so the UI module stays small and the
functions are independently testable.  Nothing in this module touches Qt.
"""

import shutil
import subprocess
from pathlib import Path

# ── Format classification ────────────────────────────────────────────────

IMAGE_FORMATS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
AUDIO_FORMATS = {"mp3", "wav", "ogg"}
VIDEO_FORMATS = {"mp4", "webm", "mkv"}
MEDIA_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS

ALL_OUTPUT_FORMATS = IMAGE_FORMATS | MEDIA_FORMATS

# Rough input-format heuristics used for validation only.
IMAGE_EXTENSIONS = IMAGE_FORMATS | {"gif", "ico", "svg", "heic", "heif", "avif"}
AUDIO_EXTENSIONS = AUDIO_FORMATS | {"flac", "aac", "wma", "m4a", "opus"}
VIDEO_EXTENSIONS = VIDEO_FORMATS | {"avi", "mov", "flv", "wmv", "ts", "m4v", "3gp"}


def classify_input(path: Path) -> str:
    """Return 'image', 'audio', 'video', or 'unknown' based on extension."""
    ext = path.suffix.lstrip(".").lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def classify_output(fmt: str) -> str:
    """Return 'image' or 'media' based on the target format string."""
    fmt = fmt.lower()
    if fmt in IMAGE_FORMATS:
        return "image"
    if fmt in MEDIA_FORMATS:
        return "media"
    return "unknown"


def validate_conversion(src: Path, fmt: str) -> str | None:
    """Return a human-readable error string if *src* → *fmt* is invalid, else None."""
    in_kind = classify_input(src)
    out_kind = classify_output(fmt)

    if out_kind == "unknown":
        return f"'{fmt.upper()}' is not a supported output format."

    if in_kind == "image" and out_kind == "media":
        return (
            f"'{src.name}' looks like an image. "
            f"It cannot be converted to {fmt.upper()} (audio/video)."
        )
    if in_kind in ("audio", "video") and out_kind == "image":
        return (
            f"'{src.name}' looks like a media file. "
            f"It cannot be converted to {fmt.upper()} (image)."
        )
    return None


# ── Safe output filename ─────────────────────────────────────────────────

def unique_path(dest: Path) -> Path:
    """Return *dest* if it doesn't exist, otherwise append _1, _2, … until unique.

    >>> from pathlib import PurePosixPath as P
    >>> # When file doesn't exist, returns the same path (tested via real filesystem below)
    """
    if not dest.exists():
        return dest
    stem = dest.stem
    parent = dest.parent
    suffix = dest.suffix
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# ── Image conversion ─────────────────────────────────────────────────────

def convert_image(src: Path, dest: Path, fmt: str) -> None:
    """Convert an image via Pillow.  *dest* must already be a safe path."""
    from PIL import Image

    with Image.open(src) as img:
        if fmt in {"jpg", "jpeg"}:
            if img.mode in ("RGBA", "LA", "P"):
                rgba = img.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                img = background
            else:
                img = img.convert("RGB")
            img.save(dest, "JPEG", quality=92, optimize=True)
        else:
            pil_fmt = {"png": "PNG", "webp": "WEBP", "bmp": "BMP", "tiff": "TIFF"}[fmt]
            img.save(dest, pil_fmt)


# ── Audio / video conversion ─────────────────────────────────────────────

def convert_media(src: Path, dest: Path) -> None:
    """Convert a media file via FFmpeg.  *dest* must already be a safe path.

    Does NOT pass ``-y``; the caller is responsible for providing a non-existing
    *dest* via :func:`unique_path`.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg is not installed.\n"
            "Install it with:  sudo apt install ffmpeg"
        )
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error",
         "-n",  # never overwrite
         "-i", str(src), str(dest)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        # Surface the last 500 chars of stderr so the message stays readable.
        err = (proc.stderr.strip() or "FFmpeg conversion failed.")
        raise RuntimeError(err[-500:])


# ── Human-readable helpers ────────────────────────────────────────────────

def human_size(size: int) -> str:
    """Return a human-friendly file size string."""
    if size < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    n = float(size)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(n)} B"
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{size} B"  # unreachable but safe

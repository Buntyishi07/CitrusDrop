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

# Supported extended image inputs
HEIF_EXTENSIONS = {"heic", "heics", "heif", "heifs", "hif"}
AVIF_EXTENSIONS = {"avif", "avifs"}

# Rough input-format heuristics used for validation only.
IMAGE_EXTENSIONS = (
    IMAGE_FORMATS
    | {"gif", "ico", "svg"}
    | HEIF_EXTENSIONS
    | AVIF_EXTENSIONS
)
AUDIO_EXTENSIONS = AUDIO_FORMATS | {"flac", "aac", "wma", "m4a", "opus"}
VIDEO_EXTENSIONS = VIDEO_FORMATS | {"avi", "mov", "flv", "wmv", "ts", "m4v", "3gp"}


# ── Decoder registration & availability ───────────────────────────────────

_HEIF_REGISTERED = False


def register_heif_support() -> bool:
    """Register pillow_heif opener with Pillow if available.

    Returns True if registration succeeded or was already active.
    """
    global _HEIF_REGISTERED
    if _HEIF_REGISTERED:
        return True
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        _HEIF_REGISTERED = True
        return True
    except (ImportError, Exception):
        return False


def is_heif_supported() -> bool:
    """Return True if HEIC/HEIF decoding is available."""
    return register_heif_support()


def is_avif_supported() -> bool:
    """Return True if AVIF decoding is available in the current Pillow environment."""
    try:
        from PIL import features

        return bool(features.check("avif"))
    except Exception:
        return False


# Automatically attempt plugin registration on module load
register_heif_support()


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
    from PIL import Image, UnidentifiedImageError

    ext = src.suffix.lstrip(".").lower()

    if ext in HEIF_EXTENSIONS and not is_heif_supported():
        raise RuntimeError(
            f"Cannot open '{src.name}': HEIC/HEIF decoding is not available.\n"
            "Install the decoder with:  pip install pillow-heif"
        )
    if ext in AVIF_EXTENSIONS and not is_avif_supported():
        raise RuntimeError(
            f"Cannot open '{src.name}': AVIF decoding is not supported by the installed Pillow version."
        )

    # Ensure HEIF plugins are registered before opening
    if ext in HEIF_EXTENSIONS:
        register_heif_support()

    try:
        with Image.open(src) as img:
            img.load()

            if fmt in {"jpg", "jpeg"}:
                # Flatten alpha channel over a white background for JPEGs
                if img.mode in ("RGBA", "LA", "PA") or (
                    img.mode == "P" and "transparency" in img.info
                ):
                    rgba = img.convert("RGBA")
                    background = Image.new("RGB", rgba.size, (255, 255, 255))
                    background.paste(rgba, mask=rgba.getchannel("A"))
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(dest, "JPEG", quality=92, optimize=True)
            else:
                # Mode adaptations for specific target formats
                if img.mode == "CMYK":
                    img = img.convert("RGB")
                elif fmt == "bmp" and img.mode in ("LA", "PA"):
                    img = img.convert("RGBA")

                pil_fmt = {
                    "png": "PNG",
                    "webp": "WEBP",
                    "bmp": "BMP",
                    "tiff": "TIFF",
                }[fmt]
                img.save(dest, pil_fmt)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise RuntimeError(
            f"Cannot decode image '{src.name}': file is corrupted or in an unsupported format ({exc})."
        ) from exc


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

"""
Tests for CitrusDrop converter utilities.

Run with:  python -m pytest tests/ -v
"""

import tempfile
from pathlib import Path

import pytest

import converter


# ── human_size ────────────────────────────────────────────────────────────

class TestHumanSize:
    def test_zero(self):
        assert converter.human_size(0) == "0 B"

    def test_bytes(self):
        assert converter.human_size(512) == "512 B"

    def test_kilobytes(self):
        assert converter.human_size(1024) == "1.0 KB"

    def test_megabytes(self):
        assert converter.human_size(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self):
        assert converter.human_size(3 * 1024**3) == "3.0 GB"

    def test_terabytes(self):
        assert converter.human_size(2 * 1024**4) == "2.0 TB"

    def test_negative(self):
        assert converter.human_size(-1) == "0 B"


# ── unique_path ───────────────────────────────────────────────────────────

class TestUniquePath:
    def test_returns_original_when_no_conflict(self, tmp_path):
        p = tmp_path / "output.png"
        assert converter.unique_path(p) == p

    def test_appends_1_on_first_conflict(self, tmp_path):
        p = tmp_path / "output.png"
        p.touch()
        result = converter.unique_path(p)
        assert result == tmp_path / "output_1.png"
        assert not result.exists()

    def test_increments_counter(self, tmp_path):
        p = tmp_path / "output.png"
        p.touch()
        (tmp_path / "output_1.png").touch()
        (tmp_path / "output_2.png").touch()
        result = converter.unique_path(p)
        assert result == tmp_path / "output_3.png"

    def test_preserves_extension(self, tmp_path):
        p = tmp_path / "video.mkv"
        p.touch()
        result = converter.unique_path(p)
        assert result.suffix == ".mkv"
        assert result.stem == "video_1"


# ── classify_input ────────────────────────────────────────────────────────

class TestClassifyInput:
    @pytest.mark.parametrize("ext,expected", [
        (".png", "image"), (".JPG", "image"), (".webp", "image"),
        (".gif", "image"), (".heic", "image"),
        (".mp3", "audio"), (".wav", "audio"), (".flac", "audio"),
        (".mp4", "video"), (".mkv", "video"), (".avi", "video"),
        (".xyz", "unknown"), (".txt", "unknown"),
    ])
    def test_classification(self, ext, expected):
        assert converter.classify_input(Path(f"file{ext}")) == expected


# ── classify_output ───────────────────────────────────────────────────────

class TestClassifyOutput:
    def test_image(self):
        assert converter.classify_output("png") == "image"
        assert converter.classify_output("JPG") == "image"

    def test_media(self):
        assert converter.classify_output("mp3") == "media"
        assert converter.classify_output("mp4") == "media"

    def test_unknown(self):
        assert converter.classify_output("pdf") == "unknown"


# ── validate_conversion ──────────────────────────────────────────────────

class TestValidateConversion:
    def test_valid_image_to_image(self):
        assert converter.validate_conversion(Path("photo.png"), "jpg") is None

    def test_valid_video_to_video(self):
        assert converter.validate_conversion(Path("clip.mp4"), "mkv") is None

    def test_image_to_audio_rejected(self):
        err = converter.validate_conversion(Path("photo.png"), "mp3")
        assert err is not None
        assert "image" in err.lower()

    def test_audio_to_image_rejected(self):
        err = converter.validate_conversion(Path("song.mp3"), "png")
        assert err is not None
        assert "media" in err.lower()

    def test_unsupported_format(self):
        err = converter.validate_conversion(Path("file.txt"), "pdf")
        assert err is not None
        assert "not a supported" in err.lower()

    def test_unknown_input_to_media_is_allowed(self):
        # Unknown input + media output: let FFmpeg decide.
        assert converter.validate_conversion(Path("file.xyz"), "mp4") is None


# ── convert_image (integration, needs Pillow) ────────────────────────────

class TestConvertImage:
    def _make_image(self, tmp_path, name="test.png", mode="RGBA"):
        from PIL import Image
        img = Image.new(mode, (10, 10), color=(255, 165, 67, 128))
        p = tmp_path / name
        img.save(p)
        return p

    def test_png_to_jpg(self, tmp_path):
        src = self._make_image(tmp_path, mode="RGBA")
        dest = tmp_path / "out.jpg"
        converter.convert_image(src, dest, "jpg")
        assert dest.exists()
        assert dest.stat().st_size > 0

    def test_png_to_webp(self, tmp_path):
        src = self._make_image(tmp_path)
        dest = tmp_path / "out.webp"
        converter.convert_image(src, dest, "webp")
        assert dest.exists()

    def test_png_to_bmp(self, tmp_path):
        src = self._make_image(tmp_path)
        dest = tmp_path / "out.bmp"
        converter.convert_image(src, dest, "bmp")
        assert dest.exists()

    def test_rgb_to_jpg(self, tmp_path):
        src = self._make_image(tmp_path, mode="RGB")
        dest = tmp_path / "out.jpg"
        converter.convert_image(src, dest, "jpg")
        assert dest.exists()

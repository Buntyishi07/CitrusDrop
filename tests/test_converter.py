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
        (".gif", "image"), (".heic", "image"), (".heif", "image"),
        (".heifs", "image"), (".hif", "image"), (".avif", "image"),
        (".avifs", "image"),
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

    def test_valid_heic_to_image(self):
        assert converter.validate_conversion(Path("photo.heic"), "png") is None
        assert converter.validate_conversion(Path("image.heif"), "webp") is None
        assert converter.validate_conversion(Path("shot.hif"), "jpg") is None

    def test_valid_avif_to_image(self):
        assert converter.validate_conversion(Path("graphic.avif"), "png") is None
        assert converter.validate_conversion(Path("graphic.avifs"), "tiff") is None

    def test_valid_video_to_video(self):
        assert converter.validate_conversion(Path("clip.mp4"), "mkv") is None

    def test_image_to_audio_rejected(self):
        err = converter.validate_conversion(Path("photo.png"), "mp3")
        assert err is not None
        assert "image" in err.lower()

    def test_heic_to_audio_rejected(self):
        err = converter.validate_conversion(Path("image.heic"), "wav")
        assert err is not None
        assert "image" in err.lower()

    def test_avif_to_video_rejected(self):
        err = converter.validate_conversion(Path("graphic.avif"), "mp4")
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


# ── HEIF & AVIF Decoding & Conversion (Milestone 2A) ─────────────────────

class TestHeifAvifConversion:
    def _make_heif_fixture(self, tmp_path, filename="sample.heic", mode="RGB"):
        from PIL import Image
        if not converter.is_heif_supported():
            pytest.skip("HEIF/HEIC support not available in environment")
        try:
            img = Image.new(mode, (16, 16), color=(255, 128, 0, 180) if "A" in mode else (255, 128, 0))
            p = tmp_path / filename
            img.save(p, format="HEIF")
            return p
        except Exception as exc:
            pytest.skip(f"HEIF fixture generation failed: {exc}")

    def _make_avif_fixture(self, tmp_path, filename="sample.avif", mode="RGB"):
        from PIL import Image
        if not converter.is_avif_supported():
            pytest.skip("AVIF support not available in Pillow environment")
        try:
            img = Image.new(mode, (16, 16), color=(0, 180, 255, 200) if "A" in mode else (0, 180, 255))
            p = tmp_path / filename
            img.save(p, format="AVIF")
            return p
        except Exception as exc:
            pytest.skip(f"AVIF fixture generation failed: {exc}")

    @pytest.mark.parametrize("out_fmt", ["png", "jpg", "webp", "bmp", "tiff"])
    def test_heic_to_all_image_formats(self, tmp_path, out_fmt):
        src = self._make_heif_fixture(tmp_path, "test.heic")
        dest = tmp_path / f"converted.{out_fmt}"
        converter.convert_image(src, dest, out_fmt)
        assert dest.exists()
        assert dest.stat().st_size > 0

    @pytest.mark.parametrize("out_fmt", ["png", "jpg", "webp", "bmp", "tiff"])
    def test_avif_to_all_image_formats(self, tmp_path, out_fmt):
        src = self._make_avif_fixture(tmp_path, "test.avif")
        dest = tmp_path / f"converted.{out_fmt}"
        converter.convert_image(src, dest, out_fmt)
        assert dest.exists()
        assert dest.stat().st_size > 0

    def test_transparent_heic_to_jpeg_flattens_alpha(self, tmp_path):
        from PIL import Image
        src = self._make_heif_fixture(tmp_path, "transparent.heic", mode="RGBA")
        dest = tmp_path / "flattened.jpg"
        converter.convert_image(src, dest, "jpg")
        assert dest.exists()
        with Image.open(dest) as out_img:
            assert out_img.mode == "RGB"

    def test_transparent_avif_to_jpeg_flattens_alpha(self, tmp_path):
        from PIL import Image
        src = self._make_avif_fixture(tmp_path, "transparent.avif", mode="RGBA")
        dest = tmp_path / "flattened.jpg"
        converter.convert_image(src, dest, "jpg")
        assert dest.exists()
        with Image.open(dest) as out_img:
            assert out_img.mode == "RGB"

    def test_corrupt_heic_raises_clear_error(self, tmp_path):
        bad = tmp_path / "corrupted.heic"
        bad.write_bytes(b"ftypheic\x00\x00\x00invalid header payload bytes")
        dest = tmp_path / "out.png"
        with pytest.raises(RuntimeError) as exc_info:
            converter.convert_image(bad, dest, "png")
        assert "cannot decode image" in str(exc_info.value).lower()
        assert "corrupted or in an unsupported format" in str(exc_info.value).lower()

    def test_corrupt_avif_raises_clear_error(self, tmp_path):
        bad = tmp_path / "corrupted.avif"
        bad.write_bytes(b"ftypavif\x00\x00\x00not real avif data")
        dest = tmp_path / "out.png"
        with pytest.raises(RuntimeError) as exc_info:
            converter.convert_image(bad, dest, "png")
        assert "cannot decode image" in str(exc_info.value).lower()
        assert "corrupted or in an unsupported format" in str(exc_info.value).lower()

    def test_missing_heif_decoder_raises_clear_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(converter, "is_heif_supported", lambda: False)
        src = tmp_path / "photo.heic"
        src.write_bytes(b"dummy")
        dest = tmp_path / "out.png"
        with pytest.raises(RuntimeError) as exc_info:
            converter.convert_image(src, dest, "png")
        assert "heic/heif decoding is not available" in str(exc_info.value).lower()
        assert "pillow-heif" in str(exc_info.value)

    def test_missing_avif_decoder_raises_clear_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(converter, "is_avif_supported", lambda: False)
        src = tmp_path / "image.avif"
        src.write_bytes(b"dummy")
        dest = tmp_path / "out.png"
        with pytest.raises(RuntimeError) as exc_info:
            converter.convert_image(src, dest, "png")
        assert "avif decoding is not supported" in str(exc_info.value).lower()

    def test_worker_heic_conversion(self, tmp_path):
        import os
        from PIL import Image

        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        from main import ConvertWorker

        _ = QApplication.instance() or QApplication([])

        src = self._make_heif_fixture(tmp_path, "worker_test.heic")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        results = []
        worker = ConvertWorker([str(src)], "jpg", out_dir)
        worker.signals.finished.connect(lambda s, f: results.append((s, f)))
        worker.run()

        assert len(results) == 1
        succeeded, failed = results[0]
        assert succeeded == 1
        assert failed == []
        assert (out_dir / "worker_test.jpg").exists()


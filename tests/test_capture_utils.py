from datetime import datetime
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSize

import capture_utils as cu

NOW = datetime(2026, 11, 9, 16, 45, 0)


def test_timestamp_format():
    assert cu.timestamp(NOW) == "20261109_164500"


def test_make_filename():
    assert cu.make_filename("video", NOW) == "video_20261109_164500.mp4"
    assert cu.make_filename("photo", NOW) == "photo_20261109_164500.jpg"


def test_make_filename_rejects_unknown_kind():
    with pytest.raises(ValueError):
        cu.make_filename("audio", NOW)


def test_make_path_creates_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(cu, "VIDEO_DIR", tmp_path / "vid")
    monkeypatch.setattr(cu, "PHOTO_DIR", tmp_path / "pic")
    video = cu.make_path("video", NOW)
    photo = cu.make_path("photo", NOW)
    assert video == tmp_path / "vid" / "video_20261109_164500.mp4"
    assert photo == tmp_path / "pic" / "photo_20261109_164500.jpg"
    assert video.parent.is_dir()
    assert photo.parent.is_dir()


def test_make_path_rejects_unknown_kind(tmp_path, monkeypatch):
    monkeypatch.setattr(cu, "PHOTO_DIR", tmp_path / "pic")
    with pytest.raises(ValueError):
        cu.make_path("audio", NOW)


def test_make_temp_path(tmp_path, monkeypatch):
    monkeypatch.setattr(cu.tempfile, "gettempdir", lambda: str(tmp_path))
    path = cu.make_temp_path(NOW)
    assert path == tmp_path / "pc_cam" / "video_20261109_164500.mp4"
    assert path.parent.is_dir()


def test_format_label():
    assert cu.format_label(1920, 1080, 29.97) == "1920 x 1080  @ 30 fps"


def _fmt(w, h, fps):
    return SimpleNamespace(resolution=lambda: QSize(w, h),
                           maxFrameRate=lambda: fps)


def test_sort_formats_largest_first_then_fps():
    a, b, c = _fmt(640, 480, 30), _fmt(1920, 1080, 30), _fmt(1920, 1080, 60)
    assert cu.sort_formats([a, b, c]) == [c, b, a]


def test_output_sizes():
    assert not cu.OUTPUT_SIZES[0].size.isValid()  # "same as camera"
    labels = [o.label for o in cu.OUTPUT_SIZES]
    assert len(labels) == len(set(labels))
    assert QSize(1920, 1080) in [o.size for o in cu.OUTPUT_SIZES]

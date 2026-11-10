from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QImage

import clips_panel as cp
from camera_window import CameraWindow
from capture_utils import VIDEO_DIR, unique_path
from clips_panel import ClipsPanel


def make_clip(tmp_path, name):
    path = tmp_path / "tmp" / name
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"x" * 10)
    return path


def ini(tmp_path):
    return QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)


def test_unique_path(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"")
    (tmp_path / "a_1.mp4").write_bytes(b"")
    assert unique_path(tmp_path, "b.mp4") == tmp_path / "b.mp4"
    assert unique_path(tmp_path, "a.mp4") == tmp_path / "a_2.mp4"


def test_save_only_checked(qapp, tmp_path):
    panel = ClipsPanel(ini(tmp_path))
    a, b = make_clip(tmp_path, "a.mp4"), make_clip(tmp_path, "b.mp4")
    panel.add_clip(a)
    panel.add_clip(b)
    panel.list.item(1).setCheckState(Qt.Unchecked)       # keep b out
    saved = panel.save_checked(tmp_path / "out")
    assert saved == [tmp_path / "out" / "a.mp4"]
    assert b.exists()
    assert not a.exists()
    assert panel.paths() == [b]


def test_save_does_not_overwrite(qapp, tmp_path):
    panel = ClipsPanel(ini(tmp_path))
    out = tmp_path / "out"
    out.mkdir()
    (out / "a.mp4").write_bytes(b"old")
    panel.add_clip(make_clip(tmp_path, "a.mp4"))
    saved = panel.save_checked(out)
    assert saved == [out / "a_1.mp4"]
    assert (out / "a.mp4").read_bytes() == b"old"


def test_discard_checked(qapp, tmp_path):
    panel = ClipsPanel(ini(tmp_path))
    a = make_clip(tmp_path, "a.mp4")
    panel.add_clip(a)
    panel.discard_checked()
    assert not a.exists()
    assert panel.count() == 0


def test_thumbnail_becomes_icon(qapp, tmp_path):
    panel = ClipsPanel(ini(tmp_path))
    image = QImage(320, 180, QImage.Format_RGB32)
    image.fill(QColor("red"))
    panel.add_clip(make_clip(tmp_path, "a.mp4"), image)
    panel.add_clip(make_clip(tmp_path, "b.mp4"), QImage())   # null: no icon
    assert not panel.list.item(0).icon().isNull()
    assert panel.list.item(1).icon().isNull()


def test_start_folder_defaults_then_remembers(qapp, tmp_path, monkeypatch):
    panel = ClipsPanel(ini(tmp_path))
    assert panel.start_folder() == str(VIDEO_DIR)

    chosen = tmp_path / "mine"
    seen = {}

    def fake_dialog(parent, title, start):
        seen["start"] = start
        return str(chosen)

    monkeypatch.setattr(cp.QFileDialog, "getExistingDirectory", fake_dialog)
    monkeypatch.setattr(cp, "VIDEO_DIR", tmp_path / "default")
    panel.add_clip(make_clip(tmp_path, "a.mp4"))
    panel.choose_and_save()
    assert (chosen / "a.mp4").exists()
    assert panel.start_folder() == str(chosen)         # remembered


def test_cancelled_folder_dialog_keeps_clips(qapp, tmp_path, monkeypatch):
    panel = ClipsPanel(ini(tmp_path))
    monkeypatch.setattr(cp, "VIDEO_DIR", tmp_path / "default")
    monkeypatch.setattr(cp.QFileDialog, "getExistingDirectory",
                        lambda *a, **k: "")
    a = make_clip(tmp_path, "a.mp4")
    panel.add_clip(a)
    panel.choose_and_save()
    assert a.exists()
    assert panel.count() == 1


def test_panel_visibility_setting(qapp, tmp_path):
    settings = ini(tmp_path)
    win = CameraWindow(settings=settings)
    win.show()
    win.always_panel.setChecked(False)
    assert not win.clips.isVisible()                     # empty and not always
    win.clips.add_clip(make_clip(tmp_path, "a.mp4"))
    assert win.clips.isVisible()                         # has a clip
    win.always_panel.setChecked(True)
    assert settings.value("always_show_panel", type=bool) is True


def test_grab_thumbnail_without_frames_is_null(qapp, tmp_path):
    win = CameraWindow(settings=ini(tmp_path))
    assert isinstance(win.grab_thumbnail(), QImage)

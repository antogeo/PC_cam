from PySide6.QtMultimedia import QMediaPlayer

import preview_dialog as pd
from preview_dialog import PreviewDialog, format_ms


def make_clip(tmp_path):
    clip = tmp_path / "tmp" / "clip.mp4"
    clip.parent.mkdir()
    clip.write_bytes(b"not a real video")
    return clip


def test_format_ms():
    assert format_ms(0) == "0:00"
    assert format_ms(65_000) == "1:05"
    assert format_ms(-5) == "0:00"


def test_save_moves_clip(qapp, tmp_path):
    clip = make_clip(tmp_path)
    dest = tmp_path / "out" / "saved.mp4"
    dlg = PreviewDialog(clip, tmp_path / "default.mp4")
    dlg.save_to(dest)
    assert dest.read_bytes() == b"not a real video"
    assert not clip.exists()
    assert dlg.saved_path == dest


def test_discard_deletes_clip(qapp, tmp_path):
    clip = make_clip(tmp_path)
    dlg = PreviewDialog(clip, tmp_path / "default.mp4")
    dlg.discard()
    assert not clip.exists()
    assert dlg.saved_path is None


def test_closing_keeps_clip(qapp, tmp_path):
    clip = make_clip(tmp_path)
    dlg = PreviewDialog(clip, tmp_path / "default.mp4")
    dlg.reject()                      # same path as X and Esc
    assert clip.exists()
    assert dlg.saved_path is None


def test_close_button_keeps_clip_and_stops_playback(qapp, tmp_path):
    clip = make_clip(tmp_path)
    dlg = PreviewDialog(clip, tmp_path / "default.mp4")
    dlg.close_button.click()
    assert clip.exists()
    assert dlg.player.playbackState() == QMediaPlayer.StoppedState


def test_save_button_adds_mp4_suffix(qapp, tmp_path, monkeypatch):
    clip = make_clip(tmp_path)
    chosen = tmp_path / "myclip"
    monkeypatch.setattr(pd.QFileDialog, "getSaveFileName",
                        lambda *a, **k: (str(chosen), ""))
    dlg = PreviewDialog(clip, tmp_path / "default.mp4")
    dlg.choose_and_save()
    assert (tmp_path / "myclip.mp4").exists()


def test_save_cancelled_keeps_clip(qapp, tmp_path, monkeypatch):
    clip = make_clip(tmp_path)
    monkeypatch.setattr(pd.QFileDialog, "getSaveFileName",
                        lambda *a, **k: ("", ""))
    dlg = PreviewDialog(clip, tmp_path / "default.mp4")
    dlg.choose_and_save()
    assert clip.exists() and dlg.saved_path is None

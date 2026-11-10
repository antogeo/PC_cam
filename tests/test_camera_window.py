"""Smoke tests: the window builds and its controls behave (no real camera needed)."""
from camera_window import CameraWindow
from capture_utils import OUTPUT_SIZES


def test_window_builds(qapp):
    win = CameraWindow()
    assert win.windowTitle() == "PC Cam"
    assert win.size_box.count() == len(OUTPUT_SIZES)
    assert [win.mode_box.itemText(i) for i in range(win.mode_box.count())] \
        == ["Video", "Photo"]


def test_recorder_uses_h264_mp4(qapp):
    from PySide6.QtMultimedia import QMediaFormat
    fmt = CameraWindow().recorder.mediaFormat()
    assert fmt.fileFormat() == QMediaFormat.FileFormat.MPEG4
    assert fmt.videoCodec() == QMediaFormat.VideoCodec.H264
    assert fmt.audioCodec() == QMediaFormat.AudioCodec.AAC


def test_audio_input_is_kept_and_unmuted(qapp):
    win = CameraWindow()
    assert win.session.audioInput() is not None
    assert not win.audio_input.isMuted()
    assert win.audio_input.volume() == 1.0


def test_shutter_label_follows_mode(qapp):
    win = CameraWindow()
    win.mode_box.setCurrentText("Photo")
    assert win.shutter.text() == "Take photo"
    win.mode_box.setCurrentText("Video")
    assert win.shutter.text() == "Record"


def test_no_camera_disables_shutter(qapp):
    win = CameraWindow()
    if not win.devices:
        assert not win.shutter.isEnabled()
        assert win.status.text() == "No camera found"
    else:
        assert win.camera_box.count() == len(win.devices)
        assert win.res_box.count() == len(win.devices[0].videoFormats())

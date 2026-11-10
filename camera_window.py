import os

# Qt's FFmpeg backend tries only VAAPI hardware encoding by default, which
# fails on many Linux machines ("No valid video codecs found"). "none" forces
# software encoding. setdefault keeps any value the user exported themselves.
os.environ.setdefault("QT_FFMPEG_ENCODING_HW_DEVICE_TYPES", "none")

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtMultimedia import (  # noqa: E402
    QAudioInput, QCamera, QImageCapture, QMediaCaptureSession,
    QMediaDevices, QMediaFormat, QMediaRecorder,
)
from PySide6.QtMultimediaWidgets import QVideoWidget  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from capture_utils import (  # noqa: E402
    OUTPUT_SIZES, format_label, make_path, make_temp_path, sort_formats,
)
from preview_dialog import PreviewDialog


class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC Cam")
        self.resize(900, 650)

        # Capture pipeline: camera -> session -> preview / recorder / photo
        self.session = QMediaCaptureSession()
        self.preview = QVideoWidget()
        self.session.setVideoOutput(self.preview)
        # Keep a reference: a temporary QAudioInput gets garbage-collected
        # and the recording silently has no sound.
        self.audio_input = QAudioInput()  # default microphone
        self.audio_input.setMuted(False)
        self.audio_input.setVolume(1.0)
        self.session.setAudioInput(self.audio_input)
        self.image_capture = QImageCapture()
        self.recorder = QMediaRecorder()
        # Qt defaults to H.265, which often has no encoder; force H.264 + AAC.
        media_format = QMediaFormat(QMediaFormat.FileFormat.MPEG4)
        media_format.setVideoCodec(QMediaFormat.VideoCodec.H264)
        media_format.setAudioCodec(QMediaFormat.AudioCodec.AAC)
        self.recorder.setMediaFormat(media_format)
        self.session.setImageCapture(self.image_capture)
        self.session.setRecorder(self.recorder)
        self.camera = None
        self.pending_path = None  # temp file of the clip being recorded

        # Controls
        self.camera_box = QComboBox()
        self.res_box = QComboBox()    # resolutions the camera supports
        self.size_box = QComboBox()   # output file size
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Video", "Photo"])
        self.shutter = QPushButton("Record")
        self.status = QLabel("Ready")

        for item in OUTPUT_SIZES:
            self.size_box.addItem(item.label, item.size)

        row = QHBoxLayout()
        for text, widget in [("Camera", self.camera_box),
                             ("Resolution", self.res_box),
                             ("Output size", self.size_box),
                             ("Mode", self.mode_box)]:
            row.addWidget(QLabel(text))
            row.addWidget(widget)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.shutter)
        layout.addWidget(self.status)

        # Wiring
        self.devices = QMediaDevices.videoInputs()
        for dev in self.devices:
            self.camera_box.addItem(dev.description())
        self.camera_box.currentIndexChanged.connect(self.select_camera)
        self.res_box.currentIndexChanged.connect(self.apply_format)
        self.mode_box.currentTextChanged.connect(self.update_shutter_label)
        self.shutter.clicked.connect(self.on_shutter)
        self.recorder.recorderStateChanged.connect(self.on_recorder_state)
        self.image_capture.imageSaved.connect(
            lambda _id, path: self.status.setText(f"Photo saved: {path}"))
        self.image_capture.errorOccurred.connect(
            lambda _id, _err, msg: self.status.setText(f"Photo error: {msg}"))
        self.recorder.errorOccurred.connect(
            lambda _err, msg: self.status.setText(f"Recording error: {msg}"))

        if self.devices:
            self.select_camera(0)
        else:
            self.status.setText("No camera found")
            self.shutter.setEnabled(False)

    # --- camera / format selection ---
    def select_camera(self, index):
        if index < 0 or index >= len(self.devices):
            return
        if self.camera:
            self.camera.stop()
        dev = self.devices[index]
        self.camera = QCamera(dev)
        self.session.setCamera(self.camera)

        # Fill the resolution list from what this camera actually supports.
        self.res_box.blockSignals(True)
        self.res_box.clear()
        for fmt in sort_formats(dev.videoFormats()):
            r = fmt.resolution()
            self.res_box.addItem(
                format_label(r.width(), r.height(), fmt.maxFrameRate()), fmt)
        self.res_box.blockSignals(False)

        self.apply_format()
        self.camera.start()

    def apply_format(self, *_):
        fmt = self.res_box.currentData()
        if fmt and self.camera:
            self.camera.setCameraFormat(fmt)

    # --- capture ---
    def update_shutter_label(self, mode):
        self.shutter.setText("Record" if mode == "Video" else "Take photo")

    def is_recording(self):
        return self.recorder.recorderState() == QMediaRecorder.RecordingState

    def on_shutter(self):
        size = self.size_box.currentData()

        if self.mode_box.currentText() == "Photo":
            self.image_capture.setResolution(size)  # null size = native
            self.image_capture.captureToFile(str(make_path("photo")))
            return

        if self.is_recording():
            self.recorder.stop()  # on_recorder_state opens the preview
            self.shutter.setText("Record")
            self.mode_box.setEnabled(True)
            return

        # Record to a temp file; the user decides in the preview to save it.
        self.pending_path = make_temp_path()
        self.recorder.setOutputLocation(
            QUrl.fromLocalFile(str(self.pending_path)))
        self.recorder.setVideoResolution(size)
        self.recorder.setQuality(QMediaRecorder.HighQuality)
        self.recorder.record()
        self.shutter.setText("Stop")
        self.status.setText("Recording...")
        self.mode_box.setEnabled(False)

    def on_recorder_state(self, state):
        """When the file is finalized, show the preview (if we have a clip)."""
        if state != QMediaRecorder.StoppedState or self.pending_path is None:
            return
        path, self.pending_path = self.pending_path, None
        if not path.exists() or path.stat().st_size == 0:
            self.status.setText("Recording failed: no data was written")
            return
        self.show_preview(path)

    def show_preview(self, path):
        dialog = PreviewDialog(path, make_path("video"), self)
        dialog.exec()
        if dialog.saved_path:
            self.status.setText(f"Video saved: {dialog.saved_path}")
        else:
            self.status.setText("Recording discarded")

    def closeEvent(self, event):
        self.pending_path = None  # closing: don't open a preview
        if self.is_recording():
            self.recorder.stop()
        if self.camera:
            self.camera.stop()
        super().closeEvent(event)

"""Window that plays back a just-recorded clip and lets the user save it."""
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSlider,
    QVBoxLayout,
)


def format_ms(ms):
    """Milliseconds -> 'm:ss'."""
    seconds = max(0, int(ms)) // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


class PreviewDialog(QDialog):
    def __init__(self, temp_path, default_save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview recording")
        self.resize(800, 560)
        self.temp_path = Path(temp_path)
        self.default_save_path = Path(default_save_path)
        self.saved_path = None

        # Playback
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.video = QVideoWidget()
        self.player.setVideoOutput(self.video)
        self.player.setSource(QUrl.fromLocalFile(str(self.temp_path)))

        # Controls
        self.play_button = QPushButton("Pause")
        self.slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("0:00 / 0:00")
        self.close_button = QPushButton("Close")
        self.save_button = QPushButton("Save...")
        self.discard_button = QPushButton("Discard")

        controls = QHBoxLayout()
        controls.addWidget(self.play_button)
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.time_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.close_button)
        buttons.addWidget(self.discard_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video, 1)
        layout.addLayout(controls)
        layout.addLayout(buttons)

        self.play_button.clicked.connect(self.toggle_play)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.slider.setMaximum)
        self.close_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.choose_and_save)
        self.discard_button.clicked.connect(self.discard)
        self.finished.connect(self._stop_playback)

        self.player.play()

    # --- playback ---
    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_button.setText("Play")
        else:
            self.player.play()
            self.play_button.setText("Pause")

    def on_position(self, position):
        if not self.slider.isSliderDown():
            self.slider.setValue(position)
        self.time_label.setText(
            f"{format_ms(position)} / {format_ms(self.player.duration())}")

    # --- save / discard ---
    def choose_and_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save video", str(self.default_save_path),
            "MP4 video (*.mp4)")
        if path:
            if not path.lower().endswith(".mp4"):
                path += ".mp4"
            self.save_to(path)

    def save_to(self, path):
        """Move the temporary clip to `path` and close the dialog."""
        self._release_player()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self.temp_path), str(path))
        self.saved_path = path
        self.accept()

    def discard(self):
        self._release_player()
        self.temp_path.unlink(missing_ok=True)
        super().reject()

    def _stop_playback(self, *_):
        """Closing only looks, never deletes: just stop the sound/video."""
        self.player.stop()

    def _release_player(self):
        self.player.stop()
        self.player.setSource(QUrl())

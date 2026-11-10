"""Bottom panel listing recorded clips; the user picks which ones to keep."""
import shutil
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout, QWidget,
)

from capture_utils import VIDEO_DIR, unique_path

THUMB_SIZE = QSize(96, 54)
SAVE_FOLDER_KEY = "save_folder"


class ClipsPanel(QWidget):
    countChanged = Signal(int)
    previewRequested = Signal(object)   # a Path
    status = Signal(str)

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings or QSettings("pc_cam", "PC Cam")

        self.list = QListWidget()
        self.list.setFlow(QListWidget.LeftToRight)
        self.list.setIconSize(THUMB_SIZE)
        self.list.setFixedHeight(120)
        self.save_button = QPushButton("Save selected...")
        self.discard_button = QPushButton("Discard selected")

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.discard_button)
        buttons.addWidget(self.save_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        self.list.itemDoubleClicked.connect(
            lambda item: self.previewRequested.emit(self._path(item)))
        self.save_button.clicked.connect(self.choose_and_save)
        self.discard_button.clicked.connect(self.discard_checked)
        self._refresh_buttons()

    # --- helpers ---
    @staticmethod
    def _path(item):
        return Path(item.data(Qt.UserRole))

    def _items(self):
        return [self.list.item(i) for i in range(self.list.count())]

    def count(self):
        return self.list.count()

    def _refresh_buttons(self):
        has = self.count() > 0
        self.save_button.setEnabled(has)
        self.discard_button.setEnabled(has)
        self.countChanged.emit(self.count())

    # --- clips ---
    def add_clip(self, path, thumbnail=None):
        """Add a clip. `thumbnail` is an optional QImage shown as its icon."""
        path = Path(path)
        size_mb = path.stat().st_size / 1_000_000
        item = QListWidgetItem(f"{path.stem}\n{size_mb:.1f} MB")
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)      # checked = will be saved
        item.setData(Qt.UserRole, str(path))
        if thumbnail is not None and not thumbnail.isNull():
            pixmap = QPixmap.fromImage(thumbnail).scaled(
                THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(pixmap))
        self.list.addItem(item)
        self._refresh_buttons()

    def paths(self, checked_only=False):
        return [self._path(i) for i in self._items()
                if not checked_only or i.checkState() == Qt.Checked]

    def remove_path(self, path):
        for item in self._items():
            if self._path(item) == Path(path):
                self.list.takeItem(self.list.row(item))
        self._refresh_buttons()

    def save_checked(self, folder):
        """Move checked clips into `folder`; return the new paths."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        saved = []
        for path in self.paths(checked_only=True):
            dest = unique_path(folder, path.name)
            shutil.move(str(path), str(dest))
            saved.append(dest)
            self.remove_path(path)
        return saved

    def discard_checked(self):
        paths = self.paths(checked_only=True)
        for path in paths:
            path.unlink(missing_ok=True)
            self.remove_path(path)
        self.status.emit(f"Discarded {len(paths)} clip(s)")

    def discard_all(self):
        for path in self.paths():
            path.unlink(missing_ok=True)
            self.remove_path(path)

    # --- choosing where to save ---
    def start_folder(self):
        """Last folder the user chose, else the default PC Cam folder."""
        return str(self.settings.value(SAVE_FOLDER_KEY, str(VIDEO_DIR)))

    def choose_and_save(self):
        start = Path(self.start_folder())
        start.mkdir(parents=True, exist_ok=True)
        folder = QFileDialog.getExistingDirectory(
            self, "Save selected clips to...", str(start))
        if folder:
            self.settings.setValue(SAVE_FOLDER_KEY, folder)
            saved = self.save_checked(folder)
            self.status.emit(f"Saved {len(saved)} clip(s) to {folder}")

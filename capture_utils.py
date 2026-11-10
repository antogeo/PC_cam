"""Pure helper logic for PC Cam (no widgets, easy to test)."""
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize

VIDEO_DIR = Path.home() / "Videos" / "PC Cam"
PHOTO_DIR = Path.home() / "Pictures" / "PC Cam"


@dataclass(frozen=True)
class OutputSize:
    """An output size choice. A null QSize means "same as the camera"."""
    label: str
    size: QSize


OUTPUT_SIZES = [
    OutputSize("Same as camera", QSize()),
    OutputSize("640 x 360", QSize(640, 360)),
    OutputSize("1280 x 720 (HD)", QSize(1280, 720)),
    OutputSize("1920 x 1080 (Full HD)", QSize(1920, 1080)),
    OutputSize("3840 x 2160 (4K)", QSize(3840, 2160)),
]


def timestamp(now=None):
    """Return a sortable timestamp such as 20261109_164500."""
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def make_filename(kind, now=None):
    """Build a file name for 'video' or 'photo'."""
    if kind == "video":
        return f"video_{timestamp(now)}.mp4"
    if kind == "photo":
        return f"photo_{timestamp(now)}.jpg"
    raise ValueError(f"unknown kind: {kind!r}")


def make_path(kind, now=None):
    """Full path in the right folder; creates the folder if missing."""
    folder = VIDEO_DIR if kind == "video" else PHOTO_DIR
    if kind not in ("video", "photo"):
        raise ValueError(f"unknown kind: {kind!r}")
    folder.mkdir(parents=True, exist_ok=True)
    return folder / make_filename(kind, now)


def make_temp_path(now=None):
    """Temporary file a recording is written to until the user saves it."""
    folder = Path(tempfile.gettempdir()) / "pc_cam"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / make_filename("video", now)


def unique_path(folder, name):
    """folder/name, or folder/stem_1.ext, stem_2.ext... if it already exists."""
    folder = Path(folder)
    candidate = folder / name
    stem, suffix = candidate.stem, candidate.suffix
    n = 1
    while candidate.exists():
        candidate = folder / f"{stem}_{n}{suffix}"
        n += 1
    return candidate


def format_label(width, height, max_fps):
    """Text shown in the resolution dropdown."""
    return f"{width} x {height}  @ {max_fps:.0f} fps"


def sort_formats(formats):
    """Largest resolution first, then highest frame rate."""
    def key(fmt):
        r = fmt.resolution()
        return (r.width() * r.height(), fmt.maxFrameRate())
    return sorted(formats, key=key, reverse=True)

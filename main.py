import sys

from PySide6.QtWidgets import QApplication

from camera_window import CameraWindow


def main():
    app = QApplication(sys.argv)
    win = CameraWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

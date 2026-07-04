from pathlib import Path
import os
import shutil
import sys


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent


def prepare_runtime_environment():
    app_dir = get_app_dir()
    bundle_dir = get_bundle_dir()

    os.chdir(app_dir)
    os.environ["PPE_APP_DIR"] = str(app_dir)
    os.environ["PPE_BUNDLE_DIR"] = str(bundle_dir)

    output_dir = app_dir / "output"
    for subdir in ["json", "preview", "java", "logs", "mph", "results"]:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)

    external_config_dir = app_dir / "config"
    bundled_config_dir = bundle_dir / "config"

    if not external_config_dir.exists() and bundled_config_dir.exists():
        shutil.copytree(bundled_config_dir, external_config_dir)


prepare_runtime_environment()

from PyQt6.QtWidgets import QApplication
from gui.app import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
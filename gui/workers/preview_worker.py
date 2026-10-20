from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from scripts.export_java import export_preview_from_config


class PreviewWorker(QThread):
    success = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        config_path: Path,
        *,
        run_dir: Path | None = None,
        json_path: Path | None = None,
        preview_path: Path | None = None,
    ):
        super().__init__()
        self.config_path = config_path
        self.run_dir = run_dir
        self.json_path = json_path
        self.preview_path = preview_path

    def run(self):
        try:
            result = export_preview_from_config(
                config_path=self.config_path,
                run_dir=self.run_dir,
                json_path=self.json_path,
                preview_path=self.preview_path,
            )
            self.success.emit(result)
        except Exception as e:
            self.failed.emit(str(e))

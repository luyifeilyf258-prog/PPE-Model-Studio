from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from scripts.export_java import export_java_from_config


class ExportWorker(QThread):
    success = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        config_path: Path,
        output_java_path: Path,
        *,
        run_dir: Path | None = None,
    ):
        super().__init__()
        self.config_path = config_path
        self.output_java_path = output_java_path
        self.run_dir = run_dir

    def run(self):
        try:
            result = export_java_from_config(
                config_path=self.config_path,
                output_java_path=self.output_java_path,
                export_json=True,
                export_preview=True,
                run_dir=self.run_dir,
            )
            self.success.emit(result)
        except Exception as e:
            self.failed.emit(str(e))

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from pipeline.run_comsol_case import run_comsol_case_from_config
from comsol_runner.runner import ComsolRunner, ComsolRunCancelled


class RunComsolWorker(QThread):
    success = pyqtSignal(dict)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal(str)

    def __init__(
            self,
            config_path: Path,
            output_java_path: Path,
            comsolcompile_path: Path,
            comsolbatch_path: Path,
            log_path: Path,
            output_mph_path: Path | None = None,
            run_study: bool = True,
            export_results: bool = True,
            run_dir: Path | None = None,
    ):
        super().__init__()
        self.config_path = config_path
        self.output_java_path = output_java_path
        self.comsolcompile_path = comsolcompile_path
        self.comsolbatch_path = comsolbatch_path
        self.log_path = log_path
        self.output_mph_path = output_mph_path
        self.run_study = run_study
        self.export_results = export_results
        self.run_dir = run_dir
        self.runner: ComsolRunner | None = None
        self.stop_requested = False

    def request_stop(self):
        self.stop_requested = True

        if self.runner is not None:
            self.runner.stop()

    def is_stop_requested(self) -> bool:
        return self.stop_requested

    def run(self):
        try:
            self.runner = ComsolRunner(
                comsolcompile_path=self.comsolcompile_path,
                comsolbatch_path=self.comsolbatch_path,
            )

            result = run_comsol_case_from_config(
                config_path=self.config_path,
                output_java_path=self.output_java_path,
                comsolcompile_path=self.comsolcompile_path,
                comsolbatch_path=self.comsolbatch_path,
                log_path=self.log_path,
                output_mph_path=self.output_mph_path,
                runner=self.runner,
                should_stop=self.is_stop_requested,
                run_study=self.run_study,
                export_results=self.export_results,
                run_dir=self.run_dir,
            )
            self.success.emit(result)

        except ComsolRunCancelled as e:
            self.cancelled.emit(str(e))
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            self.runner = None

from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.result_plot_canvas import ResultPlotCanvas

RESULT_TRANSLATIONS = {
    "导入 CSV": "Import CSV",
    "清空": "Clear",
    "导出图像": "Export Image",
    "无法导出": "Cannot Export",
    "当前没有结果曲线。": "There are no result curves to export.",
    "导出当前曲线图": "Export Current Curve Plot",
    "导出失败": "Export Failed",
    "结果曲线图已导出：": "Result curve plot exported: ",
    "所选 CSV 已在当前曲线中。": "The selected CSV is already in the current curves.",
}

class ResultManager(QWidget):
    import_requested = pyqtSignal()
    log_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultManager")

        self.default_export_dir_provider: Callable[[], Path] | None = None
        self.default_single_label: str | None = None
        self.csv_paths: list[Path] = []
        self.csv_label_overrides: dict[Path, str] = {}
        self.current_language = "zh"

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)
        self.setLayout(root_layout)

        tool_layout = QHBoxLayout()
        tool_layout.setContentsMargins(0, 0, 0, 0)
        tool_layout.setSpacing(8)
                                
        tool_layout.addStretch(1)

        self.import_button = QPushButton(self.tr_text("导入 CSV"))
        self.import_button.setObjectName("SmallToolButton")
        self.import_button.clicked.connect(self.import_requested.emit)

        self.clear_button = QPushButton(self.tr_text("清空"))
        self.clear_button.setObjectName("SmallToolButton")
        self.clear_button.clicked.connect(self.clear_results)

        self.export_button = QPushButton(self.tr_text("导出图像"))
        self.export_button.setObjectName("SmallToolButton")
        self.export_button.clicked.connect(lambda: self.export_current_plot(self))

        tool_layout.addWidget(self.import_button)
        tool_layout.addWidget(self.clear_button)
        tool_layout.addWidget(self.export_button)
        root_layout.addLayout(tool_layout)

        self.plot_canvas = ResultPlotCanvas()
        self.plot_canvas.setMinimumHeight(160)
        self.plot_canvas.clear_plot()
        root_layout.addWidget(self.plot_canvas, stretch=1)

    def tr_text(self, text: str) -> str:
        if self.current_language == "en":
            return RESULT_TRANSLATIONS.get(text, text)
        return text

    def tr_message(self, text) -> str:
        text = str(text)
        if self.current_language != "en":
            return text
        if text in RESULT_TRANSLATIONS:
            return RESULT_TRANSLATIONS[text]
        for zh, en in [("结果曲线图已导出：", "Result curve plot exported: ")]:
            if text.startswith(zh):
                return en + text[len(zh):]
        return text

    def set_language(self, language: str):
        if language not in {"zh", "en"}:
            return
        self.current_language = language
        self.import_button.setText(self.tr_text("导入 CSV"))
        self.clear_button.setText(self.tr_text("清空"))
        self.export_button.setText(self.tr_text("导出图像"))

    def set_default_export_dir_provider(self, provider: Callable[[], Path] | None):
        self.default_export_dir_provider = provider

    def get_default_export_dir(self) -> Path:
        if self.default_export_dir_provider is not None:
            try:
                path = Path(self.default_export_dir_provider())
                path.mkdir(parents=True, exist_ok=True)
                return path
            except Exception:
                pass
        fallback = Path.cwd()
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    def existing_paths(self) -> set[Path]:
        return set(self.csv_paths)

    def add_csv_files(
            self,
            csv_paths: list[str | Path],
            default_single_label: str | None = None,
            animate: bool = False,
            clear_existing: bool = False,
            label_overrides: Mapping[str | Path, str] | None = None,
    ):
        if not csv_paths:
            return

        self.default_single_label = default_single_label

        if clear_existing:
            self.csv_paths.clear()
            self.csv_label_overrides.clear()

        existing = self.existing_paths()
        added_count = 0

        for csv_path in csv_paths:
            path = Path(csv_path)

            if label_overrides:
                if path in label_overrides:
                    self.csv_label_overrides[path] = str(label_overrides[path])
                elif str(path) in label_overrides:
                    self.csv_label_overrides[path] = str(label_overrides[str(path)])
                else:
                    for key, value in label_overrides.items():
                        try:
                            if Path(key) == path:
                                self.csv_label_overrides[path] = str(value)
                                break
                        except Exception:
                            continue

            if path in existing:
                continue

            self.csv_paths.append(path)
            existing.add(path)
            added_count += 1

        if added_count == 0:
            self.log_requested.emit(self.tr_message("所选 CSV 已在当前曲线中。"))

        self.replot_all_results(animate=animate)

    def get_all_csv_paths(self) -> list[Path]:
        return list(self.csv_paths)

    def replot_all_results(self, animate: bool = False):
        paths = self.get_all_csv_paths()
        if not paths:
            self.plot_canvas.clear_plot()
            return

        if animate:
            self.plot_canvas.plot_csv_files_animated(
                paths,
                default_single_label=self.default_single_label,
                label_overrides=self.csv_label_overrides,
            )
        else:
            self.plot_canvas.plot_csv_files(
                paths,
                default_single_label=self.default_single_label,
                label_overrides=self.csv_label_overrides,
            )

    def clear_results(self):
        self.csv_paths.clear()
        self.csv_label_overrides.clear()
        self.plot_canvas.clear_plot()

    def export_current_plot(self, parent=None):
        if not self.get_all_csv_paths():
            QMessageBox.warning(parent or self, self.tr_text("无法导出"), self.tr_text("当前没有结果曲线。"))
            return

        default_dir = self.get_default_export_dir()
        default_path = default_dir / "result_curves.png"
        path, _ = QFileDialog.getSaveFileName(
            parent or self,
            self.tr_text("导出当前曲线图"),
            str(default_path),
            "PNG Image (*.png);;PDF File (*.pdf);;SVG File (*.svg)",
        )

        if not path:
            return

        output_path = Path(path)
        if output_path.suffix.lower() not in {".png", ".pdf", ".svg"}:
            output_path = output_path.with_suffix(".png")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.plot_canvas.fig.savefig(output_path, dpi=220)
            self.log_requested.emit(self.tr_message(f"结果曲线图已导出：{output_path}"))
        except Exception as e:
            QMessageBox.critical(parent or self, self.tr_text("导出失败"), str(e))

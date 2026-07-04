import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

from PyQt6.QtCore import Qt, QTimer, QUrl, QSize
from PyQt6.QtGui import QTextCursor, QAction, QActionGroup, QDesktopServices, QFont, QIntValidator, QDoubleValidator
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTextEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QGroupBox,
    QSplitter,
    QScrollArea,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QMenuBar,
    QStatusBar,
    QMenu,
    QComboBox,
    QLineEdit,
    QSizePolicy,
)

from gui.widgets.preview_view import PreviewImageView
from gui.widgets.result_manager import ResultManager
from gui.widgets.form_controls import make_float_box, make_form, make_scroll_tab
from gui.workers.export_worker import ExportWorker
from gui.workers.preview_worker import PreviewWorker
from gui.workers.comsol_worker import RunComsolWorker

def get_app_root() -> Path:
\
\
\
       
    if os.environ.get("PPE_APP_DIR"):
        return Path(os.environ["PPE_APP_DIR"]).resolve()

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[1]

APP_VERSION = "v1.0.0"
APP_NAME = "PPE Model Studio"
APP_DISPLAY_NAME = f"{APP_NAME} {APP_VERSION}"

MESH_SIZE_OPTIONS = [
    ("extremely_fine", 1, "极细", "Extremely fine"),
    ("extra_fine", 2, "很细", "Extra fine"),
    ("finer", 3, "较细", "Finer"),
    ("fine", 4, "细化", "Fine"),
    ("normal", 5, "常规", "Normal"),
    ("coarse", 6, "粗化", "Coarse"),
    ("coarser", 7, "较粗", "Coarser"),
    ("extremely_coarse", 8, "极粗", "Extremely coarse"),
]

MESH_SIZE_BY_KEY = {key: (hauto, zh, en) for key, hauto, zh, en in MESH_SIZE_OPTIONS}

UI_TRANSLATIONS = {
    "文件": "File", "打开 YAML...": "Open YAML...", "保存 YAML": "Save YAML", "另存为 YAML...": "Save YAML As...",
    "语言": "Language", "中文": "Chinese", "English": "English",
    "选择 Java 输出路径...": "Select Java Output Path...", "使用默认 Java 输出路径": "Use Default Java Output Path",
    "打开输出目录": "Open Output Directory", "退出": "Exit",
    "参数": "Parameters", "参数校验": "Validate Parameters", "从 YAML 重新载入": "Reload from YAML", "写回 YAML": "Write Back to YAML",
    "几何": "Geometry", "模型生成": "Generate Model", "重置视图": "Reset View", "导出当预览图...": "Export Current Preview...",
    "图层显示": "Layer Visibility", "区域": "Regions", "负极颗粒": "Negative particles", "正极颗粒": "Positive particles", "粘结剂": "Binder", "坐标轴": "Axes",
    "计算": "Compute", "配置 COMSOL 路径...": "Configure COMSOL Paths...", "检查 COMSOL 路径": "Check COMSOL Paths", "仅生成模型文件": "Generate Model File Only", "运行 COMSOL": "Run COMSOL", "停止 COMSOL": "Stop COMSOL", "清空求解进度": "Clear Solver Log",
    "结果": "Results", "导入CSV文件": "Import CSV Files", "清空": "Clear", "导出曲线图...": "Export Plot...", "打开结果目录": "Open Results Directory",
    "视图": "View", "重置布局": "Reset Layout", "帮助": "Help", "关于 PPE Model Studio": "About PPE Model Studio",
    "配置：未选择": "Config: not selected", "Java：未选择": "Java: not selected", "注：运行此程序需接入 COMSOL": "Note: COMSOL is required to run this program",
    "状态：就绪": "Status: Ready", "COMSOL：未检查": "COMSOL: not checked", "COMSOL：已配置": "COMSOL: configured", "COMSOL：未配置": "COMSOL: not configured", "参数输入": "Parameter Input", "材料选择": "Material Selection", "高级设置": "Advanced Settings",
    "选择电解液、负极和正极材料；当前版本材料选项固定，用于查看材料配置": "Select electrolyte, negative electrode, and positive electrode materials. The current version uses fixed material options for configuration review.",
    "当前版本仅支持该材料": "The current version only supports this material.",
    "打开 YAML": "Open YAML", "保存": "Save", "另存为": "Save As", "选择 Java 路径": "Select Java Path", "使用默认路径": "Use Default Path", "读取 CSV": "Read CSV",
    "运行 COMSOL 后显示当前求解进度...": "Show current solver progress after running COMSOL...",
    "预览图": "Preview", "日志": "Log", "运行日志": "Run Log", "求解进度": "Solver Progress", "结果曲线": "Result Curves",
    "导出截图": "Export Screenshot", "图层": "Layers",
    "电解液材料": "Electrolyte material", "负极材料": "Negative electrode material", "正极材料": "Positive electrode material",
    "网格粗细设置": "Mesh size", "瞬态求解最大迭代次数": "Transient max iterations", "稳态求解最大迭代次数": "Stationary max iterations", "截至电压": "Cutoff voltage", "步长": "Time step",
    "次": "times", "常规": "Normal",
    "电池几何": "Cell Geometry", "设置二维电池区域尺寸，包括宽度、隔膜长度和正负极长度": "Set 2D cell dimensions, including width, separator length, and electrode lengths",
    "正极结构": "Positive Structure", "设置正极活性材料、颗粒粒径分布和粘结剂网络相关参数": "Set positive active material, particle distribution, and binder network parameters",
    "负极结构": "Negative Structure", "设置负极活性材料、颗粒粒径分布、粘结剂网络和集流体连接参数": "Set negative active material, particle distribution, binder network, and collector connection parameters",
    "电池电化学": "Cell Electrochemistry", "设置电解液初始浓度和循环倍率等全局电化学参数": "Set global electrochemical parameters such as initial electrolyte concentration and C-rate",
    "正极电化学": "Positive Electrochemistry", "设置正极初始状态、反应速率常数、界面膜电阻和双电层电容": "Set positive initial state, reaction rate, film resistance, and double-layer capacitance",
    "负极电化学": "Negative Electrochemistry", "设置负极初始状态、反应速率常数、界面膜电阻和双电层电容": "Set negative initial state, reaction rate, film resistance, and double-layer capacitance",
    "电池宽度": "Cell width", "隔膜长度": "Separator length", "正极长度": "Positive electrode length", "负极长度": "Negative electrode length",
    "正极活性材料体积分数": "Positive active fraction", "正极粘结剂体积分数": "Positive binder fraction", "正极颗粒平均直径": "Positive particle mean diameter",
    "正极颗粒直径离散程度": "Positive particle diameter dispersion", "正极颗粒对数正态标准差": "Positive particle lognormal std", "正极粘结剂宽度离散程度": "Positive binder width dispersion", "正极粘结剂对数正态标准差": "Positive binder lognormal std",
    "负极活性材料体积分数": "Negative active fraction", "负极粘结剂体积分数": "Negative binder fraction", "负极颗粒平均直径": "Negative particle mean diameter",
    "负极颗粒直径离散程度": "Negative particle diameter dispersion", "负极颗粒对数正态标准差": "Negative particle lognormal std", "负极粘结剂宽度离散程度": "Negative binder width dispersion", "负极粘结剂对数正态标准差": "Negative binder lognormal std", "负极集流体连接宽度系数": "Negative collector connection width factor",
    "电解液初始盐浓度": "Initial electrolyte salt concentration", "充放电循环倍率": "Charge/discharge C-rate",
    "正极初始 SOC": "Positive initial SOC", "正极反应速率常数 k0": "Positive reaction rate k0", "正极 SEI/界面膜电阻": "Positive SEI/interface film resistance", "正极双电层电容": "Positive double-layer capacitance",
    "负极初始 SOC": "Negative initial SOC", "负极反应速率常数 k0": "Negative reaction rate k0", "负极 SEI/界面膜电阻": "Negative SEI/interface film resistance", "负极双电层电容": "Negative double-layer capacitance",
    "就绪": "Ready", "配置已加载": "Config loaded", "配置已重新载入": "Config reloaded", "模型文件生成中": "Generating model file", "COMSOL 完成": "COMSOL completed", "模型文件已生成": "Model file generated", "COMSOL 失败": "COMSOL failed", "模型文件生成失败": "Model file generation failed", "预览完成": "Preview completed", "预览失败": "Preview failed", "Java 已生成": "Java generated", "生成失败": "Generation failed", "已停止": "Stopped", "截图已导出": "Screenshot exported", "截图导出失败": "Screenshot export failed",
}

UI_TRANSLATIONS.update({
    "路径不存在": "Path Not Found",
    "路径不存在：\n": "Path does not exist:\n",
    "缺少配置文件": "Missing Config File",
    "请先选择 YAML 配置文件。": "Please select a YAML config file first.",
    "缺少配置数据": "Missing Config Data",
    "请先加载 YAML 配置文件。": "Please load a YAML config file first.",
    "重新载入失败": "Reload Failed",
    "无法导出": "Cannot Export",
    "当前没有可导出的预览内容。": "There is no preview content to export.",
    "导出当前预览截图": "Export Current Preview Screenshot",
    "导出失败": "Export Failed",
    "截图导出失败：\n": "Screenshot export failed:\n",
    "清空失败": "Clear Failed",
    "关于 PPE Model Studio": "About PPE Model Studio",
    "二维颗粒-粘结剂几何建模、COMSOL Java 导出、COMSOL batch 自动运行和 CSV 结果绘图工具。": "2D particle-binder geometry modeling, COMSOL Java export, COMSOL batch automation, and CSV result plotting tool.",
    "无法生成默认路径": "Cannot Build Default Path",
    "选择 YAML 配置文件": "Select YAML Config File",
    "读取失败": "Read Failed",
    "参数校验失败": "Parameter Validation Failed",
    "参数校验通过。": "Parameter validation passed.",
    "参数校验失败。": "Parameter validation failed.",
    "保存失败": "Save Failed",
    "另存为 YAML 配置": "Save YAML Config As",
    "另存成功": "Save As Succeeded",
    "配置已另存为：\n": "Config has been saved as:\n",
    "另存失败": "Save As Failed",
    "选择 Java 保存路径": "Select Java Save Path",
    "选择一个或多个结果 CSV 文件": "Select One or More Result CSV Files",
    "绘图失败": "Plot Failed",
    "缺少输出路径": "Missing Output Path",
    "请先选择 Java 保存路径。": "Please select a Java save path first.",
    "COMSOL 路径配置错误": "COMSOL Path Configuration Error",
    "已停止": "Stopped",
    "COMSOL 计算已被用户停止。": "COMSOL calculation was stopped by the user.",
    "完成": "Done",
    "COMSOL 无界面运行完成。": "COMSOL batch run completed.",
    "COMSOL 运行失败": "COMSOL Run Failed",
    "模型文件生成已被用户停止。": "Model file generation was stopped by the user.",
    "模型文件已生成。\n\n该 MPH 未执行求解，可用 COMSOL Desktop 打开查看模型。": "The model file has been generated.\n\nThis MPH has not been solved and can be opened in COMSOL Desktop for inspection.",
    "模型文件生成失败": "Model File Generation Failed",
    "预览图刷新成功。": "Preview refreshed successfully.",
    "预览图刷新失败": "Preview Refresh Failed",
    "Java 文件生成成功。": "Java file generated successfully.",
    "生成失败": "Generation Failed",
    "当前没有正在运行的 COMSOL 任务。": "There is no running COMSOL task.",
    "用户请求停止 COMSOL 任务，正在终止 COMSOL 进程...": "Stop requested. Terminating the COMSOL process...",
    "COMSOL 运行中": "COMSOL running",
    "任务处理中": "Task running",
    "YAML 中缺少 comsol.runner.comsolcompile_path。": "YAML is missing comsol.runner.comsolcompile_path.",
    "YAML 中缺少 comsol.runner.comsolbatch_path。": "YAML is missing comsol.runner.comsolbatch_path.",
    "配置 COMSOL 路径": "Configure COMSOL Paths",
    "请选择本机 COMSOL 的 comsolcompile.exe 和 comsolbatch.exe。": "Please select the local COMSOL comsolcompile.exe and comsolbatch.exe.",
    "comsolcompile.exe 路径": "Path to comsolcompile.exe",
    "comsolbatch.exe 路径": "Path to comsolbatch.exe",
    "浏览...": "Browse...",
    "检查路径": "Check Paths",
    "选择 comsolcompile.exe": "Select comsolcompile.exe",
    "选择 comsolbatch.exe": "Select comsolbatch.exe",
    "路径检查通过": "Path Check Passed",
    "COMSOL 路径检查通过。": "COMSOL path check passed.",
    "请先配置 COMSOL 路径。": "Please configure COMSOL paths first.",
    "COMSOL 路径已保存": "COMSOL Paths Saved",
    "COMSOL 路径已写入 YAML。": "COMSOL paths have been written to YAML.",
    "COMSOL 路径已配置并写回 YAML：": "COMSOL paths configured and written back to YAML: ",
    "COMSOL 路径不存在：": "COMSOL path does not exist: ",
    "COMSOL 路径不是文件：": "COMSOL path is not a file: ",
    "请选择 comsolcompile.exe。": "Please select comsolcompile.exe.",
    "请选择 comsolbatch.exe。": "Please select comsolbatch.exe.",
    "comsolcompile_path 应指向 comsolcompile.exe：": "comsolcompile_path should point to comsolcompile.exe: ",
    "comsolbatch_path 应指向 comsolbatch.exe：": "comsolbatch_path should point to comsolbatch.exe: ",
    "COMSOL 路径检查失败。": "COMSOL path check failed.",
    "COMSOL 路径检查通过。": "COMSOL path check passed.",
})

def safe_java_file_stem(name: str) -> str:
    cleaned = []

    for ch in str(name):
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")

    stem = "".join(cleaned).strip("_")

    if not stem:
        stem = "PPE_model"

    if stem[0].isdigit():
        stem = f"Model_{stem}"

    return stem


class ComsolPathDialog(QDialog):
    def __init__(self, parent=None, comsolcompile_path: str = "", comsolbatch_path: str = ""):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle(parent.tr_text("配置 COMSOL 路径") if parent else "配置 COMSOL 路径")
        self.setMinimumWidth(800)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.setLayout(layout)

        hint_label = QLabel(self._tr("请选择本机 COMSOL 的 comsolcompile.exe 和 comsolbatch.exe。"))
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        self.comsolcompile_edit = QLineEdit(str(comsolcompile_path or ""))
        self.comsolcompile_edit.setMinimumHeight(34)
        self.comsolcompile_edit.setPlaceholderText("C:/Program Files/COMSOL/COMSOL64/Multiphysics/bin/win64/comsolcompile.exe")

        self.comsolbatch_edit = QLineEdit(str(comsolbatch_path or ""))
        self.comsolbatch_edit.setMinimumHeight(34)
        self.comsolbatch_edit.setPlaceholderText("C:/Program Files/COMSOL/COMSOL64/Multiphysics/bin/win64/comsolbatch.exe")

        layout.addLayout(
            self._make_path_row(
                self._tr("comsolcompile.exe 路径"),
                self.comsolcompile_edit,
                lambda: self._browse_exe(self.comsolcompile_edit, "选择 comsolcompile.exe"),
            )
        )
        layout.addLayout(
            self._make_path_row(
                self._tr("comsolbatch.exe 路径"),
                self.comsolbatch_edit,
                lambda: self._browse_exe(self.comsolbatch_edit, "选择 comsolbatch.exe"),
            )
        )

        check_row = QHBoxLayout()
        check_row.addStretch(1)
        self.check_button = QPushButton(self._tr("检查路径"))
        self.check_button.setObjectName("SecondaryButton")
        self.check_button.clicked.connect(lambda: self.check_paths(show_message=True))
        check_row.addWidget(self.check_button)
        layout.addLayout(check_row)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept_if_valid)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _tr(self, text: str) -> str:
        if self.parent_window is not None and hasattr(self.parent_window, "tr_text"):
            return self.parent_window.tr_text(text)
        return text

    def _make_path_row(self, label_text: str, editor: QLineEdit, browse_slot):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setMinimumWidth(190)
        row.addWidget(label)
        row.addWidget(editor, stretch=1)

        browse_button = QPushButton(self._tr("浏览..."))
        browse_button.setObjectName("GhostButton")
        browse_button.clicked.connect(browse_slot)
        row.addWidget(browse_button)
        return row

    def _browse_exe(self, editor: QLineEdit, title_key: str):
        start_dir = str(Path(editor.text().strip().strip('"')).parent) if editor.text().strip() else ""
        if start_dir and not Path(start_dir).exists():
            start_dir = ""

        path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr(title_key),
            start_dir,
            "Executable Files (*.exe);;All Files (*)",
        )
        if path:
            editor.setText(path)

    def get_paths(self) -> tuple[Path, Path]:
        comsolcompile_path = Path(self.comsolcompile_edit.text().strip().strip('"'))
        comsolbatch_path = Path(self.comsolbatch_edit.text().strip().strip('"'))
        return comsolcompile_path, comsolbatch_path

    def _path_errors(self) -> list[str]:
        comsolcompile_path, comsolbatch_path = self.get_paths()
        errors = []

        def check_one(label: str, path: Path, expected_name: str):
            path_text = str(path)
            if not path_text or path_text == ".":
                errors.append(self._tr(f"请选择 {expected_name}。"))
                return
            if not path.exists():
                errors.append(self._tr("COMSOL 路径不存在：") + path_text)
                return
            if not path.is_file():
                errors.append(self._tr("COMSOL 路径不是文件：") + path_text)
                return
            if path.name.lower() != expected_name.lower():
                errors.append(self._tr(f"{label} 应指向 {expected_name}：") + path_text)

        check_one("comsolcompile_path", comsolcompile_path, "comsolcompile.exe")
        check_one("comsolbatch_path", comsolbatch_path, "comsolbatch.exe")
        return errors

    def check_paths(self, show_message: bool = True) -> bool:
        errors = self._path_errors()
        if errors:
            if show_message:
                QMessageBox.warning(self, self._tr("COMSOL 路径配置错误"), "\n".join(errors))
            return False

        if show_message:
            QMessageBox.information(self, self._tr("路径检查通过"), self._tr("COMSOL 路径检查通过。"))
        return True

    def accept_if_valid(self):
        if self.check_paths(show_message=True):
            self.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("MainWindow")
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1260, 760)
        self.setMinimumSize(1120, 640)

        self.config_path = None
        self.output_java_path = None
        self.latest_run_dir = None
        self.worker = None
        self.cfg_data = None
        self.preview_pixmap = None
        self.is_comsol_running = False
        self.current_language = "zh"
        self._text_bindings = []
        self._page_bindings = []
        self._menu_bindings = []
        self._combo_bindings = []
        self._last_status_text = "就绪"
        self._last_status_type = "idle"

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter = self.main_splitter
        splitter.setHandleWidth(8)

        left_panel = QWidget()
        left_panel.setObjectName("PanelColumn")
        left_panel.setMinimumWidth(650)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)
        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_panel.setObjectName("PanelColumn")
        right_panel.setMinimumWidth(360)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(12)
        right_panel.setLayout(right_layout)

        left_scroll = QScrollArea()
        left_scroll.setObjectName("LeftPanelScroll")
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setWidget(left_panel)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([720, 540])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.config_label = QLabel("配置：未选择")
        self.config_label.setObjectName("pathLabel")
        self.config_label.setWordWrap(True)

        self.output_label = QLabel("Java：未选择")
        self.output_label.setObjectName("pathLabel")
        self.output_label.setWordWrap(True)

        self.comsol_note_label = QLabel(self.tr_text("注：运行此程序需接入 COMSOL"))
        self._bind_text(self.comsol_note_label, "注：运行此程序需接入 COMSOL")
        self.comsol_note_label.setObjectName("StatusNoteLabel")
        self.comsol_note_label.setWordWrap(True)

        self.comsol_status_label = QLabel(self.tr_text("COMSOL：未检查"))
        self.comsol_status_label.setObjectName("StatusNoteLabel")
        self.comsol_status_label.setWordWrap(False)
        self.comsol_status_label.setMinimumWidth(120)

        config_btn = QPushButton("打开 YAML")
        self._bind_text(config_btn, "打开 YAML")
        config_btn.setObjectName("GhostButton")
        config_btn.clicked.connect(self.select_config)

        save_config_btn = QPushButton("保存")
        self._bind_text(save_config_btn, "保存")
        save_config_btn.setObjectName("GhostButton")
        save_config_btn.clicked.connect(self.save_config)

        save_config_as_btn = QPushButton("另存为")
        self._bind_text(save_config_as_btn, "另存为")
        save_config_as_btn.setObjectName("GhostButton")
        save_config_as_btn.clicked.connect(self.save_config_as)

        output_btn = QPushButton("选择 Java 路径")
        self._bind_text(output_btn, "选择 Java 路径")
        output_btn.setObjectName("GhostButton")
        output_btn.clicked.connect(self.select_output)

        default_output_btn = QPushButton("使用默认路径")
        self._bind_text(default_output_btn, "使用默认路径")
        default_output_btn.setObjectName("GhostButton")
        default_output_btn.clicked.connect(
            lambda: self.apply_default_output_path(silent=False)
        )

        self.preview_btn = QPushButton("模型生成")
        self._bind_text(self.preview_btn, "模型生成")
        self.preview_btn.setObjectName("SecondaryButton")
        self.preview_btn.clicked.connect(self.run_preview)

        self.run_btn = QPushButton("仅生成模型文件")
        self._bind_text(self.run_btn, "仅生成模型文件")
        self.run_btn.setObjectName("SecondaryButton")
        self.run_btn.clicked.connect(self.run_export)

        self.run_comsol_btn = QPushButton("运行 COMSOL")
        self._bind_text(self.run_comsol_btn, "运行 COMSOL")
        self.run_comsol_btn.setObjectName("PrimaryButton")
        self.run_comsol_btn.clicked.connect(self.run_comsol)

        self.stop_comsol_btn = QPushButton("停止 COMSOL")
        self._bind_text(self.stop_comsol_btn, "停止 COMSOL")
        self.stop_comsol_btn.setObjectName("DangerButton")
        self.stop_comsol_btn.setEnabled(False)
        self.stop_comsol_btn.clicked.connect(self.stop_comsol)

        self.plot_csv_btn = QPushButton("读取 CSV")
        self._bind_text(self.plot_csv_btn, "读取 CSV")
        self.plot_csv_btn.setObjectName("SecondaryButton")
        self.plot_csv_btn.clicked.connect(self.plot_result_csv)

        self.status_label = QLabel(self.tr_text("状态：就绪"))
        self.status_label.setObjectName("StatusPill")
        self.status_label.setProperty("statusType", "idle")

        self._create_menu_bar()
        root_layout.addWidget(self.menu_bar)

        root_layout.addWidget(splitter, stretch=1)

        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("AppStatusBar")
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.addWidget(self.config_label, stretch=1)
        self.status_bar.addWidget(self.comsol_note_label, stretch=1)
        self.status_bar.addWidget(self.comsol_status_label, stretch=0)
        self.status_bar.addPermanentWidget(self.status_label)
        root_layout.addWidget(self.status_bar)

        param_group = QGroupBox()
        param_group.setObjectName("CardNoTitle")
        param_layout = QVBoxLayout()
        param_layout.setContentsMargins(14, 14, 14, 14)
        param_layout.setSpacing(12)
        param_group.setLayout(param_layout)

        param_header_layout = QVBoxLayout()
        param_header_layout.setContentsMargins(2, 0, 2, 4)
        param_header_layout.setSpacing(2)

        self.param_title_label = QLabel(self.tr_text("参数输入"))
        self._bind_text(self.param_title_label, "参数输入")
        self.param_title_label.setObjectName("ParamTitle")
        param_header_layout.addWidget(self.param_title_label)
        param_layout.addLayout(param_header_layout)

        param_body_layout = QHBoxLayout()
        param_body_layout.setContentsMargins(0, 0, 0, 0)
        param_body_layout.setSpacing(12)

        self.param_nav = QListWidget()
        self.param_nav.setObjectName("ParamNav")
                                                                          
                                                            
                                                                               
        self.param_nav.setFixedWidth(220)
        self.param_nav.setSpacing(5)
        self.param_nav.setWordWrap(True)
        self.param_nav.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.param_nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.param_stack = QStackedWidget()
        self.param_stack.setObjectName("ParamStack")

        param_body_layout.addWidget(self.param_nav)
        param_body_layout.addWidget(self.param_stack, stretch=1)
        param_layout.addLayout(param_body_layout, stretch=1)

        self._build_parameter_pages()
        self.param_nav.currentRowChanged.connect(self.param_stack.setCurrentIndex)
        self.param_nav.setCurrentRow(0)

        left_layout.addWidget(param_group, stretch=1)

                                 
        self.material_group = None

        self.advanced_group = self._build_advanced_settings_group()
        left_layout.addWidget(self.advanced_group, stretch=0)

        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter = self.right_splitter
        right_splitter.setHandleWidth(8)

        preview_group = QGroupBox()
        preview_group.setObjectName("CardNoTitle")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(10)
        preview_group.setLayout(preview_layout)

        self.preview_title_label = QLabel(self.tr_text("预览图"))
        self.preview_title_label.setObjectName("ParamTitle")
        self._bind_text(self.preview_title_label, "预览图")
        preview_layout.addWidget(self.preview_title_label)

        preview_tool_layout = QHBoxLayout()
        preview_tool_layout.setContentsMargins(0, 0, 0, 0)
        preview_tool_layout.setSpacing(8)
        preview_tool_layout.addStretch(1)

        self.preview_generate_btn = QPushButton("模型生成")
        self._bind_text(self.preview_generate_btn, "模型生成")
        self.preview_generate_btn.setObjectName("SmallToolButton")
        self.preview_generate_btn.clicked.connect(self.run_preview)

        self.preview_reset_btn = QPushButton("重置视图")
        self._bind_text(self.preview_reset_btn, "重置视图")
        self.preview_reset_btn.setObjectName("SmallToolButton")
        self.preview_reset_btn.clicked.connect(self.reset_preview_view)

        self.preview_export_btn = QPushButton("导出截图")
        self._bind_text(self.preview_export_btn, "导出截图")
        self.preview_export_btn.setObjectName("SmallToolButton")
        self.preview_export_btn.clicked.connect(self.export_preview_screenshot)

        self.preview_layer_btn = QPushButton("图层")
        self._bind_text(self.preview_layer_btn, "图层")
        self.preview_layer_btn.setObjectName("SmallToolButton")
        self.preview_layer_menu = QMenu(self.preview_layer_btn)
        self.action_layer_regions = self._add_layer_action(self.preview_layer_menu, "区域", "regions", True)
        self.action_layer_negative_particles = self._add_layer_action(self.preview_layer_menu, "负极颗粒", "negative_particles", True)
        self.action_layer_positive_particles = self._add_layer_action(self.preview_layer_menu, "正极颗粒", "positive_particles", True)
        self.action_layer_binders = self._add_layer_action(self.preview_layer_menu, "粘结剂", "binders", True)
        self.preview_layer_menu.addSeparator()
        self.action_layer_axes = self._add_layer_action(self.preview_layer_menu, "坐标轴", "axes", True)
        self.preview_layer_btn.setMenu(self.preview_layer_menu)

        preview_tool_layout.addWidget(self.preview_generate_btn)
        preview_tool_layout.addWidget(self.preview_reset_btn)
        preview_tool_layout.addWidget(self.preview_export_btn)
        preview_tool_layout.addWidget(self.preview_layer_btn)
        preview_layout.addLayout(preview_tool_layout)

        self.preview_view = PreviewImageView()
        self.preview_view.setMinimumHeight(160)

        preview_layout.addWidget(self.preview_view)

        log_group = QGroupBox()
        log_group.setObjectName("CardNoTitle")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(14, 14, 14, 14)
        log_layout.setSpacing(10)
        log_group.setLayout(log_layout)

        self.log_title_label = QLabel(self.tr_text("日志"))
        self.log_title_label.setObjectName("ParamTitle")
        self._bind_text(self.log_title_label, "日志")
        log_layout.addWidget(self.log_title_label)

        self.log_tabs = QTabWidget()
        self.log_tabs.setObjectName("LogTabs")
        self.log_tabs.setMinimumHeight(120)

        self.log_box = QTextEdit()
        self.log_box.setObjectName("LogTextEdit")
        self.log_box.setReadOnly(True)

        self.solver_log_box = QTextEdit()
        self.solver_log_box.setObjectName("LogTextEdit")
        self.solver_log_box.setReadOnly(True)
        self.solver_log_box.setPlaceholderText(self.tr_text("运行 COMSOL 后显示当前求解进度..."))

        self.log_tabs.addTab(self.log_box, self.tr_text("运行日志"))
        self.log_tabs.addTab(self.solver_log_box, self.tr_text("求解进度"))
        self.log_tabs.setCurrentIndex(0)
        log_layout.addWidget(self.log_tabs)

        self.solver_log_last_text = ""
        self.solver_log_active = False
        self.active_solver_log_path: Path | None = None
        self.solver_log_timer = QTimer(self)
        self.solver_log_timer.setInterval(1000)
        self.solver_log_timer.timeout.connect(self.refresh_solver_log)

        plot_group = QGroupBox()
        plot_group.setObjectName("CardNoTitle")
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(14, 14, 14, 14)
        plot_layout.setSpacing(10)
        plot_group.setLayout(plot_layout)

        self.plot_title_label = QLabel(self.tr_text("结果曲线"))
        self.plot_title_label.setObjectName("ParamTitle")
        self._bind_text(self.plot_title_label, "结果曲线")
        plot_layout.addWidget(self.plot_title_label)

        self.result_manager = ResultManager()
        self.result_manager.set_default_export_dir_provider(
            lambda: self.get_default_results_dir()
        )
        self.result_manager.import_requested.connect(self.plot_result_csv)
        self.result_manager.log_requested.connect(self.log)
        self.result_plot = self.result_manager.plot_canvas
        self.result_manager.setMinimumHeight(180)
        plot_layout.addWidget(self.result_manager)

        right_splitter.addWidget(preview_group)
        right_splitter.addWidget(plot_group)
        right_splitter.addWidget(log_group)

        right_splitter.setSizes([300, 240, 160])
        right_splitter.setCollapsible(0, False)
        right_splitter.setCollapsible(1, False)

        right_layout.addWidget(right_splitter)

        self.setLayout(root_layout)

        self.load_stylesheet()
        self.apply_language()

    def tr_text(self, text: str) -> str:
        if self.current_language == "en":
            return UI_TRANSLATIONS.get(text, text)
        return text

    def _bind_text(self, widget, key: str):
        self._text_bindings.append((widget, key))
        if hasattr(widget, "setText"):
            widget.setText(self.tr_text(key))
        return widget

    def _bind_menu(self, menu, key: str):
        self._menu_bindings.append((menu, key))
        menu.setTitle(self.tr_text(key))
        return menu

    def _set_combo_to_data(self, combo: QComboBox, data_value):
        for i in range(combo.count()):
            if combo.itemData(i) == data_value:
                combo.setCurrentIndex(i)
                return True
        return False

    def apply_language(self):
                                                               
        for menu, key in getattr(self, "_menu_bindings", []):
            menu.setTitle(self.tr_text(key))

        for widget, key in getattr(self, "_text_bindings", []):
            if hasattr(widget, "setText"):
                widget.setText(self.tr_text(key))
            elif hasattr(widget, "setTitle"):
                widget.setTitle(self.tr_text(key))

        for item, title_key, subtitle_key, title_label, subtitle_label in getattr(self, "_page_bindings", []):
            item.setText(self.tr_text(title_key))
            item.setToolTip(self.tr_text(subtitle_key))
            title_label.setText(self.tr_text(title_key))
            subtitle_label.setText(self.tr_text(subtitle_key))
            item.setSizeHint(QSize(204, 46 if self.current_language == "en" else 44))

                                                        
        if hasattr(self, "mesh_size_combo"):
            current_key = self.mesh_size_combo.currentData()
            self.mesh_size_combo.blockSignals(True)
            self.mesh_size_combo.clear()
            for key, hauto, zh, en in MESH_SIZE_OPTIONS:
                self.mesh_size_combo.addItem(en if self.current_language == "en" else zh, key)
            self._set_combo_to_data(self.mesh_size_combo, current_key or "normal")
            self.mesh_size_combo.blockSignals(False)

        if hasattr(self, "log_tabs"):
            self.log_tabs.setTabText(0, self.tr_text("运行日志"))
            self.log_tabs.setTabText(1, self.tr_text("求解进度"))
            self.solver_log_box.setPlaceholderText(self.tr_text("运行 COMSOL 后显示当前求解进度..."))

        for combo_name in [
            "electrolyte_material_combo",
            "negative_material_combo",
            "positive_material_combo",
        ]:
            combo = getattr(self, combo_name, None)
            if combo is not None:
                combo.setToolTip(self.tr_text("当前版本仅支持该材料"))

        if hasattr(self, "result_manager") and hasattr(self.result_manager, "set_language"):
            self.result_manager.set_language(self.current_language)

        self.update_config_label()
        self.update_output_label()
        self.update_comsol_status_label()
        self.update_status(self._last_status_text, self._last_status_type)
        self.load_stylesheet()
        app = QApplication.instance()
        if app is not None:
            if self.current_language == "en":
                app.setFont(QFont("Times New Roman", 11))
            else:
                app.setFont(QFont("Microsoft YaHei", 10))

    def set_language(self, language: str):
        if language not in {"zh", "en"}:
            return
        self.current_language = language
        if hasattr(self, "action_language_zh"):
            self.action_language_zh.setChecked(language == "zh")
        if hasattr(self, "action_language_en"):
            self.action_language_en.setChecked(language == "en")
        self.apply_language()

    def tr_message(self, text) -> str:
        text = str(text)
        if self.current_language != "en":
            return text
        if text in UI_TRANSLATIONS:
            return UI_TRANSLATIONS[text]
        prefix_map = [
            ("路径不存在：\n", "Path does not exist:\n"),
            ("截图导出失败：\n", "Screenshot export failed:\n"),
            ("配置已另存为：\n", "Config has been saved as:\n"),
            ("已从 YAML 重新载入参数：", "Reloaded parameters from YAML: "),
            ("参数已写回 YAML：", "Parameters written back to YAML: "),
            ("配置已另存为：", "Config has been saved as: "),
            ("已选择 Java 输出路径：", "Selected Java output path: "),
            ("已使用默认 Java 输出路径：", "Using default Java output path: "),
            ("COMSOL 路径已配置并写回 YAML：", "COMSOL paths configured and written back to YAML: "),
            ("COMSOL 路径不存在：", "COMSOL path does not exist: "),
            ("COMSOL 路径不是文件：", "COMSOL path is not a file: "),
            ("comsolcompile_path 应指向 comsolcompile.exe：", "comsolcompile_path should point to comsolcompile.exe: "),
            ("comsolbatch_path 应指向 comsolbatch.exe：", "comsolbatch_path should point to comsolbatch.exe: "),
        ]
        for zh, en in prefix_map:
            if text.startswith(zh):
                return en + text[len(zh):]

        translated = text
        for zh, en in sorted(UI_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
            translated = translated.replace(zh, en)
        phrase_map = [
            (" 不是合法数值。", " is not a valid number."),
            (" 不是合法整数。", " is not a valid integer."),
            (" 必须大于等于 ", " must be greater than or equal to "),
            (" 必须大于 ", " must be greater than "),
            (" 必须小于 ", " must be less than "),
            (" 必须在 ", " must be between "),
            (" 到 ", " and "),
            (" 之间。", "."),
            (" 不能大于 ", " cannot be greater than "),
            ("……还有 ", "...and "),
            (" 个错误未显示。", " more errors are not shown."),
        ]
        for zh, en in phrase_map:
            translated = translated.replace(zh, en)
        return translated

    def show_warning(self, title: str, message) -> None:
        QMessageBox.warning(self, self.tr_text(title), self.tr_message(message))

    def show_info(self, title: str, message) -> None:
        QMessageBox.information(self, self.tr_text(title), self.tr_message(message))

    def show_critical(self, title: str, message) -> None:
        QMessageBox.critical(self, self.tr_text(title), self.tr_message(message))

    def _make_number_editor(self, text: str, unit: str = "", integer: bool = False):
        editor = QLineEdit(str(text))
        editor.setObjectName("ParamNumberEdit")
        editor.setFixedWidth(132)
        editor.setMinimumHeight(38)
        editor.setMaximumHeight(38)
        editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        if integer:
            editor.setValidator(QIntValidator(1, 1000000, self))
        else:
            validator = QDoubleValidator(0.0, 1.0e12, 12, self)
            validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
            editor.setValidator(validator)

        field = self._make_parameter_field(editor, unit=unit)
        return editor, field

    def _make_form_label(self, text: str):
        label = QLabel(self.tr_text(text))
        label.setObjectName("FormRowLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._bind_text(label, text)
        return label

    def _make_material_combo(self, material_name: str):
        combo = QComboBox()
        combo.setObjectName("MaterialCombo")
        combo.setEditable(False)
        combo.addItem(material_name)
        combo.setCurrentIndex(0)
        combo.setMinimumWidth(360)
        combo.setToolTip(self.tr_text("当前版本仅支持该材料"))
        return combo

    def _make_locked_line_edit(self, text: str, unit: str = ""):
        editor = QLineEdit(str(text))
        editor.setObjectName("LockedLineEdit")
        editor.setReadOnly(True)
        editor.setFixedWidth(132)
        editor.setMinimumHeight(38)
        editor.setMaximumHeight(38)
        editor.setAlignment(Qt.AlignmentFlag.AlignRight)

        field = QWidget()
        field.setObjectName("ParamField")
        field.setMinimumHeight(44)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        field.setLayout(layout)

        layout.addWidget(editor)

        unit_text = unit if unit else " "
        unit_label = QLabel(unit_text)
        unit_label.setObjectName("ParamUnitLabel")
        if unit_text.strip():
            unit_label.setMinimumWidth(92 if len(unit_text) >= 7 else 64)
            unit_label.setToolTip(unit_text)
        else:
            unit_label.setMinimumWidth(56)
        unit_label.setMinimumHeight(38)
        unit_label.setMaximumHeight(38)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit_label)
        layout.addStretch(1)
        return field

    def _build_material_selection_group(self):
        material_group = QGroupBox()
        material_group.setObjectName("CardNoTitle")

        material_layout = QVBoxLayout()
        material_layout.setContentsMargins(14, 14, 14, 14)
        material_layout.setSpacing(12)
        material_group.setLayout(material_layout)

        self.material_title_label = QLabel(self.tr_text("材料选择"))
        self._bind_text(self.material_title_label, "材料选择")
        self.material_title_label.setObjectName("ParamTitle")
        material_layout.addWidget(self.material_title_label)

        material_form = make_form()
        material_form.setHorizontalSpacing(16)
        material_form.setVerticalSpacing(10)
        material_form.setContentsMargins(12, 4, 12, 4)

        self.electrolyte_material_combo = self._make_material_combo("LiPF6 in 3:7 EC:EMC")
        self.negative_material_combo = self._make_material_combo("Graphite, LixC6 MCMB")
        self.positive_material_combo = self._make_material_combo("NMC 111, LiNi0.33Mn0.33Co0.33O2")

        material_form.addRow(self._make_form_label("电解液材料"), self.electrolyte_material_combo)
        material_form.addRow(self._make_form_label("负极材料"), self.negative_material_combo)
        material_form.addRow(self._make_form_label("正极材料"), self.positive_material_combo)

        material_layout.addLayout(material_form)
        return material_group

    def _build_advanced_settings_group(self):
        advanced_group = QGroupBox()
        advanced_group.setObjectName("CardNoTitle")
        advanced_group.setMinimumHeight(300)
        advanced_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        advanced_layout = QVBoxLayout()
        advanced_layout.setContentsMargins(14, 14, 14, 14)
        advanced_layout.setSpacing(10)
        advanced_group.setLayout(advanced_layout)

        self.advanced_title_label = QLabel(self.tr_text("高级设置"))
        self.advanced_title_label.setObjectName("ParamTitle")
        self._bind_text(self.advanced_title_label, "高级设置")
        advanced_layout.addWidget(self.advanced_title_label)

        advanced_form = make_form()
        advanced_form.setHorizontalSpacing(16)
        advanced_form.setVerticalSpacing(10)
        advanced_form.setContentsMargins(12, 2, 12, 8)

        self.mesh_size_combo = QComboBox()
        self.mesh_size_combo.setObjectName("MaterialCombo")
        self.mesh_size_combo.setEditable(False)
        for key, hauto, zh, en in MESH_SIZE_OPTIONS:
            self.mesh_size_combo.addItem(en if self.current_language == "en" else zh, key)
        self._set_combo_to_data(self.mesh_size_combo, "normal")
        self.mesh_size_combo.setMinimumWidth(140)
        self.mesh_size_combo.setToolTip("对应 COMSOL 自动网格粗细等级")

        self.transient_max_iter_editor, transient_field = self._make_number_editor("100", "", integer=True)
        self.stationary_max_iter_editor, stationary_field = self._make_number_editor("100", "", integer=True)
        self.cutoff_voltage_editor, cutoff_field = self._make_number_editor("3.3", "V", integer=False)
        self.time_step_editor, time_step_field = self._make_number_editor("2", "s", integer=False)

        advanced_form.addRow(self._make_form_label("网格粗细设置"), self.mesh_size_combo)
        advanced_form.addRow(self._make_form_label("瞬态求解最大迭代次数"), transient_field)
        advanced_form.addRow(self._make_form_label("稳态求解最大迭代次数"), stationary_field)
        advanced_form.addRow(self._make_form_label("截至电压"), cutoff_field)
        advanced_form.addRow(self._make_form_label("步长"), time_step_field)

        advanced_layout.addLayout(advanced_form)
        return advanced_group

    def load_stylesheet(self):
        qss_path = Path(__file__).resolve().parent / "styles" / "app.qss"

        if qss_path.exists():
            qss = qss_path.read_text(encoding="utf-8")
            if getattr(self, "current_language", "zh") == "en":
                qss = qss.replace(
                    'font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;',
                    'font-family: "Times New Roman", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;'
                )
            self.setStyleSheet(qss)

    def _add_action(self, menu, text: str, slot=None, shortcut: str | None = None, enabled: bool = True):
        action = QAction(self.tr_text(text), self)
        action.setEnabled(enabled)
        self._bind_text(action, text)
        if shortcut:
            action.setShortcut(shortcut)
        if slot is not None:
            action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _add_layer_action(self, menu, text: str, layer_name: str, checked: bool = True):
        action = QAction(self.tr_text(text), self)
        self._bind_text(action, text)
        action.setCheckable(True)
        action.setChecked(checked)
        action.toggled.connect(
            lambda visible, name=layer_name: self.set_preview_layer_visible(name, visible)
        )
        menu.addAction(action)
        return action

    def _create_menu_bar(self):
        self.menu_bar = QMenuBar()
        self.menu_bar.setObjectName("MainMenuBar")

        file_menu = self.menu_bar.addMenu(self.tr_text("文件"))
        self._bind_menu(file_menu, "文件")
        self.action_open_yaml = self._add_action(file_menu, "打开 YAML...", self.select_config, "Ctrl+O")
        self.action_save_yaml = self._add_action(file_menu, "保存 YAML", self.save_config, "Ctrl+S")
        self.action_save_yaml_as = self._add_action(file_menu, "另存为 YAML...", self.save_config_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        self.language_menu = file_menu.addMenu(self.tr_text("语言"))
        self._bind_menu(self.language_menu, "语言")
        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)
        self.action_language_zh = QAction(self.tr_text("中文"), self)
        self.action_language_zh.setCheckable(True)
        self.action_language_zh.setChecked(True)
        self._bind_text(self.action_language_zh, "中文")
        self.action_language_zh.triggered.connect(lambda: self.set_language("zh"))
        self.language_action_group.addAction(self.action_language_zh)
        self.language_menu.addAction(self.action_language_zh)
        self.action_language_en = QAction("English", self)
        self.action_language_en.setCheckable(True)
        self._bind_text(self.action_language_en, "English")
        self.action_language_en.triggered.connect(lambda: self.set_language("en"))
        self.language_action_group.addAction(self.action_language_en)
        self.language_menu.addAction(self.action_language_en)
        file_menu.addSeparator()
        self.action_select_java_path = self._add_action(file_menu, "选择 Java 输出路径...", self.select_output)
        self.action_default_java_path = self._add_action(file_menu, "使用默认 Java 输出路径", lambda: self.apply_default_output_path(silent=False))
        file_menu.addSeparator()
        self.action_open_output_dir = self._add_action(file_menu, "打开输出目录", self.open_output_dir)
        file_menu.addSeparator()
        self._add_action(file_menu, "退出", self.close)

        parameter_menu = self.menu_bar.addMenu(self.tr_text("参数"))
        self._bind_menu(parameter_menu, "参数")
        self.action_validate_params = self._add_action(parameter_menu, "参数校验", self.validate_parameters)
        self.action_reload_yaml = self._add_action(parameter_menu, "从 YAML 重新载入", self.reload_config_from_disk)
        self.action_write_yaml = self._add_action(parameter_menu, "写回 YAML", self.save_config)

        geometry_menu = self.menu_bar.addMenu(self.tr_text("几何"))
        self._bind_menu(geometry_menu, "几何")
        self.action_refresh_preview = self._add_action(geometry_menu, "模型生成", self.run_preview)
        self.action_reset_preview = self._add_action(geometry_menu, "重置视图", self.reset_preview_view)
        self.action_export_preview_screenshot = self._add_action(geometry_menu, "导出当预览图...", self.export_preview_screenshot)
        geometry_menu.addSeparator()
        geometry_layer_menu = geometry_menu.addMenu(self.tr_text("图层显示"))
        self._bind_menu(geometry_layer_menu, "图层显示")
        self.action_menu_layer_regions = self._add_layer_action(geometry_layer_menu, "区域", "regions", True)
        self.action_menu_layer_negative_particles = self._add_layer_action(geometry_layer_menu, "负极颗粒", "negative_particles", True)
        self.action_menu_layer_positive_particles = self._add_layer_action(geometry_layer_menu, "正极颗粒", "positive_particles", True)
        self.action_menu_layer_binders = self._add_layer_action(geometry_layer_menu, "粘结剂", "binders", True)
        geometry_layer_menu.addSeparator()
        self.action_menu_layer_axes = self._add_layer_action(geometry_layer_menu, "坐标轴", "axes", True)

        compute_menu = self.menu_bar.addMenu(self.tr_text("计算"))
        self._bind_menu(compute_menu, "计算")
        self.action_configure_comsol = self._add_action(compute_menu, "配置 COMSOL 路径...", self.configure_comsol_paths)
        self.action_check_comsol_paths = self._add_action(compute_menu, "检查 COMSOL 路径", self.check_comsol_paths_action)
        compute_menu.addSeparator()
        self.action_export_java = self._add_action(compute_menu, "仅生成模型文件", self.run_export)
        self.action_run_comsol = self._add_action(compute_menu, "运行 COMSOL", self.run_comsol)
        self.action_stop_comsol = self._add_action(compute_menu, "停止 COMSOL", self.stop_comsol, enabled=False)
        compute_menu.addSeparator()
        self.action_clear_solver_log = self._add_action(compute_menu, "清空求解进度", self.clear_solver_log_view)

        result_menu = self.menu_bar.addMenu(self.tr_text("结果"))
        self._bind_menu(result_menu, "结果")
        self.action_plot_csv = self._add_action(result_menu, "导入CSV文件", self.plot_result_csv)
        self.action_clear_plot = self._add_action(result_menu, "清空", self.clear_result_plot)
        self.action_export_plot = self._add_action(result_menu, "导出曲线图...", self.export_result_plot)
        self.action_open_result_dir = self._add_action(result_menu, "打开结果目录", self.open_result_dir)

        view_menu = self.menu_bar.addMenu(self.tr_text("视图"))
        self._bind_menu(view_menu, "视图")
        self.action_reset_layout = self._add_action(view_menu, "重置布局", self.reset_layout)

        help_menu = self.menu_bar.addMenu(self.tr_text("帮助"))
        self._bind_menu(help_menu, "帮助")
        self.action_about = self._add_action(help_menu, "关于 PPE Model Studio", self.show_about_dialog)

    def set_action_enabled(self, name: str, enabled: bool):
        action = getattr(self, name, None)
        if action is not None:
            action.setEnabled(enabled)

    def open_path_in_explorer(self, path: Path):
        path = Path(path)
        if not path.exists():
            self.show_warning("路径不存在", f"路径不存在：\n{path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_output_dir(self):
        project_dir = self.get_project_dir_from_config()
        output_dir = project_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        self.open_path_in_explorer(output_dir)

    def open_result_dir(self):
        if self.latest_run_dir is not None:
            result_dir = Path(self.latest_run_dir) / "results"
        else:
            result_dir = self.get_project_dir_from_config() / "output" / "runs"
        result_dir.mkdir(parents=True, exist_ok=True)
        self.open_path_in_explorer(result_dir)

    def reload_config_from_disk(self):
        if self.config_path is None:
            self.show_warning("缺少配置文件", "请先选择 YAML 配置文件。")
            return False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.cfg_data = yaml.safe_load(f) or {}
            self.load_config_to_widgets()
            self.apply_default_output_path(silent=True)
            self.update_config_label()
            self.update_comsol_status_label()
            self.update_status("配置已重新载入", "success")
            self.log(f"已从 YAML 重新载入参数：{self.config_path}")
            return True
        except Exception as e:
            self.show_critical("重新载入失败", str(e))
            self.update_status("重新载入失败", "error")
            return False

    def set_preview_layer_visible(self, layer_name: str, visible: bool):
        if hasattr(self, "preview_view"):
            self.preview_view.set_layer_visible(layer_name, visible)

                                           
        action_pairs = {
            "regions": ["action_layer_regions", "action_menu_layer_regions"],
            "negative_particles": ["action_layer_negative_particles", "action_menu_layer_negative_particles"],
            "positive_particles": ["action_layer_positive_particles", "action_menu_layer_positive_particles"],
            "binders": ["action_layer_binders", "action_menu_layer_binders"],
            "axes": ["action_layer_axes", "action_menu_layer_axes"],
        }

        for action_name in action_pairs.get(layer_name, []):
            action = getattr(self, action_name, None)
            if action is not None and action.isChecked() != bool(visible):
                action.blockSignals(True)
                action.setChecked(bool(visible))
                action.blockSignals(False)

    def export_preview_screenshot(self):
        if not hasattr(self, "preview_view") or not self.preview_view.has_content:
            self.show_warning("无法导出", "当前没有可导出的预览内容。")
            return

        if self.latest_run_dir is not None:
            default_dir = Path(self.latest_run_dir) / "preview"
        else:
            default_dir = self.get_project_dir_from_config() / "output" / "runs" / "screenshots"
        default_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = default_dir / f"preview_screenshot_{timestamp}.png"

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr_text("导出当前预览截图"),
            str(default_path),
            "PNG Image (*.png)"
        )

        if not path:
            return

        output_path = Path(path)
        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(".png")

        ok = self.preview_view.export_view_screenshot(output_path)
        if ok:
            self.log(f"当前预览截图已导出：{output_path}")
            self.update_status("截图已导出", "success")
        else:
            self.show_warning("导出失败", f"截图导出失败：\n{output_path}")
            self.update_status("截图导出失败", "error")

    def reset_preview_view(self):
        if hasattr(self, "preview_view") and self.preview_view.has_content:
            self.preview_view.reset_view()
            self.log("预览视图已重置。")
        else:
            self.log("当前没有可重置的预览内容。")

    def clear_solver_log_view(self):
        self.solver_log_box.clear()
        self.solver_log_last_text = ""
        self.log("求解进度显示已清空。")

    def clear_result_plot(self):
        try:
            self.result_manager.clear_results()
            self.log("结果曲线已清空。")
        except Exception as e:
            self.show_warning("清空失败", str(e))

    def export_result_plot(self):
        try:
            self.result_manager.export_current_plot(self)
        except Exception as e:
            self.show_warning("导出失败", str(e))

    def reset_layout(self):
        if hasattr(self, "main_splitter"):
            self.main_splitter.setSizes([720, 540])
        if hasattr(self, "right_splitter"):
            self.right_splitter.setSizes([300, 240, 160])
        self.log("界面布局已重置。")

    def show_about_dialog(self):
        if getattr(self, "current_language", "zh") == "en":
            message = (
                f"{APP_NAME} {APP_VERSION}\n\n"
                "A local research and teaching tool for two-dimensional particle-packing electrode models.\n\n"
                "Main features:\n"
                "- YAML-based parameter configuration and validation\n"
                "- 2D particle / binder structure generation\n"
                "- Interactive model preview with layer controls\n"
                "- COMSOL Java export and COMSOL batch automation\n"
                "- COMSOL path configuration and path checking in the GUI\n"
                "- Run-based output folders for JSON, preview images, Java, logs, MPH files, and CSV results\n"
                "- CSV voltage curve import, plotting, clearing, and image export\n\n"
                "Runtime note:\n"
                "Preview generation and CSV plotting do not require COMSOL.\n"
                "Generating MPH files and running simulations require a local COMSOL installation and valid COMSOL paths."
            )
        else:
            message = (
                f"{APP_NAME} {APP_VERSION}\n\n"
                "二维颗粒堆积电极模型本地建模、教学演示与科研辅助软件。\n\n"
                "主要功能：\n"
                "- YAML 参数配置与参数校验\n"
                "- 二维颗粒 / 粘结剂结构生成\n"
                "- 交互式结构预览与图层控制\n"
                "- COMSOL Java 模型导出与 COMSOL batch 自动运行\n"
                "- GUI 内配置和检查 COMSOL 路径\n"
                "- 按运行时间自动生成独立 run 输出目录\n"
                "- CSV 电压曲线导入、绘图、清空与图像导出\n\n"
                "运行说明：\n"
                "结构预览和 CSV 绘图不需要 COMSOL。\n"
                "生成 MPH 文件和运行仿真需要本机安装 COMSOL，并在软件中正确配置 COMSOL 路径。"
            )

        QMessageBox.about(
            self,
            self.tr_text("关于 PPE Model Studio"),
            message,
        )

    def update_status(self, text: str, status_type: str = "idle"):
        if not hasattr(self, "status_label"):
            return

        self._last_status_text = text
        self._last_status_type = status_type
        prefix = "Status" if getattr(self, "current_language", "zh") == "en" else "状态"
        self.status_label.setText(f"{prefix}：{self.tr_text(text)}")
        self.status_label.setProperty("statusType", status_type)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def update_config_label(self):
        if self.config_path is None:
            self.config_label.setText(self.tr_text("配置：未选择"))
            self.config_label.setToolTip("")
            return

        path = Path(self.config_path)
        prefix = "Config" if getattr(self, "current_language", "zh") == "en" else "配置"
        self.config_label.setText(f"{prefix}：{path.name}")
        self.config_label.setToolTip(str(path))

    def update_output_label(self):
        if self.output_java_path is None:
            self.output_label.setText(self.tr_text("Java：未选择"))
            self.output_label.setToolTip("")
            return

        path = Path(self.output_java_path)
        self.output_label.setText(f"Java：{path.name}")
        self.output_label.setToolTip(str(path))

    def _make_parameter_field(self, editor, unit: str = "", rule: str = ""):
        field = QWidget()
        field.setObjectName("ParamField")
        field.setMinimumHeight(44)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        field.setLayout(layout)

        layout.addWidget(editor)

                                      
                                     
        unit_text = unit if unit else " "
        unit_label = QLabel(unit_text)
        unit_label.setObjectName("ParamUnitLabel")
        if unit_text.strip():
            unit_label.setMinimumWidth(88 if len(unit_text) >= 7 else 62)
            unit_label.setToolTip(unit_text)
        else:
            unit_label.setMinimumWidth(56)
        unit_label.setMinimumHeight(38)
        unit_label.setMaximumHeight(38)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit_label)

        layout.addStretch(1)
        return field

    def _add_param_row(self, form, label: str, editor, unit: str = "", rule: str = "", tooltip: str | None = None):
        field = self._make_parameter_field(editor, unit=unit, rule=rule)
        if tooltip:
            editor.setToolTip(tooltip)
            field.setToolTip(tooltip)
        form.addRow(self.tr_text(label), field)
        label_widget = form.labelForField(field)
        if label_widget is not None:
            self._bind_text(label_widget, label)

    def _add_parameter_page(self, title: str, subtitle: str, form, min_height: int = 220):
        page = QWidget()
        page.setObjectName("ParamPage")

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(14, 12, 14, 14)
        page_layout.setSpacing(10)
        page.setLayout(page_layout)

        title_label = QLabel(self.tr_text(title))
        title_label.setObjectName("ParamPageTitle")

        subtitle_label = QLabel(self.tr_text(subtitle))
        subtitle_label.setObjectName("ParamPageSubtitle")
        subtitle_label.setWordWrap(True)

        page_layout.addWidget(title_label)
        page_layout.addWidget(subtitle_label)
        page_layout.addWidget(make_scroll_tab(form, min_height), stretch=1)

        item = QListWidgetItem(self.tr_text(title))
        item.setToolTip(self.tr_text(subtitle))
        item.setSizeHint(QSize(204, 44))
        self.param_nav.addItem(item)
        self.param_stack.addWidget(page)
        self._page_bindings.append((item, title, subtitle, title_label, subtitle_label))

    def _build_parameter_pages(self):
        battery_geometry_form = make_form()

        self.geo_width_h = make_float_box()
        self.geo_sep_length = make_float_box()
        self.geo_pos_length = make_float_box()
        self.geo_neg_length = make_float_box()

        self._add_param_row(battery_geometry_form, "电池宽度", self.geo_width_h, "m", "> 0", "battery.width_h")
        self._add_param_row(battery_geometry_form, "隔膜长度", self.geo_sep_length, "m", "> 0", "battery.sep_length")
        self._add_param_row(battery_geometry_form, "正极长度", self.geo_pos_length, "m", "> 0", "battery.pos_length")
        self._add_param_row(battery_geometry_form, "负极长度", self.geo_neg_length, "m", "> 0", "battery.neg_length")

        self._add_parameter_page(
            "电池几何",
            "设置二维电池区域尺寸，包括宽度、隔膜长度和正负极长度",
            battery_geometry_form,
            min_height=170,
        )

        material_form = make_form()
        material_form.setHorizontalSpacing(16)
        material_form.setVerticalSpacing(16)
        material_form.setContentsMargins(12, 12, 12, 12)

        self.electrolyte_material_combo = self._make_material_combo("LiPF6 in 3:7 EC:EMC")
        self.negative_material_combo = self._make_material_combo("Graphite, LixC6 MCMB")
        self.positive_material_combo = self._make_material_combo("NMC 111, LiNi0.33Mn0.33Co0.33O2")

        material_form.addRow(self._make_form_label("电解液材料"), self.electrolyte_material_combo)
        material_form.addRow(self._make_form_label("负极材料"), self.negative_material_combo)
        material_form.addRow(self._make_form_label("正极材料"), self.positive_material_combo)

        self._add_parameter_page(
            "材料选择",
            "选择电解液、负极和正极材料；当前版本材料选项固定，用于查看材料配置",
            material_form,
            min_height=170,
        )

        pos_structure_form = make_form()

        self.geo_pos_active_fraction = make_float_box()
        self.geo_pos_binder_fraction = make_float_box()
        self.geo_pos_particle_mean_diameter = make_float_box()
        self.geo_pos_particle_diameter_dispersion = make_float_box()
        self.geo_pos_particle_lognormal_std = make_float_box()
        self.geo_pos_binder_width_dispersion = make_float_box()
        self.geo_pos_binder_lognormal_std = make_float_box()

        self._add_param_row(pos_structure_form, "正极活性材料体积分数", self.geo_pos_active_fraction, "", "0–1；总和≤1", "positive_electrode.active_fraction")
        self._add_param_row(pos_structure_form, "正极粘结剂体积分数", self.geo_pos_binder_fraction, "", "0–1；总和≤1", "positive_electrode.binder_fraction")
        self._add_param_row(pos_structure_form, "正极颗粒平均直径", self.geo_pos_particle_mean_diameter, "m", "> 0", "positive_electrode.particle.mean_diameter")
        self._add_param_row(pos_structure_form, "正极颗粒直径离散程度", self.geo_pos_particle_diameter_dispersion, "", "≥0 且 <1", "positive_electrode.particle.diameter_dispersion")
        self._add_param_row(pos_structure_form, "正极颗粒对数正态标准差", self.geo_pos_particle_lognormal_std, "", "≥ 0", "positive_electrode.particle.lognormal_std")
        self._add_param_row(pos_structure_form, "正极粘结剂宽度离散程度", self.geo_pos_binder_width_dispersion, "", "≥0 且 <1", "positive_electrode.binder.width_dispersion")
        self._add_param_row(pos_structure_form, "正极粘结剂对数正态标准差", self.geo_pos_binder_lognormal_std, "", "≥ 0", "positive_electrode.binder.lognormal_std")

        self._add_parameter_page(
            "正极结构",
            "设置正极活性材料、颗粒粒径分布和粘结剂网络相关参数",
            pos_structure_form,
            min_height=285,
        )

        neg_structure_form = make_form()

        self.geo_neg_active_fraction = make_float_box()
        self.geo_neg_binder_fraction = make_float_box()
        self.geo_neg_particle_mean_diameter = make_float_box()
        self.geo_neg_particle_diameter_dispersion = make_float_box()
        self.geo_neg_particle_lognormal_std = make_float_box()
        self.geo_neg_binder_width_dispersion = make_float_box()
        self.geo_neg_binder_lognormal_std = make_float_box()

        self._add_param_row(neg_structure_form, "负极活性材料体积分数", self.geo_neg_active_fraction, "", "0–1；总和≤1", "negative_electrode.active_fraction")
        self._add_param_row(neg_structure_form, "负极粘结剂体积分数", self.geo_neg_binder_fraction, "", "0–1；总和≤1", "negative_electrode.binder_fraction")
        self._add_param_row(neg_structure_form, "负极颗粒平均直径", self.geo_neg_particle_mean_diameter, "m", "> 0", "negative_electrode.particle.mean_diameter")
        self._add_param_row(neg_structure_form, "负极颗粒直径离散程度", self.geo_neg_particle_diameter_dispersion, "", "≥0 且 <1", "negative_electrode.particle.diameter_dispersion")
        self._add_param_row(neg_structure_form, "负极颗粒对数正态标准差", self.geo_neg_particle_lognormal_std, "", "≥ 0", "negative_electrode.particle.lognormal_std")
        self._add_param_row(neg_structure_form, "负极粘结剂宽度离散程度", self.geo_neg_binder_width_dispersion, "", "≥0 且 <1", "negative_electrode.binder.width_dispersion")
        self._add_param_row(neg_structure_form, "负极粘结剂对数正态标准差", self.geo_neg_binder_lognormal_std, "", "≥ 0", "negative_electrode.binder.lognormal_std")

        self._add_parameter_page(
            "负极结构",
            "设置负极活性材料、颗粒粒径分布、粘结剂网络和集流体连接参数",
            neg_structure_form,
            min_height=285,
        )

        battery_electrochem_form = make_form()

        self.ec_cl_init = make_float_box()
        self.ec_c_rate = make_float_box()

        self._add_param_row(battery_electrochem_form, "电解液初始盐浓度", self.ec_cl_init, "mol/m³", "> 0", "electrochemistry.electrolyte.cl_init")
        self._add_param_row(battery_electrochem_form, "充放电循环倍率", self.ec_c_rate, "", "> 0", "electrochemistry.cycling.c_rate")

        self._add_parameter_page(
            "电池电化学",
            "设置电解液初始浓度和循环倍率等全局电化学参数",
            battery_electrochem_form,
            min_height=120,
        )

        pos_electrochem_form = make_form()

        self.ec_pos_soc0 = make_float_box()
        self.ec_pos_k0 = make_float_box()
        self.ec_pos_r_film = make_float_box()
        self.ec_pos_c_dl = make_float_box()

        self._add_param_row(pos_electrochem_form, "正极初始 SOC", self.ec_pos_soc0, "", "0–1", "electrochemistry.positive.soc0")
        self._add_param_row(pos_electrochem_form, "正极反应速率常数 k0", self.ec_pos_k0, "mol/m²/s", "> 0", "electrochemistry.positive.k0")
        self._add_param_row(pos_electrochem_form, "正极 SEI/界面膜电阻", self.ec_pos_r_film, "Ω·m²", "≥ 0", "electrochemistry.positive.r_film")
        self._add_param_row(pos_electrochem_form, "正极双电层电容", self.ec_pos_c_dl, "F/m²", "≥ 0", "electrochemistry.positive.c_dl")

        self._add_parameter_page(
            "正极电化学",
            "设置正极初始状态、反应速率常数、界面膜电阻和双电层电容",
            pos_electrochem_form,
            min_height=190,
        )

        neg_electrochem_form = make_form()

        self.ec_neg_soc0 = make_float_box()
        self.ec_neg_k0 = make_float_box()
        self.ec_neg_r_film = make_float_box()
        self.ec_neg_c_dl = make_float_box()

        self._add_param_row(neg_electrochem_form, "负极初始 SOC", self.ec_neg_soc0, "", "0–1", "electrochemistry.negative.soc0")
        self._add_param_row(neg_electrochem_form, "负极反应速率常数 k0", self.ec_neg_k0, "mol/m²/s", "> 0", "electrochemistry.negative.k0")
        self._add_param_row(neg_electrochem_form, "负极 SEI/界面膜电阻", self.ec_neg_r_film, "Ω·m²", "≥ 0", "electrochemistry.negative.r_film")
        self._add_param_row(neg_electrochem_form, "负极双电层电容", self.ec_neg_c_dl, "F/m²", "≥ 0", "electrochemistry.negative.c_dl")

        self._add_parameter_page(
            "负极电化学",
            "设置负极初始状态、反应速率常数、界面膜电阻和双电层电容",
            neg_electrochem_form,
            min_height=190,
        )

    def _build_geometry_tabs(self):
        battery_form = make_form()

        self.geo_width_h = make_float_box()
        self.geo_sep_length = make_float_box()
        self.geo_pos_length = make_float_box()
        self.geo_neg_length = make_float_box()

        battery_form.addRow("电池宽度[m]", self.geo_width_h)
        battery_form.addRow("隔膜长度[m]", self.geo_sep_length)
        battery_form.addRow("正极长度[m]", self.geo_pos_length)
        battery_form.addRow("负极长度[m]", self.geo_neg_length)

        pos_form = make_form()

        self.geo_pos_active_fraction = make_float_box()
        self.geo_pos_binder_fraction = make_float_box()
        self.geo_pos_particle_mean_diameter = make_float_box()
        self.geo_pos_particle_diameter_dispersion = make_float_box()
        self.geo_pos_particle_lognormal_std = make_float_box()
        self.geo_pos_binder_width_dispersion = make_float_box()
        self.geo_pos_binder_lognormal_std = make_float_box()

        pos_form.addRow("正极活性材料体积分数", self.geo_pos_active_fraction)
        pos_form.addRow("正极粘结剂体积分数", self.geo_pos_binder_fraction)
        pos_form.addRow("正极颗粒平均直径 [m]", self.geo_pos_particle_mean_diameter)
        pos_form.addRow("正极颗粒直径离散程度", self.geo_pos_particle_diameter_dispersion)
        pos_form.addRow("正极颗粒对数正态标准差", self.geo_pos_particle_lognormal_std)
        pos_form.addRow("正极粘结剂宽度离散程度", self.geo_pos_binder_width_dispersion)
        pos_form.addRow("正极粘结剂对数正态标准差", self.geo_pos_binder_lognormal_std)

        neg_form = make_form()

        self.geo_neg_active_fraction = make_float_box()
        self.geo_neg_binder_fraction = make_float_box()
        self.geo_neg_particle_mean_diameter = make_float_box()
        self.geo_neg_particle_diameter_dispersion = make_float_box()
        self.geo_neg_particle_lognormal_std = make_float_box()
        self.geo_neg_binder_width_dispersion = make_float_box()
        self.geo_neg_binder_lognormal_std = make_float_box()

        neg_form.addRow("负极活性材料体积分数", self.geo_neg_active_fraction)
        neg_form.addRow("负极粘结剂体积分数", self.geo_neg_binder_fraction)
        neg_form.addRow("负极颗粒平均直径 [m]", self.geo_neg_particle_mean_diameter)
        neg_form.addRow("负极颗粒直径离散程度", self.geo_neg_particle_diameter_dispersion)
        neg_form.addRow("负极颗粒对数正态标准差", self.geo_neg_particle_lognormal_std)
        neg_form.addRow("负极粘结剂宽度离散程度", self.geo_neg_binder_width_dispersion)
        neg_form.addRow("负极粘结剂对数正态标准差", self.geo_neg_binder_lognormal_std)

        self.geometry_tabs.setMinimumHeight(260)

        self.geometry_tabs.addTab(make_scroll_tab(battery_form, 170), "电池")
        self.geometry_tabs.addTab(make_scroll_tab(pos_form, 285), "正极材料")
        self.geometry_tabs.addTab(make_scroll_tab(neg_form, 320), "负极材料")

    def _build_electrochem_tabs(self):
        battery_form = make_form()

        self.ec_cl_init = make_float_box()
        self.ec_c_rate = make_float_box()

        battery_form.addRow("电解液初始盐浓度", self.ec_cl_init)
        battery_form.addRow("充放电循环倍率", self.ec_c_rate)

        pos_form = make_form()

        self.ec_pos_soc0 = make_float_box()
        self.ec_pos_k0 = make_float_box()
        self.ec_pos_r_film = make_float_box()
        self.ec_pos_c_dl = make_float_box()

        pos_form.addRow("正极初始 SOC", self.ec_pos_soc0)
        pos_form.addRow("正极反应速率常数", self.ec_pos_k0)
        pos_form.addRow("正极 SEI/界面膜电阻", self.ec_pos_r_film)
        pos_form.addRow("正极双电层电容", self.ec_pos_c_dl)

        neg_form = make_form()

        self.ec_neg_soc0 = make_float_box()
        self.ec_neg_k0 = make_float_box()
        self.ec_neg_r_film = make_float_box()
        self.ec_neg_c_dl = make_float_box()

        neg_form.addRow("负极初始 SOC", self.ec_neg_soc0)
        neg_form.addRow("负极反应速率常数", self.ec_neg_k0)
        neg_form.addRow("负极 SEI/界面膜电阻", self.ec_neg_r_film)
        neg_form.addRow("负极双电层电容", self.ec_neg_c_dl)

        self.electrochem_tabs.setMinimumHeight(190)

        self.electrochem_tabs.addTab(make_scroll_tab(battery_form, 120), "电池")
        self.electrochem_tabs.addTab(make_scroll_tab(pos_form, 190), "正极材料")
        self.electrochem_tabs.addTab(make_scroll_tab(neg_form, 190), "负极材料")

    def log(self, message: str):
        time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = str(message)

        lines = message.splitlines()
        if not lines:
            lines = [""]

        for line in lines:
            self.log_box.append(f"[{time_text}] {line}")

        self.log_box.ensureCursorVisible()

    def set_preview_image(self, image_path):
        image_path = Path(image_path)

        if not image_path.exists():
            self.log(f"预览图不存在：{image_path}")
            return False

        ok = self.preview_view.set_image(image_path)

        if ok:
            self.log(f"预览图已显示：{image_path}")
        else:
            self.log(f"预览图读取失败：{image_path}")

        return ok

    def set_preview_model(self, json_path, fallback_image_path=None):
        json_path = Path(json_path)

        if not json_path.exists():
            self.log(f"交互预览 JSON 不存在：{json_path}")
            if fallback_image_path:
                return self.set_preview_image(fallback_image_path)
            return False

        try:
            ok = self.preview_view.set_model_json(json_path)
        except Exception as e:
            self.log(f"交互式模型预览绘制异常，尝试显示 PNG 预览图：{e}")
            ok = False

        if ok:
            self.log(f"交互式模型预览已显示：{json_path}")
            return True

        self.log(f"交互式模型预览读取失败，尝试显示 PNG 预览图：{json_path}")

        if fallback_image_path:
            return self.set_preview_image(fallback_image_path)

        return False

    def update_preview_from_result(self, result: dict):
        json_path = result.get("json_path")
        preview_path = result.get("preview_path")

        if json_path:
            shown = self.set_preview_model(json_path, fallback_image_path=preview_path)
            if shown:
                return

        if preview_path:
            self.set_preview_image(preview_path)

    def get_project_dir_from_app(self) -> Path:
                                                           
                                                                       
        return get_app_root()

    def get_default_config_dir(self) -> Path:
        return self.get_project_dir_from_app() / "config"

    def get_project_dir_from_config(self) -> Path:
        if self.config_path is None:
            return self.get_project_dir_from_app()

        if self.config_path.parent.name.lower() == "config":
            return self.config_path.parent.parent

        return self.config_path.parent

    def build_default_java_path(self) -> Path:
        if self.config_path is None:
            raise ValueError("请先选择 YAML 配置文件。")

        if self.cfg_data is None:
            raise ValueError("请先加载 YAML 配置文件。")

        cfg = self.cfg_data
        project_dir = self.get_project_dir_from_config()

        java_cfg = cfg.get("comsol", {}).get("java", {})

        java_output_dir_raw = java_cfg.get("java_output_dir", "./output/java")
        java_output_dir = Path(java_output_dir_raw)

        if not java_output_dir.is_absolute():
            java_output_dir = project_dir / java_output_dir

        class_name = (
                java_cfg.get("class_name")
                or cfg.get("project", {}).get("case_name")
                or self.config_path.stem
        )

        java_stem = safe_java_file_stem(class_name)

        return java_output_dir / f"{java_stem}.java"

    def apply_default_output_path(self, silent: bool = False):
        try:
            default_path = self.build_default_java_path()

            self.output_java_path = default_path
            self.update_output_label()

            if not silent:
                self.log(f"已使用默认 Java 输出路径：{self.output_java_path}")

            return True

        except Exception as e:
            if not silent:
                self.show_warning("无法生成默认路径", str(e))
            return False

    def select_config(self):
        default_config_dir = self.get_default_config_dir()
        default_config_dir.mkdir(parents=True, exist_ok=True)

        dialog = QFileDialog(self, self.tr_text("选择 YAML 配置文件"))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("YAML Files (*.yaml *.yml)")
        dialog.setDirectory(str(default_config_dir))
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        if not dialog.exec():
            return

        selected_files = dialog.selectedFiles()
        if not selected_files:
            return

        self.config_path = Path(selected_files[0])
        self.update_config_label()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.cfg_data = yaml.safe_load(f) or {}

            self.load_config_to_widgets()
            self.apply_default_output_path(silent=True)
            self.update_comsol_status_label()
            self.update_status("配置已加载", "success")
            self.log("参数已载入，并已自动推荐 Java 输出路径。")

        except Exception as e:
            self.show_critical("读取失败", str(e))

    def load_config_to_widgets(self):
        cfg = self.cfg_data

        self.geo_width_h.set_value(cfg["battery"]["width_h"])
        self.geo_sep_length.set_value(cfg["battery"]["sep_length"])
        self.geo_pos_length.set_value(cfg["battery"]["pos_length"])
        self.geo_neg_length.set_value(cfg["battery"]["neg_length"])

        self.geo_pos_active_fraction.set_value(cfg["positive_electrode"]["active_fraction"])
        self.geo_pos_binder_fraction.set_value(cfg["positive_electrode"]["binder_fraction"])
        self.geo_pos_particle_mean_diameter.set_value(cfg["positive_electrode"]["particle"]["mean_diameter"])
        self.geo_pos_particle_diameter_dispersion.set_value(
            cfg["positive_electrode"]["particle"]["diameter_dispersion"])
        self.geo_pos_particle_lognormal_std.set_value(cfg["positive_electrode"]["particle"]["lognormal_std"])
        self.geo_pos_binder_width_dispersion.set_value(cfg["positive_electrode"]["binder"]["width_dispersion"])
        self.geo_pos_binder_lognormal_std.set_value(cfg["positive_electrode"]["binder"]["lognormal_std"])

        self.geo_neg_active_fraction.set_value(cfg["negative_electrode"]["active_fraction"])
        self.geo_neg_binder_fraction.set_value(cfg["negative_electrode"]["binder_fraction"])
        self.geo_neg_particle_mean_diameter.set_value(cfg["negative_electrode"]["particle"]["mean_diameter"])
        self.geo_neg_particle_diameter_dispersion.set_value(
            cfg["negative_electrode"]["particle"]["diameter_dispersion"])
        self.geo_neg_particle_lognormal_std.set_value(cfg["negative_electrode"]["particle"]["lognormal_std"])
        self.geo_neg_binder_width_dispersion.set_value(cfg["negative_electrode"]["binder"]["width_dispersion"])
        self.geo_neg_binder_lognormal_std.set_value(cfg["negative_electrode"]["binder"]["lognormal_std"])

        self.ec_cl_init.set_value(cfg["electrochemistry"]["electrolyte"]["cl_init"])
        self.ec_c_rate.set_value(cfg["electrochemistry"]["cycling"]["c_rate"])

        self.ec_pos_soc0.set_value(cfg["electrochemistry"]["positive"]["soc0"])
        self.ec_pos_k0.set_value(cfg["electrochemistry"]["positive"]["k0"])
        self.ec_pos_r_film.set_value(cfg["electrochemistry"]["positive"]["r_film"])
        self.ec_pos_c_dl.set_value(cfg["electrochemistry"]["positive"]["c_dl"])

        self.ec_neg_soc0.set_value(cfg["electrochemistry"]["negative"]["soc0"])
        self.ec_neg_k0.set_value(cfg["electrochemistry"]["negative"]["k0"])
        self.ec_neg_r_film.set_value(cfg["electrochemistry"]["negative"]["r_film"])
        self.ec_neg_c_dl.set_value(cfg["electrochemistry"]["negative"]["c_dl"])

        advanced = cfg.get("advanced_settings", {})
        mesh_size = advanced.get("mesh_size", "normal")
        self._set_combo_to_data(self.mesh_size_combo, mesh_size)
        self.transient_max_iter_editor.setText(str(advanced.get("transient_max_iter", 100)))
        self.stationary_max_iter_editor.setText(str(advanced.get("stationary_max_iter", 100)))
        self.cutoff_voltage_editor.setText(str(advanced.get("cutoff_voltage", 3.3)))
        self.time_step_editor.setText(str(advanced.get("time_step", 2.0)))

    def sync_widgets_to_config(self):
        if self.cfg_data is None:
            raise ValueError("请先加载 YAML 配置文件。")

        cfg = self.cfg_data

        cfg["battery"]["width_h"] = self.geo_width_h.value()
        cfg["battery"]["sep_length"] = self.geo_sep_length.value()
        cfg["battery"]["pos_length"] = self.geo_pos_length.value()
        cfg["battery"]["neg_length"] = self.geo_neg_length.value()

        cfg["positive_electrode"]["active_fraction"] = self.geo_pos_active_fraction.value()
        cfg["positive_electrode"]["binder_fraction"] = self.geo_pos_binder_fraction.value()
        cfg["positive_electrode"]["particle"]["mean_diameter"] = self.geo_pos_particle_mean_diameter.value()
        cfg["positive_electrode"]["particle"]["diameter_dispersion"] = self.geo_pos_particle_diameter_dispersion.value()
        cfg["positive_electrode"]["particle"]["lognormal_std"] = self.geo_pos_particle_lognormal_std.value()
        cfg["positive_electrode"]["binder"]["width_dispersion"] = self.geo_pos_binder_width_dispersion.value()
        cfg["positive_electrode"]["binder"]["lognormal_std"] = self.geo_pos_binder_lognormal_std.value()

        cfg["negative_electrode"]["active_fraction"] = self.geo_neg_active_fraction.value()
        cfg["negative_electrode"]["binder_fraction"] = self.geo_neg_binder_fraction.value()
        cfg["negative_electrode"]["particle"]["mean_diameter"] = self.geo_neg_particle_mean_diameter.value()
        cfg["negative_electrode"]["particle"]["diameter_dispersion"] = self.geo_neg_particle_diameter_dispersion.value()
        cfg["negative_electrode"]["particle"]["lognormal_std"] = self.geo_neg_particle_lognormal_std.value()
        cfg["negative_electrode"]["binder"]["width_dispersion"] = self.geo_neg_binder_width_dispersion.value()
        cfg["negative_electrode"]["binder"]["lognormal_std"] = self.geo_neg_binder_lognormal_std.value()

        cfg["electrochemistry"]["electrolyte"]["cl_init"] = self.ec_cl_init.value()
        cfg["electrochemistry"]["cycling"]["c_rate"] = self.ec_c_rate.value()

        cfg["electrochemistry"]["positive"]["soc0"] = self.ec_pos_soc0.value()
        cfg["electrochemistry"]["positive"]["k0"] = self.ec_pos_k0.value()
        cfg["electrochemistry"]["positive"]["r_film"] = self.ec_pos_r_film.value()
        cfg["electrochemistry"]["positive"]["c_dl"] = self.ec_pos_c_dl.value()

        cfg["electrochemistry"]["negative"]["soc0"] = self.ec_neg_soc0.value()
        cfg["electrochemistry"]["negative"]["k0"] = self.ec_neg_k0.value()
        cfg["electrochemistry"]["negative"]["r_film"] = self.ec_neg_r_film.value()
        cfg["electrochemistry"]["negative"]["c_dl"] = self.ec_neg_c_dl.value()

        mesh_key = self.mesh_size_combo.currentData() or "normal"
        mesh_hauto = MESH_SIZE_BY_KEY.get(mesh_key, (5, "常规", "Normal"))[0]
        cfg["advanced_settings"] = {
            "mesh_size": mesh_key,
            "mesh_hauto": mesh_hauto,
            "transient_max_iter": int(self.transient_max_iter_editor.text()),
            "stationary_max_iter": int(self.stationary_max_iter_editor.text()),
            "cutoff_voltage": float(self.cutoff_voltage_editor.text()),
            "time_step": float(self.time_step_editor.text()),
        }

    def write_config_to_path(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.cfg_data,
                f,
                allow_unicode=True,
                sort_keys=False,
            )

    def validate_parameters(self) -> bool:
        errors = []

        def read_value(label: str, widget):
            try:
                return widget.value()
            except Exception:
                errors.append(f"{label} 不是合法数值。")
                return None

        def require_gt(label: str, value, threshold: float):
            if value is not None and not value > threshold:
                errors.append(f"{label} 必须大于 {threshold}。")

        def require_ge(label: str, value, threshold: float):
            if value is not None and not value >= threshold:
                errors.append(f"{label} 必须大于等于 {threshold}。")

        def require_between(label: str, value, low: float, high: float):
            if value is not None and not (low <= value <= high):
                errors.append(f"{label} 必须在 {low} 到 {high} 之间。")

        def require_lt(label: str, value, high: float):
            if value is not None and not value < high:
                errors.append(f"{label} 必须小于 {high}。")

                                   
                   
                                   
        width_h = read_value("电池宽度[m]", self.geo_width_h)
        sep_length = read_value("隔膜长度[m]", self.geo_sep_length)
        pos_length = read_value("正极长度[m]", self.geo_pos_length)
        neg_length = read_value("负极长度[m]", self.geo_neg_length)

        require_gt("电池宽度[m]", width_h, 0)
        require_gt("隔膜长度[m]", sep_length, 0)
        require_gt("正极长度[m]", pos_length, 0)
        require_gt("负极长度[m]", neg_length, 0)

                                   
                   
                                   
        pos_active = read_value("正极活性材料体积分数", self.geo_pos_active_fraction)
        pos_binder = read_value("正极粘结剂体积分数", self.geo_pos_binder_fraction)
        pos_particle_d = read_value("正极颗粒平均直径 [m]", self.geo_pos_particle_mean_diameter)
        pos_particle_disp = read_value("正极颗粒直径离散程度", self.geo_pos_particle_diameter_dispersion)
        pos_particle_lognormal = read_value("正极颗粒对数正态标准差", self.geo_pos_particle_lognormal_std)
        pos_binder_disp = read_value("正极粘结剂宽度离散程度", self.geo_pos_binder_width_dispersion)
        pos_binder_lognormal = read_value("正极粘结剂对数正态标准差", self.geo_pos_binder_lognormal_std)

        require_between("正极活性材料体积分数", pos_active, 0, 1)
        require_between("正极粘结剂体积分数", pos_binder, 0, 1)
        require_gt("正极颗粒平均直径 [m]", pos_particle_d, 0)

        require_ge("正极颗粒直径离散程度", pos_particle_disp, 0)
        require_lt("正极颗粒直径离散程度", pos_particle_disp, 1)

        require_ge("正极颗粒对数正态标准差", pos_particle_lognormal, 0)

        require_ge("正极粘结剂宽度离散程度", pos_binder_disp, 0)
        require_lt("正极粘结剂宽度离散程度", pos_binder_disp, 1)

        require_ge("正极粘结剂对数正态标准差", pos_binder_lognormal, 0)

        if pos_active is not None and pos_binder is not None:
            if pos_active + pos_binder > 1:
                errors.append("正极活性材料体积分数 + 正极粘结剂体积分数 不能大于 1。")

                                   
                   
                                   
        neg_active = read_value("负极活性材料体积分数", self.geo_neg_active_fraction)
        neg_binder = read_value("负极粘结剂体积分数", self.geo_neg_binder_fraction)
        neg_particle_d = read_value("负极颗粒平均直径 [m]", self.geo_neg_particle_mean_diameter)
        neg_particle_disp = read_value("负极颗粒直径离散程度", self.geo_neg_particle_diameter_dispersion)
        neg_particle_lognormal = read_value("负极颗粒对数正态标准差", self.geo_neg_particle_lognormal_std)
        neg_binder_disp = read_value("负极粘结剂宽度离散程度", self.geo_neg_binder_width_dispersion)
        neg_binder_lognormal = read_value("负极粘结剂对数正态标准差", self.geo_neg_binder_lognormal_std)

        require_between("负极活性材料体积分数", neg_active, 0, 1)
        require_between("负极粘结剂体积分数", neg_binder, 0, 1)
        require_gt("负极颗粒平均直径 [m]", neg_particle_d, 0)

        require_ge("负极颗粒直径离散程度", neg_particle_disp, 0)
        require_lt("负极颗粒直径离散程度", neg_particle_disp, 1)

        require_ge("负极颗粒对数正态标准差", neg_particle_lognormal, 0)

        require_ge("负极粘结剂宽度离散程度", neg_binder_disp, 0)
        require_lt("负极粘结剂宽度离散程度", neg_binder_disp, 1)

        require_ge("负极粘结剂对数正态标准差", neg_binder_lognormal, 0)

        if neg_active is not None and neg_binder is not None:
            if neg_active + neg_binder > 1:
                errors.append("负极活性材料体积分数 + 负极粘结剂体积分数 不能大于 1。")

                                   
                  
                                   
        cl_init = read_value("电解液初始盐浓度", self.ec_cl_init)
        c_rate = read_value("充放电循环倍率", self.ec_c_rate)

        require_gt("电解液初始盐浓度", cl_init, 0)
        require_gt("充放电循环倍率", c_rate, 0)

                                   
                  
                                   
        pos_soc0 = read_value("正极初始 SOC", self.ec_pos_soc0)
        pos_k0 = read_value("正极反应速率常数", self.ec_pos_k0)
        pos_r_film = read_value("正极 SEI/界面膜电阻", self.ec_pos_r_film)
        pos_c_dl = read_value("正极双电层电容", self.ec_pos_c_dl)

        require_between("正极初始 SOC", pos_soc0, 0, 1)
        require_gt("正极反应速率常数", pos_k0, 0)
        require_ge("正极 SEI/界面膜电阻", pos_r_film, 0)
        require_ge("正极双电层电容", pos_c_dl, 0)

                                   
                  
                                   
        neg_soc0 = read_value("负极初始 SOC", self.ec_neg_soc0)
        neg_k0 = read_value("负极反应速率常数", self.ec_neg_k0)
        neg_r_film = read_value("负极 SEI/界面膜电阻", self.ec_neg_r_film)
        neg_c_dl = read_value("负极双电层电容", self.ec_neg_c_dl)

        require_between("负极初始 SOC", neg_soc0, 0, 1)
        require_gt("负极反应速率常数", neg_k0, 0)
        require_ge("负极 SEI/界面膜电阻", neg_r_film, 0)
        require_ge("负极双电层电容", neg_c_dl, 0)

                                   
              
                                   
        def read_int_text(label: str, editor):
            try:
                return int(editor.text())
            except Exception:
                errors.append(f"{label} 不是合法整数。")
                return None

        def read_float_text(label: str, editor):
            try:
                return float(editor.text())
            except Exception:
                errors.append(f"{label} 不是合法数值。")
                return None

        transient_max_iter = read_int_text("瞬态求解最大迭代次数", self.transient_max_iter_editor)
        stationary_max_iter = read_int_text("稳态求解最大迭代次数", self.stationary_max_iter_editor)
        cutoff_voltage = read_float_text("截至电压", self.cutoff_voltage_editor)
        time_step = read_float_text("步长", self.time_step_editor)

        require_gt("瞬态求解最大迭代次数", transient_max_iter, 0)
        require_gt("稳态求解最大迭代次数", stationary_max_iter, 0)
        require_gt("截至电压", cutoff_voltage, 0)
        require_gt("步长", time_step, 0)

        if errors:
            message = "\n".join(errors[:20])

            if len(errors) > 20:
                message += f"\n……还有 {len(errors) - 20} 个错误未显示。"

            self.log("参数校验失败。")
            self.show_warning("参数校验失败", message)
            return False

        self.log("参数校验通过。")
        return True

    def save_config(self) -> bool:
        if self.config_path is None:
            self.show_warning("缺少配置文件", "请先选择 YAML 配置文件。")
            return False

        if self.cfg_data is None:
            self.show_warning("缺少配置数据", "请先加载 YAML 配置文件。")
            return False

        try:
            if not self.validate_parameters():
                return False

            self.sync_widgets_to_config()
            self.write_config_to_path(self.config_path)
            self.update_comsol_status_label()

            self.log(f"参数已写回 YAML：{self.config_path}")
            return True

        except Exception as e:
            self.show_critical("保存失败", str(e))
            return False

    def save_config_as(self) -> bool:
        if self.cfg_data is None:
            self.show_warning("缺少配置数据", "请先加载 YAML 配置文件。")
            return False

        default_config_dir = self.get_default_config_dir()
        default_config_dir.mkdir(parents=True, exist_ok=True)

        default_file_name = "case_new.yaml"

        if self.config_path is not None:
            default_file_name = f"{self.config_path.stem}_copy.yaml"

        default_path = default_config_dir / default_file_name

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr_text("另存为 YAML 配置"),
            str(default_path),
            "YAML Files (*.yaml *.yml)"
        )

        if not path:
            return False

        new_path = Path(path)

        if new_path.suffix.lower() not in [".yaml", ".yml"]:
            new_path = new_path.with_suffix(".yaml")

        try:
            if not self.validate_parameters():
                return False

            self.sync_widgets_to_config()
            self.write_config_to_path(new_path)

            self.config_path = new_path
            self.update_config_label()
            self.apply_default_output_path(silent=True)

            self.log(f"配置已另存为：{self.config_path}")
            self.show_info("另存成功", f"配置已另存为：\n{self.config_path}")
            return True

        except Exception as e:
            self.show_critical("另存失败", str(e))
            return False

    def select_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr_text("选择 Java 保存路径"),
            "PPE_model.java",
            "Java Files (*.java)"
        )

        if path:
            self.output_java_path = Path(path)
            self.update_output_label()
            self.log(f"已选择 Java 输出路径：{self.output_java_path}")

    def create_run_dir(self) -> Path:
        project_dir = self.get_project_dir_from_config()
        runs_root = project_dir / "output" / "runs"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_run_dir = runs_root / f"run_{timestamp}"

        run_dir = base_run_dir
        index = 2
        while run_dir.exists():
            run_dir = Path(f"{base_run_dir}_{index}")
            index += 1

        for sub_dir in ["json", "preview", "java", "logs", "mph", "results"]:
            (run_dir / sub_dir).mkdir(parents=True, exist_ok=True)

        self.latest_run_dir = run_dir
        return run_dir

    def build_run_java_path(self, run_dir: Path) -> Path:
        if self.output_java_path is not None:
            java_stem = safe_java_file_stem(Path(self.output_java_path).stem)
        else:
            java_cfg = (self.cfg_data or {}).get("comsol", {}).get("java", {})
            java_stem = safe_java_file_stem(
                java_cfg.get("class_name")
                or (self.cfg_data or {}).get("project", {}).get("case_name")
                or "PPE_model"
            )

        return Path(run_dir) / "java" / f"{java_stem}.java"

    def get_default_results_dir(self) -> Path:
        if self.latest_run_dir is not None:
            return Path(self.latest_run_dir) / "results"
        return self.get_project_dir_from_config() / "output" / "runs"

    def get_legacy_result_csv_path(self) -> Path:
                                                 
        return self.get_project_dir_from_config() / "output" / "results" / "discharge_voltage.csv"

    def remember_run_dir_from_result(self, result: dict):
        run_dir = result.get("run_dir") if isinstance(result, dict) else None
        if run_dir:
            run_dir = Path(run_dir)
            if self.latest_run_dir != run_dir:
                self.log(f"本次运行目录：{run_dir}")
            self.latest_run_dir = run_dir

    def run_preview(self):
        if self.config_path is None:
            self.show_warning("缺少配置文件", "请先选择 YAML 配置文件。")
            return

        if self.cfg_data is None:
            self.show_warning("缺少配置数据", "请先加载 YAML 配置文件。")
            return

        if not self.save_config():
            return

        run_dir = self.create_run_dir()
        json_path = run_dir / "json" / "case_preview.json"
        preview_path = run_dir / "preview" / "case_preview.png"

        self.is_comsol_running = False
        self.set_busy_state(True)

        self.log("开始刷新预览图...")
        self.log(f"本次运行目录：{run_dir}")

        self.worker = PreviewWorker(
            config_path=self.config_path,
            run_dir=run_dir,
            json_path=json_path,
            preview_path=preview_path,
        )

        self.worker.success.connect(self.on_preview_success)
        self.worker.failed.connect(self.on_preview_failed)
        self.worker.start()

    def get_current_c_rate_label(self) -> str:
        try:
            c_rate = self.ec_c_rate.value()
            return f"{c_rate:g}C"
        except Exception:
            return "C-rate"

    def get_default_result_csv_path(self) -> Path:
        return self.get_default_results_dir() / "discharge_voltage.csv"

    def get_default_solver_log_path(self) -> Path:
        if self.latest_run_dir is not None:
            return Path(self.latest_run_dir) / "logs" / "comsol_batch.log"
        return self.get_project_dir_from_config() / "output" / "runs" / "comsol_batch.log"

    def refresh_solver_log(self):
        if not hasattr(self, "solver_log_box"):
            return

        if not self.solver_log_active or self.active_solver_log_path is None:
            if self.solver_log_last_text != "":
                self.solver_log_box.clear()
                self.solver_log_last_text = ""
            return

        log_path = Path(self.active_solver_log_path)

        if not log_path.exists():
            if self.solver_log_last_text != "":
                self.solver_log_box.clear()
                self.solver_log_last_text = ""
            return

        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            text = f"读取 COMSOL 日志失败：{e}"

        if text == self.solver_log_last_text:
            return

        self.solver_log_last_text = text
        self.solver_log_box.setPlainText(text)
        self.solver_log_box.moveCursor(QTextCursor.MoveOperation.End)
        self.solver_log_box.ensureCursorVisible()

    def plot_result_csv(self):
        default_csv = self.get_default_result_csv_path()
        default_dir = default_csv.parent

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr_text("选择一个或多个结果 CSV 文件"),
            str(default_dir),
            "CSV Files (*.csv);;All Files (*)"
        )

        if paths:
            csv_paths = [Path(path) for path in paths]
        elif default_csv.exists():
            csv_paths = [default_csv]
        elif self.get_legacy_result_csv_path().exists():
            csv_paths = [self.get_legacy_result_csv_path()]
        else:
            return

        try:
            self.result_manager.add_csv_files(
                csv_paths,
                default_single_label=self.get_current_c_rate_label(),
                animate=False,
            )

            if len(csv_paths) == 1:
                self.log(f"结果曲线已绘制：{csv_paths[0]}")
            else:
                self.log(f"已绘制 {len(csv_paths)} 个 CSV 文件。")
                for csv_path in csv_paths:
                    self.log(f"CSV 文件：{csv_path}")

        except Exception as e:
            self.log(f"绘图失败：{e}")
            self.show_critical("绘图失败", str(e))

    def auto_plot_discharge_curve(self, csv_path: Path):
        csv_path = Path(csv_path)

        if not csv_path.exists():
            self.log(f"自动绘图失败，CSV 文件不存在：{csv_path}")
            return False

        try:
            curve_label = self.get_current_c_rate_label()
            self.result_manager.add_csv_files(
                [csv_path],
                default_single_label=curve_label,
                animate=True,
                label_overrides={csv_path: curve_label},
            )
            self.log(f"放电结果曲线已自动生成：{csv_path}")
            self.log("曲线动画已启动，将按时间节点从左到右显示。")
            return True
        except Exception as e:
            self.log(f"自动绘制放电曲线失败：{e}")
            self.show_critical("绘图失败", str(e))
            return False

    def get_comsol_runner_paths(self) -> tuple[Path, Path]:
        if self.cfg_data is None:
            raise ValueError("请先加载 YAML 配置文件。")

        runner_cfg = self.cfg_data.get("comsol", {}).get("runner", {})

        comsolcompile_path_raw = runner_cfg.get("comsolcompile_path")
        comsolbatch_path_raw = runner_cfg.get("comsolbatch_path")

        if not comsolcompile_path_raw:
            raise ValueError("YAML 中缺少 comsol.runner.comsolcompile_path。")

        if not comsolbatch_path_raw:
            raise ValueError("YAML 中缺少 comsol.runner.comsolbatch_path。")

        comsolcompile_path = Path(str(comsolcompile_path_raw).strip().strip('"'))
        comsolbatch_path = Path(str(comsolbatch_path_raw).strip().strip('"'))

        errors = self.get_comsol_path_errors(comsolcompile_path, comsolbatch_path)
        if errors:
            raise ValueError("\n".join(errors))

        return comsolcompile_path, comsolbatch_path

    def get_comsol_path_errors(self, comsolcompile_path: Path, comsolbatch_path: Path) -> list[str]:
        errors = []

        def check_one(label: str, path: Path, expected_name: str):
            path_text = str(path)
            if not path_text or path_text == ".":
                errors.append(f"请选择 {expected_name}。")
                return
            if not path.exists():
                errors.append(f"COMSOL 路径不存在：{path_text}")
                return
            if not path.is_file():
                errors.append(f"COMSOL 路径不是文件：{path_text}")
                return
            if path.name.lower() != expected_name.lower():
                errors.append(f"{label} 应指向 {expected_name}：{path_text}")

        check_one("comsolcompile_path", comsolcompile_path, "comsolcompile.exe")
        check_one("comsolbatch_path", comsolbatch_path, "comsolbatch.exe")
        return errors

    def update_comsol_status_label(self):
        if not hasattr(self, "comsol_status_label"):
            return

        if self.cfg_data is None:
            self.comsol_status_label.setText(self.tr_text("COMSOL：未检查"))
            self.comsol_status_label.setToolTip("")
            return

        try:
            comsolcompile_path, comsolbatch_path = self.get_comsol_runner_paths()
        except Exception as e:
            self.comsol_status_label.setText(self.tr_text("COMSOL：未配置"))
            self.comsol_status_label.setToolTip(self.tr_message(str(e)))
            return

        self.comsol_status_label.setText(self.tr_text("COMSOL：已配置"))
        self.comsol_status_label.setToolTip(
            f"comsolcompile: {comsolcompile_path}\ncomsolbatch: {comsolbatch_path}"
        )

    def check_comsol_paths_action(self):
        if self.cfg_data is None:
            self.show_warning("缺少配置数据", "请先加载 YAML 配置文件。")
            return False

        try:
            self.get_comsol_runner_paths()
        except Exception as e:
            self.update_comsol_status_label()
            self.log("COMSOL 路径检查失败。")
            self.show_warning("COMSOL 路径配置错误", str(e))
            return False

        self.update_comsol_status_label()
        self.log("COMSOL 路径检查通过。")
        self.show_info("路径检查通过", "COMSOL 路径检查通过。")
        return True

    def configure_comsol_paths(self):
        if self.config_path is None:
            self.show_warning("缺少配置文件", "请先选择 YAML 配置文件。")
            return False

        if self.cfg_data is None:
            self.show_warning("缺少配置数据", "请先加载 YAML 配置文件。")
            return False

        runner_cfg = self.cfg_data.get("comsol", {}).get("runner", {})
        current_compile = runner_cfg.get("comsolcompile_path", "")
        current_batch = runner_cfg.get("comsolbatch_path", "")

        dialog = ComsolPathDialog(
            self,
            comsolcompile_path=str(current_compile or ""),
            comsolbatch_path=str(current_batch or ""),
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        comsolcompile_path, comsolbatch_path = dialog.get_paths()

        comsol_cfg = self.cfg_data.setdefault("comsol", {})
        runner_cfg = comsol_cfg.setdefault("runner", {})
        runner_cfg["comsolcompile_path"] = str(comsolcompile_path).replace("\\", "/")
        runner_cfg["comsolbatch_path"] = str(comsolbatch_path).replace("\\", "/")

        try:
            self.write_config_to_path(self.config_path)
        except Exception as e:
            self.show_critical("保存失败", str(e))
            return False

        self.update_comsol_status_label()
        self.log(f"COMSOL 路径已配置并写回 YAML：{self.config_path}")
        self.log(f"comsolcompile：{runner_cfg['comsolcompile_path']}")
        self.log(f"comsolbatch：{runner_cfg['comsolbatch_path']}")
        self.show_info("COMSOL 路径已保存", "COMSOL 路径已写入 YAML。")
        return True

    def build_default_comsol_log_path(self) -> Path:
        run_dir = self.latest_run_dir or self.create_run_dir()
        return Path(run_dir) / "logs" / "comsol_batch.log"

    def build_default_mph_path(self) -> Path:
        run_dir = self.latest_run_dir or self.create_run_dir()
        case_name = self.cfg_data.get("project", {}).get("case_name", "PPE_model")
        return Path(run_dir) / "mph" / f"{safe_java_file_stem(case_name)}.mph"

    def build_default_model_only_mph_path(self) -> Path:
        run_dir = self.latest_run_dir or self.create_run_dir()
        case_name = self.cfg_data.get("project", {}).get("case_name", "PPE_model")
        return Path(run_dir) / "mph" / f"{safe_java_file_stem(case_name)}_model_only.mph"

    def build_default_model_only_log_path(self) -> Path:
        run_dir = self.latest_run_dir or self.create_run_dir()
        return Path(run_dir) / "logs" / "build_model_only.log"

    def set_busy_state(self, busy: bool):
        self.preview_btn.setEnabled(not busy)
        self.run_btn.setEnabled(not busy)
        self.run_comsol_btn.setEnabled(not busy)
        self.plot_csv_btn.setEnabled(not busy)

        for action_name in [
            "action_refresh_preview",
            "action_export_java",
            "action_run_comsol",
            "action_configure_comsol",
            "action_check_comsol_paths",
            "action_plot_csv",
            "action_validate_params",
            "action_reload_yaml",
            "action_write_yaml",
        ]:
            self.set_action_enabled(action_name, not busy)

        stop_enabled = busy and self.is_comsol_running
        if hasattr(self, "stop_comsol_btn"):
            self.stop_comsol_btn.setEnabled(stop_enabled)
        self.set_action_enabled("action_stop_comsol", stop_enabled)

        if busy:
            if self.is_comsol_running:
                self.update_status("COMSOL 运行中", "running")
            else:
                self.update_status("任务处理中", "running")
        else:
            self.update_status("就绪", "idle")

    def prepare_solver_log_file(self, log_path: Path):
        try:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
        except Exception as e:
            self.log(f"清空旧 COMSOL 日志失败，将继续尝试显示当前日志：{e}")

    def run_comsol(self):
        if self.config_path is None:
            self.show_warning("缺少配置文件", "请先选择 YAML 配置文件。")
            return

        if self.output_java_path is None:
            self.show_warning("缺少输出路径", "请先选择 Java 保存路径。")
            return

        if not self.save_config():
            return

        try:
            comsolcompile_path, comsolbatch_path = self.get_comsol_runner_paths()
        except Exception as e:
            self.show_warning("COMSOL 路径配置错误", str(e))
            return

        run_dir = self.create_run_dir()
        output_java_path = self.build_run_java_path(run_dir)
        log_path = run_dir / "logs" / "comsol_batch.log"
        case_name = self.cfg_data.get("project", {}).get("case_name", "PPE_model")
        output_mph_path = run_dir / "mph" / f"{safe_java_file_stem(case_name)}.mph"

        self.is_comsol_running = True
        self.set_busy_state(True)

        self.log_tabs.setCurrentIndex(0)
        self.solver_log_box.clear()
        self.solver_log_last_text = ""
        self.active_solver_log_path = log_path
        self.solver_log_active = True
        self.prepare_solver_log_file(log_path)
        if not self.solver_log_timer.isActive():
            self.solver_log_timer.start()

        self.log("开始生成 Java、编译 class 并运行 COMSOL batch...")
        self.log(f"本次运行目录：{run_dir}")
        self.log(f"Java 文件：{output_java_path}")
        self.log(f"comsolcompile：{comsolcompile_path}")
        self.log(f"comsolbatch：{comsolbatch_path}")
        self.log(f"batch 日志：{log_path}")
        self.log(f"MPH 输出：{output_mph_path}")

        self.worker = RunComsolWorker(
            config_path=self.config_path,
            output_java_path=output_java_path,
            comsolcompile_path=comsolcompile_path,
            comsolbatch_path=comsolbatch_path,
            log_path=log_path,
            output_mph_path=output_mph_path,
            run_dir=run_dir,
        )

        self.worker.success.connect(self.on_comsol_success)
        self.worker.failed.connect(self.on_comsol_failed)
        self.worker.cancelled.connect(self.on_comsol_cancelled)
        self.worker.start()

    def stop_comsol(self):
        if not isinstance(self.worker, RunComsolWorker):
            self.log("当前没有正在运行的 COMSOL 任务。")
            return

        self.log("用户请求停止 COMSOL 任务，正在终止 COMSOL 进程...")
        self.stop_comsol_btn.setEnabled(False)
        self.worker.request_stop()
        self.refresh_solver_log()

    def on_comsol_cancelled(self, message: str):
        self.is_comsol_running = False
        self.set_busy_state(False)
        self.refresh_solver_log()
        self.solver_log_timer.stop()
        self.log_tabs.setCurrentIndex(0)

        if not message:
            message = "COMSOL 计算已被用户停止。"

        self.update_status("已停止", "cancelled")
        self.log(message)
        self.show_info("已停止", message)

    def on_comsol_success(self, result: dict):
        self.is_comsol_running = False
        self.set_busy_state(False)
        self.refresh_solver_log()
        self.solver_log_timer.stop()
        self.log_tabs.setCurrentIndex(0)
        self.remember_run_dir_from_result(result)

        self.update_status("COMSOL 完成", "success")
        self.log("COMSOL batch 运行完成。")
        self.log(f"Java 文件：{result.get('java_path')}")
        self.log(f"class 文件：{result.get('class_path')}")
        self.log(f"日志文件：{result.get('log_path')}")

        if result.get("output_mph_path"):
            self.log(f"MPH 文件：{result.get('output_mph_path')}")

        csv_path = self.get_default_result_csv_path()
        csv_exists = csv_path.exists()

        if csv_exists:
            self.log(f"CSV 文件：{csv_path}")
        else:
            self.log(f"未找到默认 CSV 文件：{csv_path}")

        if result.get("json_path"):
            self.log(f"JSON 文件：{result.get('json_path')}")

        if result.get("preview_path"):
            self.log(f"预览图：{result.get('preview_path')}")

        self.update_preview_from_result(result)

        if csv_exists:
            self.show_info("完成", "COMSOL 无界面运行完成。\n\n点击确定后将自动生成放电结果曲线。")
            self.auto_plot_discharge_curve(csv_path)
        else:
            self.show_info("完成", "COMSOL 无界面运行完成。\n\n但未找到默认放电结果 CSV，无法自动生成曲线。")

    def on_comsol_failed(self, error_message: str):
        self.is_comsol_running = False
        self.set_busy_state(False)
        self.refresh_solver_log()
        self.solver_log_timer.stop()
        self.log_tabs.setCurrentIndex(0)

        self.update_status("COMSOL 失败", "error")
        self.log("COMSOL batch 运行失败。")
        self.log(error_message)

        self.show_critical("COMSOL 运行失败", error_message)

    def run_export(self):
                                                   
        if self.config_path is None:
            self.show_warning("缺少配置文件", "请先选择 YAML 配置文件。")
            return

        if self.output_java_path is None:
            self.show_warning("缺少输出路径", "请先选择 Java 保存路径。")
            return

        if not self.save_config():
            return

        try:
            comsolcompile_path, comsolbatch_path = self.get_comsol_runner_paths()
        except Exception as e:
            self.show_warning("COMSOL 路径配置错误", str(e))
            return

        run_dir = self.create_run_dir()
        output_java_path = self.build_run_java_path(run_dir)
        case_name = self.cfg_data.get("project", {}).get("case_name", "PPE_model")
        log_path = run_dir / "logs" / "build_model_only.log"
        output_mph_path = run_dir / "mph" / f"{safe_java_file_stem(case_name)}_model_only.mph"

        self.is_comsol_running = True
        self.set_busy_state(True)
        self.update_status("模型文件生成中", "running")

        self.log_tabs.setCurrentIndex(0)
        self.solver_log_box.clear()
        self.solver_log_last_text = ""
        self.active_solver_log_path = log_path
        self.solver_log_active = True
        self.prepare_solver_log_file(log_path)
        if not self.solver_log_timer.isActive():
            self.solver_log_timer.start()

        self.log("开始仅生成模型文件：生成 Java、编译 class，并保存未求解的 MPH...")
        self.log("注意：本流程不会执行 study.run()，不会导出 CSV 结果。")
        self.log(f"本次运行目录：{run_dir}")
        self.log(f"Java 文件：{output_java_path}")
        self.log(f"comsolcompile：{comsolcompile_path}")
        self.log(f"comsolbatch：{comsolbatch_path}")
        self.log(f"batch 日志：{log_path}")
        self.log(f"未求解 MPH 输出：{output_mph_path}")

        self.worker = RunComsolWorker(
            config_path=self.config_path,
            output_java_path=output_java_path,
            comsolcompile_path=comsolcompile_path,
            comsolbatch_path=comsolbatch_path,
            log_path=log_path,
            output_mph_path=output_mph_path,
            run_study=False,
            export_results=False,
            run_dir=run_dir,
        )

        self.worker.success.connect(self.on_model_file_success)
        self.worker.failed.connect(self.on_model_file_failed)
        self.worker.cancelled.connect(self.on_model_file_cancelled)
        self.worker.start()

    def on_model_file_cancelled(self, message: str):
        self.is_comsol_running = False
        self.set_busy_state(False)
        self.refresh_solver_log()
        self.solver_log_timer.stop()
        self.log_tabs.setCurrentIndex(0)

        if not message:
            message = "模型文件生成已被用户停止。"

        self.update_status("已停止", "cancelled")
        self.log(message)
        self.show_info("已停止", message)

    def on_model_file_success(self, result: dict):
        self.is_comsol_running = False
        self.set_busy_state(False)
        self.refresh_solver_log()
        self.solver_log_timer.stop()
        self.log_tabs.setCurrentIndex(0)
        self.remember_run_dir_from_result(result)

        self.update_status("模型文件已生成", "success")
        self.log("仅生成模型文件完成。")
        self.log(f"Java 文件：{result.get('java_path')}")
        self.log(f"class 文件：{result.get('class_path')}")
        self.log(f"日志文件：{result.get('log_path')}")

        if result.get("output_mph_path"):
            self.log(f"未求解 MPH 文件：{result.get('output_mph_path')}")

        if result.get("json_path"):
            self.log(f"JSON 文件：{result.get('json_path')}")

        if result.get("preview_path"):
            self.log(f"预览图：{result.get('preview_path')}")

        self.update_preview_from_result(result)

        self.show_info(
            "完成",
            "模型文件已生成。\n\n该 MPH 未执行求解，可用 COMSOL Desktop 打开查看模型。",
        )

    def on_model_file_failed(self, error_message: str):
        self.is_comsol_running = False
        self.set_busy_state(False)
        self.refresh_solver_log()
        self.solver_log_timer.stop()
        self.log_tabs.setCurrentIndex(0)

        self.update_status("模型文件生成失败", "error")
        self.log("仅生成模型文件失败。")
        self.log(error_message)
        self.show_critical("模型文件生成失败", error_message)

    def on_preview_success(self, result: dict):
        self.set_busy_state(False)
        self.remember_run_dir_from_result(result)

        self.update_status("预览完成", "success")
        self.log("预览图刷新成功。")

        if result.get("json_path"):
            self.log(f"JSON 文件：{result.get('json_path')}")

        if result.get("preview_path"):
            self.log(f"预览图：{result.get('preview_path')}")

        self.update_preview_from_result(result)

        self.show_info("完成", "预览图刷新成功。")

    def on_preview_failed(self, error_message: str):
        self.set_busy_state(False)

        self.update_status("预览失败", "error")
        self.log("预览图刷新失败。")
        self.log(error_message)

        self.show_critical("预览图刷新失败", error_message)

    def on_success(self, result: dict):
        self.set_busy_state(False)
        self.remember_run_dir_from_result(result)

        self.update_status("Java 已生成", "success")
        self.log("生成成功。")
        self.log(f"Java 文件：{result.get('java_path')}")

        if result.get("json_path"):
            self.log(f"JSON 文件：{result.get('json_path')}")

        if result.get("preview_path"):
            self.log(f"预览图：{result.get('preview_path')}")

        self.update_preview_from_result(result)

        self.show_info("完成", "Java 文件生成成功。")

    def on_failed(self, error_message: str):
        self.set_busy_state(False)
        self.update_status("生成失败", "error")
        self.log("生成失败。")
        self.log(error_message)
        self.show_critical("生成失败", error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
"""A compact, bilingual selector for the bundled offline examples."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


HEADERS = {
    "zh": [
        "案例序号", "正极粒径 (m)", "正极颗粒面积分数", "实际正极颗粒数量",
        "实际正极粘结剂数量", "网格等级", "随机种子", "三角形单元数",
        "瞬态自由度", "选择",
    ],
    "en": [
        "Case", "Positive particle diameter (m)", "Positive active fraction",
        "Positive particles", "Positive binders", "Mesh size", "Random seed",
        "Triangle elements", "Transient DOF", "Select",
    ],
}

MESH_LABELS = {
    "fine": ("细化", "Fine"),
    "normal": ("常规", "Normal"),
    "coarse": ("粗化", "Coarse"),
}


class OfflineCaseDialog(QDialog):
    def __init__(self, cases: list[dict], language: str = "zh", parent=None):
        super().__init__(parent)
        self.cases = cases
        self.language = "en" if language == "en" else "zh"
        self.selected_case = None
        self.setWindowTitle("Offline Case Gallery" if self.language == "en" else "离线案例展示")
        self.resize(1250, 640)
        self.setMinimumSize(880, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel(
            "Select one case, then click Use to load its configuration, electrode structure, and result curve."
            if self.language == "en" else
            "选择一组案例，点击“使用”后加载配置、电极结构和结果曲线。"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(len(cases), len(HEADERS[self.language]), self)
        self.table.setHorizontalHeaderLabels(HEADERS[self.language])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(31)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setWordWrap(False)
        self.table.cellClicked.connect(self._select_row)
        self.choice_group = QButtonGroup(self)
        self.choice_group.setExclusive(True)

        for row, case in enumerate(cases):
            mesh = MESH_LABELS.get(case["mesh_size"], (case["mesh_size"],) * 2)
            values = [
                str(case["number"]),
                f'{case["positive_mean_diameter_m"]:.7f}',
                f'{case["positive_active_fraction"]:g}',
                str(case["positive_particle_count"]),
                str(case["positive_binder_count"]),
                mesh[1 if self.language == "en" else 0],
                str(case["random_seed"]),
                f'{case["triangle_elements"]:,}',
                f'{case["transient_dof"]:,}',
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)

            radio = QRadioButton(self.table)
            radio.setAccessibleName(
                f'Case {case["number"]}' if self.language == "en" else f'案例 {case["number"]}'
            )
            radio.toggled.connect(lambda checked, index=row: self._choose(index) if checked else None)
            self.choice_group.addButton(radio, row)
            wrapper = QWidget(self.table)
            radio_layout = QHBoxLayout(wrapper)
            radio_layout.setContentsMargins(0, 0, 0, 0)
            radio_layout.addStretch()
            radio_layout.addWidget(radio)
            radio_layout.addStretch()
            self.table.setCellWidget(row, len(values), wrapper)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 76)
        self.table.setColumnWidth(9, 72)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.close_button = QPushButton("Close" if self.language == "en" else "关闭", self)
        self.close_button.clicked.connect(self.reject)
        self.use_button = QPushButton("Use" if self.language == "en" else "使用", self)
        self.use_button.setObjectName("PrimaryButton")
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self.accept)
        buttons.addWidget(self.close_button)
        buttons.addWidget(self.use_button)
        layout.addLayout(buttons)

    def _select_row(self, row: int, _column: int):
        self.choice_group.button(row).setChecked(True)

    def _choose(self, row: int):
        self.selected_case = self.cases[row]
        self.use_button.setEnabled(True)

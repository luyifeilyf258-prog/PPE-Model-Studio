from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QLineEdit, QFormLayout, QScrollArea, QWidget


class FloatLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()

        validator = QDoubleValidator(-1e100, 1e100, 99)
        validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
        self.setValidator(validator)

        self.setFixedWidth(132)
        self.setMinimumHeight(38)
        self.setMaximumHeight(38)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setPlaceholderText("0.0")

    def set_value(self, value):
        if value is None:
            self.setText("")
        else:
            self.setText(f"{float(value):.12g}")

    def value(self):
        text = self.text().strip()
        if text == "":
            return 0.0
        return float(text)


def make_float_box():
    return FloatLineEdit()


def make_form():
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
    form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(24)
    form.setVerticalSpacing(20)
    form.setContentsMargins(14, 12, 14, 20)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
    return form


def make_scroll_tab(form: QFormLayout, min_height: int = 260):
    content = QWidget()
    content.setLayout(form)
    content.setMinimumHeight(min_height + 40)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(content)

    return scroll



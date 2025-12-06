from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QFrame, QSizePolicy
)


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(24)

        hdr = QHBoxLayout()
        title = QLabel("Reports")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.report_type = QComboBox()
        self.report_type.addItems(["Sales Performance", "Category Distribution", "User Accounts"])
        self.report_type.setFixedWidth(220)
        hdr.addWidget(self.report_type)

        btn_generate = QPushButton("Generate")
        btn_generate.setObjectName("primaryBtn")
        btn_generate.setFixedHeight(36)
        hdr.addWidget(btn_generate)

        root.addLayout(hdr)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        def make_kpi(title_text, value_text):
            card = QFrame()
            card.setObjectName("Card")
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            inner = QVBoxLayout(card)
            inner.setContentsMargins(14, 12, 14, 12)
            label = QLabel(title_text)
            label.setObjectName("CardTitle")
            value = QLabel(value_text)
            value.setObjectName("CardValue")
            inner.addWidget(label)
            inner.addWidget(value)
            return card

        kpi_row.addWidget(make_kpi("Revenue (30d)", "₱125,400"))
        kpi_row.addWidget(make_kpi("Avg Order", "₱420"))
        kpi_row.addWidget(make_kpi("Top Category", "Beverages"))
        root.addLayout(kpi_row)

        chart_area = QFrame()
        chart_area.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_area)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.addWidget(QLabel("Chart area (placeholder)"))
        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setPlainText("Generated charts and report tables will appear here.")
        notes.setFixedHeight(220)
        chart_layout.addWidget(notes)
        root.addWidget(chart_area, 1)

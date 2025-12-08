from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class ModernCard(QFrame):
    def __init__(self, title, value="", parent=None):
        super().__init__(parent)

        self.setObjectName("modernCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("modernCardTitle")

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("modernCardValue")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.title_lbl)
        layout.addSpacing(4)
        layout.addWidget(self.value_lbl)
        layout.addStretch()

        # Local fallback styling (in case global theme isn't applied yet)
        self.setStyleSheet("""
            QFrame#modernCard {
                background: #FFFFFF;
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.08);
            }
            QLabel#modernCardTitle {
                color: #64748B;
                font-weight: 600;
                background: transparent;
            }
            QLabel#modernCardValue {
                color: #0F172A;
                font-weight: 800;
                font-size: 16px;
                background: transparent;
            }
        """)

    def set_value(self, value: str):
        self.value_lbl.setText(value or "")

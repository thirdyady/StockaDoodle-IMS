# desktop_app/ui/components/modern_card.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class ModernCard(QFrame):
    def __init__(self, title, value="", parent=None):
        super().__init__(parent)
        self.setObjectName("modernCard")
        self.setStyleSheet("""
            QFrame#modernCard { background: white; border-radius:12px; padding:12px; }
            QLabel.cardTitle { color:#64748b; font-weight:600; }
            QLabel.cardValue { color:#0f172a; font-weight:800; font-size:16px; }
        """)
        l = QVBoxLayout(self)
        t = QLabel(title)
        t.setProperty("class","cardTitle")
        v = QLabel(value)
        v.setProperty("class","cardValue")
        v.setAlignment(Qt.AlignmentFlag.AlignLeft)
        l.addWidget(t)
        l.addWidget(v)
        l.addStretch()

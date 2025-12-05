# desktop_app/ui/splash_screen.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 240)
        layout = QVBoxLayout(self)
        lbl = QLabel("StockaDoodle\nLoading...")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size:20px; font-weight:700;")
        layout.addWidget(lbl)

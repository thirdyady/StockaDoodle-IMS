# desktop_app/ui/sales/sales_management.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt

class SalesManagementPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        header = QHBoxLayout()
        h = QLabel("Sales Management / POS")
        h.setObjectName("title")
        header.addWidget(h)
        header.addStretch()
        root.addLayout(header)

        pos_frame = QFrame()
        pos_frame.setObjectName("Card")
        pos_layout = QVBoxLayout(pos_frame)
        pos_layout.addWidget(QLabel("Product search"))
        search = QLineEdit()
        search.setPlaceholderText("Search by name or barcode")
        pos_layout.addWidget(search)
        pos_layout.addWidget(QLabel("Cart"))
        cart = QTextEdit()
        cart.setReadOnly(True)
        cart.setPlainText("Cart is empty (demo)")
        pos_layout.addWidget(cart)
        checkout_btn = QPushButton("Checkout")
        checkout_btn.setObjectName("primaryBtn")
        pos_layout.addWidget(checkout_btn)
        root.addWidget(pos_frame)

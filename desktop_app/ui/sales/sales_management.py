# desktop_app/ui/sales/sales_management.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QFrame
)


class SalesManagementPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(24)

        header = QHBoxLayout()
        title = QLabel("Sales Management / POS")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        pos_frame = QFrame()
        pos_frame.setObjectName("Card")

        pos_layout = QVBoxLayout(pos_frame)
        pos_layout.setContentsMargins(12, 12, 12, 12)
        pos_layout.setSpacing(10)

        pos_layout.addWidget(QLabel("Product search"))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or barcode")
        pos_layout.addWidget(self.search)

        pos_layout.addWidget(QLabel("Cart"))

        self.cart = QTextEdit()
        self.cart.setReadOnly(True)
        self.cart.setPlainText("Cart is empty (demo)")
        pos_layout.addWidget(self.cart)

        self.checkout_btn = QPushButton("Checkout")
        self.checkout_btn.setObjectName("primaryBtn")
        pos_layout.addWidget(self.checkout_btn)

        root.addWidget(pos_frame)

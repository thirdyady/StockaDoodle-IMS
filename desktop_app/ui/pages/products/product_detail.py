# desktop_app/ui/pages/products/product_detail.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class ProductDetailPage(QWidget):
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.product = product or {"name": "Product X", "price": "₱0", "stock": 0}
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(24)


        header = QHBoxLayout()
        title = QLabel(f"{self.product.get('name')} — {self.product.get('price')}")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondaryBtn")
        edit_btn.setFixedHeight(34)
        header.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("secondaryBtn")
        delete_btn.setFixedHeight(34)
        header.addWidget(delete_btn)

        root.addLayout(header)

        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.addWidget(QLabel(f"Current stock: {self.product.get('stock')}"))
        cl.addWidget(QLabel("Stock batches and controls will appear here."))

        root.addWidget(card)

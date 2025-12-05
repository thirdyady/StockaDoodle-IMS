# desktop_app/ui/pages/products/product_list.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QListWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class ProductListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(24)


        header = QHBoxLayout()
        title = QLabel("Products")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("Add product")
        add_btn.setObjectName("primaryBtn")
        add_btn.setFixedHeight(36)
        header.addWidget(add_btn)

        root.addLayout(header)

        listing_card = QFrame()
        listing_card.setObjectName("Card")
        cl = QVBoxLayout(listing_card)
        cl.setContentsMargins(10, 10, 10, 10)

        list_widget = QListWidget()
        list_widget.addItem("Coca-Cola 330ml — ₱45 — Stock: 342")
        list_widget.addItem("Pepsi 330ml — ₱42 — Stock: 128")
        list_widget.addItem("Sprite 300ml — ₱40 — Stock: 75")

        cl.addWidget(list_widget)
        root.addWidget(listing_card)

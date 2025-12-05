# desktop_app/ui/pages/products/product_form.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PyQt6.QtCore import Qt

class ProductFormPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(24)


        title = QLabel("Product Form")
        title.setObjectName("title")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)

        cl.addWidget(QLabel("Name"))
        self.name = QLineEdit()
        cl.addWidget(self.name)

        cl.addWidget(QLabel("Price"))
        self.price = QLineEdit()
        cl.addWidget(self.price)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedHeight(36)
        cl.addWidget(save_btn)

        root.addWidget(card)

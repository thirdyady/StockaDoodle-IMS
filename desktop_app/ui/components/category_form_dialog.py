# desktop_app/ui/components/category_form_dialog.py

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt


class CategoryFormDialog(QDialog):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api

        self.setWindowTitle("Add Category")
        self.setMinimumWidth(420)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(14, 12, 14, 12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Snacks, Dairy, Toiletries")

        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(90)
        self.desc_input.setPlaceholderText("Optional description")

        form.addRow("Category Name:", self.name_input)
        form.addRow("Description:", self.desc_input)

        form_layout.addLayout(form)
        root.addWidget(form_card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Create")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)

        root.addLayout(btn_row)

    def _on_save(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip() or None

        if not name:
            QMessageBox.warning(self, "Validation", "Category name is required.")
            return

        try:
            self.api.create_category(name=name, description=desc)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create category:\n{e}")

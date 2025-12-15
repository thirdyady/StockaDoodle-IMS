# desktop_app/ui/pages/products/product_form.py

from __future__ import annotations

import traceback
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QSpinBox, QPushButton, QFrame,
    QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from desktop_app.api_client.stockadoodle_api import StockaDoodleAPI, StockaDoodleAPIError


class ProductFormPage(QWidget):
    """
    Product create/edit form.

    - Loads categories from API
    - Sends category_id to backend
    - Works for create and optional edit-mode
    """

    # Let parent pages refresh lists after save
    product_saved = pyqtSignal(dict)

    def __init__(
        self,
        user_data: Optional[Dict[str, Any]] = None,
        product: Optional[Dict[str, Any]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.user = user_data or {}
        self.api = StockaDoodleAPI()

        # If product is passed, treat as edit mode
        self.product = product

        self._categories: List[Dict[str, Any]] = []
        self._build_ui()
        self._load_categories()
        self._load_product_if_edit()

    # ------------------------------------------------------------
    # UI
    # ------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)

        # Header
        title = QLabel("Add Product" if not self.product else "Edit Product")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #0A0A0A;
        """)
        subtitle = QLabel("Fill in product details. Category is required.")
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: rgba(0,0,0,0.55);
        """)

        root.addWidget(title)
        root.addWidget(subtitle)

        # Card container
        card = QFrame()
        card.setObjectName("productFormCard")
        card.setStyleSheet("""
            #productFormCard {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #DDE3EA;
            }
        """)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 20, 22, 20)
        cl.setSpacing(14)

        # --------------------------
        # Name
        # --------------------------
        cl.addWidget(self._label("Product Name"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Nescafe Coffee 3-in-1")
        cl.addWidget(self.name_input)

        # --------------------------
        # Brand
        # --------------------------
        cl.addWidget(self._label("Brand (optional)"))
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("e.g., Nestlé")
        cl.addWidget(self.brand_input)

        # --------------------------
        # Category
        # --------------------------
        cl.addWidget(self._label("Category"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Loading categories...", None)
        cl.addWidget(self.category_combo)

        # --------------------------
        # Price + Min Stock row
        # --------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(6)
        left.addWidget(self._label("Price (₱)"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("e.g., 25")
        left.addWidget(self.price_input)

        right = QVBoxLayout()
        right.setSpacing(6)
        right.addWidget(self._label("Min Stock Level"))
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 999999)
        self.min_stock_spin.setValue(10)
        right.addWidget(self.min_stock_spin)

        row1.addLayout(left, 1)
        row1.addLayout(right, 1)
        cl.addLayout(row1)

        # --------------------------
        # Initial Stock + Expiration row
        # --------------------------
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        left2 = QVBoxLayout()
        left2.setSpacing(6)
        left2.addWidget(self._label("Initial Stock (optional)"))
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        self.stock_spin.setValue(0)
        left2.addWidget(self.stock_spin)

        right2 = QVBoxLayout()
        right2.setSpacing(6)
        right2.addWidget(self._label("Expiration Date (optional)"))
        self.exp_date = QDateEdit()
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setDisplayFormat("yyyy-MM-dd")
        self.exp_date.setDate(QDate.currentDate())
        right2.addWidget(self.exp_date)

        row2.addLayout(left2, 1)
        row2.addLayout(right2, 1)
        cl.addLayout(row2)

        # --------------------------
        # Details
        # --------------------------
        cl.addWidget(self._label("Details (optional)"))
        self.details_input = QTextEdit()
        self.details_input.setPlaceholderText("Short product notes or description...")
        self.details_input.setFixedHeight(90)
        cl.addWidget(self.details_input)

        # --------------------------
        # Buttons
        # --------------------------
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 0 14px;
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                background: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        self.save_btn = QPushButton("Save Product")
        self.save_btn.setFixedHeight(34)
        self.save_btn.setStyleSheet("""
            QPushButton {
                padding: 0 14px;
                border-radius: 8px;
                background: #2563EB;
                color: white;
                font-size: 12px;
                font-weight: 700;
                border: none;
            }
            QPushButton:disabled {
                background: #9CA3AF;
            }
        """)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)

        cl.addLayout(btn_row)

        root.addWidget(card)

        # Wire
        self.cancel_btn.clicked.connect(self._handle_cancel)
        self.save_btn.clicked.connect(self._handle_save)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("""
            font-size: 11px;
            color: rgba(0,0,0,0.55);
            font-weight: 600;
        """)
        return lbl

    # ------------------------------------------------------------
    # DATA: categories
    # ------------------------------------------------------------
    def _load_categories(self):
        try:
            self._categories = self.api.get_categories(include_image=False) or []

            self.category_combo.clear()

            if not self._categories:
                self.category_combo.addItem("No categories found", None)
                return

            self.category_combo.addItem("Select a category...", None)

            for c in self._categories:
                # Expecting {"id": int, "name": str}
                cid = c.get("id")
                cname = c.get("name") or "Unnamed"
                self.category_combo.addItem(cname, cid)

        except Exception:
            self.category_combo.clear()
            self.category_combo.addItem("Failed to load categories", None)

    # ------------------------------------------------------------
    # DATA: edit mode
    # ------------------------------------------------------------
    def _load_product_if_edit(self):
        if not self.product:
            return

        self.name_input.setText(self.product.get("name", ""))
        self.brand_input.setText(self.product.get("brand", ""))
        self.price_input.setText(str(self.product.get("price", "")))
        self.min_stock_spin.setValue(int(self.product.get("min_stock_level", 10)))
        self.details_input.setPlainText(self.product.get("details", ""))

        # Stock is computed via batches; we won't prefill "initial stock" in edit mode
        self.stock_spin.setValue(0)

        # If the product dict includes category_id use it;
        # if only category name is present, best effort select by name.
        category_id = self.product.get("category_id")
        category_name = self.product.get("category")

        if category_id is not None:
            self._select_category_by_id(category_id)
        elif category_name:
            self._select_category_by_name(category_name)

        self.save_btn.setText("Update Product")

    def _select_category_by_id(self, cid):
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == cid:
                self.category_combo.setCurrentIndex(i)
                return

    def _select_category_by_name(self, name):
        name = (name or "").strip().lower()
        for i in range(self.category_combo.count()):
            txt = (self.category_combo.itemText(i) or "").strip().lower()
            if txt == name:
                self.category_combo.setCurrentIndex(i)
                return

    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------
    def _handle_cancel(self):
        # Just clear fields if used standalone
        self.name_input.clear()
        self.brand_input.clear()
        self.price_input.clear()
        self.min_stock_spin.setValue(10)
        self.stock_spin.setValue(0)
        self.details_input.clear()
        if self.category_combo.count() > 0:
            self.category_combo.setCurrentIndex(0)

    def _handle_save(self):
        name = self.name_input.text().strip()
        brand = self.brand_input.text().strip() or None
        price_text = self.price_input.text().strip()
        min_stock = int(self.min_stock_spin.value())
        stock_level = int(self.stock_spin.value())
        details = self.details_input.toPlainText().strip() or None

        category_id = self.category_combo.currentData()

        if not name:
            QMessageBox.warning(self, "Missing Field", "Product name is required.")
            return

        if not price_text.isdigit():
            QMessageBox.warning(self, "Invalid Price", "Price must be a whole number.")
            return

        if category_id is None:
            QMessageBox.warning(self, "Missing Field", "Please select a category.")
            return

        price = int(price_text)

        # Expiration date only meaningful if initial stock is used
        expiration_date = None
        if stock_level > 0:
            expiration_date = self.exp_date.date().toString("yyyy-MM-dd")

        added_by = self.user.get("id")

        try:
            if not self.product:
                created = self.api.create_product(
                    name=name,
                    price=price,
                    brand=brand,
                    category_id=category_id,
                    min_stock_level=min_stock,
                    details=details,
                    stock_level=stock_level if stock_level > 0 else None,
                    expiration_date=expiration_date,
                    added_by=added_by
                )
                QMessageBox.information(self, "Success", "Product created successfully.")
                self.product_saved.emit(created)

            else:
                # PATCH update
                updated = self.api.update_product(
                    self.product.get("id"),
                    name=name,
                    price=price,
                    brand=brand,
                    category_id=category_id,
                    min_stock_level=min_stock,
                    details=details,
                    # Optional: allow "stock_level" additive restock only if user typed >0
                    stock_level=stock_level if stock_level > 0 else None,
                    expiration_date=expiration_date,
                    added_by=added_by
                )
                QMessageBox.information(self, "Success", "Product updated successfully.")
                self.product_saved.emit(updated)

        except StockaDoodleAPIError as e:
            QMessageBox.critical(self, "API Error", str(e))
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", "Unexpected error while saving product.")

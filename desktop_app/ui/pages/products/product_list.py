# desktop_app/ui/pages/products/product_list.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QComboBox,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from desktop_app.api_client.stockadoodle_api import StockaDoodleAPI
from desktop_app.utils.helpers import get_feather_icon


# ===========================================
# PRODUCT FORM DIALOG (ADD / EDIT)
# ===========================================
class ProductFormDialog(QDialog):
    def __init__(self, api: StockaDoodleAPI, categories: dict,
                 product: dict | None = None, parent=None):
        super().__init__(parent)
        self.api = api
        self.categories = categories or {}
        self.product = product

        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(420)

        self._build_ui()
        if self.product:
            self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit()
        self.brand_input = QLineEdit()

        self.price_input = QSpinBox()
        self.price_input.setRange(0, 1_000_000)
        self.price_input.setSingleStep(10)

        self.category_combo = QComboBox()

        if self.categories:
            for cid, cname in self.categories.items():
                self.category_combo.addItem(str(cname), cid)
        else:
            # fallback placeholder so UI doesn't look broken
            self.category_combo.addItem("— No categories loaded —", None)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 99_999)

        self.details_input = QTextEdit()

        form.addRow("Name:", self.name_input)
        form.addRow("Brand:", self.brand_input)
        form.addRow("Price (₱, whole number):", self.price_input)
        form.addRow("Category:", self.category_combo)
        form.addRow("Min Stock Level:", self.min_stock_input)
        form.addRow("Details:", self.details_input)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self.setStyleSheet("""
            QDialog { background: #FFFFFF; }
            QLabel { font-size: 13px; }
            QLineEdit, QSpinBox, QComboBox, QTextEdit {
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                padding: 6px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #7FA2FF;
                background: #F9FBFF;
            }
            QPushButton#primaryBtn {
                background: #0A2A83;
                color: white;
                padding: 8px 18px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton#primaryBtn:hover {
                background: #153AAB;
            }
        """)

    def _populate(self):
        self.name_input.setText(self.product.get("name", ""))
        self.brand_input.setText(self.product.get("brand", ""))
        self.price_input.setValue(int(self.product.get("price", 0)))
        self.min_stock_input.setValue(int(self.product.get("min_stock_level", 0)))
        self.details_input.setPlainText(self.product.get("details", "") or "")

        # We support both server styles:
        # - product has category_id
        # - product has category (name string)
        category_id = self.product.get("category_id")
        if category_id is not None:
            idx = self.category_combo.findData(category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

    def _on_save(self):
        name = self.name_input.text().strip()
        brand = self.brand_input.text().strip()
        price = self.price_input.value()
        min_stock = self.min_stock_input.value()
        details = self.details_input.toPlainText().strip()
        category_id = self.category_combo.currentData()

        if not name:
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return

        try:
            payload = dict(
                name=name,
                brand=brand,
                price=price,
                min_stock_level=min_stock,
                details=details,
                category_id=category_id
            )

            if self.product:
                self.api.update_product(self.product["id"], **payload)
            else:
                self.api.create_product(**payload)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save product:\n{e}")


# ===========================================
# MAIN PRODUCT LIST PAGE
# ===========================================
class ProductListPage(QWidget):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)

        self.user = user_data or {}
        self.api = StockaDoodleAPI()

        self.current_page = 1
        self.per_page = 10
        self.total_pages = 1

        self.category_map: dict[int, str] = {}

        self._build_ui()
        self._load_categories()
        self.load_products()

    # ---------------------------------------
    # UI BUILD
    # ---------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(18)

        # Header Row
        header_row = QHBoxLayout()
        title = QLabel("Products")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
        """)
        header_row.addWidget(title)
        header_row.addStretch()

        self.btn_add = QPushButton("Add Product")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.setIcon(get_feather_icon("plus", 16))
        self.btn_add.setFixedHeight(38)
        self.btn_add.clicked.connect(self._open_add_dialog)
        header_row.addWidget(self.btn_add)

        root.addLayout(header_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Brand", "Category",
            "Price (₱)", "Stock", "Min Stock", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        self.table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #DDE3EA;
                gridline-color: #E3E8F5;
            }
            QHeaderView::section {
                background-color: #F4F6FD;
                padding: 6px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 4px;
                font-size: 13px;
            }
        """)

        root.addWidget(self.table)

        # Pagination Row
        pager_row = QHBoxLayout()
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setStyleSheet("font-size: 13px; color: #666;")
        pager_row.addWidget(self.page_label)

        pager_row.addStretch()

        self.btn_prev = QPushButton("Prev")
        self.btn_next = QPushButton("Next")

        for btn in (self.btn_prev, self.btn_next):
            btn.setFixedHeight(32)

        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

        pager_row.addWidget(self.btn_prev)
        pager_row.addWidget(self.btn_next)

        root.addLayout(pager_row)

        self.setStyleSheet("""
            QPushButton#primaryBtn {
                background: #0A2A83;
                color: white;
                border-radius: 8px;
                padding: 0 18px;
                font-weight: 600;
            }
            QPushButton#primaryBtn:hover {
                background: #153AAB;
            }
        """)

    # ---------------------------------------
    # DATA LOADING
    # ---------------------------------------
    def _load_categories(self):
        """
        Cache category id -> name.

        Handles both API styles:
        1) returns a list
        2) returns {"categories": [...]}
        """
        try:
            cats = self.api.get_categories()

            if isinstance(cats, dict):
                cats_list = cats.get("categories", [])
            else:
                cats_list = cats or []

            self.category_map = {
                c.get("id"): c.get("name", "Unknown")
                for c in cats_list
                if c and c.get("id") is not None
            }

        except Exception:
            self.category_map = {}

    def load_products(self):
        try:
            result = self.api.get_products(page=self.current_page, per_page=self.per_page)
            products = result.get("products", [])

            self.total_pages = result.get("pages", 1) or 1
            self._populate_table(products)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products:\n{e}")
            self._populate_table([])

    def _populate_table(self, products: list[dict]):
        self.table.setRowCount(0)

        for row_idx, product in enumerate(products):
            self.table.insertRow(row_idx)

            def set_item(col, text):
                item = QTableWidgetItem(str(text))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col, item)

            set_item(0, product.get("id", ""))
            set_item(1, product.get("name", ""))
            set_item(2, product.get("brand", ""))

            # Support both server keys:
            # - category_id
            # - category (name)
            cat_name = "—"
            if product.get("category"):
                cat_name = product.get("category")
            else:
                cat_name = self.category_map.get(product.get("category_id"), "—")

            set_item(3, cat_name)

            set_item(4, product.get("price", 0))
            set_item(5, product.get("stock_level", 0))
            set_item(6, product.get("min_stock_level", 0))

            # Actions column
            actions_widget = QWidget()
            h = QHBoxLayout(actions_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)

            # Edit button
            btn_edit = QPushButton()
            edit_icon = get_feather_icon("edit-2", 14)
            if isinstance(edit_icon, QIcon) and not edit_icon.isNull():
                btn_edit.setIcon(edit_icon)
            else:
                btn_edit.setText("Edit")

            btn_edit.setFixedSize(34, 28)
            btn_edit.setToolTip("Edit product")
            btn_edit.setStyleSheet("""
                QPushButton {
                    border: 1px solid #D9E4FF;
                    background: #F3F6FF;
                    border-radius: 6px;
                    font-size: 11px;
                    padding: 0 6px;
                }
                QPushButton:hover {
                    background: #E8EEFF;
                }
            """)
            btn_edit.clicked.connect(lambda _, p=product: self._open_edit_dialog(p))

            # Delete button
            btn_delete = QPushButton()
            del_icon = get_feather_icon("trash-2", 14)
            if isinstance(del_icon, QIcon) and not del_icon.isNull():
                btn_delete.setIcon(del_icon)
            else:
                btn_delete.setText("Del")

            btn_delete.setFixedSize(34, 28)
            btn_delete.setToolTip("Delete product")
            btn_delete.setStyleSheet("""
                QPushButton {
                    border: 1px solid #FFD6D6;
                    background: #FFF2F2;
                    border-radius: 6px;
                    font-size: 11px;
                    padding: 0 6px;
                    color: #8A1E1E;
                }
                QPushButton:hover {
                    background: #FFE6E6;
                }
            """)
            btn_delete.clicked.connect(lambda _, p=product: self._confirm_delete(p))

            h.addWidget(btn_edit)
            h.addWidget(btn_delete)
            h.addStretch()

            self.table.setCellWidget(row_idx, 7, actions_widget)

        self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

    # ---------------------------------------
    # PAGINATION
    # ---------------------------------------
    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_products()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_products()

    # ---------------------------------------
    # CRUD HANDLERS
    # ---------------------------------------
    def _open_add_dialog(self):
        dlg = ProductFormDialog(self.api, self.category_map, parent=self)
        if dlg.exec():
            self._load_categories()
            self.load_products()

    def _open_edit_dialog(self, product: dict):
        dlg = ProductFormDialog(self.api, self.category_map, product=product, parent=self)
        if dlg.exec():
            self._load_categories()
            self.load_products()

    def _confirm_delete(self, product: dict):
        name = product.get("name", "this product")
        reply = QMessageBox.question(
            self,
            "Delete Product",
            f"Are you sure you want to permanently delete:\n\n{name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.api.delete_product(product.get("id"))
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete product:\n{e}")

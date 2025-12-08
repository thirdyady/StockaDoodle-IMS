# desktop_app/ui/pages/products/product_list.py

from __future__ import annotations

from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QComboBox,
    QMessageBox, QFrame, QSizePolicy, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from desktop_app.utils.helpers import get_feather_icon
from desktop_app.utils.api_wrapper import get_api

from desktop_app.ui.components.stock_batch_selector import StockBatchSelector
from desktop_app.ui.components.product_card import ProductCard
from desktop_app.ui.components.category_form_dialog import CategoryFormDialog


# ===========================================
# PRODUCT FORM DIALOG (ADD / EDIT)
# ===========================================
class ProductFormDialog(QDialog):
    def __init__(self, api, categories: dict, product: dict | None = None, parent=None):
        super().__init__(parent)
        self.api = api
        self.categories = categories or {}
        self.product = product

        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(440)

        self._build_ui()
        if self.product:
            self._populate()

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
        self.brand_input = QLineEdit()

        self.price_input = QSpinBox()
        self.price_input.setRange(0, 1_000_000)
        self.price_input.setSingleStep(10)

        self.category_combo = QComboBox()
        if self.categories:
            for cid, cname in self.categories.items():
                self.category_combo.addItem(str(cname), cid)
        else:
            self.category_combo.addItem("— No categories loaded —", None)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 99_999)

        self.details_input = QTextEdit()
        self.details_input.setFixedHeight(90)

        form.addRow("Name:", self.name_input)
        form.addRow("Brand:", self.brand_input)
        form.addRow("Price (₱):", self.price_input)
        form.addRow("Category:", self.category_combo)
        form.addRow("Min Stock Level:", self.min_stock_input)
        form.addRow("Details:", self.details_input)

        form_layout.addLayout(form)
        root.addWidget(form_card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

        self.setStyleSheet("""
            QDialog { background: #F7F9FC; }
            QLineEdit, QSpinBox, QComboBox, QTextEdit {
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                padding: 6px 8px;
                font-size: 13px;
                background: #FFFFFF;
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
            QPushButton#primaryBtn:hover { background: #153AAB; }
        """)

    def _populate(self):
        self.name_input.setText(self.product.get("name", ""))
        self.brand_input.setText(self.product.get("brand", ""))
        self.price_input.setValue(int(self.product.get("price", 0)))
        self.min_stock_input.setValue(int(self.product.get("min_stock_level", 0)))
        self.details_input.setPlainText(self.product.get("details", "") or "")

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
# STOCK BATCHES DIALOG
# ===========================================
class StockBatchesDialog(QDialog):
    def __init__(self, api, product: dict, parent=None):
        super().__init__(parent)
        self.api = api
        self.product = product or {}
        self.product_id = self.product.get("id")

        name = self.product.get("name", "Product")
        self.setWindowTitle(f"Stock Batches — {name}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(520)

        self._build_ui()
        self._load_batches()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        header_card = QFrame()
        header_card.setObjectName("Card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)

        title = QLabel(self.product.get("name", "Product"))
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0A2A83;")

        meta = QLabel(
            f"ID: {self.product.get('id', '—')}    "
            f"Brand: {self.product.get('brand', '—')}    "
            f"Price: ₱{self.product.get('price', 0)}"
        )
        meta.setObjectName("muted")

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(title)
        title_col.addWidget(meta)

        header_layout.addLayout(title_col)
        header_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(32)
        btn_close.clicked.connect(self.accept)
        header_layout.addWidget(btn_close)

        root.addWidget(header_card)

        self.selector = StockBatchSelector(self.product_id or 0, parent=self)
        self.selector.batches_updated.connect(self._load_batches)
        root.addWidget(self.selector, 1)

        self.setStyleSheet("""
            QDialog { background: #F7F9FC; }
            QPushButton {
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid #D3D8E5;
                background: #FFFFFF;
            }
            QPushButton:hover { background: #F3F6FF; }
        """)

    def _load_batches(self):
        if not self.product_id:
            QMessageBox.warning(self, "Error", "Invalid product ID.")
            return

        try:
            result = self.api.get_stock_batches(self.product_id)

            batches = []
            if isinstance(result, dict):
                batches = result.get("stock_batches", []) or result.get("batches", []) or []

            self.selector.load_batches(batches)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load stock batches:\n{e}")
            self.selector.load_batches([])


# ===========================================
# MAIN INVENTORY PAGE (CARD GRID)
# ===========================================
class ProductListPage(QWidget):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)

        self.user = user_data or {}
        self.api = get_api()

        self.category_map: dict[int, str] = {}
        self.all_products: List[Dict[str, Any]] = []
        self.filtered_products: List[Dict[str, Any]] = []

        self._build_ui()
        self._load_categories()
        self._load_all_products()

    # ---------------------------------------
    # UI BUILD
    # ---------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(18)

        # Header row
        header = QHBoxLayout()
        title = QLabel("Inventory")
        title.setObjectName("title")
        header.addWidget(title)

        subtitle = QLabel("Manage products, pricing, categories, and stock batches.")
        subtitle.setObjectName("muted")
        header.addWidget(subtitle)

        header.addStretch()

        self.btn_add_category = QPushButton("Add Category")
        self.btn_add_category.setIcon(get_feather_icon("folder-plus", 16))
        self.btn_add_category.setFixedHeight(36)
        self.btn_add_category.clicked.connect(self._open_add_category_dialog)
        header.addWidget(self.btn_add_category)

        self.btn_add = QPushButton("Add Product")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.setIcon(get_feather_icon("plus", 16))
        self.btn_add.setFixedHeight(36)
        self.btn_add.clicked.connect(self._open_add_dialog)
        header.addWidget(self.btn_add)

        root.addLayout(header)

        # Filter bar (replaces old global header search)
        filter_card = QFrame()
        filter_card.setObjectName("Card")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(14, 10, 14, 10)
        filter_layout.setSpacing(10)

        filter_label = QLabel("Filter")
        filter_label.setObjectName("CardTitle")
        filter_layout.addWidget(filter_label)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search by name, brand, or category (not case sensitive)")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input, 1)

        self.btn_clear_filter = QPushButton("Clear")
        self.btn_clear_filter.setFixedHeight(30)
        self.btn_clear_filter.clicked.connect(lambda: self.filter_input.setText(""))
        filter_layout.addWidget(self.btn_clear_filter)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setFixedHeight(30)
        self.btn_refresh.clicked.connect(self._load_all_products)
        filter_layout.addWidget(self.btn_refresh)

        root.addWidget(filter_card)

        # Grid card wrapper
        grid_card = QFrame()
        grid_card.setObjectName("Card")
        grid_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        grid_card_layout = QVBoxLayout(grid_card)
        grid_card_layout.setContentsMargins(12, 12, 12, 12)
        grid_card_layout.setSpacing(8)

        card_title = QLabel("Products")
        card_title.setObjectName("CardTitle")
        grid_card_layout.addWidget(card_title)

        # Scroll area with grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)

        self.scroll.setWidget(self.grid_host)
        grid_card_layout.addWidget(self.scroll, 1)

        root.addWidget(grid_card, 1)

    # ---------------------------------------
    # DATA LOADING
    # ---------------------------------------
    def _load_categories(self):
        try:
            cats = self.api.get_categories()
            cats_list = cats if isinstance(cats, list) else cats.get("categories", []) or []

            self.category_map = {
                c.get("id"): c.get("name", "Unknown")
                for c in cats_list
                if c and c.get("id") is not None
            }

        except Exception:
            self.category_map = {}

    def _load_all_products(self):
        """
        Since pagination UI is removed, we fetch a larger set.
        We also attempt to walk pages if backend supports it.
        """
        products: List[Dict[str, Any]] = []

        try:
            first = self.api.get_products(page=1, per_page=50)
            products.extend(first.get("products", []) or [])
            pages = int(first.get("pages", 1) or 1)

            # Fetch remaining pages (bounded for safety)
            max_pages = min(pages, 20)
            for p in range(2, max_pages + 1):
                res = self.api.get_products(page=p, per_page=50)
                products.extend(res.get("products", []) or [])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products:\n{e}")
            products = []

        self.all_products = products
        self._apply_filter()

    # ---------------------------------------
    # FILTERING
    # ---------------------------------------
    def _apply_filter(self):
        q = (self.filter_input.text() if hasattr(self, "filter_input") else "") or ""
        q = q.strip().lower()

        if not q:
            self.filtered_products = list(self.all_products)
            self._render_cards()
            return

        def cat_name_for(p: Dict[str, Any]) -> str:
            if p.get("category"):
                return str(p.get("category"))
            cid = p.get("category_id")
            return str(self.category_map.get(cid, ""))

        filtered = []
        for p in self.all_products:
            name = str(p.get("name", "")).lower()
            brand = str(p.get("brand", "")).lower()
            cat = cat_name_for(p).lower()

            if q in name or q in brand or q in cat:
                filtered.append(p)

        self.filtered_products = filtered
        self._render_cards()

    # ---------------------------------------
    # CARD RENDERER
    # ---------------------------------------
    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def _render_cards(self):
        self._load_categories()  # keep category names fresh
        self._clear_grid()

        items = self.filtered_products

        # 3 cards per row
        cols = 3
        row = 0
        col = 0

        for product in items:
            cat_name = "—"
            if product.get("category"):
                cat_name = str(product.get("category"))
            else:
                cat_name = self.category_map.get(product.get("category_id"), "—")

            card = ProductCard(
                product=product,
                category_name=cat_name,
                on_edit=self._open_edit_dialog,
                on_stock=self._open_stock_batches,
                on_delete=self._confirm_delete
            )

            self.grid.addWidget(card, row, col)

            col += 1
            if col >= cols:
                col = 0
                row += 1

        # Add a stretch spacer row
        self.grid.setRowStretch(row + 1, 1)

    # ---------------------------------------
    # CRUD HANDLERS
    # ---------------------------------------
    def _open_add_category_dialog(self):
        dlg = CategoryFormDialog(self.api, parent=self)
        if dlg.exec():
            self._load_categories()
            self._apply_filter()

    def _open_add_dialog(self):
        self._load_categories()
        dlg = ProductFormDialog(self.api, self.category_map, parent=self)
        if dlg.exec():
            self._load_all_products()

    def _open_edit_dialog(self, product: dict):
        self._load_categories()
        dlg = ProductFormDialog(self.api, self.category_map, product=product, parent=self)
        if dlg.exec():
            self._load_all_products()

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
                self._load_all_products()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete product:\n{e}")

    # ---------------------------------------
    # STOCK BATCH ENTRY POINT
    # ---------------------------------------
    def _open_stock_batches(self, product: dict):
        dlg = StockBatchesDialog(self.api, product, parent=self)
        dlg.exec()
        self._load_all_products()

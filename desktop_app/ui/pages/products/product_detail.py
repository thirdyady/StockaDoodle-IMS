# desktop_app/ui/pages/products/product_detail.py

from __future__ import annotations

from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt

from desktop_app.utils.api_wrapper import (
    get_product, get_stock_batches, get_current_user_data, delete_product
)
from desktop_app.ui.components.stock_batch_selector import StockBatchSelector
from desktop_app.ui.components.confirm_delete_dialog import ConfirmDeleteDialog


class ProductDetailPage(QWidget):
    """
    Product detail page that displays single product information
    plus stock batch management UI.
    """

    def __init__(
        self,
        user_data: Optional[Dict[str, Any]] = None,
        product_id: Optional[int] = None,
        product: Optional[Dict[str, Any]] = None,
        parent=None
    ):
        super().__init__(parent)

        self.user = user_data or {}
        self.product_id = product_id or (product.get("id") if product else None)
        self.product: Dict[str, Any] = product or {}

        self._build_ui()

        # Load fresh data if ID is available
        if self.product_id is not None:
            self.reload()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)

        # Header row
        header = QHBoxLayout()

        self.title_lbl = QLabel("Product Details")
        self.title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #0A0A0A;")
        header.addWidget(self.title_lbl)

        header.addStretch()

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setFixedHeight(34)
        self.btn_edit.setEnabled(False)  # wired by list/detail flow if you want later
        self.btn_edit.setStyleSheet("""
            QPushButton {
                padding: 0 14px;
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                background: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #F7F9FF;
            }
        """)
        header.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedHeight(34)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                padding: 0 14px;
                border-radius: 8px;
                border: 1px solid #FECACA;
                background: #FFF5F5;
                color: #B91C1C;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #FFECEC;
            }
        """)
        self.btn_delete.clicked.connect(self._on_delete_product)
        header.addWidget(self.btn_delete)

        root.addLayout(header)

        # Info card
        self.info_card = QFrame()
        self.info_card.setObjectName("productInfoCard")
        self.info_card.setStyleSheet("""
            #productInfoCard {
                background: #FFFFFF;
                border: 1px solid #E5EAF5;
                border-radius: 14px;
            }
        """)

        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.setSpacing(10)

        self.meta_lbl = QLabel("")
        self.meta_lbl.setStyleSheet("font-size: 12px; color: rgba(0,0,0,0.55);")

        self.name_lbl = QLabel("—")
        self.name_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #0A2A83;")

        self.brand_lbl = QLabel("Brand: —")
        self.price_lbl = QLabel("Price: —")
        self.category_lbl = QLabel("Category: —")
        self.stock_lbl = QLabel("Current Stock: —")
        self.min_stock_lbl = QLabel("Low-stock threshold: —")
        self.details_lbl = QLabel("")

        for w in [self.brand_lbl, self.price_lbl, self.category_lbl, self.stock_lbl, self.min_stock_lbl]:
            w.setStyleSheet("font-size: 13px; color: #24324F; font-weight: 600;")

        self.details_lbl.setWordWrap(True)
        self.details_lbl.setStyleSheet("font-size: 12px; color: rgba(0,0,0,0.6);")

        info_layout.addWidget(self.meta_lbl)
        info_layout.addWidget(self.name_lbl)
        info_layout.addSpacing(4)
        info_layout.addWidget(self.brand_lbl)
        info_layout.addWidget(self.price_lbl)
        info_layout.addWidget(self.category_lbl)
        info_layout.addWidget(self.stock_lbl)
        info_layout.addWidget(self.min_stock_lbl)
        info_layout.addSpacing(6)
        info_layout.addWidget(self.details_lbl)

        root.addWidget(self.info_card)

        # Stock batch selector container
        self.batch_card = QFrame()
        self.batch_card.setObjectName("batchCard")
        self.batch_card.setStyleSheet("""
            #batchCard {
                background: #FFFFFF;
                border: 1px solid #E5EAF5;
                border-radius: 14px;
            }
        """)

        batch_layout = QVBoxLayout(self.batch_card)
        batch_layout.setContentsMargins(22, 18, 22, 18)
        batch_layout.setSpacing(12)

        # Selector widget
        self.batch_selector = StockBatchSelector(self.product_id or 0, parent=self)
        self.batch_selector.batches_updated.connect(self._load_batches)

        batch_layout.addWidget(self.batch_selector)

        root.addWidget(self.batch_card)

        # Spacer
        root.addStretch(1)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def set_product(self, product_id: int, product: Optional[Dict[str, Any]] = None):
        self.product_id = product_id
        self.product = product or {}
        self.batch_selector.product_id = product_id
        self.reload()

    def reload(self):
        self._load_product()
        self._load_batches()

    # ---------------------------------------------------------
    # Data loading
    # ---------------------------------------------------------
    def _load_product(self):
        if self.product_id is None:
            return

        try:
            data = get_product(self.product_id, include_image=False, include_batches=False)
            # Backend might return {"product": {...}} or the product dict itself
            if isinstance(data, dict) and "product" in data:
                self.product = data.get("product") or {}
            elif isinstance(data, dict):
                self.product = data
            else:
                self.product = {}

            self._render_product()

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load product:\n{str(e)}")

    def _load_batches(self):
        if self.product_id is None:
            return

        try:
            data = get_stock_batches(self.product_id)
            batches = []

            if isinstance(data, dict):
                batches = data.get("batches", []) or data.get("stock_batches", []) or []
            if not isinstance(batches, list):
                batches = []

            self.batch_selector.load_batches(batches)

            # Update stock label from server result if available
            new_stock = data.get("new_stock_level") if isinstance(data, dict) else None
            if new_stock is not None:
                self.stock_lbl.setText(f"Current Stock: {new_stock}")

        except Exception as e:
            # Don't hard-crash the page for batch errors
            QMessageBox.warning(self, "Batch Error", f"Failed to load stock batches:\n{str(e)}")

    # ---------------------------------------------------------
    # Render
    # ---------------------------------------------------------
    def _render_product(self):
        p = self.product or {}

        pid = p.get("id", self.product_id or "—")
        name = p.get("name", "—")
        brand = p.get("brand") or "—"
        price = p.get("price")
        category_name = (
            p.get("category_name")
            or (p.get("category") if isinstance(p.get("category"), str) else None)
            or "—"
        )
        stock = p.get("stock_level", p.get("stock", "—"))
        min_stock = p.get("min_stock_level", p.get("min_stock", "—"))
        details = p.get("details") or ""

        # Header title
        self.title_lbl.setText("Product Details")
        self.meta_lbl.setText(f"ID: {pid}")

        self.name_lbl.setText(name)
        self.brand_lbl.setText(f"Brand: {brand}")

        if price is None:
            self.price_lbl.setText("Price: —")
        else:
            try:
                self.price_lbl.setText(f"Price: ₱{float(price):,.2f}")
            except Exception:
                self.price_lbl.setText(f"Price: {price}")

        self.category_lbl.setText(f"Category: {category_name}")
        self.stock_lbl.setText(f"Current Stock: {stock}")
        self.min_stock_lbl.setText(f"Low-stock threshold: {min_stock}")

        self.details_lbl.setText(details)

        # Enable edit only if you wire it later
        self.btn_edit.setEnabled(True)

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------
    def _on_delete_product(self):
        if self.product_id is None:
            return

        product_snapshot = dict(self.product or {})
        product_snapshot["id"] = self.product_id

        def do_delete(pid: int):
            user = get_current_user_data() or {}
            uid = user.get("id")
            delete_product(pid, user_id=uid)

        dlg = ConfirmDeleteDialog(product_snapshot, on_confirm=do_delete, parent=self)
        if dlg.exec():
            # If your list page handles navigation back, great.
            # Otherwise we just clear out the view.
            self.product = {}
            self.product_id = None
            self.title_lbl.setText("Product Details")
            self.meta_lbl.setText("")
            self.name_lbl.setText("—")
            self.brand_lbl.setText("Brand: —")
            self.price_lbl.setText("Price: —")
            self.category_lbl.setText("Category: —")
            self.stock_lbl.setText("Current Stock: —")
            self.min_stock_lbl.setText("Low-stock threshold: —")
            self.details_lbl.setText("")
            self.batch_selector.load_batches([])

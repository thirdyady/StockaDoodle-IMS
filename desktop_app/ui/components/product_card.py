# desktop_app/ui/components/product_card.py

from __future__ import annotations

from typing import Dict, Any, Callable, Optional

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from desktop_app.utils.helpers import get_feather_icon


class ProductCard(QFrame):
    """
    Compact product card for the 3-column Inventory layout.

    Adds:
    - Thumbnail with graceful placeholder.
    """

    def __init__(
        self,
        product: Dict[str, Any],
        category_name: str = "—",
        on_edit: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_stock: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], None]] = None,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.product = product
        self.category_name = category_name

        self.on_edit = on_edit
        self.on_stock = on_stock
        self.on_delete = on_delete

        self.setObjectName("productCard")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        name = str(self.product.get("name", ""))
        brand = str(self.product.get("brand", ""))
        price = float(self.product.get("price", 0) or 0)
        stock = int(self.product.get("stock_level", 0) or 0)
        pid = self.product.get("id", "—")
        min_stock = self.product.get("min_stock_level", "—")

        # -------------------------
        # Thumbnail
        # -------------------------
        thumb = QLabel()
        thumb.setObjectName("productThumb")
        thumb.setFixedHeight(90)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)

        img_path = (
            self.product.get("thumbnail")
            or self.product.get("image")
            or self.product.get("image_path")
            or self.product.get("photo")
            or ""
        )

        pix = QPixmap(str(img_path)) if img_path else QPixmap()
        if not pix.isNull():
            thumb.setPixmap(pix.scaled(
                220, 90,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            thumb.setStyleSheet("background: #F8FAFF; border-radius: 10px;")
        else:
            thumb.setText("No Image")
            thumb.setStyleSheet("""
                QLabel#productThumb {
                    background: #F8FAFF;
                    border: 1px dashed #D7DEEE;
                    border-radius: 10px;
                    color: rgba(15,23,42,0.45);
                    font-size: 11px;
                    font-weight: 600;
                }
            """)

        root.addWidget(thumb)

        # -------------------------
        # Title row
        # -------------------------
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title = QLabel(name)
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0F172A;")

        title_row.addWidget(title, 1)

        stock_badge = QLabel(f"Stock: {stock}")
        stock_badge.setObjectName("badge")
        stock_badge.setStyleSheet("""
            QLabel#badge {
                background: #EEF3FF;
                color: #0A2A83;
                padding: 2px 8px;
                border-radius: 999px;
                font-size: 10px;
                font-weight: 700;
            }
        """)
        title_row.addWidget(stock_badge, 0)

        root.addLayout(title_row)

        # Meta
        brand_lbl = QLabel(brand if brand else "—")
        brand_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: rgba(15,23,42,0.60);")

        cat_lbl = QLabel(self.category_name or "—")
        cat_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: rgba(15,23,42,0.60);")

        root.addWidget(brand_lbl)
        root.addWidget(cat_lbl)

        # Price row
        price_lbl = QLabel(f"₱{price:,.2f}")
        price_lbl.setStyleSheet("font-size: 18px; font-weight: 900; color: #0A2A83;")
        root.addWidget(price_lbl)

        # Actions row
        actions = QHBoxLayout()
        actions.setSpacing(6)

        btn_edit = QPushButton()
        btn_stock = QPushButton()
        btn_delete = QPushButton()

        self._apply_icon(btn_edit, "edit-2", "Edit")
        self._apply_icon(btn_stock, "package", "Stock")
        self._apply_icon(btn_delete, "trash-2", "Delete")

        btn_edit.clicked.connect(lambda: self.on_edit(self.product) if self.on_edit else None)
        btn_stock.clicked.connect(lambda: self.on_stock(self.product) if self.on_stock else None)
        btn_delete.clicked.connect(lambda: self.on_delete(self.product) if self.on_delete else None)

        for b in (btn_edit, btn_stock, btn_delete):
            b.setFixedHeight(28)

        actions.addWidget(btn_edit)
        actions.addWidget(btn_stock)
        actions.addWidget(btn_delete)
        actions.addStretch()

        root.addLayout(actions)

        # Hidden metadata in tooltip
        self.setToolTip(
            f"ID: {pid}\n"
            f"Min Stock: {min_stock}\n"
            f"Category: {self.category_name or '—'}"
        )

        # Card styling
        self.setStyleSheet("""
            QFrame#productCard {
                background: #FFFFFF;
                border: 1px solid #E2E8F5;
                border-radius: 14px;
            }
            QPushButton {
                border-radius: 8px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #D7DEEE;
                background: #FFFFFF;
            }
            QPushButton:hover {
                background: #F4F7FF;
            }
        """)

    def _apply_icon(self, btn: QPushButton, icon_name: str, fallback_text: str):
        icon = get_feather_icon(icon_name, 14)
        if isinstance(icon, QIcon) and not icon.isNull():
            btn.setIcon(icon)
        else:
            btn.setText(fallback_text)

# desktop_app/ui/sales/sales_records.py

from __future__ import annotations

from typing import Dict, Any, Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QStyledItemDelegate, QApplication
)
from PyQt6.QtCore import Qt, QEvent, QRect
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QStyle, QStyleOptionButton, QStyleOptionViewItem

from desktop_app.utils.api_wrapper import get_api
from desktop_app.utils.app_state import get_current_user


class ReturnButtonDelegate(QStyledItemDelegate):
    """
    Paints a real-looking button inside a table cell (no setCellWidget),
    so it never clips/overlaps gridlines and behaves with selection/hover.
    """

    def __init__(self, parent, on_click):
        super().__init__(parent)
        self._on_click = on_click
        self._pressed_rc = None  # (row, col) while mouse is pressed

    def _button_rect(self, cell_rect: QRect) -> QRect:
        # Keep it comfortably inside the cell (prevents gridline overlap)
        margin_x = 12
        margin_y = 10
        btn_h = 28
        btn_w = 104

        r = cell_rect.adjusted(margin_x, margin_y, -margin_x, -margin_y)
        x = r.x() + (r.width() - btn_w) // 2
        y = r.y() + (r.height() - btn_h) // 2
        return QRect(x, y, btn_w, btn_h)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        # 1) Let Qt paint the normal cell background/selection (so row highlight works)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""  # we don't want text in this column
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        # 2) Paint a button inside the cell
        btn_rect = self._button_rect(option.rect)

        btn_opt = QStyleOptionButton()
        btn_opt.rect = btn_rect
        btn_opt.text = "Return"
        btn_opt.state = QStyle.StateFlag.State_Enabled

        # hover effect
        if option.state & QStyle.StateFlag.State_MouseOver:
            btn_opt.state |= QStyle.StateFlag.State_MouseOver

        # pressed effect
        if self._pressed_rc == (index.row(), index.column()):
            btn_opt.state |= QStyle.StateFlag.State_Sunken

        # Use the widget's style so it respects your app theme
        style.drawControl(QStyle.ControlElement.CE_PushButton, btn_opt, painter, opt.widget)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if self._button_rect(option.rect).contains(event.pos()):
                self._pressed_rc = (index.row(), index.column())
                if option.widget:
                    option.widget.viewport().update(option.rect)
                return True

        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            was_pressed = (self._pressed_rc == (index.row(), index.column()))
            self._pressed_rc = None
            if option.widget:
                option.widget.viewport().update(option.rect)

            if was_pressed and self._button_rect(option.rect).contains(event.pos()):
                sale_id = index.data(Qt.ItemDataRole.UserRole)
                sale_item_index = index.data(Qt.ItemDataRole.UserRole + 1)
                if sale_id is not None and sale_item_index is not None:
                    self._on_click(str(sale_id), sale_item_index)
                return True

        return False


class SalesRecordsPage(QWidget):
    """
    Sales Tab (sold items log).
    - One row per sale item
    - Return action per row
    - No date range / retailer filter UI
    """

    PAGE_SIZE = 10
    ROW_HEIGHT = 46
    ACTION_COL_WIDTH = 150

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.api = get_api()

        self._all_sale_items: List[Dict[str, Any]] = []
        self.current_page = 1
        self.total_pages = 1

        self._build_ui()
        self.refresh()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _peso(self, v: Any) -> str:
        try:
            return f"₱{float(v):,.2f}"
        except Exception:
            return "₱0.00"

    def _logged_in_user_id(self) -> Optional[int]:
        try:
            u = getattr(self.api, "current_user", None)
            if isinstance(u, dict) and u.get("id") is not None:
                return int(u["id"])
        except Exception:
            pass

        try:
            u2 = get_current_user()
            if isinstance(u2, dict) and u2.get("id") is not None:
                return int(u2["id"])
        except Exception:
            pass

        try:
            if isinstance(self.user, dict) and self.user.get("id") is not None:
                return int(self.user["id"])
        except Exception:
            pass

        return None

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(14)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        title = QLabel("Sales")
        title.setObjectName("title")
        hdr.addWidget(title)

        subtitle = QLabel("Sold items log (from Point of Sale).")
        subtitle.setObjectName("muted")
        hdr.addWidget(subtitle)

        hdr.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setObjectName("ghost")
        self.btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(self.btn_refresh)

        root.addLayout(hdr)

        # Card
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        hint = QLabel("Each row is a sold item. Use Return to mark an item as returned.")
        hint.setObjectName("muted")
        card_layout.addWidget(hint)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Sale ID", "Retailer", "Product", "Qty", "Unit Price", "Line Total", ""]
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setWordWrap(False)
        self.table.setShowGrid(True)
        self.table.setMouseTracking(True)  # enables hover visuals for delegate

        # Stable row sizing
        vh = self.table.verticalHeader()
        vh.setVisible(False)
        vh.setDefaultSectionSize(self.ROW_HEIGHT)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)

        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        # Fixed action column
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, self.ACTION_COL_WIDTH)

        # ✅ Delegate-based button (NO setCellWidget)
        self.table.setItemDelegateForColumn(6, ReturnButtonDelegate(self.table, self._return_item))

        self.table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        card_layout.addWidget(self.table, 1)

        # Pagination bar
        pag_row = QHBoxLayout()
        pag_row.setSpacing(8)

        self.btn_prev = QPushButton("←")
        self.btn_prev.setFixedWidth(42)
        self.btn_prev.clicked.connect(self._prev_page)

        self.btn_next = QPushButton("→")
        self.btn_next.setFixedWidth(42)
        self.btn_next.clicked.connect(self._next_page)

        self.page_label = QLabel("Page 1 / 1")
        self.page_label.setObjectName("muted")

        pag_row.addWidget(self.btn_prev)
        pag_row.addWidget(self.btn_next)
        pag_row.addSpacing(8)
        pag_row.addWidget(self.page_label)
        pag_row.addStretch()

        card_layout.addLayout(pag_row)
        root.addWidget(card, 1)

    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------
    def refresh(self):
        try:
            res = self.api.get_sales(start_date=None, end_date=None, retailer_id=None)

            items: List[Dict[str, Any]] = []
            if isinstance(res, dict):
                maybe = res.get("sale_items")
                if isinstance(maybe, list):
                    items = maybe

            self._all_sale_items = items
            self.current_page = 1

            total = len(self._all_sale_items)
            self.total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

            self._render_page()

        except Exception as e:
            QMessageBox.critical(self, "Sales", str(e))
            self._all_sale_items = []
            self.current_page = 1
            self.total_pages = 1
            self._render_page()

    # ---------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------
    def _render_page(self):
        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_items = (self._all_sale_items or [])[start:end]

        sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)

        self.table.setRowCount(len(page_items))

        for row, item in enumerate(page_items):
            self.table.setRowHeight(row, self.ROW_HEIGHT)

            sale_id = str(item.get("sale_id", ""))
            retailer = str(item.get("retailer_name", "") or item.get("retailer_id", ""))
            product = str(item.get("product_name", "") or item.get("product_id", ""))
            qty = str(item.get("quantity", ""))
            unit_price = self._peso(item.get("unit_price", 0))
            line_total = self._peso(item.get("line_total", 0))

            vals = [sale_id, retailer, product, qty, unit_price, line_total]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, c, it)

            # Action column item holds IDs (delegate uses these on click)
            sale_item_index = item.get("sale_item_index", None)
            action_item = QTableWidgetItem("")
            action_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # no editing, no text selection needed
            action_item.setData(Qt.ItemDataRole.UserRole, sale_id)
            action_item.setData(Qt.ItemDataRole.UserRole + 1, sale_item_index)
            self.table.setItem(row, 6, action_item)

        self.table.setSortingEnabled(sorting)

        self.page_label.setText(f"Page {self.current_page} / {self.total_pages}")
        self.btn_prev.setDisabled(self.current_page <= 1)
        self.btn_next.setDisabled(self.current_page >= self.total_pages)

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------
    def _return_item(self, sale_id: str, sale_item_index: Any):
        if not sale_id or sale_item_index is None:
            QMessageBox.warning(self, "Return", "Missing sale_id or sale_item_index.")
            return

        user_id = self._logged_in_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Return", "No logged-in user ID found.")
            return

        confirm = QMessageBox.question(
            self,
            "Return Item",
            f"Mark this sold item as returned?\n\nSale ID: {sale_id}\nItem Index: {sale_item_index}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            fn = getattr(self.api, "return_sale_item", None)
            if callable(fn):
                fn(int(sale_id), int(sale_item_index), user_id=user_id)
            else:
                req = getattr(self.api, "_request", None)
                if not callable(req):
                    raise Exception("API client missing return_sale_item() and _request().")
                req(
                    "DELETE",
                    f"/sales/{int(sale_id)}/items/{int(sale_item_index)}",
                    json={"user_id": user_id}
                )

            QMessageBox.information(self, "Return", "Item returned successfully.")
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Return Failed", str(e))

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_page()

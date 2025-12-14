# desktop_app/ui/sales/sales_management.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QFrame,
    QSizePolicy, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
    QStyledItemDelegate, QApplication, QStyle, QStyleOptionViewItem
)
from PyQt6.QtCore import Qt, QEvent, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from desktop_app.utils.api_wrapper import get_api
from desktop_app.utils.app_state import get_current_user


# ------------------------------------------------------------
# Delegates: Add/Remove buttons + Qty stepper (NO QSpinBox)
# ------------------------------------------------------------
class ActionButtonDelegate(QStyledItemDelegate):
    """
    Paints a button inside a table cell (NO setCellWidget),
    so it never overlaps gridlines and behaves correctly with selection/hover.
    """

    def __init__(self, parent, text: str, on_click, kind: str = "add"):
        super().__init__(parent)
        self._text = text
        self._on_click = on_click  # callback(product_id:int)
        self._pressed_rc: Optional[tuple[int, int]] = None  # (row, col)
        self._kind = kind  # "add" or "remove"

    def _button_rect(self, cell_rect: QRect) -> QRect:
        margin_x = 10
        margin_y = 10
        btn_h = 30
        btn_w = 108 if self._kind == "remove" else 96

        r = cell_rect.adjusted(margin_x, margin_y, -margin_x, -margin_y)
        x = r.x() + (r.width() - btn_w) // 2
        y = r.y() + (r.height() - btn_h) // 2
        return QRect(x, y, btn_w, btn_h)

    def _colors(self, hovered: bool, pressed: bool):
        if self._kind == "add":
            bg = QColor("#EEF3FF")
            border = QColor("#C9D6F3")
            text = QColor("#0A2A83")
            if hovered:
                bg = QColor("#DBEAFE")
                border = QColor("#7AA7FF")
            if pressed:
                bg = QColor("#C7D2FE")
                border = QColor("#6B86FF")
            return bg, border, text

        # remove
        bg = QColor("#FFFFFF")
        border = QColor("#D9E2F5")
        text = QColor("#0F172A")
        if hovered:
            bg = QColor("#F1F5FF")
            border = QColor("#9BB6FF")
        if pressed:
            bg = QColor("#E2E8F0")
            border = QColor("#94A3B8")
        return bg, border, text

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        # 1) Paint normal cell background/selection
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        # 2) Paint button
        btn_rect = self._button_rect(option.rect)

        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        pressed = (self._pressed_rc == (index.row(), index.column()))
        bg, border, text = self._colors(hovered=hovered, pressed=pressed)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(border)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(bg)
        painter.drawRoundedRect(btn_rect, 10, 10)

        painter.setPen(text)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, self._text)

        painter.restore()

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
                pid = index.data(Qt.ItemDataRole.UserRole)
                if pid is not None:
                    try:
                        self._on_click(int(pid))
                    except Exception:
                        pass
                return True

        return False


class QtyStepperDelegate(QStyledItemDelegate):
    """
    Paints a compact qty control inside the Qty cell:

        [ - ]  [  3  ]  [ + ]

    and handles clicks/wheel to increment/decrement.

    This avoids QSpinBox arrows being hidden by your global stylesheet/theme.
    """

    def __init__(self, parent, on_qty_change):
        super().__init__(parent)
        self._on_qty_change = on_qty_change  # callback(product_id:int, qty:int)
        self._pressed: Optional[tuple[int, int, str]] = None  # (row, col, "minus"/"plus")

    def _outer_rect(self, cell_rect: QRect) -> QRect:
        # keep it comfortably inside the cell to avoid gridline overlap
        margin_x = 8
        margin_y = 10
        h = 30

        r = cell_rect.adjusted(margin_x, margin_y, -margin_x, -margin_y)
        y = r.y() + (r.height() - h) // 2
        return QRect(r.x(), y, r.width(), h)

    def _parts(self, cell_rect: QRect):
        outer = self._outer_rect(cell_rect)

        btn_w = 26
        gap = 6
        minus_rect = QRect(outer.x(), outer.y(), btn_w, outer.height())
        plus_rect = QRect(outer.right() - btn_w + 1, outer.y(), btn_w, outer.height())

        center_x = minus_rect.right() + 1 + gap
        center_w = outer.width() - (btn_w * 2) - (gap * 2)
        center_rect = QRect(center_x, outer.y(), max(40, center_w), outer.height())

        return outer, minus_rect, center_rect, plus_rect

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        # 1) paint standard cell background/selection first
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        # 2) read data
        try:
            qty = int(index.data(Qt.ItemDataRole.DisplayRole) or 1)
        except Exception:
            qty = 1

        try:
            stock = int(index.data(Qt.ItemDataRole.UserRole + 1) or 1)
        except Exception:
            stock = 1

        qty = max(1, min(qty, max(1, stock)))

        # 3) geometry
        outer, minus_rect, center_rect, plus_rect = self._parts(option.rect)

        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        pressed_minus = (self._pressed == (index.row(), index.column(), "minus"))
        pressed_plus = (self._pressed == (index.row(), index.column(), "plus"))

        # 4) draw
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # outer stroke
        border = QColor(0, 0, 0, 45) if hovered else QColor(0, 0, 0, 35)
        pen = QPen(border)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(outer, 8, 8)

        # buttons background
        btn_bg = QColor("#F8FAFF")
        btn_bg_hover = QColor("#EEF3FF")
        btn_bg_pressed = QColor("#DBEAFE")

        # minus
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(btn_bg_pressed if pressed_minus else (btn_bg_hover if hovered else btn_bg))
        painter.drawRoundedRect(minus_rect, 8, 8)

        # plus
        painter.setBrush(btn_bg_pressed if pressed_plus else (btn_bg_hover if hovered else btn_bg))
        painter.drawRoundedRect(plus_rect, 8, 8)

        # center area
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(center_rect, 8, 8)

        # symbols
        txt = QColor("#0F172A")
        muted = QColor(15, 23, 42, 160)

        # disable look if qty at limits
        minus_color = muted if qty <= 1 else txt
        plus_color = muted if qty >= stock else txt

        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        painter.setPen(minus_color)
        painter.drawText(minus_rect, Qt.AlignmentFlag.AlignCenter, "–")

        painter.setPen(plus_color)
        painter.drawText(plus_rect, Qt.AlignmentFlag.AlignCenter, "+")

        # qty text
        painter.setPen(txt)
        painter.drawText(center_rect, Qt.AlignmentFlag.AlignCenter, str(qty))

        painter.restore()

    def _apply_change(self, model, index, delta: int):
        # pid stored in UserRole
        pid = index.data(Qt.ItemDataRole.UserRole)
        if pid is None:
            return

        try:
            pid_int = int(pid)
        except Exception:
            return

        try:
            qty = int(index.data(Qt.ItemDataRole.DisplayRole) or 1)
        except Exception:
            qty = 1

        try:
            stock = int(index.data(Qt.ItemDataRole.UserRole + 1) or 1)
        except Exception:
            stock = 1

        stock = max(1, stock)
        qty = max(1, min(qty, stock))

        new_qty = qty + delta
        new_qty = max(1, min(new_qty, stock))

        if new_qty == qty:
            return

        # update model text
        model.setData(index, str(new_qty), Qt.ItemDataRole.DisplayRole)

        # notify logic layer
        try:
            self._on_qty_change(pid_int, new_qty)
        except Exception:
            pass

    def editorEvent(self, event, model, option, index):
        # wheel to change qty
        if event.type() == QEvent.Type.Wheel:
            # QWheelEvent: angleDelta().y() positive => up
            try:
                dy = event.angleDelta().y()
            except Exception:
                dy = 0
            if dy != 0:
                self._apply_change(model, index, 1 if dy > 0 else -1)
                if option.widget:
                    option.widget.viewport().update(option.rect)
                return True

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            _, minus_rect, _, plus_rect = self._parts(option.rect)

            if minus_rect.contains(event.pos()):
                self._pressed = (index.row(), index.column(), "minus")
                if option.widget:
                    option.widget.viewport().update(option.rect)
                return True

            if plus_rect.contains(event.pos()):
                self._pressed = (index.row(), index.column(), "plus")
                if option.widget:
                    option.widget.viewport().update(option.rect)
                return True

            return False

        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            pressed = self._pressed
            self._pressed = None

            if option.widget:
                option.widget.viewport().update(option.rect)

            if not pressed:
                return False

            _, minus_rect, _, plus_rect = self._parts(option.rect)
            kind = pressed[2]

            if kind == "minus" and minus_rect.contains(event.pos()):
                self._apply_change(model, index, -1)
                return True

            if kind == "plus" and plus_rect.contains(event.pos()):
                self._apply_change(model, index, +1)
                return True

            return False

        return False


# ------------------------------------------------------------
# Data
# ------------------------------------------------------------
@dataclass
class CartItem:
    product_id: int
    name: str
    brand: str
    price: float
    stock: int
    quantity: int = 1

    @property
    def line_total(self) -> float:
        return float(self.price) * int(self.quantity)


class PointOfSalePage(QWidget):
    """
    POS page integrated with API.

    Fixes:
    - Add/Remove are delegate buttons (no setCellWidget overlap)
    - Qty is delegate stepper (- / +) (no QSpinBox arrows to get hidden)
    - Qty column stays compact so Product text stays readable
    """

    ROW_HEIGHT = 52

    # Compact widths to reduce horizontal scroll in non-fullscreen
    RESULTS_ACTION_COL_WIDTH = 120
    CART_ACTION_COL_WIDTH = 128
    CART_QTY_COL_WIDTH = 110

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}

        self.api = get_api()
        self.cart_items: List[CartItem] = []
        self.products_cache: List[Dict[str, Any]] = []
        self._cart_row_by_pid: Dict[int, int] = {}
        self._product_by_id: Dict[int, Dict[str, Any]] = {}

        self.init_ui()
        self.load_products_initial()

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------
    def log_msg(self, text: str):
        self.messages.append(text)

    def show_error(self, title: str, msg: str):
        QMessageBox.critical(self, title, msg)

    def show_info(self, title: str, msg: str):
        QMessageBox.information(self, title, msg)

    def peso(self, value: Any) -> str:
        try:
            return f"₱{float(value):,.2f}"
        except Exception:
            return "₱0.00"

    def _get_logged_in_user_id(self) -> Optional[int]:
        try:
            user = getattr(self.api, "current_user", None)
            if isinstance(user, dict) and user.get("id") is not None:
                return int(user["id"])
        except Exception:
            pass

        try:
            user2 = get_current_user()
            if isinstance(user2, dict) and user2.get("id") is not None:
                return int(user2["id"])
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
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(10)

        title = QLabel("Point of Sale")
        title.setObjectName("title")
        header.addWidget(title)

        subtitle = QLabel("Checkout and record sales.")
        subtitle.setObjectName("muted")
        header.addWidget(subtitle)

        header.addStretch()
        root.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(16)

        # LEFT
        left = QVBoxLayout()
        left.setSpacing(12)

        search_card = QFrame()
        search_card.setObjectName("Card")
        search_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        sc_layout = QVBoxLayout(search_card)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl = QLabel("Product search")
        lbl.setStyleSheet("font-weight: 800; background: transparent;")
        row1.addWidget(lbl)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by product name or brand")
        self.search.returnPressed.connect(self.on_search_clicked)
        self.search.setMinimumHeight(34)
        row1.addWidget(self.search, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("secondaryBtn")
        self.search_btn.setMinimumHeight(34)
        self.search_btn.clicked.connect(self.on_search_clicked)
        row1.addWidget(self.search_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("ghost")
        self.refresh_btn.setMinimumHeight(34)
        self.refresh_btn.clicked.connect(self.load_products_initial)
        row1.addWidget(self.refresh_btn)

        sc_layout.addLayout(row1)

        note = QLabel("Note: FEFO batch deduction is applied automatically by the backend.")
        note.setObjectName("muted")
        sc_layout.addWidget(note)

        left.addWidget(search_card)

        # Products card
        results_card = QFrame()
        results_card.setObjectName("Card")
        results_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(14, 12, 14, 12)
        results_layout.setSpacing(10)

        results_header = QLabel("Products")
        results_header.setObjectName("CardTitle")
        results_layout.addWidget(results_header)

        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(["ID", "Name", "Brand", "Price", "Stock", ""])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setWordWrap(False)
        self.results_table.setShowGrid(True)
        self.results_table.setMouseTracking(True)
        self.results_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        vh = self.results_table.verticalHeader()
        vh.setVisible(False)
        vh.setDefaultSectionSize(self.ROW_HEIGHT)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        hh = self.results_table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Name
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Brand
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Price
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Stock
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)            # Add
        self.results_table.setColumnWidth(5, self.RESULTS_ACTION_COL_WIDTH)

        self.results_table.setItemDelegateForColumn(
            5, ActionButtonDelegate(self.results_table, "Add", self._on_add_clicked, kind="add")
        )

        results_layout.addWidget(self.results_table, 1)
        left.addWidget(results_card, 1)

        # RIGHT
        right = QVBoxLayout()
        right.setSpacing(12)

        cart_card = QFrame()
        cart_card.setObjectName("Card")
        cart_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(14, 12, 14, 12)
        cart_layout.setSpacing(10)

        cart_header_row = QHBoxLayout()
        cart_header_row.setSpacing(10)

        cart_header = QLabel("Cart")
        cart_header.setObjectName("CardTitle")
        cart_header_row.addWidget(cart_header)
        cart_header_row.addStretch()

        self.clear_cart_btn = QPushButton("Clear")
        self.clear_cart_btn.setObjectName("ghost")
        self.clear_cart_btn.setMinimumHeight(32)
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        cart_header_row.addWidget(self.clear_cart_btn)

        cart_layout.addLayout(cart_header_row)

        self.cart_table = QTableWidget(0, 6)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Unit", "Line Total", "Stock", ""])
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cart_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.cart_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # qty handled by delegate
        self.cart_table.setWordWrap(False)
        self.cart_table.setShowGrid(True)
        self.cart_table.setMouseTracking(True)
        self.cart_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        vh2 = self.cart_table.verticalHeader()
        vh2.setVisible(False)
        vh2.setDefaultSectionSize(self.ROW_HEIGHT)
        vh2.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        hh2 = self.cart_table.horizontalHeader()
        hh2.setStretchLastSection(False)

        hh2.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)          # Product
        hh2.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)            # Qty
        hh2.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Unit
        hh2.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Line Total
        hh2.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Stock
        hh2.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)            # Remove

        hh2.setMinimumSectionSize(60)
        self.cart_table.setColumnWidth(1, self.CART_QTY_COL_WIDTH)
        self.cart_table.setColumnWidth(5, self.CART_ACTION_COL_WIDTH)

        self.cart_table.setItemDelegateForColumn(
            5, ActionButtonDelegate(self.cart_table, "Remove", self._on_remove_clicked, kind="remove")
        )
        self.cart_table.setItemDelegateForColumn(
            1, QtyStepperDelegate(self.cart_table, self._on_qty_changed_by_pid)
        )

        cart_layout.addWidget(self.cart_table, 1)

        total_row = QHBoxLayout()
        total_row.addStretch()
        self.total_label = QLabel("Total: ₱0.00")
        self.total_label.setObjectName("CardValue")
        total_row.addWidget(self.total_label)
        cart_layout.addLayout(total_row)

        self.checkout_btn = QPushButton("Checkout")
        self.checkout_btn.setObjectName("primaryBtn")
        self.checkout_btn.setMinimumHeight(42)
        self.checkout_btn.clicked.connect(self.on_checkout)
        cart_layout.addWidget(self.checkout_btn)

        right.addWidget(cart_card, 2)

        # Messages card
        msg_card = QFrame()
        msg_card.setObjectName("Card")
        msg_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        msg_layout = QVBoxLayout(msg_card)
        msg_layout.setContentsMargins(14, 12, 14, 12)
        msg_layout.setSpacing(10)

        msg_title = QLabel("System Messages")
        msg_title.setObjectName("CardTitle")
        msg_layout.addWidget(msg_title)

        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setPlaceholderText("System messages will appear here.")
        self.messages.setMinimumHeight(140)
        msg_layout.addWidget(self.messages)

        right.addWidget(msg_card)

        content.addLayout(left, 3)
        content.addLayout(right, 3)
        root.addLayout(content, 1)

    # ---------------------------------------------------------
    # Delegate callbacks
    # ---------------------------------------------------------
    def _on_add_clicked(self, product_id: int):
        prod = self._product_by_id.get(int(product_id))
        if prod:
            self.add_to_cart(prod)

    def _on_remove_clicked(self, product_id: int):
        self.remove_from_cart(int(product_id))

    def _on_qty_changed_by_pid(self, product_id: int, new_qty: int):
        item = self.find_cart_item(int(product_id))
        if not item:
            return

        if new_qty > item.stock:
            new_qty = item.stock
        if new_qty < 1:
            new_qty = 1

        item.quantity = int(new_qty)

        row = self._cart_row_by_pid.get(int(product_id))
        if row is not None:
            it = QTableWidgetItem(self.peso(item.line_total))
            it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.cart_table.setItem(row, 3, it)

        self.update_total_label()

    # ---------------------------------------------------------
    # Products loading / searching
    # ---------------------------------------------------------
    def load_products_initial(self):
        try:
            res = self.api.get_products(page=1, per_page=100)
            self.products_cache = res.get("products", []) or []
            self.render_results(self.products_cache)
            self.log_msg(f"Loaded {len(self.products_cache)} products.")
        except Exception as e:
            self.products_cache = []
            self.render_results([])
            self.log_msg(f"Failed to load products: {e}")

    def on_search_clicked(self):
        query = self.search.text().strip()

        if query:
            try:
                res = self.api.get_products(page=1, per_page=100, name=query)
                products = res.get("products", []) or []
                self.products_cache = products
                self.render_results(products)
                self.log_msg(f"Search backend: '{query}' → {len(products)} results.")
                return
            except Exception:
                pass

        if not self.products_cache:
            self.load_products_initial()
            return

        if not query:
            self.render_results(self.products_cache)
            self.log_msg("Showing all cached products.")
            return

        q_lower = query.lower()
        filtered = [
            p for p in self.products_cache
            if q_lower in str(p.get("name", "")).lower()
            or q_lower in str(p.get("brand", "")).lower()
        ]
        self.render_results(filtered)
        self.log_msg(f"Search local: '{query}' → {len(filtered)} results.")

    def render_results(self, products: List[Dict[str, Any]]):
        sorting = self.results_table.isSortingEnabled()
        self.results_table.setSortingEnabled(False)

        self._product_by_id = {}
        self.results_table.setRowCount(len(products))

        for row, p in enumerate(products):
            self.results_table.setRowHeight(row, self.ROW_HEIGHT)

            pid = int(p.get("id"))
            name = str(p.get("name", ""))
            brand = str(p.get("brand", ""))
            price = float(p.get("price", 0))
            stock = int(p.get("stock_level", 0))

            self._product_by_id[pid] = p

            it0 = QTableWidgetItem(str(pid))
            it1 = QTableWidgetItem(name)
            it2 = QTableWidgetItem(brand)
            it3 = QTableWidgetItem(self.peso(price))
            it4 = QTableWidgetItem(str(stock))

            for it in (it0, it1, it2, it3, it4):
                it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            self.results_table.setItem(row, 0, it0)
            self.results_table.setItem(row, 1, it1)
            self.results_table.setItem(row, 2, it2)
            self.results_table.setItem(row, 3, it3)
            self.results_table.setItem(row, 4, it4)

            action = QTableWidgetItem("")
            action.setFlags(Qt.ItemFlag.ItemIsEnabled)
            action.setData(Qt.ItemDataRole.UserRole, pid)
            self.results_table.setItem(row, 5, action)

        self.results_table.setSortingEnabled(sorting)

    # ---------------------------------------------------------
    # Cart logic
    # ---------------------------------------------------------
    def find_cart_item(self, product_id: int) -> Optional[CartItem]:
        for item in self.cart_items:
            if item.product_id == product_id:
                return item
        return None

    def add_to_cart(self, product: Dict[str, Any]):
        try:
            pid = int(product.get("id"))
            name = str(product.get("name", ""))
            brand = str(product.get("brand", ""))
            price = float(product.get("price", 0))
            stock = int(product.get("stock_level", 0))

            if stock <= 0:
                self.show_error("Out of Stock", f"'{name}' has no available stock.")
                return

            existing = self.find_cart_item(pid)
            if existing:
                if existing.quantity + 1 > stock:
                    self.show_error("Stock Limit", f"Cannot exceed available stock for '{name}'.")
                    return
                existing.quantity += 1
            else:
                self.cart_items.append(CartItem(
                    product_id=pid,
                    name=name,
                    brand=brand,
                    price=price,
                    stock=stock,
                    quantity=1
                ))

            self.render_cart()
            self.log_msg(f"Added to cart: {name}")

        except Exception as e:
            self.show_error("Add to Cart Error", str(e))

    def remove_from_cart(self, product_id: int):
        self.cart_items = [i for i in self.cart_items if i.product_id != product_id]
        self.render_cart()

    def clear_cart(self):
        self.cart_items = []
        self.render_cart()

    def render_cart(self):
        sorting = self.cart_table.isSortingEnabled()
        self.cart_table.setSortingEnabled(False)

        self._cart_row_by_pid = {}
        self.cart_table.setRowCount(len(self.cart_items))

        for row, item in enumerate(self.cart_items):
            self.cart_table.setRowHeight(row, self.ROW_HEIGHT)
            self._cart_row_by_pid[item.product_id] = row

            it0 = QTableWidgetItem(item.name)
            it1 = QTableWidgetItem(str(item.quantity))  # displayed qty (delegate draws control)
            it2 = QTableWidgetItem(self.peso(item.price))
            it3 = QTableWidgetItem(self.peso(item.line_total))
            it4 = QTableWidgetItem(str(item.stock))

            it0.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            it2.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            it3.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            it4.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            # Qty cell must be enabled/selectable so delegate gets events
            it1.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            # store pid + stock for qty delegate
            it1.setData(Qt.ItemDataRole.UserRole, item.product_id)
            it1.setData(Qt.ItemDataRole.UserRole + 1, item.stock)

            self.cart_table.setItem(row, 0, it0)
            self.cart_table.setItem(row, 1, it1)
            self.cart_table.setItem(row, 2, it2)
            self.cart_table.setItem(row, 3, it3)
            self.cart_table.setItem(row, 4, it4)

            action = QTableWidgetItem("")
            action.setFlags(Qt.ItemFlag.ItemIsEnabled)
            action.setData(Qt.ItemDataRole.UserRole, item.product_id)
            self.cart_table.setItem(row, 5, action)

        self.cart_table.setSortingEnabled(sorting)
        self.update_total_label()

    def update_total_label(self):
        total = sum(i.line_total for i in self.cart_items)
        self.total_label.setText(f"Total: {self.peso(total)}")

    # ---------------------------------------------------------
    # Checkout
    # ---------------------------------------------------------
    def on_checkout(self):
        if not self.cart_items:
            self.show_error("Checkout Error", "Your cart is empty.")
            return

        retailer_id = self._get_logged_in_user_id()
        if retailer_id is None:
            self.show_error(
                "Checkout Error",
                "No logged-in user ID found.\n"
                "Please login again so the system can detect the seller."
            )
            return

        items_payload = []
        total_amount = 0.0

        for item in self.cart_items:
            line_total = round(item.line_total, 2)
            items_payload.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "line_total": line_total
            })
            total_amount += line_total

        total_amount = round(total_amount, 2)

        try:
            self.api.record_sale(
                retailer_id=retailer_id,
                items=items_payload,
                total_amount=total_amount
            )

            self.show_info("Sale Recorded", "Sale recorded successfully.")
            self.log_msg(f"Sale success | Retailer #{retailer_id} | Total {self.peso(total_amount)}")

            self.clear_cart()
            self.load_products_initial()

        except Exception as e:
            self.show_error("Checkout Error", str(e))
            self.log_msg(f"Checkout failed: {e}")


# Backward compatible name (so existing imports / dynamic loader won't break)
SalesManagementPage = PointOfSalePage

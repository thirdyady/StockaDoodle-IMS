# desktop_app/ui/sales/sales_management.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QFrame,
    QSizePolicy, QMessageBox, QTableWidget, QTableWidgetItem,
    QSpinBox, QHeaderView
)
from PyQt6.QtCore import Qt

from desktop_app.utils.api_wrapper import get_api
from desktop_app.utils.app_state import get_current_user


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


class SalesManagementPage(QWidget):
    """
    Functional POS / Sales page integrated with the real API.

    - Retailer ID input removed.
    - Retailer ID inferred from logged-in user.
    - Added Refresh button.
    - "Results" renamed to "Products".
    """

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}

        self.api = get_api()
        self.cart_items: List[CartItem] = []
        self.products_cache: List[Dict[str, Any]] = []

        self.init_ui()
        self.load_products_initial()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(18)

        # Title row
        header = QHBoxLayout()
        title = QLabel("Sales")
        title.setObjectName("title")
        header.addWidget(title)

        subtitle = QLabel("Point-of-sale and sales recording.")
        subtitle.setObjectName("muted")
        header.addWidget(subtitle)

        header.addStretch()
        root.addLayout(header)

        # Main content split
        content = QHBoxLayout()
        content.setSpacing(16)

        # LEFT: Search + Products table
        left = QVBoxLayout()
        left.setSpacing(12)

        # Search card
        search_card = QFrame()
        search_card.setObjectName("Card")
        search_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sc_layout = QVBoxLayout(search_card)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Product search"))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by product name or brand")
        row1.addWidget(self.search, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedHeight(32)
        self.search_btn.clicked.connect(self.on_search_clicked)
        row1.addWidget(self.search_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedHeight(32)
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
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(14, 12, 14, 12)
        results_layout.setSpacing(8)

        results_header = QLabel("Products")
        results_header.setObjectName("CardTitle")
        results_layout.addWidget(results_header)

        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(["ID", "Name", "Brand", "Price", "Stock", ""])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setMinimumHeight(320)

        # ✅ Better column UX
        try:
            hh = self.results_table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Name
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Brand
            hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Price
            hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Stock
            hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Button
        except Exception:
            pass

        # Hard nudge widths for readability
        self.results_table.setColumnWidth(0, 60)
        self.results_table.setColumnWidth(2, 140)
        self.results_table.setColumnWidth(5, 80)

        results_layout.addWidget(self.results_table)

        left.addWidget(results_card, 1)

        # RIGHT: Cart
        right = QVBoxLayout()
        right.setSpacing(12)

        cart_card = QFrame()
        cart_card.setObjectName("Card")
        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(14, 12, 14, 12)
        cart_layout.setSpacing(8)

        cart_header_row = QHBoxLayout()
        cart_header = QLabel("Cart")
        cart_header.setObjectName("CardTitle")
        cart_header_row.addWidget(cart_header)
        cart_header_row.addStretch()

        self.clear_cart_btn = QPushButton("Clear")
        self.clear_cart_btn.setFixedHeight(28)
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        cart_header_row.addWidget(self.clear_cart_btn)

        cart_layout.addLayout(cart_header_row)

        self.cart_table = QTableWidget(0, 6)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Unit", "Line Total", "Stock", ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.setMinimumHeight(260)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        cart_layout.addWidget(self.cart_table)

        total_row = QHBoxLayout()
        total_row.addStretch()
        self.total_label = QLabel("Total: ₱0.00")
        self.total_label.setObjectName("CardValue")
        total_row.addWidget(self.total_label)
        cart_layout.addLayout(total_row)

        self.checkout_btn = QPushButton("Checkout")
        self.checkout_btn.setObjectName("primaryBtn")
        self.checkout_btn.setFixedHeight(40)
        self.checkout_btn.clicked.connect(self.on_checkout)
        cart_layout.addWidget(self.checkout_btn)

        right.addWidget(cart_card, 1)

        # Messages card
        msg_card = QFrame()
        msg_card.setObjectName("Card")
        msg_layout = QVBoxLayout(msg_card)
        msg_layout.setContentsMargins(14, 12, 14, 12)
        msg_layout.setSpacing(8)

        msg_title = QLabel("System Messages")
        msg_title.setObjectName("CardTitle")
        msg_layout.addWidget(msg_title)

        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setPlaceholderText("System messages will appear here.")
        self.messages.setFixedHeight(140)
        msg_layout.addWidget(self.messages)

        right.addWidget(msg_card)

        content.addLayout(left, 2)
        content.addLayout(right, 2)
        root.addLayout(content)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Logged-in user ID
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Products loading / searching
    # ------------------------------------------------------------------
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
        self.results_table.setRowCount(0)

        for p in products:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            pid = int(p.get("id"))
            name = str(p.get("name", ""))
            brand = str(p.get("brand", ""))
            price = float(p.get("price", 0))
            stock = int(p.get("stock_level", 0))

            self.results_table.setItem(row, 0, QTableWidgetItem(str(pid)))
            self.results_table.setItem(row, 1, QTableWidgetItem(name))
            self.results_table.setItem(row, 2, QTableWidgetItem(brand))
            self.results_table.setItem(row, 3, QTableWidgetItem(self.peso(price)))
            self.results_table.setItem(row, 4, QTableWidgetItem(str(stock)))

            add_btn = QPushButton("Add")
            add_btn.setFixedHeight(26)
            add_btn.setMinimumWidth(60)
            add_btn.clicked.connect(lambda _, prod=p: self.add_to_cart(prod))
            self.results_table.setCellWidget(row, 5, add_btn)

        try:
            self.results_table.resizeColumnsToContents()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Cart
    # ------------------------------------------------------------------
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
        self.cart_table.setRowCount(0)

        for item in self.cart_items:
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)

            self.cart_table.setItem(row, 0, QTableWidgetItem(item.name))

            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(max(1, item.stock))
            qty_spin.setValue(item.quantity)
            qty_spin.valueChanged.connect(lambda val, it=item: self.on_qty_changed(it, val))
            self.cart_table.setCellWidget(row, 1, qty_spin)

            self.cart_table.setItem(row, 2, QTableWidgetItem(self.peso(item.price)))
            self.cart_table.setItem(row, 3, QTableWidgetItem(self.peso(item.line_total)))
            self.cart_table.setItem(row, 4, QTableWidgetItem(str(item.stock)))

            rm_btn = QPushButton("Remove")
            rm_btn.setFixedHeight(26)
            rm_btn.clicked.connect(lambda _, pid=item.product_id: self.remove_from_cart(pid))
            self.cart_table.setCellWidget(row, 5, rm_btn)

        self.update_total_label()

    def on_qty_changed(self, item: CartItem, new_qty: int):
        if new_qty > item.stock:
            new_qty = item.stock
        item.quantity = int(new_qty)
        self.render_cart()

    def update_total_label(self):
        total = sum(i.line_total for i in self.cart_items)
        self.total_label.setText(f"Total: {self.peso(total)}")

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------
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

# desktop_app/ui/main_window.py

import importlib
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel
)
from PyQt6.QtCore import Qt

from desktop_app.ui.side_bar import SideBar
from desktop_app.ui.header_bar import HeaderBar

from desktop_app.ui.pages.dashboard import DashboardPage
from desktop_app.ui.pages.products.product_list import ProductListPage
from desktop_app.ui.pages.profile import ProfilePage


# ---------------------------------------------------------
# Simple placeholder page for missing modules
# ---------------------------------------------------------
class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str = "This page is not implemented yet."):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(10)

        t = QLabel(title)
        t.setStyleSheet("font-size: 24px; font-weight: 800;")

        s = QLabel(subtitle)
        s.setStyleSheet("font-size: 13px; color: rgba(0,0,0,0.55);")

        layout.addWidget(t)
        layout.addWidget(s)
        layout.addStretch()


# ---------------------------------------------------------
# Safe dynamic import helpers
# ---------------------------------------------------------
def load_page_class(module_candidates, class_candidates):
    """
    Try importing a module from a list of module paths.
    Then try retrieving a class from a list of class names.
    Returns the class or None.
    """
    for mod_name in module_candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue

        for cls_name in class_candidates:
            cls = getattr(mod, cls_name, None)
            if cls:
                return cls

    return None


class MainWindow(QMainWindow):
    """
    Main shell:
    - Header (top)
    - Sidebar (left)
    - Stack pages (right)
    """

    def __init__(self, user_data=None):
        super().__init__()
        self.user = user_data or {}

        self.setWindowTitle("StockaDoodle")
        self.setMinimumSize(1200, 720)

        self._build_ui()
        self._wire_signals()

    # =========================================================
    # UI BUILD
    # =========================================================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self.header = HeaderBar(self.user)
        root.addWidget(self.header)

        # Body row
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        # Sidebar
        self.sidebar = SideBar(self.user)
        body.addWidget(self.sidebar)

        # Stack
        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)

        # Map labels -> widgets
        self.pages_by_label = {}

        # -----------------------------
        # Always-available pages
        # -----------------------------
        self.dashboard_page = DashboardPage(self.user)
        self._add_page("Dashboard", self.dashboard_page)

        self.inventory_page = ProductListPage(self.user)
        self._add_page("Inventory", self.inventory_page)

        self.profile_page = ProfilePage(self.user)
        self._add_page("Profile", self.profile_page)

        # -----------------------------
        # Sales page
        # Your actual structure:
        # ✅ desktop_app/ui/sales/sales_management.py
        # -----------------------------
        sales_module_candidates = [
            "desktop_app.ui.sales.sales_management",
            # fallback patterns in case teammates added alternates
            "desktop_app.ui.pages.sales.sales_page",
            "desktop_app.ui.sales.sales_page",
        ]
        sales_class_candidates = [
            "SalesManagementPage",
            "SalesPage",
            "SalesManagement",
        ]

        SalesCls = load_page_class(sales_module_candidates, sales_class_candidates)
        if SalesCls:
            try:
                self.sales_page = SalesCls(self.user)
            except TypeError:
                self.sales_page = SalesCls()
        else:
            self.sales_page = PlaceholderPage("Sales")

        self._add_page("Sales", self.sales_page)

        # -----------------------------
        # Reports page
        # Your actual structure:
        # ✅ desktop_app/ui/reports/reports_page.py
        # -----------------------------
        reports_module_candidates = [
            "desktop_app.ui.reports.reports_page",
            "desktop_app.ui.reports",
            # fallback patterns
            "desktop_app.ui.pages.reports.reports_page",
            "desktop_app.ui.pages.reports",
        ]
        reports_class_candidates = [
            "ReportsPage",
            "ReportPage",
            "Reports",
        ]

        ReportsCls = load_page_class(reports_module_candidates, reports_class_candidates)
        if ReportsCls:
            try:
                self.reports_page = ReportsCls(self.user)
            except TypeError:
                self.reports_page = ReportsCls()
        else:
            self.reports_page = PlaceholderPage("Reports")

        self._add_page("Reports", self.reports_page)

        # Default view
        self.navigate_to("Dashboard")

    def _add_page(self, label: str, widget: QWidget):
        self.pages_by_label[label] = widget
        self.stack.addWidget(widget)

    # =========================================================
    # WIRING
    # =========================================================
    def _wire_signals(self):
        self.sidebar.menu.currentRowChanged.connect(self._handle_sidebar_row_changed)

        self.header.toggle_sidebar.connect(self._toggle_sidebar)

        # This signal must exist in HeaderBar
        # (you said you replaced header_bar.py already)
        if hasattr(self.header, "view_profile_requested"):
            self.header.view_profile_requested.connect(
                lambda: self.navigate_to("Profile")
            )

    # =========================================================
    # NAVIGATION
    # =========================================================
    def _handle_sidebar_row_changed(self, row_index: int):
        item = self.sidebar.menu.item(row_index)
        if not item:
            return

        label = item.text()

        # Retailer safety rule
        if self.user.get("role", "").lower() == "retailer" and label == "Reports":
            self.navigate_to("Profile")
            return

        self.navigate_to(label)

    def navigate_to(self, label: str):
        widget = self.pages_by_label.get(label)
        if not widget:
            return

        self.stack.setCurrentWidget(widget)

        # Sync sidebar highlight
        for i in range(self.sidebar.menu.count()):
            it = self.sidebar.menu.item(i)
            if it and it.text() == label:
                if self.sidebar.menu.currentRow() != i:
                    self.sidebar.menu.setCurrentRow(i)
                break

    # =========================================================
    # SIDEBAR TOGGLE
    # =========================================================
    def _toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

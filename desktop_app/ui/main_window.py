# desktop_app/ui/main_window.py

from __future__ import annotations

import importlib
from typing import Dict, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

from desktop_app.ui.side_bar import SideBar

from desktop_app.ui.pages.dashboard import DashboardPage
from desktop_app.ui.pages.products.product_list import ProductListPage

# IMPORTANT:
# We intentionally import the "pages" profile, not the profile folder version
# to avoid duplicate profile implementations.
from desktop_app.ui.pages.profile import ProfilePage

# ✅ REAL ADMIN PAGE
from desktop_app.ui.pages.administration import AdministrationPage


# ---------------------------------------------------------
# Simple placeholder page for missing modules
# ---------------------------------------------------------
class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str = "This page is not implemented yet."):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(8)

        t = QLabel(title)
        t.setStyleSheet("font-size: 24px; font-weight: 800; background: transparent;")

        s = QLabel(subtitle)
        s.setStyleSheet("font-size: 12px; color: rgba(0,0,0,0.55); background: transparent;")

        layout.addWidget(t)
        layout.addWidget(s)
        layout.addStretch()


# ---------------------------------------------------------
# Safe dynamic import helpers
# ---------------------------------------------------------
def load_page_class(module_candidates: List[str], class_candidates: List[str]):
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
    - Sidebar (left)
    - Stack pages (right)

    Role-aware page loading to match your paper.
    """

    def __init__(self, user_data=None):
        super().__init__()
        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()

        self.setWindowTitle("StockaDoodle")
        self.setMinimumSize(1200, 720)

        self.pages_by_label: Dict[str, QWidget] = {}

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

        # Body row
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        # Sidebar
        self.sidebar = SideBar(self.user)
        body.addWidget(self.sidebar)

        # Right content wrapper
        right_wrap = QFrame()
        right_wrap.setObjectName("rightWrap")
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("mainStack")
        right_layout.addWidget(self.stack)

        body.addWidget(right_wrap, 1)

        # -----------------------------
        # Build pages based on role
        # -----------------------------
        allowed_labels = self._allowed_labels_for_role()

        # Dashboard
        self.dashboard_page = DashboardPage(self.user)
        self._add_page_if_allowed("Dashboard", self.dashboard_page, allowed_labels)

        # Inventory
        self.inventory_page = ProductListPage(self.user)
        self._add_page_if_allowed("Inventory", self.inventory_page, allowed_labels)

        # Sales (dynamic)
        self.sales_page = self._load_sales_page()
        self._add_page_if_allowed("Sales", self.sales_page, allowed_labels)

        # Reports (dynamic)
        self.reports_page = self._load_reports_page()
        self._add_page_if_allowed("Reports", self.reports_page, allowed_labels)

        # ✅ Administration (admin only) – REAL PAGE
        self.administration_page = AdministrationPage(self.user)
        self._add_page_if_allowed("Administration", self.administration_page, allowed_labels)

        # Alerts (manager only)
        self.alerts_page = self._load_alerts_page()
        self._add_page_if_allowed("Alerts", self.alerts_page, allowed_labels)

        # Activity (admin only)
        self.activity_page = self._load_activity_page()
        self._add_page_if_allowed("Activity", self.activity_page, allowed_labels)

        # Profile (always)
        self.profile_page = ProfilePage(self.user)
        self._add_page_if_allowed("Profile", self.profile_page, allowed_labels)

        # Default view
        self.navigate_to("Dashboard" if "Dashboard" in self.pages_by_label else "Profile")

        self.setStyleSheet("""
            QFrame#rightWrap {
                background: transparent;
            }
        """)

    def _allowed_labels_for_role(self) -> List[str]:
        if self.role == "admin":
            return [
                "Dashboard", "Inventory", "Sales", "Reports",
                "Administration", "Activity", "Profile",
            ]

        if self.role == "manager":
            return [
                "Dashboard", "Inventory", "Sales", "Alerts",
                "Reports", "Profile",
            ]

        return [
            "Dashboard", "Sales", "Inventory", "Profile",
        ]

    def _add_page_if_allowed(self, label: str, widget: QWidget, allowed_labels: List[str]):
        if label not in allowed_labels:
            return
        self.pages_by_label[label] = widget
        self.stack.addWidget(widget)

    # =========================================================
    # PAGE LOADERS
    # =========================================================
    def _load_sales_page(self) -> QWidget:
        sales_module_candidates = [
            "desktop_app.ui.sales.sales_management",
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
                return SalesCls(self.user)
            except TypeError:
                try:
                    return SalesCls(user_data=self.user)
                except Exception:
                    return PlaceholderPage("Sales")
            except Exception:
                return PlaceholderPage("Sales")
        return PlaceholderPage("Sales")

    def _load_reports_page(self) -> QWidget:
        reports_module_candidates = [
            "desktop_app.ui.reports.reports_page",
            "desktop_app.ui.reports",
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
                return ReportsCls(self.user)
            except TypeError:
                try:
                    return ReportsCls(user_data=self.user)
                except Exception:
                    return PlaceholderPage("Reports")
            except Exception:
                return PlaceholderPage("Reports")
        return PlaceholderPage("Reports")

    def _load_activity_page(self) -> QWidget:
        """
        Admin-only advanced activity page.

        IMPORTANT:
        - Only load the intended ActivityPage module to avoid signature mismatch.
        - Never instantiate without user data.
        """
        activity_module_candidates = [
            "desktop_app.ui.pages.activity",
        ]
        activity_class_candidates = [
            "ActivityPage",
        ]

        ActivityCls = load_page_class(activity_module_candidates, activity_class_candidates)
        if ActivityCls:
            try:
                return ActivityCls(user_data=self.user)
            except TypeError:
                try:
                    return ActivityCls(self.user)
                except Exception:
                    return PlaceholderPage("Activity")
            except Exception:
                return PlaceholderPage("Activity")

        return PlaceholderPage("Activity")

    def _load_alerts_page(self) -> QWidget:
        alerts_module_candidates = [
            "desktop_app.ui.pages.alerts",
            "desktop_app.ui.pages.alerts.alerts_page",
            "desktop_app.ui.alerts.alerts_page",
        ]
        alerts_class_candidates = [
            "AlertsPage",
            "AlertPage",
        ]

        AlertsCls = load_page_class(alerts_module_candidates, alerts_class_candidates)
        if AlertsCls:
            try:
                return AlertsCls(self.user)
            except TypeError:
                try:
                    return AlertsCls(user_data=self.user)
                except Exception:
                    return PlaceholderPage("Alerts")
            except Exception:
                return PlaceholderPage("Alerts")

        return PlaceholderPage(
            "Alerts",
            "Low Stock and Expiration alerts will be shown here."
        )

    # =========================================================
    # WIRING
    # =========================================================
    def _wire_signals(self):
        self.sidebar.menu.currentRowChanged.connect(self._handle_sidebar_row_changed)

        # Footer dropdown → profile
        if hasattr(self.sidebar, "profile_requested"):
            self.sidebar.profile_requested.connect(lambda: self.navigate_to("Profile"))

        # Footer dropdown → logout
        if hasattr(self.sidebar, "logout_requested"):
            self.sidebar.logout_requested.connect(self._handle_logout)

        # Dashboard "View More" → Activity (only if Activity exists)
        if hasattr(self, "dashboard_page") and hasattr(self.dashboard_page, "view_activity_requested"):
            if "Activity" in self.pages_by_label:
                self.dashboard_page.view_activity_requested.connect(
                    lambda: self.navigate_to("Activity")
                )

    # =========================================================
    # NAVIGATION
    # =========================================================
    def _handle_sidebar_row_changed(self, row_index: int):
        item = self.sidebar.menu.item(row_index)
        if not item:
            return

        label = item.text().strip()
        if not label:
            label = item.data(Qt.ItemDataRole.UserRole) or ""

        if not label:
            return

        if label not in self.pages_by_label:
            self.navigate_to("Profile" if "Profile" in self.pages_by_label else "Dashboard")
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
            if not it:
                continue

            raw_label = it.text().strip() or (it.data(Qt.ItemDataRole.UserRole) or "")
            if raw_label == label:
                if self.sidebar.menu.currentRow() != i:
                    self.sidebar.menu.setCurrentRow(i)
                break

    # =========================================================
    # LOGOUT HANDLER
    # =========================================================
    def _handle_logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

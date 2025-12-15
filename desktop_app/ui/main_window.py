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
from desktop_app.ui.pages.profile import ProfilePage
from desktop_app.ui.pages.administration import AdministrationPage
from desktop_app.ui.pages.alerts import AlertsPage


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
    POS vs Sales split:
    - "Point of Sale" = cart/checkout page (SalesManagementPage alias)
    - "Sales" = sales records/history (SalesRecordsPage)
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

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("appCentral")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        self.sidebar = SideBar(self.user)
        body.addWidget(self.sidebar)

        # Right side wrapper
        right_wrap = QFrame()
        right_wrap.setObjectName("rightWrap")
        right_wrap.setFrameShape(QFrame.Shape.NoFrame)

        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("mainStack")
        right_layout.addWidget(self.stack)

        body.addWidget(right_wrap, 1)

        allowed_labels = self._allowed_labels_for_role()

        # Dashboard
        self.dashboard_page = DashboardPage(self.user)
        self._add_page_if_allowed("Dashboard", self.dashboard_page, allowed_labels)

        # Inventory
        self.inventory_page = ProductListPage(self.user)
        self._add_page_if_allowed("Inventory", self.inventory_page, allowed_labels)

        # Point of Sale (POS)
        self.pos_page = self._load_pos_page()
        self._add_page_if_allowed("Point of Sale", self.pos_page, allowed_labels)

        # Sales Records
        self.sales_records_page = self._load_sales_records_page()
        self._add_page_if_allowed("Sales", self.sales_records_page, allowed_labels)

        # Reports
        self.reports_page = self._load_reports_page()
        self._add_page_if_allowed("Reports", self.reports_page, allowed_labels)

        # Administration (admin only)
        self.administration_page = AdministrationPage(self.user)
        self._add_page_if_allowed("Administration", self.administration_page, allowed_labels)

        # Alerts (admin + manager)
        self.alerts_page = AlertsPage(self.user)
        self._add_page_if_allowed("Alerts", self.alerts_page, allowed_labels)

        # Activity (admin only)
        self.activity_page = self._load_activity_page()
        self._add_page_if_allowed("Activity", self.activity_page, allowed_labels)

        # Profile (always)
        self.profile_page = ProfilePage(self.user)
        self._add_page_if_allowed("Profile", self.profile_page, allowed_labels)

        # Default page
        self.navigate_to("Dashboard" if "Dashboard" in self.pages_by_label else "Profile")

        # ✅ Design fix only:
        # Ensure right panel + stacked widget never shows default Qt gray.
        self.setStyleSheet("""
            QFrame#rightWrap {
                background: transparent;
                border: none;
            }
            QStackedWidget#mainStack {
                background: transparent;
                border: none;
            }
        """)

    def _allowed_labels_for_role(self) -> List[str]:
        if self.role == "admin":
            return [
                "Dashboard", "Inventory", "Point of Sale", "Sales",
                "Reports", "Alerts", "Administration", "Activity", "Profile",
            ]

        if self.role == "manager":
            return [
                "Dashboard", "Inventory", "Point of Sale", "Sales",
                "Alerts", "Reports", "Profile",
            ]

        # Retailer: POS only
        return [
            "Dashboard", "Inventory", "Point of Sale", "Profile",
        ]

    def _add_page_if_allowed(self, label: str, widget: QWidget, allowed_labels: List[str]):
        if label not in allowed_labels:
            return
        self.pages_by_label[label] = widget
        self.stack.addWidget(widget)

    # -------------------------
    # Loaders
    # -------------------------
    def _load_pos_page(self) -> QWidget:
        module_candidates = [
            "desktop_app.ui.sales.sales_management",
        ]
        class_candidates = [
            "SalesManagementPage",
        ]

        Cls = load_page_class(module_candidates, class_candidates)
        if Cls:
            try:
                return Cls(self.user)
            except TypeError:
                try:
                    return Cls(user_data=self.user)
                except Exception:
                    return PlaceholderPage("Point of Sale")
            except Exception:
                return PlaceholderPage("Point of Sale")

        return PlaceholderPage("Point of Sale")

    def _load_sales_records_page(self) -> QWidget:
        module_candidates = [
            "desktop_app.ui.sales.sales_records",
        ]
        class_candidates = [
            "SalesRecordsPage",
        ]

        Cls = load_page_class(module_candidates, class_candidates)
        if Cls:
            try:
                return Cls(self.user)
            except TypeError:
                try:
                    return Cls(user_data=self.user)
                except Exception:
                    return PlaceholderPage("Sales")
            except Exception:
                return PlaceholderPage("Sales")

        return PlaceholderPage("Sales", "Missing SalesRecordsPage in sales_records.py")

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

    # -------------------------
    # Wiring + navigation
    # -------------------------
    def _wire_signals(self):
        self.sidebar.menu.currentRowChanged.connect(self._handle_sidebar_row_changed)

        if hasattr(self.sidebar, "profile_requested"):
            self.sidebar.profile_requested.connect(lambda: self.navigate_to("Profile"))

        if hasattr(self.sidebar, "logout_requested"):
            self.sidebar.logout_requested.connect(self._handle_logout)

        if hasattr(self, "dashboard_page") and hasattr(self.dashboard_page, "view_activity_requested"):
            if "Activity" in self.pages_by_label:
                self.dashboard_page.view_activity_requested.connect(
                    lambda: self.navigate_to("Activity")
                )

        # ✅ If ProfilePage emits user updates (new photo/name),
        # refresh sidebar footer avatar + update local user dict.
        if hasattr(self, "profile_page") and hasattr(self.profile_page, "user_updated"):
            try:
                self.profile_page.user_updated.connect(self._on_user_updated)
            except Exception:
                pass

    def _on_user_updated(self, patch: dict):
        """
        patch can be partial like {"profile_image_path": "C:/.../avatar.png"}.
        """
        if isinstance(patch, dict):
            self.user.update(patch)

        # refresh sidebar footer
        if hasattr(self, "sidebar") and hasattr(self.sidebar, "update_user"):
            try:
                self.sidebar.update_user(self.user)
            except Exception:
                pass

        # optional sync for pages that keep a reference
        try:
            if hasattr(self, "dashboard_page"):
                self.dashboard_page.user = self.user
            if hasattr(self, "inventory_page"):
                self.inventory_page.user = self.user
        except Exception:
            pass

    def _handle_sidebar_row_changed(self, row_index: int):
        item = self.sidebar.menu.item(row_index)
        if not item:
            return

        label = (item.text() or "").strip()
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

            raw_label = (it.text() or "").strip() or (it.data(Qt.ItemDataRole.UserRole) or "")
            if raw_label == label:
                if self.sidebar.menu.currentRow() != i:
                    self.sidebar.menu.setCurrentRow(i)
                break

    def _handle_logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

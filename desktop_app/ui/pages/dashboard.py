# desktop_app/ui/pages/dashboard.py

from __future__ import annotations

import traceback
from datetime import date
from typing import Any, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QHeaderView

from desktop_app.utils.api_wrapper import get_api


# ====================================
# Reusable shadows
# ====================================
def apply_card_shadow(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(22)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 90))
    widget.setGraphicsEffect(shadow)


# ====================================
# KPI Card Component
# ====================================
class DashboardCard(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("DashboardCard")

        self.setFixedHeight(135)
        self.setStyleSheet("""
            QFrame#DashboardCard {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #DDE3EA;
            }
        """)

        apply_card_shadow(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(20, 16, 20, 16)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #4A5568;
            background: transparent;
        """)

        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet("""
            font-size: 28px;
            font-weight: 800;
            color: #1E3A8A;
            background: transparent;
        """)

        layout.addWidget(self.title_lbl)
        layout.addSpacing(8)
        layout.addWidget(self.value_lbl)
        layout.addStretch()

    def set_value(self, text):
        self.value_lbl.setText(str(text))


# ====================================
# Recent Activity Preview (Dashboard)
# ====================================
class RecentActivityPreview(QFrame):
    """
    Dashboard-only compact preview of activity logs.

    Requirements:
    - Show only the MOST RECENT top 10 logs
    - 2 pages max:
        Page 1: 5 rows
        Page 2: 5 rows
    - No more pages allowed
    - 'View More' will open full Activity tab
    """
    view_more_clicked = pyqtSignal()

    PAGE_SIZE = 5
    MAX_LOGS = 10

    def __init__(self, user: Dict[str, Any], api):
        super().__init__()
        self.user = user or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = api

        self._all_logs: List[Dict[str, Any]] = []
        self.current_page = 1
        self.total_pages = 2  # fixed

        self._build_ui()

    def _build_ui(self):
        self.setObjectName("activityFrame")
        self.setMinimumHeight(380)
        self.setStyleSheet("""
            #activityFrame {
                background: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #DDE3EA;
            }
        """)
        apply_card_shadow(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(12)

        # Header row
        header_row = QHBoxLayout()
        lbl_recent = QLabel("Recent Activity")
        lbl_recent.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            background: transparent;
        """)
        header_row.addWidget(lbl_recent)
        header_row.addStretch()

        self.btn_view_more = QPushButton("View More")
        self.btn_view_more.setObjectName("secondaryBtn")
        self.btn_view_more.setFixedHeight(30)
        self.btn_view_more.clicked.connect(self.view_more_clicked.emit)
        header_row.addWidget(self.btn_view_more)

        root.addLayout(header_row)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["User", "Action", "Timestamp"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Cleaner sizing
        try:
            hh = self.table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        except Exception:
            pass

        # ✅ Make rows visually fill space cleanly
        try:
            vh = self.table.verticalHeader()
            vh.setVisible(False)
            vh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

        root.addWidget(self.table, 1)

        # Pagination bar
        pag_row = QHBoxLayout()
        pag_row.setSpacing(6)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(self._prev_page)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(self._next_page)

        self.page_label = QLabel("Page 1 / 2")
        self.page_label.setStyleSheet("color: rgba(0,0,0,0.55);")

        pag_row.addWidget(self.btn_prev)
        pag_row.addWidget(self.btn_next)
        pag_row.addSpacing(10)
        pag_row.addWidget(self.page_label)
        pag_row.addStretch()

        root.addLayout(pag_row)

    # ----------------------------
    # Data
    # ----------------------------
    def refresh(self):
        self.current_page = 1
        self._all_logs = self._fetch_top_10()
        self._render_page()

    def _fetch_top_10(self) -> List[Dict[str, Any]]:
        logs: List[Dict[str, Any]] = []

        try:
            # Admin: prefer global API logs
            if self.role == "admin":
                res = self.api.get_api_logs(limit=self.MAX_LOGS)
                if isinstance(res, dict):
                    logs = res.get("logs", []) or []
                elif isinstance(res, list):
                    logs = res

            # Fallback to per-user logs
            if not logs:
                uid = self.user.get("id", 0) or 0
                res = self.api.get_user_logs(uid, limit=self.MAX_LOGS)
                if isinstance(res, dict):
                    logs = res.get("logs", []) or []
                elif isinstance(res, list):
                    logs = res

        except Exception:
            logs = []

        # Normalize for UI
        normalized: List[Dict[str, Any]] = []
        for log in (logs or [])[: self.MAX_LOGS]:
            method = str(log.get("method") or log.get("action") or "").upper()
            target = (
                log.get("target")
                or log.get("target_entity")
                or log.get("entity")
                or ""
            )
            details = log.get("details") or log.get("notes") or log.get("message") or ""
            user_name = log.get("user_name") or log.get("username") or log.get("user") or "System"
            ts = str(log.get("timestamp") or log.get("log_time") or "")

            if method and target:
                action_txt = f"{method} {target}"
            else:
                action_txt = str(log.get("action") or log.get("message") or "Activity")

            if details:
                d = str(details).strip()
                if len(d) > 80:
                    d = d[:77] + "..."
                action_txt = f"{action_txt} — {d}"

            normalized.append({
                "user": user_name,
                "action": action_txt,
                "timestamp": ts
            })

        return normalized

    # ----------------------------
    # Rendering
    # ----------------------------
    def _render_page(self):
        logs = self._all_logs or []
        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_logs = logs[start:end]

        # ✅ fixed row count, then fill
        self.table.setRowCount(self.PAGE_SIZE)

        for i in range(self.PAGE_SIZE):
            if i < len(page_logs):
                row = page_logs[i]
                self.table.setItem(i, 0, QTableWidgetItem(str(row.get("user", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(str(row.get("action", ""))))
                self.table.setItem(i, 2, QTableWidgetItem(str(row.get("timestamp", ""))))
                for c in range(3):
                    it = self.table.item(i, c)
                    if it:
                        it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                for c in range(3):
                    blank = QTableWidgetItem("")
                    blank.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.table.setItem(i, c, blank)

        try:
            self.table.resizeColumnsToContents()
        except Exception:
            pass

        self.page_label.setText(f"Page {self.current_page} / 2")
        self.btn_prev.setDisabled(self.current_page <= 1)
        has_page2 = len(self._all_logs) > self.PAGE_SIZE
        self.btn_next.setDisabled(self.current_page >= 2 or not has_page2)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def _next_page(self):
        if self.current_page < 2 and len(self._all_logs) > self.PAGE_SIZE:
            self.current_page += 1
            self._render_page()


# ====================================
# MAIN DASHBOARD PAGE
# ====================================
class DashboardPage(QWidget):
    """
    Emits view_activity_requested when the user clicks 'View More'
    in the Recent Activity panel.
    """
    view_activity_requested = pyqtSignal()

    def __init__(self, user_data=None):
        super().__init__()
        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = get_api()

        self._build_ui()
        self.refresh_dashboard_data()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_dashboard_data)
        self.timer.start(20000)

    # ========================================================================
    # UI BUILDING
    # ========================================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(32)
        root.setContentsMargins(32, 32, 32, 32)

        user_name = self.user.get("full_name", "User")
        title = QLabel(f"Dashboard – Welcome, {user_name}")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #0A0A0A;
            background: transparent;
        """)
        root.addWidget(title)

        # KPI GRID
        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(22)
        kpi_grid.setVerticalSpacing(18)

        self.card_inventory_value = DashboardCard("Total Inventory Value")
        self.card_low_stock = DashboardCard("Low Stock Alerts")
        self.card_recent_sales = DashboardCard("Recent Sales Today")
        self.card_active_users = DashboardCard("Users Registered")

        kpi_grid.addWidget(self.card_inventory_value, 0, 0)
        kpi_grid.addWidget(self.card_low_stock, 0, 1)
        kpi_grid.addWidget(self.card_recent_sales, 0, 2)
        kpi_grid.addWidget(self.card_active_users, 0, 3)

        root.addLayout(kpi_grid)

        # Recent Activity Preview
        self.activity_preview = RecentActivityPreview(self.user, self.api)
        self.activity_preview.view_more_clicked.connect(self.view_activity_requested.emit)
        root.addWidget(self.activity_preview)

    # ========================================================================
    # Helpers
    # ========================================================================
    def _safe_num(self, x):
        try:
            return float(x or 0)
        except Exception:
            return 0

    # ========================================================================
    # DATA REFRESH
    # ========================================================================
    def refresh_dashboard_data(self):
        try:
            # -----------------------------------------------------
            # KPI 1 – INVENTORY VALUE
            # -----------------------------------------------------
            products_data = self.api.get_products(per_page=9999)
            prods = products_data.get("products", []) or []

            total_value = 0
            for p in prods:
                price = self._safe_num(p.get("price"))
                stock = self._safe_num(p.get("stock_level"))
                total_value += price * stock

            self.card_inventory_value.set_value(f"₱{int(total_value):,}")

            # -----------------------------------------------------
            # KPI 2 – LOW STOCK ITEMS
            # -----------------------------------------------------
            low_stock_items = [
                p for p in prods
                if self._safe_num(p.get("stock_level")) <= self._safe_num(p.get("min_stock_level", 1))
            ]
            self.card_low_stock.set_value(len(low_stock_items))

            # -----------------------------------------------------
            # KPI 3 – TODAY SALES TOTAL
            # -----------------------------------------------------
            today = date.today().isoformat()
            sales_data = self.api.get_sales(start_date=today, end_date=today)

            total_today = 0
            for s in sales_data.get("sales", []) or []:
                total_today += self._safe_num(s.get("total_amount"))

            self.card_recent_sales.set_value(f"₱{int(total_today):,}")

            # -----------------------------------------------------
            # KPI 4 – USER COUNT
            # -----------------------------------------------------
            users_data = self.api.get_users()
            users_list = users_data if isinstance(users_data, list) else (users_data.get("users", []) or [])
            self.card_active_users.set_value(len(users_list))

            # -----------------------------------------------------
            # Recent Activity Preview (top 10 only)
            # -----------------------------------------------------
            self.activity_preview.refresh()

        except Exception:
            print("\n>>> DASHBOARD FETCH ERROR <<<")
            traceback.print_exc()

# desktop_app/ui/pages/dashboard.py

import traceback
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QListWidget,
    QGridLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor

from desktop_app.api_client.stockadoodle_api import StockaDoodleAPI


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
                background: white;
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
        """)

        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet("""
            font-size: 28px;
            font-weight: 800;
            color: #1E3A8A;
        """)

        layout.addWidget(self.title_lbl)
        layout.addSpacing(8)
        layout.addWidget(self.value_lbl)
        layout.addStretch()

    def set_value(self, text):
        self.value_lbl.setText(str(text))


# ====================================
# MAIN DASHBOARD PAGE
# ====================================
class DashboardPage(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self.user = user_data or {}
        self.api = StockaDoodleAPI()

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

        user_name = self.user.get('full_name', 'User')
        title = QLabel(f"Dashboard – Welcome, {user_name}")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #0A0A0A;
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

        # =====================================
        # Recent Activity Panel
        # =====================================
        activity_frame = QFrame()
        activity_frame.setObjectName("activityFrame")
        activity_frame.setMinimumHeight(380)
        activity_frame.setStyleSheet("""
            #activityFrame {
                background: white;
                border-radius: 20px;
                border: 1px solid #DDE3EA;
            }
        """)

        apply_card_shadow(activity_frame)

        af_layout = QVBoxLayout(activity_frame)
        af_layout.setContentsMargins(24, 22, 24, 22)

        lbl_recent = QLabel("Recent Activity")
        lbl_recent.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
        """)

        af_layout.addWidget(lbl_recent)

        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget::item {
                padding: 12px 6px;
                border-bottom: 1px solid #E9EEF6;
                font-size: 14px;
            }
        """)

        af_layout.addWidget(self.activity_list)
        root.addWidget(activity_frame)

    # ========================================================================
    # DATA REFRESH
    # ========================================================================
    def refresh_dashboard_data(self):
        try:
            # -----------------------------------------------------
            # KPI 1 – INVENTORY VALUE
            # -----------------------------------------------------
            products_data = self.api.get_products(per_page=9999)
            prods = products_data.get("products", [])

            def safe_num(x):
                try:
                    return float(x or 0)
                except Exception:
                    return 0

            total_value = 0
            for p in prods:
                price = safe_num(p.get("price"))
                stock = safe_num(p.get("stock_level"))
                total_value += price * stock

            self.card_inventory_value.set_value(f"₱{int(total_value):,}")

            # -----------------------------------------------------
            # KPI 2 – LOW STOCK ITEMS
            # -----------------------------------------------------
            low_stock_items = [
                p for p in prods
                if safe_num(p.get("stock_level")) <= safe_num(p.get("min_stock_level", 1))
            ]
            self.card_low_stock.set_value(len(low_stock_items))

            # -----------------------------------------------------
            # KPI 3 – TODAY SALES TOTAL (FIXED)
            # -----------------------------------------------------
            today = date.today().isoformat()
            sales_data = self.api.get_sales(start_date=today, end_date=today)

            total_today = 0
            for s in sales_data.get("sales", []):
                total_today += safe_num(s.get("total_amount"))

            self.card_recent_sales.set_value(f"₱{int(total_today):,}")

            # -----------------------------------------------------
            # KPI 4 – USER COUNT
            # -----------------------------------------------------
            users = self.api.get_users()
            self.card_active_users.set_value(len(users))

            # -----------------------------------------------------
            # ACTIVITY SECTION (role-aware)
            # -----------------------------------------------------
            self.activity_list.clear()

            try:
                logs = self.api.get_user_logs(
                    self.user.get("id", 0),
                    limit=10
                ).get("logs", [])

                if logs:
                    for log in logs:
                        msg = log.get("message") or log.get("action") or "User activity"
                        timestamp = log.get("timestamp", "")
                        self.activity_list.addItem(f"{msg} • {timestamp}")
                else:
                    self.activity_list.addItem("No recent activity yet.")

            except Exception:
                self.activity_list.addItem("Activity log access unavailable.")

        except Exception:
            print("\n>>> DASHBOARD FETCH ERROR <<<")
            traceback.print_exc()

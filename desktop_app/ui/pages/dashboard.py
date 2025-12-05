# desktop_app/ui/pages/dashboard.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QListWidget, QListWidgetItem,
    QSizePolicy
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from utils.helpers import get_feather_icon


class KPICard(QFrame):
    def __init__(self, title: str, value: str, icon_name: str | None = None):
        super().__init__()
        self.setObjectName("KPI")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(14)

        # ICON
        icon_frame = QFrame()
        icon_frame.setObjectName("IconBubble")
        icon_frame.setFixedSize(46, 46)

        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if icon_name:
            icon: QIcon = get_feather_icon(icon_name, 28)
            if icon and not icon.isNull():
                icon_label.setPixmap(icon.pixmap(28, 28))

        icon_layout.addWidget(icon_label)
        main_layout.addWidget(icon_frame)

        # TEXT
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("kpiTitle")

        lbl_value = QLabel(value)
        lbl_value.setObjectName("kpiValue")

        text_col.addWidget(lbl_title)
        text_col.addWidget(lbl_value)

        main_layout.addLayout(text_col)
        main_layout.addStretch()


class DashboardPage(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self.user = user_data or {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(22)

        # Greeting
        user_name = self.user.get("full_name", "User")
        title = QLabel(f"Welcome back, {user_name}")
        title.setProperty("class", "pageTitle")
        root.addWidget(title)

        # KPI ROW
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(18)

        kpi_row.addWidget(KPICard("Total Inventory Value", "₱2,847,650", "dollar-sign"))
        kpi_row.addWidget(KPICard("Low Stock Alerts", "12", "alert-triangle"))
        kpi_row.addWidget(KPICard("Recent Sales Volume", "₱156,780", "trending-up"))
        kpi_row.addWidget(KPICard("Active User Sessions", "24", "users"))

        container = QWidget()
        container.setLayout(kpi_row)
        root.addWidget(container)

        # ACTIVITY
        activity_frame = QFrame()
        activity_frame.setObjectName("activityBox")

        layout = QVBoxLayout(activity_frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        lbl = QLabel("Recent Activity")
        lbl.setObjectName("activityTitle")
        layout.addWidget(lbl)

        self.list = QListWidget()
        self.list.setObjectName("activityList")

        entries = [
            "Retailer John updated Coca-Cola stock (2m ago)",
            "Admin created user — michael (10m ago)",
            "Pepsi batch expired (17m ago)",
            "Retail sale recorded — Transaction #4451 (25m ago)",
            "Notification pushed to staff",
            "Stock replenished — Coke Zero (30m ago)",
            "Low stock alert — Sprite 330ml",
            "User logged in — retail_user05",
        ]

        for e in entries:
            self.list.addItem(QListWidgetItem(e))

        layout.addWidget(self.list)
        root.addWidget(activity_frame, 1)

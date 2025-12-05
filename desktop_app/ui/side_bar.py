# desktop_app/ui/side_bar.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QSizePolicy, QSpacerItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from utils.helpers import get_feather_icon


class SideBar(QWidget):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user or {}

        self.setObjectName("sideBar")
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 6)
        layout.setSpacing(12)

        # ---- BRAND ----
        brand = QLabel("StockaDoodle")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        # ---- MENU ----
        self.menu = QListWidget()
        self.menu.setObjectName("sidebarMenu")
        self.menu.setSpacing(2)

        # menu configuration
        items = [
            ("Dashboard", "home"),
            ("Inventory", "archive"),
            ("Sales", "shopping-cart"),
            ("Reports", "bar-chart-2"),
            ("Profile", "user"),
        ]

        for text, icon_name in items:
            item = QListWidgetItem(text)

            icon: QIcon = get_feather_icon(icon_name, 20)
            if icon and not icon.isNull():
                item.setIcon(icon)

            self.menu.addItem(item)

        self.menu.setCurrentRow(0)

        layout.addWidget(self.menu)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # ---- USER FOOTER ----
        user_footer = QLabel(f"{self.user.get('full_name', 'User')}\n{self.user.get('role', '')}")
        user_footer.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        layout.addWidget(user_footer)

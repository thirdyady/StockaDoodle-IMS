# desktop_app/ui/side_bar.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QVBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QSize
from desktop_app.utils.helpers import get_feather_icon


class SideBar(QWidget):

    def __init__(self, user=None):
        super().__init__()

        self.user = user or {}
        self.role = self.user.get("role", "").lower()

        self.setObjectName("sidebar")
        self.setFixedWidth(240)

        self._apply_style()
        self._build_ui()

    # =========================================================
    # UI BUILD
    # =========================================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        # BRANDING
        brand = QLabel("StockaDoodle")
        brand.setStyleSheet("""
            font-size: 21px;
            font-weight: 800;
            color: #0A2A83;
        """)
        layout.addWidget(brand)

        # MENU LIST
        self.menu = QListWidget()
        self.menu.setObjectName("sidebarMenu")
        self.menu.setSpacing(6)

        # ALWAYS keep the same order to protect page indices
        menu_items = [
            ("Dashboard", "home"),
            ("Inventory", "archive"),
            ("Sales", "shopping-cart"),
            ("Reports", "bar-chart-2"),
            ("Profile", "user")
        ]

        self._items = {}

        for label, icon_name in menu_items:
            item = QListWidgetItem(label)
            item.setIcon(get_feather_icon(icon_name, 19))
            item.setSizeHint(QSize(200, 46))
            self.menu.addItem(item)
            self._items[label.lower()] = item

        # Retailer restriction: disable Reports (but keep row index)
        if self.role == "retailer":
            reports_item = self._items.get("reports")
            if reports_item:
                reports_item.setFlags(reports_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                # Optional subtle hint without changing label too much:
                reports_item.setToolTip("Reports access is restricted for retailer accounts.")

        self.menu.setCurrentRow(0)
        layout.addWidget(self.menu)

        layout.addStretch()

        # =========================================================
        # PROFILE FOOTER CARD
        # =========================================================
        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        footer.setFixedHeight(75)
        footer.setStyleSheet("""
            #sidebarFooter {
                background: #F4F7FF;
                border-radius: 12px;
                border: 1px solid #DFE6FF;
            }
        """)

        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(10, 10, 10, 10)

        full_name = QLabel(self.user.get("full_name", "User"))
        full_name.setStyleSheet("font-weight: 700; color: #1A1A1A; font-size: 14px;")

        role_lbl = QLabel(self.user.get("role", "-").capitalize())
        role_lbl.setStyleSheet("font-size: 12px; color: rgba(0,0,0,0.57);")

        f_layout.addWidget(full_name)
        f_layout.addWidget(role_lbl)

        layout.addWidget(footer)

    # =========================================================
    # STYLING
    # =========================================================
    def _apply_style(self):
        self.setStyleSheet("""
            QWidget#sidebar {
                background: #FFFFFF;
                border-right: 1px solid #E2E6EE;
            }

            QListWidget#sidebarMenu {
                border: none;
                outline: none;
                background: transparent;
            }

            QListWidget#sidebarMenu::item {
                margin-left: 4px;
                padding-left: 14px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 500;
                height: 42px;
                color: #24324F;
            }

            QListWidget#sidebarMenu::item:hover {
                background: #EEF3FF;
            }

            QListWidget#sidebarMenu::item:selected {
                background: #CAD8FF;
                border: 1px solid #9DB8FF;
                color: #0A2A83;
            }

            /* Disabled item styling (Reports for retailer) */
            QListWidget#sidebarMenu::item:disabled {
                color: rgba(36, 50, 79, 0.35);
                background: transparent;
            }
        """)

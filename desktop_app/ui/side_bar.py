# desktop_app/ui/side_bar.py

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QHBoxLayout, QToolButton, QSizePolicy, QMenu
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon

from desktop_app.utils.helpers import get_feather_icon


class SideBar(QWidget):
    """
    Modern collapsible sidebar with role-aware menus.

    Roles per your paper:
    - admin: Dashboard, Inventory, Sales, Reports, Administration, Activity, Profile
    - manager: Dashboard, Inventory, Sales, Alerts, Reports, Profile
    - retailer: Dashboard, Sales, Inventory (view-only), Profile

    Notes:
    - Access enforcement for view-only/edit-only should be handled in pages,
      not just the sidebar.
    """

    profile_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    EXPANDED_WIDTH = 260
    COLLAPSED_WIDTH = 84

    ICON_TINT = "#0A2A83"

    def __init__(self, user=None):
        super().__init__()

        self.user = user or {}
        self.role = (self.user.get("role") or "").lower()

        self.setObjectName("sidebar")

        # IMPORTANT for full-height feel
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._collapsed = False
        self._items: Dict[str, QListWidgetItem] = {}
        self._label_widgets = []

        self._footer_frame = None
        self._footer_name = None
        self._footer_role = None
        self._btn_footer_menu = None

        self._build_ui()
        self._apply_style()
        self.set_collapsed(False)

    # =========================================================
    # UI BUILD
    # =========================================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        # -----------------------------------------------------
        # Brand block with logo toggle
        # -----------------------------------------------------
        brand_card = QFrame()
        brand_card.setObjectName("sidebarBrandCard")
        brand_layout = QHBoxLayout(brand_card)
        brand_layout.setContentsMargins(12, 12, 12, 12)
        brand_layout.setSpacing(10)

        # Toggle button (logo)
        self.btn_toggle = QToolButton()
        self.btn_toggle.setObjectName("sidebarBurger")
        self.btn_toggle.setFixedSize(32, 32)
        self.btn_toggle.setIconSize(QSize(20, 20))
        self._set_toggle_logo_icon()
        self.btn_toggle.clicked.connect(self.toggle_collapsed)
        brand_layout.addWidget(self.btn_toggle)

        brand_text_wrap = QWidget()
        brand_text_col = QVBoxLayout(brand_text_wrap)
        brand_text_col.setContentsMargins(0, 0, 0, 0)
        brand_text_col.setSpacing(2)

        brand = QLabel("StockaDoodle")
        brand.setObjectName("sidebarBrand")

        subtitle = QLabel("Inventory Management")
        subtitle.setObjectName("sidebarBrandSub")

        brand_text_col.addWidget(brand)
        brand_text_col.addWidget(subtitle)

        self._label_widgets.extend([brand, subtitle])

        brand_layout.addWidget(brand_text_wrap, 1)

        layout.addWidget(brand_card)

        # -----------------------------------------------------
        # Section label
        # -----------------------------------------------------
        section = QLabel("MAIN")
        section.setObjectName("sidebarSection")
        self._label_widgets.append(section)
        layout.addWidget(section)

        # -----------------------------------------------------
        # Menu list
        # -----------------------------------------------------
        self.menu = QListWidget()
        self.menu.setObjectName("sidebarMenu")
        self.menu.setSpacing(6)

        # Remove unnecessary scrollbars
        self.menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Ensure full use of vertical space
        self.menu.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        menu_items = self._resolve_menu_items()
        self._items = {}

        for label, icon_name in menu_items:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, label)

            icon = get_feather_icon(icon_name, 18, color=self.ICON_TINT)
            if isinstance(icon, QIcon) and not icon.isNull():
                item.setIcon(icon)

            item.setSizeHint(QSize(220, 44))
            self.menu.addItem(item)
            self._items[label.lower()] = item

        self.menu.setCurrentRow(0)
        layout.addWidget(self.menu, 1)

        layout.addStretch(0)

        # -----------------------------------------------------
        # Footer user card + dropdown
        # -----------------------------------------------------
        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        self._footer_frame = footer

        footer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(12, 12, 12, 12)
        f_layout.setSpacing(10)

        initials = self._derive_initials(self.user.get("full_name", "User"))
        bubble = QLabel(initials)
        bubble.setObjectName("sidebarAvatar")
        bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble.setFixedSize(36, 36)

        # Middle: name + role
        text_col_wrap = QWidget()
        text_col = QVBoxLayout(text_col_wrap)
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(0)

        full_name = QLabel(self.user.get("full_name", "User"))
        full_name.setObjectName("sidebarName")

        role_lbl = QLabel((self.user.get("role") or "-").capitalize())
        role_lbl.setObjectName("sidebarRole")

        self._footer_name = full_name
        self._footer_role = role_lbl

        self._label_widgets.extend([full_name, role_lbl])

        text_col.addWidget(full_name)
        text_col.addWidget(role_lbl)

        # Right: dropdown button
        btn_menu = QToolButton()
        btn_menu.setObjectName("sidebarFooterMenuBtn")
        btn_menu.setFixedSize(28, 28)
        btn_menu.setIconSize(QSize(14, 14))

        chevron = get_feather_icon("chevron-up", 14, color=self.ICON_TINT)
        if not chevron.isNull():
            btn_menu.setIcon(chevron)

        btn_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        menu = QMenu(btn_menu)
        act_profile = menu.addAction("View Profile")
        act_logout = menu.addAction("Logout")

        act_profile.triggered.connect(lambda: self.profile_requested.emit())
        act_logout.triggered.connect(lambda: self.logout_requested.emit())

        btn_menu.setMenu(menu)
        self._btn_footer_menu = btn_menu

        f_layout.addWidget(bubble)
        f_layout.addWidget(text_col_wrap, 1)
        f_layout.addWidget(btn_menu)

        layout.addWidget(footer)

        # Optional: clicking the footer body also opens profile
        footer.mousePressEvent = self._on_footer_clicked  # type: ignore

    def _set_toggle_logo_icon(self):
        """
        Use stockadoodle logo files from:
        desktop_app/assets/icons/
        """
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        icons_dir = os.path.join(base, "assets", "icons")

        logo_png = os.path.join(icons_dir, "stockadoodle-transparent.png")
        logo_ico = os.path.join(icons_dir, "stockadoodle.ico")

        if os.path.exists(logo_png):
            self.btn_toggle.setIcon(QIcon(logo_png))
            return
        if os.path.exists(logo_ico):
            self.btn_toggle.setIcon(QIcon(logo_ico))
            return

        # fallback if missing
        icon = get_feather_icon("menu", 18, color=self.ICON_TINT)
        if not icon.isNull():
            self.btn_toggle.setIcon(icon)

    def _resolve_menu_items(self) -> List[Tuple[str, str]]:
        # Admin menu
        if self.role == "admin":
            return [
                ("Dashboard", "home"),
                ("Inventory", "archive"),
                ("Sales", "shopping-cart"),
                ("Reports", "bar-chart-2"),
                ("Administration", "settings"),
                ("Activity", "activity"),
                ("Profile", "user"),
            ]

        # Manager menu
        if self.role == "manager":
            return [
                ("Dashboard", "home"),
                ("Inventory", "archive"),
                ("Sales", "shopping-cart"),
                ("Alerts", "alert-triangle"),
                ("Reports", "bar-chart-2"),
                ("Profile", "user"),
            ]

        # Retailer menu
        return [
            ("Dashboard", "home"),
            ("Sales", "shopping-cart"),
            ("Inventory", "archive"),
            ("Profile", "user"),
        ]

    # =========================================================
    # COLLAPSE LOGIC
    # =========================================================
    def toggle_collapsed(self):
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, value: bool):
        self._collapsed = bool(value)

        self.setFixedWidth(self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH)

        # Hide/show text labels in brand/section/footer
        for w in self._label_widgets:
            if w is not None:
                w.setVisible(not self._collapsed)

        # Menu labels -> icons only
        for i in range(self.menu.count()):
            it = self.menu.item(i)
            if not it:
                continue
            label = it.data(Qt.ItemDataRole.UserRole) or ""
            it.setText("" if self._collapsed else label)

        # Adjust item size hint for collapsed state
        base_h = 44
        for i in range(self.menu.count()):
            it = self.menu.item(i)
            if not it:
                continue
            it.setSizeHint(QSize(52 if self._collapsed else 220, base_h))

        # Hide footer dropdown button text-only mode cleanliness
        if self._btn_footer_menu:
            self._btn_footer_menu.setVisible(not self._collapsed)

        if self._footer_frame:
            self._footer_frame.setToolTip("Profile")

    def is_collapsed(self) -> bool:
        return self._collapsed

    # =========================================================
    # FOOTER CLICK
    # =========================================================
    def _on_footer_clicked(self, event):
        self.profile_requested.emit()
        event.accept()

    # =========================================================
    # STYLING
    # =========================================================
    def _apply_style(self):
        self.setStyleSheet("""
            QWidget#sidebar {
                background: #FFFFFF;
                border-right: 1px solid #E6EAF3;
            }

            /* Brand card */
            QFrame#sidebarBrandCard {
                background: #F6F8FF;
                border: 1px solid #E3E9FF;
                border-radius: 14px;
            }

            QToolButton#sidebarBurger {
                background: #FFFFFF;
                border: 1px solid #DDE5FF;
                border-radius: 8px;
            }
            QToolButton#sidebarBurger:hover {
                background: #EEF3FF;
            }

            QLabel#sidebarBrand {
                font-size: 20px;
                font-weight: 900;
                color: #0A2A83;
                background: transparent;
            }

            QLabel#sidebarBrandSub {
                font-size: 11px;
                font-weight: 600;
                color: rgba(10, 42, 131, 0.65);
                background: transparent;
            }

            QLabel#sidebarSection {
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
                color: rgba(15, 23, 42, 0.45);
                margin-left: 6px;
                background: transparent;
            }

            /* Menu container */
            QListWidget#sidebarMenu {
                border: none;
                outline: none;
                background: transparent;
            }

            /* Menu items */
            QListWidget#sidebarMenu::item {
                margin-left: 2px;
                padding-left: 12px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                height: 40px;
                color: #23324D;
                background: transparent;
            }

            QListWidget#sidebarMenu::item:hover {
                background: #EEF3FF;
            }

            QListWidget#sidebarMenu::item:selected {
                background: #0A2A83;
                color: #FFFFFF;
            }

            QListWidget#sidebarMenu::item:disabled {
                color: rgba(35, 50, 77, 0.28);
                background: transparent;
            }

            /* Footer */
            QFrame#sidebarFooter {
                background: #F8FAFF;
                border: 1px solid #E5EBFF;
                border-radius: 14px;
                min-height: 72px;
            }

            QLabel#sidebarAvatar {
                background: #0A2A83;
                color: white;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 800;
            }

            QLabel#sidebarName {
                font-size: 13px;
                font-weight: 800;
                color: #0F172A;
                background: transparent;
            }

            QLabel#sidebarRole {
                font-size: 11px;
                font-weight: 600;
                color: rgba(15, 23, 42, 0.55);
                background: transparent;
            }

            QToolButton#sidebarFooterMenuBtn {
                background: #FFFFFF;
                border: 1px solid #DDE5FF;
                border-radius: 8px;
            }
            QToolButton#sidebarFooterMenuBtn:hover {
                background: #EEF3FF;
            }
        """)

    # =========================================================
    # UTIL
    # =========================================================
    def _derive_initials(self, name: str):
        parts = (name or "").strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return (name or "U")[:2].upper()

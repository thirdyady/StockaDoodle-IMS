# desktop_app/ui/header_bar.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from utils.helpers import get_feather_icon


class HeaderBar(QWidget):
    toggle_sidebar = pyqtSignal()

    def __init__(self, user_data=None):
        super().__init__()

        self.user = user_data or {}

        self.setObjectName("headerBar")
        self.setFixedHeight(62)

        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.setSpacing(14)

        # ---- TOGGLE SIDEBAR BTN ----
        menu_btn = QPushButton()
        menu_btn.setObjectName("headerMenu")
        menu_btn.setIcon(get_feather_icon("menu", 20))
        menu_btn.setFixedSize(36, 36)
        menu_btn.clicked.connect(self.toggle_sidebar.emit)
        layout.addWidget(menu_btn)

        # ---- APP TITLE ----
        title = QLabel("StockaDoodle")
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        layout.addStretch()

        # ---- SEARCH BAR ----
        search = QLineEdit()
        search.setObjectName("headerSearch")
        search.setPlaceholderText("Search products, categories, orders…")
        search.setFixedHeight(36)
        search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(search, 2)

        # ---- AVATAR/INITIAL ----
        initials = self._get_initials(self.user.get("full_name", "User"))

        avatar_btn = QPushButton(initials)
        avatar_btn.setObjectName("avatarBtn")
        avatar_btn.setFixedSize(38, 38)
        layout.addWidget(avatar_btn)

    def _get_initials(self, text: str) -> str:
        parts = text.split(" ")
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[1][0].upper()
        return text[0:2].upper()

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QMenu, QToolButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction

from desktop_app.utils.helpers import get_feather_icon


class HeaderBar(QWidget):
    toggle_sidebar = pyqtSignal()
    view_profile_requested = pyqtSignal()

    def __init__(self, user_data=None):
        super().__init__()

        self.user = user_data or {}
        self.full_name = self.user.get("full_name", "User")
        self.initials = self._derive_initials(self.full_name)

        self.setObjectName("headerBar")
        self.setFixedHeight(68)

        self._apply_stylesheet()
        self._build()

    # =============================================================
    # UI BUILD
    # =============================================================
    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(18)

        # Sidebar toggle
        btn_menu = QPushButton()
        btn_menu.setObjectName("menuBtn")
        btn_menu.setIcon(get_feather_icon("menu", 22))
        btn_menu.setFixedSize(42, 42)
        btn_menu.clicked.connect(self.toggle_sidebar.emit)
        layout.addWidget(btn_menu)

        # Title
        title = QLabel("StockaDoodle")
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        layout.addStretch()

        # Search bar (UI-only for now)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search products, sales, users...")
        self.search.setObjectName("searchBox")
        self.search.setFixedHeight(42)
        layout.addWidget(self.search, 3)

        # Profile button
        self.profile_btn = QToolButton()
        self.profile_btn.setObjectName("profileBtn")
        self.profile_btn.setFixedSize(42, 42)
        self.profile_btn.setText(self.initials)
        self.profile_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # Dropdown menu
        self.menu = QMenu(self)
        act_profile = QAction("View Profile", self)
        act_logout = QAction("Logout", self)

        self.menu.addAction(act_profile)
        self.menu.addSeparator()
        self.menu.addAction(act_logout)

        self.profile_btn.setMenu(self.menu)

        act_profile.triggered.connect(self.view_profile_requested.emit)
        act_logout.triggered.connect(self._logout_request)

        layout.addWidget(self.profile_btn)

    # =============================================================
    # STYLES
    # =============================================================
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget#headerBar {
                background: #FFFFFF;
                border-bottom: 1px solid #E1E5EE;
            }

            #headerTitle {
                font-size: 21px;
                font-weight: 800;
                color: #0A2A83;
            }

            #menuBtn {
                background: #F3F6FF;
                border: 1px solid #D9E4FF;
                border-radius: 10px;
            }

            #menuBtn:hover {
                background: #E8EEFF;
            }

            #searchBox {
                padding-left: 14px;
                font-size: 14px;
                border-radius: 10px;
                border: 1px solid #D3D8E5;
                background: #FAFBFF;
            }

            #searchBox:focus {
                border: 1px solid #8CAFFF;
                background: white;
            }

            #profileBtn {
                background: #0A2A83;
                color: white;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
            }

            #profileBtn:hover {
                background: #153AAB;
            }

            QMenu {
                background: #FFFFFF;
                border: 1px solid #CDD5EA;
                border-radius: 8px;
            }

            QMenu::item {
                padding: 8px 18px;
                font-size: 14px;
            }

            QMenu::item:selected {
                background: #E6ECFF;
            }
        """)

    # =============================================================
    # UTILITIES
    # =============================================================
    def _derive_initials(self, name: str):
        parts = (name or "").strip().split(" ")
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return (name or "U")[:2].upper()

    # =============================================================
    # LOGOUT
    # =============================================================
    def _logout_request(self):
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()

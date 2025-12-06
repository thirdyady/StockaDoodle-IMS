from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


# ====================================
# Small helper: shadow
# ====================================
def apply_card_shadow(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(22)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 90))
    widget.setGraphicsEffect(shadow)


# ====================================
# Reusable info row
# ====================================
class InfoRow(QWidget):
    def __init__(self, label: str, value: str = ""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        lbl = QLabel(label)
        lbl.setStyleSheet("""
            font-size: 12px;
            color: rgba(0,0,0,0.55);
            font-weight: 600;
            min-width: 110px;
        """)

        self.val = QLabel(value or "—")
        self.val.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #111827;
        """)

        layout.addWidget(lbl)
        layout.addWidget(self.val, 1)

    def set_value(self, value: str):
        self.val.setText(value or "—")


# ====================================
# MAIN PROFILE PAGE
# ====================================
class ProfilePage(QWidget):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self._build_ui()
        self._load_user()

    # ---------------------------------------
    # UI
    # ---------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(22)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Profile")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 800;
            color: #0A0A0A;
        """)
        subtitle = QLabel("Account details and role access.")
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: rgba(0,0,0,0.55);
        """)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        title_row.addLayout(title_col)
        title_row.addStretch()

        root.addLayout(title_row)

        # Main card
        card = QFrame()
        card.setObjectName("profileCard")
        card.setStyleSheet("""
            #profileCard {
                background: #FFFFFF;
                border-radius: 18px;
                border: 1px solid #DDE3EA;
            }
        """)
        apply_card_shadow(card)

        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(28, 24, 28, 24)
        c_layout.setSpacing(18)

        # Header inside card
        header = QHBoxLayout()
        self.name_lbl = QLabel(self.user.get("full_name", "User"))
        self.name_lbl.setStyleSheet("""
            font-size: 22px;
            font-weight: 800;
            color: #0A2A83;
        """)

        self.role_badge = QLabel((self.user.get("role") or "—").capitalize())
        self.role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.role_badge.setFixedHeight(26)
        self.role_badge.setStyleSheet("""
            background: #EEF3FF;
            border: 1px solid #D7E2FF;
            color: #0A2A83;
            border-radius: 8px;
            padding: 0 10px;
            font-size: 11px;
            font-weight: 700;
        """)

        header.addWidget(self.name_lbl)
        header.addStretch()
        header.addWidget(self.role_badge)

        c_layout.addLayout(header)

        # Divider line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #E6EAF3;")
        c_layout.addWidget(line)

        # Info grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(38)
        grid.setVerticalSpacing(14)

        # Left column
        self.row_id = InfoRow("User ID")
        self.row_username = InfoRow("Username")
        self.row_email = InfoRow("Email")

        # Right column
        self.row_role = InfoRow("Role")
        self.row_status = InfoRow("Status", "Active")
        self.row_note = InfoRow("Access")

        grid.addWidget(self.row_id, 0, 0)
        grid.addWidget(self.row_username, 1, 0)
        grid.addWidget(self.row_email, 2, 0)

        grid.addWidget(self.row_role, 0, 1)
        grid.addWidget(self.row_status, 1, 1)
        grid.addWidget(self.row_note, 2, 1)

        c_layout.addLayout(grid)

        # Role-based access note
        self.access_hint = QLabel("")
        self.access_hint.setStyleSheet("""
            font-size: 12px;
            color: rgba(0,0,0,0.55);
        """)
        c_layout.addWidget(self.access_hint)

        # Optional buttons row (purely UI for now)
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_change_password = QPushButton("Change Password")
        self.btn_change_password.setEnabled(False)  # hook later if needed
        self.btn_change_password.setStyleSheet("""
            QPushButton {
                height: 34px;
                padding: 0 14px;
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                background: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:disabled {
                color: rgba(0,0,0,0.35);
                background: #F7F8FB;
            }
        """)

        btn_row.addWidget(self.btn_change_password)
        c_layout.addLayout(btn_row)

        root.addWidget(card)
        root.addStretch()

    # ---------------------------------------
    # DATA
    # ---------------------------------------
    def _load_user(self):
        uid = str(self.user.get("id", "—"))
        username = self.user.get("username", "—")
        email = self.user.get("email", "—")
        role = (self.user.get("role") or "—").capitalize()

        self.name_lbl.setText(self.user.get("full_name", "User"))
        self.role_badge.setText(role)

        self.row_id.set_value(uid)
        self.row_username.set_value(username)
        self.row_email.set_value(email)
        self.row_role.set_value(role)

        # Simple role descriptions
        role_lower = (self.user.get("role") or "").lower()
        if role_lower == "admin":
            access = "Full access to users, inventory, sales, reports."
        elif role_lower == "manager":
            access = "Inventory, sales, reports, and monitoring access."
        elif role_lower == "staff":
            access = "Inventory operations and sales support."
        elif role_lower == "retailer":
            access = "Sales + limited inventory view. Reports restricted."
        else:
            access = "Role access not defined."

        self.row_note.set_value(access)
        self.access_hint.setText(access)

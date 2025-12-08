# desktop_app/ui/pages/profile.py

from __future__ import annotations

import traceback
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

from desktop_app.utils.api_wrapper import get_api


class ProfilePage(QWidget):
    """
    Profile page (clean look)

    Tabs:
      - Information
      - Security
    """

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)

        self.setObjectName("profilePage")

        self.user: Dict[str, Any] = user_data or {}
        self.api = get_api()

        self._build_ui()
        self._apply_strong_overrides()
        self._populate_fields()

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(20)

        header = QHBoxLayout()
        name = self.user.get("full_name") or self.user.get("username") or "User"

        title = QLabel(f"Profile — {name}")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # -----------------------------------------------------
        # Information Tab
        # -----------------------------------------------------
        self.info_tab = QWidget()
        self.info_tab.setObjectName("profileInfoTab")

        info_l = QVBoxLayout(self.info_tab)
        info_l.setContentsMargins(6, 6, 6, 6)
        info_l.setSpacing(12)

        info_card = QFrame()
        info_card.setObjectName("Card")

        ic = QVBoxLayout(info_card)
        ic.setContentsMargins(18, 16, 18, 16)
        ic.setSpacing(12)

        info_title = QLabel("Account Information")
        info_title.setObjectName("CardTitle")
        ic.addWidget(info_title)

        self.input_full_name = QLineEdit()
        self.input_full_name.setPlaceholderText("Full name")

        self.input_username = QLineEdit()
        self.input_username.setReadOnly(True)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email")

        self.input_role = QLineEdit()
        self.input_role.setReadOnly(True)

        ic.addWidget(self._field_block("Full Name", self.input_full_name))
        ic.addWidget(self._field_block("Username", self.input_username))
        ic.addWidget(self._field_block("Email", self.input_email))
        ic.addWidget(self._field_block("Role", self.input_role))

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setObjectName("ghost")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)

        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setFixedHeight(36)
        self.btn_save.clicked.connect(self._on_save_clicked)

        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_save)
        ic.addLayout(btn_row)

        info_l.addWidget(info_card)
        info_l.addStretch()

        self.tabs.addTab(self.info_tab, "Information")

        # -----------------------------------------------------
        # Security Tab
        # -----------------------------------------------------
        self.security_tab = QWidget()
        self.security_tab.setObjectName("profileSecurityTab")

        sec_l = QVBoxLayout(self.security_tab)
        sec_l.setContentsMargins(6, 6, 6, 6)
        sec_l.setSpacing(12)

        sec_card = QFrame()
        sec_card.setObjectName("Card")

        sc = QVBoxLayout(sec_card)
        sc.setContentsMargins(18, 16, 18, 16)
        sc.setSpacing(10)

        sec_title = QLabel("Security")
        sec_title.setObjectName("CardTitle")
        sc.addWidget(sec_title)

        lbl_cp = QLabel("Change Password")
        lbl_cp.setStyleSheet("background: transparent;")
        sc.addWidget(lbl_cp)

        self.input_curr_pwd = QLineEdit()
        self.input_curr_pwd.setPlaceholderText("Current password")
        self.input_curr_pwd.setEchoMode(QLineEdit.EchoMode.Password)

        self.input_new_pwd = QLineEdit()
        self.input_new_pwd.setPlaceholderText("New password")
        self.input_new_pwd.setEchoMode(QLineEdit.EchoMode.Password)

        self.input_confirm_pwd = QLineEdit()
        self.input_confirm_pwd.setPlaceholderText("Confirm new password")
        self.input_confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)

        sc.addWidget(self.input_curr_pwd)
        sc.addWidget(self.input_new_pwd)
        sc.addWidget(self.input_confirm_pwd)

        self.btn_change_pwd = QPushButton("Change Password")
        self.btn_change_pwd.setObjectName("secondaryBtn")
        self.btn_change_pwd.setFixedHeight(36)
        self.btn_change_pwd.clicked.connect(self._on_change_password_clicked)

        sc.addWidget(self.btn_change_pwd)

        note = QLabel("This will attempt to call the backend change-password endpoint.")
        note.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55); background: transparent;")
        sc.addWidget(note)

        sec_l.addWidget(sec_card)
        sec_l.addStretch()

        self.tabs.addTab(self.security_tab, "Security")

        root.addWidget(self.tabs)

    def _field_block(self, label_text: str, widget: QLineEdit) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("profileFieldBlock")

        l = QVBoxLayout(wrap)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setObjectName("profileFieldLabel")
        l.addWidget(lbl)
        l.addWidget(widget)

        wrap.setStyleSheet("background: transparent;")
        lbl.setStyleSheet("background: transparent;")

        widget.setStyleSheet("""
            background: #FFFFFF;
            color: #0F172A;
            border: 1px solid #D8E0F0;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 12.5px;
        """)

        return wrap

    # =========================================================
    # STRONG OVERRIDES
    # =========================================================
    def _apply_strong_overrides(self):
        self.setStyleSheet("""
            #profilePage QWidget#profileInfoTab,
            #profilePage QWidget#profileSecurityTab {
                background: transparent;
            }
            #profilePage QWidget#profileFieldBlock {
                background: transparent;
            }
            #profilePage QLabel#profileFieldLabel {
                background: transparent;
                font-weight: 600;
            }
        """)

    # =========================================================
    # Data
    # =========================================================
    def _populate_fields(self):
        self.input_full_name.setText(self.user.get("full_name", "") or "")
        self.input_username.setText(self.user.get("username", "") or "")
        self.input_email.setText(self.user.get("email", "") or "")
        self.input_role.setText((self.user.get("role") or "").capitalize())

    # =========================================================
    # Actions
    # =========================================================
    def _on_refresh_clicked(self):
        try:
            uid = self.user.get("id")
            if not uid:
                QMessageBox.information(self, "Profile", "No user ID found.")
                return

            data = None
            try:
                data = self.api.get_user(uid)  # type: ignore
            except Exception:
                data = None

            if not data:
                try:
                    users = self.api.get_users()
                    if isinstance(users, dict):
                        users = users.get("users", [])
                    data = next((u for u in (users or []) if u.get("id") == uid), None)
                except Exception:
                    data = None

            if not data:
                QMessageBox.information(
                    self, "Profile",
                    "Refresh unavailable. Backend may not support this yet."
                )
                return

            self.user.update(data)
            self._populate_fields()
            QMessageBox.information(self, "Profile", "Profile refreshed.")
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Profile", "Refresh failed.")

    def _on_save_clicked(self):
        full_name = self.input_full_name.text().strip()
        email = self.input_email.text().strip()

        if not full_name:
            QMessageBox.warning(self, "Validation", "Full name cannot be empty.")
            return

        uid = self.user.get("id")
        if not uid:
            QMessageBox.warning(self, "Save Error", "No user ID found.")
            return

        payload = {"full_name": full_name, "email": email}

        try:
            updated = False

            # ✅ correct signature: kwargs
            try:
                resp = self.api.update_user(uid, **payload)  # type: ignore
                if resp is not None:
                    updated = True
                    if isinstance(resp, dict):
                        self.user.update(resp)
            except Exception:
                updated = False

            if not updated:
                self.user.update(payload)

            self._populate_fields()

            QMessageBox.information(
                self, "Profile",
                "Changes saved." if updated else "Saved locally. Backend update not available yet."
            )
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Save Error", "Failed to save changes.")

    # -----------------------------
    # Password Change (real attempt)
    # -----------------------------
    def _on_change_password_clicked(self):
        curr = (self.input_curr_pwd.text() or "").strip()
        new = (self.input_new_pwd.text() or "").strip()
        confirm = (self.input_confirm_pwd.text() or "").strip()

        if not curr or not new:
            QMessageBox.warning(self, "Change Password", "Current and new password are required.")
            return

        if new != confirm:
            QMessageBox.warning(self, "Change Password", "New password and confirmation do not match.")
            return

        uid = self.user.get("id")

        try:
            ok = self._attempt_change_password(uid, curr, new)
            if ok:
                QMessageBox.information(self, "Change Password", "Password updated successfully.")
                self.input_curr_pwd.clear()
                self.input_new_pwd.clear()
                self.input_confirm_pwd.clear()
            else:
                QMessageBox.warning(
                    self, "Change Password",
                    "Password update failed.\nBackend method not found or signature mismatch."
                )
        except Exception as e:
            QMessageBox.critical(self, "Change Password", str(e))

    def _attempt_change_password(self, uid: Optional[int], current_pwd: str, new_pwd: str) -> bool:
        """
        Try common backend signatures without crashing.
        """
        candidates = [
            "change_password",
            "update_password",
            "set_password",
        ]

        for name in candidates:
            fn = getattr(self.api, name, None)
            if not callable(fn):
                continue

            # Try most explicit signatures first
            try:
                if uid is not None:
                    fn(user_id=uid, current_password=current_pwd, new_password=new_pwd)
                    return True
            except Exception:
                pass

            try:
                if uid is not None:
                    fn(uid, current_pwd, new_pwd)
                    return True
            except Exception:
                pass

            try:
                fn(current_password=current_pwd, new_password=new_pwd)
                return True
            except Exception:
                pass

            try:
                fn(current_pwd, new_pwd)
                return True
            except Exception:
                pass

        return False

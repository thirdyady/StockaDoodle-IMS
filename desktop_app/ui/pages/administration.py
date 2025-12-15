# desktop_app/ui/pages/administration.py

from __future__ import annotations

import csv
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QLineEdit,
    QComboBox, QCheckBox, QFormLayout, QFileDialog, QHeaderView,
    QToolButton
)

from desktop_app.utils.api_wrapper import get_api


# =========================================================
# Dialogs
# =========================================================

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User")
        self.setMinimumWidth(420)
        self._result_payload: Optional[Dict[str, Any]] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Create new account")
        title.setObjectName("CardTitle")
        root.addWidget(title)

        form_wrap = QFrame()
        form_wrap.setObjectName("Card")
        f_l = QFormLayout(form_wrap)
        f_l.setContentsMargins(12, 12, 12, 12)
        f_l.setSpacing(10)

        self.full_name = QLineEdit()
        self.username = QLineEdit()
        self.email = QLineEdit()

        self.role = QComboBox()
        self.role.addItems(["admin", "manager", "retailer"])

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Temporary password")

        self.active = QCheckBox("Active account")
        self.active.setChecked(True)

        f_l.addRow("Full name", self.full_name)
        f_l.addRow("Username", self.username)
        f_l.addRow("Email", self.email)
        f_l.addRow("Role", self.role)
        f_l.addRow("Password", self.password)
        f_l.addRow("", self.active)

        root.addWidget(form_wrap)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Create")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._on_create)

        btn_row.addWidget(cancel)
        btn_row.addWidget(save)

        root.addLayout(btn_row)

    def _on_create(self):
        payload = {
            "full_name": (self.full_name.text() or "").strip(),
            "username": (self.username.text() or "").strip(),
            "email": (self.email.text() or "").strip(),
            "role": (self.role.currentText() or "retailer").strip(),
            "password": (self.password.text() or "").strip(),
            "is_active": bool(self.active.isChecked()),
        }

        if not payload["full_name"] or not payload["username"] or not payload["email"]:
            QMessageBox.warning(self, "Missing fields", "Full name, username, and email are required.")
            return

        if not payload["password"]:
            QMessageBox.warning(self, "Missing fields", "Password is required for new users.")
            return

        self._result_payload = payload
        self.accept()

    def get_payload(self) -> Optional[Dict[str, Any]]:
        return self._result_payload


class EditDetailsDialog(QDialog):
    def __init__(self, user_row: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit User Details")
        self.setMinimumWidth(420)
        self.user_row = user_row or {}
        self._result_payload: Optional[Dict[str, Any]] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Update user details")
        title.setObjectName("CardTitle")
        root.addWidget(title)

        form_wrap = QFrame()
        form_wrap.setObjectName("Card")
        f_l = QFormLayout(form_wrap)
        f_l.setContentsMargins(12, 12, 12, 12)
        f_l.setSpacing(10)

        self.full_name = QLineEdit(self.user_row.get("full_name", ""))
        self.username = QLineEdit(self.user_row.get("username", ""))
        self.email = QLineEdit(self.user_row.get("email", ""))

        self.role = QComboBox()
        self.role.addItems(["admin", "manager", "retailer"])
        current_role = (self.user_row.get("role") or "retailer").lower()
        idx = self.role.findText(current_role)
        if idx >= 0:
            self.role.setCurrentIndex(idx)

        f_l.addRow("Full name", self.full_name)
        f_l.addRow("Username", self.username)
        f_l.addRow("Email", self.email)
        f_l.addRow("Role", self.role)

        root.addWidget(form_wrap)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Save")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._on_save)

        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _on_save(self):
        payload = {
            "id": self.user_row.get("id"),
            "full_name": (self.full_name.text() or "").strip(),
            "username": (self.username.text() or "").strip(),
            "email": (self.email.text() or "").strip(),
            "role": (self.role.currentText() or "retailer").strip(),
        }

        if not payload["id"]:
            QMessageBox.warning(self, "Error", "Missing user ID.")
            return

        if not payload["full_name"] or not payload["username"] or not payload["email"]:
            QMessageBox.warning(self, "Missing fields", "Full name, username, and email are required.")
            return

        self._result_payload = payload
        self.accept()

    def get_payload(self) -> Optional[Dict[str, Any]]:
        return self._result_payload


class ChangePasswordDialog(QDialog):
    def __init__(self, user_row: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.setMinimumWidth(420)
        self.user_row = user_row or {}
        self._result_password: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Set a new password")
        title.setObjectName("CardTitle")
        root.addWidget(title)

        form_wrap = QFrame()
        form_wrap.setObjectName("Card")
        f_l = QFormLayout(form_wrap)
        f_l.setContentsMargins(12, 12, 12, 12)
        f_l.setSpacing(10)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        f_l.addRow("New password", self.new_password)
        f_l.addRow("Confirm", self.confirm_password)

        root.addWidget(form_wrap)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Save")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._on_save)

        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _on_save(self):
        a = (self.new_password.text() or "").strip()
        b = (self.confirm_password.text() or "").strip()

        if not a:
            QMessageBox.warning(self, "Missing", "Password cannot be empty.")
            return
        if a != b:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        self._result_password = a
        self.accept()

    def get_password(self) -> Optional[str]:
        return self._result_password


class ChangeQuotaDialog(QDialog):
    def __init__(self, user_row: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Retailer Quota")
        self.setMinimumWidth(420)
        self.user_row = user_row or {}
        self._result_quota: Optional[float] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Update daily quota")
        title.setObjectName("CardTitle")
        root.addWidget(title)

        form_wrap = QFrame()
        form_wrap.setObjectName("Card")
        f_l = QFormLayout(form_wrap)
        f_l.setContentsMargins(12, 12, 12, 12)
        f_l.setSpacing(10)

        self.new_quota = QLineEdit()
        self.new_quota.setPlaceholderText("e.g. 1000")

        f_l.addRow("New quota", self.new_quota)

        root.addWidget(form_wrap)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Save")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._on_save)

        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _on_save(self):
        txt = (self.new_quota.text() or "").strip()
        try:
            val = float(txt)
        except Exception:
            QMessageBox.warning(self, "Invalid", "Quota must be a number.")
            return

        if val < 0:
            QMessageBox.warning(self, "Invalid", "Quota must be non-negative.")
            return

        self._result_quota = val
        self.accept()

    def get_quota(self) -> Optional[float]:
        return self._result_quota


# =========================================================
# Page
# =========================================================

class AdministrationPage(QWidget):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = get_api()

        self._users_cache: List[Dict[str, Any]] = []
        self._filtered_cache: List[Dict[str, Any]] = []

        self._build_ui()
        self.refresh()

    # ---------------------------
    # Icon helper
    # ---------------------------
    def _icon(self, filename: str) -> QIcon:
        """
        Loads icons from desktop_app/assets/icons/<filename>.
        If missing, returns empty QIcon (button will still work with tooltip).
        """
        base = Path(__file__).resolve().parents[2]  # desktop_app/
        p = base / "assets" / "icons" / filename
        if p.exists():
            return QIcon(str(p))
        return QIcon()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("User Management")
        title.setObjectName("title")
        hdr.addWidget(title)

        subtitle = QLabel("Manage user accounts, roles, and permissions")
        subtitle.setObjectName("muted")
        hdr.addWidget(subtitle)

        hdr.addStretch()

        self.btn_export = QPushButton("Export All")
        self.btn_export.setObjectName("secondaryBtn")
        self.btn_export.clicked.connect(self.export_all)
        hdr.addWidget(self.btn_export)

        self.btn_add = QPushButton("Add User")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.clicked.connect(self.add_user)
        hdr.addWidget(self.btn_add)

        root.addLayout(hdr)

        # Filters card
        filters = QFrame()
        filters.setObjectName("Card")
        fl = QVBoxLayout(filters)
        fl.setContentsMargins(14, 12, 14, 12)
        fl.setSpacing(10)

        row1 = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search users by name, email, or username...")
        self.search.textChanged.connect(self.apply_filters)
        row1.addWidget(self.search, 2)

        self.lbl_count = QLabel("Showing 0 of 0 users")
        self.lbl_count.setObjectName("muted")
        row1.addWidget(self.lbl_count, 1, alignment=Qt.AlignmentFlag.AlignRight)
        fl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.role_filter = QComboBox()
        self.role_filter.addItems(["All Roles", "admin", "manager", "retailer"])
        self.role_filter.currentIndexChanged.connect(self.apply_filters)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "active", "inactive"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        row2.addWidget(QLabel("Filter by Role"))
        row2.addWidget(self.role_filter, 1)
        row2.addSpacing(18)
        row2.addWidget(QLabel("Filter by Status"))
        row2.addWidget(self.status_filter, 1)

        row2.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        row2.addWidget(self.btn_refresh)

        fl.addLayout(row2)
        root.addWidget(filters)

        # Table card
        card = QFrame()
        card.setObjectName("Card")
        c_l = QVBoxLayout(card)
        c_l.setContentsMargins(12, 12, 12, 12)
        c_l.setSpacing(10)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Role", "Email", "Last Login", "Status", "Actions"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # allow horizontal scroll (important for smaller widths)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)

        try:
            hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)            # Name
            hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Role
            hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Email
            hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Last Login
            hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status

            # Actions fixed + narrow (icon buttons prevent overlap)
            hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(5, 176)
        except Exception:
            pass

        c_l.addWidget(self.table, 1)
        root.addWidget(card, 1)

        # Lock down if not admin
        if self.role != "admin":
            self.btn_add.setDisabled(True)
            self.btn_export.setDisabled(True)
            self.btn_refresh.setDisabled(True)
            self.search.setDisabled(True)
            self.role_filter.setDisabled(True)
            self.status_filter.setDisabled(True)

    # ---------------------------
    # Data
    # ---------------------------
    def refresh(self):
        if self.role != "admin":
            self._users_cache = []
            self._filtered_cache = []
            self._render([])
            return

        try:
            users_data = self.api.get_users()
            if isinstance(users_data, dict):
                self._users_cache = users_data.get("users", []) or []
            else:
                self._users_cache = users_data or []

            self.apply_filters()

        except Exception:
            traceback.print_exc()
            self._users_cache = []
            self._filtered_cache = []
            self._render([])

    def apply_filters(self):
        users = list(self._users_cache or [])

        role_sel = (self.role_filter.currentText() or "").strip().lower()
        if role_sel and role_sel != "all roles":
            users = [u for u in users if str(u.get("role") or "").lower() == role_sel]

        status_sel = (self.status_filter.currentText() or "").strip().lower()
        if status_sel and status_sel != "all status":
            want_active = (status_sel == "active")
            users = [u for u in users if bool(u.get("is_active", True)) == want_active]

        q = (self.search.text() or "").strip().lower()
        if q:
            def blob(u: Dict[str, Any]) -> str:
                return " ".join([
                    str(u.get("full_name") or ""),
                    str(u.get("username") or ""),
                    str(u.get("email") or ""),
                    str(u.get("role") or ""),
                ]).lower()
            users = [u for u in users if q in blob(u)]

        self._filtered_cache = users
        self._render(users)

    # ---------------------------
    # Render
    # ---------------------------
    def _render(self, users: List[Dict[str, Any]]):
        total = len(self._users_cache or [])
        showing = len(users or [])
        self.lbl_count.setText(f"Showing {showing} of {total} users")

        self.table.setRowCount(0)

        # current user id (for "admin cannot disable themselves")
        current_uid = None
        for k in ("id", "user_id", "retailer_id"):
            if self.user.get(k) is not None:
                try:
                    current_uid = int(self.user.get(k))
                    break
                except Exception:
                    current_uid = None

        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 46)

            uid = u.get("id")
            full_name = str(u.get("full_name") or "")
            username = str(u.get("username") or "")
            email = str(u.get("email") or "")
            role = str(u.get("role") or "").lower()
            is_active = bool(u.get("is_active", True))

            name_text = full_name if full_name else username
            if full_name and username and username.lower() not in full_name.lower():
                name_text = f"{full_name}  (@{username})"

            role_text = role.capitalize() if role else ""
            status_text = "Active" if is_active else "Inactive"

            last_login = ""
            for key in ("last_login", "last_login_at", "lastLogin"):
                if u.get(key):
                    last_login = str(u.get(key))
                    break

            self.table.setItem(row, 0, QTableWidgetItem(name_text))
            self.table.setItem(row, 1, QTableWidgetItem(role_text))
            self.table.setItem(row, 2, QTableWidgetItem(email))
            self.table.setItem(row, 3, QTableWidgetItem(last_login))
            self.table.setItem(row, 4, QTableWidgetItem(status_text))

            # Actions: icon toolbuttons (no overlap in small windows)
            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(0, 0, 0, 0)
            al.setSpacing(8)

            def make_btn(icon_file: str, tooltip: str, handler, enabled: bool = True):
                b = QToolButton()
                b.setToolTip(tooltip)
                b.setIcon(self._icon(icon_file))
                b.setFixedSize(34, 30)
                b.setEnabled(bool(enabled))
                b.clicked.connect(handler)
                return b

            btn_edit = make_btn(
                "edit-2.svg",
                "Edit user",
                lambda _, uu=u: self.edit_details(uu),
                enabled=True
            )
            al.addWidget(btn_edit)

            btn_quota = make_btn(
                "target.svg",
                "Change retailer quota",
                lambda _, uu=u: self.change_quota(uu),
                enabled=(role == "retailer")
            )
            al.addWidget(btn_quota)

            btn_pw = make_btn(
                "key.svg",
                "Change password",
                lambda _, uu=u: self.change_password(uu),
                enabled=True
            )
            al.addWidget(btn_pw)

            # Disable/Enable (admins cannot disable themselves)
            is_self = False
            try:
                is_self = (current_uid is not None and uid is not None and int(uid) == int(current_uid))
            except Exception:
                is_self = False

            can_toggle = not (role == "admin" and is_self)

            toggle_tip = "Disable user" if is_active else "Enable user"
            if not can_toggle:
                toggle_tip = "Admins cannot disable their own account"

            icon_file = "user-x.svg" if is_active else "user-check.svg"
            btn_toggle = make_btn(
                icon_file,
                toggle_tip,
                lambda _, uu=u: self.toggle_status(uu),
                enabled=can_toggle
            )
            al.addWidget(btn_toggle)

            self.table.setCellWidget(row, 5, actions)

        try:
            self.table.setColumnWidth(5, 176)
        except Exception:
            pass

    # ---------------------------
    # Actions
    # ---------------------------
    def add_user(self):
        dlg = AddUserDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dlg.get_payload()
        if not payload:
            return

        try:
            self.api.create_user(
                username=payload["username"],
                password=payload["password"],
                full_name=payload["full_name"],
                email=payload["email"],
                role=payload.get("role", "retailer"),
            )

            if payload.get("is_active") is False:
                self.refresh()
                created = next((u for u in self._users_cache if u.get("username") == payload["username"]), None)
                if created and created.get("id"):
                    self.api.update_user(int(created["id"]), is_active=False)

            QMessageBox.information(self, "Success", "User created.")
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Create failed", str(e))

    def edit_details(self, user_row: Dict[str, Any]):
        if not user_row:
            QMessageBox.information(self, "Edit", "Missing user row.")
            return

        dlg = EditDetailsDialog(user_row, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dlg.get_payload()
        if not payload:
            return

        try:
            uid = payload.pop("id", None)
            if not uid:
                QMessageBox.warning(self, "Edit", "Missing user ID.")
                return

            self.api.update_user(int(uid), **payload)

            QMessageBox.information(self, "Success", "User updated.")
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Update failed", str(e))

    def change_password(self, user_row: Dict[str, Any]):
        if not user_row:
            QMessageBox.information(self, "Password", "Missing user row.")
            return

        uid = user_row.get("id")
        if not uid:
            QMessageBox.warning(self, "Password", "Missing user ID.")
            return

        dlg = ChangePasswordDialog(user_row, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new_pw = dlg.get_password()
        if not new_pw:
            return

        try:
            self.api.update_user(int(uid), password=new_pw)
            QMessageBox.information(self, "Success", "Password updated.")
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Password update failed", str(e))

    def toggle_status(self, user_row: Dict[str, Any]):
        if not user_row:
            QMessageBox.information(self, "Status", "Missing user row.")
            return

        uid = user_row.get("id")
        if not uid:
            QMessageBox.warning(self, "Status", "Missing user ID.")
            return

        # extra safety: prevent admin disabling self even if clicked somehow
        try:
            cur_id = self.user.get("id") or self.user.get("user_id") or self.user.get("retailer_id")
            if cur_id is not None:
                cur_id = int(cur_id)
            row_role = str(user_row.get("role") or "").lower()
            if row_role == "admin" and cur_id is not None and int(uid) == int(cur_id):
                QMessageBox.information(self, "Not allowed", "Admins cannot disable their own account.")
                return
        except Exception:
            pass

        current = bool(user_row.get("is_active", True))
        new_value = not current

        msg = (
            "Disable this user?\n\nThey must NOT be able to login even with correct credentials."
            if new_value is False
            else "Enable this user?\n\nThey will be able to login again."
        )

        reply = QMessageBox.question(
            self,
            "Confirm status change",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api.update_user(int(uid), is_active=new_value)
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Status update failed", str(e))

    def change_quota(self, user_row: Dict[str, Any]):
        if not user_row:
            QMessageBox.information(self, "Quota", "Missing user row.")
            return

        if str(user_row.get("role") or "").lower() != "retailer":
            QMessageBox.information(self, "Quota", "Quota is only for Retailers.")
            return

        uid = user_row.get("id")
        if not uid:
            QMessageBox.warning(self, "Quota", "Missing user ID.")
            return

        fn = getattr(self.api, "update_retailer_quota", None)
        if not callable(fn):
            QMessageBox.warning(
                self,
                "Quota",
                "Your API client has no update_retailer_quota() method wired yet.\n"
                "We can wire it next."
            )
            return

        dlg = ChangeQuotaDialog(user_row, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new_quota = dlg.get_quota()
        if new_quota is None:
            return

        try:
            updated_by = None
            try:
                cu = getattr(self.api, "current_user", None)
                if isinstance(cu, dict) and cu.get("id") is not None:
                    updated_by = int(cu["id"])
            except Exception:
                updated_by = None

            if updated_by is not None:
                fn(int(uid), float(new_quota), updated_by=updated_by)
            else:
                fn(int(uid), float(new_quota))

            QMessageBox.information(self, "Success", "Quota updated.")
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Quota update failed", str(e))

    # ---------------------------
    # Export
    # ---------------------------
    def export_all(self):
        if self.role != "admin":
            QMessageBox.information(self, "Export", "Only admins can export.")
            return

        rows = self._filtered_cache or []
        if not rows:
            QMessageBox.information(self, "Export", "No users to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Users",
            "users_export.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=["id", "full_name", "username", "email", "role", "is_active"]
                )
                w.writeheader()
                for u in rows:
                    w.writerow({
                        "id": u.get("id", ""),
                        "full_name": u.get("full_name", ""),
                        "username": u.get("username", ""),
                        "email": u.get("email", ""),
                        "role": u.get("role", ""),
                        "is_active": u.get("is_active", True),
                    })

            QMessageBox.information(self, "Export", f"CSV saved:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

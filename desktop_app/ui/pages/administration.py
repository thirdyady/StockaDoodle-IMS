# desktop_app/ui/pages/administration.py

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QLineEdit,
    QComboBox, QCheckBox, QFormLayout
)

from desktop_app.utils.api_wrapper import get_api


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


class EditUserDialog(QDialog):
    def __init__(self, user_row: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit User")
        self.setMinimumWidth(420)
        self.user_row = user_row or {}
        self._result_payload: Optional[Dict[str, Any]] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Update account")
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

        self.active = QCheckBox("Active account")
        self.active.setChecked(bool(self.user_row.get("is_active", True)))

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("Leave blank to keep current password")

        f_l.addRow("Full name", self.full_name)
        f_l.addRow("Username", self.username)
        f_l.addRow("Email", self.email)
        f_l.addRow("Role", self.role)
        f_l.addRow("New password", self.new_password)
        f_l.addRow("", self.active)

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
            "is_active": bool(self.active.isChecked())
        }

        pwd = (self.new_password.text() or "").strip()
        if pwd:
            payload["password"] = pwd

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


class AdministrationPage(QWidget):
    """
    Admin-only user account administration.
    """

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.role = (self.user.get("role") or "").lower()
        self.api = get_api()

        self._users_cache: List[Dict[str, Any]] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Administration")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(self.btn_refresh)

        self.btn_add = QPushButton("Add User")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.clicked.connect(self.add_user)
        hdr.addWidget(self.btn_add)

        root.addLayout(hdr)

        card = QFrame()
        card.setObjectName("Card")
        c_l = QVBoxLayout(card)
        c_l.setContentsMargins(12, 12, 12, 12)
        c_l.setSpacing(10)

        subtitle = QLabel("Manage user accounts, roles, and status")
        subtitle.setObjectName("muted")
        c_l.addWidget(subtitle)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Full Name", "Username", "Role", "Email", "Status"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        c_l.addWidget(self.table, 1)

        act = QHBoxLayout()

        self.btn_edit = QPushButton("Edit Selected")
        self.btn_edit.clicked.connect(self.edit_selected)

        self.btn_toggle = QPushButton("Activate/Deactivate")
        self.btn_toggle.clicked.connect(self.toggle_selected)

        self.btn_reset = QPushButton("Reset Password")
        self.btn_reset.setObjectName("secondaryBtn")
        self.btn_reset.clicked.connect(self.reset_password_stub)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_selected)

        act.addWidget(self.btn_edit)
        act.addWidget(self.btn_toggle)
        act.addWidget(self.btn_reset)
        act.addStretch()
        act.addWidget(self.btn_delete)

        c_l.addLayout(act)

        root.addWidget(card, 1)

    def refresh(self):
        if self.role != "admin":
            self._users_cache = []
            self._render([])
            return

        try:
            users_data = self.api.get_users()
            if isinstance(users_data, dict):
                self._users_cache = users_data.get("users", []) or []
            else:
                self._users_cache = users_data or []

            self._render(self._users_cache)

        except Exception:
            traceback.print_exc()
            self._users_cache = []
            self._render([])

    def _render(self, users: List[Dict[str, Any]]):
        self.table.setRowCount(0)

        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            uid = str(u.get("id", ""))
            full_name = str(u.get("full_name", ""))
            username = str(u.get("username", ""))
            role = str(u.get("role", ""))
            email = str(u.get("email", ""))
            is_active = bool(u.get("is_active", True))

            status = "Active" if is_active else "Inactive"

            self.table.setItem(row, 0, QTableWidgetItem(uid))
            self.table.setItem(row, 1, QTableWidgetItem(full_name))
            self.table.setItem(row, 2, QTableWidgetItem(username))
            self.table.setItem(row, 3, QTableWidgetItem(role))
            self.table.setItem(row, 4, QTableWidgetItem(email))
            self.table.setItem(row, 5, QTableWidgetItem(status))

        try:
            self.table.resizeColumnsToContents()
        except Exception:
            pass

    def _selected_user(self) -> Optional[Dict[str, Any]]:
        row = self.table.currentRow()
        if row < 0:
            return None

        try:
            uid_item = self.table.item(row, 0)
            uid = int(uid_item.text()) if uid_item else None
        except Exception:
            uid = None

        if uid is None:
            return None

        for u in self._users_cache:
            try:
                if int(u.get("id", -1)) == uid:
                    return u
            except Exception:
                continue

        return None

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

    def edit_selected(self):
        user_row = self._selected_user()
        if not user_row:
            QMessageBox.information(self, "Edit", "Please select a user row.")
            return

        dlg = EditUserDialog(user_row, self)
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

    def toggle_selected(self):
        user_row = self._selected_user()
        if not user_row:
            QMessageBox.information(self, "Status", "Please select a user row.")
            return

        uid = user_row.get("id")
        if not uid:
            QMessageBox.warning(self, "Status", "Missing user ID.")
            return

        current = bool(user_row.get("is_active", True))
        new_value = not current

        try:
            self.api.update_user(int(uid), is_active=new_value)
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Status update failed", str(e))

    def delete_selected(self):
        user_row = self._selected_user()
        if not user_row:
            QMessageBox.information(self, "Delete", "Please select a user row.")
            return

        uid = user_row.get("id")
        if not uid:
            QMessageBox.warning(self, "Delete", "Missing user ID.")
            return

        reply = QMessageBox.question(
            self,
            "Delete user",
            f"Delete user ID {uid}?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api.delete_user(int(uid))
            QMessageBox.information(self, "Success", "User deleted.")
            self.refresh()

        except Exception as e:
            QMessageBox.critical(self, "Delete failed", str(e))

    def reset_password_stub(self):
        user_row = self._selected_user()
        if not user_row:
            QMessageBox.information(self, "Reset Password", "Please select a user row.")
            return

        QMessageBox.information(
            self,
            "Reset Password",
            "This is a UI placeholder.\nYou can wire a real reset flow later."
        )

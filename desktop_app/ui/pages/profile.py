# desktop_app/ui/pages/profile.py

from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QFrame, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QStandardPaths, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QFont
)

from desktop_app.utils.api_wrapper import get_api


# =========================================================
# Avatar helpers
# =========================================================

AVATAR_SIZE = 56  # header avatar size


def _app_cache_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not base:
        base = os.path.expanduser("~/.stockadoodle")
    os.makedirs(base, exist_ok=True)
    return base


def _local_profile_photo_path(user_id: Optional[int]) -> str:
    uid = int(user_id) if user_id is not None else 0
    return os.path.join(_app_cache_dir(), f"profile_{uid}.png")


def _derive_initials(name: str) -> str:
    parts = (name or "").strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "U"


def _initials_avatar_pixmap(size: int, initials: str, bg_hex: str = "#0A2A83") -> QPixmap:
    """
    Safe initials avatar painter (NO fillRect with string).
    Draws a circle with initials centered.
    """
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    bg = QColor(bg_hex)
    if not bg.isValid():
        bg = QColor("#0A2A83")

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(bg)
    painter.drawEllipse(0, 0, size, size)

    # text
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI")
    font.setBold(True)
    font.setPixelSize(max(10, int(size * 0.36)))
    painter.setFont(font)

    painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, (initials or "U")[:2].upper())
    painter.end()
    return pm


def _round_pixmap(pix: QPixmap, size: int) -> QPixmap:
    """
    Crop/scale into a circle.
    """
    if pix.isNull():
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)
        return out

    scaled = pix.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)

    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    p.setClipPath(path)

    # center crop
    x = (scaled.width() - size) // 2
    y = (scaled.height() - size) // 2
    p.drawPixmap(0, 0, scaled.copy(x, y, size, size))
    p.end()

    return out


# =========================================================
# Profile Page
# =========================================================

class ProfilePage(QWidget):
    """
    Profile page (clean look)

    Tabs:
      - Information
      - Security

    Photo behavior:
      - If user has a local cached photo: use it
      - Else: use initials (default)
    """

    # ✅ lets MainWindow refresh sidebar footer avatar if needed
    user_updated = pyqtSignal(dict)

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)

        self.setObjectName("profilePage")

        self.user: Dict[str, Any] = user_data or {}
        self.api = get_api()

        self._build_ui()
        self._apply_strong_overrides()
        self._populate_fields()
        self._refresh_avatar()

    # =========================================================
    # UI
    # =========================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(20)

        # Header row (avatar + title)
        header = QHBoxLayout()
        header.setSpacing(12)

        self.avatar_lbl = QLabel()
        self.avatar_lbl.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.avatar_lbl.setStyleSheet("background: transparent;")
        header.addWidget(self.avatar_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

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

        # Photo controls (local only; safe)
        photo_row = QHBoxLayout()
        photo_row.setSpacing(10)

        self.btn_upload_photo = QPushButton("Upload Photo")
        self.btn_upload_photo.setObjectName("secondaryBtn")
        self.btn_upload_photo.setFixedHeight(34)
        self.btn_upload_photo.clicked.connect(self._on_upload_photo)

        self.btn_remove_photo = QPushButton("Remove Photo")
        self.btn_remove_photo.setObjectName("ghost")
        self.btn_remove_photo.setFixedHeight(34)
        self.btn_remove_photo.clicked.connect(self._on_remove_photo)

        photo_row.addWidget(self.btn_upload_photo)
        photo_row.addWidget(self.btn_remove_photo)
        photo_row.addStretch()
        ic.addLayout(photo_row)

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
    # Avatar logic
    # =========================================================
    def _refresh_avatar(self):
        """
        Priority:
          1) local cached profile_<uid>.png
          2) initials default
        """
        uid = self.user.get("id")
        local_path = _local_profile_photo_path(uid)

        pix = QPixmap()
        if os.path.exists(local_path):
            pix = QPixmap(local_path)

        if not pix.isNull():
            pix = _round_pixmap(pix, AVATAR_SIZE)
            self.avatar_lbl.setPixmap(pix)
            return

        # initials default
        name = self.user.get("full_name") or self.user.get("username") or "User"
        initials = _derive_initials(str(name))
        pix2 = _initials_avatar_pixmap(AVATAR_SIZE, initials)
        self.avatar_lbl.setPixmap(pix2)

    def _on_upload_photo(self):
        uid = self.user.get("id")
        if not uid:
            QMessageBox.information(self, "Profile Photo", "No user ID found.")
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Photo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.ico)"
        )
        if not path:
            return

        try:
            pix = QPixmap(path)
            if pix.isNull():
                QMessageBox.warning(self, "Profile Photo", "Invalid image file.")
                return

            # Save locally as PNG (reliable)
            save_path = _local_profile_photo_path(uid)
            scaled = pix.scaled(
                256, 256,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            crop = scaled.copy(
                max(0, (scaled.width() - 256) // 2),
                max(0, (scaled.height() - 256) // 2),
                256, 256
            )
            ok = crop.save(save_path, "PNG")
            if not ok:
                QMessageBox.warning(self, "Profile Photo", "Failed to save profile photo locally.")
                return

            # keep local user dict updated (for sidebar)
            self.user["profile_image_path"] = save_path
            self.user_updated.emit({"profile_image_path": save_path})

            # Optional best-effort backend update (won't break if not supported)
            try:
                with open(save_path, "rb") as f:
                    raw = f.read()
                try:
                    self.api.update_user(int(uid), image_data=raw)  # type: ignore
                except Exception:
                    pass
            except Exception:
                pass

            self._refresh_avatar()
            QMessageBox.information(self, "Profile Photo", "Profile photo updated.")

        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Profile Photo", "Upload failed.")

    def _on_remove_photo(self):
        uid = self.user.get("id")
        if not uid:
            QMessageBox.information(self, "Profile Photo", "No user ID found.")
            return

        try:
            save_path = _local_profile_photo_path(uid)
            if os.path.exists(save_path):
                os.remove(save_path)

            # update local user dict + sidebar
            if "profile_image_path" in self.user:
                self.user["profile_image_path"] = ""
            self.user_updated.emit({"profile_image_path": ""})

            # Optional best-effort backend remove (ignore if not supported)
            try:
                self.api.update_user(int(uid), image_data=None)  # type: ignore
            except Exception:
                pass

            self._refresh_avatar()
            QMessageBox.information(self, "Profile Photo", "Profile photo removed (initials shown).")
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Profile Photo", "Failed to remove photo.")

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
            self._refresh_avatar()
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

            # notify (for sidebar name changes)
            self.user_updated.emit({"full_name": self.user.get("full_name", full_name)})

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

            try:
                if uid is not None:
                    fn(user_id=uid, old_password=current_pwd, new_password=new_pwd)
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
                fn(old_password=current_pwd, new_password=new_pwd)
                return True
            except Exception:
                pass

            try:
                fn(current_pwd, new_pwd)
                return True
            except Exception:
                pass

        return False

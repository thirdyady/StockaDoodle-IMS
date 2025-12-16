# desktop_app/ui/side_bar.py

from __future__ import annotations

import os
from typing import Dict, List, Tuple, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QHBoxLayout, QToolButton, QSizePolicy, QMenu
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QStandardPaths
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QImageReader

from desktop_app.utils.helpers import get_feather_icon
from desktop_app.utils.icons import get_icon


# ---------------------------------------------------------
# Profile photo cache helpers (matches ProfilePage behavior)
# ---------------------------------------------------------
def _app_cache_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not base:
        base = os.path.expanduser("~/.stockadoodle")
    os.makedirs(base, exist_ok=True)
    return base


def _local_profile_photo_path(user_id: Optional[int]) -> str:
    uid = int(user_id) if user_id is not None else 0
    return os.path.join(_app_cache_dir(), f"profile_{uid}.png")


def _load_pixmap_fresh(path: str) -> QPixmap:
    """
    Load image using QImageReader to avoid any stale image behavior
    and to support auto-transform.
    """
    try:
        if not path or not os.path.exists(path):
            return QPixmap()

        reader = QImageReader(path)
        reader.setAutoTransform(True)
        img = reader.read()
        if img.isNull():
            return QPixmap()

        return QPixmap.fromImage(img)
    except Exception:
        return QPixmap()


class _SidebarItemWidget(QWidget):
    """
    Custom row widget so we can:
    - keep icons visible on selected state (white on blue)
    - keep text from clipping (layout driven, not QListWidget's text rendering)
    - collapse without messing with item.text()/UserRole data
    """

    def __init__(
        self,
        label: str,
        icon_key: str,
        icon_size: int,
        normal_color: str,
        selected_color: str,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setObjectName("sidebarItem")

        # ✅ ensures the widget fills the whole QListWidget row width
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._label_text = label
        self._icon_key = icon_key
        self._icon_size = icon_size
        self._normal_color = normal_color
        self._selected_color = selected_color

        self._collapsed = False
        self._selected = False

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setObjectName("sidebarItemIcon")
        self.icon_lbl.setFixedSize(icon_size + 8, icon_size + 8)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_lbl = QLabel(label)
        self.text_lbl.setObjectName("sidebarItemText")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # ✅ init dynamic property so QSS can target reliably
        self.text_lbl.setProperty("selected", False)

        row.addWidget(self.icon_lbl)
        row.addWidget(self.text_lbl, 1)

        self._refresh_icon()

    def set_collapsed(self, collapsed: bool):
        self._collapsed = bool(collapsed)
        self.text_lbl.setVisible(not self._collapsed)

    def set_selected(self, selected: bool):
        self._selected = bool(selected)

        # ✅ Set selected on BOTH container + label (fixes Dashboard stuck-white issue)
        self.setProperty("selected", self._selected)
        self.text_lbl.setProperty("selected", self._selected)

        self._refresh_icon()

        # ✅ Force stylesheet re-eval on widget + label
        for w in (self, self.text_lbl, self.icon_lbl):
            try:
                w.style().unpolish(w)
                w.style().polish(w)
                w.update()
            except Exception:
                pass

        self.update()

    def _to_pixmap(self, icon: QIcon, size: int) -> QPixmap:
        try:
            pm = icon.pixmap(size, size)
            return pm
        except Exception:
            return QPixmap()

    def _resolve_icon(self, key: str, size: int, color: str) -> QIcon:
        """
        Prefer your assets/icons PNG/SVG loader, fallback to feather loader.
        """
        ico = get_icon(key, size=size, color=color)
        if isinstance(ico, QIcon) and not ico.isNull():
            return ico

        f = get_feather_icon(key, size, color=color)
        if isinstance(f, QIcon) and not f.isNull():
            return f

        return QIcon()

    def _refresh_icon(self):
        color = self._selected_color if self._selected else self._normal_color
        ico = self._resolve_icon(self._icon_key, self._icon_size, color)
        pm = self._to_pixmap(ico, self._icon_size)

        if pm.isNull():
            self.icon_lbl.setText("•")
        else:
            self.icon_lbl.setPixmap(pm)


class SideBar(QWidget):
    """
    Role rules:
    - Admin/Manager: Inventory + Point of Sale + Sales
    - Retailer: Inventory + Point of Sale only (NO Sales tab)
    """

    profile_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    EXPANDED_WIDTH = 260
    COLLAPSED_WIDTH = 84

    ICON_TINT = "#0A2A83"
    ICON_TINT_SELECTED = "#FFFFFF"

    def __init__(self, user=None):
        super().__init__()

        self.user = user or {}
        self.role = (self.user.get("role") or "").lower()

        self.setObjectName("sidebar")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._collapsed = False
        self._items: Dict[str, QListWidgetItem] = {}
        self._item_widgets: Dict[str, _SidebarItemWidget] = {}
        self._label_widgets = []

        self._footer_frame = None
        self._footer_name = None
        self._footer_role = None
        self._btn_footer_menu = None
        self._footer_avatar = None
        self._footer_text_wrap = None

        self._build_ui()
        self._apply_style()

        self.set_collapsed(False)
        self._sync_selected_state()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def update_user(self, user: dict):
        self.user = user or {}
        self.role = (self.user.get("role") or "").lower()

        if self._footer_name:
            self._footer_name.setText(self.user.get("full_name", "User"))

        if self._footer_role:
            self._footer_role.setText((self.user.get("role") or "-").capitalize())

        self._refresh_footer_avatar()

    # ---------------------------------------------------------
    # Footer avatar helpers
    # ---------------------------------------------------------
    def _get_profile_image_path(self) -> str:
        p = str(
            self.user.get("profile_image_path")
            or self.user.get("profile_photo_path")
            or self.user.get("avatar_path")
            or self.user.get("profile_picture")
            or self.user.get("photo")
            or ""
        ).strip()

        if p and os.path.exists(p):
            return p

        uid = self.user.get("id")
        cached = _local_profile_photo_path(uid)
        if cached and os.path.exists(cached):
            return cached

        return ""

    def _rounded_pixmap(self, pm: QPixmap, size: int, radius: int) -> QPixmap:
        if pm.isNull():
            return pm

        scaled = pm.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, radius, radius)
        painter.setClipPath(path)

        x = int((scaled.width() - size) / 2) if scaled.width() > size else 0
        y = int((scaled.height() - size) / 2) if scaled.height() > size else 0
        painter.drawPixmap(0, 0, scaled, x, y, size, size)

        painter.end()
        return out

    def _refresh_footer_avatar(self):
        if not self._footer_avatar:
            return

        avatar_size = 36
        radius = 10

        img_path = self._get_profile_image_path()

        try:
            if img_path and os.path.exists(img_path):
                pm = _load_pixmap_fresh(img_path)
                if not pm.isNull():
                    rounded = self._rounded_pixmap(pm, avatar_size, radius)
                    self._footer_avatar.setPixmap(rounded)
                    self._footer_avatar.setText("")
                    self._footer_avatar.setStyleSheet("""
                        QLabel#sidebarAvatar {
                            background: transparent;
                            border-radius: 10px;
                        }
                    """)
                    self._footer_avatar.update()
                    return
        except Exception:
            pass

        initials = self._derive_initials(self.user.get("full_name", "User"))
        self._footer_avatar.setPixmap(QPixmap())
        self._footer_avatar.setText(initials)
        self._footer_avatar.setStyleSheet("""
            QLabel#sidebarAvatar {
                background: #0A2A83;
                color: white;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 800;
            }
        """)
        self._footer_avatar.update()

    # ---------------------------------------------------------
    # Click helpers
    # ---------------------------------------------------------
    def _bind_row_click(self, row_widget: _SidebarItemWidget, row_index: int):
        def handler(event, idx=row_index):
            try:
                self.menu.setCurrentRow(idx)
            except Exception:
                pass
            try:
                event.accept()
            except Exception:
                pass

        for w in (row_widget, row_widget.icon_lbl, row_widget.text_lbl):
            try:
                w.setCursor(Qt.CursorShape.PointingHandCursor)
                w.mousePressEvent = handler  # type: ignore
            except Exception:
                pass

    def _bind_footer_click(self):
        if not self._footer_frame:
            return

        def handler(event):
            if self._btn_footer_menu:
                try:
                    if self._btn_footer_menu.underMouse():
                        return
                except Exception:
                    pass
            self.profile_requested.emit()
            try:
                event.accept()
            except Exception:
                pass

        clickable = [self._footer_frame, self._footer_avatar, self._footer_name, self._footer_role, self._footer_text_wrap]
        for w in clickable:
            if not w:
                continue
            try:
                w.setCursor(Qt.CursorShape.PointingHandCursor)
                w.mousePressEvent = handler  # type: ignore
            except Exception:
                pass

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        brand_card = QFrame()
        brand_card.setObjectName("sidebarBrandCard")
        brand_layout = QHBoxLayout(brand_card)
        brand_layout.setContentsMargins(12, 12, 12, 12)
        brand_layout.setSpacing(10)

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

        section = QLabel("MAIN")
        section.setObjectName("sidebarSection")
        self._label_widgets.append(section)
        layout.addWidget(section)

        self.menu = QListWidget()
        self.menu.setObjectName("sidebarMenu")
        self.menu.setSpacing(6)
        self.menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.menu.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.menu.setUniformItemSizes(True)
        self.menu.setFrameShape(QFrame.Shape.NoFrame)

        self.menu.currentRowChanged.connect(lambda _: self._sync_selected_state())

        menu_items = self._resolve_menu_items()
        self._items = {}
        self._item_widgets = {}

        for idx, (label, icon_key) in enumerate(menu_items):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, label)
            item.setSizeHint(QSize(1, 46))

            w = _SidebarItemWidget(
                label=label,
                icon_key=icon_key,
                icon_size=18,
                normal_color=self.ICON_TINT,
                selected_color=self.ICON_TINT_SELECTED,
            )

            self.menu.addItem(item)
            self.menu.setItemWidget(item, w)
            self._bind_row_click(w, idx)

            self._items[label.lower()] = item
            self._item_widgets[label.lower()] = w

        self.menu.setCurrentRow(0)
        layout.addWidget(self.menu, 1)
        layout.addStretch(0)

        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        self._footer_frame = footer
        footer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(12, 12, 12, 12)
        f_layout.setSpacing(10)

        self._footer_avatar = QLabel()
        self._footer_avatar.setObjectName("sidebarAvatar")
        self._footer_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer_avatar.setFixedSize(36, 36)
        self._refresh_footer_avatar()

        text_col_wrap = QWidget()
        self._footer_text_wrap = text_col_wrap
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

        f_layout.addWidget(self._footer_avatar)
        f_layout.addWidget(text_col_wrap, 1)
        f_layout.addWidget(btn_menu)

        layout.addWidget(footer)
        self._bind_footer_click()

    def _set_toggle_logo_icon(self):
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

        icon = get_feather_icon("menu", 18, color=self.ICON_TINT)
        if not icon.isNull():
            self.btn_toggle.setIcon(icon)

    def _resolve_menu_items(self) -> List[Tuple[str, str]]:
        if self.role == "admin":
            return [
                ("Dashboard", "home"),
                ("Inventory", "archive"),
                ("Point of Sale", "shopping-cart"),
                ("Sales", "sales"),
                ("Alerts", "alert-triangle"),
                ("Reports", "bar-chart-2"),
                ("Administration", "settings"),
                ("Activity", "activity"),
                ("Profile", "user"),
            ]

        if self.role == "manager":
            return [
                ("Dashboard", "home"),
                ("Inventory", "archive"),
                ("Point of Sale", "shopping-cart"),
                ("Sales", "sales"),
                ("Alerts", "alert-triangle"),
                ("Reports", "bar-chart-2"),
                ("Profile", "user"),
            ]

        return [
            ("Dashboard", "home"),
            ("Inventory", "archive"),
            ("Point of Sale", "shopping-cart"),
            ("Profile", "user"),
        ]

    def toggle_collapsed(self):
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, value: bool):
        self._collapsed = bool(value)
        self.setFixedWidth(self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH)

        for w in self._label_widgets:
            if w is not None:
                w.setVisible(not self._collapsed)

        for _, w in self._item_widgets.items():
            w.set_collapsed(self._collapsed)

        if self._btn_footer_menu:
            self._btn_footer_menu.setVisible(not self._collapsed)

        if self._footer_frame:
            self._footer_frame.setToolTip("Profile")

    def is_collapsed(self) -> bool:
        return self._collapsed

    def _sync_selected_state(self):
        current = self.menu.currentRow()
        for i in range(self.menu.count()):
            it = self.menu.item(i)
            if not it:
                continue
            label = (it.data(Qt.ItemDataRole.UserRole) or "").strip().lower()
            w = self._item_widgets.get(label)
            if w:
                w.set_selected(i == current)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget#sidebar {
                background: #FFFFFF;
                border-right: 1px solid #E6EAF3;
            }

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

            QListWidget#sidebarMenu {
                border: none;
                outline: none;
                background: transparent;
            }

            QWidget#sidebarItem {
                border-radius: 12px;
                background: transparent;
            }

            QWidget#sidebarItem:hover {
                background: #EEF3FF;
            }

            QWidget#sidebarItem[selected="true"] {
                background: #0A2A83;
            }

            QLabel#sidebarItemText {
                font-size: 14px;
                font-weight: 700;
                color: #23324D;
                background: transparent;
            }

            /* ✅ fix: text color driven directly by label's own selected property */
            QLabel#sidebarItemText[selected="true"] {
                color: #FFFFFF;
            }

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

    def _derive_initials(self, name: str):
        parts = (name or "").strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return (name or "U")[:2].upper()

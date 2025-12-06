# desktop_app/utils/icons.py
import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt

try:
    from desktop_app.utils.config import AppConfig
    _ICONS_DIR = getattr(
        AppConfig,
        "ICONS_DIR",
        os.path.join(os.path.dirname(__file__), "..", "assets", "icons"),
    )
except Exception:
    _ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")


def _icon_path(name: str):
    png = os.path.join(_ICONS_DIR, f"{name}.png")
    svg = os.path.join(_ICONS_DIR, f"{name}.svg")
    return png, svg


def get_icon(icon_name: str, size: int = 24, color: str | None = None) -> QIcon:
    """
    Generic icon loader.

    - Tries PNG first
    - Then tries SVG (optionally tinting stroke="currentColor")
    - On failure: returns empty QIcon WITHOUT printing warnings
    """
    png, svg = _icon_path(icon_name)

    if os.path.exists(png):
        icon = QIcon(png)
        if size != 24:
            return QIcon(icon.pixmap(size, size))
        return icon

    if os.path.exists(svg):
        try:
            with open(svg, "r", encoding="utf-8") as f:
                svg_text = f.read()
            if color:
                svg_text = svg_text.replace('stroke="currentColor"', f'stroke="{color}"')
            renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            renderer.render(painter)
            painter.end()
            return QIcon(pix)
        except Exception:
            return QIcon(svg)

    # Silent fallback
    return QIcon()

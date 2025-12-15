# desktop_app/utils/icons.py

import os
from typing import Optional

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
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


def _tint_pixmap(pix: QPixmap, color: str) -> QPixmap:
    """
    Tint a pixmap with a solid color.
    Works best for monochrome icons.
    """
    if pix.isNull():
        return pix

    tinted = QPixmap(pix.size())
    tinted.fill(Qt.GlobalColor.transparent)

    painter = QPainter(tinted)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawPixmap(0, 0, pix)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(color))
    painter.end()

    return tinted


def get_icon(icon_name: str, size: int = 24, color: Optional[str] = None) -> QIcon:
    """
    Generic icon loader.

    - Tries PNG first (optionally tinted)
    - Then tries SVG (optionally stroke/fill tinted)
    - Silent fallback on failure
    """
    png, svg = _icon_path(icon_name)

    # ---------------------------
    # PNG
    # ---------------------------
    if os.path.exists(png):
        try:
            pix = QPixmap(png)
            if not pix.isNull():
                if size:
                    pix = pix.scaled(
                        size, size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                if color:
                    pix = _tint_pixmap(pix, color)

                return QIcon(pix)
        except Exception:
            return QIcon(png)

    # ---------------------------
    # SVG
    # ---------------------------
    if os.path.exists(svg):
        try:
            with open(svg, "r", encoding="utf-8") as f:
                svg_text = f.read()

            if color:
                svg_text = svg_text.replace('stroke="currentColor"', f'stroke="{color}"')
                svg_text = svg_text.replace('fill="currentColor"', f'fill="{color}"')

            renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pix)
            renderer.render(painter)
            painter.end()

            return QIcon(pix)
        except Exception:
            return QIcon(svg)

    return QIcon()

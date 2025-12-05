# desktop_app/utils/icons.py
import os
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QPainter

from utils.config import AppConfig

def get_icon(icon_name: str, size: int = 24, color: str = None) -> QIcon:
    icons_dir = AppConfig.ICONS_DIR if hasattr(AppConfig, "ICONS_DIR") else os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
    png = os.path.join(icons_dir, f"{icon_name}.png")
    svg = os.path.join(icons_dir, f"{icon_name}.svg")
    if os.path.exists(png):
        icon = QIcon(png)
        if size != 24:
            return QIcon(icon.pixmap(size, size))
        return icon
    if os.path.exists(svg):
        # render svg to pixmap
        try:
            with open(svg, 'r', encoding='utf-8') as f:
                svg_text = f.read()
            if color:
                svg_text = svg_text.replace('stroke="currentColor"', f'stroke="{color}"')
            renderer = QSvgRenderer(QByteArray(svg_text.encode('utf-8')))
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(pix)
            renderer.render(p)
            p.end()
            return QIcon(pix)
        except Exception:
            return QIcon(svg)
    # fallback
    return QIcon()

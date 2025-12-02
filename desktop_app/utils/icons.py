# icons.py
#
# This module provides utility functions for loading and manipulating icons, specifically
# Feather icons from the assets/icons directory. It handles SVG and PNG icons with
# optional color manipulation.
#
# Usage: Imported by UI modules that need to display icons with consistent styling.

import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtSvg import QSvgRenderer
from utils.config import AppConfig


# Cache for loaded icons to improve performance
_icon_cache = {}


def get_icon(icon_name: str, color: str = None, size: int = 24) -> QIcon:
    """
    Load an icon from the assets/icons directory and optionally apply a color.
    Supports both PNG and SVG formats, with SVG color manipulation.
    
    Args:
        icon_name: Name of the icon file without extension (e.g., "user", "trash-2")
        color: Optional color string (e.g., "#FF0000", "white") to apply to SVG icons
        size: Desired size of the icon in pixels
        
    Returns:
        QIcon: The loaded QIcon object, or empty QIcon if not found
    """
    # Create cache key
    cache_key = f"{icon_name}_{color}_{size}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    
    icon_path_png = os.path.join(AppConfig.ICONS_DIR, f"{icon_name}.png")
    icon_path_svg = os.path.join(AppConfig.ICONS_DIR, f"{icon_name}.svg")
    
    # Try PNG first (faster rendering)
    if os.path.exists(icon_path_png):
        icon = QIcon(icon_path_png)
        if size != 24:
            pixmap = icon.pixmap(size, size)
            icon = QIcon(pixmap)
        _icon_cache[cache_key] = icon
        return icon
    
    # Fallback to SVG
    elif os.path.exists(icon_path_svg):
        icon = _load_svg_icon(icon_path_svg, color, size)
        if icon:
            _icon_cache[cache_key] = icon
            return icon
    
    # Icon not found
    print(f"Warning: Icon '{icon_name}' not found in {AppConfig.ICONS_DIR}")
    return QIcon()


def _load_svg_icon(svg_path: str, color: str = None, size: int = 24) -> QIcon:
    """
    Load and optionally colorize an SVG icon.
    
    Args:
        svg_path: Path to the SVG file
        color: Optional color to apply
        size: Desired icon size
        
    Returns:
        QIcon: The loaded and processed icon
    """
    try:
        # Read SVG content
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Apply color if specified
        if color:
            # Replace stroke and fill colors with the specified color
            # Common patterns in Feather icons
            svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')
            svg_content = svg_content.replace('stroke="#000"', f'stroke="{color}"')
            svg_content = svg_content.replace('stroke="#000000"', f'stroke="{color}"')
            svg_content = svg_content.replace('fill="currentColor"', f'fill="{color}"')
            svg_content = svg_content.replace('fill="#000"', f'fill="{color}"')
            svg_content = svg_content.replace('fill="#000000"', f'fill="{color}"')
        
        # Render SVG to pixmap
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    except Exception as e:
        print(f"Error loading SVG icon {svg_path}: {e}")
        # Fallback: try loading as regular icon
        return QIcon(svg_path)


def get_feather_icon(icon_name: str, color: str = None, size: int = 24) -> QIcon:
    """
    Alias for get_icon() for backward compatibility and clarity.
    Specifically loads Feather icons from the assets/icons directory.
    
    Args:
        icon_name: Name of the Feather icon without extension
        color: Optional color to apply
        size: Desired icon size in pixels
        
    Returns:
        QIcon: The loaded icon
    """
    return get_icon(icon_name, color, size)


def preload_common_icons(size: int = 24):
    """
    Preload commonly used icons into the cache for better performance.
    
    Args:
        size: Size for the preloaded icons
    """
    common_icons = [
        "home", "package", "dollar-sign", "users", "settings", "log-out",
        "plus", "edit", "trash-2", "search", "filter", "calendar",
        "chevron-down", "chevron-up", "chevron-left", "chevron-right",
        "x", "check", "alert-circle", "info", "check-circle", "x-circle",
        "user", "bell", "menu", "grid", "list", "download", "upload",
        "image", "file-text", "pie-chart", "bar-chart", "trending-up"
    ]
    
    for icon_name in common_icons:
        get_icon(icon_name, None, size)


def clear_icon_cache():
    """Clear the icon cache to free memory."""
    global _icon_cache
    _icon_cache.clear()


def get_icon_list() -> list:
    """
    Get a list of all available icons in the icons directory.
    
    Returns:
        List of icon names (without extension)
    """
    icons = []
    if os.path.exists(AppConfig.ICONS_DIR):
        for filename in os.listdir(AppConfig.ICONS_DIR):
            if filename.endswith(('.svg', '.png')):
                icon_name = os.path.splitext(filename)[0]
                if icon_name not in icons:
                    icons.append(icon_name)
    return sorted(icons)


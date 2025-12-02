# helpers.py
#
# This module provides various utility functions for the application, primarily focused on
# UI formatting, currency, dates, text manipulation, and image handling.
#
# Usage: Imported by UI modules to handle common formatting and utility tasks.

import os
import locale
from datetime import datetime
from typing import Optional
from PyQt6.QtGui import QPixmap, QImage, QPainter, QFont, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from utils.config import AppConfig


def format_currency(amount: float, symbol: Optional[str] = None) -> str:
    """
    Format a number as currency with proper locale formatting.
    
    Args:
        amount: The amount to format
        symbol: Optional currency symbol (defaults to AppConfig.CURRENCY_SYMBOL)
        
    Returns:
        Formatted currency string (e.g., "₱1,234.50")
    """
    if symbol is None:
        symbol = AppConfig.CURRENCY_SYMBOL
    
    try:
        # Try to use locale-specific formatting
        locale.setlocale(locale.LC_ALL, AppConfig.CURRENCY_LOCALE)
        formatted = locale.currency(amount, grouping=True, symbol=False)
        return f"{symbol}{formatted}"
    except (locale.Error, ValueError):
        # Fallback to manual formatting
        return f"{symbol}{amount:,.2f}"


def format_date(date_value, format_str: Optional[str] = None) -> str:
    """
    Format a date value as a string.
    
    Args:
        date_value: Date string, datetime object, or QDate object
        format_str: Optional format string (defaults to DISPLAY_DATE_FORMAT)
        
    Returns:
        Formatted date string
    """
    if format_str is None:
        format_str = AppConfig.DISPLAY_DATE_FORMAT
    
    # Handle different input types
    if isinstance(date_value, str):
        # Try to parse common formats
        for fmt in [AppConfig.DATE_FORMAT, AppConfig.DATETIME_FORMAT, "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(date_value.split()[0], fmt.split()[0])
                return dt.strftime(format_str)
            except (ValueError, IndexError):
                continue
        return date_value  # Return as-is if parsing fails
    
    elif hasattr(date_value, 'strftime'):
        # datetime object
        return date_value.strftime(format_str)
    elif hasattr(date_value, 'toString'):
        # QDate object
        return date_value.toString(format_str)
    
    return str(date_value)


def format_datetime(datetime_value, format_str: Optional[str] = None) -> str:
    """
    Format a datetime value as a string with time.
    
    Args:
        datetime_value: Datetime string or datetime object
        format_str: Optional format string
        
    Returns:
        Formatted datetime string
    """
    if format_str is None:
        format_str = f"{AppConfig.DISPLAY_DATE_FORMAT} {AppConfig.DISPLAY_TIME_FORMAT}"
    
    return format_date(datetime_value, format_str)


def shorten_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Shorten text to a maximum length with ellipsis.
    
    Args:
        text: The text to shorten
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated (default: "...")
        
    Returns:
        Shortened text string
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def humanize_quantity(quantity: float) -> str:
    """
    Convert large numbers to human-readable format (K, M, etc.).
    
    Args:
        quantity: The quantity to humanize
        
    Returns:
        Humanized string (e.g., "1.0K", "2.5M")
    """
    if quantity < 1000:
        return str(int(quantity))
    elif quantity < 1000000:
        return f"{quantity / 1000:.1f}K"
    elif quantity < 1000000000:
        return f"{quantity / 1000000:.1f}M"
    else:
        return f"{quantity / 1000000000:.1f}B"


def get_feather_icon(icon_name: str, color: Optional[str] = None, size: int = 24):
    """
    Returns a QIcon by loading a PNG or SVG from the assets/icons/ directory.
    Attempts to load .png first, then .svg if .png is not found.
    
    Args:
        icon_name: Name of the icon file without extension (e.g., "user", "plus-circle")
        color: Optional color to apply to SVG icons
        size: Desired size of the icon in pixels
        
    Returns:
        QIcon: Icon object ready to use, or empty QIcon if not found
    """
    from PyQt6.QtGui import QIcon
    
    icon_path_png = os.path.join(AppConfig.ICONS_DIR, f"{icon_name}.png")
    icon_path_svg = os.path.join(AppConfig.ICONS_DIR, f"{icon_name}.svg")
    
    # Prioritize PNG if it exists
    if os.path.exists(icon_path_png):
        icon = QIcon(icon_path_png)
        if size != 24:
            # Return pixmap at specific size
            pixmap = icon.pixmap(size, size)
            return QIcon(pixmap)
        return icon
    
    # Fallback to SVG
    elif os.path.exists(icon_path_svg):
        icon = QIcon(icon_path_svg)
        if size != 24:
            pixmap = icon.pixmap(size, size)
            return QIcon(pixmap)
        return icon
    else:
        print(f"Warning: Icon '{icon_name}' not found in {AppConfig.ICONS_DIR}. Returning empty QIcon.")
        return QIcon()


def load_product_image(image_path: Optional[str], target_size: tuple = (150, 150), 
                       keep_aspect_ratio: bool = True) -> QPixmap:
    """
    Load a product image from path and scale it to target size.
    If the image cannot be loaded, returns a placeholder QPixmap.
    
    Args:
        image_path: Path to the image file (absolute or relative)
        target_size: Tuple of (width, height) for the scaled QPixmap
        keep_aspect_ratio: Whether to maintain aspect ratio while scaling
        
    Returns:
        QPixmap: The scaled QPixmap or placeholder
    """
    placeholder_path = os.path.join(AppConfig.IMAGES_DIR, "no-image.png")
    
    if image_path and os.path.exists(image_path):
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                if keep_aspect_ratio:
                    return pixmap.scaled(
                        target_size[0], target_size[1],
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    return pixmap.scaled(
                        target_size[0], target_size[1],
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
    
    # Generate placeholder
    placeholder_pixmap = QPixmap(target_size[0], target_size[1])
    placeholder_pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(placeholder_pixmap)
    text_color = QColor(AppConfig.TEXT_COLOR)
    font_name = AppConfig.FONT_FAMILY.split(',')[0].strip()
    
    painter.setPen(text_color)
    painter.setFont(QFont(font_name, 8))
    
    # Draw border
    painter.setPen(Qt.GlobalColor.gray)
    painter.drawRect(0, 0, target_size[0] - 1, target_size[1] - 1)
    
    # Draw text
    painter.setPen(QColor(AppConfig.TEXT_COLOR))
    painter.drawText(placeholder_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No Image")
    
    painter.end()
    return placeholder_pixmap


def save_product_image(source_path: str) -> Optional[str]:
    """
    Save a product image from source path to the product images directory.
    Generates a unique filename using UUID to prevent conflicts.
    
    Args:
        source_path: Absolute or relative path to the source image file
        
    Returns:
        Relative path to the saved image file, or None if saving fails
    """
    import shutil
    import uuid
    
    if not source_path:
        return None
    
    os.makedirs(AppConfig.PRODUCT_IMAGE_DIR, exist_ok=True)
    
    file_extension = os.path.splitext(source_path)[1].lower()
    if not file_extension:
        QMessageBox.warning(None, "Image Error", "Could not determine file extension for the image.")
        return None
    
    if file_extension and not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    if file_extension not in valid_extensions:
        QMessageBox.warning(None, "Image Error", 
                          f"Unsupported image format: {file_extension}. Please use JPG, PNG, GIF, BMP, or WEBP.")
        return None
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    destination_path = os.path.join(AppConfig.PRODUCT_IMAGE_DIR, unique_filename)
    
    try:
        shutil.copy(source_path, destination_path)
        print(f"Image saved: {destination_path}")
        return os.path.relpath(destination_path, start=os.getcwd())
    except Exception as e:
        QMessageBox.critical(None, "Image Save Error", f"Failed to save image: {e}")
        return None


def delete_product_image(relative_path: Optional[str]):
    """
    Delete a product image file given its relative path.
    
    Args:
        relative_path: Relative path to the image file to delete
    """
    if not relative_path:
        return
    
    full_path = os.path.join(os.getcwd(), relative_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
            print(f"Deleted image: {full_path}")
        except Exception as e:
            print(f"Error deleting image {full_path}: {e}")
    else:
        print(f"Image not found for deletion: {full_path}")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage with safe division.
    
    Args:
        part: The part value
        total: The total value
        
    Returns:
        Percentage as float (0-100)
    """
    if total == 0:
        return 0.0
    return (part / total) * 100


def get_stock_status_label(stock: int, min_stock_level: int) -> tuple[str, str]:
    """
    Determine stock status label and CSS class based on stock levels.
    
    Args:
        stock: Current stock quantity
        min_stock_level: Minimum stock level threshold
        
    Returns:
        Tuple of (status_text, status_class)
    """
    if stock <= 0:
        return ("No Stock", "status-no-stock")
    elif stock <= min_stock_level:
        return ("Low Stock", "status-low-stock")
    else:
        return ("In Stock", "status-in-stock")


def truncate_middle(text: str, max_length: int) -> str:
    """
    Truncate text from the middle, keeping beginning and end visible.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of result
        
    Returns:
        Truncated text (e.g., "Very lo...name")
    """
    if len(text) <= max_length:
        return text
    
    part_length = (max_length - 3) // 2
    return f"{text[:part_length]}...{text[-part_length:]}"


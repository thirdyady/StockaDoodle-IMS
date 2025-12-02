# config.py
#
# This module defines the AppConfig class, which centralizes application-wide configurations.
# It includes color schemes for UI theming, font settings, API URLs, and file paths.
# Access these settings via AppConfig.PROPERTY_NAME.
#
# Usage: Imported by UI modules for consistent styling and by API modules for endpoint configuration.

import os


class AppConfig:
    """
    Centralized configuration class for the StockaDoodle IMS application.
    Stores UI theme colors, font settings, API configuration, and file paths.
    """
    
    # --- API Configuration ---
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000/api/v1")
    API_TIMEOUT = 30  # Request timeout in seconds
    
    # --- General Colors ---
    # Used for main backgrounds, sidebars, cards, inputs, and borders.
    BACKGROUND_COLOR = "#1E293B"  # Slate-800 for main backgrounds
    DARK_BACKGROUND = "#0F172A"   # Slate-900 for sidebars/headers
    CARD_BACKGROUND = "#334155"   # Slate-700 for cards/panels
    INPUT_BACKGROUND = "#475569"  # Slate-600 for input fields
    BORDER_COLOR = "#64748B"      # Slate-500 for borders
    
    # --- Text Colors ---
    # For general text, titles, and secondary text on dark backgrounds.
    TEXT_COLOR = "#F1F5F9"        # Slate-100 for general text
    LIGHT_TEXT = "#FFFFFF"        # Pure white for titles, important text
    TEXT_COLOR_ALT = "#CBD5E1"    # Slate-300 for secondary text
    TEXT_COLOR_MUTED = "#94A3B8"  # Slate-400 for muted text
    
    # --- Accent Colors ---
    # Used for primary actions, success/error indicators, and warnings.
    PRIMARY_COLOR = "#6C5CE7"     # Vibrant purple/blue for main actions, highlights
    PRIMARY_HOVER = "#5A4FCF"     # Darker purple on hover
    SECONDARY_COLOR = "#00B894"   # Teal/green for success, positive indicators
    ACCENT_COLOR = "#D63031"      # Red for errors, critical alerts
    WARNING_COLOR = "#FDCB6E"     # Yellow/orange for warnings, low stock
    INFO_COLOR = "#0984E3"        # Blue for informational messages
    
    # --- Specific Card Colors (for Dashboards) ---
    SALES_CARD_COLOR = "#FFA502"  # Orange/Gold for sales
    PRODUCTS_CARD_COLOR = "#2ED573" # Green for products
    USERS_CARD_COLOR = "#1E90FF"  # Blue for users
    LOW_STOCK_CARD_COLOR = "#FF6B6B" # Light Red for low stock
    EXPIRING_CARD_COLOR = "#A55EEA" # Purple for expiring items
    DISPOSAL_CARD_COLOR = "#FF7675" # Coral for disposal reports
    
    # --- Font Configuration ---
    # Defines font family and various sizes for consistent typography.
    FONT_FAMILY = "Inter"  # Modern sans-serif font
    FONT_SIZE_XSMALL = 8
    FONT_SIZE_SMALL = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_MEDIUM = 12
    FONT_SIZE_LARGE = 14
    FONT_SIZE_XLARGE = 18
    FONT_SIZE_XXLARGE = 24
    FONT_SIZE_HERO = 32
    
    # --- MFA Configuration ---
    # Parameters for Multi-Factor Authentication code generation and expiry.
    MFA_CODE_LENGTH = 6  # Length of the MFA verification code
    MFA_CODE_EXPIRY_MINUTES = 5  # MFA code expires after this many minutes
    MFA_CODE_EXPIRY_SECONDS = MFA_CODE_EXPIRY_MINUTES * 60
    
    # --- File Paths ---
    # Defines directories for assets and data storage.
    ASSETS_DIR = "assets"
    ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
    IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
    PRODUCT_IMAGE_DIR = os.path.join(ASSETS_DIR, "product_images")
    FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
    
    # --- UI Configuration ---
    SIDEBAR_WIDTH = 250  # Width of the sidebar in pixels
    SIDEBAR_COLLAPSED_WIDTH = 70  # Width when collapsed
    HEADER_HEIGHT = 60  # Height of header bar in pixels
    CARD_RADIUS = 12  # Border radius for cards
    BUTTON_RADIUS = 8  # Border radius for buttons
    INPUT_RADIUS = 6  # Border radius for inputs
    
    # --- Animation Configuration ---
    ANIMATION_DURATION = 200  # Duration in milliseconds for transitions
    HOVER_TRANSITION = "all 0.2s ease"
    
    # --- Table Configuration ---
    TABLE_ROW_HEIGHT = 50  # Default row height for tables
    TABLE_HEADER_HEIGHT = 45  # Default header height for tables
    
    # --- Notification Configuration ---
    NOTIFICATION_TIMEOUT = 3000  # Auto-dismiss timeout in milliseconds
    NOTIFICATION_POSITION = "top-right"  # Position on screen
    
    # --- Pagination Configuration ---
    ITEMS_PER_PAGE = 20  # Default items per page
    
    # --- Currency Configuration ---
    CURRENCY_SYMBOL = "₱"  # Philippine Peso
    CURRENCY_LOCALE = "en_PH"  # Locale for currency formatting
    
    # --- Date/Time Configuration ---
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DISPLAY_DATE_FORMAT = "%b %d, %Y"  # e.g., "Dec 01, 2025"
    DISPLAY_TIME_FORMAT = "%I:%M %p"  # e.g., "02:30 PM"
    
    # --- Validation Configuration ---
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50
    
    # --- Stock Configuration ---
    DEFAULT_MIN_STOCK_LEVEL = 5  # Default minimum stock level
    LOW_STOCK_THRESHOLD_MULTIPLIER = 1.0  # Multiplier for low stock (1.0x min level)
    
    # --- Window Configuration ---
    WINDOW_MIN_WIDTH = 1280
    WINDOW_MIN_HEIGHT = 720
    WINDOW_DEFAULT_WIDTH = 1440
    WINDOW_DEFAULT_HEIGHT = 900
    
    # Ensure the product image directory exists upon class definition.
    os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


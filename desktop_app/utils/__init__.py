# __init__.py
#
# This module exports all utility functions and classes for easy importing.
# Usage: from utils import AppConfig, format_currency, success, etc.

# Configuration
from utils.config import AppConfig

# Styles
from utils.styles import (
    get_global_stylesheet,
    get_dashboard_card_style,
    get_product_card_style,
    get_category_card_style,
    get_dialog_style,
    get_header_bar_style,
    get_title_bar_style,
    get_loading_spinner_style,
    get_modern_card_style,
    get_badge_style,
    apply_table_styles
)

# Helpers
from utils.helpers import (
    format_currency,
    format_date,
    format_datetime,
    shorten_text,
    humanize_quantity,
    get_feather_icon,
    load_product_image,
    save_product_image,
    delete_product_image,
    format_file_size,
    calculate_percentage,
    get_stock_status_label,
    truncate_middle
)

# Icons
from utils.icons import (
    get_icon,
    get_feather_icon as get_feather_icon_from_icons,
    preload_common_icons,
    clear_icon_cache,
    get_icon_list
)

# Notifications
from utils.notifications import (
    show_notification,
    success,
    error,
    warning,
    info,
    ToastNotification
)

# Validators
from utils.validators import (
    validate_quantity,
    validate_price,
    validate_email,
    validate_password,
    validate_username,
    validate_product_name,
    validate_brand,
    validate_min_stock_level,
    validate_date_string,
    validate_not_empty,
    validate_length,
    validate_disposal_reason,
    validate_phone_number
)

# Animations
from utils.animations import (
    fade_in,
    fade_out,
    slide_in,
    slide_out,
    scale_up,
    pulse,
    setup_card_hover_effect,
    animate_page_transition,
    setup_button_press_effect
)

# API Wrapper
from utils.api_wrapper import (
    get_api,
    set_api,
    reset_api,
    login,
    logout,
    get_products,
    get_product,
    create_product,
    update_product,
    delete_product,
    get_stock_batches,
    add_stock_batch,
    dispose_product,
    record_sale,
    get_sales,
    get_categories,
    get_product_logs,
    get_current_user_data,
    verify_mfa
)

# App State
from utils.app_state import (
    get_app_state,
    get_current_user,
    set_current_user,
    get_api_client,
    set_api_client,
    is_dark_mode,
    set_dark_mode,
    get_selected_product_id,
    set_selected_product_id,
    get_selected_category_id,
    set_selected_category_id,
    clear_app_state
)

__all__ = [
    # Config
    'AppConfig',
    
    # Styles
    'get_global_stylesheet',
    'get_dashboard_card_style',
    'get_product_card_style',
    'get_category_card_style',
    'get_dialog_style',
    'get_header_bar_style',
    'get_title_bar_style',
    'get_loading_spinner_style',
    'get_modern_card_style',
    'get_badge_style',
    'apply_table_styles',
    
    # Helpers
    'format_currency',
    'format_date',
    'format_datetime',
    'shorten_text',
    'humanize_quantity',
    'get_feather_icon',
    'load_product_image',
    'save_product_image',
    'delete_product_image',
    'format_file_size',
    'calculate_percentage',
    'get_stock_status_label',
    'truncate_middle',
    
    # Icons
    'get_icon',
    'preload_common_icons',
    'clear_icon_cache',
    'get_icon_list',
    
    # Notifications
    'show_notification',
    'success',
    'error',
    'warning',
    'info',
    'ToastNotification',
    
    # Validators
    'validate_quantity',
    'validate_price',
    'validate_email',
    'validate_password',
    'validate_username',
    'validate_product_name',
    'validate_brand',
    'validate_min_stock_level',
    'validate_date_string',
    'validate_not_empty',
    'validate_length',
    'validate_disposal_reason',
    'validate_phone_number',
    
    # Animations
    'fade_in',
    'fade_out',
    'slide_in',
    'slide_out',
    'scale_up',
    'pulse',
    'setup_card_hover_effect',
    'animate_page_transition',
    'setup_button_press_effect',
    
    # API Wrapper
    'get_api',
    'set_api',
    'reset_api',
    'login',
    'logout',
    'get_products',
    'get_product',
    'create_product',
    'update_product',
    'delete_product',
    'get_stock_batches',
    'add_stock_batch',
    'dispose_product',
    'record_sale',
    'get_sales',
    'get_categories',
    'get_product_logs',
    'get_current_user_data',
    'verify_mfa',
    
    # App State
    'get_app_state',
    'get_current_user',
    'set_current_user',
    'get_api_client',
    'set_api_client',
    'is_dark_mode',
    'set_dark_mode',
    'get_selected_product_id',
    'set_selected_product_id',
    'get_selected_category_id',
    'set_selected_category_id',
    'clear_app_state',
]


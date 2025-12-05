from flask import request
from datetime import datetime
import base64

def parse_date(value):
    """Convert string to date — accepts YYYY-MM-DD or ISO format"""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def get_image_binary():
    """
    Extract image binary data from:
    - multipart/form-data → file upload (field name: 'image')
    - JSON or form-data → binary data (field name: 'image_data')
    Returns bytes or None
    """
    # 1. File upload
    if "image" in request.files and request.files["image"].filename:
        file = request.files["image"]
        return file.read()

    # 2. Binary data from JSON or form
    raw = (
        request.form.get("image_data") or
        (request.get_json(silent=True) or {}).get("image_data")
    )
    if raw:
        # If it's already bytes, return as-is
        if isinstance(raw, bytes):
            return raw
        # If it's a string representation, try to decode
        try:
            return raw.encode('latin1') if isinstance(raw, str) else None
        except Exception:
            return None
    return None


def extract_int(value, default=None):
    """Safely convert value to int, return default on failure"""
    try:
        return int(value) if value is not None and value != "" else default
    except (TypeError, ValueError):
        return default
    
def sanitize_string(value, max_length=None):
    """
    Sanitize string input for MongoDB
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
    """
    if not value:
        return ""
    
    # Convert to string and strip whitespace
    sanitized = str(value).strip()
    
    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_email(email):
    """
    Basic email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid format
    """
    import re
    
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_currency(amount):
    """
    Format amount as currency string
    
    Args:
        amount: Numeric amount
        
    Returns:
        str: Formatted currency (e.g., "$1,234.56")
    """
    try:
        return f"${float(amount):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def calculate_percentage(part, whole):
    """
    Calculate percentage safely
    
    Args:
        part: Part value
        whole: Whole value
        
    Returns:
        float: Percentage (0-100)
    """
    try:
        if whole == 0:
            return 0.0
        return (float(part) / float(whole)) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def truncate_text(text, max_length=50, suffix="..."):
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_request_data():
    """
    Get request data from JSON or form data
    
    Returns:
        dict: Request data
    """
    if request.content_type and 'multipart/form-data' in request.content_type:
        return request.form.to_dict()
    return request.get_json(silent=True) or {}


def build_mongo_filter(filters_dict):
    """
    Build MongoDB filter query from dictionary
    
    Args:
        filters_dict: Dictionary of field: value pairs
        
    Returns:
        dict: MongoDB filter query
    """
    mongo_filter = {}
    
    for key, value in filters_dict.items():
        if value is not None and value != "":
            # Handle case-insensitive string matching
            if isinstance(value, str):
                mongo_filter[key + "__icontains"] = value
            else:
                mongo_filter[key] = value
    
    return mongo_filter
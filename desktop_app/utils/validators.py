# desktop_app/utils/validators.py
#
# Form validation functions.

import re
from typing import Tuple, Optional
from datetime import datetime

from desktop_app.utils.config import AppConfig


ValidationResult = Tuple[bool, Optional[str]]


def validate_quantity(value: str) -> ValidationResult:
    if not value or not value.strip():
        return False, "Quantity cannot be empty"

    try:
        qty = int(value.strip())
        if qty < 0:
            return False, "Quantity must be a positive number"
        if qty > 999999:
            return False, "Quantity is too large (max: 999,999)"
        return True, None
    except ValueError:
        return False, "Quantity must be a whole number"


def validate_price(value: str) -> ValidationResult:
    if not value or not value.strip():
        return False, "Price cannot be empty"

    try:
        price = float(value.strip())
        if price < 0:
            return False, "Price must be a positive number"
        if price > 999999.99:
            return False, "Price is too large (max: ₱999,999.99)"
        if price == 0:
            return False, "Price must be greater than zero"
        return True, None
    except ValueError:
        return False, "Price must be a valid number"


def validate_email(email: str) -> ValidationResult:
    if not email or not email.strip():
        return False, "Email cannot be empty"

    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "Please enter a valid email address"

    if len(email) > 255:
        return False, "Email address is too long"

    return True, None


def validate_password(password: str, is_new: bool = True) -> ValidationResult:
    if not password:
        if is_new:
            return False, "Password cannot be empty"
        return True, None

    if is_new:
        if len(password) < AppConfig.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AppConfig.MIN_PASSWORD_LENGTH} characters long"

        if len(password) > AppConfig.MAX_PASSWORD_LENGTH:
            return False, f"Password must be no more than {AppConfig.MAX_PASSWORD_LENGTH} characters"

        has_letter = re.search(r'[a-zA-Z]', password)
        has_number = re.search(r'\d', password)

        if not has_letter:
            return False, "Password must contain at least one letter"

        if not has_number:
            return False, "Password must contain at least one number"

    return True, None


def validate_username(username: str) -> ValidationResult:
    if not username or not username.strip():
        return False, "Username cannot be empty"

    username = username.strip()

    if len(username) < AppConfig.MIN_USERNAME_LENGTH:
        return False, f"Username must be at least {AppConfig.MIN_USERNAME_LENGTH} characters long"

    if len(username) > AppConfig.MAX_USERNAME_LENGTH:
        return False, f"Username must be no more than {AppConfig.MAX_USERNAME_LENGTH} characters"

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, None


def validate_product_name(name: str) -> ValidationResult:
    if not name or not name.strip():
        return False, "Product name cannot be empty"

    name = name.strip()

    if len(name) < 2:
        return False, "Product name must be at least 2 characters long"

    if len(name) > 100:
        return False, "Product name is too long (max: 100 characters)"

    return True, None


def validate_brand(brand: str) -> ValidationResult:
    if not brand or not brand.strip():
        return False, "Brand cannot be empty"

    brand = brand.strip()

    if len(brand) > 50:
        return False, "Brand name is too long (max: 50 characters)"

    return True, None


def validate_min_stock_level(level: str) -> ValidationResult:
    if not level or not level.strip():
        return True, None

    try:
        min_level = int(level.strip())
        if min_level < 0:
            return False, "Minimum stock level cannot be negative"
        if min_level > 1000:
            return False, "Minimum stock level is too high (max: 1,000)"
        return True, None
    except ValueError:
        return False, "Minimum stock level must be a whole number"


def validate_date_string(date_str: str, format_str: str | None = None) -> ValidationResult:
    if not date_str or not date_str.strip():
        return True, None

    if format_str is None:
        format_str = AppConfig.DATE_FORMAT

    try:
        datetime.strptime(date_str.strip(), format_str)
        return True, None
    except ValueError:
        return False, f"Date must be in format: {format_str}"


def validate_not_empty(value: str, field_name: str = "Field") -> ValidationResult:
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty"
    return True, None


def validate_length(value: str, min_length: int = 0, max_length: int | None = None,
                    field_name: str = "Field") -> ValidationResult:
    if value is None:
        value = ""

    length = len(value.strip()) if isinstance(value, str) else 0

    if length < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"

    if max_length and length > max_length:
        return False, f"{field_name} must be no more than {max_length} characters long"

    return True, None


def validate_disposal_reason(reason: str) -> ValidationResult:
    if not reason or not reason.strip():
        return False, "Disposal reason cannot be empty"

    reason = reason.strip()

    if len(reason) < 5:
        return False, "Disposal reason must be at least 5 characters long"

    if len(reason) > 500:
        return False, "Disposal reason is too long (max: 500 characters)"

    return True, None


def validate_phone_number(phone: str) -> ValidationResult:
    if not phone or not phone.strip():
        return True, None

    phone = phone.strip()
    phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)

    if not phone_clean.isdigit():
        return False, "Phone number can only contain digits, spaces, hyphens, and parentheses"

    if len(phone_clean) < 7:
        return False, "Phone number is too short"

    if len(phone_clean) > 15:
        return False, "Phone number is too long"

    return True, None

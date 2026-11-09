"""
Helper functions for Polymarket Crypto Lab
"""
import uuid
from datetime import datetime
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
    
    Returns:
        Unique ID string
    """
    return f"{prefix}{uuid.uuid4()}"


def generate_uuid() -> str:
    """
    Generate a UUID string.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def timestamp() -> str:
    """
    Get current timestamp as ISO format string.
    
    Returns:
        ISO format timestamp
    """
    return datetime.utcnow().isoformat()


def format_price(price: float, decimals: int = 4) -> str:
    """
    Format a price for display.
    
    Args:
        price: Price value
        decimals: Number of decimal places
    
    Returns:
        Formatted price string
    """
    return f"{price:.{decimals}f}"


def format_pnl(pnl: float, currency: str = "pUSD") -> str:
    """
    Format PnL for display.
    
    Args:
        pnl: PnL value
        currency: Currency symbol
    
    Returns:
        Formatted PnL string with color
    """
    if pnl > 0:
        return f"+{pnl:.2f} {currency}"
    elif pnl < 0:
        return f"{pnl:.2f} {currency}"
    else:
        return f"0.00 {currency}"


def format_pct(value: float, decimals: int = 2) -> str:
    """
    Format a percentage value.
    
    Args:
        value: Percentage value (0-1 or 0-100)
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    if value > 1:
        return f"{value:.{decimals}f}%"
    else:
        return f"{value * 100:.{decimals}f}%"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is 0
    
    Returns:
        Result of division or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def slugify(text: str) -> str:
    """
    Convert text to a URL slug.
    
    Args:
        text: Text to convert
    
    Returns:
        URL slug
    """
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def parse_bool(value: Any, default: bool = False) -> bool:
    """
    Parse a boolean value from various types.
    
    Args:
        value: Value to parse
        default: Default value if parsing fails
    
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ('true', 'yes', '1', 'on'):
            return True
        elif value_lower in ('false', 'no', '0', 'off'):
            return False
    if isinstance(value, int):
        return value != 0
    return default


def get_nested_value(data: dict, keys: list, default: Any = None) -> Any:
    """
    Get a nested value from a dictionary.
    
    Args:
        data: Dictionary to search
        keys: List of keys to traverse
        default: Default value if key not found
    
    Returns:
        Value at the nested path or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

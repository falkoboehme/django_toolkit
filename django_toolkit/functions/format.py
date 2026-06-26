"""
Format conversion utilities for Django
"""
from django.utils.safestring import mark_safe


def django_format_to_python(django_format: str) -> str:
    """Convert Django format string to Python strftime format string"""
    replacements = {
        'Y': '%Y',  # 4-digit year
        'y': '%y',  # 2-digit year
        'm': '%m',  # Month as zero-padded decimal
        'n': '%-m', # Month as decimal (no padding) - Unix only
        'd': '%d',  # Day as zero-padded decimal
        'j': '%j',  # Day of year
        'H': '%H',  # Hour (24-hour, zero-padded)
        'h': '%I',  # Hour (12-hour, zero-padded)
        'i': '%M',  # Minute
        's': '%S',  # Second
        'A': '%p',  # AM/PM
    }
    
    result = django_format
    for django_char, python_char in replacements.items():
        result = result.replace(django_char, python_char)
    
    return result


def render_color_field(color_value: str, text: str = "") -> str:
    """
    Render a color value as a colored badge with optional text.
    
    Args:
        color_value: Hex color code (e.g., '#3f8cff')
        text: Optional text to display inside the badge
        
    Returns:
        HTML markup for a colored badge
        
    Examples:
        # Just color square
        render_color_field('#3f8cff')
        
        # Color badge with text
        render_color_field('#3f8cff', 'Strength')
    """
    if not color_value:
        return ""
    
    if text:
        # Badge with text inside
        return mark_safe(
            f'<span style="display:inline-block; background-color:{color_value}; padding:0.1rem 0.45rem; border-radius:4px; color:#fff; font-weight:500; text-shadow:0 1px 2px rgba(0,0,0,0.2); margin:0.1rem 0.2rem; font-size:0.85rem;">{text}</span>'
        )
    else:
        # Small color square without text
        return mark_safe(
            f'<span style="display:inline-block; background-color:{color_value}; width:20px; height:20px; border-radius:4px; border:1px solid #ddd; vertical-align:middle; margin-right:0.5rem;" title="{color_value}"></span>{color_value}'
        )

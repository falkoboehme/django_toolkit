"""
Format conversion utilities for Django
"""


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

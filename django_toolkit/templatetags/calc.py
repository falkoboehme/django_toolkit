from django import template

register = template.Library()

@register.filter
def modulo(num, val):
    return num % val


@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None
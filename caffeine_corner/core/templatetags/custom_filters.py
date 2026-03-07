from django import template
register = template.Library()

@register.filter
def to_int(value):
    return int(value)
@register.filter
def to_float(value):
    return float(value)

@register.filter
def to_str(value):
    return str(value)

@register.filter
def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes']
    return bool(value)
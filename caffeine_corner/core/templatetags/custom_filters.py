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

@register.filter
def add_variant_price(price, variant):
    if variant:
        return price + variant.additional_price
    return price

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
@property
def redeem_choices(self):
    """List of redeemable options para sa dropdown."""
    choices = []
    max_redeemable = self.redeemable_points
    step = 100
    for pts in range(step, max_redeemable + step, step):
        choices.append({
            'points':  pts,
            'discount': (pts // 100) * 10
        })
    return choices
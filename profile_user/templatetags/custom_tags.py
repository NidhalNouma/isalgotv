from django import template
from django.template.loader import render_to_string
import json
from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.simple_tag(takes_context=True)
def render_template(context, template_name, **kwargs):
    # Flatten the context and merge it with additional keyword arguments
    context_dict = context.flatten()
    full_context = {**context_dict, **kwargs}  # Merge the flattened context with kwargs
    return render_to_string(template_name, full_context)


@register.filter
def load_json(data):
    try:
        return json.loads(data.replace("'", "\""))
    except ValueError:
        return {}



@register.filter(name='abbrev')
def abbrev(value):
    """
    Abbreviates a number:
      1k for 1000, 1M for 1000000, etc.
    """
    try:
        n = float(value)
    except (ValueError, TypeError):
        return value

    if n < 1000:
        return str(int(n))
    elif n < 1000000:
        return f"{n/1000:.1f}k".rstrip('0').rstrip('.')
    elif n < 1000000000:
        return f"{n/1000000:.1f}M".rstrip('0').rstrip('.')
    elif n < 1000000000000:
        return f"{n/1000000000:.1f}B".rstrip('0').rstrip('.')
    else:
        return f"{n/1000000000000:.1f}T".rstrip('0').rstrip('.')

@register.filter(name='trim_zeros')
def trim_zeros(value):
    """
    Removes unnecessary trailing zeros from a decimal or float.
    E.g., 0.002000 -> "0.002", 2.5000 -> "2.5", 3.000 -> "3"
    """
    from decimal import Decimal, InvalidOperation
    try:
        d = Decimal(str(value))
        # Normalize and format in fixed-point to remove trailing zeros
        normalized = d.normalize()
        return format(normalized, 'f')
    except (InvalidOperation, ValueError, TypeError):
        return value

@register.filter(name='to_datetime')
def to_datetime(value):
    """
    Convert an ISO-8601 datetime string to a Python datetime for formatting.
    """
    try:
        return parse_datetime(value)
    except Exception:
        return None
    

@register.filter(name='to_float')
def to_float(value):
    """
    Convert a string or numeric input into a Python float (fallback to 0.0).
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

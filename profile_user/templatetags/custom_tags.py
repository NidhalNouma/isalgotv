from django import template
from django.template.loader import render_to_string
import json

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
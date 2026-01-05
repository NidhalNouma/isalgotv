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



@register.filter
def differance(value1, value2):
    try:
        return abs(Decimal(value1) - Decimal(value2))
    except (InvalidOperation, TypeError):
        return Decimal('0.0')
    


@register.filter
def sum_percentage(value1, value2):
    """
    Calculate what percentage value1 is of value2.
    E.g., to_percentage(50, 200) returns 25.0
    """
    try:
        val1 = Decimal(value1)
        val2 = Decimal(value2) + val1
        if val1 <= 0:
            return Decimal('0.0')
        if val2 == 0:
            return Decimal('0.0')
        percentage = (val1 / val2) * 100
        if percentage > 100:
            percentage = Decimal('100.0')
        elif percentage < 0:
            percentage = Decimal('0.0')

        return percentage
    except (InvalidOperation, TypeError):
        return Decimal('0.0')

@register.filter
def calc_win_rate(wins, total):
    """
    Calculate win rate as a percentage.
    E.g., calc_win_rate(30, 100) returns 30.0
    """
    try:
        wins_dec = Decimal(wins)
        total_dec = Decimal(total)
        if total_dec == 0:
            return Decimal('0.0')
        win_rate = (wins_dec / total_dec) * 100
        win_rate = win_rate.quantize(Decimal('0.01'))  # Round to 2 decimal places
        return win_rate
    except (InvalidOperation, TypeError):
        return Decimal('0.0')


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



CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'CHF',
    'CNY': '¥',
    'HKD': 'HK$',
    'INR': '₹',
    'KRW': '₩',
    'NZD': 'NZ$',
    'SEK': 'kr',
    'NOK': 'kr',
    'MXN': 'MX$',
    'RUB': '₽',
    'BRL': 'R$',
    'ZAR': 'R',
    'TRY': '₺',
    'SGD': 'S$',
    'DKK': 'kr',
    'PLN': 'zł',
    'TWD': 'NT$',
    'THB': '฿',
    'MYR': 'RM',
    'IDR': 'Rp',
    'PHP': '₱',
    'CZK': 'Kč',
    'HUF': 'Ft',
    'ILS': '₪',
    'SAR': '﷼',
    'AED': 'د.إ',
    'COP': 'COL$',
    'CLP': 'CLP$',
    'ARS': 'AR$',
}


@register.filter(name='currency_symbol')
def currency_symbol(code):
    """
    Convert a currency code (e.g. 'USD', 'EUR') to its symbol.
    """
    try:
        return CURRENCY_SYMBOLS.get(code.upper(), code)
    except Exception:
        return code


@register.filter(name='automate_access')
def automate_access(access_list, broker_name):
    """
    Check if the broker_name is in the comma-separated access_list string.
    """
    try:
        access_list = access_list.lower()
        denied = "-" + broker_name
        if denied in access_list:
            return False

        if "all" in access_list or "*" in access_list:
            return True

        access_items = [item.strip() for item in access_list.split(',')]
        return broker_name in access_items
    except Exception:
        return False
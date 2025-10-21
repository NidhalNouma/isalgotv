from django import template
from dateutil.relativedelta import relativedelta
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0 
    
@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg


@register.filter(name='count_lines')
def count_lines(value):
    # Count the number of lines in the given text
    return len(value.split('\n'))

@register.filter
def get_price(prices, title):
    return prices.get(title, '')


@register.filter
def period_in_months_years(start_date, end_date):
    if not all([start_date, end_date]):
        return ""

    # Calculate the difference between two dates
    delta = relativedelta(end_date, start_date)
    
    # Construct the period string
    years = delta.years
    months = delta.months
    period_str = ""
    if years > 0:
        period_str += f"{years} {'year' if years == 1 else 'years'} "
    if months > 0:
        period_str += f"{months} {'month' if months == 1 else 'months'}"
    # print('djnjd kjnjws ', start_date, end_date, delta, period_str.strip())
    
    return period_str.strip()


@register.filter
def map_months_to_number(start_date, end_date):
    if not all([start_date, end_date]):
        return 40  # Return the minimum value if either date is missing

    # Calculate the total duration in months
    delta = relativedelta(end_date, start_date)
    total_months = delta.years * 12 + delta.months

    # Map the duration to the 40-100 range
    if total_months < 4:
        return 40
    elif total_months >= 60:
        return 100
    else:
        # Linear interpolation between 40 (at 4 months) and 100 (at 60 months)
        return round(40 + (total_months - 4) * (60 / (60 - 4)))


# @register.filter
# def format_profit(value):
#     # Ensure we handle input correctly
#     if isinstance(value, (int, float)):
#         print(value)
#         # Split the integer and decimal parts
#         integer_part, decimal_part = str(value).split('.')
#         # Create a formatted string
#         return f'<span style="font-size: larger; font-weight: bold;">{integer_part}</span><span style="font-size: smaller;">.{decimal_part}</span>'
#     return value


@register.filter
def format_profit(value):
    try:
        value = float(value)
        integer_part, decimal_part = str(value).split('.')
        # Create a formatted string
        return f'<span >{integer_part}</span><span class="text-xs">.{decimal_part}</span>'

    except ValueError:
        return value  # If conversion fails, return the original value


@register.filter
def concise_timesince(value):
    """
    Return only the first part of Django's timesince (e.g. '5 months' instead of '5 months, 2 weeks').
    """
    try:
        result = timesince(value)
        return result.split(",")[0].strip()
    except Exception:
        return ""

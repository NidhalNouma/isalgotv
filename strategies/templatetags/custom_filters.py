from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg


@register.filter(name='count_lines')
def count_lines(value):
    # Count the number of lines in the given text
    return len(value.split('\n'))
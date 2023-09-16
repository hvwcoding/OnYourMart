from django import template

register = template.Library()


@register.filter
def placeholders_range(value):
    return range(6 - value)

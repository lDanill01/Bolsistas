from django import template

from editais.models import EditalProvisorio

register = template.Library()


@register.filter
def br_money(value):
    if value is None:
        return 'R$ 0,00'
    value = float(value)
    if value < 0:
        negative = True
        value = abs(value)
    else:
        negative = False
    int_part = int(value)
    dec_part = int(round((value - int_part) * 100))
    int_str = f'{int_part:,}'.replace(',', '.')
    result = f'R$ {int_str},{dec_part:02d}'
    if negative:
        result = f'-{result}'
    return result


@register.filter
def dict_get(d, key):
    if not d:
        return ''
    return d.get(key, '')


@register.filter
def evento_display(codigo):
    for c, label in EditalProvisorio.EVENTO_CHOICES:
        if c == codigo:
            return label
    return codigo

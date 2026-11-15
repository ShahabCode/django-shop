from django import template

register = template.Library()

_PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


@register.filter
def fa_num(value):
    """12000 -> ۱۲٬۰۰۰ (جداکننده هزارگان و ارقام فارسی)."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f'{value:,}'.replace(',', '٬').translate(_PERSIAN_DIGITS)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Query string فعلی را نگه می‌دارد و فقط پارامترهای داده‌شده را عوض می‌کند.
    مثال: href="?{% url_replace page=3 %}"  (sort و q حفظ می‌شن)
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()

from django import template
register = template.Library()
@register.filter
def mask_phone(value):
    if not value:
        return "**********"
    value = str(value)
    if len(value) <= 4:
        return value
    return "*" * (len(value) - 4) + value[-4:]

@register.filter
def mask_email(value):
    if not value or "@" not in value:
        return value

    username, domain = value.split("@", 1)

    if len(username) <= 2:
        masked = username[0] + "*"
    else:
        masked = username[:2] + "*" * (len(username) - 2)

    return f"{masked}@{domain}"
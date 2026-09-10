from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()

_ZERO = Decimal("0")
_ONE = Decimal("1")
_FIVE = Decimal("5")
_HUNDRED = Decimal("100")


def _normalise_rating(value):
    """Return a finite Decimal rating clamped to the 0..5 range."""
    if value in (None, ""):
        return _ZERO

    try:
        # str() avoids binary-float artefacts and replace() also tolerates a
        # localized value such as "3,6" if one ever reaches the filter.
        rating = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return _ZERO

    if not rating.is_finite():
        return _ZERO
    return max(_ZERO, min(_FIVE, rating))


def _css_number(value):
    """Serialize a Decimal with a CSS-safe dot decimal separator."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


@register.filter
def rating_percent(value):
    """Convert a rating out of 5 to a CSS-safe percentage from 0 to 100."""
    return _css_number(_normalise_rating(value) * Decimal("20"))


@register.filter
def rating_stars(value):
    """Return the exact CSS-safe 0..100 fill percentage for each star."""
    rating = _normalise_rating(value)
    fills = []

    for index in range(5):
        fill = rating - Decimal(index)
        fill = max(_ZERO, min(_ONE, fill)) * _HUNDRED
        # Returning strings is intentional: Django localizes numeric template
        # values in French (60.0 -> 60,0). A comma makes a CSS width invalid
        # and caused every overlay star to fall back to its full intrinsic width.
        fills.append(_css_number(fill))

    return fills

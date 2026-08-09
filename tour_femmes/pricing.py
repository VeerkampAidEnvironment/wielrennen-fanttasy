from __future__ import annotations

from decimal import Decimal, InvalidOperation


PRICE_QUANTUM = Decimal("0.01")
MAX_RIDER_PRICE = Decimal("999999.99")
ZERO_PRICE = Decimal("0.00")


def parse_rider_price(value: str) -> Decimal:
    """Parse a non-negative rider price with at most two decimal places."""
    normalized = value.strip().replace(",", ".")
    try:
        price = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("Invalid rider price") from exc

    if not price.is_finite() or price < ZERO_PRICE or price > MAX_RIDER_PRICE:
        raise ValueError("Invalid rider price")

    quantized = price.quantize(PRICE_QUANTUM)
    if price != quantized:
        raise ValueError("Rider prices support at most two decimal places")
    return quantized


def price_value(value: object | None) -> str:
    """Render a price without insignificant zeroes, using a decimal point."""
    if value is None:
        return ""
    try:
        rendered = format(Decimal(str(value)), "f")
    except (InvalidOperation, ValueError):
        return str(value)
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def price_label(value: object | None) -> str:
    """Render a price for the Dutch UI."""
    return price_value(value).replace(".", ",")

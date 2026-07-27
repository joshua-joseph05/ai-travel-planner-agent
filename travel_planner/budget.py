"""Budget helpers — parse money and pick priced options."""

from __future__ import annotations

import re
from typing import Any, Optional


def parse_money(text: Optional[str]) -> Optional[float]:
    """Extract a numeric amount from text like '$5,000' or 'budget 5000'."""
    if not text:
        return None
    match = re.search(r"(\d[\d,]*\.?\d*)", text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def cheapest(
    options: list[dict[str, Any]],
    price_key: str = "price",
) -> Optional[dict[str, Any]]:
    priced = [o for o in options if o.get(price_key) is not None]
    if not priced:
        return None
    return min(priced, key=lambda o: float(o[price_key]))


def pick_under_budget(
    options: list[dict[str, Any]],
    max_price: Optional[float],
    price_key: str = "price",
) -> Optional[dict[str, Any]]:
    """Prefer the cheapest option at or under max_price; else overall cheapest."""
    priced = [o for o in options if o.get(price_key) is not None]
    if not priced:
        return None
    if max_price is not None:
        under = [o for o in priced if float(o[price_key]) <= max_price]
        if under:
            return min(under, key=lambda o: float(o[price_key]))
    return min(priced, key=lambda o: float(o[price_key]))

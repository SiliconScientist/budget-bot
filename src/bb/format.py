from __future__ import annotations

from decimal import Decimal


def format_currency(amount: Decimal) -> str:
    return f"${amount:,.2f}"

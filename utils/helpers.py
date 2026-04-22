import calendar
from datetime import datetime


MONTH_NAMES = {i: calendar.month_name[i] for i in range(1, 13)}


def get_month_year_options(n: int = 12) -> list[tuple[str, int, int]]:
    """Return last n months as (label, month, year) tuples."""
    now = datetime.now()
    result = []
    for i in range(n):
        year = now.year if now.month - i > 0 else now.year - 1
        month = (now.month - i - 1) % 12 + 1
        year = now.year - (i >= now.month)
        label = f"{MONTH_NAMES[month]} {year}"
        result.append((label, month, year))
    return result


def format_currency(amount: float) -> str:
    return f"₹ {amount:,.2f}"


def validate_pan(pan: str) -> bool:
    import re
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan.upper())) if pan else True


def validate_ifsc(ifsc: str) -> bool:
    import re
    return bool(re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc.upper())) if ifsc else True


def get_current_month_year() -> tuple[int, int]:
    now = datetime.now()
    return now.month, now.year

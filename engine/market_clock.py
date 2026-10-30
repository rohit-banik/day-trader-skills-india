"""Clock-window helper for regular NSE/BSE cash-equity trading."""

from datetime import datetime, time, timedelta, timezone


IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")
REGULAR_OPEN = time(9, 15)
REGULAR_CLOSE = time(15, 30)
SUPPORTED_EXCHANGES = frozenset({"NSE", "BSE"})


def within_regular_equity_clock_window(
    exchange: str,
    at: datetime | None = None,
) -> bool:
    """Return whether a time falls within regular weekday equity hours.

    This checks only the weekday and clock window. It does not check exchange
    holidays, special sessions, or segment-specific schedules, and cannot by
    itself authorize an order.
    """
    if exchange not in SUPPORTED_EXCHANGES:
        raise ValueError("exchange must be NSE or BSE")

    if at is None:
        at = datetime.now(IST)
    elif at.tzinfo is None:
        raise ValueError("at must include timezone information")

    local_time = at.astimezone(IST)
    clock_time = local_time.time().replace(tzinfo=None)

    return (
        local_time.weekday() < 5
        and REGULAR_OPEN <= clock_time < REGULAR_CLOSE
    )

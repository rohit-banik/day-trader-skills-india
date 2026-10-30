"""Fetch selected Groww daily candles and apply the daily scanner rules."""

import time
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Any

from engine.daily_scanner import scan_daily_responses
from engine.market_clock import IST


MAX_LOOKBACK_DAYS = 180


def _as_date(value: date | datetime | None) -> date:
    if value is None:
        return datetime.now(IST).date()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("as_of_date datetime must include a timezone.")
        return value.astimezone(IST).date()
    if isinstance(value, date):
        return value
    raise ValueError("as_of_date must be a date or timezone-aware datetime.")


def fetch_daily_scan(
    instruments: Sequence[Mapping[str, Any]],
    data_client: Any,
    as_of_date: date | datetime | None = None,
    lookback_days: int = 90,
    min_price_inr: float = 0.0,
    min_volume: int = 0,
    pause_seconds: float = 0.2,
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, str]]]:
    """Fetch candles for the supplied instruments and scan their completed closes."""
    if not instruments:
        raise ValueError("Provide at least one instrument.")
    if type(lookback_days) is not int or not 1 <= lookback_days <= MAX_LOOKBACK_DAYS:
        raise ValueError("lookback_days must be between 1 and 180.")
    if pause_seconds < 0:
        raise ValueError("pause_seconds cannot be negative.")

    cutoff = _as_date(as_of_date)
    end_date = cutoff - timedelta(days=1)
    start_date = end_date - timedelta(days=lookback_days - 1)
    start_time = f"{start_date.isoformat()} 00:00:00"
    end_time = f"{end_date.isoformat()} 23:59:59"

    responses = {}
    request_failures = {}

    for index, instrument in enumerate(instruments):
        groww_symbol = instrument.get("groww_symbol")
        if not isinstance(groww_symbol, str) or not groww_symbol:
            continue

        if index and pause_seconds:
            time.sleep(pause_seconds)

        try:
            responses[groww_symbol] = data_client.get_daily_candles(
                exchange=instrument["exchange"],
                symbol=instrument["trading_symbol"],
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as exc:
            responses[groww_symbol] = None
            request_failures[groww_symbol] = type(exc).__name__

    hits, counts, failed = scan_daily_responses(
        instruments= instruments,
        responses=responses,
        as_of_date=cutoff,
        min_price_inr=min_price_inr,
        min_volume=min_volume,
    )

    for item in failed:
        error_type = request_failures.get(item.get("groww_symbol", ""))
        if error_type:
            item["reason"] = f"Groww request failed ({error_type})."

    counts["request_failed"] = len(request_failures)
    return hits, counts, failed

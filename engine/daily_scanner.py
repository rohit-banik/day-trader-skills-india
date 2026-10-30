"""Apply daily scanner rules to supplied Groww candle responses."""

import math
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from engine.market_clock import IST
from engine.scanner_signals import MIN_DAILY_CLOSES, find_daily_setups


def _candle_date(timestamp: Any) -> date:
    if isinstance(timestamp, str):
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Candle timestamp is not valid ISO format.") from exc

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)
        else:
            parsed = parsed.astimezone(IST)
        return parsed.date()

    if isinstance(timestamp, (int, float)) and math.isfinite(float(timestamp)):
        seconds = float(timestamp)
        if seconds > 10_000_000_000:
            seconds /= 1000.0
        return datetime.fromtimestamp(seconds, tz=IST).date()

    raise ValueError("Candle timestamp must be ISO text or epoch time.")


def _finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def scan_daily_responses(
    universe: Iterable[Mapping[str, Any]],
    responses: Mapping[str, Any],
    as_of_date: date | datetime | None = None,
    min_price_inr: float = 0.0,
    min_volume: int = 0,
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, str]]]:
    """Scan already-fetched daily responses; this function makes no API calls."""
    if as_of_date is None:
        cutoff = datetime.now(IST).date()
    elif isinstance(as_of_date, datetime):
        if as_of_date.tzinfo is None:
            raise ValueError("as_of_date datetime must include a timezone.")
        cutoff = as_of_date.astimezone(IST).date()
    elif isinstance(as_of_date, date):
        cutoff = as_of_date
    else:
        raise ValueError("as_of_date must be a date or timezone-aware datetime.")

    if not math.isfinite(float(min_price_inr)) or min_price_inr < 0:
        raise ValueError("min_price_inr must be a finite non-negative amount.")
    if type(min_volume) is not int or min_volume < 0:
        raise ValueError("min_volume must be a non-negative integer.")

    counts = {
        "requested": 0,
        "fetched": 0,
        "short": 0,
        "illiquid": 0,
        "scanned": 0,
        "hits": 0,
    }
    hits = []
    failed = []

    for instrument in universe:
        counts["requested"] += 1
        groww_symbol = instrument.get("groww_symbol")
        if not isinstance(groww_symbol, str) or not groww_symbol:
            failed.append({"groww_symbol": "", "reason": "Instrument has no Groww symbol."})
            continue

        response = responses.get(groww_symbol)
        candles = response.get("candles") if isinstance(response, Mapping) else None
        if not isinstance(candles, list):
            failed.append(
                {"groww_symbol": groww_symbol, "reason": "No candle list in response."}
            )
            continue

        counts["fetched"] += 1
        daily = []
        try:
            for candle in candles:
                if not isinstance(candle, (list, tuple)) or len(candle) < 6:
                    continue
                if _candle_date(candle[0]) >= cutoff:
                    continue

                close = _finite_number(candle[4])
                if close is None or close <= 0:
                    continue

                volume = _finite_number(candle[5])
                daily.append((_candle_date(candle[0]), close, int(volume) if volume is not None and volume > 0 else 0))
        except (OverflowError, OSError, ValueError) as exc:
            failed.append({"groww_symbol": groww_symbol, "reason": str(exc)})
            continue

        daily.sort(key=lambda item: item[0])
        if len(daily) < MIN_DAILY_CLOSES:
            counts["short"] += 1
            continue

        closes = [close for _, close, _ in daily]
        last_date, last_close, last_volume = daily[-1]

        if last_close < min_price_inr or last_volume < min_volume:
            counts["illiquid"] += 1
            continue

        counts["scanned"] += 1
        setups, metrics = find_daily_setups(closes)
        if not setups:
            continue

        hits.append(
            {
                "exchange": instrument.get("exchange"),
                "symbol": instrument.get("trading_symbol"),
                "name": instrument.get("name"),
                "setups": setups,
                "close_inr": round(last_close, 2),
                "close_date": last_date.isoformat(),
                "rsi": round(metrics["rsi"], 1),
                "volume": last_volume,
            }
        )

    hits.sort(
        key=lambda item: (
            -(item["close_inr"] * item["volume"]),
            item.get("exchange") or "",
            item.get("symbol") or "",
        )
    )
    counts["hits"] = len(hits)
    return hits, counts, failed


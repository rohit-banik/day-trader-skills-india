"""Pure daily chart-pattern calculations for the Indian-market scanner."""

import math
from collections.abc import Iterable


MIN_DAILY_CLOSES = 30


def _validated_closes(closes: Iterable[float]) -> list[float]:
    try:
        values = [float(value) for value in closes]
    except (TypeError, ValueError) as exc:
        raise ValueError("Closes must be numeric prices.") from exc

    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("Close prices must be finite values greater than zero.")

    return values


def wilder_rsi(closes: Iterable[float], period: int = 14) -> float | None:
    """Calculate Wilder RSI from oldest-to-newest closing prices."""
    values = _validated_closes(closes)

    if type(period) is not int or period <= 0:
        raise ValueError("period must be a positive integer.")
    if len(values) < period + 1:
        return None

    gains = [
        max(0.0, values[index] - values[index - 1])
        for index in range(1, len(values))
    ]
    losses = [
        max(0.0, values[index - 1] - values[index])
        for index in range(1, len(values))
    ]

    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period

    for index in range(period, len(gains)):
        average_gain = (average_gain * (period - 1) + gains[index]) / period
        average_loss = (average_loss * (period - 1) + losses[index]) / period

    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss
    return 100.0 - 100.0 / (1.0 + relative_strength)


def find_daily_setups(closes: Iterable[float]) -> tuple[list[str], dict[str, float]]:
    """Return matching setup tags and measurements from completed daily closes.

    These tags identify charts matching rules; they are not buy recommendations.
    """
    values = _validated_closes(closes)
    if len(values) < MIN_DAILY_CLOSES:
        raise ValueError(
            f"At least {MIN_DAILY_CLOSES} completed daily closes are required."
        )

    last = values[-1]
    high20 = max(values[-21:-1])
    ma20 = sum(values[-20:]) / 20.0
    ma20_previous = sum(values[-21:-1]) / 20.0
    run_pct = (values[-6] / values[-16] - 1.0) * 100.0
    range5_pct = (max(values[-5:]) - min(values[-5:])) / last * 100.0
    rsi = wilder_rsi(values)
    previous_rsi = wilder_rsi(values[:-1])

    tags = []
    if last > high20:
        tags.append("breakout_20d")
    if run_pct > 10.0 and range5_pct < 5.0:
        tags.append("bull_flag")
    if values[-2] < ma20_previous and last > ma20:
        tags.append("reclaim_ma20")
    if rsi is not None and rsi < 30.0:
        tags.append("oversold")
    if previous_rsi is not None and previous_rsi < 30.0 and last > values[-2]:
        tags.append("oversold_bounce")

    metrics = {
        "rsi": rsi if rsi is not None else 0.0,
        "rsi_prev": previous_rsi if previous_rsi is not None else 0.0,
        "high20": high20,
        "ma20": ma20,
        "run_pct": run_pct,
        "range5_pct": range5_pct,
    }
    return tags, metrics

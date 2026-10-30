"""Read-only Groww instrument directory helpers."""

import math
from collections.abc import Mapping, Sequence
from typing import Any

from integrations.groww.market_data import GrowwMarketData


SUPPORTED_EXCHANGES = frozenset({"NSE", "BSE"})


def _text(value: Any) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _integer(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None and number.is_integer() else None


def _flag(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


class GrowwInstrumentDirectory(GrowwMarketData):
    """Fetch and filter the Groww instrument list for the scanner."""

    def get_cash_equities(
        self,
        exchanges: Sequence[str] = ("NSE", "BSE"),
    ) -> list[dict[str, Any]]:
        allowed = {
            exchange.strip().upper()
            for exchange in exchanges
            if isinstance(exchange, str)
        }
        if not allowed or not allowed.issubset(SUPPORTED_EXCHANGES):
            raise ValueError("Exchanges must be NSE, BSE, or both.")

        instrument_data = self._client.get_all_instruments()
        if not hasattr(instrument_data, "to_dict"):
            raise RuntimeError("Groww returned an unsupported instrument-list format.")

        rows = instrument_data.to_dict(orient="records")
        result = []

        for row in rows:
            if not isinstance(row, Mapping):
                continue

            exchange = (_text(row.get("exchange")) or "").upper()
            segment = (_text(row.get("segment")) or "").upper()
            instrument_type = (_text(row.get("instrument_type")) or "").upper()
            symbol = _text(row.get("trading_symbol"))
            groww_symbol = _text(row.get("groww_symbol"))

            if (
                exchange not in allowed
                or segment != "CASH"
                or instrument_type != "EQ"
                or not symbol
                or not groww_symbol
            ):
                continue

            result.append(
                {
                    "exchange": exchange,
                    "segment": segment,
                    "instrument_type": instrument_type,
                    "trading_symbol": symbol,
                    "groww_symbol": groww_symbol,
                    "name": _text(row.get("name")),
                    "series": _text(row.get("series")),
                    "isin": _text(row.get("isin")),
                    "lot_size": _integer(row.get("lot_size")),
                    "tick_size": _number(row.get("tick_size")),
                    "buy_allowed": _flag(row.get("buy_allowed")),
                    "sell_allowed": _flag(row.get("sell_allowed")),
                }
            )

        return sorted(
            result,
            key=lambda instrument: (
                instrument["exchange"],
                instrument["trading_symbol"],
                instrument["series"] or "",
            ),
        )

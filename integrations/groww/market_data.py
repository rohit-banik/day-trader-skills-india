"""Read-only Groww market-data access."""

import os
from typing import Any, Sequence


class GrowwMarketData:
    """Read quotes and prices; this class has no order methods."""

    def __init__(self) -> None:
        token = os.environ.get("GROWW_API_ACCESS_TOKEN")
        if not token:
            raise RuntimeError(
                "GROWW_API_ACCESS_TOKEN is missing; set it locally before requesting data."
            )

        try:
            from growwapi import GrowwAPI
        except ImportError as exc:
            raise RuntimeError(
                "Groww SDK is missing; install the project requirements first."
            ) from exc

        self._client = GrowwAPI(token)

    @staticmethod
    def _instrument(exchange: str, symbol: str) -> tuple[str, str]:
        if not isinstance(exchange, str) or not isinstance(symbol, str):
            raise ValueError("Exchange and trading symbol must be text.")

        exchange = exchange.strip().upper()
        symbol = symbol.strip().upper()

        if exchange not in {"NSE", "BSE"}:
            raise ValueError("Exchange must be NSE or BSE.")
        if not symbol:
            raise ValueError("Trading symbol cannot be empty.")

        return exchange, symbol

    @classmethod
    def _instruments(
        cls,
        instruments: Sequence[tuple[str, str]],
    ) -> tuple[tuple[str, str], ...]:
        items = tuple(instruments)
        if not items:
            raise ValueError("Provide at least one instrument.")
        if len(items) > 50:
            raise ValueError("Groww supports up to 50 instruments per batch call.")

        normalized = []
        for item in items:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ValueError("Each instrument must be (exchange, trading_symbol).")
            normalized.append(cls._instrument(item[0], item[1]))

        return tuple(normalized)

    def get_quote(self, exchange: str, symbol: str) -> Any:
        exchange, symbol = self._instrument(exchange, symbol)
        exchange_value = getattr(self._client, f"EXCHANGE_{exchange}")
        return self._client.get_quote(
            exchange=exchange_value,
            segment=self._client.SEGMENT_CASH,
            trading_symbol=symbol,
        )

    def get_ltp(
        self,
        instruments: Sequence[tuple[str, str]],
    ) -> Any:
        normalized = self._instruments(instruments)
        exchange_symbols = tuple(
            f"{exchange}_{symbol}" for exchange, symbol in normalized
        )
        return self._client.get_ltp(
            segment=self._client.SEGMENT_CASH,
            exchange_trading_symbols=exchange_symbols,
        )

    def get_ohlc(
        self,
        instruments: Sequence[tuple[str, str]],
    ) -> Any:
        normalized = self._instruments(instruments)
        exchange_symbols = tuple(
            f"{exchange}_{symbol}" for exchange, symbol in normalized
        )
        return self._client.get_ohlc(
            segment=self._client.SEGMENT_CASH,
            exchange_trading_symbols=exchange_symbols,
        )

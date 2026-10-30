"""Read-only Groww historical intraday candle access."""

from datetime import datetime, timedelta
from typing import Any

from integrations.groww.market_data import GrowwMarketData


class GrowwHistoricalData(GrowwMarketData):
    """Fetch cash-equity candles using IST wall-clock time strings."""

    _INTERVAL_CONSTANTS = {
        1: "CANDLE_INTERVAL_MIN_1",
        2: "CANDLE_INTERVAL_MIN_2",
        3: "CANDLE_INTERVAL_MIN_3",
        5: "CANDLE_INTERVAL_MIN_5",
        10: "CANDLE_INTERVAL_MIN_10",
        15: "CANDLE_INTERVAL_MIN_15",
        30: "CANDLE_INTERVAL_MIN_30",
    }

    @staticmethod
    def _parse_time(value: str) -> datetime:
        if not isinstance(value, str):
            raise ValueError("Times must be IST strings in YYYY-MM-DD HH:MM:SS format.")
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(
                "Times must be IST strings in YYYY-MM-DD HH:MM:SS format."
            ) from exc

    def get_historical_candles(
        self,
        exchange: str,
        symbol: str,
        start_time: str,
        end_time: str,
        interval_minutes: int = 5,
    ) -> Any:
        if type(interval_minutes) is not int or interval_minutes not in self._INTERVAL_CONSTANTS:
            raise ValueError("Interval must be one of 1, 2, 3, 5, 10, 15, or 30 minutes.")

        start = self._parse_time(start_time)
        end = self._parse_time(end_time)

        if end <= start:
            raise ValueError("end_time must be later than start_time.")

        max_days = 30 if interval_minutes <= 5 else 90
        if end - start > timedelta(days=max_days):
            raise ValueError(
                f"Groww allows at most {max_days} days per request at this interval."
            )

        exchange, symbol = self._instrument(exchange, symbol)
        exchange_value = getattr(self._client, f"EXCHANGE_{exchange}")
        candle_interval = getattr(
            self._client,
            self._INTERVAL_CONSTANTS[interval_minutes],
        )

        return self._client.get_historical_candles(
            exchange=exchange_value,
            segment=self._client.SEGMENT_CASH,
            groww_symbol=f"{exchange}-{symbol}",
            start_time=start_time,
            end_time=end_time,
            candle_interval=candle_interval,
        )

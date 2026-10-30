"""Read-only Groww daily candle access for cash equities."""

from datetime import timedelta
from typing import Any

from integrations.groww.historical_data import GrowwHistoricalData


MAX_DAYS_PER_REQUEST = 180


class GrowwDailyData(GrowwHistoricalData):
    """Fetch daily cash-equity candles; times are IST wall-clock strings."""

    def get_daily_candles(
        self,
        exchange: str,
        symbol: str,
        start_time: str,
        end_time: str,
    ) -> Any:
        start = self._parse_time(start_time)
        end = self._parse_time(end_time)

        if end <= start:
            raise ValueError("end_time must be later than start_time.")
        if end - start > timedelta(days=MAX_DAYS_PER_REQUEST):
            raise ValueError("Groww allows at most 180 days per daily-candle request.")

        exchange, symbol = self._instrument(exchange, symbol)
        exchange_value = getattr(self._client, f"EXCHANGE_{exchange}")

        return self._client.get_historical_candles(
            exchange=exchange_value,
            segment=self._client.SEGMENT_CASH,
            groww_symbol=f"{exchange}-{symbol}",
            start_time=start_time,
            end_time=end_time,
            candle_interval=self._client.CANDLE_INTERVAL_DAY,
        )

"""Command-line daily scan for selected NSE/BSE cash-equity symbols."""

import argparse
import sys

from engine.groww_daily_scan import fetch_daily_scan
from integrations.groww.daily_data import GrowwDailyData


def parse_symbols(value: str) -> list[dict[str, str]]:
    instruments = []
    seen = set()

    for item in value.split(","):
        item = item.strip()
        if ":" not in item:
            raise ValueError(f"Expected EXCHANGE:SYMBOL, got {item!r}.")

        exchange, symbol = item.split(":", 1)
        exchange = exchange.strip().upper()
        symbol = symbol.strip().upper()

        if exchange not in {"NSE", "BSE"} or not symbol:
            raise ValueError(f"Invalid instrument {item!r}; use NSE:SYMBOL or BSE:SYMBOL.")

        key = (exchange, symbol)
        if key in seen:
            continue
        seen.add(key)

        instruments.append(
            {
                "exchange": exchange,
                "trading_symbol": symbol,
                "groww_symbol": f"{exchange}-{symbol}",
                "name": "",
            }
        )

    if not instruments:
        raise ValueError("Provide at least one instrument.")

    return instruments


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan selected NSE/BSE cash equities using completed daily closes."
    )
    parser.add_argument(
        "--symbols",
        required=True,
        help="Comma-separated exchange symbols, e.g. NSE:RELIANCE,BSE:TCS",
    )
    parser.add_argument("--min-price-inr", type=float, default=0.0)
    parser.add_argument("--min-volume", type=int, default=0)
    parser.add_argument("--pause-seconds", type=float, default=0.2)
    args = parser.parse_args(argv)

    try:
        instruments = parse_symbols(args.symbols)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        groww = GrowwDailyData()
    except Exception as exc:
        parser.error(
            f"Groww client could not be initialized ({type(exc).__name__}); "
            "check the local environment and SDK setup."
        )

    hits, counts, failed = fetch_daily_scan(
        instruments=instruments,
        data_client=groww,
        min_price_inr=args.min_price_inr,
        min_volume=args.min_volume,
        pause_seconds=args.pause_seconds,
    )

    print("Daily scan results: rule matches only, not buy recommendations.")
    print(
        "Requested: {requested}; fetched: {fetched}; scanned: {scanned}; "
        "short history: {short}; filtered: {illiquid}; failed: {failed_count}; "
        "matches: {hits_count}".format(
            failed_count=len(failed),
            hits_count=len(hits),
            **counts,
        )
    )

    for hit in hits:
        print(
            "{exchange}:{symbol} | {setups} | INR {price:.2f} | "
            "close {date} | RSI {rsi:.1f}".format(
                exchange=hit["exchange"],
                symbol=hit["symbol"],
                setups=", ".join(hit["setups"]),
                price=hit["close_inr"],
                date=hit["close_date"],
                rsi=hit["rsi"],
            )
        )

    for item in failed:
        print(
            "Skipped {symbol}: {reason}".format(
                symbol=item.get("groww_symbol") or "(unknown instrument)",
                reason=item["reason"],
            ),
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

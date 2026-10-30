"""Load and validate the DayTrader settings."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = PROJECT_ROOT / "config" / "settings.example.json"


class SettingsError(ValueError):
    """Raised when settings are missing or unsafe."""


def load_settings(path=DEFAULT_SETTINGS):
    path = Path(path)

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SettingsError(f"Cannot read settings file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SettingsError(f"Invalid JSON in settings file: {path}") from exc

    if not isinstance(settings, dict):
        raise SettingsError("Settings must be a JSON object.")

    market = settings.get("market")
    if not isinstance(market, dict):
        raise SettingsError("The market section is required.")

    exchanges = market.get("exchanges")
    if (
        not isinstance(exchanges, list)
        or not exchanges
        or any(exchange not in {"NSE", "BSE"} for exchange in exchanges)
    ):
        raise SettingsError("Exchanges must contain NSE and/or BSE.")

    if market.get("timezone") != "Asia/Kolkata":
        raise SettingsError("Market timezone must be Asia/Kolkata.")
    if market.get("currency") != "INR":
        raise SettingsError("Market currency must be INR.")

    broker = settings.get("broker")
    if not isinstance(broker, dict) or broker.get("provider") != "groww":
        raise SettingsError("Broker provider must be groww.")
    if broker.get("connected") is not False:
        raise SettingsError("Groww connection is not implemented yet; keep connected false.")

    execution = settings.get("execution")
    if not isinstance(execution, dict):
        raise SettingsError("The execution section is required.")
    if execution.get("mode") != "paper":
        raise SettingsError("Only paper mode is available.")
    if execution.get("live_orders_enabled") is not False:
        raise SettingsError("Live orders must remain disabled.")
    if execution.get("require_explicit_approval") is not True:
        raise SettingsError("Explicit approval must be required.")

    risk = settings.get("risk")
    if not isinstance(risk, dict) or risk.get("limits_configured") is not False:
        raise SettingsError("Risk limits are not implemented; keep them unconfigured.")

    return settings

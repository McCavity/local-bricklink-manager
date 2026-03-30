"""Currency conversion using the European Central Bank's free API."""
import logging
import requests

logger = logging.getLogger(__name__)

# Cache exchange rates for the lifetime of the process
_rate_cache = {}


def get_exchange_rate(currency_code):
    """Get exchange rate: 1 EUR = X currency_code.

    Uses the ECB's free Frankfurter API (no key needed).
    Returns None if the rate cannot be fetched.
    """
    if currency_code == "EUR":
        return 1.0

    code = currency_code.upper()
    if code in _rate_cache:
        return _rate_cache[code]

    try:
        resp = requests.get(
            "https://api.frankfurter.dev/v1/latest",
            params={"from": "EUR", "to": code},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("rates", {}).get(code)
        if rate:
            _rate_cache[code] = float(rate)
            logger.info(f"Exchange rate: 1 EUR = {rate} {code}")
            return float(rate)
    except Exception as e:
        logger.warning(f"Failed to fetch exchange rate for {code}: {e}")

    return None


def convert_to_eur(amount, currency_code):
    """Convert an amount in foreign currency to EUR.

    Returns (eur_amount, rate) or (None, None) if conversion fails.
    """
    if currency_code == "EUR":
        return amount, 1.0

    rate = get_exchange_rate(currency_code)
    if rate and rate > 0:
        return amount / rate, rate

    return None, None

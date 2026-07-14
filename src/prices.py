"""Live stock quotes for the portfolio tracker. Plain python, no LangChain.

This is the one place the app reaches the network for market data. It is *not* a
cloud LLM API, so the project's LangChain/LLM boundary is untouched; it does
relax the "fully offline" claim for the portfolio feature only. ``yfinance`` is
imported lazily and every failure (missing package, no network, unknown ticker)
degrades to ``None`` so the UI can fall back to manual price entry — the fetch
never raises.
"""

from __future__ import annotations

try:  # optional dependency: absent installs still run, prices just go manual
    import yfinance as _yf
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    _yf = None


def _last_price(ticker: str) -> float | None:
    """Return the last traded price for ``ticker`` or ``None`` on any failure."""
    if _yf is None:
        return None
    try:
        price = _yf.Ticker(ticker).fast_info["last_price"]
    except Exception:  # network error, unknown ticker, API shape change
        return None
    return float(price) if price else None


def fetch_prices(tickers: list[str]) -> dict[str, float | None]:
    """Map each ticker to its current price, or ``None`` when unavailable.

    Offline (no ``yfinance`` or no network) every ticker maps to ``None`` and the
    caller prompts for manual entry. Tickers are upper-cased and de-duplicated.
    """
    return {t: _last_price(t) for t in dict.fromkeys(s.upper() for s in tickers)}

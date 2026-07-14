"""Price fetching: mocked yfinance success, offline fallback, robustness."""

from __future__ import annotations

import pytest

from src import prices


class _FastInfo(dict):
    """Stand-in for yfinance's fast_info mapping."""


class _FakeTicker:
    def __init__(self, ticker: str):
        self.ticker = ticker

    @property
    def fast_info(self):
        return _FastInfo(last_price=123.45)


class _FakeYF:
    Ticker = _FakeTicker


def test_fetch_prices_success(monkeypatch):
    monkeypatch.setattr(prices, "_yf", _FakeYF)
    assert prices.fetch_prices(["AAPL", "msft"]) == {"AAPL": 123.45, "MSFT": 123.45}


def test_tickers_upper_cased_and_deduped(monkeypatch):
    monkeypatch.setattr(prices, "_yf", _FakeYF)
    result = prices.fetch_prices(["aapl", "AAPL", "Aapl"])
    assert list(result) == ["AAPL"]


def test_offline_returns_none(monkeypatch):
    monkeypatch.setattr(prices, "_yf", None)
    assert prices.fetch_prices(["AAPL", "MSFT"]) == {"AAPL": None, "MSFT": None}


def test_fetch_error_degrades_to_none(monkeypatch):
    class _Boom:
        @staticmethod
        def Ticker(_t):
            raise RuntimeError("network down")

    monkeypatch.setattr(prices, "_yf", _Boom)
    assert prices.fetch_prices(["AAPL"]) == {"AAPL": None}


@pytest.mark.parametrize("value", [0, None])
def test_missing_price_is_none(monkeypatch, value):
    class _Info:
        @staticmethod
        def Ticker(_t):
            class _T:
                fast_info = {"last_price": value}

            return _T()

    monkeypatch.setattr(prices, "_yf", _Info)
    assert prices.fetch_prices(["AAPL"]) == {"AAPL": None}

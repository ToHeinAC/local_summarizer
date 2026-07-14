"""Portfolio CSV parsing, metrics, and 100-bagger recommendation rules."""

from __future__ import annotations

import pytest

from src import portfolio as pf

CSV = (
    "ticker,quantity,buy_price,currency,thesis_broken\n"
    "AAPL,10,100,USD,\n"
    "MSFT,5,200,USD,x\n"
)


def test_parse_csv_basic():
    holdings = pf.parse_csv(CSV)
    assert [h.ticker for h in holdings] == ["AAPL", "MSFT"]
    assert holdings[0].quantity == 10 and holdings[0].buy_price == 100
    assert holdings[0].currency == "USD"
    assert holdings[1].thesis_broken is True  # "x" is truthy
    assert holdings[0].thesis_broken is False


def test_parse_csv_case_insensitive_headers_and_lowercase_ticker():
    holdings = pf.parse_csv("Ticker,Quantity,Buy_Price\naapl,1,50\n")
    assert holdings[0].ticker == "AAPL"


def test_parse_csv_skips_blank_lines():
    holdings = pf.parse_csv("ticker,quantity,buy_price\nAAPL,1,10\n\n,,\n")
    assert len(holdings) == 1


def test_parse_csv_missing_column():
    with pytest.raises(ValueError, match="missing required column"):
        pf.parse_csv("ticker,quantity\nAAPL,1\n")


def test_parse_csv_bad_number_names_row():
    with pytest.raises(ValueError, match="Row 2 .AAPL."):
        pf.parse_csv("ticker,quantity,buy_price\nAAPL,ten,10\n")


def test_parse_csv_empty_holdings():
    with pytest.raises(ValueError, match="no holdings"):
        pf.parse_csv("ticker,quantity,buy_price\n")


def test_build_portfolio_metrics():
    holdings = [pf.Holding("AAPL", 10, 100), pf.Holding("MSFT", 5, 200)]
    port = pf.build_portfolio(holdings, {"AAPL": 150, "MSFT": 200})
    aapl, msft = port.positions
    assert aapl.market_value == 1500 and aapl.cost_basis == 1000
    assert aapl.gain == 500 and aapl.gain_pct == 0.5
    assert aapl.multiple == 1.5
    # weights against total value 1500 + 1000 = 2500
    assert aapl.weight == pytest.approx(0.6)
    assert port.total_cost == 2000
    assert port.total_value == 2500
    assert port.total_gain == 500
    assert port.total_gain_pct == 0.25
    assert port.priced is True


def test_unpriced_position_is_none_and_holds():
    port = pf.build_portfolio([pf.Holding("AAPL", 1, 100)], {"AAPL": None})
    pos = port.positions[0]
    assert pos.current_price is None and pos.market_value is None
    assert pos.weight is None and pos.recommendation == pf.HOLD
    assert port.priced is False and port.total_value is None


def test_partial_pricing_weights_use_priced_total():
    holdings = [pf.Holding("AAPL", 1, 100), pf.Holding("MSFT", 1, 100)]
    port = pf.build_portfolio(holdings, {"AAPL": 100, "MSFT": None})
    assert port.positions[0].weight == 1.0  # only priced position
    assert port.priced is True


# --- recommendation rules --------------------------------------------------
def _pos(gain_pct=0.0, weight=0.1, thesis_broken=False):
    h = pf.Holding("X", 1, 100, thesis_broken=thesis_broken)
    return pf.Position(h, 100, 100, 100, 0, gain_pct, 1.0, weight, pf.HOLD)


def test_default_is_hold():
    assert pf.recommend(_pos(gain_pct=2.0, weight=0.1)) == pf.HOLD  # up big -> still hold


def test_dip_triggers_add():
    assert pf.recommend(_pos(gain_pct=-0.25)) == pf.ADD
    assert pf.recommend(_pos(gain_pct=-0.20)) == pf.ADD  # at threshold
    assert pf.recommend(_pos(gain_pct=-0.19)) == pf.HOLD


def test_concentration_triggers_trim():
    assert pf.recommend(_pos(weight=0.30)) == pf.TRIM
    assert pf.recommend(_pos(weight=0.25)) == pf.HOLD  # at cap, not over


def test_thesis_broken_outranks_all():
    assert pf.recommend(_pos(gain_pct=-0.5, weight=0.9, thesis_broken=True)) == pf.REVIEW


def test_concentration_outranks_dip():
    assert pf.recommend(_pos(gain_pct=-0.5, weight=0.3)) == pf.TRIM


def test_snapshot_csv_roundtrips_as_holdings():
    holdings = [pf.Holding("AAPL", 10, 100, "USD", thesis_broken=True)]
    port = pf.build_portfolio(holdings, {"AAPL": 150})
    snap = pf.snapshot_csv(port)
    assert "recommendation" in snap.splitlines()[0]
    reparsed = pf.parse_csv(snap)  # extra columns ignored on re-upload
    assert reparsed[0].ticker == "AAPL" and reparsed[0].thesis_broken is True

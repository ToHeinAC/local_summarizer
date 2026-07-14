"""Stock-portfolio domain: CSV round-trip, metrics, 100-bagger rules.

Plain python, no LangChain, no LLM. A portfolio is a list of ``Holding`` rows
(the user's own picks, uploaded as CSV). Given current prices it computes each
position's value, gain, x-multiple toward 100 and portfolio weight, then applies
a deliberately hold-biased rule set.

The recommendation philosophy follows the *100 Baggers* research (Mayer/Phelps):
the chief enemy of a 100-bagger is selling too soon, so the default is **HOLD**.
Nothing here is investment advice — it only tracks the picks so they are not lost
and flags thesis-consistent nudges.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, replace

# --- recommendation labels -------------------------------------------------
HOLD = "hold"
ADD = "add"
TRIM = "trim"
REVIEW = "review"

# --- rule thresholds (tunable) ---------------------------------------------
ADD_DIP_PCT = -0.20  # price this far below cost -> thesis-consistent top-up
CONCENTRATION_CAP = 0.25  # single position past this weight -> trim for risk
BAGGER_GOAL = 100  # the x-multiple the tracker counts toward

# --- CSV --------------------------------------------------------------------
REQUIRED_COLUMNS = ("ticker", "quantity", "buy_price")
OPTIONAL_COLUMNS = ("currency", "thesis_broken")
_TRUTHY = {"true", "1", "yes", "y", "x"}

CSV_TEMPLATE = (
    "ticker,quantity,buy_price,currency,thesis_broken\n"
    "AAPL,10,150.00,USD,\n"
    "MSFT,5,300.00,USD,\n"
)


@dataclass(frozen=True)
class Holding:
    """One line of the portfolio: a stock the user bought and wants to keep."""

    ticker: str
    quantity: float
    buy_price: float
    currency: str = ""
    thesis_broken: bool = False


@dataclass(frozen=True)
class Position:
    """A ``Holding`` valued at a current price, with its recommendation."""

    holding: Holding
    current_price: float | None
    cost_basis: float
    market_value: float | None
    gain: float | None
    gain_pct: float | None
    multiple: float | None  # current / buy price, i.e. x-bagger progress
    weight: float | None  # fraction of the priced portfolio's value
    recommendation: str


@dataclass(frozen=True)
class Portfolio:
    positions: list[Position]
    total_cost: float
    total_value: float | None
    total_gain: float | None
    total_gain_pct: float | None
    priced: bool  # True if at least one position had a current price


def parse_csv(text: str) -> list[Holding]:
    """Parse an uploaded portfolio CSV into holdings.

    Headers are matched case-insensitively and trimmed; ``ticker``, ``quantity``
    and ``buy_price`` are required. Raises ``ValueError`` on a missing column or
    an unparseable number, naming the offending row.
    """
    reader = csv.DictReader(io.StringIO(text))
    headers = {(h or "").strip().lower(): h for h in (reader.fieldnames or [])}
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")

    def cell(row: dict, name: str) -> str:
        return (row.get(headers[name], "") or "").strip() if name in headers else ""

    holdings: list[Holding] = []
    for i, row in enumerate(reader, start=2):  # row 1 is the header
        ticker = cell(row, "ticker").upper()
        if not ticker:
            continue  # skip blank lines
        try:
            quantity = float(cell(row, "quantity"))
            buy_price = float(cell(row, "buy_price"))
        except ValueError:
            raise ValueError(f"Row {i} ({ticker}): quantity and buy_price must be numbers")
        holdings.append(
            Holding(
                ticker=ticker,
                quantity=quantity,
                buy_price=buy_price,
                currency=cell(row, "currency").upper(),
                thesis_broken=cell(row, "thesis_broken").lower() in _TRUTHY,
            )
        )
    if not holdings:
        raise ValueError("CSV contained no holdings")
    return holdings


def recommend(
    position: Position,
    *,
    add_dip_pct: float = ADD_DIP_PCT,
    concentration_cap: float = CONCENTRATION_CAP,
) -> str:
    """Apply the hold-biased 100-bagger rule to a valued position.

    Precedence: a broken thesis outranks everything (REVIEW), then concentration
    risk (TRIM), then a thesis-consistent dip (ADD); otherwise HOLD — winners are
    never trimmed merely for being up.
    """
    if position.holding.thesis_broken:
        return REVIEW
    if position.weight is not None and position.weight > concentration_cap:
        return TRIM
    if position.gain_pct is not None and position.gain_pct <= add_dip_pct:
        return ADD
    return HOLD


def build_portfolio(
    holdings: list[Holding],
    prices: dict[str, float | None],
    *,
    add_dip_pct: float = ADD_DIP_PCT,
    concentration_cap: float = CONCENTRATION_CAP,
) -> Portfolio:
    """Value every holding at its current price and derive recommendations.

    ``prices`` maps upper-cased ticker -> price (or ``None`` when unavailable).
    Weights are taken against the total value of the *priced* positions, so a
    partially priced portfolio still yields sensible weights.
    """
    total_value = sum(
        h.quantity * prices[h.ticker]
        for h in holdings
        if prices.get(h.ticker) is not None
    )
    priced = total_value > 0

    positions: list[Position] = []
    for h in holdings:
        price = prices.get(h.ticker)
        cost_basis = h.quantity * h.buy_price
        if price is None:
            pos = Position(h, None, cost_basis, None, None, None, None, None, HOLD)
        else:
            market_value = h.quantity * price
            gain = market_value - cost_basis
            pos = Position(
                holding=h,
                current_price=price,
                cost_basis=cost_basis,
                market_value=market_value,
                gain=gain,
                gain_pct=gain / cost_basis if cost_basis else None,
                multiple=price / h.buy_price if h.buy_price else None,
                weight=market_value / total_value if priced else None,
                recommendation=HOLD,
            )
        positions.append(
            replace(pos, recommendation=recommend(
                pos, add_dip_pct=add_dip_pct, concentration_cap=concentration_cap
            ))
        )

    total_cost = sum(p.cost_basis for p in positions)
    total_gain = (total_value - total_cost) if priced else None
    return Portfolio(
        positions=positions,
        total_cost=total_cost,
        total_value=total_value if priced else None,
        total_gain=total_gain,
        total_gain_pct=(total_gain / total_cost) if priced and total_cost else None,
        priced=priced,
    )


def snapshot_csv(portfolio: Portfolio) -> str:
    """Serialize the portfolio to CSV for download.

    Carries the holding columns (so the file re-uploads cleanly) plus a valued
    snapshot: current price, value, gain %, multiple, weight, recommendation.
    """
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "ticker", "quantity", "buy_price", "currency", "thesis_broken",
        "current_price", "market_value", "gain_pct", "multiple", "weight",
        "recommendation",
    ])
    for p in portfolio.positions:
        h = p.holding
        writer.writerow([
            h.ticker, h.quantity, h.buy_price, h.currency,
            "true" if h.thesis_broken else "",
            _num(p.current_price), _num(p.market_value), _num(p.gain_pct),
            _num(p.multiple), _num(p.weight), p.recommendation,
        ])
    return out.getvalue()


def _num(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"

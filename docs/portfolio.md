# Portfolio tracker

A second section of the app (sidebar **Bereich / Section** switch) for tracking a
self-chosen stock portfolio. Plain Python, **no LLM, no LangChain** — it lives
entirely on the services side of the boundary. Modules: `src/portfolio.py`
(domain + rules) and `src/prices.py` (quotes); UI in `src/app.py`.

## Philosophy: 100 baggers
Recommendations follow the *100 Baggers* research (Christopher Mayer; Thomas
Phelps, *100 to 1 in the Stock Market*): the chief enemy of a 100-bagger is
**selling too soon**, so the tracker is deliberately hold-biased. It exists to
keep the picks in view and count their progress toward 100×, **not** to generate
trade signals. Nothing here is investment advice.

## Data in/out: CSV only
No server-side storage. The portfolio *is* the user's CSV.

- **Upload** a CSV; **download** a valued snapshot CSV that re-uploads cleanly.
- Required columns: `ticker`, `quantity`, `buy_price`. Optional: `currency`,
  `thesis_broken` (a truthy flag — `true`/`1`/`yes`/`y`/`x` — that the user's
  investment thesis for that holding has broken).
- Headers are matched case-insensitively and trimmed; tickers are upper-cased.
  A missing required column or a non-numeric `quantity`/`buy_price` raises
  `ValueError` naming the offending row. `CSV_TEMPLATE` is offered as a starter
  download.

## Prices (`src/prices.py`)
`fetch_prices(tickers) -> {ticker: price | None}` fetches live quotes via
**`yfinance`** (Yahoo Finance). This is the one place the app touches the network
for market data — it is *not* a cloud LLM API, so the LangChain/LLM boundary is
untouched, but it does relax the app's "fully offline" claim **for this feature
only**. `yfinance` is imported lazily; a missing package, no network, or an
unknown ticker degrades to `None` per ticker (the fetch never raises), and the UI
falls back to **manual price entry** (`st.number_input` per unpriced ticker).
Fetching is button-driven (**Kurse aktualisieren**), never automatic, so no run
hits the network unasked.

## Metrics & rules (`src/portfolio.py`)
`build_portfolio(holdings, prices) -> Portfolio` values each holding and derives
its recommendation. Per position: `cost_basis`, `market_value`, `gain`,
`gain_pct`, `multiple` (current ÷ buy price, i.e. x-bagger progress toward
`BAGGER_GOAL = 100`) and `weight` (fraction of the *priced* positions' value, so
a partially priced portfolio still yields sensible weights). Portfolio totals:
`total_cost`, `total_value`, `total_gain`, `total_gain_pct`, and `priced`.

`recommend(position)` — precedence, hold-biased:

| Rule | When | Meaning |
|---|---|---|
| **REVIEW** 🔴 | `thesis_broken` set | Highest priority — the user flagged the thesis as broken. Selling is a manual call; never auto-derived from price. |
| **TRIM** 🟠 | `weight > CONCENTRATION_CAP` (0.25) | Risk management only, *not* profit-taking — winners are otherwise let to run. |
| **ADD** 🔵 | `gain_pct <= ADD_DIP_PCT` (−0.20) | Thesis-consistent top-up on a dip. |
| **HOLD** 🟢 | otherwise (incl. large gains, or no price) | The default and the whole point. |

Thresholds are module constants (`ADD_DIP_PCT`, `CONCENTRATION_CAP`,
`BAGGER_GOAL`), tunable in one place.

## UI (`src/app.py`)
The sidebar radio switches between **📝 Zusammenfassung** (the summarizer,
unchanged) and **📈 Portfolio**. The portfolio panel: template download → CSV
upload → **Kurse aktualisieren** → per-ticker manual inputs for anything without
a live price → totals (`st.metric`) → positions table (`st.dataframe`) with a
colour-coded recommendation column and a legend → snapshot CSV download. All
strings are German-default / English via `i18n`; recommendation labels map
through `_RECO_KEY`. Session keys: `pf_prices` (fetched quotes), `pf_manual_<T>`
(manual inputs), `mode_radio` (section).

## Tests
`tests/test_portfolio.py` (parsing, metrics, each recommendation branch,
snapshot round-trip) and `tests/test_prices.py` (mocked yfinance success, offline
fallback, error degradation) run fully offline — `yfinance` is monkeypatched via
`prices._yf`. `tests/test_app.py` covers the mode switch, upload, price fetch,
table/download rendering, and the manual-entry fallback. See
[testing.md](testing.md).

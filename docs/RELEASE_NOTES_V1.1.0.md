# Multi-Asset Market Risk Platform v1.1.0

This release turns Risk Ledger from a fixed demonstration book into a configurable, linked portfolio-risk application.

## Highlights

- Approved catalog of 26 instruments: global equity ETFs, six US stocks, credit and inflation-linked bond ETFs, four Treasury tenors, gold, silver, platinum, commodities, oil, cash, and EUR/USD.
- Four starting presets: Diversified Core, Growth Tilt, Defensive Income, and Inflation Aware.
- Portfolio Builder with add/remove selection, editable target weights, signed FX overlay, automatic residual cash, validation feedback, and an asset-class allocation preview.
- One shared calculation service recalculates portfolio history, NAV/P&L, three VaR/ES approaches, rolling backtesting, risk contributions, deterministic stress, and custom downloads from the same resolved allocation.
- Expanded 25-factor synthetic and live-data mappings plus asset-class-aware stress defaults.
- Custom in-memory Markdown reports, portfolio-definition JSON, evidence tables, and ZIP bundles.
- Thirty-four passing tests, 77% aggregate package coverage, clean Ruff, verified wheel/CLI, and Playwright desktop/mobile checks with zero overlap candidates or browser errors.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"
python -m market_risk app
```

Open `http://localhost:8501`, choose **Portfolio builder**, edit the allocation, and select **Apply portfolio & recalculate all results**.

## Evidence Boundary

The bundled 520-row, 25-factor snapshot is deterministic and synthetic. It verifies software and model mechanics; it is not historical portfolio performance, investment advice, or production/regulatory evidence.

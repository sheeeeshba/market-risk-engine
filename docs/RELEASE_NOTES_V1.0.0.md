# Multi-Asset Market Risk Platform v1.0.0

The first application-level release adds the **Risk Ledger** interactive review workspace on top of the quantitative engine introduced in v0.1.0.

## Highlights

- Seven clearly named review tabs covering overview, models, backtesting, stress, contributions, portfolio/P&L, and evidence.
- Configurable confidence level, models, chart history, money units, USD/%NAV basis, and risk-driver depth.
- Switchable model confidence curve, stress scenario set, and NAV/daily/cumulative P&L chart modes.
- Responsive financial formatting, wrapped model labels, protected plot margins, and mobile-safe horizontal tab navigation.
- Typed `MarketRiskPlatform` and `MarketRiskAnalysis` interfaces with validated artifacts and complete ZIP downloads.
- Credential-free synthetic Demo plus guarded, session-only FRED input for optional live mode.
- Twenty-eight passing tests, Python 3.11/3.12 CI, and clean desktop/mobile browser rendering checks.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"
python -m market_risk app
```

Then open `http://localhost:8501`.

## Evidence Boundary

The public Demo remains deterministic and synthetic. Its values demonstrate calculation, integration, and presentation behaviour only; they are not historical performance or production model evidence.

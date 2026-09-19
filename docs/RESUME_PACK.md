# Resume Pack

Use the engineering-only bullets in `CV_PROJECT_SECTION.md` now. They describe verified implementation scope and tests without presenting artificial values as market history. Numerical market conclusions remain blocked until a permitted real-data snapshot is verified.

## Proposed Project Title

**Multi-Asset Market Risk Platform | Python, Streamlit, Plotly, VaR, Expected Shortfall**

Do not add SQL: no SQL layer is implemented.

## Engineering Bullets

- Built a modular Python market-risk engine with a configurable 26-instrument catalog and 25 mapped risk factors, implementing Historical, Parametric Normal, and Monte Carlo VaR plus Expected Shortfall at three confidence levels.
- Developed a leak-free rolling backtesting framework with next-valid-date alignment, Kupiec and Christoffersen tests, deterministic seeds, and exception diagnostics.
- Designed duration-convexity bond P&L, direct FX overlay accounting, six hypothetical stress scenarios, distributional volatility/correlation stress, and additive position/factor risk contributions.
- Built a responsive analyst workspace with a linked add/remove/reweight portfolio builder, eight review tabs, correctly scaled USD/%NAV views, and downloadable custom evidence.
- Automated a versioned management-style report with eight generated figures, CSV evidence tables, configuration and snapshot hashes, a verification manifest, CI, and 34 tests.

These scope counts are supported by the public code and synthetic verification manifest. Do not claim business impact, users, profitability, deployment scale, production readiness, regulatory approval, or historical model performance.

## 90-Second Walkthrough Draft

“The decision question is how much a configurable multi-asset portfolio could lose over the next valid valuation interval, what drives that risk, and whether forecast exceptions behave plausibly. The user can select from 26 approved stocks, ETFs, bonds, metals, commodities, cash, and FX exposures; one validated allocation then drives every result. I separate the funded book from zero-funded FX overlays and reconcile daily P&L to NAV. I compare Historical, Parametric Normal, and full-revaluation Monte Carlo VaR and Expected Shortfall using the same 250-row information set. The rolling engine freezes end-of-date holdings and tests the next valid interval, preventing look-ahead bias. Component VaR and exact-tail Historical ES identify drivers, while six scenarios show losses outside normal conditions. The repository uses artificial data, so I present its numbers as engineering verification rather than empirical market evidence.”

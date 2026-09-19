# Changelog

## 1.1.0 — 2026-09-19

- Added a validated 26-instrument catalog spanning equity ETFs, individual stocks, credit, TIPS, four Treasury tenors, precious metals, commodities, cash, and FX.
- Added four portfolio presets and a responsive Portfolio Builder for adding/removing instruments, editing target weights, configuring the EUR/USD overlay, and calculating residual cash automatically.
- Added one linked calculation service so allocation changes recalculate NAV/P&L, all VaR/ES models, rolling backtesting, contributions, scenarios, and downloadable evidence together.
- Expanded the deterministic snapshot from 7 to 25 factors and made stress defaults asset-class aware so newly selected instruments remain covered.
- Added portable in-memory reports/ZIP bundles for custom portfolios and expanded the suite to 34 tests.

## 1.0.0 — 2026-09-17

- Added the responsive **Risk Ledger** Streamlit workspace with seven task-oriented tabs.
- Added configurable confidence, model, history, money-unit, USD/%NAV, risk-driver, scenario, model-curve, and portfolio-chart views.
- Added a typed `MarketRiskPlatform` / `MarketRiskAnalysis` application boundary and complete evidence ZIP downloads.
- Added explicit financial formatting, responsive label wrapping, chart spacing, synthetic-data classification, and live-mode credential gating.
- Added VS Code tasks, deployment/security/contribution guides, portfolio/CV copy, and a GitHub-ready dashboard screenshot.
- Expanded CI and the automated suite to 28 tests, including platform validation and Streamlit interaction tests.
- Completed desktop and mobile browser checks with no detected label overlap, console errors, or page errors.

## 0.1.0 — 2026-09-16

- Added canonical funded-book and zero-funded-value FX overlay accounting.
- Added Historical Simulation, Parametric Normal, and Monte Carlo VaR/ES at three confidence levels.
- Added leak-free rolling forecasts, Kupiec and Christoffersen backtests, and explicit low-power warnings.
- Added position, asset-class, and factor contributions plus six hypothetical scenarios.
- Added volatility/correlation stress, artificial crisis fixtures, eight figures, and automated reports.
- Added deterministic offline snapshot, optional live-data adapters, Colab notebook, CLI, and verification manifest.
- Added 22 automated tests and GitHub Actions CI.

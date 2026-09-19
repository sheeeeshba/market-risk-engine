# One-Page Engineering Project Case Study

> **Evidence boundary:** this version is suitable for discussing engineering design, controls, and validation. Its artificial market values must not be presented as historical findings or portfolio performance.

## Problem

Translate a transparent multi-asset portfolio into explainable P&L, current VaR/ES, rolling forecasts, exception diagnostics, additive risk drivers, deterministic stresses, and a reviewable analyst application.

## Portfolio and Data

The approved universe contains 26 instruments: broad equity ETFs, individual stocks, credit and inflation-linked ETFs, four synthetic duration-convexity Treasury tenors, precious metals, commodities, USD cash, and a separately accounted EUR/USD overlay. Twenty-five risk factors feed a common validated calendar. The bundled 520-row series is deterministic and artificial.

## Approach

The implementation separates the instrument catalog, user allocation, data alignment, portfolio accounting, risk models, backtesting, contributions, stresses, and reporting behind testable interfaces. A single resolved allocation drives every downstream calculation, preventing charts and headline results from drifting apart. A typed platform layer exposes both committed and in-memory custom analysis to the responsive Risk Ledger UI.

## Strongest Demonstration Chart

`outputs/figures/03_rolling_var_vs_realized_loss.png` shows how next-interval artificial losses compare with three rolling 99% VaR models. It is watermarked and cannot be presented as market history.

## Verified Engineering Results

- Implemented Historical, Parametric Normal, and full-revaluation Monte Carlo VaR/ES at three confidence levels.
- Generated 270 aligned forecasts per model from the 520-row artificial snapshot and applied Kupiec/Christoffersen diagnostics with low-power warnings.
- Reconciled six hypothetical scenarios and additive position/factor contributions; generated eight figures and a versioned report.
- Delivered eight task-oriented UI tabs, a linked add/remove/reweight portfolio builder, configurable Plotly views, consistent USD/%NAV formatting, and complete downloadable evidence bundles.

## Validation

Thirty-four automated tests cover catalog/allocation controls, linked recalculation, signs, units, data gaps, accounting, exact tail weights, covariance and seed behaviour, backtest edge cases, scenario reconciliation, platform validation, Streamlit interactions, live-mode gating, and an end-to-end small run. The verification manifest identifies commands, hashes, timestamps, input snapshot, exit status, and verified artifacts.

## Key Limitation

Artificial data validate implementation mechanics but cannot validate empirical model performance or support market conclusions.

## Before Real-World Use

Add a permitted real-data snapshot with provenance, reproduce crisis shocks from observed endpoints, run a longer out-of-sample study, validate provider terms and operational controls, replace synthetic screenshots, and subject the model to independent review.

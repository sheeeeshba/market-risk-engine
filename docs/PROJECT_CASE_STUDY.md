# One-Page Engineering Project Case Study

> **Evidence boundary:** this version is suitable for discussing engineering design, controls, and validation. Its artificial market values must not be presented as historical findings or portfolio performance.

## Problem

Translate a transparent multi-asset portfolio into explainable P&L, current VaR/ES, rolling forecasts, exception diagnostics, additive risk drivers, deterministic stresses, and a reviewable analyst application.

## Portfolio and Data

The Core portfolio contains four synthetic total-return ETF holdings, two synthetic duration-convexity Treasury positions, USD cash, and a separately accounted long-EUR overlay. Seven risk factors feed a common validated calendar. The bundled 520-row series is deterministic and artificial.

## Approach

The implementation separates data alignment, portfolio accounting, risk models, backtesting, contributions, stresses, and reporting behind testable interfaces. A typed platform layer validates artifacts before exposing them to the responsive Risk Ledger UI. Every forecast uses only information available through its forecast date. Random seeds, configuration and factor hashes, runtime versions, and outputs are recorded.

## Strongest Demonstration Chart

`outputs/figures/03_rolling_var_vs_realized_loss.png` shows how next-interval artificial losses compare with three rolling 99% VaR models. It is watermarked and cannot be presented as market history.

## Verified Engineering Results

- Implemented Historical, Parametric Normal, and full-revaluation Monte Carlo VaR/ES at three confidence levels.
- Generated 270 aligned forecasts per model from the 520-row artificial snapshot and applied Kupiec/Christoffersen diagnostics with low-power warnings.
- Reconciled six hypothetical scenarios and additive position/factor contributions; generated eight figures and a versioned report.
- Delivered seven task-oriented UI tabs, configurable Plotly views, consistent USD/%NAV formatting, and a complete downloadable evidence bundle.

## Validation

Twenty-eight automated tests cover signs, units, data gaps, accounting, exact tail weights, covariance and seed behaviour, backtest edge cases, scenario reconciliation, platform validation, Streamlit interactions, live-mode gating, and an end-to-end small run. Desktop and mobile browser checks also verify chart changes, readable labels, and error-free rendering. The verification manifest identifies commands, hashes, timestamps, input snapshot, exit status, and verified artifacts.

## Key Limitation

Artificial data validate implementation mechanics but cannot validate empirical model performance or support market conclusions.

## Before Real-World Use

Add a permitted real-data snapshot with provenance, reproduce crisis shocks from observed endpoints, run a longer out-of-sample study, validate provider terms and operational controls, replace synthetic screenshots, and subject the model to independent review.

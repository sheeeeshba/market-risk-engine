# Project Status

Last updated: 2026-09-19 (Europe/Prague)

## Current State

- The project is version-controlled and published at `https://github.com/sheeeeshba/market-risk-engine`.
- No `outputs/market_risk_engine_blueprint.md` existed; the attached master prompt is authoritative.
- A complete Core engineering path now runs from the bundled deterministic factor snapshot through P&L, three VaR/ES models, rolling backtests, contributions, stresses, eight figures, a one-page summary, and a management report.
- Version 1.1 adds a 26-instrument catalog, four presets, a linked Portfolio Builder, 25-factor data, asset-class-aware stresses, in-memory custom evidence bundles, and eight review tabs.
- The current snapshot is artificial and every generated presentation output is watermarked `SYNTHETIC DATA — NOT FOR RESUME RESULTS`.
- Historical conclusions and case-study market metrics remain blocked until a permitted real-data snapshot is verified; an explicitly watermarked recruiter screenshot and engineering-only CV bullets are ready.
- The normal wheel install and CLI were verified. A public Colab launch URL is available, while a hosted clean-Colab execution remains an explicit verification follow-up.

## Confirmed Test Seams

Tests exercise the public data/calendar, portfolio/P&L, risk-model, backtesting, contribution, stress, and report/figure interfaces. They assert observable financial behaviour rather than private implementation details.

## Canonical Decisions

- Positive P&L is profit; positive loss is `-P&L`; VaR and ES are loss magnitudes.
- Treasury changes are absolute decimal-yield changes; 100 basis points is `0.01`.
- EURUSD is USD per EUR, so a long-EUR overlay profits when EURUSD rises.
- User-selected funded assets plus automatically calculated residual cash equal 100% of NAV; the zero-funded-value FX overlay is reported separately.
- Forecasts use exactly 250 valid factor rows ending at `t`, end-of-`t` holdings, and P&L at `t_next`.
- One day means one valid common portfolio valuation interval; no square-root-of-time scaling is used.
- Core ETFs are synthetic adjusted-total-return holdings; bonds use constant duration/convexity; FX P&L settles into cash.
- Missing ETF/FX levels are never filled. Treasury levels may be forward-filled for at most three business days with flags and ages.
- No incompatible convention was found or silently combined.

## Phase Gates

| Phase | Status | Acceptance evidence |
|---|---|---|
| 0 — Inspect, decide, scaffold | COMPLETE | Structure, configuration, conventions, and independent worked examples |
| 1 — Reproducible data layer | COMPLETE FOR SYNTHETIC; LIVE UNVERIFIED | Fixed snapshot hash, calendar tests, live adapter with explicit fields and units |
| 2 — Portfolio and P&L | COMPLETE | Catalog/allocation validation, add/remove/reweight controls, position/P&L/NAV reconciliation, and rebalance tests |
| 3 — Current risk models | COMPLETE | Historical, Parametric, Monte Carlo, tail-weight, seed, and convergence evidence |
| 4 — First demonstration | PRESENTATION MECHANICS COMPLETE; REAL-DATA GATE BLOCKED | Basic stresses, artificial COVID fixture, figures, summary, README |
| 5 — Rolling forecasts | COMPLETE FOR SYNTHETIC | 270 aligned forecasts/model, statistical edge fixtures, no-future-input validation |
| 6 — Contributions and full stress | COMPLETE FOR SYNTHETIC | Position/asset-class/factor tables, six scenarios, distributional stress, three artificial replays |
| 7 — Automated reporting | COMPLETE FOR SYNTHETIC | Strict template, 8 PNGs, 15+ evidence files, warnings and watermarks |
| 8 — Refactor and reproduce | COMPLETE LOCALLY; HOSTED COLAB FOLLOW-UP | 34 tests, lint, clean install/CLI, platform/UI tests; hosted Colab execution not yet verified |
| 9 — Recruiter package | ENGINEERING VERSION COMPLETE | Public GitHub repository, dashboard screenshot, and evidence-limited CV/LinkedIn copy ready; market-result claims remain blocked on real data |

## Latest Executed Results

- Snapshot pipeline command: exit status 0.
- Pytest: 34 passed; non-failing Seaborn pending-deprecation warnings may appear during figure tests.
- Ruff: all checks passed.
- Browser UX check: desktop and 430-pixel mobile views rendered with no detected text/chart-label overlaps, console errors, or page errors.
- Monte Carlo convergence: all three 50k-versus-100k 99% VaR comparisons are below the approximate 2% target; ES differences are reported separately.
- Outputs: one multi-section report, one-page summary, eight figures, current/rolling/stress/contribution/convergence tables, diagnostics JSON, and verification manifest.

## Known Limitations and Honest Blocks

- No verified redistributable real-data snapshot is bundled.
- Live retrieval was not executed because this workspace has no user FRED credential; the adapter is implemented but not acceptance-tested.
- Artificial crisis shocks validate calculation and presentation only, not historical replay accuracy.
- Backtesting has 2.7 expected 99% exceptions per model and therefore emits low-power warnings.
- The public notebook defaults to the published repository; a clean hosted Colab execution has not yet been recorded in the manifest.

## Progress Contract

1. Files created/changed: instrument catalog and portfolio domain, shared calculation service, typed application layer, Streamlit dashboard, configurations, tests/fixtures, deterministic snapshot, report template, generated evidence, README, case study, and CV material.
2. Functionality completed: linked custom-portfolio recalculation across the full synthetic Core flow, configurable review workspace, portable downloads, and optional guarded live adapter.
3. Commands executed: normal install, exact CLI snapshot run, pytest with coverage, Ruff, Streamlit AppTest, and desktop/mobile browser interaction checks.
4. Actual result: Core mechanics work and reconcile; recruiter/historical evidence is deliberately not claimed.
5. Assumptions: zero cash return, constant bond sensitivities between rebalances, zero-mean primary Normal models, sample covariance, and artificial offline factors.
6. Next gate: create a permitted real snapshot with provenance, reproduce crisis endpoints, run the notebook in fresh Colab, replace watermarked outputs, and rerun all manifest gates.

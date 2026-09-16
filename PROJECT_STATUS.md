# Project Status

Last updated: 2026-09-16 (Europe/Prague)

## Current State

- The workspace was empty at project start and is not a Git repository.
- No `outputs/market_risk_engine_blueprint.md` existed; the attached master prompt is authoritative.
- A complete Core engineering path now runs from the bundled deterministic factor snapshot through P&L, three VaR/ES models, rolling backtests, contributions, stresses, eight figures, a one-page summary, and a management report.
- The current snapshot is artificial and every generated presentation output is watermarked `SYNTHETIC DATA — NOT FOR RESUME RESULTS`.
- Historical conclusions, a recruiter screenshot, case-study market metrics, and resume bullets remain blocked until a permitted real-data snapshot is verified.
- The normal wheel install and CLI were verified. A hosted clean-Colab run remains blocked until the repository has a public clone URL.

## Confirmed Test Seams

Tests exercise the public data/calendar, portfolio/P&L, risk-model, backtesting, contribution, stress, and report/figure interfaces. They assert observable financial behaviour rather than private implementation details.

## Canonical Decisions

- Positive P&L is profit; positive loss is `-P&L`; VaR and ES are loss magnitudes.
- Treasury changes are absolute decimal-yield changes; 100 basis points is `0.01`.
- EURUSD is USD per EUR, so a long-EUR overlay profits when EURUSD rises.
- Funded assets and cash equal NAV; the zero-funded-value FX overlay is reported separately.
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
| 2 — Portfolio and P&L | COMPLETE | Position/P&L/NAV reconciliation and rebalance tests |
| 3 — Current risk models | COMPLETE | Historical, Parametric, Monte Carlo, tail-weight, seed, and convergence evidence |
| 4 — First demonstration | PRESENTATION MECHANICS COMPLETE; REAL-DATA GATE BLOCKED | Basic stresses, artificial COVID fixture, figures, summary, README |
| 5 — Rolling forecasts | COMPLETE FOR SYNTHETIC | 270 aligned forecasts/model, statistical edge fixtures, no-future-input validation |
| 6 — Contributions and full stress | COMPLETE FOR SYNTHETIC | Position/asset-class/factor tables, six scenarios, distributional stress, three artificial replays |
| 7 — Automated reporting | COMPLETE FOR SYNTHETIC | Strict template, 8 PNGs, 15+ evidence files, warnings and watermarks |
| 8 — Refactor and reproduce | PARTIAL | 22 tests and clean wheel/CLI pass; hosted Colab run not yet verified |
| 9 — Recruiter package | BLOCKED ON REAL DATA AND COLAB | Evidence-limited drafts exist and are prominently blocked |

## Latest Executed Results

- Snapshot pipeline command: exit status 0.
- Pytest: 22 passed; two non-failing Seaborn pending-deprecation warnings.
- Ruff: all checks passed.
- Monte Carlo convergence: all three 50k-versus-100k 99% VaR comparisons are below the approximate 2% target; ES differences are reported separately.
- Outputs: one multi-section report, one-page summary, eight figures, current/rolling/stress/contribution/convergence tables, diagnostics JSON, and verification manifest.

## Known Limitations and Honest Blocks

- No verified redistributable real-data snapshot is bundled.
- Live retrieval was not executed because this workspace has no user FRED credential; the adapter is implemented but not acceptance-tested.
- Artificial crisis shocks validate calculation and presentation only, not historical replay accuracy.
- Backtesting has 2.7 expected 99% exceptions per model and therefore emits low-power warnings.
- No Git commit hash is available; the manifest records a workspace tree hash instead.
- Colab setup requires a published repository URL supplied through the `MARKET_RISK_REPO_URL` Secret.

## Progress Contract

1. Files created/changed: modular package, configurations, tests/fixtures, deterministic snapshot, notebook, report template, generated evidence, README, methodology, validation, limitation, case-study, interview, and blocked resume documentation.
2. Functionality completed: full Core engineering flow on synthetic data plus optional live adapter.
3. Commands executed: normal wheel install, exact CLI snapshot run, pytest, Ruff, JSON/placeholder scans, and visual inspection of key figures.
4. Actual result: Core mechanics work and reconcile; recruiter/historical evidence is deliberately not claimed.
5. Assumptions: zero cash return, constant bond sensitivities between rebalances, zero-mean primary Normal models, sample covariance, and artificial offline factors.
6. Next gate: publish the repository, create a permitted real snapshot with provenance, reproduce crisis endpoints, run the notebook in fresh Colab, replace watermarked outputs, and rerun all manifest gates.


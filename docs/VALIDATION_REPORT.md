# Validation Report

## Scope

Validation covers the artificial offline snapshot and the Core calculation interfaces. Live provider retrieval is implemented but has not been acceptance-tested with credentials in this workspace.

## Executed Evidence

- End-to-end snapshot command completed with exit status 0.
- Full pytest suite completed successfully; see `outputs/verification_manifest.json` for the current recorded gate after the final test run.
- The integration test created eight figures and a report from a small portfolio flow.
- The production snapshot run created the required report, 16 CSV tables, and eight PNG figures.
- Thirty-four automated tests pass with 77% aggregate package coverage, including allocation, linked recalculation, typed platform, and Streamlit interaction suites.
- Desktop and 430-pixel mobile browser checks changed presets, applied a custom portfolio, and found no text/chart-label overlaps, console errors, or page errors.

## Covered Controls

- Deterministic synthetic generation and no missing factor values.
- Market-price/FX no-fill rule, limited and flagged rate fill, multi-civil-day interval flag.
- Catalog uniqueness, add/remove/reweight allocation, automatic residual cash, NAV identity, overlay exclusion, and monthly post-close rebalance.
- Long equity, long bond, convexity, and long-EUR sign checks.
- Exact tied-boundary Historical ES weights and effective tail mass.
- Confidence monotonicity, zero covariance, Normal closed-form check, Monte Carlo seed reproducibility.
- Additive position/factor Parametric VaR and Historical ES contributions.
- Six scenario reconciliation and distributional-stress semantics.
- Kupiec and Christoffersen zero/all/missing-transition handling and intentional date-alignment failure.
- End-to-end artifact existence and report metadata propagation.
- Eight dashboard tabs, preset selection, custom Apply workflow, configurable view controls, committed/custom downloads, and live-mode credential gating.

## Observed Warnings

- The bundled rolling 99% backtest has fewer than five expected exceptions and unstable transition cell counts.
- Seaborn emits a pending-deprecation warning for internal heat-map missing-value coloring; outputs are unaffected.
- Normal wheel installation of version 1.1.0 and the CLI import seam were verified.

## Blocked Validation

- Real-data snapshot provenance and historical crisis endpoint reproduction.
- Clean hosted Google Colab execution from a published public repository.
- Live-mode provider integration with a user FRED key.
- Any claim of production, regulatory, or resume-ready historical performance.

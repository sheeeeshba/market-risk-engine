# One-Page Market Risk Summary — 2024-12-31

> **SYNTHETIC DATA — NOT FOR RESUME RESULTS.** Educational model — not approved for regulatory capital or live trading limits.

- NAV: **USD 9,117,367**; funded gross exposure: **USD 9,117,367**; overlay notional: **USD 676,322**.
- 99% one-interval VaR range across Core models: **USD 90,233–USD 91,731**.
- 97.5% ES range: **USD 91,534–USD 97,676**.
- Largest component-VaR driver: **SPY**, USD 42,249.
- Worst hypothetical stress: **Stocks and Bonds Fall Together**, loss USD 1,043,993 (11.45% of NAV).
- Backtesting: **270 forecasts per model**; warnings: LOW_POWER_FEWER_THAN_5_EXPECTED_EXCEPTIONS, UNSTABLE_TRANSITION_COUNTS.
- Monte Carlo convergence: maximum 50k-vs-100k 99% VaR difference **0.83%**; ES difference **1.05%**.

Primary control: every forecast uses only information through its forecast date and next-valid-date hypothetical P&L. Primary limitation: the bundled results use artificial data and cannot support historical or resume claims.

![Rolling VaR versus realized loss](../../outputs/figures/03_rolling_var_vs_realized_loss.png)

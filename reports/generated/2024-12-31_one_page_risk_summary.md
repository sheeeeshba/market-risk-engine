# One-Page Market Risk Summary — 2024-12-31

> **SYNTHETIC DATA — NOT FOR RESUME RESULTS.** Educational model — not approved for regulatory capital or live trading limits.

- NAV: **USD 9,064,211**; funded gross exposure: **USD 9,064,211**; overlay notional: **USD 462,203**.
- 99% one-interval VaR range across Core models: **USD 89,345–USD 93,934**.
- 97.5% ES range: **USD 89,768–USD 94,011**.
- Largest component-VaR driver: **SPY**, USD 16,838.
- Worst hypothetical stress: **Stocks and Bonds Fall Together**, loss USD 1,254,378 (13.84% of NAV).
- Backtesting: **270 forecasts per model**; warnings: LOW_POWER_FEWER_THAN_5_EXPECTED_EXCEPTIONS, UNSTABLE_TRANSITION_COUNTS.
- Monte Carlo convergence: maximum 50,000-vs-100,000 99% VaR difference **0.28%**; ES difference **0.75%**.

Primary control: every forecast uses only information through its forecast date and next-valid-date hypothetical P&L. Primary limitation: the bundled results use artificial data and cannot support historical or resume claims.

![Rolling VaR versus realized loss](../../outputs/figures/03_rolling_var_vs_realized_loss.png)

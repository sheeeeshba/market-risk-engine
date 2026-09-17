# Interview Guide

## 1. What does 99% one-interval VaR mean?

It is a loss threshold estimated so that approximately 1% of comparable next valid valuation intervals are expected to exceed it under the model. It is not the maximum possible loss, a guarantee, or a multi-day crisis estimate.

## 2. Why report Expected Shortfall as well?

VaR identifies a threshold but says nothing about losses beyond it. ES averages tail losses using the paired estimator. In this project, 99% Historical ES with 250 rows has only 2.5 effective observations, so it is visibly unstable.

## 3. Why can the three models differ?

Historical Simulation retains empirical joint shocks and nonlinear bond convexity but has sparse tails. Parametric Normal is transparent and additive but linear and distribution-dependent. Monte Carlo uses the same Normal covariance assumption but fully revalues the bond convexity term and adds simulation error.

## 4. How is look-ahead bias prevented?

For forecast date `t`, the engine selects exactly 250 rows ending at `t`, uses end-of-`t` holdings, and compares the forecast with portfolio P&L on the next valid date. The output records `max_input_date`, `forecast_date`, `expected_next_date`, and `realized_date`; validation hard-fails future inputs or a one-day alignment error.

## 5. What is Hypothetical rather than Actual P&L here?

Hypothetical P&L applies market moves to the controlled Core representation and its scheduled monthly rebalance rules. It omits fees, taxes, intraday trading, carry, cash interest, external flows, and other actual desk effects.

## 6. Kupiec versus Christoffersen?

Kupiec asks whether the total exception rate matches the nominal rate. Christoffersen asks whether breaches cluster through transition probabilities. Conditional coverage combines both. With few expected breaches, non-rejection has low power and does not prove correctness.

## 7. Explain duration, convexity, and DV01.

Modified duration gives the first-order inverse relationship between yield and bond price. Convexity adds the second-order curvature and offsets some loss for a positive-convexity long bond when yields rise. DV01 is the approximate loss sensitivity to a +1 bp yield move under the report convention.

## 8. What is the FX quote risk?

EURUSD is USD per EUR. A positive return means EUR strengthens, so the long-EUR overlay gains. EFA is already represented by its USD-listed adjusted-return factor, so adding EURUSD to it would double-count currency risk.

## 9. Why can a component contribution be negative?

Euler contribution measures interaction with total portfolio risk, not standalone risk. A position negatively correlated with the rest can reduce total variance and therefore have a legitimate negative component VaR. The code does not floor it to zero.

## 10. Why does volatility stress not create immediate P&L?

Volatility is a property of a distribution, not a realized deterministic shock. Scaling volatilities and replacing correlations changes VaR/ES. Immediate P&L requires a specified factor move.

## 11. What Python design choice matters most?

Finance logic is behind small public interfaces that return data rather than hiding state in notebook cells. `MarketRiskPlatform` validates the evidence and returns one typed result used by the Streamlit UI and downloads. The same engine interfaces serve the CLI, notebook, and tests. Dependencies and configuration are inputs, deterministic results are outputs, and side effects are concentrated in snapshot/report adapters.

## 12. What would you improve first?

Replace the artificial snapshot with permitted real data and reproduce crisis endpoint shocks. Then extend out-of-sample evidence before considering one challenger such as EWMA. Full bond cash-flow repricing and stronger operational governance come before any production claim.

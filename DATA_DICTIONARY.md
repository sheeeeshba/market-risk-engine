# Data Dictionary

All amounts are USD unless explicitly stated. Positive P&L is profit; positive loss is loss.

## Risk-Factor Snapshot

| Field | Unit | Definition |
|---|---|---|
| `portfolio_date` | date | Valid common portfolio valuation date. |
| `SPY_RETURN` | decimal return | Adjusted simple return for the synthetic SPY total-return holding. |
| `QQQ_RETURN` | decimal return | Adjusted simple return for the synthetic QQQ total-return holding. |
| `EFA_RETURN` | decimal return | Adjusted simple return for the USD-listed EFA factor; no second FX shock is applied. |
| `GLD_RETURN` | decimal return | Adjusted simple return for the synthetic GLD total-return holding. |
| `DGS5_CHANGE` | decimal yield change | Absolute change in the 5Y Treasury yield; `0.01` is 100 bp. |
| `DGS10_CHANGE` | decimal yield change | Absolute change in the 10Y Treasury yield; `0.01` is 100 bp. |
| `EURUSD_RETURN` | decimal return | Simple return of USD per EUR; positive means EUR strengthens. |

## Position State

| Field | Unit | Definition |
|---|---|---|
| `market_value` | USD | Signed funded book market value; zero for the FX overlay. |
| `notional` | USD-equivalent | Signed overlay risk notional; not included in the NAV identity. |
| `modified_duration` | years approximation | First-order bond price sensitivity to a decimal yield change. |
| `convexity` | per decimal-yield squared | Second-order bond price sensitivity. |
| `target_weight` | fraction of NAV | Recurring funded target weight. |
| `holdings_version` | integer | Increments after each monthly close rebalance. |

## Daily Portfolio Output

| Field | Unit | Definition |
|---|---|---|
| `portfolio_pnl` | USD | Sum of position P&L; FX P&L is included once and settled into cash. |
| `portfolio_loss` | USD | `-portfolio_pnl`. |
| `nav` | USD | Funded ETF and bond book values plus cash. |
| `gross_funded_exposure` | USD | Sum of absolute funded market values. |
| `overlay_notional` | USD-equivalent | Absolute FX overlay notional, reported separately. |
| `rebalanced` | boolean | True when post-P&L holdings were reset after the first valid close of a month. |

## Risk and Backtesting Output

| Field | Unit | Definition |
|---|---|---|
| `var` | USD loss | Confidence-level loss threshold. |
| `es` | USD loss | Tail-weighted average loss beyond the paired VaR threshold. |
| `forecast_date` | date | Close after which the forecast is produced. |
| `realized_date` | date | Next valid common valuation date used for hypothetical P&L. |
| `exception` | boolean | True only when realized loss is strictly greater than VaR. |
| `breach_magnitude` | USD | `max(realized_loss - VaR, 0)`. |
| `component_var` | USD loss | Additive Euler contribution to Parametric VaR; may be negative. |
| `historical_es_contribution` | USD loss | Position loss averaged with exact portfolio-tail scenario weights. |


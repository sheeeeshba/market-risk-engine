# Data Dictionary

All amounts are USD unless explicitly stated. Positive P&L is profit; positive loss is loss.

## Risk-Factor Snapshot

| Field | Unit | Definition |
|---|---|---|
| `portfolio_date` | date | Valid common portfolio valuation date. |
| `SPY_RETURN` … `XOM_RETURN` | decimal return | Adjusted simple returns for six equity/real-estate ETFs and six individual US stocks. |
| `LQD_RETURN`, `HYG_RETURN`, `TIP_RETURN` | decimal return | Adjusted simple returns for investment-grade credit, high-yield credit, and inflation-linked bond ETFs. |
| `GLD_RETURN`, `SLV_RETURN`, `PPLT_RETURN` | decimal return | Adjusted simple returns for gold, silver, and platinum instruments. |
| `DBC_RETURN`, `USO_RETURN` | decimal return | Adjusted simple returns for broad commodities and oil. |
| `DGS2_CHANGE`, `DGS5_CHANGE`, `DGS10_CHANGE`, `DGS30_CHANGE` | decimal yield change | Absolute Treasury yield changes by tenor; `0.01` is 100 bp. |
| `EURUSD_RETURN` | decimal return | Simple return of USD per EUR; positive means EUR strengthens. |

The canonical ordered list is exported as `market_risk.data_pipeline.FACTOR_COLUMNS`; `config/instrument_catalog.yaml` maps every non-cash instrument to exactly one factor.

## Position State

| Field | Unit | Definition |
|---|---|---|
| `market_value` | USD | Signed funded book market value; zero for the FX overlay. |
| `notional` | USD-equivalent | Signed overlay risk notional; not included in the NAV identity. |
| `modified_duration` | years approximation | First-order bond price sensitivity to a decimal yield change. |
| `convexity` | per decimal-yield squared | Second-order bond price sensitivity. |
| `target_weight` | fraction of NAV | Recurring funded target weight. |
| `holdings_version` | integer | Increments after each monthly close rebalance. |

## Portfolio Allocation Input

| Field | Unit | Definition |
|---|---|---|
| `funded_weights` | fraction of NAV | User-selected non-cash target weights; each must be non-negative and their sum cannot exceed 1.0. |
| `residual_cash_weight` | fraction of NAV | Automatically calculated as `1.0 - sum(funded_weights)`. |
| `overlay_fractions` | fraction of NAV notional | Signed zero-funded FX overlay targets, reported separately from the funding identity. |
| `preset_key` | identifier | Optional named starting allocation; becomes null after custom editing. |

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

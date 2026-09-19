# Diversified Multi-Asset Demonstration Portfolio — Diversified Core — Market Risk Report

> **SYNTHETIC DATA — NOT FOR RESUME RESULTS.** Educational model — not approved for regulatory capital or live trading limits.

| Governance field | Value |
|---|---|
| Valuation date | 2024-12-31 |
| Base currency | USD |
| Model version | 1.1.0 |
| Data source / snapshot | Deterministic artificial latent-factor generator / `synthetic_demo_seed42_n520_end2024-12-31` |
| Data retrieval or creation time | 2026-09-19T12:35:06.537394+00:00 |
| Lookback | 250 valid portfolio intervals |
| Confidence levels | 95.0%, 97.5%, 99.0% |
| Monte Carlo paths / seed | 50,000 / 42 |
| Configuration hash | `fb9c2f366244ef728c5a85ec678d31c3820c30f0f5bc3f4f329490851215f543` |
| Runtime | python 3.14.2, numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, matplotlib 3.11.2 |
| Generated UTC | 2026-09-19T12:51:37.168198+00:00 |

## Executive Summary

- NAV: **USD 9,064,211**; gross funded exposure: **USD 9,064,211**; overlay notional: **USD 462,203**.
- Primary 99% VaR ranges from **USD 89,345** to **USD 93,934** across the three Core models.
- Primary 97.5% ES ranges from **USD 89,768** to **USD 94,011**.
- Largest Parametric component-VaR driver: **SPY** (USD 16,838).
- Worst configured deterministic stress: **Stocks and Bonds Fall Together**, loss **USD 1,254,378** (13.84% of NAV).
- Backtesting generated **270** leak-free next-interval forecasts per model; interpretation is subject to the warnings below.

## Portfolio and Sensitivities

| position_id    | instrument_type   | asset_class             | factor        | market_value   | notional    |
|:---------------|:------------------|:------------------------|:--------------|:---------------|:------------|
| SPY            | etf               | US Equity               | SPY_RETURN    | USD 899,002    | USD 0       |
| QQQ            | etf               | US Equity               | QQQ_RETURN    | USD 435,710    | USD 0       |
| IWM            | etf               | US Equity               | IWM_RETURN    | USD 363,081    | USD 0       |
| EFA            | etf               | International Equity    | EFA_RETURN    | USD 630,658    | USD 0       |
| EEM            | etf               | Emerging Markets Equity | EEM_RETURN    | USD 359,807    | USD 0       |
| VNQ            | etf               | Real Estate             | VNQ_RETURN    | USD 276,421    | USD 0       |
| AAPL           | equity            | US Equity               | AAPL_RETURN   | USD 177,623    | USD 0       |
| MSFT           | equity            | US Equity               | MSFT_RETURN   | USD 181,085    | USD 0       |
| JPM            | equity            | US Equity               | JPM_RETURN    | USD 184,262    | USD 0       |
| JNJ            | equity            | US Equity               | JNJ_RETURN    | USD 179,820    | USD 0       |
| XOM            | equity            | US Equity               | XOM_RETURN    | USD 184,379    | USD 0       |
| LQD            | etf               | Investment Grade Credit | LQD_RETURN    | USD 545,661    | USD 0       |
| HYG            | etf               | High Yield Credit       | HYG_RETURN    | USD 360,171    | USD 0       |
| TIP            | etf               | Inflation-Linked Bonds  | TIP_RETURN    | USD 458,280    | USD 0       |
| US2Y           | bond              | Government Bonds        | DGS2_CHANGE   | USD 461,851    | USD 0       |
| US5Y           | bond              | Government Bonds        | DGS5_CHANGE   | USD 551,684    | USD 0       |
| US10Y          | bond              | Government Bonds        | DGS10_CHANGE  | USD 555,252    | USD 0       |
| US30Y          | bond              | Government Bonds        | DGS30_CHANGE  | USD 269,117    | USD 0       |
| GLD            | etf               | Precious Metals         | GLD_RETURN    | USD 544,671    | USD 0       |
| SLV            | etf               | Precious Metals         | SLV_RETURN    | USD 184,967    | USD 0       |
| PPLT           | etf               | Precious Metals         | PPLT_RETURN   | USD 95,176     | USD 0       |
| DBC            | etf               | Commodities             | DBC_RETURN    | USD 360,570    | USD 0       |
| USO            | etf               | Commodities             | USO_RETURN    | USD 160,835    | USD 0       |
| USD_CASH       | cash              | Cash                    | CASH_RETURN   | USD 644,127    | USD 0       |
| EURUSD_OVERLAY | fx_forward        | FX                      | EURUSD_RETURN | USD 0          | USD 462,203 |

Total signed DV01 reports the approximate loss for a +1 bp parallel yield move: **USD 1,238**. A positive DV01 is a loss sensitivity for the long positive-duration Core bond book.

![Exposure by asset class and factor](../../outputs/figures/01_exposure_by_asset_class_and_factor.png)

## Current VaR and Expected Shortfall

|                               | var        | es          | var_pct_nav   | es_pct_nav   |
|:------------------------------|:-----------|:------------|:--------------|:-------------|
| ('Historical', 0.95)          | USD 68,694 | USD 85,164  | 0.76%         | 0.94%        |
| ('Parametric Normal', 0.95)   | USD 63,412 | USD 79,522  | 0.70%         | 0.88%        |
| ('Monte Carlo Normal', 0.95)  | USD 63,657 | USD 79,392  | 0.70%         | 0.88%        |
| ('Historical', 0.975)         | USD 84,151 | USD 94,011  | 0.93%         | 1.04%        |
| ('Parametric Normal', 0.975)  | USD 75,560 | USD 90,127  | 0.83%         | 0.99%        |
| ('Monte Carlo Normal', 0.975) | USD 75,645 | USD 89,768  | 0.83%         | 0.99%        |
| ('Historical', 0.99)          | USD 93,934 | USD 104,844 | 1.04%         | 1.16%        |
| ('Parametric Normal', 0.99)   | USD 89,685 | USD 102,749 | 0.99%         | 1.13%        |
| ('Monte Carlo Normal', 0.99)  | USD 89,345 | USD 101,948 | 0.99%         | 1.12%        |

Historical ES uses exactly 6.25 effective observations at the primary ES confidence. Small effective tail mass makes the estimate unstable; 99% ES from 250 observations would use only 2.5 effective observations.

### Monte Carlo Convergence

|   seed |   comparison_low_paths |   comparison_high_paths | var_abs_difference_pct   | es_abs_difference_pct   | var_target_below_2pct   |
|-------:|-----------------------:|------------------------:|:-------------------------|:------------------------|:------------------------|
|     42 |                  50000 |                  100000 | 0.28%                    | 0.01%                   | True                    |
|    314 |                  50000 |                  100000 | 0.18%                    | 0.75%                   | True                    |
|   2026 |                  50000 |                  100000 | 0.27%                    | 0.08%                   | True                    |

The maximum absolute 50,000-versus-100,000-path difference across three seeds is 0.28% for 99% VaR and 0.75% for ES. The approximate 2% VaR convergence target is evaluated per seed in the table.

![Loss distribution](../../outputs/figures/02_loss_distribution_var_es.png)

## Risk Contributions

| position_id    | component_var   | historical_es_contribution   | asset_class             | factor        |
|:---------------|:----------------|:-----------------------------|:------------------------|:--------------|
| SPY            | USD 16,838      | USD 16,092                   | US Equity               | SPY_RETURN    |
| QQQ            | USD 9,664       | USD 10,044                   | US Equity               | QQQ_RETURN    |
| IWM            | USD 6,887       | USD 7,592                    | US Equity               | IWM_RETURN    |
| EFA            | USD 10,200      | USD 9,380                    | International Equity    | EFA_RETURN    |
| EEM            | USD 6,611       | USD 7,321                    | Emerging Markets Equity | EEM_RETURN    |
| VNQ            | USD 3,668       | USD 4,552                    | Real Estate             | VNQ_RETURN    |
| AAPL           | USD 3,874       | USD 3,855                    | US Equity               | AAPL_RETURN   |
| MSFT           | USD 3,504       | USD 4,117                    | US Equity               | MSFT_RETURN   |
| JPM            | USD 2,859       | USD 2,554                    | US Equity               | JPM_RETURN    |
| JNJ            | USD 1,330       | USD 615                      | US Equity               | JNJ_RETURN    |
| XOM            | USD 2,517       | USD 2,599                    | US Equity               | XOM_RETURN    |
| LQD            | USD 2,400       | USD 4,265                    | Investment Grade Credit | LQD_RETURN    |
| HYG            | USD 3,823       | USD 5,509                    | High Yield Credit       | HYG_RETURN    |
| TIP            | USD 1,708       | USD 3,305                    | Inflation-Linked Bonds  | TIP_RETURN    |
| US2Y           | USD 177         | USD 120                      | Government Bonds        | DGS2_CHANGE   |
| US5Y           | USD 579         | USD 799                      | Government Bonds        | DGS5_CHANGE   |
| US10Y          | USD 1,281       | USD 906                      | Government Bonds        | DGS10_CHANGE  |
| US30Y          | USD 1,467       | USD 1,144                    | Government Bonds        | DGS30_CHANGE  |
| GLD            | USD 2,284       | USD 1,285                    | Precious Metals         | GLD_RETURN    |
| SLV            | USD 1,737       | USD 1,984                    | Precious Metals         | SLV_RETURN    |
| PPLT           | USD 873         | USD 563                      | Precious Metals         | PPLT_RETURN   |
| DBC            | USD 2,059       | USD 3,275                    | Commodities             | DBC_RETURN    |
| USO            | USD 1,486       | USD 1,082                    | Commodities             | USO_RETURN    |
| USD_CASH       | USD 0           | USD 0                        | Cash                    | CASH_RETURN   |
| EURUSD_OVERLAY | USD 1,861       | USD 1,052                    | FX                      | EURUSD_RETURN |

The position contributions reconcile to total Parametric VaR. Negative contributions are retained as genuine diversification or hedge effects.

Top-three component-VaR concentration is **40.92%**. Negative primary Parametric contributions: **None in the primary Parametric decomposition**.

### Asset-Class Contributions

| asset_class             | component_var   | historical_es_contribution   |
|:------------------------|:----------------|:-----------------------------|
| US Equity               | USD 47,472      | USD 47,470                   |
| International Equity    | USD 10,200      | USD 9,380                    |
| Emerging Markets Equity | USD 6,611       | USD 7,321                    |
| Real Estate             | USD 3,668       | USD 4,552                    |
| Investment Grade Credit | USD 2,400       | USD 4,265                    |
| High Yield Credit       | USD 3,823       | USD 5,509                    |
| Inflation-Linked Bonds  | USD 1,708       | USD 3,305                    |
| Government Bonds        | USD 3,504       | USD 2,970                    |
| Precious Metals         | USD 4,894       | USD 3,831                    |
| Commodities             | USD 3,545       | USD 4,357                    |
| Cash                    | USD 0           | USD 0                        |
| FX                      | USD 1,861       | USD 1,052                    |

### Factor Contributions

| factor        | exposure       | component_var   | historical_es_contribution   |
|:--------------|:---------------|:----------------|:-----------------------------|
| SPY_RETURN    | USD 899,002    | USD 16,838      | USD 16,092                   |
| QQQ_RETURN    | USD 435,710    | USD 9,664       | USD 10,044                   |
| IWM_RETURN    | USD 363,081    | USD 6,887       | USD 7,592                    |
| EFA_RETURN    | USD 630,658    | USD 10,200      | USD 9,380                    |
| EEM_RETURN    | USD 359,807    | USD 6,611       | USD 7,321                    |
| VNQ_RETURN    | USD 276,421    | USD 3,668       | USD 4,552                    |
| AAPL_RETURN   | USD 177,623    | USD 3,874       | USD 3,855                    |
| MSFT_RETURN   | USD 181,085    | USD 3,504       | USD 4,117                    |
| JPM_RETURN    | USD 184,262    | USD 2,859       | USD 2,554                    |
| JNJ_RETURN    | USD 179,820    | USD 1,330       | USD 615                      |
| XOM_RETURN    | USD 184,379    | USD 2,517       | USD 2,599                    |
| LQD_RETURN    | USD 545,661    | USD 2,400       | USD 4,265                    |
| HYG_RETURN    | USD 360,171    | USD 3,823       | USD 5,509                    |
| TIP_RETURN    | USD 458,280    | USD 1,708       | USD 3,305                    |
| DGS2_CHANGE   | USD -877,517   | USD 177         | USD 120                      |
| DGS5_CHANGE   | USD -2,482,578 | USD 579         | USD 799                      |
| DGS10_CHANGE  | USD -4,442,014 | USD 1,281       | USD 906                      |
| DGS30_CHANGE  | USD -4,574,983 | USD 1,467       | USD 1,144                    |
| GLD_RETURN    | USD 544,671    | USD 2,284       | USD 1,285                    |
| SLV_RETURN    | USD 184,967    | USD 1,737       | USD 1,984                    |
| PPLT_RETURN   | USD 95,176     | USD 873         | USD 563                      |
| DBC_RETURN    | USD 360,570    | USD 2,059       | USD 3,275                    |
| USO_RETURN    | USD 160,835    | USD 1,486       | USD 1,082                    |
| EURUSD_RETURN | USD 462,203    | USD 1,861       | USD 1,052                    |

![Position risk contribution](../../outputs/figures/06_position_risk_contribution.png)

## Rolling Forecasts and Backtesting

|                              |   forecasts |   exceptions |   expected_exceptions |   p_value_uc |   p_value_ind |   p_value_cc |
|:-----------------------------|------------:|-------------:|----------------------:|-------------:|--------------:|-------------:|
| ('Historical', 0.99)         |         270 |            2 |                   2.7 |        0.654 |         0.863 |        0.891 |
| ('Parametric Normal', 0.99)  |         270 |            2 |                   2.7 |        0.654 |         0.863 |        0.891 |
| ('Monte Carlo Normal', 0.99) |         270 |            2 |                   2.7 |        0.654 |         0.863 |        0.891 |

Statistical non-rejection does not prove model correctness. Kupiec tests unconditional coverage; Christoffersen tests exception independence. This project does not claim a complete regulatory ES backtest.

- Warning: `LOW_POWER_FEWER_THAN_5_EXPECTED_EXCEPTIONS`
- Warning: `UNSTABLE_TRANSITION_COUNTS`

![Rolling VaR](../../outputs/figures/03_rolling_var_vs_realized_loss.png)

![Exception timeline](../../outputs/figures/04_exception_timeline.png)

![Backtesting scorecard](../../outputs/figures/05_backtesting_scorecard.png)

## Hypothetical Stress Tests

| scenario_id                   | scenario_name                                | scenario_loss   | loss_pct_nav   | principal_loss_driver   |
|:------------------------------|:---------------------------------------------|:----------------|:---------------|:------------------------|
| global_equity_selloff         | Global Equity Selloff                        | USD 898,186     | 9.91%          | SPY                     |
| parallel_rates_up_100bp       | Parallel Rates +100 bps                      | USD 116,957     | 1.29%          | US10Y                   |
| parallel_rates_up_200bp       | Parallel Rates +200 bps                      | USD 220,286     | 2.43%          | US10Y                   |
| foreign_currencies_down_10pct | Foreign Currencies Depreciate 10% versus USD | USD 46,220      | 0.51%          | EURUSD_OVERLAY          |
| stocks_and_bonds_fall         | Stocks and Bonds Fall Together               | USD 1,254,378   | 13.84%         | SPY                     |
| flight_to_quality             | Flight to Quality                            | USD 739,979     | 8.16%          | SPY                     |

Scenario gains remain negative losses; they are not floored to zero. ETF shocks apply to USD-listed total-return factors, and EURUSD shocks apply only to the direct FX overlay.

![Stress waterfall](../../outputs/figures/07_stress_loss_waterfall.png)

## Historical-Crisis Replay Archive

| scenario_id                    | scenario_name                                   | horizon                            | scenario_loss   | loss_pct_nav   |
|:-------------------------------|:------------------------------------------------|:-----------------------------------|:----------------|:---------------|
| gfc_lehman_synthetic           | GFC / Lehman Window (Artificial Fixture)        | 2008-09-15_to_2008-10-10_multi_day | USD 1,505,735   | 16.61%         |
| covid_2020_synthetic           | COVID-19 Window (Artificial Fixture)            | 2020-02-19_to_2020-03-23_multi_day | USD 1,602,034   | 17.67%         |
| inflation_rates_2022_synthetic | Inflation and Rates Window (Artificial Fixture) | 2022-01-03_to_2022-10-12_multi_day | USD 1,573,911   | 17.36%         |

These are multi-day scenario replays and are not comparable horizons to the one-valid-interval VaR. The archive currently contains artificial shocks only and cannot be described as observed crisis performance.
## Volatility and Correlation Stress

|   volatility_scale | immediate_pnl   | parametric_var   | parametric_increase   | monte_carlo_var   | monte_carlo_es   |
|-------------------:|:----------------|:-----------------|:----------------------|:------------------|:-----------------|
|                1.5 | USD 0           | USD 91,554       | 2.08%                 | USD 91,324        | USD 104,856      |
|                2   | USD 0           | USD 122,072      | 36.11%                | USD 121,763       | USD 139,790      |

A pure volatility change creates no immediate deterministic P&L for this Core portfolio. It changes the distribution used to estimate VaR and ES.

![Correlation comparison](../../outputs/figures/08_normal_vs_crisis_correlation.png)

## Data Quality and Controls

- Required ETF and FX factors are never forward-filled or silently replaced with zero.
- Treasury forward-fill is limited to three business days and exposed through quality flags.
- Position P&L reconciles to portfolio P&L, and funded holdings reconcile to NAV.
- Forecast windows end on the forecast date; realized P&L is the next valid portfolio interval.
- Random seeds, configuration hash, snapshot ID, runtime versions, and generated files are recorded.

## Assumptions and Limitations

- Core ETFs are synthetic adjusted-total-return holdings; fees, taxes, and trading costs are omitted.
- Bonds use constant duration and convexity, with no coupon/carry, pull-to-par, or daily sensitivity ageing.
- Cash earns zero; the FX overlay is zero funded value and settles daily P&L into cash.
- Normal Parametric and Monte Carlo models assume stable covariance and do not capture skewness or fat tails.
- Historical estimates depend on a short 250-observation window and sparse tail mass.
- No square-root-of-time scaling is used; one day means one valid common valuation interval.
- All numerical results in this report are engineering demonstrations on artificial data and are blocked from resume claims.

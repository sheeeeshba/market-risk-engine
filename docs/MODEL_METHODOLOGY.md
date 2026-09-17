# Model Methodology and Governance

## Intended and Prohibited Use

This is an educational, institutional-style portfolio project. It demonstrates risk measurement, controls, testing, and communication. It is not approved for regulatory capital, production limits, investment advice, or live trading.

## Authoritative Decisions

No external blueprint existed at project start, so the attached master specification is authoritative. No conflicting convention was combined. Positive P&L is profit; loss is `-P&L`; VaR/ES are loss magnitudes. Rate changes are absolute decimal yield changes, EURUSD is USD per EUR, and one day means one valid common portfolio valuation interval.

## Data and Common Calendar

Raw timestamps are normalized, duplicate dates retain the last retrieved observation, and ETF/FX levels define the candidate calendar. ETF/FX gaps are never filled. DGS5/DGS10 may be carried forward for at most three business days, with fill flags and ages. Remaining incomplete dates are dropped, then returns and yield changes are calculated between consecutive surviving dates. Multi-civil-day intervals are flagged.

The bundled snapshot is artificial. Optional live mode explicitly requests Yahoo `Adj Close` with `auto_adjust=False`; FRED yields arrive as percentages and are divided by 100 before differencing.

## Portfolio Accounting and Timing

Funded assets plus cash start at USD 10 million. The FX overlay has zero funded value and is excluded from the NAV identity. For every date: start with prior-close holdings, apply shocks, update ETF and bond values, settle FX P&L into cash, reconcile pre-trade NAV, rebalance after the first valid close of each month, and store holdings for the next interval.

Rebalancing sets funded positions to recurring target weights against cash and resets FX notional to 7.5% of NAV. There are no external flows, so pre-rebalance `NAV_t = NAV_t-1 + P&L_t`.

## P&L Models

ETF P&L is signed market value times adjusted simple return. Bond percentage price change is:

`-Modified Duration × ΔYield + 0.5 × Convexity × ΔYield²`.

Bond P&L is signed market value times that change. DV01 is reported as signed market value times modified duration times `0.0001`; a positive number for the long Core bond book is the approximate loss under a +1 bp move.

Direct FX P&L is signed USD-equivalent notional times EURUSD return. EFA is a USD-listed total-return factor, so no second FX shock is applied.

## Current Risk Models

Historical Simulation fully revalues current holdings under the latest 250 joint shocks. If losses sorted worst-first are `L_(1)…L_(N)`, tail mass is `q=N(1-α)`. VaR is `L_(ceil(q))`. ES uses full mass for the worst `floor(q)` observations plus fractional mass at the boundary. All tied boundary scenarios share boundary mass equally. The returned weights are reused for position ES contributions.

Parametric risk uses zero mean, linear factor exposure `x`, and sample covariance `Σ`. P&L volatility is `sqrt(x'Σx)`, VaR is `zα σ`, and Normal ES is `σ φ(zα)/(1-α)`.

Monte Carlo draws zero-mean multivariate Normal factor shocks with deterministic seeds, then fully revalues ETFs, duration-convexity bonds, and FX. Covariance is symmetrized; only tiny negative numerical eigenvalues may be clipped, with diagnostics recorded. Material non-positive-semidefinite failures stop the run.

## Contributions

Position component VaR is `zα (x_i'Σx)/σ`. Factor component VaR uses the corresponding Euler decomposition. Contributions reconcile to total Parametric VaR; negative values are retained. Historical ES contributions use the exact portfolio-tail weights, not each position's standalone tail.

## Rolling Forecasts and Backtesting

A forecast after close `t` uses exactly 250 shocks ending at `t` and end-of-`t` holdings. It is compared with hypothetical P&L from `t` to the next valid date `t_next`. Inputs after `t` are forbidden. An exception is `realized loss > VaR`.

Kupiec tests unconditional coverage. Christoffersen tests transition independence using `n00`, `n01`, `n10`, and `n11`; conditional coverage sums the two likelihood-ratio statistics. `0 × log(0)` is evaluated as zero. Missing transition rows return `INSUFFICIENT_TRANSITIONS`. Warnings identify fewer than 250 forecasts, fewer than five expected exceptions, and unstable transition counts.

## Stress Testing

Six versioned hypothetical scenarios fully revalue positions and preserve gains as negative losses. Volatility/correlation stress changes covariance and risk estimates, not immediate deterministic P&L. The bundled crisis archive is an artificial engineering fixture; a real archive must calculate endpoint returns and yield changes from verified market levels.

## Model-Risk Register

- Data risk: provider revisions, timestamp mismatches, licensing, and adjusted-price interpretation.
- Model risk: linear Normal assumptions, stable covariance, limited Historical tail mass, and duration-convexity approximation.
- Implementation risk: date alignment, unit conversion, double signs, duplicate FX exposure, and stale artifacts.
- Use risk: interpreting non-rejection as validation, comparing multi-day stress with one-interval VaR, or presenting synthetic results as history.

## Change Log

- 1.0.0: typed platform/application boundary, interactive Risk Ledger review workspace, configurable presentation controls, evidence bundle downloads, and expanded UI validation.
- 0.1.0: canonical Core accounting, three VaR/ES models, rolling backtests, contributions, stress engine, automated report, tests, and synthetic offline snapshot.

# Model Limitations Register

| ID | Limitation | Risk | Control / next step |
|---|---|---|---|
| DATA-01 | Bundled factors are artificial. | Historical conclusions would be invalid. | Watermark every output; block resume and case-study metrics; replace with verified real snapshot. |
| DATA-02 | Yahoo/FRED live mode depends on provider availability and terms. | Failed refresh or unsuitable redistribution. | Snapshot fallback, provenance metadata, explicit fields/units, no bundled provider data by default. |
| DATA-03 | Rate forward-fill can mask a short closure mismatch. | Stale rate shock. | Maximum three business days; flags and fill ages; incomplete dates dropped. |
| MODEL-01 | Normal models assume stable covariance and elliptical tails. | Tail risk may be understated. | Compare with Historical model; stress vol/correlation; add only evidence-backed challenger. |
| MODEL-02 | 250 rows provide only 2.5 effective observations for 99% Historical ES. | High estimator variance. | Display effective tail mass and warning; avoid over-precision. |
| MODEL-03 | Bonds use constant duration and convexity. | Large/non-parallel shocks may be mispriced. | Compare duration-only and convexity; future full cash-flow/key-rate repricing. |
| MODEL-04 | Stock and ETF factors are USD-listed total returns. | No local-equity/FX decomposition. | Do not add a second FX shock to international USD-listed instruments; future decomposition must replace, not layer onto, the mapping. |
| MODEL-05 | No transaction costs, taxes, carry, cash interest, or ageing. | Actual P&L differs from hypothetical P&L. | Disclose and keep backtest explicitly hypothetical. |
| TEST-01 | 270 artificial rolling forecasts imply 2.7 expected 99% breaches. | Coverage tests have low power. | Emit low-power and transition warnings; use longer real history. |
| OPS-01 | Clean hosted Colab run is not yet verified. | Recruiter reproduction may fail. | Publish repository, set public URL, run notebook in a fresh Colab runtime, record evidence. |
| USE-01 | Educational implementation has no regulatory governance. | Misuse for limits or capital. | Prominent prohibition in README, notebook, report, and package docstring. |

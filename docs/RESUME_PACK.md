# Resume Pack

Use the engineering-only bullets in `CV_PROJECT_SECTION.md` now. They describe verified implementation scope and tests without presenting artificial values as market history. Numerical market conclusions remain blocked until a permitted real-data snapshot is verified.

## Proposed Project Title

**Multi-Asset Market Risk Platform | Python, Streamlit, Plotly, VaR, Expected Shortfall**

Do not add SQL: no SQL layer is implemented.

## Engineering Bullets

- Built a modular Python market-risk engine for eight portfolio positions and seven mapped risk factors, implementing Historical, Parametric Normal, and Monte Carlo VaR plus Expected Shortfall at three confidence levels.
- Developed a leak-free rolling backtesting framework with next-valid-date alignment, Kupiec and Christoffersen tests, deterministic seeds, and exception diagnostics.
- Designed duration-convexity bond P&L, direct FX overlay accounting, six hypothetical stress scenarios, distributional volatility/correlation stress, and additive position/factor risk contributions.
- Built a responsive analyst workspace with configurable risk charts, seven review tabs, correctly scaled USD/%NAV views, and downloadable evidence.
- Automated a versioned management-style report with eight generated figures, CSV evidence tables, configuration and snapshot hashes, a verification manifest, CI, and 28 tests.

These scope counts are supported by the public code and synthetic verification manifest. Do not claim business impact, users, profitability, deployment scale, production readiness, regulatory approval, or historical model performance.

## 90-Second Walkthrough Draft

“The decision question is how much this multi-asset portfolio could lose over the next valid valuation interval, what drives that risk, and whether the forecast exceptions behave plausibly. I first separate the USD 10 million funded book from the zero-funded-value EUR overlay and reconcile daily P&L to NAV. I then compare Historical, Parametric Normal, and full-revaluation Monte Carlo VaR and Expected Shortfall using the same 250-row information set. The rolling engine freezes end-of-date holdings and tests the next valid interval, preventing look-ahead bias. Component VaR and exact-tail Historical ES identify position drivers, while six scenarios and crisis replays show losses outside normal conditions. A Streamlit control room lets a reviewer change confidence, models, history, units, and USD versus NAV views without altering the underlying calculation, then download the evidence bundle. The current repository uses artificial data, so I treat the numbers as engineering verification and would replace them with a permitted real snapshot before making empirical claims.”

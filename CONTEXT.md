# Market Risk Portfolio Context

This context defines how selectable instruments become one funded portfolio and how that portfolio is represented consistently across accounting, risk, stress, and reporting.

## Language

**Instrument Catalog**:
The approved set of selectable instruments, each with one instrument type, asset class, risk factor, and valuation convention.
_Avoid_: Asset list, ticker list

**Active Instrument**:
A catalog instrument currently included in a Portfolio Allocation with a non-zero target weight or overlay notional.
_Avoid_: Added stock, enabled row

**Funded Instrument**:
An instrument whose market value is part of NAV and whose target weight participates in the 100% funding identity.
_Avoid_: Cash-consuming asset

**FX Overlay**:
A zero-funded-value currency position whose signed notional creates P&L but is excluded from the funded NAV identity.
_Avoid_: FX investment, funded currency holding

**Portfolio Allocation**:
The selected funded target weights and overlay notional fractions used for the next complete risk calculation.
_Avoid_: Portfolio settings, weights form

**Residual Cash**:
The funded cash weight automatically calculated as 100% minus the selected non-cash funded weights.
_Avoid_: Unallocated error, spare percentage

**Resolved Portfolio**:
The validated position set produced by combining an Instrument Catalog with one Portfolio Allocation and initial NAV.
_Avoid_: Generated config, custom portfolio data

**Recalculation**:
A complete refresh of portfolio history, P&L, VaR/Expected Shortfall, backtesting, stress, and contributions from one Resolved Portfolio.
_Avoid_: Chart refresh, partial update

# Manual Worked Examples

These literals are independent reference values used by `tests/test_manual_example.py`.

## Equity

A long ETF book value of USD 100 with an adjusted return of -10% produces:

`P&L = 100 × (-0.10) = -USD 10`.

The position loses money, and portfolio loss is positive USD 10.

## Bond

For USD 100 market value, modified duration 5, convexity 20, and a +100 bp (`+0.01`) yield shock:

`percentage change = -5 × 0.01 + 0.5 × 20 × 0.01² = -0.049`.

`P&L = 100 × (-0.049) = -USD 4.90`.

The duration-only P&L would be -USD 5.00, so positive convexity offsets USD 0.10 of the loss.

## FX

A long-EUR USD-equivalent notional of USD 100 with a -10% EURUSD return produces:

`P&L = 100 × (-0.10) = -USD 10`.

Because EURUSD is USD per EUR, the long-EUR overlay loses when EUR weakens.


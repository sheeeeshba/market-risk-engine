"""Canonical single-position P&L functions.

All inputs are signed USD market values or signed USD-equivalent notionals.
Positive output is profit; negative output is loss. Yield changes are absolute
decimal changes, so 100 basis points is ``0.01``.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def etf_pnl(market_value: ArrayLike, adjusted_return: ArrayLike) -> float | NDArray[np.float64]:
    """Return synthetic total-return ETF P&L.

    A negative signed market value naturally represents a short position, so a
    separate direction multiplier must not be applied.
    """

    result = np.asarray(market_value, dtype=float) * np.asarray(adjusted_return, dtype=float)
    return float(result) if result.ndim == 0 else result


def bond_percentage_change(
    modified_duration: float,
    convexity: float,
    yield_change: ArrayLike,
) -> float | NDArray[np.float64]:
    """Approximate bond price return using duration and convexity."""

    dy = np.asarray(yield_change, dtype=float)
    result = -float(modified_duration) * dy + 0.5 * float(convexity) * dy**2
    return float(result) if result.ndim == 0 else result


def bond_pnl(
    market_value: ArrayLike,
    modified_duration: float,
    convexity: float,
    yield_change: ArrayLike,
) -> float | NDArray[np.float64]:
    """Return synthetic constant-sensitivity bond P&L."""

    result = np.asarray(market_value, dtype=float) * np.asarray(
        bond_percentage_change(modified_duration, convexity, yield_change), dtype=float
    )
    return float(result) if result.ndim == 0 else result


def fx_pnl(
    signed_usd_notional: ArrayLike,
    eurusd_return: ArrayLike,
) -> float | NDArray[np.float64]:
    """Return direct EURUSD overlay P&L for a USD-per-EUR quote."""

    result = np.asarray(signed_usd_notional, dtype=float) * np.asarray(
        eurusd_return, dtype=float
    )
    return float(result) if result.ndim == 0 else result


def dv01(market_value: float, modified_duration: float) -> float:
    """Return signed loss magnitude for a +1 bp yield shock.

    A positive number for a long positive-duration bond means the position loses
    approximately this amount when yield rises by one basis point.
    """

    return float(market_value) * float(modified_duration) * 0.0001


"""Hard controls for configuration, factor data, and numerical results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

SUPPORTED_INSTRUMENTS = {"equity", "etf", "bond", "cash", "fx_forward"}


def validate_portfolio_config(config: Mapping[str, Any]) -> dict[str, float]:
    """Validate the funding identity and factor-specific required fields."""

    if not config.get("base_currency"):
        raise ValueError("Portfolio base_currency is required.")
    positions = config.get("positions")
    if not isinstance(positions, list) or not positions:
        raise ValueError("Portfolio positions must be a non-empty list.")

    identifiers: set[str] = set()
    funded_weights = 0.0
    net_funded = 0.0
    gross_funded = 0.0
    overlay_notional = 0.0
    for position in positions:
        position_id = str(position.get("position_id", ""))
        if not position_id or position_id in identifiers:
            raise ValueError(f"Position identifiers must be present and unique: {position_id!r}")
        identifiers.add(position_id)
        instrument = position.get("instrument_type")
        if instrument not in SUPPORTED_INSTRUMENTS:
            raise ValueError(f"Unsupported instrument type for {position_id}: {instrument!r}")
        if not position.get("factor"):
            raise ValueError(f"Position {position_id} has no mapped risk factor.")

        market_value = float(position.get("initial_market_value", 0.0))
        if instrument != "fx_forward":
            if "target_weight" not in position:
                raise ValueError(f"Funded position {position_id} requires target_weight.")
            funded_weights += float(position["target_weight"])
            net_funded += market_value
            gross_funded += abs(market_value)
        else:
            if position.get("quote_convention") != "USD_per_EUR":
                raise ValueError(
                    f"Ambiguous FX convention for {position_id}; Core requires USD_per_EUR."
                )
            if market_value != 0.0:
                raise ValueError(f"FX overlay {position_id} must have zero funded market value.")
            overlay_notional += abs(float(position.get("initial_notional", 0.0)))

        if instrument == "bond" and (
            "modified_duration" not in position or "convexity" not in position
        ):
            raise ValueError(f"Bond {position_id} requires modified_duration and convexity.")

    if not np.isclose(funded_weights, 1.0, atol=1e-8, rtol=0.0):
        raise ValueError(f"Funded target weights including cash must sum to 1.0; got {funded_weights}.")
    expected_nav = float(config.get("initial_nav", net_funded))
    if not np.isclose(net_funded, expected_nav, atol=0.01, rtol=0.0):
        raise ValueError(
            f"Initial funded market value {net_funded:.2f} does not equal NAV {expected_nav:.2f}."
        )
    return {
        "funded_weight_sum": funded_weights,
        "net_funded_market_value": net_funded,
        "gross_funded_exposure": gross_funded,
        "overlay_notional": overlay_notional,
    }


def validate_factor_frame(factors: pd.DataFrame, required_columns: list[str]) -> None:
    """Hard-fail when factor data could silently remove risk."""

    missing_columns = sorted(set(required_columns) - set(factors.columns))
    if missing_columns:
        raise ValueError(f"Missing required factor columns: {', '.join(missing_columns)}")
    if not isinstance(factors.index, pd.DatetimeIndex):
        raise TypeError("Factor data must use a DatetimeIndex named portfolio_date.")
    if factors.index.has_duplicates or not factors.index.is_monotonic_increasing:
        raise ValueError("Factor dates must be unique and increasing.")
    if factors[required_columns].isna().any().any():
        raise ValueError("Factor data contain missing shocks; missing risk cannot become zero.")
    if not np.isfinite(factors[required_columns].to_numpy(dtype=float)).all():
        raise ValueError("Factor data contain infinite or non-numeric shocks.")


def validate_covariance(covariance: np.ndarray, tolerance: float = -1e-10) -> float:
    """Validate covariance symmetry and return its minimum eigenvalue."""

    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Covariance must be a square matrix.")
    if not np.allclose(matrix, matrix.T, atol=1e-12, rtol=1e-10):
        raise ValueError("Covariance matrix is not symmetric.")
    minimum = float(np.linalg.eigvalsh(matrix).min())
    if minimum < tolerance:
        raise ValueError(f"Covariance is not positive semidefinite; min eigenvalue={minimum:.3e}.")
    return minimum

"""Deterministic scenarios, crisis replays, and distributional stress tests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .var_models import (
    factor_exposure_by_position,
    monte_carlo_portfolio_var_es,
    parametric_var_es,
    repair_covariance,
    revalue_factor_shocks,
)


@dataclass(frozen=True)
class StressResults:
    summary: pd.DataFrame
    detail: pd.DataFrame
    warnings: tuple[str, ...]


def run_deterministic_stresses(
    snapshot: pd.DataFrame,
    scenario_config: Mapping[str, Any],
    nav: float,
) -> StressResults:
    """Apply each configured joint shock once and reconcile position P&L."""

    if nav <= 0.0:
        raise ValueError("Stress testing requires a positive NAV.")
    scenarios = scenario_config.get("scenarios")
    if not isinstance(scenarios, Mapping) or not scenarios:
        raise ValueError("Stress configuration must contain scenarios.")
    factors = list(dict.fromkeys(snapshot.loc[snapshot["instrument_type"] != "cash", "factor"]))
    factor_asset_classes = (
        snapshot.loc[snapshot["instrument_type"] != "cash", ["factor", "asset_class"]]
        .drop_duplicates("factor")
        .set_index("factor")["asset_class"]
        .to_dict()
    )
    summary_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for scenario_id, scenario in scenarios.items():
        configured_shocks = scenario.get("shocks", {})
        asset_class_shocks = scenario.get("asset_class_shocks", {})
        if not isinstance(configured_shocks, Mapping) or not isinstance(
            asset_class_shocks, Mapping
        ):
            raise ValueError(f"Scenario {scenario_id} shocks must be mappings.")
        unused = sorted(set(configured_shocks) - set(factors))
        if unused:
            warnings.append(f"{scenario_id}: unused scenario factors {unused}")
        shock_row = {
            factor: float(
                configured_shocks.get(
                    factor,
                    asset_class_shocks.get(factor_asset_classes[factor], 0.0),
                )
            )
            for factor in factors
        }
        shocks = pd.DataFrame([shock_row], index=[scenario_id])
        position_pnl = revalue_factor_shocks(snapshot, shocks).iloc[0]
        portfolio_pnl = float(position_pnl.sum())
        position_losses = -position_pnl
        principal_driver = (
            str(position_losses.idxmax())
            if not np.isclose(float(position_losses.abs().max()), 0.0)
            else "No affected position"
        )

        for position_id, position in snapshot.iterrows():
            shock = float(shock_row.get(position["factor"], 0.0))
            pnl = float(position_pnl[position_id])
            if position["instrument_type"] == "bond":
                duration_only = -float(position["market_value"]) * float(
                    position["modified_duration"]
                ) * shock
            else:
                duration_only = pnl
            detail_rows.append(
                {
                    "scenario_id": scenario_id,
                    "position_id": position_id,
                    "scenario_name": scenario.get("name", scenario_id),
                    "scenario_type": scenario.get("type", "unknown"),
                    "horizon": scenario.get("horizon", "unspecified"),
                    "factor": position["factor"],
                    "asset_class": position["asset_class"],
                    "factor_shock": shock,
                    "position_pnl": pnl,
                    "position_loss": -pnl,
                    "duration_only_pnl": duration_only,
                }
            )
        summary_rows.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": scenario.get("name", scenario_id),
                "scenario_type": scenario.get("type", "unknown"),
                "horizon": scenario.get("horizon", "unspecified"),
                "scenario_pnl": portfolio_pnl,
                "scenario_loss": -portfolio_pnl,
                "loss_pct_nav": -portfolio_pnl / nav,
                "principal_loss_driver": principal_driver,
                "reconciliation_difference": portfolio_pnl - float(position_pnl.sum()),
            }
        )

    summary = pd.DataFrame(summary_rows).set_index("scenario_id")
    detail = pd.DataFrame(detail_rows).set_index(["scenario_id", "position_id"])
    return StressResults(summary=summary, detail=detail, warnings=tuple(warnings))


def volatility_correlation_stress(
    snapshot: pd.DataFrame,
    base_covariance: pd.DataFrame,
    crisis_correlation: pd.DataFrame,
    volatility_scale: float,
    confidence: float,
    monte_carlo_paths: int,
    seed: int,
) -> dict[str, Any]:
    """Scale volatilities, replace correlations, and recalculate distributional risk."""

    if volatility_scale <= 0.0:
        raise ValueError("Volatility scale must be positive.")
    factors = list(base_covariance.columns)
    if list(base_covariance.index) != factors:
        raise ValueError("Base covariance labels must align.")
    crisis = crisis_correlation.reindex(index=factors, columns=factors)
    if crisis.isna().any().any() or not np.allclose(crisis, crisis.T, atol=1e-12):
        raise ValueError("Crisis correlation matrix must be complete and symmetric.")
    if not np.allclose(np.diag(crisis), 1.0, atol=1e-10):
        raise ValueError("Crisis correlation diagonal must equal one.")

    base_matrix, base_repair = repair_covariance(base_covariance.to_numpy(dtype=float))
    volatilities = np.sqrt(np.clip(np.diag(base_matrix), 0.0, None)) * volatility_scale
    stressed_matrix = np.diag(volatilities) @ crisis.to_numpy(dtype=float) @ np.diag(volatilities)
    stressed_matrix, stressed_repair = repair_covariance(stressed_matrix)
    stressed_covariance = pd.DataFrame(stressed_matrix, index=factors, columns=factors)

    position_exposure = factor_exposure_by_position(snapshot, factors)
    total_exposure = position_exposure.sum(axis=0).to_numpy(dtype=float)
    base_parametric = parametric_var_es(total_exposure, base_matrix, confidence)
    stressed_parametric = parametric_var_es(total_exposure, stressed_matrix, confidence)
    base_mc, _ = monte_carlo_portfolio_var_es(
        snapshot, pd.DataFrame(base_matrix, index=factors, columns=factors), confidence,
        monte_carlo_paths, seed,
    )
    stressed_mc, _ = monte_carlo_portfolio_var_es(
        snapshot, stressed_covariance, confidence, monte_carlo_paths, seed,
    )
    return {
        "volatility_scale": volatility_scale,
        "immediate_deterministic_pnl": 0.0,
        "base_parametric_var": base_parametric.var,
        "stressed_parametric_var": stressed_parametric.var,
        "parametric_var_increase_pct": (
            stressed_parametric.var / base_parametric.var - 1.0
            if base_parametric.var != 0.0
            else np.nan
        ),
        "base_parametric_es": base_parametric.es,
        "stressed_parametric_es": stressed_parametric.es,
        "base_monte_carlo_var": base_mc.var,
        "stressed_monte_carlo_var": stressed_mc.var,
        "base_monte_carlo_es": base_mc.es,
        "stressed_monte_carlo_es": stressed_mc.es,
        "base_covariance_repair": base_repair,
        "stressed_covariance_repair": stressed_repair,
        "stressed_covariance": stressed_covariance,
    }

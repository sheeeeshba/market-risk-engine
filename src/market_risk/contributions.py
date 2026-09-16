"""Additive Parametric VaR and Historical ES decompositions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from .var_models import repair_covariance


@dataclass(frozen=True)
class ParametricContributions:
    total_var: float
    sigma_pnl: float
    position: pd.DataFrame
    factor: pd.DataFrame
    standalone_sum: float
    diversification_benefit: float


def parametric_contributions(
    position_exposures: pd.DataFrame,
    covariance: pd.DataFrame,
    confidence: float,
) -> ParametricContributions:
    """Calculate position and factor Euler contributions to linear Normal VaR."""

    if not 0.0 < confidence < 1.0:
        raise ValueError("Confidence must be between zero and one.")
    factors = list(covariance.columns)
    if list(covariance.index) != factors:
        raise ValueError("Covariance index and columns must use the same factor order.")
    exposures = position_exposures.reindex(columns=factors, fill_value=0.0).astype(float)
    matrix, _ = repair_covariance(covariance.to_numpy(dtype=float))
    total = exposures.sum(axis=0).to_numpy(dtype=float)
    variance = float(total @ matrix @ total)
    sigma = float(np.sqrt(max(variance, 0.0)))
    z_score = float(norm.ppf(confidence))
    total_var = z_score * sigma

    position_rows: list[dict[str, float]] = []
    for position_id, row in exposures.iterrows():
        vector = row.to_numpy(dtype=float)
        standalone_sigma = float(np.sqrt(max(float(vector @ matrix @ vector), 0.0)))
        component = 0.0 if sigma == 0.0 else z_score * float(vector @ matrix @ total) / sigma
        position_rows.append(
            {
                "position_id": position_id,
                "component_var": component,
                "standalone_var": z_score * standalone_sigma,
                "component_share": component / total_var if total_var != 0.0 else 0.0,
            }
        )
    position = pd.DataFrame(position_rows).set_index("position_id")

    covariance_times_total = matrix @ total
    marginal_volatility = (
        covariance_times_total / sigma if sigma != 0.0 else np.zeros_like(covariance_times_total)
    )
    factor_component_volatility = total * marginal_volatility
    factor = pd.DataFrame(
        {
            "exposure": total,
            "marginal_volatility": marginal_volatility,
            "component_volatility": factor_component_volatility,
            "component_var": z_score * factor_component_volatility,
        },
        index=factors,
    )
    factor.index.name = "factor"
    factor["component_share"] = (
        factor["component_var"] / total_var if total_var != 0.0 else 0.0
    )
    standalone_sum = float(position["standalone_var"].sum())
    return ParametricContributions(
        total_var=total_var,
        sigma_pnl=sigma,
        position=position,
        factor=factor,
        standalone_sum=standalone_sum,
        diversification_benefit=standalone_sum - total_var,
    )


def historical_es_contributions(
    position_pnl: pd.DataFrame,
    scenario_weights: np.ndarray,
) -> pd.Series:
    """Average position losses with the exact portfolio-tail weights."""

    weights = np.asarray(scenario_weights, dtype=float)
    if weights.ndim != 1 or weights.size != len(position_pnl):
        raise ValueError("Scenario weights must align one-for-one with P&L scenarios.")
    if not np.isclose(weights.sum(), 1.0, atol=1e-12):
        raise ValueError("Historical ES scenario weights must sum to one.")
    values = (-position_pnl).mul(weights, axis=0).sum(axis=0)
    values.name = "historical_es_contribution"
    return values


def aggregate_position_contributions(
    contributions: pd.Series,
    snapshot: pd.DataFrame,
    grouping: str,
) -> pd.Series:
    """Aggregate an additive position decomposition by snapshot metadata."""

    if grouping not in snapshot.columns:
        raise ValueError(f"Snapshot has no grouping field {grouping!r}.")
    aligned = pd.DataFrame(
        {"contribution": contributions, grouping: snapshot.loc[contributions.index, grouping]}
    )
    return aligned.groupby(grouping, sort=False)["contribution"].sum()


"""Historical, Parametric, and Monte Carlo one-interval risk models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from .pnl import bond_pnl


@dataclass(frozen=True)
class RiskEstimate:
    var: float
    es: float
    confidence: float


@dataclass(frozen=True)
class HistoricalRiskEstimate(RiskEstimate):
    scenario_weights: np.ndarray
    effective_tail_mass: float


@dataclass(frozen=True)
class ParametricRiskEstimate(RiskEstimate):
    sigma_pnl: float
    mean_pnl: float = 0.0


@dataclass(frozen=True)
class MonteCarloRiskEstimate(RiskEstimate):
    paths: int
    seed: int
    simulated_mean_pnl: float
    simulated_sigma_pnl: float
    covariance_diagnostics: dict[str, Any]


def _validate_confidence(confidence: float) -> None:
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"Confidence must be between zero and one; got {confidence}.")


def historical_var_es(losses: np.ndarray, confidence: float) -> HistoricalRiskEstimate:
    """Estimate Historical VaR/ES with exact finite-sample tail weights.

    Returned scenario weights are in the input order, sum to one, and assign
    equal fractional mass to every scenario tied at the VaR boundary.
    """

    _validate_confidence(confidence)
    values = np.asarray(losses, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("Historical losses must be a non-empty finite one-dimensional array.")
    count = values.size
    tail_mass = count * (1.0 - confidence)
    sorted_losses = np.sort(values)[::-1]
    rank = max(1, int(np.ceil(tail_mass - 1e-14)))
    var = float(sorted_losses[rank - 1])

    strictly_worse = values > var
    boundary = values == var
    worse_count = int(strictly_worse.sum())
    boundary_count = int(boundary.sum())
    raw_weights = np.zeros(count, dtype=float)
    raw_weights[strictly_worse] = 1.0
    boundary_mass = tail_mass - worse_count
    if boundary_count <= 0 or boundary_mass < -1e-12:
        raise ArithmeticError("Could not allocate the Historical ES tail mass.")
    raw_weights[boundary] = max(0.0, boundary_mass) / boundary_count
    scenario_weights = raw_weights / tail_mass
    es = float(np.dot(scenario_weights, values))
    return HistoricalRiskEstimate(
        var=var,
        es=es,
        confidence=confidence,
        scenario_weights=scenario_weights,
        effective_tail_mass=float(tail_mass),
    )


def parametric_var_es(
    exposure: np.ndarray,
    covariance: np.ndarray,
    confidence: float,
    mean_pnl: float = 0.0,
) -> ParametricRiskEstimate:
    """Calculate linear Normal VaR and ES in report-currency units."""

    _validate_confidence(confidence)
    x = np.asarray(exposure, dtype=float)
    covariance = np.asarray(covariance, dtype=float)
    if x.ndim != 1 or covariance.shape != (x.size, x.size):
        raise ValueError("Exposure and covariance dimensions do not match.")
    covariance, _ = repair_covariance(covariance)
    variance = float(x @ covariance @ x)
    if variance < -1e-8:
        raise ValueError(f"Portfolio variance is negative: {variance}.")
    sigma = float(np.sqrt(max(variance, 0.0)))
    z_score = float(norm.ppf(confidence))
    var = float(-mean_pnl + z_score * sigma)
    es = float(-mean_pnl + sigma * norm.pdf(z_score) / (1.0 - confidence))
    return ParametricRiskEstimate(
        var=var,
        es=es,
        confidence=confidence,
        sigma_pnl=sigma,
        mean_pnl=float(mean_pnl),
    )


def repair_covariance(covariance: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Symmetrise and, only for tiny numerical negatives, clip eigenvalues."""

    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Covariance must be square.")
    symmetric = (matrix + matrix.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    minimum = float(eigenvalues.min())
    diagnostics: dict[str, Any] = {
        "original_minimum_eigenvalue": minimum,
        "repair_method": "none",
        "maximum_absolute_adjustment": 0.0,
    }
    if minimum < -1e-8:
        raise ValueError(
            f"Unrecoverable covariance failure: minimum eigenvalue {minimum:.3e} is material."
        )
    if minimum < 0.0:
        repaired = (eigenvectors * np.clip(eigenvalues, 0.0, None)) @ eigenvectors.T
        repaired = (repaired + repaired.T) / 2.0
        diagnostics["repair_method"] = "eigenvalue_clip_to_zero"
        diagnostics["maximum_absolute_adjustment"] = float(np.max(np.abs(repaired - symmetric)))
        symmetric = repaired
    return symmetric, diagnostics


def monte_carlo_var_es(
    exposure: np.ndarray,
    covariance: np.ndarray,
    confidence: float,
    paths: int,
    seed: int,
) -> MonteCarloRiskEstimate:
    """Simulate linear zero-mean Normal factor P&L with a deterministic seed."""

    _validate_confidence(confidence)
    if paths < 100:
        raise ValueError("Monte Carlo paths must be at least 100.")
    x = np.asarray(exposure, dtype=float)
    if x.ndim != 1:
        raise ValueError("Exposure must be one-dimensional.")
    covariance, diagnostics = repair_covariance(np.asarray(covariance, dtype=float))
    if covariance.shape != (x.size, x.size):
        raise ValueError("Exposure and covariance dimensions do not match.")
    generator = np.random.default_rng(seed)
    shocks = generator.multivariate_normal(np.zeros(x.size), covariance, size=paths)
    pnl = shocks @ x
    losses = -pnl
    var = float(np.quantile(losses, confidence, method="higher"))
    tail = losses[losses >= var]
    es = float(tail.mean()) if tail.size else var
    return MonteCarloRiskEstimate(
        var=var,
        es=es,
        confidence=confidence,
        paths=paths,
        seed=seed,
        simulated_mean_pnl=float(pnl.mean()),
        simulated_sigma_pnl=float(pnl.std(ddof=1)),
        covariance_diagnostics=diagnostics,
    )


def factor_exposure_by_position(
    snapshot: pd.DataFrame,
    factor_order: list[str],
) -> pd.DataFrame:
    """Map signed positions to linear factor exposures in USD."""

    exposures = pd.DataFrame(0.0, index=snapshot.index, columns=factor_order)
    for position_id, position in snapshot.iterrows():
        factor = position["factor"]
        if position["instrument_type"] in {"equity", "etf"}:
            exposures.loc[position_id, factor] = float(position["market_value"])
        elif position["instrument_type"] == "bond":
            exposures.loc[position_id, factor] = -float(position["market_value"]) * float(
                position["modified_duration"]
            )
        elif position["instrument_type"] == "fx_forward":
            exposures.loc[position_id, factor] = float(position["notional"])
        elif position["instrument_type"] == "cash":
            continue
        else:
            raise ValueError(f"Unsupported instrument type: {position['instrument_type']}")
    return exposures


def revalue_factor_shocks(snapshot: pd.DataFrame, factor_shocks: pd.DataFrame) -> pd.DataFrame:
    """Fully revalue Core positions under rows of joint factor shocks."""

    position_pnl = pd.DataFrame(0.0, index=factor_shocks.index, columns=snapshot.index)
    for position_id, position in snapshot.iterrows():
        instrument = position["instrument_type"]
        if instrument == "cash":
            continue
        factor = position["factor"]
        if factor not in factor_shocks:
            raise ValueError(f"Scenario shocks do not contain mapped factor {factor!r}.")
        shocks = factor_shocks[factor].to_numpy(dtype=float)
        if instrument in {"equity", "etf"}:
            pnl = float(position["market_value"]) * shocks
        elif instrument == "bond":
            pnl = bond_pnl(
                float(position["market_value"]),
                float(position["modified_duration"]),
                float(position["convexity"]),
                shocks,
            )
        elif instrument == "fx_forward":
            pnl = float(position["notional"]) * shocks
        else:
            raise ValueError(f"Unsupported instrument type: {instrument}")
        position_pnl[position_id] = pnl
    return position_pnl


def monte_carlo_portfolio_var_es(
    snapshot: pd.DataFrame,
    covariance: pd.DataFrame,
    confidence: float,
    paths: int,
    seed: int,
) -> tuple[MonteCarloRiskEstimate, pd.DataFrame]:
    """Simulate factors and fully revalue ETFs, duration-convexity bonds, and FX."""

    _validate_confidence(confidence)
    repaired, diagnostics = repair_covariance(covariance.to_numpy(dtype=float))
    generator = np.random.default_rng(seed)
    simulations = generator.multivariate_normal(
        np.zeros(len(covariance.columns)), repaired, size=paths
    )
    target_volatility = np.sqrt(np.clip(np.diag(repaired), 0.0, None))
    simulated_volatility = simulations.std(axis=0, ddof=1)
    safe_outer = np.outer(target_volatility, target_volatility)
    target_correlation = np.divide(
        repaired,
        safe_outer,
        out=np.eye(len(target_volatility)),
        where=safe_outer > 0.0,
    )
    simulated_correlation = np.corrcoef(simulations, rowvar=False)
    diagnostics.update(
        {
            "maximum_absolute_simulated_factor_mean": float(
                np.max(np.abs(simulations.mean(axis=0)))
            ),
            "maximum_relative_volatility_error": float(
                np.max(
                    np.divide(
                        np.abs(simulated_volatility - target_volatility),
                        target_volatility,
                        out=np.zeros_like(target_volatility),
                        where=target_volatility > 0.0,
                    )
                )
            ),
            "maximum_absolute_correlation_error": float(
                np.max(np.abs(simulated_correlation - target_correlation))
            ),
        }
    )
    shocks = pd.DataFrame(simulations, columns=covariance.columns)
    position_pnl = revalue_factor_shocks(snapshot, shocks)
    pnl = position_pnl.sum(axis=1).to_numpy(dtype=float)
    losses = -pnl
    var = float(np.quantile(losses, confidence, method="higher"))
    tail = losses[losses >= var]
    estimate = MonteCarloRiskEstimate(
        var=var,
        es=float(tail.mean()) if tail.size else var,
        confidence=confidence,
        paths=paths,
        seed=seed,
        simulated_mean_pnl=float(pnl.mean()),
        simulated_sigma_pnl=float(pnl.std(ddof=1)),
        covariance_diagnostics=diagnostics,
    )
    return estimate, position_pnl

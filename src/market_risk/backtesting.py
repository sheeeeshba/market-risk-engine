"""Leak-free rolling forecasts and VaR exception tests."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2

from .portfolio import PortfolioHistory, position_snapshot_on
from .var_models import (
    factor_exposure_by_position,
    historical_var_es,
    monte_carlo_portfolio_var_es,
    parametric_var_es,
    revalue_factor_shocks,
)


def _binomial_log_likelihood(successes: int, trials: int, probability: float) -> float:
    failures = trials - successes
    terms = 0.0
    if successes:
        if probability <= 0.0:
            return -math.inf
        terms += successes * math.log(probability)
    if failures:
        if probability >= 1.0:
            return -math.inf
        terms += failures * math.log1p(-probability)
    return terms


def kupiec_test(exceptions: list[bool] | np.ndarray, confidence: float) -> dict[str, Any]:
    """Kupiec unconditional-coverage likelihood-ratio test."""

    if not 0.0 < confidence < 1.0:
        raise ValueError("Confidence must be between zero and one.")
    values = np.asarray(exceptions, dtype=bool)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Kupiec test requires at least one exception flag.")
    trials = int(values.size)
    observed = int(values.sum())
    expected_probability = 1.0 - confidence
    observed_probability = observed / trials
    null_ll = _binomial_log_likelihood(observed, trials, expected_probability)
    alternative_ll = _binomial_log_likelihood(observed, trials, observed_probability)
    lr_uc = float(-2.0 * (null_ll - alternative_ll))
    return {
        "forecasts": trials,
        "exceptions": observed,
        "expected_exceptions": trials * expected_probability,
        "observed_exception_rate": observed_probability,
        "expected_exception_rate": expected_probability,
        "lr_uc": lr_uc,
        "p_value_uc": float(chi2.sf(lr_uc, df=1)),
    }


def christoffersen_tests(exceptions: list[bool] | np.ndarray) -> dict[str, Any]:
    """Christoffersen independence transition test with explicit edge handling."""

    values = np.asarray(exceptions, dtype=bool)
    if values.ndim != 1 or values.size < 2:
        return {
            "status": "INSUFFICIENT_TRANSITIONS",
            "n00": 0,
            "n01": 0,
            "n10": 0,
            "n11": 0,
            "lr_ind": math.nan,
            "p_value_ind": math.nan,
        }
    prior = values[:-1]
    current = values[1:]
    n00 = int((~prior & ~current).sum())
    n01 = int((~prior & current).sum())
    n10 = int((prior & ~current).sum())
    n11 = int((prior & current).sum())
    row0 = n00 + n01
    row1 = n10 + n11
    result: dict[str, Any] = {"n00": n00, "n01": n01, "n10": n10, "n11": n11}
    if row0 == 0 or row1 == 0:
        result.update(
            status="INSUFFICIENT_TRANSITIONS", lr_ind=math.nan, p_value_ind=math.nan
        )
        return result

    pi01 = n01 / row0
    pi11 = n11 / row1
    total_transitions = row0 + row1
    common_pi = (n01 + n11) / total_transitions
    null_ll = _binomial_log_likelihood(n01 + n11, total_transitions, common_pi)
    alternative_ll = _binomial_log_likelihood(n01, row0, pi01) + _binomial_log_likelihood(
        n11, row1, pi11
    )
    lr_ind = float(-2.0 * (null_ll - alternative_ll))
    result.update(
        status="OK",
        probability_after_no_breach=pi01,
        probability_after_breach=pi11,
        lr_ind=lr_ind,
        p_value_ind=float(chi2.sf(lr_ind, df=1)),
    )
    return result


def conditional_coverage_test(
    exceptions: list[bool] | np.ndarray,
    confidence: float,
) -> dict[str, Any]:
    """Combine Kupiec coverage and Christoffersen independence statistics."""

    coverage = kupiec_test(exceptions, confidence)
    independence = christoffersen_tests(exceptions)
    result = {**coverage, **independence}
    if independence["status"] != "OK":
        result.update(lr_cc=math.nan, p_value_cc=math.nan)
    else:
        lr_cc = float(coverage["lr_uc"] + independence["lr_ind"])
        result.update(lr_cc=lr_cc, p_value_cc=float(chi2.sf(lr_cc, df=2)))
    warnings: list[str] = []
    if coverage["forecasts"] < 250:
        warnings.append("LOW_POWER_FEWER_THAN_250_FORECASTS")
    if coverage["expected_exceptions"] < 5:
        warnings.append("LOW_POWER_FEWER_THAN_5_EXPECTED_EXCEPTIONS")
    if independence["status"] != "OK" or min(
        independence["n00"], independence["n01"], independence["n10"], independence["n11"]
    ) < 5:
        warnings.append("UNSTABLE_TRANSITION_COUNTS")
    result["warnings"] = warnings
    return result


def validate_forecast_alignment(forecasts: pd.DataFrame) -> None:
    """Hard-fail future leakage and non-next-date realized P&L alignment."""

    required = {"forecast_date", "realized_date", "expected_next_date", "max_input_date"}
    missing = sorted(required - set(forecasts.columns))
    if missing:
        raise ValueError(f"Forecast alignment table is missing columns: {missing}")
    for column in required:
        forecasts[column] = pd.to_datetime(forecasts[column])
    if (forecasts["max_input_date"] > forecasts["forecast_date"]).any():
        raise ValueError("A forecast uses an input timestamp after its forecast date.")
    if (forecasts["realized_date"] <= forecasts["forecast_date"]).any():
        raise ValueError("Forecast and realized dates are reversed or equal.")
    if not (forecasts["realized_date"] == forecasts["expected_next_date"]).all():
        raise ValueError("Realized P&L is not aligned to the next valid portfolio date.")


def rolling_var_forecasts(
    factors: pd.DataFrame,
    portfolio_history: PortfolioHistory,
    window: int = 250,
    confidence: float = 0.99,
    monte_carlo_paths: int = 10_000,
    master_seed: int = 42,
    model_version: str = "0.1.0",
) -> pd.DataFrame:
    """Generate Historical, Parametric, and Monte Carlo forecasts after close at t."""

    if len(factors) <= window:
        raise ValueError(
            f"Insufficient estimation history: need more than {window} rows, got {len(factors)}."
        )
    factor_order = list(factors.columns)
    rows: list[dict[str, Any]] = []
    for offset in range(window - 1, len(factors) - 1):
        forecast_date = factors.index[offset]
        realized_date = factors.index[offset + 1]
        estimation = factors.iloc[offset - window + 1 : offset + 1]
        snapshot = position_snapshot_on(portfolio_history, forecast_date)
        historical_position_pnl = revalue_factor_shocks(snapshot, estimation)
        historical = historical_var_es(
            -historical_position_pnl.sum(axis=1).to_numpy(dtype=float), confidence
        )
        covariance = estimation.cov().reindex(index=factor_order, columns=factor_order)
        position_exposure = factor_exposure_by_position(snapshot, factor_order)
        parametric = parametric_var_es(
            position_exposure.sum(axis=0).to_numpy(dtype=float),
            covariance.to_numpy(dtype=float),
            confidence,
        )
        rolling_seed = int(master_seed + offset * 1_000_003)
        monte_carlo, _ = monte_carlo_portfolio_var_es(
            snapshot,
            covariance,
            confidence,
            monte_carlo_paths,
            rolling_seed,
        )
        realized_pnl = float(portfolio_history.daily.loc[realized_date, "portfolio_pnl"])
        realized_loss = -realized_pnl
        next_positions = portfolio_history.positions.xs(realized_date)
        principal_contributor = str((-next_positions["position_pnl"]).idxmax())
        common = {
            "forecast_date": forecast_date,
            "realized_date": realized_date,
            "expected_next_date": realized_date,
            "max_input_date": estimation.index.max(),
            "confidence": confidence,
            "lookback": window,
            "holdings_version": int(snapshot["holdings_version"].max()),
            "model_version": model_version,
            "hypothetical_pnl": realized_pnl,
            "realized_loss": realized_loss,
            "principal_contributor": principal_contributor,
        }
        estimates = {
            "Historical": historical,
            "Parametric Normal": parametric,
            "Monte Carlo Normal": monte_carlo,
        }
        for model, estimate in estimates.items():
            rows.append(
                {
                    **common,
                    "model": model,
                    "var": estimate.var,
                    "es": estimate.es,
                    "exception": bool(realized_loss > estimate.var),
                    "breach_magnitude": max(0.0, realized_loss - estimate.var),
                    "seed": rolling_seed if model == "Monte Carlo Normal" else np.nan,
                }
            )
    forecasts = pd.DataFrame(rows)
    validate_forecast_alignment(forecasts)
    return forecasts


def backtest_scorecard(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Summarise exception coverage and independence for each model/confidence."""

    rows: list[dict[str, Any]] = []
    for (model, confidence), group in forecasts.groupby(["model", "confidence"], sort=False):
        result = conditional_coverage_test(group["exception"].to_numpy(), float(confidence))
        rows.append({"model": model, "confidence": confidence, **result})
    return pd.DataFrame(rows).set_index(["model", "confidence"])


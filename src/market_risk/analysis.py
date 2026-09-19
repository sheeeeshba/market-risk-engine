"""Pure calculation service shared by batch reports and the portfolio builder."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .backtesting import backtest_scorecard, rolling_var_forecasts
from .contributions import historical_es_contributions, parametric_contributions
from .portfolio import PortfolioHistory, run_portfolio_history
from .stress_testing import StressResults, run_deterministic_stresses, volatility_correlation_stress
from .var_models import (
    HistoricalRiskEstimate,
    MonteCarloRiskEstimate,
    factor_exposure_by_position,
    historical_var_es,
    monte_carlo_portfolio_var_es,
    parametric_var_es,
    revalue_factor_shocks,
)


@dataclass(frozen=True)
class CalculationProfile:
    """Monte Carlo work budget, made explicit for report and interactive runs."""

    current_paths: int
    rolling_paths: int
    convergence_paths: tuple[int, int, int]
    convergence_seeds: tuple[int, ...] = (42, 314, 2_026)

    @classmethod
    def report(cls, model_config: Mapping[str, Any]) -> CalculationProfile:
        return cls(
            current_paths=int(model_config["current_monte_carlo_paths"]),
            rolling_paths=int(model_config["rolling_monte_carlo_paths"]),
            convergence_paths=(25_000, 50_000, 100_000),
        )

    @classmethod
    def interactive(cls, model_config: Mapping[str, Any]) -> CalculationProfile:
        return cls(
            current_paths=min(int(model_config["current_monte_carlo_paths"]), 10_000),
            rolling_paths=min(int(model_config["rolling_monte_carlo_paths"]), 1_000),
            convergence_paths=(2_500, 5_000, 10_000),
        )


@dataclass(frozen=True)
class CalculatedPortfolioRisk:
    """Complete linked calculation produced from one resolved portfolio."""

    portfolio_config: Mapping[str, Any]
    active_factors: pd.DataFrame
    portfolio: PortfolioHistory
    snapshot: pd.DataFrame
    current_risk: pd.DataFrame
    forecasts: pd.DataFrame
    scorecard: pd.DataFrame
    position_contributions: pd.DataFrame
    factor_contributions: pd.DataFrame
    asset_class_contributions: pd.DataFrame
    negative_hedges: pd.DataFrame
    stresses: StressResults
    crises: StressResults
    distributional_stress: pd.DataFrame
    convergence: pd.DataFrame
    convergence_summary: pd.DataFrame
    position_exposure: pd.DataFrame
    historical_losses: pd.Series
    base_correlation: pd.DataFrame
    crisis_correlation: pd.DataFrame
    historical_estimates: Mapping[float, HistoricalRiskEstimate]
    monte_carlo_estimates: Mapping[float, MonteCarloRiskEstimate]
    top_three_concentration: float
    calculation_profile: CalculationProfile

    @property
    def nav(self) -> float:
        return float(self.portfolio.daily.iloc[-1]["nav"])

    @property
    def as_of_date(self) -> str:
        return str(self.active_factors.index[-1].date())

    def public_tables(self) -> dict[str, pd.DataFrame]:
        """Return dashboard/download tables with index values promoted to columns."""

        allocation = pd.DataFrame(self.portfolio_config["positions"]).rename(
            columns={"initial_market_value": "initial_market_value"}
        )
        return {
            "portfolio_allocation": allocation,
            "daily_portfolio_pnl": self.portfolio.daily.reset_index(),
            "position_history": self.portfolio.positions.reset_index(),
            "current_risk": self.current_risk.reset_index(drop=True),
            "rolling_forecasts": self.forecasts.reset_index(drop=True),
            "backtesting_scorecard": self.scorecard.reset_index(),
            "risk_contributions": self.position_contributions.reset_index(),
            "factor_contributions": self.factor_contributions.reset_index(),
            "asset_class_contributions": self.asset_class_contributions.reset_index(),
            "negative_hedging_contributions": self.negative_hedges.reset_index(),
            "stress_summary": self.stresses.summary.reset_index(),
            "stress_detail": self.stresses.detail.reset_index(),
            "crisis_replay_summary": self.crises.summary.reset_index(),
            "volatility_correlation_stress": self.distributional_stress.reset_index(),
            "monte_carlo_convergence": self.convergence.reset_index(drop=True),
            "monte_carlo_convergence_summary": self.convergence_summary.reset_index(),
        }


def calculate_portfolio_risk(
    factors: pd.DataFrame,
    portfolio_config: Mapping[str, Any],
    model_config: Mapping[str, Any],
    stress_config: Mapping[str, Any],
    crisis_config: Mapping[str, Any],
    *,
    profile: CalculationProfile | None = None,
) -> CalculatedPortfolioRisk:
    """Recalculate every risk layer from one resolved portfolio definition."""

    profile = profile or CalculationProfile.report(model_config)
    active_factor_names = list(
        dict.fromkeys(
            str(position["factor"])
            for position in portfolio_config["positions"]
            if position["instrument_type"] != "cash"
        )
    )
    missing = sorted(set(active_factor_names) - set(factors.columns))
    if missing:
        raise ValueError(f"Portfolio factors are absent from market data: {', '.join(missing)}")
    active_factors = factors.loc[:, active_factor_names].copy()

    window = int(model_config["estimation_window"])
    if len(active_factors) <= window:
        raise ValueError(
            f"Insufficient estimation history: {len(active_factors)} rows for {window}-row window."
        )
    portfolio = run_portfolio_history(
        active_factors,
        portfolio_config,
        reconciliation_tolerance_usd=float(model_config["pnl_tolerance_usd"]),
    )
    snapshot = portfolio.ending_snapshot
    estimation = active_factors.iloc[-window:]
    covariance = estimation.cov()
    factor_order = list(estimation.columns)
    position_exposure = factor_exposure_by_position(snapshot, factor_order)
    total_exposure = position_exposure.sum(axis=0).to_numpy(dtype=float)
    historical_position_pnl = revalue_factor_shocks(snapshot, estimation)
    historical_losses = -historical_position_pnl.sum(axis=1)

    nav = float(portfolio.daily.iloc[-1]["nav"])
    risk_rows: list[dict[str, Any]] = []
    historical_estimates: dict[float, HistoricalRiskEstimate] = {}
    monte_carlo_estimates: dict[float, MonteCarloRiskEstimate] = {}
    for confidence in [float(value) for value in model_config["confidence_levels"]]:
        historical = historical_var_es(historical_losses.to_numpy(dtype=float), confidence)
        historical_estimates[confidence] = historical
        parametric = parametric_var_es(
            total_exposure, covariance.to_numpy(dtype=float), confidence
        )
        monte_carlo, _ = monte_carlo_portfolio_var_es(
            snapshot,
            covariance,
            confidence,
            profile.current_paths,
            int(model_config["master_seed"]),
        )
        monte_carlo_estimates[confidence] = monte_carlo
        for model, estimate in (
            ("Historical", historical),
            ("Parametric Normal", parametric),
            ("Monte Carlo Normal", monte_carlo),
        ):
            risk_rows.append(
                {
                    "model": model,
                    "confidence": confidence,
                    "var": estimate.var,
                    "es": estimate.es,
                    "var_pct_nav": estimate.var / nav,
                    "es_pct_nav": estimate.es / nav,
                    "effective_tail_mass": getattr(estimate, "effective_tail_mass", np.nan),
                }
            )
    current_risk = pd.DataFrame(risk_rows).set_index(["model", "confidence"], drop=False)

    primary_var_confidence = float(model_config["primary_var_confidence"])
    primary_es_confidence = float(model_config["primary_es_confidence"])
    decomposition = parametric_contributions(
        position_exposure, covariance, primary_var_confidence
    )
    historical_es_position = historical_es_contributions(
        historical_position_pnl,
        historical_estimates[primary_es_confidence].scenario_weights,
    )
    position_contributions = decomposition.position.copy()
    position_contributions["historical_es_contribution"] = historical_es_position
    position_contributions["asset_class"] = snapshot.loc[
        position_contributions.index, "asset_class"
    ]
    position_contributions["factor"] = snapshot.loc[position_contributions.index, "factor"]
    asset_class_contributions = position_contributions.groupby("asset_class", sort=False)[
        ["component_var", "historical_es_contribution"]
    ].sum()
    historical_factor_contributions = position_contributions.groupby("factor", sort=False)[
        "historical_es_contribution"
    ].sum()
    factor_contributions = decomposition.factor.copy()
    factor_contributions["historical_es_contribution"] = (
        historical_factor_contributions.reindex(factor_contributions.index, fill_value=0.0)
    )
    negative_hedges = position_contributions[position_contributions["component_var"] < 0.0]
    top_three_concentration = (
        float(position_contributions["component_var"].nlargest(3).sum() / decomposition.total_var)
        if decomposition.total_var
        else 0.0
    )

    forecasts = rolling_var_forecasts(
        active_factors,
        portfolio,
        window=window,
        confidence=primary_var_confidence,
        monte_carlo_paths=profile.rolling_paths,
        master_seed=int(model_config["master_seed"]),
        model_version=str(model_config["model_version"]),
    )
    scorecard = backtest_scorecard(forecasts)
    stresses = run_deterministic_stresses(snapshot, stress_config, nav)
    crises = run_deterministic_stresses(snapshot, crisis_config, nav)

    base_correlation = estimation.corr()
    estimation_portfolio_pnl = historical_position_pnl.sum(axis=1)
    stress_regime = estimation.loc[
        estimation_portfolio_pnl <= estimation_portfolio_pnl.quantile(0.20)
    ]
    crisis_correlation = stress_regime.corr().reindex(index=factor_order, columns=factor_order)
    distributional_rows: list[dict[str, Any]] = []
    for scale in (1.5, 2.0):
        result = volatility_correlation_stress(
            snapshot,
            covariance,
            crisis_correlation,
            scale,
            primary_var_confidence,
            profile.current_paths,
            int(model_config["master_seed"]),
        )
        distributional_rows.append(
            {
                "volatility_scale": scale,
                "immediate_pnl": result["immediate_deterministic_pnl"],
                "parametric_var": result["stressed_parametric_var"],
                "parametric_increase": result["parametric_var_increase_pct"],
                "monte_carlo_var": result["stressed_monte_carlo_var"],
                "monte_carlo_es": result["stressed_monte_carlo_es"],
            }
        )
    distributional_stress = pd.DataFrame(distributional_rows).set_index("volatility_scale")

    convergence_rows: list[dict[str, Any]] = []
    for paths in profile.convergence_paths:
        for seed in profile.convergence_seeds:
            estimate, _ = monte_carlo_portfolio_var_es(
                snapshot, covariance, primary_var_confidence, paths, seed
            )
            convergence_rows.append(
                {"paths": paths, "seed": seed, "var": estimate.var, "es": estimate.es}
            )
    convergence = pd.DataFrame(convergence_rows)
    convergence_pivot = convergence.pivot(index="seed", columns="paths", values=["var", "es"])
    comparison_low = profile.convergence_paths[-2]
    comparison_high = profile.convergence_paths[-1]
    convergence_summary = pd.DataFrame(index=convergence_pivot.index)
    convergence_summary["comparison_low_paths"] = comparison_low
    convergence_summary["comparison_high_paths"] = comparison_high
    convergence_summary["var_abs_difference_pct"] = (
        convergence_pivot[("var", comparison_low)]
        / convergence_pivot[("var", comparison_high)]
        - 1.0
    ).abs()
    convergence_summary["es_abs_difference_pct"] = (
        convergence_pivot[("es", comparison_low)]
        / convergence_pivot[("es", comparison_high)]
        - 1.0
    ).abs()
    convergence_summary["var_target_below_2pct"] = (
        convergence_summary["var_abs_difference_pct"] < 0.02
    )

    return CalculatedPortfolioRisk(
        portfolio_config=portfolio_config,
        active_factors=active_factors,
        portfolio=portfolio,
        snapshot=snapshot,
        current_risk=current_risk,
        forecasts=forecasts,
        scorecard=scorecard,
        position_contributions=position_contributions,
        factor_contributions=factor_contributions,
        asset_class_contributions=asset_class_contributions,
        negative_hedges=negative_hedges,
        stresses=stresses,
        crises=crises,
        distributional_stress=distributional_stress,
        convergence=convergence,
        convergence_summary=convergence_summary,
        position_exposure=position_exposure,
        historical_losses=historical_losses,
        base_correlation=base_correlation,
        crisis_correlation=crisis_correlation,
        historical_estimates=historical_estimates,
        monte_carlo_estimates=monte_carlo_estimates,
        top_three_concentration=top_three_concentration,
        calculation_profile=profile,
    )

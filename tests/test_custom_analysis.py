from __future__ import annotations

from pathlib import Path

import numpy as np

from market_risk.analysis import CalculationProfile, calculate_portfolio_risk
from market_risk.config import load_yaml
from market_risk.data_pipeline import generate_synthetic_demo
from market_risk.portfolio_builder import load_default_portfolio, resolve_portfolio

ROOT = Path(__file__).resolve().parents[1]


def test_portfolio_edits_recalculate_every_linked_result() -> None:
    factors, _ = generate_synthetic_demo(periods=80, seed=17)
    catalog, library, _, _ = load_default_portfolio(ROOT)
    model = load_yaml(ROOT / "config/model_config.yaml")
    model["estimation_window"] = 50
    stress = load_yaml(ROOT / "config/stress_scenarios.yaml")
    crises = load_yaml(ROOT / "config/historical_crises.yaml")
    profile = CalculationProfile(
        current_paths=300,
        rolling_paths=100,
        convergence_paths=(100, 200, 300),
        convergence_seeds=(42,),
    )
    equity = library.allocation().with_weights({"NVDA": 0.80}, {})
    defensive = library.allocation().with_weights({"US2Y": 0.45, "GLD": 0.35}, {})

    equity_result = calculate_portfolio_risk(
        factors,
        resolve_portfolio(catalog, equity),
        model,
        stress,
        crises,
        profile=profile,
    )
    defensive_result = calculate_portfolio_risk(
        factors,
        resolve_portfolio(catalog, defensive),
        model,
        stress,
        crises,
        profile=profile,
    )

    assert set(equity_result.snapshot.index) == {"NVDA", "USD_CASH"}
    assert set(defensive_result.snapshot.index) == {"US2Y", "GLD", "USD_CASH"}
    assert not np.isclose(equity_result.nav, defensive_result.nav)
    equity_var = equity_result.current_risk.loc[("Parametric Normal", 0.99), "var"]
    defensive_var = defensive_result.current_risk.loc[("Parametric Normal", 0.99), "var"]
    assert not np.isclose(equity_var, defensive_var)
    assert not np.isclose(
        equity_result.stresses.summary.loc["global_equity_selloff", "scenario_loss"],
        defensive_result.stresses.summary.loc["global_equity_selloff", "scenario_loss"],
    )
    assert set(equity_result.position_contributions.index) == {"NVDA", "USD_CASH"}
    assert set(defensive_result.position_contributions.index) == {"US2Y", "GLD", "USD_CASH"}

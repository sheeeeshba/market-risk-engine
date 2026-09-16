from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_risk.config import load_yaml
from market_risk.portfolio import initial_position_snapshot
from market_risk.stress_testing import run_deterministic_stresses, volatility_correlation_stress

ROOT = Path(__file__).resolve().parents[1]


def test_required_stresses_reconcile_and_preserve_financial_signs() -> None:
    portfolio = load_yaml(ROOT / "config/core_portfolio.yaml")
    scenarios = load_yaml(ROOT / "config/stress_scenarios.yaml")
    snapshot = initial_position_snapshot(portfolio)

    result = run_deterministic_stresses(snapshot, scenarios, nav=10_000_000.0)

    assert set(result.summary.index) >= {
        "global_equity_selloff",
        "parallel_rates_up_100bp",
        "parallel_rates_up_200bp",
        "foreign_currencies_down_10pct",
        "stocks_and_bonds_fall",
        "flight_to_quality",
    }
    grouped = result.detail.groupby(level="scenario_id")["position_pnl"].sum()
    assert np.allclose(grouped.reindex(result.summary.index), result.summary["scenario_pnl"])
    rates = result.detail.xs("parallel_rates_up_100bp")
    assert rates.loc["US5Y", "position_pnl"] < 0.0
    assert rates.loc["US5Y", "position_pnl"] > rates.loc["US5Y", "duration_only_pnl"]
    fx = result.detail.xs("foreign_currencies_down_10pct")
    assert fx.loc["EURUSD_OVERLAY", "position_pnl"] == -75_000.0


def test_pure_volatility_stress_changes_risk_not_immediate_pnl() -> None:
    portfolio = load_yaml(ROOT / "config/core_portfolio.yaml")
    snapshot = initial_position_snapshot(portfolio)
    factors = ["SPY_RETURN", "QQQ_RETURN", "EFA_RETURN", "GLD_RETURN", "DGS5_CHANGE", "DGS10_CHANGE", "EURUSD_RETURN"]
    covariance = pd.DataFrame(np.diag([0.01**2] * 4 + [0.0005**2] * 2 + [0.005**2]), index=factors, columns=factors)

    result = volatility_correlation_stress(
        snapshot,
        covariance,
        crisis_correlation=pd.DataFrame(np.eye(7), index=factors, columns=factors),
        volatility_scale=2.0,
        confidence=0.99,
        monte_carlo_paths=2_000,
        seed=42,
    )

    assert result["immediate_deterministic_pnl"] == 0.0
    assert np.isclose(result["stressed_parametric_var"] / result["base_parametric_var"], 2.0)

from __future__ import annotations

import numpy as np

from market_risk.pnl import bond_pnl, etf_pnl, fx_pnl
from market_risk.var_models import monte_carlo_var_es, parametric_var_es


def test_canonical_direction_and_convexity_invariants() -> None:
    assert etf_pnl(-100.0, -0.10) == 10.0
    duration_only = -100.0 * 5.0 * 0.01
    duration_convexity = bond_pnl(100.0, 5.0, 20.0, 0.01)
    assert duration_convexity < 0.0
    assert duration_convexity > duration_only
    assert fx_pnl(100.0, -0.10) < 0.0


def test_linear_scaling_and_perfect_hedge() -> None:
    covariance = np.array([[0.01**2]])
    base = parametric_var_es(np.array([100.0]), covariance, 0.99)
    doubled = parametric_var_es(np.array([200.0]), covariance, 0.99)
    hedged = parametric_var_es(np.array([0.0]), covariance, 0.99)

    assert np.isclose(doubled.var, 2.0 * base.var)
    assert np.isclose(doubled.es, 2.0 * base.es)
    assert hedged.var == 0.0
    assert hedged.es == 0.0


def test_monte_carlo_approaches_parametric_for_linear_normal_fixture() -> None:
    exposure = np.array([100.0, 50.0])
    covariance = np.array([[0.01**2, 0.00002], [0.00002, 0.008**2]])
    parametric = parametric_var_es(exposure, covariance, 0.99)
    simulation = monte_carlo_var_es(exposure, covariance, 0.99, paths=100_000, seed=42)

    assert abs(simulation.var / parametric.var - 1.0) < 0.03
    assert abs(simulation.es / parametric.es - 1.0) < 0.04


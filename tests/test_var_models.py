from __future__ import annotations

import numpy as np

from market_risk.var_models import (
    historical_var_es,
    monte_carlo_var_es,
    parametric_var_es,
)


def test_historical_estimator_uses_exact_tied_tail_mass() -> None:
    losses = np.array([10.0, 8.0, 8.0, 2.0, 0.0])
    result = historical_var_es(losses, confidence=0.60)

    assert result.var == 8.0
    assert result.es == 9.0
    assert result.effective_tail_mass == 2.0
    assert np.allclose(result.scenario_weights, [0.5, 0.25, 0.25, 0.0, 0.0])
    assert result.scenario_weights.sum() == 1.0


def test_parametric_normal_matches_known_one_factor_result() -> None:
    result = parametric_var_es(
        exposure=np.array([100.0]),
        covariance=np.array([[0.01**2]]),
        confidence=0.99,
    )

    assert np.isclose(result.sigma_pnl, 1.0)
    assert np.isclose(result.var, 2.326347874, rtol=1e-8)
    assert result.es >= result.var


def test_zero_covariance_has_zero_risk_and_monte_carlo_is_reproducible() -> None:
    exposure = np.array([100.0, -50.0])
    covariance = np.zeros((2, 2))
    parametric = parametric_var_es(exposure, covariance, 0.99)
    assert parametric.var == 0.0
    assert parametric.es == 0.0

    first = monte_carlo_var_es(
        exposure=exposure,
        covariance=np.array([[0.01, 0.002], [0.002, 0.005]]),
        confidence=0.99,
        paths=20_000,
        seed=42,
    )
    second = monte_carlo_var_es(
        exposure=exposure,
        covariance=np.array([[0.01, 0.002], [0.002, 0.005]]),
        confidence=0.99,
        paths=20_000,
        seed=42,
    )
    assert first.var == second.var
    assert first.es == second.es
    assert first.es >= first.var


def test_risk_does_not_decrease_with_confidence() -> None:
    losses = np.arange(1.0, 101.0)
    values = [historical_var_es(losses, confidence).var for confidence in [0.95, 0.975, 0.99]]
    assert values == sorted(values)


from __future__ import annotations

import numpy as np
import pandas as pd

from market_risk.contributions import historical_es_contributions, parametric_contributions
from market_risk.var_models import historical_var_es


def test_parametric_position_and_factor_contributions_reconcile_with_hedge() -> None:
    exposures = pd.DataFrame({"EQUITY": [100.0, -20.0]}, index=["LONG", "HEDGE"])
    covariance = pd.DataFrame([[0.01**2]], index=["EQUITY"], columns=["EQUITY"])

    result = parametric_contributions(exposures, covariance, confidence=0.99)

    assert np.isclose(result.position["component_var"].sum(), result.total_var)
    assert np.isclose(result.factor["component_var"].sum(), result.total_var)
    assert result.position.loc["HEDGE", "component_var"] < 0.0
    assert result.position.loc["LONG", "standalone_var"] > result.total_var


def test_historical_es_position_contributions_use_exact_portfolio_tail() -> None:
    pnl = pd.DataFrame(
        {"A": [-8.0, -5.0, -4.0, 2.0, 3.0], "B": [-2.0, -3.0, -4.0, 0.0, 1.0]}
    )
    estimate = historical_var_es(-pnl.sum(axis=1).to_numpy(), confidence=0.60)
    contributions = historical_es_contributions(pnl, estimate.scenario_weights)

    assert np.isclose(contributions.sum(), estimate.es)
    assert contributions.index.tolist() == ["A", "B"]


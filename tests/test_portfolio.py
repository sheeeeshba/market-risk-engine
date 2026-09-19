from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_risk.data_pipeline import FACTOR_COLUMNS
from market_risk.portfolio import initial_position_snapshot, run_portfolio_history
from market_risk.portfolio_builder import load_default_portfolio
from market_risk.validation import validate_portfolio_config

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_portfolio_separates_funding_from_overlay() -> None:
    _, _, _, config = load_default_portfolio(ROOT)
    summary = validate_portfolio_config(config)
    snapshot = initial_position_snapshot(config)

    assert summary["funded_weight_sum"] == 1.0
    assert np.isclose(summary["net_funded_market_value"], 10_000_000.0)
    assert summary["overlay_notional"] == 500_000.0
    assert snapshot.loc["EURUSD_OVERLAY", "market_value"] == 0.0


def test_portfolio_history_reconciles_pnl_nav_and_monthly_rebalance() -> None:
    _, _, _, config = load_default_portfolio(ROOT)
    factors = pd.DataFrame(
        0.0,
        index=pd.to_datetime(["2024-01-31", "2024-02-01"]),
        columns=FACTOR_COLUMNS,
    )
    factors.loc["2024-01-31", ["SPY_RETURN", "EURUSD_RETURN"]] = -0.10
    result = run_portfolio_history(factors, config)

    assert result.daily.loc["2024-01-31", "portfolio_pnl"] == -150_000.0
    assert np.isclose(result.daily.loc["2024-01-31", "nav"], 9_850_000.0)
    assert np.allclose(result.daily["position_pnl_sum"], result.daily["portfolio_pnl"])
    assert np.allclose(result.daily["funded_market_value"], result.daily["nav"])
    assert result.daily["rebalanced"].all()

    jan = result.positions.xs(pd.Timestamp("2024-01-31"))
    assert np.isclose(jan.loc["SPY", "end_market_value"], 0.10 * 9_850_000.0)
    assert np.isclose(jan.loc["EURUSD_OVERLAY", "end_notional"], 0.05 * 9_850_000.0)

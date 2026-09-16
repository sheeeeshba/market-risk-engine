from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_risk.config import load_yaml
from market_risk.portfolio import initial_position_snapshot, run_portfolio_history
from market_risk.validation import validate_portfolio_config

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_portfolio_separates_funding_from_overlay() -> None:
    config = load_yaml(ROOT / "config/core_portfolio.yaml")
    summary = validate_portfolio_config(config)
    snapshot = initial_position_snapshot(config)

    assert summary["funded_weight_sum"] == 1.0
    assert summary["net_funded_market_value"] == 10_000_000.0
    assert summary["overlay_notional"] == 750_000.0
    assert snapshot.loc["EURUSD_OVERLAY", "market_value"] == 0.0


def test_portfolio_history_reconciles_pnl_nav_and_monthly_rebalance() -> None:
    config = load_yaml(ROOT / "config/core_portfolio.yaml")
    factors = pd.DataFrame(
        [
            [-0.10, 0.0, 0.0, 0.0, 0.0, 0.0, -0.10],
            [0.00, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00],
        ],
        index=pd.to_datetime(["2024-01-31", "2024-02-01"]),
        columns=[
            "SPY_RETURN",
            "QQQ_RETURN",
            "EFA_RETURN",
            "GLD_RETURN",
            "DGS5_CHANGE",
            "DGS10_CHANGE",
            "EURUSD_RETURN",
        ],
    )
    result = run_portfolio_history(factors, config)

    assert result.daily.loc["2024-01-31", "portfolio_pnl"] == -275_000.0
    assert result.daily.loc["2024-01-31", "nav"] == 9_725_000.0
    assert np.allclose(result.daily["position_pnl_sum"], result.daily["portfolio_pnl"])
    assert np.allclose(result.daily["funded_market_value"], result.daily["nav"])
    assert result.daily["rebalanced"].all()

    jan = result.positions.xs(pd.Timestamp("2024-01-31"))
    assert jan.loc["SPY", "end_market_value"] == 0.20 * 9_725_000.0
    assert jan.loc["EURUSD_OVERLAY", "end_notional"] == 0.075 * 9_725_000.0


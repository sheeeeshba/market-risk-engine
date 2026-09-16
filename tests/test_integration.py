from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_risk.backtesting import backtest_scorecard, rolling_var_forecasts
from market_risk.config import load_yaml
from market_risk.contributions import parametric_contributions
from market_risk.data_pipeline import generate_synthetic_demo
from market_risk.portfolio import run_portfolio_history
from market_risk.reporting import create_core_figures, render_market_risk_report
from market_risk.stress_testing import run_deterministic_stresses
from market_risk.var_models import (
    factor_exposure_by_position,
    historical_var_es,
    monte_carlo_portfolio_var_es,
    parametric_var_es,
    revalue_factor_shocks,
)

ROOT = Path(__file__).resolve().parents[1]


def test_small_portfolio_flows_through_report_and_eight_figures(tmp_path: Path) -> None:
    factors, metadata = generate_synthetic_demo(periods=270, seed=7)
    portfolio_config = load_yaml(ROOT / "config/core_portfolio.yaml")
    stress_config = load_yaml(ROOT / "config/stress_scenarios.yaml")
    history = run_portfolio_history(factors, portfolio_config)
    snapshot = history.ending_snapshot
    estimation = factors.iloc[-250:]
    covariance = estimation.cov()
    exposures = factor_exposure_by_position(snapshot, list(estimation.columns))
    position_pnl = revalue_factor_shocks(snapshot, estimation)
    losses = -position_pnl.sum(axis=1)
    historical = historical_var_es(losses.to_numpy(), 0.99)
    parametric = parametric_var_es(exposures.sum(axis=0).to_numpy(), covariance.to_numpy(), 0.99)
    monte_carlo, _ = monte_carlo_portfolio_var_es(snapshot, covariance, 0.99, 1_000, 7)
    current_risk = pd.DataFrame(
        [
            {"model": "Historical", "confidence": 0.99, "var": historical.var, "es": historical.es},
            {"model": "Parametric Normal", "confidence": 0.99, "var": parametric.var, "es": parametric.es},
            {"model": "Monte Carlo Normal", "confidence": 0.99, "var": monte_carlo.var, "es": monte_carlo.es},
        ]
    )
    contributions = parametric_contributions(exposures, covariance, 0.99).position
    forecasts = rolling_var_forecasts(
        factors, history, window=250, confidence=0.99, monte_carlo_paths=500, master_seed=7
    )
    scorecard = backtest_scorecard(forecasts)
    stresses = run_deterministic_stresses(snapshot, stress_config, history.daily.iloc[-1]["nav"])
    correlation = estimation.corr()

    figures = create_core_figures(
        tmp_path / "figures",
        str(factors.index[-1].date()),
        snapshot,
        exposures,
        history.daily,
        losses,
        current_risk,
        forecasts,
        scorecard,
        contributions,
        stresses.summary,
        stresses.detail,
        correlation,
        correlation,
        synthetic=True,
    )
    assert len(figures) == 8
    assert all(Path(path).exists() for path in figures.values())

    template = tmp_path / "report.md.j2"
    template.write_text("snapshot={{ snapshot_id }}; var={{ var }}\n", encoding="utf-8")
    report = render_market_risk_report(
        template,
        tmp_path / "report.md",
        {"snapshot_id": metadata["snapshot_id"], "var": f"{historical.var:.6f}"},
    )
    text = report.read_text(encoding="utf-8")
    assert metadata["snapshot_id"] in text
    assert f"{historical.var:.6f}" in text


"""End-to-end market-risk pipeline behind one testable interface."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .analysis import CalculationProfile, calculate_portfolio_risk
from .config import configuration_hash, load_yaml, project_root
from .data_pipeline import (
    SYNTHETIC_WATERMARK,
    download_live_factors,
    generate_synthetic_demo,
    load_snapshot,
    save_snapshot,
)
from .pnl import dv01
from .portfolio_builder import load_default_portfolio
from .reporting import create_core_figures, render_market_risk_report, runtime_versions
from .verification import record_gate


def _currency(value: float) -> str:
    return f"USD {value:,.0f}"


def _percent(value: float) -> str:
    return f"{value:.2%}"


def _markdown(frame: pd.DataFrame, formats: dict[str, Any] | None = None) -> str:
    display = frame.copy()
    for column, formatter in (formats or {}).items():
        if column in display:
            display[column] = display[column].map(formatter)
    return display.to_markdown(index=True)


def create_synthetic_snapshot(
    root: str | Path | None = None,
    periods: int = 520,
    seed: int = 42,
) -> dict[str, Any]:
    """Create the distributable artificial snapshot used for engineering verification."""

    root = Path(root or project_root())
    factors, metadata = generate_synthetic_demo(periods=periods, seed=seed)
    metadata["created_utc"] = datetime.now(timezone.utc).isoformat()
    factors_path = root / "data/snapshots/synthetic_demo_factors.csv"
    metadata_path = root / "data/snapshots/synthetic_demo_metadata.json"
    save_snapshot(factors, metadata, str(factors_path), str(metadata_path))
    return {"factors_path": str(factors_path), "metadata_path": str(metadata_path), **metadata}


def load_factor_data(
    root: Path,
    data_mode: str,
    model_config: dict[str, Any],
    fred_api_key: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if data_mode == "synthetic_demo":
        create_synthetic_snapshot(root, periods=520, seed=int(model_config["master_seed"]))
    if data_mode in {"snapshot", "synthetic_demo"}:
        factors_path = root / "data/snapshots/synthetic_demo_factors.csv"
        metadata_path = root / "data/snapshots/synthetic_demo_metadata.json"
        if not factors_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(
                "Snapshot files are missing. Run `python -m market_risk.cli make-synthetic-snapshot` "
                "for the artificial engineering fixture, or supply a verified real snapshot."
            )
        factors = load_snapshot(str(factors_path))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return factors, metadata
    if data_mode == "live":
        factors, quality, metadata = download_live_factors(
            start_date="2007-01-01",
            end_date=None,
            fred_api_key=fred_api_key,
            max_rate_fill_business_days=int(model_config["rate_forward_fill_business_days"]),
        )
        processed = root / "data/processed"
        processed.mkdir(parents=True, exist_ok=True)
        factors.to_csv(processed / "latest_live_factors.csv", index_label="portfolio_date")
        quality.to_csv(processed / "latest_live_data_quality.csv", index_label="portfolio_date")
        (processed / "latest_live_metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        return factors, metadata
    raise ValueError(f"Unsupported data mode: {data_mode!r}")


def run_pipeline(
    model_config_path: str | Path,
    data_mode: str | None = None,
    *,
    fred_api_key: str | None = None,
) -> dict[str, str]:
    """Run the validated snapshot pipeline and return generated artifact paths."""

    model_config_path = Path(model_config_path).resolve()
    root = model_config_path.parents[1]
    model_config = load_yaml(model_config_path)
    catalog_config = load_yaml(root / "config/instrument_catalog.yaml")
    portfolio_library_config = load_yaml(root / "config/core_portfolio.yaml")
    _, _, allocation, portfolio_config = load_default_portfolio(root)
    stress_config = load_yaml(root / "config/stress_scenarios.yaml")
    crisis_config = load_yaml(root / "config/historical_crises.yaml")
    config_hash = configuration_hash(
        model_config,
        catalog_config,
        portfolio_library_config,
        allocation.as_dict(),
        stress_config,
        crisis_config,
    )
    selected_mode = data_mode or str(model_config["data_mode_default"])
    factors, data_metadata = load_factor_data(
        root, selected_mode, model_config, fred_api_key=fred_api_key
    )
    synthetic = data_metadata.get("data_classification") == SYNTHETIC_WATERMARK

    calculation = calculate_portfolio_risk(
        factors,
        portfolio_config,
        model_config,
        stress_config,
        crisis_config,
        profile=CalculationProfile.report(model_config),
    )
    window = int(model_config["estimation_window"])
    portfolio = calculation.portfolio
    snapshot = calculation.snapshot
    as_of_date = calculation.as_of_date
    position_exposure = calculation.position_exposure
    historical_losses = calculation.historical_losses
    current_risk = calculation.current_risk
    historical_estimates = calculation.historical_estimates
    monte_carlo_estimates = calculation.monte_carlo_estimates
    primary_var_confidence = float(model_config["primary_var_confidence"])
    primary_es_confidence = float(model_config["primary_es_confidence"])
    position_contributions = calculation.position_contributions
    asset_class_contributions = calculation.asset_class_contributions
    factor_contributions = calculation.factor_contributions
    negative_hedges = calculation.negative_hedges
    top_three_concentration = calculation.top_three_concentration
    forecasts = calculation.forecasts
    scorecard = calculation.scorecard
    nav = calculation.nav
    stresses = calculation.stresses
    crises = calculation.crises
    base_correlation = calculation.base_correlation
    crisis_correlation = calculation.crisis_correlation
    distributional_stress = calculation.distributional_stress
    convergence = calculation.convergence
    convergence_summary = calculation.convergence_summary

    tables = root / "outputs/tables"
    figures_directory = root / "outputs/figures"
    tables.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(portfolio_config["positions"]).to_csv(
        tables / "portfolio_allocation.csv", index=False
    )
    portfolio.daily.to_csv(tables / "daily_portfolio_pnl.csv")
    portfolio.positions.to_csv(tables / "position_history.csv")
    current_risk.to_csv(tables / "current_risk.csv", index=False)
    forecasts.to_csv(tables / "rolling_forecasts.csv", index=False)
    scorecard.to_csv(tables / "backtesting_scorecard.csv")
    position_contributions.to_csv(tables / "risk_contributions.csv")
    factor_contributions.to_csv(tables / "factor_contributions.csv")
    asset_class_contributions.to_csv(tables / "asset_class_contributions.csv")
    negative_hedges.to_csv(tables / "negative_hedging_contributions.csv")
    stresses.summary.to_csv(tables / "stress_summary.csv")
    stresses.detail.to_csv(tables / "stress_detail.csv")
    crises.summary.to_csv(tables / "crisis_replay_summary.csv")
    distributional_stress.to_csv(tables / "volatility_correlation_stress.csv")
    convergence.to_csv(tables / "monte_carlo_convergence.csv", index=False)
    convergence_summary.to_csv(tables / "monte_carlo_convergence_summary.csv")
    (tables / "monte_carlo_diagnostics.json").write_text(
        json.dumps(
            {
                "confidence": primary_var_confidence,
                "paths": int(model_config["current_monte_carlo_paths"]),
                "seed": int(model_config["master_seed"]),
                "simulated_mean_pnl": monte_carlo_estimates[
                    primary_var_confidence
                ].simulated_mean_pnl,
                "simulated_sigma_pnl": monte_carlo_estimates[
                    primary_var_confidence
                ].simulated_sigma_pnl,
                "covariance_diagnostics": monte_carlo_estimates[
                    primary_var_confidence
                ].covariance_diagnostics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    figures = create_core_figures(
        figures_directory,
        as_of_date,
        snapshot,
        position_exposure,
        portfolio.daily,
        historical_losses,
        current_risk.reset_index(drop=True),
        forecasts,
        scorecard,
        position_contributions,
        stresses.summary,
        stresses.detail,
        base_correlation,
        crisis_correlation,
        synthetic,
    )

    report_directory = root / "reports/generated"
    report_path = report_directory / f"{as_of_date}_market_risk_report.md"
    summary_path = report_directory / f"{as_of_date}_one_page_risk_summary.md"
    relative_figures = {
        key: os.path.relpath(value, start=report_directory) for key, value in figures.items()
    }
    nav_row = portfolio.daily.iloc[-1]
    risk_99 = current_risk[current_risk["confidence"] == primary_var_confidence]
    risk_975 = current_risk[current_risk["confidence"] == primary_es_confidence]
    top_driver = position_contributions["component_var"].idxmax()
    worst_stress = stresses.summary["scenario_loss"].idxmax()
    warning_set = sorted(
        {
            warning
            for warnings in scorecard["warnings"]
            for warning in (warnings if isinstance(warnings, list) else [str(warnings)])
        }
    )
    portfolio_display = snapshot[
        ["instrument_type", "asset_class", "factor", "market_value", "notional"]
    ].copy()
    total_dv01 = sum(
        dv01(float(row["market_value"]), float(row["modified_duration"]))
        for _, row in snapshot[snapshot["instrument_type"] == "bond"].iterrows()
    )
    runtime = runtime_versions()
    context = {
        "portfolio_name": portfolio_config["portfolio_name"],
        "synthetic": synthetic,
        "as_of_date": as_of_date,
        "base_currency": portfolio_config["base_currency"],
        "model_version": model_config["model_version"],
        "data_source": data_metadata["source"],
        "snapshot_id": data_metadata["snapshot_id"],
        "data_timestamp": data_metadata.get("created_utc", "not recorded"),
        "lookback": window,
        "confidence_levels": ", ".join(f"{x:.1%}" for x in model_config["confidence_levels"]),
        "mc_paths": f"{calculation.calculation_profile.current_paths:,}",
        "seed": model_config["master_seed"],
        "configuration_hash": config_hash,
        "runtime": ", ".join(f"{key} {value}" for key, value in runtime.items()),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "nav": _currency(nav),
        "gross_exposure": _currency(float(nav_row["gross_funded_exposure"])),
        "overlay_notional": _currency(float(nav_row["overlay_notional"])),
        "var_low": _currency(float(risk_99["var"].min())),
        "var_high": _currency(float(risk_99["var"].max())),
        "es_low": _currency(float(risk_975["es"].min())),
        "es_high": _currency(float(risk_975["es"].max())),
        "top_risk_driver": top_driver,
        "top_risk_contribution": _currency(float(position_contributions.loc[top_driver, "component_var"])),
        "worst_stress": stresses.summary.loc[worst_stress, "scenario_name"],
        "worst_stress_loss": _currency(float(stresses.summary.loc[worst_stress, "scenario_loss"])),
        "worst_stress_pct": _percent(float(stresses.summary.loc[worst_stress, "loss_pct_nav"])),
        "forecast_count": forecasts["forecast_date"].nunique(),
        "portfolio_table": _markdown(portfolio_display, {"market_value": _currency, "notional": _currency}),
        "total_dv01": _currency(total_dv01),
        "current_risk_table": _markdown(
            current_risk.reset_index(drop=True).set_index(["model", "confidence"])[["var", "es", "var_pct_nav", "es_pct_nav"]],
            {"var": _currency, "es": _currency, "var_pct_nav": _percent, "es_pct_nav": _percent},
        ),
        "historical_tail_mass": f"{historical_estimates[primary_es_confidence].effective_tail_mass:.2f}",
        "position_contribution_table": _markdown(
            position_contributions[["component_var", "historical_es_contribution", "asset_class", "factor"]],
            {"component_var": _currency, "historical_es_contribution": _currency},
        ),
        "asset_class_contribution_table": _markdown(
            asset_class_contributions,
            {"component_var": _currency, "historical_es_contribution": _currency},
        ),
        "factor_contribution_table": _markdown(
            factor_contributions[["exposure", "component_var", "historical_es_contribution"]],
            {"exposure": _currency, "component_var": _currency, "historical_es_contribution": _currency},
        ),
        "top_three_concentration": _percent(top_three_concentration),
        "negative_hedges": ", ".join(negative_hedges.index) if len(negative_hedges) else "None in the primary Parametric decomposition",
        "convergence_table": _markdown(
            convergence_summary,
            {"var_abs_difference_pct": _percent, "es_abs_difference_pct": _percent},
        ),
        "convergence_low_paths": f"{calculation.calculation_profile.convergence_paths[-2]:,}",
        "convergence_high_paths": f"{calculation.calculation_profile.convergence_paths[-1]:,}",
        "max_var_convergence_difference": _percent(
            float(convergence_summary["var_abs_difference_pct"].max())
        ),
        "max_es_convergence_difference": _percent(
            float(convergence_summary["es_abs_difference_pct"].max())
        ),
        "backtest_table": _markdown(
            scorecard[["forecasts", "exceptions", "expected_exceptions", "p_value_uc", "p_value_ind", "p_value_cc"]],
            {"expected_exceptions": lambda x: f"{x:.2f}", "p_value_uc": lambda x: f"{x:.3f}", "p_value_ind": lambda x: f"{x:.3f}", "p_value_cc": lambda x: f"{x:.3f}"},
        ),
        "backtest_warnings": warning_set,
        "stress_table": _markdown(
            stresses.summary[["scenario_name", "scenario_loss", "loss_pct_nav", "principal_loss_driver"]],
            {"scenario_loss": _currency, "loss_pct_nav": _percent},
        ),
        "crisis_table": _markdown(
            crises.summary[["scenario_name", "horizon", "scenario_loss", "loss_pct_nav"]],
            {"scenario_loss": _currency, "loss_pct_nav": _percent},
        ),
        "volatility_stress_table": _markdown(
            distributional_stress,
            {"immediate_pnl": _currency, "parametric_var": _currency, "parametric_increase": _percent, "monte_carlo_var": _currency, "monte_carlo_es": _currency},
        ),
        **{f"figure_{key}": value for key, value in relative_figures.items()},
    }
    render_market_risk_report(
        root / "reports/templates/market_risk_report.md.j2", report_path, context
    )
    summary_path.write_text(
        "\n".join(
            [
                f"# One-Page Market Risk Summary — {as_of_date}",
                "",
                f"> **{SYNTHETIC_WATERMARK}.** Educational model — not approved for regulatory capital or live trading limits."
                if synthetic
                else "> Educational model — not approved for regulatory capital or live trading limits.",
                "",
                f"- NAV: **{_currency(nav)}**; funded gross exposure: **{_currency(float(nav_row['gross_funded_exposure']))}**; overlay notional: **{_currency(float(nav_row['overlay_notional']))}**.",
                f"- 99% one-interval VaR range across Core models: **{_currency(float(risk_99['var'].min()))}–{_currency(float(risk_99['var'].max()))}**.",
                f"- 97.5% ES range: **{_currency(float(risk_975['es'].min()))}–{_currency(float(risk_975['es'].max()))}**.",
                f"- Largest component-VaR driver: **{top_driver}**, {_currency(float(position_contributions.loc[top_driver, 'component_var']))}.",
                f"- Worst hypothetical stress: **{stresses.summary.loc[worst_stress, 'scenario_name']}**, loss {_currency(float(stresses.summary.loc[worst_stress, 'scenario_loss']))} ({_percent(float(stresses.summary.loc[worst_stress, 'loss_pct_nav']))} of NAV).",
                f"- Backtesting: **{forecasts['forecast_date'].nunique()} forecasts per model**; warnings: {', '.join(warning_set)}.",
                f"- Monte Carlo convergence: maximum {calculation.calculation_profile.convergence_paths[-2]:,}-vs-{calculation.calculation_profile.convergence_paths[-1]:,} 99% VaR difference **{_percent(float(convergence_summary['var_abs_difference_pct'].max()))}**; ES difference **{_percent(float(convergence_summary['es_abs_difference_pct'].max()))}**.",
                "",
                "Primary control: every forecast uses only information through its forecast date and next-valid-date hypothetical P&L. Primary limitation: the bundled results use artificial data and cannot support historical or resume claims.",
                "",
                "![Rolling VaR versus realized loss](../../outputs/figures/03_rolling_var_vs_realized_loss.png)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    verified_outputs = [
        str(report_path),
        str(summary_path),
        *(str(path) for path in sorted(tables.glob("*.csv"))),
        *(str(path) for path in sorted(figures_directory.glob("*.png"))),
    ]
    record_gate(
        root / "outputs/verification_manifest.json",
        "snapshot_pipeline",
        "python -m market_risk.cli run --config config/model_config.yaml "
        f"--data-mode {selected_mode}",
        0,
        root,
        config_hash,
        data_metadata["snapshot_id"],
        verified_outputs,
    )
    return {
        "report": str(report_path),
        "summary": str(summary_path),
        "manifest": str(root / "outputs/verification_manifest.json"),
        "figures": str(figures_directory),
        "tables": str(tables),
        "snapshot_id": data_metadata["snapshot_id"],
        "data_classification": data_metadata["data_classification"],
    }

"""Deterministic management-report tables, figures, and Markdown rendering."""

from __future__ import annotations

import platform
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from jinja2 import Environment, FileSystemLoader, StrictUndefined

WATERMARK = "SYNTHETIC DATA — NOT FOR RESUME RESULTS"
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]


def _finish_figure(figure: plt.Figure, path: Path, source_note: str) -> None:
    figure.text(0.01, 0.01, source_note, fontsize=8, color="#555555")
    figure.tight_layout(rect=(0, 0.035, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def create_core_figures(
    output_directory: str | Path,
    as_of_date: str,
    snapshot: pd.DataFrame,
    factor_exposures: pd.DataFrame,
    portfolio_daily: pd.DataFrame,
    historical_losses: pd.Series,
    current_risk: pd.DataFrame,
    forecasts: pd.DataFrame,
    scorecard: pd.DataFrame,
    position_contributions: pd.DataFrame,
    stress_summary: pd.DataFrame,
    stress_detail: pd.DataFrame,
    base_correlation: pd.DataFrame,
    crisis_correlation: pd.DataFrame,
    synthetic: bool,
) -> dict[str, str]:
    """Create the eight required decision-focused visualisations."""

    destination = Path(output_directory)
    note = (
        f"{WATERMARK}. Source: deterministic artificial fixture. As of {as_of_date}."
        if synthetic
        else f"Source: validated processed snapshot. As of {as_of_date}."
    )
    paths: dict[str, str] = {}
    sns.set_theme(style="whitegrid", context="notebook")

    # 1. Asset-class and factor exposures.
    funded = snapshot[snapshot["instrument_type"] != "fx_forward"].groupby("asset_class")[
        "market_value"
    ].sum()
    factor_total = factor_exposures.sum(axis=0)
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    funded.sort_values().plot.barh(ax=axes[0], color=COLORS[0])
    axes[0].set(title=f"Funded Exposure by Asset Class — {as_of_date}", xlabel="USD", ylabel="")
    factor_total.sort_values().plot.barh(ax=axes[1], color=COLORS[2])
    axes[1].set(title="Signed Linear Factor Exposure", xlabel="USD sensitivity", ylabel="")
    axes[1].axvline(0, color="#333333", linewidth=0.8)
    path = destination / "01_exposure_by_asset_class_and_factor.png"
    _finish_figure(figure, path, note)
    paths["exposures"] = str(path)

    # 2. Loss distribution and three-model thresholds.
    figure, axis = plt.subplots(figsize=(11, 6))
    sns.histplot(historical_losses, bins=45, stat="density", color=COLORS[0], alpha=0.45, ax=axis)
    primary = current_risk[current_risk["confidence"] == current_risk["confidence"].max()]
    for color, (_, row) in zip(COLORS[1:], primary.iterrows(), strict=False):
        axis.axvline(row["var"], color=color, linewidth=2, label=f"{row['model']} VaR")
        axis.axvline(row["es"], color=color, linewidth=1.3, linestyle="--", label=f"{row['model']} ES")
    axis.set(
        title=f"Portfolio Loss Distribution with 99% Risk Thresholds — {as_of_date}",
        xlabel="One valid interval loss (USD)",
        ylabel="Density",
    )
    axis.legend(fontsize=8, ncol=2)
    path = destination / "02_loss_distribution_var_es.png"
    _finish_figure(figure, path, note)
    paths["loss_distribution"] = str(path)

    # 3. Rolling VaR versus realized loss.
    figure, axis = plt.subplots(figsize=(13, 6))
    realized = forecasts.drop_duplicates("forecast_date").set_index("realized_date")["realized_loss"]
    axis.plot(realized.index, realized, color="#333333", linewidth=0.9, label="Realized hypothetical loss")
    for color, (model, group) in zip(
        COLORS, forecasts.groupby("model", sort=False), strict=False
    ):
        axis.plot(group["realized_date"], group["var"], color=color, linewidth=1.25, label=f"{model} VaR")
    axis.axhline(0.0, color="#777777", linewidth=0.7)
    axis.set(title="Rolling 99% VaR versus Next-Interval Loss", xlabel="Realized date", ylabel="USD loss")
    axis.legend(fontsize=8)
    path = destination / "03_rolling_var_vs_realized_loss.png"
    _finish_figure(figure, path, note)
    paths["rolling_var"] = str(path)

    # 4. Exception timeline and breach magnitude.
    figure, axis = plt.subplots(figsize=(13, 5))
    for color, (model, group) in zip(
        COLORS, forecasts.groupby("model", sort=False), strict=False
    ):
        breaches = group[group["exception"]]
        axis.scatter(
            breaches["realized_date"],
            breaches["breach_magnitude"],
            color=color,
            s=38,
            label=f"{model} exceptions",
        )
    axis.set(title="VaR Exception Timeline and Magnitude", xlabel="Realized date", ylabel="Loss above VaR (USD)")
    axis.legend(fontsize=8)
    path = destination / "04_exception_timeline.png"
    _finish_figure(figure, path, note)
    paths["exceptions"] = str(path)

    # 5. Backtesting scorecard.
    score = scorecard.reset_index()
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(score))
    axes[0].bar(x - 0.18, score["observed_exception_rate"], 0.36, label="Observed", color=COLORS[1])
    axes[0].bar(x + 0.18, score["expected_exception_rate"], 0.36, label="Expected", color=COLORS[0])
    axes[0].set_xticks(x, score["model"], rotation=20, ha="right")
    axes[0].set(title="Exception Rates", ylabel="Rate")
    axes[0].legend()
    pvalues = score.set_index("model")[["p_value_uc", "p_value_ind", "p_value_cc"]]
    sns.heatmap(pvalues, annot=True, fmt=".3f", vmin=0, vmax=1, cmap="viridis", ax=axes[1])
    axes[1].set(title="Coverage-Test p-values", xlabel="Test", ylabel="")
    path = destination / "05_backtesting_scorecard.png"
    _finish_figure(figure, path, note)
    paths["backtesting_scorecard"] = str(path)

    # 6. Position component VaR.
    figure, axis = plt.subplots(figsize=(11, 6))
    ordered = position_contributions["component_var"].sort_values()
    colors = [COLORS[2] if value < 0 else COLORS[1] for value in ordered]
    ordered.plot.barh(ax=axis, color=colors)
    axis.axvline(0, color="#333333", linewidth=0.8)
    axis.set(title="99% Parametric Component VaR by Position", xlabel="USD contribution", ylabel="")
    path = destination / "06_position_risk_contribution.png"
    _finish_figure(figure, path, note)
    paths["contributions"] = str(path)

    # 7. Worst scenario loss waterfall.
    worst_scenario = str(stress_summary["scenario_loss"].idxmax())
    losses = stress_detail.xs(worst_scenario)["position_loss"].sort_values(ascending=False)
    cumulative = losses.cumsum().shift(fill_value=0.0)
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.bar(losses.index, losses, bottom=cumulative, color=[COLORS[1] if x >= 0 else COLORS[2] for x in losses])
    axis.plot(losses.index, losses.cumsum(), color="#333333", marker="o", linewidth=1.2)
    axis.set(
        title=f"Stress-Loss Waterfall: {stress_summary.loc[worst_scenario, 'scenario_name']}",
        xlabel="Position",
        ylabel="Cumulative USD loss",
    )
    axis.tick_params(axis="x", rotation=30)
    path = destination / "07_stress_loss_waterfall.png"
    _finish_figure(figure, path, note)
    paths["stress_waterfall"] = str(path)

    # 8. Normal-versus-crisis correlation.
    figure, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.heatmap(base_correlation, vmin=-1, vmax=1, center=0, cmap="vlag", ax=axes[0])
    sns.heatmap(crisis_correlation, vmin=-1, vmax=1, center=0, cmap="vlag", ax=axes[1])
    axes[0].set_title("Full-window Correlation")
    axes[1].set_title("Synthetic Stress-Regime Correlation")
    path = destination / "08_normal_vs_crisis_correlation.png"
    _finish_figure(figure, path, note)
    paths["correlations"] = str(path)
    return paths


def render_market_risk_report(
    template_path: str | Path,
    output_path: str | Path,
    context: Mapping[str, Any],
) -> Path:
    """Render a strict Jinja template and reject unresolved placeholders."""

    template_path = Path(template_path)
    environment = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    rendered = environment.get_template(template_path.name).render(**dict(context))
    if "{{" in rendered or "{%" in rendered:
        raise ValueError("Generated report contains unresolved template placeholders.")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered.rstrip() + "\n", encoding="utf-8")
    return target


def runtime_versions() -> dict[str, str]:
    """Return reportable runtime versions without importing package metadata manually."""

    import matplotlib as mpl
    import scipy

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "matplotlib": mpl.__version__,
    }

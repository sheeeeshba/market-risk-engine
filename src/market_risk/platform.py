"""High-leverage interface for running and inspecting one market-risk analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import load_yaml, project_root
from .data_pipeline import SYNTHETIC_WATERMARK
from .models import ArtifactPaths, MarketRiskAnalysis, RiskHeadline

TABLE_FILES = {
    "asset_class_contributions": "asset_class_contributions.csv",
    "backtesting_scorecard": "backtesting_scorecard.csv",
    "crisis_replay_summary": "crisis_replay_summary.csv",
    "current_risk": "current_risk.csv",
    "daily_portfolio_pnl": "daily_portfolio_pnl.csv",
    "factor_contributions": "factor_contributions.csv",
    "monte_carlo_convergence": "monte_carlo_convergence.csv",
    "monte_carlo_convergence_summary": "monte_carlo_convergence_summary.csv",
    "negative_hedging_contributions": "negative_hedging_contributions.csv",
    "position_history": "position_history.csv",
    "risk_contributions": "risk_contributions.csv",
    "rolling_forecasts": "rolling_forecasts.csv",
    "stress_detail": "stress_detail.csv",
    "stress_summary": "stress_summary.csv",
    "volatility_correlation_stress": "volatility_correlation_stress.csv",
}

DATE_COLUMNS = {
    "daily_portfolio_pnl": ("portfolio_date",),
    "position_history": ("portfolio_date",),
    "rolling_forecasts": (
        "forecast_date",
        "realized_date",
        "expected_next_date",
        "max_input_date",
    ),
}

REQUIRED_COLUMNS = {
    "current_risk": {"model", "confidence", "var", "es", "var_pct_nav", "es_pct_nav"},
    "daily_portfolio_pnl": {"portfolio_date", "nav", "gross_funded_exposure", "overlay_notional"},
    "risk_contributions": {"position_id", "component_var", "historical_es_contribution"},
    "rolling_forecasts": {"forecast_date", "realized_date", "model", "var", "es", "exception"},
    "stress_summary": {"scenario_name", "scenario_loss", "loss_pct_nav"},
}


class MarketRiskPlatform:
    """Run, validate, and load a complete analysis behind one compact interface."""

    def __init__(
        self,
        root: str | Path | None = None,
        model_config_path: str | Path | None = None,
    ) -> None:
        self.root = _resolve_root(root)
        self.model_config_path = Path(
            model_config_path or self.root / "config/model_config.yaml"
        ).resolve()

    def analyze(
        self,
        *,
        data_mode: str = "snapshot",
        refresh: bool = False,
        fred_api_key: str | None = None,
    ) -> MarketRiskAnalysis:
        """Return a validated result, regenerating artifacts only when requested."""

        if data_mode not in {"snapshot", "synthetic_demo", "live"}:
            raise ValueError(f"Unsupported data mode: {data_mode!r}")
        if refresh or data_mode == "live" or not self._artifacts_exist():
            from .engine import run_pipeline

            run_pipeline(self.model_config_path, data_mode, fred_api_key=fred_api_key)

        config = load_yaml(self.model_config_path)
        tables = self._load_tables()
        metadata = self._load_metadata(data_mode)
        headline = _build_headline(tables, config)
        artifacts = self._artifact_paths(headline.as_of_date)
        figures = {
            path.stem: path for path in sorted(artifacts.figures_directory.glob("*.png"))
        }
        if len(figures) < 8:
            raise ValueError(
                f"Analysis is incomplete: expected at least 8 figures, found {len(figures)}."
            )

        data_classification = str(metadata.get("data_classification", "LIVE OR EXTERNAL DATA"))
        return MarketRiskAnalysis(
            root=self.root,
            portfolio_name=str(config["portfolio_name"]),
            model_version=str(config["model_version"]),
            base_currency=str(config["base_currency"]),
            data_mode=data_mode,
            snapshot_id=str(metadata.get("snapshot_id", "not-recorded")),
            data_classification=data_classification,
            is_synthetic=data_classification == SYNTHETIC_WATERMARK,
            headline=headline,
            tables=tables,
            figures=figures,
            artifacts=artifacts,
        )

    def _artifacts_exist(self) -> bool:
        tables = self.root / "outputs/tables"
        return all((tables / filename).is_file() for filename in TABLE_FILES.values())

    def _load_tables(self) -> dict[str, pd.DataFrame]:
        directory = self.root / "outputs/tables"
        tables: dict[str, pd.DataFrame] = {}
        for name, filename in TABLE_FILES.items():
            path = directory / filename
            if not path.is_file():
                raise FileNotFoundError(f"Required analysis table is missing: {path}")
            frame = pd.read_csv(path)
            for column in DATE_COLUMNS.get(name, ()):
                if column in frame:
                    frame[column] = pd.to_datetime(frame[column], errors="raise")
            required = REQUIRED_COLUMNS.get(name, set())
            missing = required.difference(frame.columns)
            if missing:
                raise ValueError(f"{filename} is missing required columns: {sorted(missing)}")
            if frame.empty and name not in {"negative_hedging_contributions"}:
                raise ValueError(f"Required analysis table is empty: {path}")
            tables[name] = frame
        return tables

    def _load_metadata(self, data_mode: str) -> dict:
        if data_mode == "live":
            path = self.root / "data/processed/latest_live_metadata.json"
        else:
            path = self.root / "data/snapshots/synthetic_demo_metadata.json"
        if not path.is_file():
            raise FileNotFoundError(f"Data provenance metadata is missing: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _artifact_paths(self, as_of_date: str) -> ArtifactPaths:
        artifacts = ArtifactPaths(
            report=self.root / f"reports/generated/{as_of_date}_market_risk_report.md",
            summary=self.root / f"reports/generated/{as_of_date}_one_page_risk_summary.md",
            manifest=self.root / "outputs/verification_manifest.json",
            tables_directory=self.root / "outputs/tables",
            figures_directory=self.root / "outputs/figures",
        )
        for path in (artifacts.report, artifacts.summary, artifacts.manifest):
            if not path.is_file():
                raise FileNotFoundError(f"Required analysis artifact is missing: {path}")
        return artifacts


def _resolve_root(root: str | Path | None) -> Path:
    if root is not None:
        candidate = Path(root).resolve()
        if not (candidate / "config/model_config.yaml").is_file():
            raise FileNotFoundError(f"Not a market-risk project root: {candidate}")
        return candidate
    candidates = [Path.cwd().resolve(), project_root().resolve()]
    for candidate in candidates:
        if (candidate / "config/model_config.yaml").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate config/model_config.yaml. Run from the repository root or pass root=."
    )


def _build_headline(tables: dict[str, pd.DataFrame], config: dict) -> RiskHeadline:
    daily = tables["daily_portfolio_pnl"].sort_values("portfolio_date")
    current_risk = tables["current_risk"]
    contributions = tables["risk_contributions"]
    stresses = tables["stress_summary"]
    forecasts = tables["rolling_forecasts"]
    latest = daily.iloc[-1]

    primary_var_confidence = float(config["primary_var_confidence"])
    primary_es_confidence = float(config["primary_es_confidence"])
    primary_var = current_risk[current_risk["confidence"].round(6) == primary_var_confidence]
    primary_es = current_risk[current_risk["confidence"].round(6) == primary_es_confidence]
    if primary_var.empty or primary_es.empty:
        raise ValueError("Current-risk table does not contain the configured primary confidence levels.")

    top = contributions.loc[contributions["component_var"].idxmax()]
    worst = stresses.loc[stresses["scenario_loss"].idxmax()]
    return RiskHeadline(
        as_of_date=str(pd.Timestamp(latest["portfolio_date"]).date()),
        nav=float(latest["nav"]),
        gross_funded_exposure=float(latest["gross_funded_exposure"]),
        overlay_notional=float(latest["overlay_notional"]),
        primary_var_confidence=primary_var_confidence,
        primary_es_confidence=primary_es_confidence,
        var_low=float(primary_var["var"].min()),
        var_high=float(primary_var["var"].max()),
        es_low=float(primary_es["es"].min()),
        es_high=float(primary_es["es"].max()),
        top_risk_driver=str(top["position_id"]),
        top_component_var=float(top["component_var"]),
        worst_stress=str(worst["scenario_name"]),
        worst_stress_loss=float(worst["scenario_loss"]),
        worst_stress_pct_nav=float(worst["loss_pct_nav"]),
        forecast_count=int(forecasts["forecast_date"].nunique()),
        total_exceptions=int(forecasts["exception"].astype(bool).sum()),
    )

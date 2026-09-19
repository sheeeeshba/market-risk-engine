"""High-leverage interface for running and inspecting one market-risk analysis."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .analysis import CalculationProfile, calculate_portfolio_risk
from .config import configuration_hash, load_yaml, project_root
from .data_pipeline import SYNTHETIC_WATERMARK
from .models import ArtifactPaths, MarketRiskAnalysis, RiskHeadline
from .portfolio_builder import (
    InstrumentCatalog,
    PortfolioAllocation,
    PortfolioLibrary,
    load_instrument_catalog,
    load_portfolio_library,
    resolve_portfolio,
)

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
    "portfolio_allocation": "portfolio_allocation.csv",
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
        default_allocation = self.portfolio_library().allocation()
        return MarketRiskAnalysis(
            root=self.root,
            portfolio_name=default_allocation.portfolio_name,
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

    def portfolio_catalog(self) -> InstrumentCatalog:
        """Return the approved universe displayed by the portfolio builder."""

        return load_instrument_catalog(self.root / "config/instrument_catalog.yaml")

    def portfolio_library(self) -> PortfolioLibrary:
        """Return named starting allocations and portfolio-level controls."""

        return load_portfolio_library(self.root / "config/core_portfolio.yaml")

    def analyze_portfolio(
        self,
        allocation: PortfolioAllocation,
        *,
        data_mode: str = "snapshot",
        fred_api_key: str | None = None,
    ) -> MarketRiskAnalysis:
        """Recalculate all risk outputs for one user-edited portfolio."""

        if data_mode not in {"snapshot", "synthetic_demo", "live"}:
            raise ValueError(f"Unsupported data mode: {data_mode!r}")
        catalog = self.portfolio_catalog()
        portfolio_config = resolve_portfolio(catalog, allocation)
        model_config = load_yaml(self.model_config_path)
        stress_config = load_yaml(self.root / "config/stress_scenarios.yaml")
        crisis_config = load_yaml(self.root / "config/historical_crises.yaml")
        from .engine import load_factor_data

        factors, metadata = load_factor_data(
            self.root,
            data_mode,
            model_config,
            fred_api_key=fred_api_key,
        )
        profile = CalculationProfile.interactive(model_config)
        calculation = calculate_portfolio_risk(
            factors,
            portfolio_config,
            model_config,
            stress_config,
            crisis_config,
            profile=profile,
        )
        tables = calculation.public_tables()
        headline = _build_headline(tables, model_config)
        data_classification = str(metadata.get("data_classification", "LIVE OR EXTERNAL DATA"))
        allocation_hash = configuration_hash(allocation.as_dict())[:12]
        report_text, summary_text = _custom_narrative(
            allocation,
            headline,
            tables,
            data_classification,
            profile,
        )
        manifest = {
            "analysis_type": "interactive_custom_portfolio",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "allocation_hash": allocation_hash,
            "snapshot_id": metadata.get("snapshot_id", "not-recorded"),
            "calculation_profile": {
                "current_monte_carlo_paths": profile.current_paths,
                "rolling_monte_carlo_paths": profile.rolling_paths,
                "convergence_paths": profile.convergence_paths,
            },
            "gates": {
                "portfolio_validation": {
                    "exit_status": 0,
                    "utc_timestamp": datetime.now(timezone.utc).isoformat(),
                    "detail": "Funding identity, instrument mappings, and linked recalculation passed.",
                }
            },
        }
        return MarketRiskAnalysis(
            root=self.root,
            portfolio_name=allocation.portfolio_name,
            model_version=str(model_config["model_version"]),
            base_currency=allocation.base_currency,
            data_mode=data_mode,
            snapshot_id=f"{metadata.get('snapshot_id', 'not-recorded')} · {allocation_hash}",
            data_classification=data_classification,
            is_synthetic=data_classification == SYNTHETIC_WATERMARK,
            headline=headline,
            tables=tables,
            figures={},
            artifacts=None,
            generated_report_text=report_text,
            generated_summary_text=summary_text,
            generated_manifest=manifest,
            portfolio_definition=allocation.as_dict(),
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


def _custom_narrative(
    allocation: PortfolioAllocation,
    headline: RiskHeadline,
    tables: dict[str, pd.DataFrame],
    data_classification: str,
    profile: CalculationProfile,
) -> tuple[str, str]:
    """Create portable Markdown evidence for an in-memory custom calculation."""

    funded_count = sum(value > 0.0 for value in allocation.funded_weights.values())
    overlay_count = sum(value != 0.0 for value in allocation.overlay_fractions.values())
    summary_lines = [
        f"# Custom Portfolio Risk Summary — {headline.as_of_date}",
        "",
        f"> **{data_classification}.** Educational analysis; not investment advice.",
        "",
        f"- Portfolio: **{allocation.portfolio_name}**",
        f"- Active funded positions: **{funded_count}**; overlays: **{overlay_count}**; residual cash: **{allocation.residual_cash_weight:.1%}**",
        f"- Closing NAV: **USD {headline.nav:,.0f}**",
        f"- {headline.primary_var_confidence:.1%} VaR range: **USD {headline.var_low:,.0f}–USD {headline.var_high:,.0f}**",
        f"- {headline.primary_es_confidence:.1%} ES range: **USD {headline.es_low:,.0f}–USD {headline.es_high:,.0f}**",
        f"- Largest component-VaR driver: **{headline.top_risk_driver}** (USD {headline.top_component_var:,.0f})",
        f"- Worst configured stress: **{headline.worst_stress}** (USD {headline.worst_stress_loss:,.0f}; {headline.worst_stress_pct_nav:.1%} of NAV)",
        "",
        f"Interactive profile: {profile.current_paths:,} current Monte Carlo paths and {profile.rolling_paths:,} paths per rolling forecast.",
    ]
    allocation_table = tables["portfolio_allocation"]
    risk_table = tables["current_risk"]
    report_lines = [
        f"# Custom Market Risk Report — {headline.as_of_date}",
        "",
        *summary_lines[2:],
        "",
        "## Resolved allocation",
        "",
        allocation_table.to_markdown(index=False),
        "",
        "## Current VaR and Expected Shortfall",
        "",
        risk_table[["model", "confidence", "var", "es", "var_pct_nav", "es_pct_nav"]].to_markdown(index=False),
        "",
        "All portfolio history, backtesting, contributions, and stress tables are included in the downloadable ZIP bundle.",
    ]
    return "\n".join(report_lines) + "\n", "\n".join(summary_lines) + "\n"

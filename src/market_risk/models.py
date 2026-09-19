"""Typed public results returned by the market-risk platform interface."""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


@dataclass(frozen=True)
class ArtifactPaths:
    """Generated evidence locations for one completed analysis."""

    report: Path
    summary: Path
    manifest: Path
    tables_directory: Path
    figures_directory: Path


@dataclass(frozen=True)
class RiskHeadline:
    """Decision-relevant metrics used by the CLI and analyst dashboard."""

    as_of_date: str
    nav: float
    gross_funded_exposure: float
    overlay_notional: float
    primary_var_confidence: float
    primary_es_confidence: float
    var_low: float
    var_high: float
    es_low: float
    es_high: float
    top_risk_driver: str
    top_component_var: float
    worst_stress: str
    worst_stress_loss: float
    worst_stress_pct_nav: float
    forecast_count: int
    total_exceptions: int


@dataclass(frozen=True)
class MarketRiskAnalysis:
    """Complete, validated result exposed at the platform seam."""

    root: Path
    portfolio_name: str
    model_version: str
    base_currency: str
    data_mode: str
    snapshot_id: str
    data_classification: str
    is_synthetic: bool
    headline: RiskHeadline
    tables: dict[str, pd.DataFrame]
    figures: dict[str, Path]
    artifacts: ArtifactPaths | None
    generated_report_text: str | None = None
    generated_summary_text: str | None = None
    generated_manifest: dict | None = None
    portfolio_definition: dict | None = None

    def table(self, name: str) -> pd.DataFrame:
        """Return a defensive copy of one named evidence table."""

        try:
            return self.tables[name].copy()
        except KeyError as error:
            available = ", ".join(sorted(self.tables))
            raise KeyError(f"Unknown evidence table {name!r}. Available: {available}") from error

    @property
    def report_text(self) -> str:
        if self.generated_report_text is not None:
            return self.generated_report_text
        if self.artifacts is None:
            raise ValueError("This analysis has no generated report.")
        return self.artifacts.report.read_text(encoding="utf-8")

    @property
    def summary_text(self) -> str:
        if self.generated_summary_text is not None:
            return self.generated_summary_text
        if self.artifacts is None:
            raise ValueError("This analysis has no generated summary.")
        return self.artifacts.summary.read_text(encoding="utf-8")

    @property
    def verification_manifest(self) -> dict:
        if self.generated_manifest is not None:
            return dict(self.generated_manifest)
        if self.artifacts is None:
            raise ValueError("This analysis has no verification manifest.")
        return json.loads(self.artifacts.manifest.read_text(encoding="utf-8"))

    @property
    def report_filename(self) -> str:
        return self.artifacts.report.name if self.artifacts else "custom_market_risk_report.md"

    @property
    def summary_filename(self) -> str:
        return self.artifacts.summary.name if self.artifacts else "custom_risk_summary.md"

    @property
    def is_custom(self) -> bool:
        return self.artifacts is None

    def bundle_bytes(self) -> bytes:
        """Build an in-memory reviewer bundle without including secrets or caches."""

        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
            if self.artifacts is not None:
                paths = [
                    self.artifacts.report,
                    self.artifacts.summary,
                    self.artifacts.manifest,
                    *sorted(self.artifacts.tables_directory.glob("*.csv")),
                    *sorted(self.artifacts.tables_directory.glob("*.json")),
                    *sorted(self.artifacts.figures_directory.glob("*.png")),
                ]
                for path in paths:
                    if path.is_file():
                        archive.write(path, arcname=str(path.relative_to(self.root)))
            else:
                archive.writestr("reports/custom_market_risk_report.md", self.report_text)
                archive.writestr("reports/custom_risk_summary.md", self.summary_text)
                archive.writestr(
                    "outputs/verification_manifest.json",
                    json.dumps(self.verification_manifest, indent=2, default=str),
                )
                archive.writestr(
                    "config/portfolio_definition.json",
                    json.dumps(self.portfolio_definition or {}, indent=2, default=str),
                )
                for name, frame in sorted(self.tables.items()):
                    archive.writestr(f"outputs/tables/{name}.csv", frame.to_csv(index=False))
        return buffer.getvalue()

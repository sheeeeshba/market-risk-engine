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
    artifacts: ArtifactPaths

    def table(self, name: str) -> pd.DataFrame:
        """Return a defensive copy of one named evidence table."""

        try:
            return self.tables[name].copy()
        except KeyError as error:
            available = ", ".join(sorted(self.tables))
            raise KeyError(f"Unknown evidence table {name!r}. Available: {available}") from error

    @property
    def report_text(self) -> str:
        return self.artifacts.report.read_text(encoding="utf-8")

    @property
    def summary_text(self) -> str:
        return self.artifacts.summary.read_text(encoding="utf-8")

    @property
    def verification_manifest(self) -> dict:
        return json.loads(self.artifacts.manifest.read_text(encoding="utf-8"))

    def bundle_bytes(self) -> bytes:
        """Build an in-memory reviewer bundle without including secrets or caches."""

        buffer = BytesIO()
        paths = [
            self.artifacts.report,
            self.artifacts.summary,
            self.artifacts.manifest,
            *sorted(self.artifacts.tables_directory.glob("*.csv")),
            *sorted(self.artifacts.tables_directory.glob("*.json")),
            *sorted(self.artifacts.figures_directory.glob("*.png")),
        ]
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
            for path in paths:
                if path.is_file():
                    archive.write(path, arcname=str(path.relative_to(self.root)))
        return buffer.getvalue()

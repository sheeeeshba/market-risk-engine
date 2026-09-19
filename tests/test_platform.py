from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from market_risk.platform import MarketRiskPlatform

ROOT = Path(__file__).resolve().parents[1]


def test_platform_loads_complete_committed_analysis_without_regeneration() -> None:
    result = MarketRiskPlatform(ROOT).analyze(data_mode="snapshot", refresh=False)

    assert result.portfolio_name == (
        "Diversified Multi-Asset Demonstration Portfolio — Diversified Core"
    )
    assert result.is_synthetic is True
    assert result.headline.as_of_date == "2024-12-31"
    assert result.headline.nav > 0
    assert result.headline.var_high >= result.headline.var_low > 0
    assert result.headline.es_high >= result.headline.es_low > 0
    assert result.headline.forecast_count == 270
    assert len(result.figures) == 8


def test_platform_result_builds_secret_free_reviewer_bundle() -> None:
    result = MarketRiskPlatform(ROOT).analyze(refresh=False)

    with ZipFile(BytesIO(result.bundle_bytes())) as archive:
        names = set(archive.namelist())

    assert "outputs/verification_manifest.json" in names
    assert "outputs/tables/current_risk.csv" in names
    assert "outputs/figures/03_rolling_var_vs_realized_loss.png" in names
    assert all(".env" not in name and "secret" not in name.lower() for name in names)


def test_platform_custom_allocation_returns_linked_in_memory_bundle() -> None:
    platform = MarketRiskPlatform(ROOT)
    allocation = platform.portfolio_library().allocation().with_weights(
        {"SPY": 0.45, "GLD": 0.25, "US10Y": 0.20},
        {},
        portfolio_name="Three-asset test portfolio",
    )

    result = platform.analyze_portfolio(allocation)

    assert result.is_custom
    assert result.portfolio_name == "Three-asset test portfolio"
    assert set(result.table("portfolio_allocation")["position_id"]) == {
        "SPY",
        "GLD",
        "US10Y",
        "USD_CASH",
    }
    assert set(result.table("risk_contributions")["position_id"]) == {
        "SPY",
        "GLD",
        "US10Y",
        "USD_CASH",
    }
    with ZipFile(BytesIO(result.bundle_bytes())) as archive:
        names = set(archive.namelist())
    assert "config/portfolio_definition.json" in names
    assert "outputs/tables/current_risk.csv" in names


def test_platform_rejects_a_non_project_root(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Not a market-risk project root"):
        MarketRiskPlatform(tmp_path)

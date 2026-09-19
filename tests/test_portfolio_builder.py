from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from market_risk.data_pipeline import FACTOR_COLUMNS
from market_risk.portfolio_builder import load_default_portfolio, resolve_portfolio

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_covers_stocks_bonds_metals_commodities_and_every_factor() -> None:
    catalog, _, _, _ = load_default_portfolio(ROOT)
    frame = catalog.frame()

    assert len(frame) == 26
    assert {"equity", "etf", "bond", "cash", "fx_forward"}.issubset(
        set(frame["instrument_type"])
    )
    assert {"Precious Metals", "Commodities", "Government Bonds"}.issubset(
        set(frame["asset_class"])
    )
    catalog_factors = set(frame.loc[frame["instrument_type"] != "cash", "factor"])
    assert catalog_factors == set(FACTOR_COLUMNS)


def test_default_preset_resolves_residual_cash_and_funding_identity() -> None:
    _, _, allocation, resolved = load_default_portfolio(ROOT)
    positions = {position["position_id"]: position for position in resolved["positions"]}

    assert np.isclose(allocation.invested_weight, 0.93)
    assert np.isclose(positions["USD_CASH"]["target_weight"], 0.07)
    assert np.isclose(
        sum(
            position["target_weight"]
            for position in resolved["positions"]
            if position["instrument_type"] != "fx_forward"
        ),
        1.0,
    )


def test_add_remove_and_reweight_changes_resolved_positions_and_values() -> None:
    catalog, library, _, _ = load_default_portfolio(ROOT)
    base = library.allocation("defensive")
    custom = base.with_weights(
        {"NVDA": 0.20, "GLD": 0.15, "US10Y": 0.35},
        {},
        portfolio_name="Test custom portfolio",
    )
    resolved = resolve_portfolio(catalog, custom)
    positions = {position["position_id"]: position for position in resolved["positions"]}

    assert set(positions) == {"NVDA", "GLD", "US10Y", "USD_CASH"}
    assert positions["NVDA"]["instrument_type"] == "equity"
    assert positions["NVDA"]["initial_market_value"] == 2_000_000.0
    assert np.isclose(positions["USD_CASH"]["initial_market_value"], 3_000_000.0)


def test_invalid_or_empty_allocations_fail_before_risk_calculation() -> None:
    catalog, library, _, _ = load_default_portfolio(ROOT)
    base = library.allocation()

    with pytest.raises(ValueError, match="cannot exceed 100%"):
        resolve_portfolio(catalog, base.with_weights({"SPY": 0.8, "GLD": 0.4}, {}))
    with pytest.raises(ValueError, match="at least one"):
        resolve_portfolio(catalog, base.with_weights({}, {}))
    with pytest.raises(ValueError, match="Unknown funded instrument"):
        resolve_portfolio(catalog, base.with_weights({"FAKE": 0.5}, {}))

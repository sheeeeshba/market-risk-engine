from __future__ import annotations

import numpy as np
import pandas as pd

from market_risk.data_pipeline import FACTOR_COLUMNS, build_common_calendar, generate_synthetic_demo


def test_synthetic_demo_is_deterministic_and_watermarked() -> None:
    first, first_meta = generate_synthetic_demo(periods=300, seed=42)
    second, second_meta = generate_synthetic_demo(periods=300, seed=42)

    pd.testing.assert_frame_equal(first, second)
    assert list(first.columns) == FACTOR_COLUMNS
    assert first_meta["data_classification"] == "SYNTHETIC DATA — NOT FOR RESUME RESULTS"
    assert first_meta == second_meta
    assert np.isfinite(first.to_numpy()).all()


def test_common_calendar_never_fills_etf_or_fx_and_flags_rate_fill() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    levels = {
        "SPY": pd.Series([100.0, 101.0, np.nan, 103.0], index=dates),
        "QQQ": pd.Series([200.0, 202.0, 204.0, 206.0], index=dates),
        "EFA": pd.Series([70.0, 70.5, 71.0, 71.5], index=dates),
        "GLD": pd.Series([180.0, 181.0, 182.0, 183.0], index=dates),
        "EURUSD": pd.Series([1.10, 1.11, 1.12, 1.13], index=dates),
        "DGS5": pd.Series([0.040, np.nan, 0.042, 0.043], index=dates),
        "DGS10": pd.Series([0.045, 0.046, 0.047, 0.048], index=dates),
    }

    factors, quality = build_common_calendar(levels, max_rate_fill_business_days=3)

    # 2024-01-04 is excluded because SPY is missing. Rate level on 2024-01-03 is filled,
    # then returns/changes are calculated only between surviving dates.
    assert list(factors.index) == [pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-05")]
    assert factors.loc["2024-01-03", "DGS5_CHANGE"] == 0.0
    assert quality.loc["2024-01-03", "DGS5_was_filled"]
    assert quality.loc["2024-01-05", "interval_civil_days"] == 2


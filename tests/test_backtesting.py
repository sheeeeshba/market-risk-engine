from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from market_risk.backtesting import (
    christoffersen_tests,
    kupiec_test,
    validate_forecast_alignment,
)


def test_kupiec_handles_no_and_all_breaches_without_crashing() -> None:
    no_breaches = kupiec_test([False] * 100, confidence=0.99)
    all_breaches = kupiec_test([True] * 100, confidence=0.99)

    assert no_breaches["exceptions"] == 0
    assert all_breaches["exceptions"] == 100
    assert math.isfinite(no_breaches["lr_uc"])
    assert math.isfinite(all_breaches["lr_uc"])
    assert 0.0 <= no_breaches["p_value_uc"] <= 1.0


def test_christoffersen_detects_clustered_transitions_and_missing_rows() -> None:
    clustered = christoffersen_tests([False] * 20 + [True] * 8 + [False] * 20)
    assert clustered["status"] == "OK"
    assert clustered["n11"] == 7
    assert clustered["lr_ind"] > 0.0

    missing_row = christoffersen_tests([False] * 20)
    assert missing_row["status"] == "INSUFFICIENT_TRANSITIONS"
    assert math.isnan(missing_row["lr_ind"])


def test_alignment_validator_catches_intentional_one_day_error() -> None:
    valid = pd.DataFrame(
        {
            "forecast_date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "realized_date": pd.to_datetime(["2024-01-03", "2024-01-04"]),
            "expected_next_date": pd.to_datetime(["2024-01-03", "2024-01-04"]),
            "max_input_date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        }
    )
    validate_forecast_alignment(valid)

    invalid = valid.copy()
    invalid.loc[0, "realized_date"] = pd.Timestamp("2024-01-04")
    with pytest.raises(ValueError, match="next valid portfolio date"):
        validate_forecast_alignment(invalid)


def test_versioned_independent_breach_fixture_matches_expected_rate() -> None:
    fixture_path = Path(__file__).parent / "fixtures/backtesting_cases.yaml"
    case = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))["independent_approximate_rate"]
    flags = [index in set(case["breach_indices"]) for index in range(case["length"])]
    result = kupiec_test(flags, confidence=0.99)
    assert result["exceptions"] == 5
    assert np.isclose(result["observed_exception_rate"], result["expected_exception_rate"])

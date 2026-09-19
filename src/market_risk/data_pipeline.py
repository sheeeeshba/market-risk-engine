"""Reproducible market-data adapters and common-calendar construction."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

RETURN_LEVEL_MAP = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM",
    "EFA": "EFA",
    "EEM": "EEM",
    "VNQ": "VNQ",
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "NVDA": "NVDA",
    "JPM": "JPM",
    "JNJ": "JNJ",
    "XOM": "XOM",
    "LQD": "LQD",
    "HYG": "HYG",
    "TIP": "TIP",
    "GLD": "GLD",
    "SLV": "SLV",
    "PPLT": "PPLT",
    "DBC": "DBC",
    "USO": "USO",
    "EURUSD": "EURUSD=X",
}
RATE_LEVELS = ("DGS2", "DGS5", "DGS10", "DGS30")
FACTOR_COLUMNS = [
    *(f"{name}_RETURN" for name in RETURN_LEVEL_MAP if name != "EURUSD"),
    *(f"{name}_CHANGE" for name in RATE_LEVELS),
    "EURUSD_RETURN",
]
LEVEL_COLUMNS = [*RETURN_LEVEL_MAP, *RATE_LEVELS]
SYNTHETIC_WATERMARK = "SYNTHETIC DATA — NOT FOR RESUME RESULTS"


def _frame_hash(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=True, float_format="%.12g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_synthetic_demo(
    periods: int = 1_000,
    seed: int = 42,
    end_date: str = "2024-12-31",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create deterministic, economically plausible artificial factor shocks.

    The series is deliberately not calibrated to or presented as historical market
    data. It exists to verify formulas, engineering, charts, and report structure.
    """

    if periods < 2:
        raise ValueError("Synthetic demo requires at least two factor observations.")
    rng = np.random.default_rng(seed)

    # Independent latent shocks: global risk, technology, small caps, international
    # equities, rates, credit, inflation/real assets, precious metals, oil, and FX.
    latent = rng.standard_normal((periods, 10))
    regime_scale = np.where(rng.random(periods) < 0.04, 2.75, 1.0)
    latent *= regime_scale[:, None]
    idiosyncratic = rng.standard_normal((periods, len(FACTOR_COLUMNS)))

    # Daily loadings produce decimal returns and decimal-yield changes.  The fixture
    # is designed for diversified engineering tests, not historical calibration.
    loading_rows = {
        "SPY_RETURN": [0.0080, 0.0015, 0.0010, 0.0005, -0.0004, 0.0005, 0.0003, 0.0, 0.0, 0.0],
        "QQQ_RETURN": [0.0075, 0.0060, 0.0003, 0.0003, -0.0007, 0.0003, 0.0, 0.0, 0.0, 0.0],
        "IWM_RETURN": [0.0080, 0.0005, 0.0055, 0.0005, -0.0008, 0.0015, 0.0005, 0.0, 0.0, 0.0],
        "EFA_RETURN": [0.0060, 0.0, 0.0005, 0.0050, -0.0003, 0.0005, 0.0004, 0.0, 0.0, 0.0020],
        "EEM_RETURN": [0.0065, 0.0, 0.0010, 0.0065, -0.0005, 0.0010, 0.0015, 0.0, 0.0, 0.0025],
        "VNQ_RETURN": [0.0050, 0.0, 0.0010, 0.0005, -0.0025, 0.0010, 0.0025, 0.0, 0.0, 0.0],
        "AAPL_RETURN": [0.0070, 0.0065, 0.0, 0.0, -0.0005, 0.0, 0.0, 0.0, 0.0, 0.0],
        "MSFT_RETURN": [0.0068, 0.0058, 0.0, 0.0, -0.0004, 0.0, 0.0, 0.0, 0.0, 0.0],
        "NVDA_RETURN": [0.0080, 0.0100, 0.0, 0.0, -0.0007, 0.0, 0.0, 0.0, 0.0, 0.0],
        "JPM_RETURN": [0.0075, -0.0005, 0.0015, 0.0, 0.0015, 0.0020, 0.0, 0.0, 0.0, 0.0],
        "JNJ_RETURN": [0.0045, -0.0010, -0.0005, 0.0, -0.0002, -0.0003, 0.0, 0.0, 0.0, 0.0],
        "XOM_RETURN": [0.0055, -0.0005, 0.0005, 0.0, 0.0003, 0.0005, 0.0025, 0.0, 0.0045, 0.0],
        "LQD_RETURN": [0.0010, 0.0, 0.0, 0.0, -0.0032, 0.0020, 0.0002, 0.0, 0.0, 0.0],
        "HYG_RETURN": [0.0040, 0.0, 0.0008, 0.0, -0.0012, 0.0040, 0.0005, 0.0, 0.0, 0.0],
        "TIP_RETURN": [0.0010, 0.0, 0.0, 0.0, -0.0022, 0.0005, 0.0035, 0.0, 0.0, 0.0],
        "GLD_RETURN": [-0.0008, 0.0, 0.0, 0.0, -0.0010, 0.0, 0.0010, 0.0065, 0.0, 0.0010],
        "SLV_RETURN": [0.0010, 0.0, 0.0005, 0.0, -0.0010, 0.0, 0.0015, 0.0085, 0.0, 0.0010],
        "PPLT_RETURN": [0.0020, 0.0, 0.0005, 0.0010, -0.0007, 0.0, 0.0020, 0.0070, 0.0010, 0.0005],
        "DBC_RETURN": [0.0010, 0.0, 0.0005, 0.0010, 0.0003, 0.0, 0.0050, 0.0010, 0.0040, 0.0],
        "USO_RETURN": [0.0020, 0.0, 0.0010, 0.0005, 0.0003, 0.0, 0.0025, 0.0, 0.0110, 0.0],
        "DGS2_CHANGE": [-0.00003, 0.0, 0.0, 0.0, 0.00030, -0.00002, 0.00008, 0.0, 0.0, 0.0],
        "DGS5_CHANGE": [-0.00004, 0.0, 0.0, 0.0, 0.00036, -0.00002, 0.00009, 0.0, 0.0, 0.0],
        "DGS10_CHANGE": [-0.00004, 0.0, 0.0, 0.0, 0.00042, -0.00001, 0.00010, 0.0, 0.0, 0.0],
        "DGS30_CHANGE": [-0.00004, 0.0, 0.0, 0.0, 0.00048, 0.0, 0.00012, 0.0, 0.0, 0.0],
        "EURUSD_RETURN": [0.0010, -0.0005, 0.0, 0.0015, -0.0002, 0.0, 0.0, 0.0, 0.0, 0.0045],
    }
    loadings = np.array([loading_rows[column] for column in FACTOR_COLUMNS])
    idio_vol_by_factor = {
        "SPY_RETURN": 0.0035,
        "QQQ_RETURN": 0.0040,
        "IWM_RETURN": 0.0045,
        "EFA_RETURN": 0.0040,
        "EEM_RETURN": 0.0055,
        "VNQ_RETURN": 0.0045,
        "AAPL_RETURN": 0.0060,
        "MSFT_RETURN": 0.0050,
        "NVDA_RETURN": 0.0100,
        "JPM_RETURN": 0.0060,
        "JNJ_RETURN": 0.0045,
        "XOM_RETURN": 0.0060,
        "LQD_RETURN": 0.0015,
        "HYG_RETURN": 0.0025,
        "TIP_RETURN": 0.0018,
        "GLD_RETURN": 0.0040,
        "SLV_RETURN": 0.0065,
        "PPLT_RETURN": 0.0060,
        "DBC_RETURN": 0.0035,
        "USO_RETURN": 0.0090,
        "DGS2_CHANGE": 0.00012,
        "DGS5_CHANGE": 0.00015,
        "DGS10_CHANGE": 0.00017,
        "DGS30_CHANGE": 0.00020,
        "EURUSD_RETURN": 0.0025,
    }
    idio_vol = np.array([idio_vol_by_factor[column] for column in FACTOR_COLUMNS])
    values = latent @ loadings.T + idiosyncratic * idio_vol
    return_indices = [index for index, column in enumerate(FACTOR_COLUMNS) if column.endswith("_RETURN")]
    values[:, return_indices] = np.clip(values[:, return_indices], -0.30, 0.30)
    values[:, FACTOR_COLUMNS.index("EURUSD_RETURN")] = np.clip(
        values[:, FACTOR_COLUMNS.index("EURUSD_RETURN")], -0.12, 0.12
    )

    index = pd.bdate_range(end=pd.Timestamp(end_date), periods=periods, name="portfolio_date")
    frame = pd.DataFrame(values, index=index, columns=FACTOR_COLUMNS)
    metadata = {
        "snapshot_id": f"synthetic_demo_seed{seed}_n{periods}_end{end_date}",
        "data_classification": SYNTHETIC_WATERMARK,
        "source": "Deterministic artificial latent-factor generator",
        "seed": seed,
        "periods": periods,
        "as_of_date": str(index[-1].date()),
        "factor_hash": _frame_hash(frame),
    }
    return frame, metadata


def _normalise_series(series: pd.Series, name: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    index = pd.to_datetime(values.index, utc=True).tz_convert(None).normalize()
    normalised = pd.Series(values.to_numpy(dtype=float), index=index, name=name)
    # Later retrieval wins when a provider returns duplicate dates.
    return normalised.groupby(level=0, sort=True).last()


def _rate_fill_on_calendar(
    raw: pd.Series,
    candidate: pd.DatetimeIndex,
    max_business_days: int,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    observed = raw.dropna().sort_index()
    result = raw.reindex(candidate)
    was_filled = pd.Series(False, index=candidate, dtype=bool)
    age = pd.Series(0.0, index=candidate, dtype=float)

    for date in candidate[result.isna()]:
        prior = observed.loc[observed.index < date]
        if prior.empty:
            continue
        prior_date = prior.index[-1]
        business_age = int(np.busday_count(prior_date.date(), date.date()))
        if business_age <= max_business_days:
            result.loc[date] = float(prior.iloc[-1])
            was_filled.loc[date] = True
            age.loc[date] = float(business_age)
    return result, was_filled, age


def build_common_calendar(
    raw_levels: Mapping[str, pd.Series],
    max_rate_fill_business_days: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Align raw levels and calculate factors without masking missing risk.

    Market-price and EURUSD levels define the candidate calendar and are never filled.
    Treasury levels alone may be carried forward for a limited documented age.
    """

    missing = sorted(set(LEVEL_COLUMNS) - set(raw_levels))
    if missing:
        raise ValueError(f"Missing required raw level series: {', '.join(missing)}")
    if max_rate_fill_business_days < 0:
        raise ValueError("Maximum rate fill age cannot be negative.")

    normalised = {name: _normalise_series(raw_levels[name], name) for name in LEVEL_COLUMNS}
    non_rate = pd.concat(
        [normalised[name] for name in RETURN_LEVEL_MAP], axis=1, join="outer"
    )
    candidate = pd.DatetimeIndex(non_rate.dropna(how="any").index).sort_values()
    aligned = non_rate.reindex(candidate)
    quality = pd.DataFrame(index=candidate)

    for rate in RATE_LEVELS:
        filled, flags, ages = _rate_fill_on_calendar(
            normalised[rate], candidate, max_rate_fill_business_days
        )
        aligned[rate] = filled
        quality[f"{rate}_was_filled"] = flags
        quality[f"{rate}_fill_age_business_days"] = ages

    aligned = aligned.dropna(subset=LEVEL_COLUMNS)
    quality = quality.reindex(aligned.index)

    factors = pd.DataFrame(index=aligned.index)
    for ticker in RETURN_LEVEL_MAP:
        factors[f"{ticker}_RETURN"] = aligned[ticker].pct_change(fill_method=None)
    for rate in RATE_LEVELS:
        factors[f"{rate}_CHANGE"] = aligned[rate].diff()
    factors = factors[FACTOR_COLUMNS].iloc[1:]
    factors.index.name = "portfolio_date"

    quality = quality.iloc[1:].copy()
    quality["interval_civil_days"] = aligned.index.to_series().diff().dt.days.iloc[1:].to_numpy()
    quality["has_multi_civil_day_interval"] = quality["interval_civil_days"] > 1
    quality.index.name = "portfolio_date"
    if factors.isna().any().any():
        raise ValueError("Common-calendar construction left missing factor shocks.")
    return factors, quality


def save_snapshot(
    factors: pd.DataFrame,
    metadata: Mapping[str, Any],
    factors_path: str,
    metadata_path: str,
) -> None:
    """Persist a processed snapshot and its provenance metadata."""

    import json
    from pathlib import Path

    factor_target = Path(factors_path)
    metadata_target = Path(metadata_path)
    factor_target.parent.mkdir(parents=True, exist_ok=True)
    metadata_target.parent.mkdir(parents=True, exist_ok=True)
    factors.to_csv(factor_target, index_label="portfolio_date")
    metadata_target.write_text(json.dumps(dict(metadata), indent=2), encoding="utf-8")


def load_snapshot(factors_path: str) -> pd.DataFrame:
    """Load and validate a processed factor snapshot."""

    factors = pd.read_csv(factors_path, parse_dates=["portfolio_date"], index_col="portfolio_date")
    if list(factors.columns) != FACTOR_COLUMNS:
        raise ValueError(f"Snapshot factors must be ordered as: {FACTOR_COLUMNS}")
    if factors.isna().any().any():
        raise ValueError("Snapshot contains missing factor shocks; missing risk cannot become zero.")
    factors.index.name = "portfolio_date"
    return factors.astype(float)


def download_live_factors(
    start_date: str = "2007-01-01",
    end_date: str | None = None,
    fred_api_key: str | None = None,
    max_rate_fill_business_days: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Download optional live ETF/FX levels from Yahoo and Treasury yields from FRED.

    Yahoo is requested with ``auto_adjust=False`` and the explicit ``Adj Close``
    field. FRED percent yields are divided by 100 before calendar alignment.
    The Yahoo ``end`` argument is exclusive, so one day is added to the requested
    inclusive end date.
    """

    try:
        import yfinance as yf
    except ImportError as error:
        raise RuntimeError(
            "Live mode requires the optional dependency: install with `pip install '.[live]'`."
        ) from error
    api_key = fred_api_key or os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Live mode requires FRED_API_KEY in the environment or Colab Secrets. "
            "Create a free key at the official FRED API site."
        )

    inclusive_end = pd.Timestamp(end_date or datetime.now(timezone.utc).date()).normalize()
    yahoo_exclusive_end = str((inclusive_end + timedelta(days=1)).date())
    ticker_map = RETURN_LEVEL_MAP
    downloaded = yf.download(
        list(ticker_map.values()),
        start=start_date,
        end=yahoo_exclusive_end,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=True,
        group_by="column",
        multi_level_index=True,
    )
    if downloaded is None or downloaded.empty:
        raise RuntimeError("Yahoo download returned no rows; check connectivity and requested dates.")
    raw_levels: dict[str, pd.Series] = {}
    for canonical_name, ticker in ticker_map.items():
        try:
            series = downloaded[("Adj Close", ticker)]
        except KeyError as error:
            raise RuntimeError(
                f"Yahoo response has no explicit Adj Close field for {ticker}; refusing to guess a price field."
            ) from error
        raw_levels[canonical_name] = series.rename(canonical_name)

    for series_id in RATE_LEVELS:
        parameters = urllib.parse.urlencode(
            {
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start_date,
                "observation_end": str(inclusive_end.date()),
                "sort_order": "asc",
            }
        )
        request = urllib.request.Request(
            f"https://api.stlouisfed.org/fred/series/observations?{parameters}",
            headers={"User-Agent": "multi-asset-market-risk-engine/1.1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            raise RuntimeError(f"FRED download failed for {series_id}: {error}") from error
        observations = payload.get("observations", [])
        values = {
            item["date"]: np.nan if item["value"] == "." else float(item["value"]) / 100.0
            for item in observations
        }
        raw_levels[series_id] = pd.Series(values, dtype=float, name=series_id)

    factors, quality = build_common_calendar(
        raw_levels, max_rate_fill_business_days=max_rate_fill_business_days
    )
    retrieved_utc = datetime.now(timezone.utc).isoformat()
    metadata = {
        "snapshot_id": f"live_common_calendar_asof_{factors.index[-1].date()}",
        "data_classification": "LIVE PROVIDER DATA — REVIEW REDISTRIBUTION TERMS",
        "source": "Yahoo Finance Adj Close via yfinance; FRED DGS2, DGS5, DGS10, and DGS30",
        "price_field": "Adj Close",
        "yfinance_auto_adjust": False,
        "fx_quote": "EURUSD = USD per EUR",
        "fred_input_unit": "percent yield",
        "stored_rate_unit": "decimal yield",
        "retrieved_utc": retrieved_utc,
        "as_of_date": str(factors.index[-1].date()),
        "factor_hash": _frame_hash(factors),
    }
    return factors, quality, metadata

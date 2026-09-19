"""Funded-portfolio and zero-funded-value overlay accounting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .pnl import bond_pnl, etf_pnl, fx_pnl
from .validation import validate_factor_frame, validate_portfolio_config


@dataclass(frozen=True)
class PortfolioHistory:
    """Observable result of the portfolio accounting module."""

    daily: pd.DataFrame
    positions: pd.DataFrame
    ending_snapshot: pd.DataFrame


def initial_position_snapshot(config: Mapping[str, Any]) -> pd.DataFrame:
    """Return the prior-close position state used by the first factor interval."""

    validate_portfolio_config(config)
    rows: list[dict[str, Any]] = []
    for position in config["positions"]:
        rows.append(
            {
                "position_id": position["position_id"],
                "name": position["name"],
                "instrument_type": position["instrument_type"],
                "asset_class": position["asset_class"],
                "factor": position["factor"],
                "market_value": float(position.get("initial_market_value", 0.0)),
                "notional": float(position.get("initial_notional", 0.0)),
                "target_weight": position.get("target_weight"),
                "target_notional_fraction_of_nav": position.get(
                    "target_notional_fraction_of_nav"
                ),
                "modified_duration": float(position.get("modified_duration", 0.0)),
                "convexity": float(position.get("convexity", 0.0)),
                "holdings_version": 0,
            }
        )
    return pd.DataFrame(rows).set_index("position_id")


def _required_factors(snapshot: pd.DataFrame) -> list[str]:
    return sorted(set(snapshot.loc[snapshot["instrument_type"] != "cash", "factor"]))


def run_portfolio_history(
    factors: pd.DataFrame,
    config: Mapping[str, Any],
    reconciliation_tolerance_usd: float = 0.01,
) -> PortfolioHistory:
    """Apply shocks, settle P&L, reconcile NAV, and rebalance monthly.

    Rebalancing occurs after the first available close in every calendar month and
    therefore changes holdings only for the following valid interval.
    """

    snapshot = initial_position_snapshot(config).copy()
    validate_factor_frame(factors, _required_factors(snapshot))
    previous_nav = float(snapshot.loc[snapshot["instrument_type"] != "fx_forward", "market_value"].sum())
    previous_date: pd.Timestamp | None = None
    version = 0
    daily_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []

    for date, shocks in factors.iterrows():
        start = snapshot.copy()
        pnl_by_position: dict[str, float] = {}
        for position_id, position in start.iterrows():
            instrument = position["instrument_type"]
            if instrument in {"equity", "etf"}:
                pnl = etf_pnl(position["market_value"], shocks[position["factor"]])
            elif instrument == "bond":
                pnl = bond_pnl(
                    position["market_value"],
                    position["modified_duration"],
                    position["convexity"],
                    shocks[position["factor"]],
                )
            elif instrument == "fx_forward":
                pnl = fx_pnl(position["notional"], shocks[position["factor"]])
            elif instrument == "cash":
                pnl = 0.0
            else:  # protected by configuration validation
                raise ValueError(f"Unsupported instrument type: {instrument}")
            pnl_by_position[position_id] = float(pnl)

        pretrade = start.copy()
        for position_id, position in start.iterrows():
            if position["instrument_type"] in {"equity", "etf", "bond"}:
                pretrade.loc[position_id, "market_value"] += pnl_by_position[position_id]
        cash_ids = start.index[start["instrument_type"] == "cash"].tolist()
        if len(cash_ids) != 1:
            raise ValueError("Core accounting requires exactly one cash position.")
        overlay_pnl = sum(
            pnl_by_position[position_id]
            for position_id in start.index[start["instrument_type"] == "fx_forward"]
        )
        pretrade.loc[cash_ids[0], "market_value"] += overlay_pnl

        funded_mask = pretrade["instrument_type"] != "fx_forward"
        nav = float(pretrade.loc[funded_mask, "market_value"].sum())
        portfolio_pnl = float(sum(pnl_by_position.values()))
        tolerance = max(reconciliation_tolerance_usd, 1e-10 * float(start["market_value"].abs().sum()))
        if not np.isclose(nav, previous_nav + portfolio_pnl, atol=tolerance, rtol=0.0):
            raise ValueError(
                f"NAV reconciliation failed on {date.date()}: NAV={nav:.6f}, "
                f"prior NAV + P&L={previous_nav + portfolio_pnl:.6f}."
            )

        rebalanced = previous_date is None or (date.year, date.month) != (
            previous_date.year,
            previous_date.month,
        )
        end = pretrade.copy()
        if rebalanced:
            version += 1
            for position_id, position in end.iterrows():
                if position["instrument_type"] != "fx_forward":
                    end.loc[position_id, "market_value"] = nav * float(position["target_weight"])
                else:
                    end.loc[position_id, "notional"] = nav * float(
                        position["target_notional_fraction_of_nav"]
                    )
                end.loc[position_id, "holdings_version"] = version

        funded_end = float(end.loc[end["instrument_type"] != "fx_forward", "market_value"].sum())
        if not np.isclose(funded_end, nav, atol=tolerance, rtol=0.0):
            raise ValueError(f"Funded holdings do not reconcile to NAV on {date.date()}.")

        for position_id in start.index:
            position_rows.append(
                {
                    "portfolio_date": date,
                    "position_id": position_id,
                    "name": start.loc[position_id, "name"],
                    "instrument_type": start.loc[position_id, "instrument_type"],
                    "asset_class": start.loc[position_id, "asset_class"],
                    "factor": start.loc[position_id, "factor"],
                    "target_weight": start.loc[position_id, "target_weight"],
                    "target_notional_fraction_of_nav": start.loc[
                        position_id, "target_notional_fraction_of_nav"
                    ],
                    "start_market_value": float(start.loc[position_id, "market_value"]),
                    "start_notional": float(start.loc[position_id, "notional"]),
                    "position_pnl": pnl_by_position[position_id],
                    "pretrade_market_value": float(pretrade.loc[position_id, "market_value"]),
                    "end_market_value": float(end.loc[position_id, "market_value"]),
                    "end_notional": float(end.loc[position_id, "notional"]),
                    "modified_duration": float(end.loc[position_id, "modified_duration"]),
                    "convexity": float(end.loc[position_id, "convexity"]),
                    "holdings_version": int(end.loc[position_id, "holdings_version"]),
                    "rebalanced": bool(rebalanced),
                }
            )
        daily_rows.append(
            {
                "portfolio_date": date,
                "portfolio_pnl": portfolio_pnl,
                "portfolio_loss": -portfolio_pnl,
                "position_pnl_sum": float(sum(pnl_by_position.values())),
                "nav": nav,
                "funded_market_value": funded_end,
                "gross_funded_exposure": float(
                    end.loc[end["instrument_type"] != "fx_forward", "market_value"].abs().sum()
                ),
                "overlay_notional": float(
                    end.loc[end["instrument_type"] == "fx_forward", "notional"].abs().sum()
                ),
                "rebalanced": bool(rebalanced),
                "holdings_version": version,
            }
        )
        snapshot = end
        previous_nav = nav
        previous_date = date

    daily = pd.DataFrame(daily_rows).set_index("portfolio_date")
    positions = pd.DataFrame(position_rows).set_index(["portfolio_date", "position_id"])
    return PortfolioHistory(daily=daily, positions=positions, ending_snapshot=snapshot)


def position_snapshot_on(history: PortfolioHistory, date: pd.Timestamp) -> pd.DataFrame:
    """Return end-of-date holdings in the canonical snapshot shape."""

    rows = history.positions.xs(pd.Timestamp(date)).copy()
    snapshot = rows[["instrument_type", "asset_class", "factor", "end_market_value", "end_notional", "modified_duration", "convexity", "holdings_version"]]
    return snapshot.rename(columns={"end_market_value": "market_value", "end_notional": "notional"})

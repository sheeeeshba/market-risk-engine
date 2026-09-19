"""Validated portfolio-catalog and allocation interface.

The dashboard edits a compact :class:`PortfolioAllocation`.  This module is the
single seam that turns that user input into the fully specified position format
consumed by accounting, VaR, backtesting, contributions, and stress testing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import load_yaml
from .validation import SUPPORTED_INSTRUMENTS, validate_portfolio_config


@dataclass(frozen=True)
class InstrumentSpec:
    """One approved instrument and its canonical risk-factor mapping."""

    instrument_id: str
    name: str
    instrument_type: str
    asset_class: str
    factor: str
    provider_symbol: str | None = None
    modified_duration: float | None = None
    convexity: float | None = None
    quote_convention: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> InstrumentSpec:
        instrument_id = str(value.get("instrument_id", "")).strip()
        name = str(value.get("name", "")).strip()
        instrument_type = str(value.get("instrument_type", "")).strip()
        asset_class = str(value.get("asset_class", "")).strip()
        factor = str(value.get("factor", "")).strip()
        if not all((instrument_id, name, instrument_type, asset_class, factor)):
            raise ValueError("Every catalog instrument requires id, name, type, asset class, and factor.")
        if instrument_type not in SUPPORTED_INSTRUMENTS:
            raise ValueError(
                f"Unsupported catalog instrument type for {instrument_id}: {instrument_type!r}"
            )
        duration = value.get("modified_duration")
        convexity = value.get("convexity")
        quote_convention = value.get("quote_convention")
        if instrument_type == "bond" and (duration is None or convexity is None):
            raise ValueError(f"Catalog bond {instrument_id} requires duration and convexity.")
        if instrument_type == "fx_forward" and not quote_convention:
            raise ValueError(f"Catalog FX overlay {instrument_id} requires a quote convention.")
        return cls(
            instrument_id=instrument_id,
            name=name,
            instrument_type=instrument_type,
            asset_class=asset_class,
            factor=factor,
            provider_symbol=(
                str(value["provider_symbol"]) if value.get("provider_symbol") is not None else None
            ),
            modified_duration=float(duration) if duration is not None else None,
            convexity=float(convexity) if convexity is not None else None,
            quote_convention=str(quote_convention) if quote_convention is not None else None,
        )

    @property
    def is_funded(self) -> bool:
        return self.instrument_type != "fx_forward"

    @property
    def is_selectable_funded(self) -> bool:
        return self.instrument_type not in {"cash", "fx_forward"}


@dataclass(frozen=True)
class InstrumentCatalog:
    """Immutable approved universe used by both the UI and calculation engine."""

    version: str
    base_currency: str
    instruments: tuple[InstrumentSpec, ...]

    def __post_init__(self) -> None:
        if not self.version or not self.base_currency:
            raise ValueError("Catalog version and base currency are required.")
        identifiers = [item.instrument_id for item in self.instruments]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Catalog instrument identifiers must be unique.")
        non_cash_factors = [
            item.factor for item in self.instruments if item.instrument_type != "cash"
        ]
        if len(non_cash_factors) != len(set(non_cash_factors)):
            raise ValueError("Non-cash catalog risk factors must be unique.")
        if not any(item.instrument_type == "cash" for item in self.instruments):
            raise ValueError("Catalog requires at least one cash instrument.")

    @property
    def by_id(self) -> dict[str, InstrumentSpec]:
        return {item.instrument_id: item for item in self.instruments}

    @property
    def funded_choices(self) -> tuple[InstrumentSpec, ...]:
        return tuple(item for item in self.instruments if item.is_selectable_funded)

    @property
    def overlays(self) -> tuple[InstrumentSpec, ...]:
        return tuple(item for item in self.instruments if item.instrument_type == "fx_forward")

    def frame(self) -> pd.DataFrame:
        """Return the catalog in a dashboard-friendly tabular shape."""

        return pd.DataFrame(
            [
                {
                    "instrument_id": item.instrument_id,
                    "name": item.name,
                    "instrument_type": item.instrument_type,
                    "asset_class": item.asset_class,
                    "factor": item.factor,
                    "provider_symbol": item.provider_symbol,
                }
                for item in self.instruments
            ]
        )


@dataclass(frozen=True)
class PortfolioAllocation:
    """User-controlled weights before residual cash is calculated."""

    portfolio_name: str
    base_currency: str
    initial_nav: float
    rebalance_frequency: str
    residual_cash_instrument: str
    funded_weights: Mapping[str, float]
    overlay_fractions: Mapping[str, float]
    preset_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "funded_weights",
            {str(key): float(value) for key, value in self.funded_weights.items()},
        )
        object.__setattr__(
            self,
            "overlay_fractions",
            {str(key): float(value) for key, value in self.overlay_fractions.items()},
        )

    @property
    def invested_weight(self) -> float:
        return float(sum(self.funded_weights.values()))

    @property
    def residual_cash_weight(self) -> float:
        return float(1.0 - self.invested_weight)

    @property
    def active_risk_positions(self) -> int:
        return sum(weight > 0.0 for weight in self.funded_weights.values()) + sum(
            not np.isclose(fraction, 0.0) for fraction in self.overlay_fractions.values()
        )

    def with_weights(
        self,
        funded_weights: Mapping[str, float],
        overlay_fractions: Mapping[str, float] | None = None,
        *,
        portfolio_name: str | None = None,
    ) -> PortfolioAllocation:
        """Return a custom allocation while preserving portfolio-level controls."""

        return PortfolioAllocation(
            portfolio_name=portfolio_name or self.portfolio_name,
            base_currency=self.base_currency,
            initial_nav=self.initial_nav,
            rebalance_frequency=self.rebalance_frequency,
            residual_cash_instrument=self.residual_cash_instrument,
            funded_weights=dict(funded_weights),
            overlay_fractions=dict(
                self.overlay_fractions if overlay_fractions is None else overlay_fractions
            ),
            preset_key=None,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "portfolio_name": self.portfolio_name,
            "base_currency": self.base_currency,
            "initial_nav": self.initial_nav,
            "rebalance_frequency": self.rebalance_frequency,
            "residual_cash_instrument": self.residual_cash_instrument,
            "funded_weights": dict(self.funded_weights),
            "overlay_fractions": dict(self.overlay_fractions),
            "preset_key": self.preset_key,
            "residual_cash_weight": self.residual_cash_weight,
        }


@dataclass(frozen=True)
class PortfolioLibrary:
    """Portfolio-level defaults and named starting allocations."""

    portfolio_name: str
    base_currency: str
    initial_nav: float
    rebalance_frequency: str
    residual_cash_instrument: str
    default_preset: str
    presets: Mapping[str, Mapping[str, Any]]

    def allocation(self, preset_key: str | None = None) -> PortfolioAllocation:
        key = preset_key or self.default_preset
        if key not in self.presets:
            available = ", ".join(sorted(self.presets))
            raise KeyError(f"Unknown portfolio preset {key!r}. Available: {available}")
        preset = self.presets[key]
        display_name = str(preset.get("name", key.replace("_", " ").title()))
        return PortfolioAllocation(
            portfolio_name=f"{self.portfolio_name} — {display_name}",
            base_currency=self.base_currency,
            initial_nav=self.initial_nav,
            rebalance_frequency=self.rebalance_frequency,
            residual_cash_instrument=self.residual_cash_instrument,
            funded_weights=dict(preset.get("funded_weights", {})),
            overlay_fractions=dict(preset.get("overlay_fractions", {})),
            preset_key=key,
        )

    def preset_table(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "preset_key": key,
                    "name": value.get("name", key.replace("_", " ").title()),
                    "description": value.get("description", ""),
                }
                for key, value in self.presets.items()
            ]
        )


def load_instrument_catalog(path: str | Path) -> InstrumentCatalog:
    """Load and validate the approved instrument universe."""

    value = load_yaml(path)
    raw_instruments = value.get("instruments")
    if not isinstance(raw_instruments, list) or not raw_instruments:
        raise ValueError("Instrument catalog requires a non-empty instruments list.")
    return InstrumentCatalog(
        version=str(value.get("catalog_version", "")).strip(),
        base_currency=str(value.get("base_currency", "")).strip(),
        instruments=tuple(InstrumentSpec.from_mapping(item) for item in raw_instruments),
    )


def load_portfolio_library(path: str | Path) -> PortfolioLibrary:
    """Load named presets and portfolio-level controls."""

    value = load_yaml(path)
    presets = value.get("presets")
    if not isinstance(presets, dict) or not presets:
        raise ValueError("Portfolio configuration requires at least one preset.")
    library = PortfolioLibrary(
        portfolio_name=str(value.get("portfolio_name", "")).strip(),
        base_currency=str(value.get("base_currency", "")).strip(),
        initial_nav=float(value.get("initial_nav", 0.0)),
        rebalance_frequency=str(value.get("rebalance_frequency", "")).strip(),
        residual_cash_instrument=str(value.get("residual_cash_instrument", "")).strip(),
        default_preset=str(value.get("default_preset", "")).strip(),
        presets=presets,
    )
    if not library.portfolio_name or not library.base_currency:
        raise ValueError("Portfolio name and base currency are required.")
    if library.initial_nav <= 0.0 or not np.isfinite(library.initial_nav):
        raise ValueError("Initial NAV must be a positive finite number.")
    if library.default_preset not in presets:
        raise ValueError("Default portfolio preset is not defined.")
    return library


def resolve_portfolio(
    catalog: InstrumentCatalog,
    allocation: PortfolioAllocation,
) -> dict[str, Any]:
    """Resolve editable weights into the canonical accounting configuration."""

    if allocation.base_currency != catalog.base_currency:
        raise ValueError(
            f"Allocation currency {allocation.base_currency} does not match catalog currency "
            f"{catalog.base_currency}."
        )
    if allocation.initial_nav <= 0.0 or not np.isfinite(allocation.initial_nav):
        raise ValueError("Initial NAV must be a positive finite number.")
    if not allocation.rebalance_frequency:
        raise ValueError("Rebalance frequency is required.")

    catalog_by_id = catalog.by_id
    cash = catalog_by_id.get(allocation.residual_cash_instrument)
    if cash is None or cash.instrument_type != "cash":
        raise ValueError("Residual cash instrument must identify a catalog cash position.")

    positions: list[dict[str, Any]] = []
    invested_weight = 0.0
    for instrument_id, raw_weight in allocation.funded_weights.items():
        instrument = catalog_by_id.get(instrument_id)
        if instrument is None:
            raise ValueError(f"Unknown funded instrument: {instrument_id}")
        if not instrument.is_selectable_funded:
            raise ValueError(f"{instrument_id} cannot be used as an editable funded instrument.")
        weight = float(raw_weight)
        if not np.isfinite(weight) or weight < 0.0:
            raise ValueError(f"Weight for {instrument_id} must be finite and non-negative.")
        if np.isclose(weight, 0.0):
            continue
        invested_weight += weight
        positions.append(_funded_position(instrument, weight, allocation.initial_nav))

    if not positions:
        raise ValueError("Select at least one risk-bearing funded instrument.")
    if invested_weight > 1.0 + 1e-10:
        raise ValueError(
            f"Funded weights cannot exceed 100%; current total is {invested_weight:.2%}."
        )
    residual_cash = max(0.0, 1.0 - invested_weight)
    positions.append(_funded_position(cash, residual_cash, allocation.initial_nav))

    for instrument_id, raw_fraction in allocation.overlay_fractions.items():
        instrument = catalog_by_id.get(instrument_id)
        if instrument is None:
            raise ValueError(f"Unknown overlay instrument: {instrument_id}")
        if instrument.instrument_type != "fx_forward":
            raise ValueError(f"{instrument_id} is not an FX overlay instrument.")
        fraction = float(raw_fraction)
        if not np.isfinite(fraction):
            raise ValueError(f"Overlay fraction for {instrument_id} must be finite.")
        if np.isclose(fraction, 0.0):
            continue
        positions.append(_overlay_position(instrument, fraction, allocation.initial_nav))

    resolved = {
        "portfolio_name": allocation.portfolio_name,
        "base_currency": allocation.base_currency,
        "initial_nav": allocation.initial_nav,
        "rebalance_frequency": allocation.rebalance_frequency,
        "preset_key": allocation.preset_key,
        "residual_cash_instrument": allocation.residual_cash_instrument,
        "positions": positions,
    }
    validate_portfolio_config(resolved)
    return resolved


def load_default_portfolio(
    root: str | Path,
    preset_key: str | None = None,
) -> tuple[InstrumentCatalog, PortfolioLibrary, PortfolioAllocation, dict[str, Any]]:
    """Load the catalog, choose a preset, and return its resolved configuration."""

    root_path = Path(root)
    catalog = load_instrument_catalog(root_path / "config/instrument_catalog.yaml")
    library = load_portfolio_library(root_path / "config/core_portfolio.yaml")
    allocation = library.allocation(preset_key)
    resolved = resolve_portfolio(catalog, allocation)
    return catalog, library, allocation, resolved


def _funded_position(
    instrument: InstrumentSpec,
    weight: float,
    initial_nav: float,
) -> dict[str, Any]:
    position: dict[str, Any] = {
        "position_id": instrument.instrument_id,
        "name": instrument.name,
        "instrument_type": instrument.instrument_type,
        "asset_class": instrument.asset_class,
        "factor": instrument.factor,
        "target_weight": float(weight),
        "initial_market_value": float(initial_nav * weight),
    }
    if instrument.instrument_type == "bond":
        position["modified_duration"] = instrument.modified_duration
        position["convexity"] = instrument.convexity
    return position


def _overlay_position(
    instrument: InstrumentSpec,
    fraction: float,
    initial_nav: float,
) -> dict[str, Any]:
    return {
        "position_id": instrument.instrument_id,
        "name": instrument.name,
        "instrument_type": instrument.instrument_type,
        "asset_class": instrument.asset_class,
        "factor": instrument.factor,
        "quote_convention": instrument.quote_convention,
        "target_notional_fraction_of_nav": float(fraction),
        "initial_market_value": 0.0,
        "initial_notional": float(initial_nav * fraction),
    }

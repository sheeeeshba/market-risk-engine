"""Configuration loading and reproducibility helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping and fail with a beginner-readable message."""

    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Configuration file does not exist: {target}")
    with target.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"Configuration root must be a mapping: {target}")
    return value


def configuration_hash(*configs: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 hash across configuration mappings."""

    payload = json.dumps(configs, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def project_root() -> Path:
    """Return the installed source tree's project root."""

    return Path(__file__).resolve().parents[2]

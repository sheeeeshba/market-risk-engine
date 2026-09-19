"""Multi-Asset Market Risk Engine.

Educational model — not approved for regulatory capital or live trading limits.
"""

from .models import MarketRiskAnalysis, RiskHeadline
from .platform import MarketRiskPlatform

__all__ = ["MarketRiskAnalysis", "MarketRiskPlatform", "RiskHeadline"]

__version__ = "1.1.0"

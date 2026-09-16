"""Independent worked examples that define the first public P&L seam."""

from market_risk.pnl import bond_pnl, etf_pnl, fx_pnl


def test_manual_one_asset_equity_loss() -> None:
    """A USD 100 long position losing 10% has P&L of -USD 10."""
    result = etf_pnl(market_value=100.0, adjusted_return=-0.10)
    assert result == -10.0


def test_manual_bond_and_fx_signs() -> None:
    """Known literals establish decimal-yield and direct-FX sign conventions."""
    # -100 * 5 * 0.01 + 0.5 * 100 * 20 * 0.01^2 = -4.90
    assert bond_pnl(100.0, modified_duration=5.0, convexity=20.0, yield_change=0.01) == -4.9
    assert fx_pnl(100.0, eurusd_return=-0.10) == -10.0


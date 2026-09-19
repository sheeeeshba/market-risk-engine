from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_demo_dashboard_renders_complete_risk_workspace() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=120)

    assert not app.exception
    assert len(app.metric) >= 5
    metric_values = {item.label: item.value for item in app.metric}
    assert metric_values["Portfolio NAV"] == "$9.06m"
    assert metric_values["99.0% VaR range"] == "$89.3k to 93.9k"
    assert metric_values["99.0% ES range"] == "$101.9k to 104.8k"
    assert "Data source" in {item.label for item in app.selectbox}
    assert "FRED API key" in {item.label for item in app.text_input}
    assert "Run risk analysis" in {item.label for item in app.button}
    assert {
        "Portfolio builder",
        "Overview",
        "Risk models",
        "Backtesting",
        "Stress tests",
        "Risk contributions",
        "Portfolio & P&L",
        "Evidence & downloads",
    }.issubset({tab.label for tab in app.tabs})
    assert len(app.download_button) == 3


def test_dashboard_view_controls_update_without_recalculating() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=120)

    confidence = next(item for item in app.selectbox if item.label == "Confidence level")
    confidence.select(0.975).run(timeout=120)
    money = next(item for item in app.selectbox if item.label == "Money display")
    money.select("USD millions").run(timeout=120)
    basis = next(item for item in app.radio if item.label == "Risk chart basis")
    basis.set_value("% of NAV").run(timeout=120)
    model_chart = next(item for item in app.radio if item.label == "Model chart")
    model_chart.set_value("Confidence curve").run(timeout=120)
    instruments = next(
        item for item in app.multiselect if item.label == "Included funded instruments"
    )
    instruments.set_value([*instruments.value, "NVDA"]).run(timeout=120)

    assert not app.exception
    assert confidence.value == 0.975
    assert money.value == "USD millions"
    assert basis.value == "% of NAV"
    draft_metrics = {item.label: item.value for item in app.metric}
    assert draft_metrics["Active instruments"] == "24"
    assert draft_metrics["Invested"] == "95.00%"
    assert draft_metrics["Residual cash"] == "5.00%"


def test_live_mode_is_gated_before_data_download() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=120)

    source = next(item for item in app.selectbox if item.label == "Data source")
    source.select("Live market data").run(timeout=120)

    fred_key = next(item for item in app.text_input if item.label == "FRED API key")
    analyze = next(item for item in app.button if item.label == "Run risk analysis")
    assert fred_key.disabled is False
    assert analyze.disabled is True
    assert not app.exception

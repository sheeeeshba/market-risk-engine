"""Interactive analyst workspace for the Multi-Asset Market Risk Engine.

Run with ``python -m streamlit run streamlit_app.py``. The committed synthetic
snapshot loads without credentials; live mode keeps a supplied FRED key only in
the current Streamlit process and never writes it to project outputs.
"""

from __future__ import annotations

import html
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".mplconfig"))
load_dotenv(PROJECT_ROOT / ".env")

from market_risk.models import MarketRiskAnalysis  # noqa: E402
from market_risk.platform import MarketRiskPlatform  # noqa: E402
from market_risk.portfolio_builder import PortfolioAllocation  # noqa: E402

APP_VERSION = "1.1.0"

COLORS = {
    "paper": "#F4F6F8",
    "surface": "#FFFFFF",
    "ink": "#16324F",
    "muted": "#637282",
    "line": "#D7DEE5",
    "teal": "#197278",
    "red": "#B23A48",
    "amber": "#B26A00",
    "blue": "#2B5C88",
    "soft_blue": "#E8F0F6",
    "soft_red": "#FAECEE",
}

MONEY_UNITS = ("Automatic", "USD", "USD thousands", "USD millions")
DATE_WINDOWS = {
    "All available dates": None,
    "Last 12 months": 252,
    "Last 6 months": 126,
    "Last 3 months": 63,
}


@dataclass(frozen=True)
class ViewSettings:
    """User-controlled presentation settings; calculations remain unchanged."""

    confidence: float
    models: tuple[str, ...]
    date_window: int | None
    money_unit: str
    value_basis: str
    top_drivers: int


st.set_page_config(
    page_title="Risk Ledger | Multi-Asset Market Risk",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_css() -> None:
    """Apply the restrained institutional risk-ledger visual system."""

    st.markdown(
        f"""
        <style>
        :root {{
            --paper: {COLORS['paper']};
            --surface: {COLORS['surface']};
            --ink: {COLORS['ink']};
            --muted: {COLORS['muted']};
            --line: {COLORS['line']};
            --teal: {COLORS['teal']};
            --red: {COLORS['red']};
            --amber: {COLORS['amber']};
            --blue: {COLORS['blue']};
        }}
        .stApp {{
            background: var(--paper);
            color: var(--ink);
            font-family: "IBM Plex Sans", "SF Pro Text", "Segoe UI", sans-serif;
        }}
        [data-testid="stHeader"] {{ background: rgba(244, 246, 248, .92); }}
        [data-testid="stSidebar"] {{
            background: #EAF0F4;
            border-right: 1px solid var(--line);
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stCaptionContainer"] {{ color: var(--muted); }}
        .block-container {{
            max-width: 1500px;
            padding: 1.6rem clamp(1rem, 2.5vw, 2.5rem) 4rem;
        }}
        h1, h2, h3, h4, [data-testid="stMarkdownContainer"] {{ color: var(--ink); }}
        h2 {{ margin: 0 0 .45rem; letter-spacing: -.025em; line-height: 1.18; }}
        h3 {{ margin: 1.2rem 0 .5rem; letter-spacing: -.015em; line-height: 1.25; }}
        .brand {{
            padding: .2rem 0 1rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1rem;
        }}
        .brand strong {{ color: var(--ink); font-size: 1.08rem; letter-spacing: -.02em; }}
        .brand span {{ display: block; color: var(--muted); font-size: .78rem; margin-top: .25rem; }}
        .risk-header {{
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(16rem, .6fr);
            gap: 1.2rem;
            align-items: end;
            background: var(--surface);
            border-top: 4px solid var(--ink);
            border-bottom: 1px solid var(--line);
            padding: 1.3rem 1.4rem 1.15rem;
            margin-bottom: 1rem;
        }}
        .risk-header h1 {{
            margin: 0;
            font-size: clamp(1.75rem, 3vw, 2.7rem);
            letter-spacing: -.055em;
            line-height: 1.02;
        }}
        .risk-header p {{ color: var(--muted); margin: .65rem 0 0; max-width: 48rem; line-height: 1.5; }}
        .header-meta {{
            text-align: right;
            color: var(--muted);
            font-size: .84rem;
            line-height: 1.7;
            overflow-wrap: anywhere;
        }}
        .header-meta strong {{ color: var(--ink); font-variant-numeric: tabular-nums; }}
        .classification {{
            display: inline-flex;
            border: 1px solid var(--amber);
            color: var(--amber);
            background: #FFF8E8;
            padding: .28rem .55rem;
            font-size: .72rem;
            font-weight: 700;
            margin-top: .5rem;
        }}
        .risk-tape {{
            background: var(--surface);
            border: 1px solid var(--line);
            padding: 1rem 1.2rem 1.15rem;
            margin: 0 0 1rem;
        }}
        .tape-head {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: .35rem 1rem;
            align-items: baseline;
        }}
        .tape-head strong {{ color: var(--ink); }}
        .tape-head span {{ color: var(--muted); font-size: .78rem; }}
        .track {{ position: relative; height: 2.1rem; margin: .75rem .2rem .35rem; }}
        .track-line {{ position: absolute; left: 0; right: 0; top: 1rem; height: 2px; background: var(--line); }}
        .var-band {{ position: absolute; top: .68rem; height: .64rem; background: var(--blue); min-width: 4px; }}
        .es-band {{ position: absolute; top: .82rem; height: .34rem; background: var(--red); min-width: 4px; }}
        .tape-labels {{
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: .5rem 1.2rem;
            align-items: start;
            color: var(--muted);
            font-size: .73rem;
            font-variant-numeric: tabular-nums;
        }}
        .section-intro {{
            background: var(--surface);
            border-left: 4px solid var(--ink);
            padding: 1rem 1.15rem .95rem;
            margin: .9rem 0 1.15rem;
        }}
        .section-intro h2 {{ margin: 0 0 .32rem; font-size: 1.35rem; }}
        .section-intro p {{
            color: var(--muted);
            line-height: 1.55;
            max-width: 76ch;
            margin: 0;
        }}
        .control-note {{
            color: var(--muted);
            font-size: .8rem;
            line-height: 1.45;
            padding: .55rem .65rem;
            background: rgba(255,255,255,.55);
            border: 1px solid var(--line);
            margin: .35rem 0 .75rem;
        }}
        .ledger-note {{
            border-left: 3px solid var(--teal);
            background: var(--surface);
            padding: .75rem .9rem;
            color: var(--muted);
            line-height: 1.5;
            margin: .65rem 0 1rem;
        }}
        [data-testid="stMetric"] {{
            background: var(--surface);
            border-top: 2px solid var(--ink);
            border-bottom: 1px solid var(--line);
            padding: .75rem .85rem;
            min-height: 105px;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--muted); }}
        [data-testid="stMetricValue"] {{
            color: var(--ink);
            font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
            font-size: 1.35rem;
            font-variant-numeric: tabular-nums;
        }}
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
            gap: .15rem;
            border-bottom: 1px solid var(--line);
            overflow-x: auto;
        }}
        div[data-testid="stTabs"] button {{ color: var(--muted); font-weight: 650; white-space: nowrap; }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{ color: var(--ink); }}
        div[data-testid="stTabs"] [role="tabpanel"] {{ padding-top: .65rem; }}
        [data-testid="stDataFrame"] {{ border: 1px solid var(--line); margin: .2rem 0 .9rem; }}
        [data-testid="stPlotlyChart"] {{
            background: var(--surface);
            border: 1px solid var(--line);
            padding: .2rem;
            margin: .15rem 0 .85rem;
        }}
        div.stButton > button, div.stDownloadButton > button {{
            border-radius: 2px;
            border: 1px solid var(--ink);
            min-height: 2.6rem;
            font-weight: 700;
            color: var(--ink);
            background: var(--surface);
        }}
        div.stButton > button[kind="primary"]:not(:disabled),
        div.stDownloadButton > button[kind="primary"]:not(:disabled) {{
            color: #FFFFFF;
            background: var(--ink);
            border-color: var(--ink);
        }}
        div.stButton > button p,
        div.stDownloadButton > button p {{ color: inherit !important; }}
        button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-primary"] p,
        [data-testid="stSidebar"] button[kind="primary"] * {{ color: #FFFFFF !important; }}
        div.stButton > button:focus-visible,
        div.stDownloadButton > button:focus-visible,
        input:focus-visible,
        [role="tab"]:focus-visible {{ outline: 3px solid rgba(25, 114, 120, .35); outline-offset: 2px; }}
        @media (max-width: 800px) {{
            .risk-header {{ grid-template-columns: 1fr; }}
            .header-meta {{ text-align: left; }}
            .tape-labels {{ grid-template-columns: 1fr; }}
        }}
        @media (prefers-reduced-motion: reduce) {{ * {{ scroll-behavior: auto !important; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def _load_committed_analysis() -> MarketRiskAnalysis:
    return MarketRiskPlatform(PROJECT_ROOT).analyze(data_mode="snapshot", refresh=False)


def _money_scale(unit: str, values: pd.Series | list[float]) -> tuple[float, str, str]:
    """Return divisor, suffix, and readable axis label for a display unit."""

    maximum = max((abs(float(value)) for value in values if pd.notna(value)), default=0.0)
    resolved = unit
    if unit == "Automatic":
        resolved = "USD millions" if maximum >= 1_000_000 else "USD thousands" if maximum >= 1_000 else "USD"
    if resolved == "USD millions":
        return 1_000_000.0, "m", "USD millions"
    if resolved == "USD thousands":
        return 1_000.0, "k", "USD thousands"
    return 1.0, "", "USD"


def _money(value: float, unit: str = "Automatic") -> str:
    divisor, suffix, _ = _money_scale(unit, [value])
    scaled = value / divisor
    decimals = 2 if divisor == 1_000_000 else 1 if divisor == 1_000 else 0
    sign = "-" if scaled < 0 else ""
    return f"{sign}${abs(scaled):,.{decimals}f}{suffix}"


def _money_range(low: float, high: float, unit: str = "Automatic") -> str:
    """Format a range with one currency sign so Streamlit does not parse inline math."""

    divisor, suffix, _ = _money_scale(unit, [low, high])
    decimals = 2 if divisor == 1_000_000 else 1 if divisor == 1_000 else 0

    def fragment(value: float, *, currency: bool) -> str:
        scaled = value / divisor
        sign = "-" if scaled < 0 else ""
        symbol = "$" if currency else ""
        return f"{sign}{symbol}{abs(scaled):,.{decimals}f}{suffix}"

    return f"{fragment(low, currency=True)} to {fragment(high, currency=False)}"


def _money_axis(values: pd.Series, unit: str) -> tuple[pd.Series, str, str]:
    divisor, suffix, label = _money_scale(unit, values.tolist())
    return values.astype(float) / divisor, suffix, label


def _percent(value: float) -> str:
    return f"{value:.2%}"


def _plot_layout(
    figure: go.Figure,
    title: str,
    height: int = 430,
    *,
    legend: bool = True,
    left_margin: int = 55,
) -> go.Figure:
    figure.update_layout(
        title={
            "text": title,
            "font": {"size": 17, "color": COLORS["ink"]},
            "x": 0.015,
            "xanchor": "left",
            "y": 0.97,
            "yanchor": "top",
        },
        height=height,
        margin={"l": left_margin, "r": 34, "t": 124 if legend else 72, "b": 55},
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font={"family": "IBM Plex Sans, SF Pro Text, sans-serif", "color": COLORS["ink"]},
        legend={
            "orientation": "h",
            "y": 1.04,
            "yanchor": "bottom",
            "x": 0,
            "xanchor": "left",
            "font": {"size": 11},
        },
        showlegend=legend,
        hoverlabel={"bgcolor": COLORS["ink"], "font_color": "#FFFFFF"},
        hovermode="closest",
    )
    figure.update_xaxes(
        gridcolor=COLORS["line"], zerolinecolor=COLORS["line"], automargin=True
    )
    figure.update_yaxes(
        gridcolor=COLORS["line"], zerolinecolor=COLORS["line"], automargin=True
    )
    return figure


def _section_intro(title: str, description: str) -> None:
    st.markdown(
        f"<div class='section-intro'><h2>{html.escape(title)}</h2>"
        f"<p>{html.escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def _tail_window(frame: pd.DataFrame, date_column: str, periods: int | None) -> pd.DataFrame:
    ordered = frame.sort_values(date_column)
    if periods is None:
        return ordered
    dates = ordered[date_column].drop_duplicates().tail(periods)
    return ordered[ordered[date_column].isin(dates)]


def _selected_current_risk(
    result: MarketRiskAnalysis, settings: ViewSettings
) -> pd.DataFrame:
    risk = result.table("current_risk")
    return risk[
        risk["model"].isin(settings.models)
        & risk["confidence"].round(6).eq(round(settings.confidence, 6))
    ].copy()


def _risk_tape(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    selected = _selected_current_risk(result, settings)
    var_low = float(selected["var"].min())
    var_high = float(selected["var"].max())
    es_low = float(selected["es"].min())
    es_high = float(selected["es"].max())
    maximum = max(es_high * 1.25, var_high * 1.45, 1.0)
    var_left = 100 * var_low / maximum
    var_width = 100 * (var_high - var_low) / maximum
    es_left = 100 * es_low / maximum
    es_width = 100 * (es_high - es_low) / maximum
    confidence = f"{settings.confidence:.1%}"
    st.markdown(
        f"""
        <div class="risk-tape">
          <div class="tape-head">
            <strong>{confidence} one-interval tail-risk range</strong>
            <span>VaR in blue · Expected Shortfall in red · scale to {_money(maximum, settings.money_unit)}</span>
          </div>
          <div class="track">
            <div class="track-line"></div>
            <div class="var-band" style="left:{var_left:.2f}%;width:{max(var_width, .5):.2f}%"></div>
            <div class="es-band" style="left:{es_left:.2f}%;width:{max(es_width, .5):.2f}%"></div>
          </div>
          <div class="tape-labels">
            <span>$0</span>
            <span>VaR {_money_range(var_low, var_high, settings.money_unit)}</span>
            <span>ES {_money_range(es_low, es_high, settings.money_unit)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _risk_model_chart(
    result: MarketRiskAnalysis,
    settings: ViewSettings,
    mode: str = "Selected confidence",
) -> go.Figure:
    risk = result.table("current_risk")
    risk = risk[risk["model"].isin(settings.models)].copy()
    figure = go.Figure()
    percent_basis = settings.value_basis == "% of NAV"
    if mode == "Selected confidence":
        selected = _selected_current_risk(result, settings)
        model_labels = ["<br>".join(str(model).split()) for model in selected["model"]]
        model_names = selected["model"].astype(str)
        var_column = "var_pct_nav" if percent_basis else "var"
        es_column = "es_pct_nav" if percent_basis else "es"
        if percent_basis:
            var_values = selected[var_column]
            es_values = selected[es_column]
            hover = "%{y:.2%} of NAV"
            text_template = "%{y:.2%}"
            axis_title = "% of NAV"
            tickformat = ".1%"
        else:
            combined = pd.concat([selected[var_column], selected[es_column]], ignore_index=True)
            divisor, suffix, axis_title = _money_scale(settings.money_unit, combined.tolist())
            var_values = selected[var_column] / divisor
            es_values = selected[es_column] / divisor
            hover = f"$%{{y:,.1f}}{suffix}"
            text_template = f"$%{{y:,.1f}}{suffix}"
            tickformat = ",.1f"
        figure.add_bar(
            name="VaR",
            x=model_labels,
            y=var_values,
            customdata=model_names,
            marker_color=COLORS["blue"],
            texttemplate=text_template,
            textposition="outside",
            hovertemplate="%{customdata}<br>VaR " + hover + "<extra></extra>",
        )
        figure.add_bar(
            name="Expected Shortfall",
            x=model_labels,
            y=es_values,
            customdata=model_names,
            marker_color=COLORS["red"],
            texttemplate=text_template,
            textposition="outside",
            hovertemplate="%{customdata}<br>Expected Shortfall " + hover + "<extra></extra>",
        )
        figure.update_layout(barmode="group", uniformtext_minsize=9, uniformtext_mode="hide")
        figure.update_yaxes(title=axis_title, tickformat=tickformat, rangemode="tozero")
        figure.update_xaxes(title=None, tickangle=0)
        title = f"Model comparison at {settings.confidence:.1%} confidence"
    else:
        palette = [COLORS["blue"], COLORS["teal"], COLORS["amber"]]
        money_values = pd.concat([risk["var"], risk["es"]], ignore_index=True)
        divisor, suffix, money_label = _money_scale(settings.money_unit, money_values.tolist())
        for color, (model, group) in zip(
            palette, risk.groupby("model", sort=False), strict=False
        ):
            labels = [f"{confidence:.1%}" for confidence in group["confidence"]]
            for measure, dash in (("var", "solid"), ("es", "dot")):
                if percent_basis:
                    values = group[f"{measure}_pct_nav"]
                    hover = "%{y:.2%} of NAV"
                else:
                    values = group[measure] / divisor
                    hover = f"$%{{y:,.1f}}{suffix}"
                label = "VaR" if measure == "var" else "ES"
                figure.add_scatter(
                    name=model,
                    legendgroup=model,
                    showlegend=measure == "var",
                    x=labels,
                    y=values,
                    mode="lines+markers",
                    line={"color": color, "dash": dash, "width": 2},
                    hovertemplate=f"{html.escape(model)} · {label}<br>%{{x}}: {hover}<extra></extra>",
                )
        figure.update_yaxes(
            title="% of NAV" if percent_basis else money_label,
            tickformat=".1%" if percent_basis else ",.1f",
        )
        figure.update_xaxes(title="Confidence level")
        title = "Tail-risk curve · solid VaR / dotted Expected Shortfall"
    return _plot_layout(figure, title, height=470)


def _portfolio_chart(
    result: MarketRiskAnalysis,
    settings: ViewSettings,
    mode: str = "NAV",
) -> go.Figure:
    daily = _tail_window(
        result.table("daily_portfolio_pnl"), "portfolio_date", settings.date_window
    )
    if mode == "Daily P&L":
        raw = daily["portfolio_pnl"]
        values, suffix, axis_title = _money_axis(raw, settings.money_unit)
        colors = [COLORS["teal"] if value >= 0 else COLORS["red"] for value in raw]
        figure = go.Figure(
            go.Bar(
                x=daily["portfolio_date"],
                y=values,
                marker_color=colors,
                hovertemplate=f"%{{x|%Y-%m-%d}}<br>Daily P&L $%{{y:,.1f}}{suffix}<extra></extra>",
            )
        )
        title = "Daily hypothetical portfolio P&L"
    else:
        raw = daily["nav"] if mode == "NAV" else daily["portfolio_pnl"].cumsum()
        values, suffix, axis_title = _money_axis(raw, settings.money_unit)
        label = "NAV" if mode == "NAV" else "Cumulative P&L"
        figure = go.Figure(
            go.Scatter(
                x=daily["portfolio_date"],
                y=values,
                mode="lines",
                line={"color": COLORS["ink"], "width": 2},
                hovertemplate=f"%{{x|%Y-%m-%d}}<br>{label} $%{{y:,.2f}}{suffix}<extra></extra>",
            )
        )
        title = "Portfolio NAV path" if mode == "NAV" else "Cumulative hypothetical P&L"
    figure.update_yaxes(title=axis_title, tickformat=",.1f")
    figure.update_xaxes(title=None)
    figure.update_layout(hovermode="x unified")
    return _plot_layout(figure, title, legend=False, height=450)


def _backtest_chart(result: MarketRiskAnalysis, settings: ViewSettings) -> go.Figure:
    forecasts = result.table("rolling_forecasts")
    forecasts = forecasts[forecasts["model"].isin(settings.models)]
    forecasts = _tail_window(forecasts, "realized_date", settings.date_window)
    divisor, suffix, axis_title = _money_scale(
        settings.money_unit,
        pd.concat([forecasts["realized_loss"], forecasts["var"]], ignore_index=True).tolist(),
    )
    realized = forecasts.drop_duplicates("realized_date")
    figure = go.Figure(
        go.Scatter(
            x=realized["realized_date"],
            y=realized["realized_loss"] / divisor,
            name="Realized hypothetical loss",
            mode="lines",
            line={"color": COLORS["ink"], "width": 1.4},
            hovertemplate=f"%{{x|%Y-%m-%d}}<br>Realized loss $%{{y:,.1f}}{suffix}<extra></extra>",
        )
    )
    palette = [COLORS["blue"], COLORS["teal"], COLORS["amber"]]
    for color, (model, group) in zip(palette, forecasts.groupby("model", sort=False), strict=False):
        figure.add_scatter(
            x=group["realized_date"],
            y=group["var"] / divisor,
            name=f"{model} VaR",
            mode="lines",
            line={"color": color, "width": 1.5},
            hovertemplate=f"{html.escape(model)}<br>%{{x|%Y-%m-%d}}<br>VaR $%{{y:,.1f}}{suffix}<extra></extra>",
        )
        breaches = group[group["exception"].astype(bool)]
        figure.add_scatter(
            x=breaches["realized_date"],
            y=breaches["realized_loss"] / divisor,
            name=f"{model} breach",
            mode="markers",
            marker={"color": COLORS["red"], "size": 8, "symbol": "x"},
            showlegend=False,
            hovertemplate=f"{html.escape(model)} breach<br>%{{x|%Y-%m-%d}}<br>$%{{y:,.1f}}{suffix}<extra></extra>",
        )
    figure.update_yaxes(title=axis_title, tickformat=",.1f")
    figure.update_xaxes(title=None)
    figure.update_layout(hovermode="x unified")
    return _plot_layout(figure, "Rolling 99% VaR versus next-interval loss", height=520)


def _stress_chart(
    result: MarketRiskAnalysis,
    table_name: str,
    title: str,
    settings: ViewSettings,
) -> go.Figure:
    stress = result.table(table_name).sort_values("scenario_loss")
    if settings.value_basis == "% of NAV":
        values = stress["loss_pct_nav"]
        axis_title = "% of NAV"
        tickformat = ".1%"
        text = values.map(lambda value: f"{value:.1%}")
        hover = "%{x:.2%} of NAV"
    else:
        values, suffix, axis_title = _money_axis(stress["scenario_loss"], settings.money_unit)
        tickformat = ",.1f"
        text = [f"${value:,.1f}{suffix}" for value in values]
        hover = f"$%{{x:,.1f}}{suffix}"
    figure = go.Figure(
        go.Bar(
            x=values,
            y=stress["scenario_name"],
            orientation="h",
            marker_color=COLORS["red"],
            text=text,
            textposition="auto",
            hovertemplate="%{y}<br>Loss " + hover + "<extra></extra>",
        )
    )
    figure.update_xaxes(title=axis_title, tickformat=tickformat, rangemode="tozero")
    figure.update_yaxes(title=None)
    return _plot_layout(figure, title, height=480, legend=False, left_margin=210)


def _contribution_chart(result: MarketRiskAnalysis, settings: ViewSettings) -> go.Figure:
    contributions = result.table("risk_contributions").nlargest(
        settings.top_drivers, "component_var"
    )
    contributions = contributions.sort_values("component_var")
    percent_basis = settings.value_basis == "% of NAV"
    if percent_basis:
        values = contributions["component_share"]
        axis_title = "% of total VaR"
        tickformat = ".0%"
        hover = "%{x:.1%} of total VaR"
    else:
        values, suffix, axis_title = _money_axis(
            contributions["component_var"], settings.money_unit
        )
        tickformat = ",.1f"
        hover = f"$%{{x:,.1f}}{suffix}"
    colors = [COLORS["teal"] if value < 0 else COLORS["blue"] for value in values]
    figure = go.Figure(
        go.Bar(
            x=values,
            y=contributions["position_id"],
            orientation="h",
            marker_color=colors,
            hovertemplate="%{y}<br>Component VaR " + hover + "<extra></extra>",
        )
    )
    figure.update_xaxes(title=axis_title, tickformat=tickformat)
    figure.update_yaxes(title=None)
    return _plot_layout(
        figure,
        "Position contribution to 99% Parametric VaR",
        legend=False,
        left_margin=90,
    )


def _render_header(result: MarketRiskAnalysis) -> None:
    safe_name = html.escape(result.portfolio_name)
    safe_snapshot = html.escape(result.snapshot_id)
    safe_classification = html.escape(result.data_classification)
    st.markdown(
        f"""
        <section class="risk-header">
          <div>
            <h1>Risk Ledger</h1>
            <p>{safe_name}. Compare model risk, inspect exceptions, trace concentrations,
            and download the complete evidence bundle from one review surface.</p>
          </div>
          <div class="header-meta">
            As of <strong>{result.headline.as_of_date}</strong><br>
            Model <strong>v{html.escape(result.model_version)}</strong><br>
            Snapshot <strong>{safe_snapshot}</strong><br>
            <span class="classification">{safe_classification}</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_source_controls() -> tuple[str, str, bool]:
    with st.sidebar:
        st.markdown(
            "<div class='brand'><strong>Risk Ledger</strong><span>Multi-asset model control room</span></div>",
            unsafe_allow_html=True,
        )
        source = st.selectbox(
            "Data source",
            ["Demo snapshot", "Live market data"],
            help="Demo is deterministic and needs no credentials. Live mode downloads Yahoo/FRED data.",
        )
        live = source == "Live market data"
        fred_key = st.text_input(
            "FRED API key",
            type="password",
            value="",
            disabled=not live,
            placeholder="Not required for Demo" if not live else "Paste a session-only key",
            help="Kept in the current process only; never written to reports or downloads.",
        )
        run = st.button(
            "Run risk analysis",
            type="primary",
            width="stretch",
            disabled=live and not fred_key.strip(),
        )
        st.caption(
            "Demo results use synthetic factors and validate engineering behaviour only. "
            "They are not historical performance or investment advice."
        )
    return ("live" if live else "snapshot"), (fred_key if live else ""), run


def _render_view_controls(result: MarketRiskAnalysis) -> ViewSettings:
    risk = result.table("current_risk")
    confidences = sorted(float(value) for value in risk["confidence"].unique())
    models = list(dict.fromkeys(risk["model"].tolist()))
    driver_count = len(result.table("risk_contributions"))
    with st.sidebar:
        st.divider()
        st.markdown("### View controls")
        st.markdown(
            "<div class='control-note'>These controls change presentation only. "
            "They do not recalculate portfolio risk.</div>",
            unsafe_allow_html=True,
        )
        confidence = st.selectbox(
            "Confidence level",
            confidences,
            index=len(confidences) - 1,
            format_func=lambda value: f"{value:.1%}",
            help="Applied to the current VaR/Expected Shortfall comparison.",
        )
        selected_models = st.multiselect(
            "Models shown",
            models,
            default=models,
            help="Hide a model to simplify comparison charts and rolling backtests.",
        )
        if not selected_models:
            st.warning("At least one model is required; all models remain visible.")
            selected_models = models
        window_label = st.selectbox("Chart history", list(DATE_WINDOWS), index=0)
        money_unit = st.selectbox(
            "Money display",
            MONEY_UNITS,
            index=0,
            help="Automatic chooses USD, thousands, or millions independently for each chart.",
        )
        value_basis = st.radio(
            "Risk chart basis",
            ["USD loss", "% of NAV"],
            horizontal=True,
            help="Applied to model, stress, and contribution charts.",
        )
        top_drivers = st.slider(
            "Risk drivers shown",
            min_value=min(3, driver_count),
            max_value=driver_count,
            value=driver_count,
            help="Limits the position-contribution chart to the largest component-VaR drivers.",
        )
        st.divider()
        st.caption(f"Application v{APP_VERSION} · Python analytics + Streamlit")
    return ViewSettings(
        confidence=float(confidence),
        models=tuple(selected_models),
        date_window=DATE_WINDOWS[window_label],
        money_unit=money_unit,
        value_basis=value_basis,
        top_drivers=top_drivers,
    )


def _run_analysis(mode: str, fred_key: str, run_requested: bool) -> MarketRiskAnalysis:
    if "analysis" not in st.session_state:
        st.session_state.analysis = _load_committed_analysis()
    if run_requested:
        try:
            with st.spinner("Running portfolio, model, backtesting, and stress layers…"):
                platform = MarketRiskPlatform(PROJECT_ROOT)
                active_allocation = st.session_state.get("active_allocation")
                if isinstance(active_allocation, PortfolioAllocation):
                    st.session_state.analysis = platform.analyze_portfolio(
                        active_allocation,
                        data_mode=mode,
                        fred_api_key=fred_key or None,
                    )
                else:
                    st.session_state.analysis = platform.analyze(
                        data_mode=mode,
                        refresh=True,
                        fred_api_key=fred_key or None,
                    )
        except Exception as error:  # Streamlit must turn operational failures into guidance.
            st.error(f"Analysis did not run: {error}")
            st.info(
                "Demo requires the standard installation. Live mode additionally requires "
                "`pip install '.[live]'` and a valid FRED API key."
            )
    return st.session_state.analysis


def _allocation_preview(allocation: pd.DataFrame, cash_weight: float) -> go.Figure:
    """Show the draft allocation before the expensive linked recalculation."""

    preview = allocation[allocation["Weight %"] > 0.0].copy()
    grouped = preview.groupby("Asset class", sort=False)["Weight %"].sum()
    labels = grouped.index.tolist()
    values = grouped.tolist()
    colors = [COLORS["blue"], COLORS["teal"], COLORS["amber"], "#6D597A", "#4F772D"]
    if cash_weight > 1e-9:
        labels.append("USD cash")
        values.append(cash_weight * 100.0)
    figure = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.58,
            sort=False,
            textinfo="label+percent",
            textposition="inside",
            insidetextorientation="horizontal",
            marker={"colors": [colors[index % len(colors)] for index in range(len(labels))]},
            hovertemplate="%{label}<br>%{value:.2f}% of NAV<extra></extra>",
        )
    )
    figure.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")
    return _plot_layout(
        figure,
        "Draft allocation by asset class",
        height=520,
        legend=False,
        left_margin=25,
    )


def _render_portfolio_builder(
    result: MarketRiskAnalysis,
    mode: str,
    fred_key: str,
) -> None:
    _section_intro(
        "Build your portfolio",
        "Choose approved stocks, ETFs, bonds, precious metals, commodities, and an FX "
        "overlay. Edit target weights, review residual cash, then apply once to recalculate "
        "NAV, VaR/ES, backtesting, stress losses, and risk contributions together.",
    )
    platform = MarketRiskPlatform(PROJECT_ROOT)
    catalog = platform.portfolio_catalog()
    library = platform.portfolio_library()
    preset_table = library.preset_table().set_index("preset_key")
    preset_keys = list(library.presets)
    preset_key = st.selectbox(
        "Starting allocation",
        preset_keys,
        index=preset_keys.index(library.default_preset),
        format_func=lambda key: str(preset_table.loc[key, "name"]),
        help="A preset is only a starting point; every selected weight remains editable.",
        key="portfolio_preset",
    )
    preset = library.allocation(preset_key)
    st.caption(str(preset_table.loc[preset_key, "description"]))

    choices = catalog.funded_choices
    by_id = catalog.by_id
    option_ids = [item.instrument_id for item in choices]
    labels = {
        item.instrument_id: f"{item.instrument_id} · {item.asset_class} · {item.name}"
        for item in choices
    }
    selected_ids = st.multiselect(
        "Included funded instruments",
        option_ids,
        default=[key for key, value in preset.funded_weights.items() if value > 0.0],
        format_func=lambda instrument_id: labels[instrument_id],
        help="Remove an item to exclude it completely; add any instrument from the approved catalog.",
        key=f"selected_instruments_{preset_key}",
    )
    editor_rows = []
    for instrument_id in selected_ids:
        item = by_id[instrument_id]
        editor_rows.append(
            {
                "Symbol": instrument_id,
                "Instrument": item.name,
                "Asset class": item.asset_class,
                "Type": "Stock" if item.instrument_type == "equity" else item.instrument_type.upper(),
                "Weight %": 100.0 * float(preset.funded_weights.get(instrument_id, 0.02)),
            }
        )
    editor_input = pd.DataFrame(
        editor_rows,
        columns=["Symbol", "Instrument", "Asset class", "Type", "Weight %"],
    )
    edited = st.data_editor(
        editor_input,
        hide_index=True,
        width="stretch",
        disabled=["Symbol", "Instrument", "Asset class", "Type"],
        column_config={
            "Symbol": st.column_config.TextColumn(width="small"),
            "Instrument": st.column_config.TextColumn(width="large"),
            "Asset class": st.column_config.TextColumn(width="medium"),
            "Type": st.column_config.TextColumn(width="small"),
            "Weight %": st.column_config.NumberColumn(
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                format="%.2f%%",
                help="Target funded weight as a percentage of portfolio NAV.",
            ),
        },
        key=f"allocation_editor_{preset_key}",
    )
    overlay_default = 100.0 * float(preset.overlay_fractions.get("EURUSD_OVERLAY", 0.0))
    overlay_percent = st.slider(
        "EUR/USD overlay notional (% of NAV)",
        min_value=-25.0,
        max_value=25.0,
        value=overlay_default,
        step=1.0,
        help="Zero-funded currency overlay. Negative values reverse the direction.",
        key=f"fx_overlay_{preset_key}",
    )

    total_weight = float(edited["Weight %"].sum()) / 100.0 if not edited.empty else 0.0
    residual_cash = 1.0 - total_weight
    classes = edited.loc[edited["Weight %"] > 0.0, "Asset class"].nunique()
    metrics = st.columns(4)
    metrics[0].metric("Active instruments", f"{int((edited['Weight %'] > 0.0).sum()):,}")
    metrics[1].metric("Asset classes", f"{classes:,}")
    metrics[2].metric("Invested", _percent(total_weight))
    metrics[3].metric("Residual cash", _percent(residual_cash))

    valid = True
    if edited.empty or total_weight <= 0.0:
        st.error("Select at least one instrument and assign it a positive weight.")
        valid = False
    elif total_weight > 1.0 + 1e-10:
        st.error(f"Target weights total {_percent(total_weight)}. Reduce them to 100% or less.")
        valid = False
    elif residual_cash < 0.01:
        st.warning("Residual cash is below 1%; the portfolio has very little liquidity buffer.")
    else:
        st.success(
            f"Funding identity is valid: {_percent(total_weight)} invested + "
            f"{_percent(residual_cash)} cash = 100.00%."
        )

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown("### Apply linked calculation")
        st.markdown(
            "<div class='control-note'>Draft edits update the preview immediately. Risk results "
            "change only when you click Apply, so Monte Carlo and rolling backtests are not rerun "
            "after every keystroke.</div>",
            unsafe_allow_html=True,
        )
        apply_clicked = st.button(
            "Apply portfolio & recalculate all results",
            type="primary",
            disabled=not valid or (mode == "live" and not fred_key.strip()),
            width="stretch",
        )
        reset_clicked = st.button("Reset to committed diversified demo", width="stretch")
        if result.is_custom:
            st.info(
                f"Active results use a custom allocation. Current top risk driver: "
                f"{result.headline.top_risk_driver}."
            )
    with right:
        st.plotly_chart(
            _allocation_preview(edited, max(residual_cash, 0.0)),
            width="stretch",
            key=f"allocation_preview_{preset_key}",
        )

    if apply_clicked:
        weights = {
            str(row["Symbol"]): float(row["Weight %"]) / 100.0
            for _, row in edited.iterrows()
            if float(row["Weight %"]) > 0.0
        }
        overlays = (
            {"EURUSD_OVERLAY": overlay_percent / 100.0}
            if abs(overlay_percent) > 1e-12
            else {}
        )
        allocation = preset.with_weights(
            weights,
            overlays,
            portfolio_name=f"Custom Multi-Asset Portfolio · {len(weights)} funded positions",
        )
        try:
            with st.spinner("Recalculating every linked portfolio and risk layer…"):
                st.session_state.analysis = platform.analyze_portfolio(
                    allocation,
                    data_mode=mode,
                    fred_api_key=fred_key or None,
                )
                st.session_state.active_allocation = allocation
            st.rerun()
        except Exception as error:
            st.error(f"Custom portfolio could not be calculated: {error}")
    if reset_clicked:
        st.session_state.analysis = _load_committed_analysis()
        st.session_state.pop("active_allocation", None)
        st.rerun()

    with st.expander("Browse the complete approved instrument catalog"):
        catalog_view = catalog.frame().copy()
        catalog_view["instrument_type"] = catalog_view["instrument_type"].replace(
            {"equity": "stock", "fx_forward": "FX overlay"}
        )
        st.dataframe(
            catalog_view.rename(
                columns={
                    "instrument_id": "Symbol",
                    "name": "Instrument",
                    "instrument_type": "Type",
                    "asset_class": "Asset class",
                    "factor": "Risk factor",
                    "provider_symbol": "Data symbol",
                }
            ),
            hide_index=True,
            width="stretch",
        )


def _render_overview(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    _section_intro(
        "Portfolio risk overview",
        "Start here for the selected confidence level: current model range, stress severity, "
        "exception count, and the portfolio path behind those numbers.",
    )
    headline = result.headline
    risk = _selected_current_risk(result, settings)
    var_low, var_high = float(risk["var"].min()), float(risk["var"].max())
    es_low, es_high = float(risk["es"].min()), float(risk["es"].max())
    exceptions = result.table("rolling_forecasts")
    exceptions = int(
        exceptions[exceptions["model"].isin(settings.models)]["exception"].astype(bool).sum()
    )
    first_row = st.columns(3)
    first_row[0].metric("Portfolio NAV", _money(headline.nav, settings.money_unit))
    first_row[1].metric(
        f"{settings.confidence:.1%} VaR range",
        _money_range(var_low, var_high, settings.money_unit),
    )
    first_row[2].metric(
        f"{settings.confidence:.1%} ES range",
        _money_range(es_low, es_high, settings.money_unit),
    )
    second_row = st.columns(3)
    second_row[0].metric("Worst stress / NAV", _percent(headline.worst_stress_pct_nav))
    second_row[1].metric("Largest VaR driver", headline.top_risk_driver)
    second_row[2].metric("99% exceptions shown", f"{exceptions:,}")
    st.markdown(
        f"<div class='ledger-note'>Largest component-VaR driver: <strong>{html.escape(headline.top_risk_driver)}</strong> "
        f"({_money(headline.top_component_var, settings.money_unit)}). Worst hypothetical scenario: "
        f"<strong>{html.escape(headline.worst_stress)}</strong> "
        f"({_money(headline.worst_stress_loss, settings.money_unit)}, {_percent(headline.worst_stress_pct_nav)} of NAV). "
        f"The backtest remains fixed at 99%, independently of the current-risk confidence selector.</div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        _risk_model_chart(result, settings), width="stretch", key="overview_models"
    )
    st.plotly_chart(
        _portfolio_chart(result, settings, "NAV"), width="stretch", key="overview_nav"
    )


def _render_models(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    _section_intro(
        "Risk model comparison",
        "Compare VaR with Expected Shortfall for the chosen models. Switch between one "
        "confidence level and the complete confidence curve without rerunning calculations.",
    )
    chart_mode = st.radio(
        "Model chart",
        ["Selected confidence", "Confidence curve"],
        horizontal=True,
        key="model_chart_mode",
    )
    st.plotly_chart(
        _risk_model_chart(result, settings, chart_mode),
        width="stretch",
        key="models_current",
    )
    risk = result.table("current_risk")
    risk = risk[risk["model"].isin(settings.models)]
    display = risk.copy()
    display["confidence"] = display["confidence"].map(lambda value: f"{value:.1%}")
    display["var"] = display["var"].map(lambda value: _money(value, settings.money_unit))
    display["es"] = display["es"].map(lambda value: _money(value, settings.money_unit))
    display["var_pct_nav"] = display["var_pct_nav"].map(_percent)
    display["es_pct_nav"] = display["es_pct_nav"].map(_percent)
    display["tail_uplift"] = (risk["es"] / risk["var"] - 1.0).map(_percent)
    st.dataframe(
        display[
            [
                "model",
                "confidence",
                "var",
                "es",
                "tail_uplift",
                "var_pct_nav",
                "es_pct_nav",
            ]
        ].rename(
            columns={
                "model": "Model",
                "confidence": "Confidence",
                "var": "VaR",
                "es": "Expected Shortfall",
                "tail_uplift": "ES above VaR",
                "var_pct_nav": "VaR / NAV",
                "es_pct_nav": "ES / NAV",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    st.subheader("Monte Carlo convergence")
    convergence = result.table("monte_carlo_convergence_summary").copy()
    for column in ["var_abs_difference_pct", "es_abs_difference_pct"]:
        convergence[column] = convergence[column].map(_percent)
    st.dataframe(
        convergence.rename(
            columns={
                "seed": "Seed",
                "comparison_low_paths": "Lower path count",
                "comparison_high_paths": "Higher path count",
                "var_abs_difference_pct": "Absolute VaR difference",
                "es_abs_difference_pct": "Absolute ES difference",
                "var_target_below_2pct": "VaR difference below 2%",
            }
        ),
        hide_index=True,
        width="stretch",
    )


def _render_backtesting(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    _section_intro(
        "Rolling VaR backtesting",
        "Every forecast uses information available through the forecast date and is compared "
        "with next-valid-date hypothetical loss. Red crosses mark exceptions.",
    )
    st.plotly_chart(
        _backtest_chart(result, settings), width="stretch", key="backtesting_timeline"
    )
    score = result.table("backtesting_scorecard")
    score = score[score["model"].isin(settings.models)]
    view = score[
        [
            "model",
            "forecasts",
            "exceptions",
            "expected_exceptions",
            "observed_exception_rate",
            "p_value_uc",
            "p_value_ind",
            "p_value_cc",
            "status",
        ]
    ].copy()
    view["expected_exceptions"] = view["expected_exceptions"].map(lambda value: f"{value:.2f}")
    view["observed_exception_rate"] = view["observed_exception_rate"].map(_percent)
    for column in ["p_value_uc", "p_value_ind", "p_value_cc"]:
        view[column] = view[column].map(lambda value: f"{value:.3f}")
    st.dataframe(
        view.rename(
            columns={
                "model": "Model",
                "forecasts": "Forecasts",
                "exceptions": "Exceptions",
                "expected_exceptions": "Expected exceptions",
                "observed_exception_rate": "Observed rate",
                "p_value_uc": "Kupiec p-value",
                "p_value_ind": "Independence p-value",
                "p_value_cc": "Conditional coverage p-value",
                "status": "Status",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Kupiec coverage and Christoffersen independence results are diagnostics, not proof of "
        "model correctness. The bundled 99% sample has low expected exception counts."
    )


def _render_stress(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    _section_intro(
        "Stress testing",
        "Review deterministic portfolio losses under hypothetical shocks or artificial crisis "
        "fixtures. The selector changes the scenario set; the sidebar changes USD versus NAV view.",
    )
    scenario_set = st.radio(
        "Scenario set",
        ["Hypothetical scenarios", "Artificial crisis fixtures"],
        horizontal=True,
        key="scenario_set",
    )
    table_name = (
        "stress_summary" if scenario_set == "Hypothetical scenarios" else "crisis_replay_summary"
    )
    st.plotly_chart(
        _stress_chart(result, table_name, scenario_set, settings),
        width="stretch",
        key="stress_selected",
    )
    scenarios = result.table(table_name).copy()
    scenarios["scenario_loss"] = scenarios["scenario_loss"].map(
        lambda value: _money(value, settings.money_unit)
    )
    scenarios["loss_pct_nav"] = scenarios["loss_pct_nav"].map(_percent)
    scenario_columns = [
        "scenario_name",
        "horizon",
        "scenario_loss",
        "loss_pct_nav",
        "principal_loss_driver",
    ]
    st.dataframe(
        scenarios[[column for column in scenario_columns if column in scenarios]].rename(
            columns={
                "scenario_name": "Scenario",
                "horizon": "Horizon",
                "scenario_loss": "Loss",
                "loss_pct_nav": "Loss / NAV",
                "principal_loss_driver": "Main driver",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    st.subheader("Volatility and correlation stress")
    distributional = result.table("volatility_correlation_stress").copy()
    distributional["volatility_scale"] = distributional["volatility_scale"].map(
        lambda value: f"{value:.1f}×"
    )
    for column in ["immediate_pnl", "parametric_var", "monte_carlo_var", "monte_carlo_es"]:
        distributional[column] = distributional[column].map(
            lambda value: _money(value, settings.money_unit)
        )
    distributional["parametric_increase"] = distributional["parametric_increase"].map(_percent)
    st.dataframe(
        distributional.rename(
            columns={
                "volatility_scale": "Volatility scale",
                "immediate_pnl": "Immediate P&L",
                "parametric_var": "Parametric VaR",
                "parametric_increase": "VaR increase",
                "monte_carlo_var": "Monte Carlo VaR",
                "monte_carlo_es": "Monte Carlo ES",
            }
        ),
        hide_index=True,
        width="stretch",
    )


def _render_contributions(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    _section_intro(
        "Risk contributions",
        "Trace portfolio risk to positions, asset classes, and factors. Positive component VaR "
        "adds risk; negative values identify diversification or hedge effects.",
    )
    st.plotly_chart(
        _contribution_chart(result, settings),
        width="stretch",
        key="contributions_position",
    )
    left, right = st.columns(2)
    with left:
        st.subheader("By asset class")
        asset_classes = result.table("asset_class_contributions").copy()
        for column in ["component_var", "historical_es_contribution"]:
            asset_classes[column] = asset_classes[column].map(
                lambda value: _money(value, settings.money_unit)
            )
        st.dataframe(
            asset_classes.rename(
                columns={
                    "asset_class": "Asset class",
                    "component_var": "Component VaR",
                    "historical_es_contribution": "Historical ES contribution",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    with right:
        st.subheader("By factor")
        factors = result.table("factor_contributions").copy()
        for column in ["exposure", "component_var", "historical_es_contribution"]:
            factors[column] = factors[column].map(lambda value: _money(value, settings.money_unit))
        factors["component_share"] = factors["component_share"].map(_percent)
        st.dataframe(
            factors[
                [
                    "factor",
                    "exposure",
                    "component_var",
                    "component_share",
                    "historical_es_contribution",
                ]
            ].rename(
                columns={
                    "factor": "Factor",
                    "exposure": "Exposure",
                    "component_var": "Component VaR",
                    "component_share": "Share of VaR",
                    "historical_es_contribution": "Historical ES contribution",
                }
            ),
            hide_index=True,
            width="stretch",
        )


def _render_portfolio(result: MarketRiskAnalysis, settings: ViewSettings) -> None:
    _section_intro(
        "Portfolio and P&L",
        "Change the chart between NAV, daily P&L, and cumulative P&L. The table shows the "
        "closing holdings used for the latest risk calculation.",
    )
    chart_mode = st.radio(
        "Portfolio chart",
        ["NAV", "Daily P&L", "Cumulative P&L"],
        horizontal=True,
        key="portfolio_chart_mode",
    )
    st.plotly_chart(
        _portfolio_chart(result, settings, chart_mode), width="stretch", key="portfolio_nav"
    )
    positions = result.table("position_history")
    latest_date = positions["portfolio_date"].max()
    latest = positions[positions["portfolio_date"] == latest_date].copy()
    st.subheader(f"Closing positions · {latest_date.date()}")
    latest["target_allocation"] = latest.apply(
        lambda row: (
            f"{float(row['target_notional_fraction_of_nav']):.2%} notional"
            if row["instrument_type"] == "fx_forward"
            else f"{float(row['target_weight']):.2%}"
        ),
        axis=1,
    )
    for column in ["end_market_value", "end_notional", "position_pnl"]:
        latest[column] = latest[column].map(lambda value: _money(value, settings.money_unit))
    st.dataframe(
        latest[
            [
                "position_id",
                "name",
                "instrument_type",
                "asset_class",
                "target_allocation",
                "end_market_value",
                "end_notional",
                "position_pnl",
            ]
        ].rename(
            columns={
                "position_id": "Position",
                "name": "Instrument name",
                "instrument_type": "Instrument",
                "asset_class": "Asset class",
                "target_allocation": "Target",
                "end_market_value": "Market value",
                "end_notional": "Notional",
                "position_pnl": "Daily P&L",
            }
        ),
        hide_index=True,
        width="stretch",
    )


def _render_downloads(result: MarketRiskAnalysis) -> None:
    _section_intro(
        "Evidence and downloads",
        "Download the management report, one-page summary, or one ZIP containing every "
        "evidence table, generated figure, and reproducibility record.",
    )
    left, middle, right = st.columns(3)
    left.download_button(
        "Download report",
        data=result.report_text,
        file_name=result.report_filename,
        mime="text/markdown",
        width="stretch",
    )
    middle.download_button(
        "Download one-page summary",
        data=result.summary_text,
        file_name=result.summary_filename,
        mime="text/markdown",
        width="stretch",
    )
    right.download_button(
        "Download complete ZIP",
        data=result.bundle_bytes(),
        file_name=f"market-risk-evidence-{result.headline.as_of_date}.zip",
        mime="application/zip",
        type="primary",
        width="stretch",
    )

    manifest = result.verification_manifest
    gates = pd.DataFrame(
        [
            {
                "gate": name,
                "exit_status": details.get("exit_status"),
                "commit": str(details.get("git_commit") or "")[:7],
                "timestamp": details.get("utc_timestamp"),
            }
            for name, details in manifest.get("gates", {}).items()
        ]
    )
    st.subheader("Verification gates")
    st.dataframe(gates, hide_index=True, width="stretch")
    if result.figures:
        selected = st.selectbox("Inspect generated figure", sorted(result.figures))
        st.image(str(result.figures[selected]), width="stretch")
    else:
        st.info(
            "This custom analysis is calculated in memory. Its complete live tables and "
            "portfolio definition are included in the ZIP download."
        )


def main() -> None:
    _inject_css()
    mode, fred_key, run_requested = _render_source_controls()
    result = _run_analysis(mode, fred_key, run_requested)
    settings = _render_view_controls(result)
    _render_header(result)
    _risk_tape(result, settings)
    tabs = st.tabs(
        [
            "Portfolio builder",
            "Overview",
            "Risk models",
            "Backtesting",
            "Stress tests",
            "Risk contributions",
            "Portfolio & P&L",
            "Evidence & downloads",
        ]
    )
    with tabs[0]:
        _render_portfolio_builder(result, mode, fred_key)
    with tabs[1]:
        _render_overview(result, settings)
    with tabs[2]:
        _render_models(result, settings)
    with tabs[3]:
        _render_backtesting(result, settings)
    with tabs[4]:
        _render_stress(result, settings)
    with tabs[5]:
        _render_contributions(result, settings)
    with tabs[6]:
        _render_portfolio(result, settings)
    with tabs[7]:
        _render_downloads(result)


main()

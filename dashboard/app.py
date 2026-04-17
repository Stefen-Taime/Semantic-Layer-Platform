"""Streamlit dashboard for MetricForge NYC semantic metrics.

Modern, opinionated UI: dark theme, glass cards, plotly charts with auto-
detection (time-series, ranking bar, heatmap) and a clean sidebar for
configuration so the main canvas stays focused on insights.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("METRICFORGE_API_URL", "http://localhost:8000")

# --------------------------------------------------------------------------
# Page configuration and global styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="MetricForge NYC",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CUSTOM_CSS = """
<style>
    :root {
        --mf-bg: #0b1020;
        --mf-surface: rgba(255, 255, 255, 0.04);
        --mf-border: rgba(255, 255, 255, 0.08);
        --mf-accent: #8b5cf6;
        --mf-accent-2: #22d3ee;
        --mf-text: #e5e7eb;
        --mf-muted: #9ca3af;
    }

    html, body, [class*="css"]  {
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
            Roboto, "Helvetica Neue", sans-serif !important;
        letter-spacing: -0.01em;
    }

    .stApp {
        background:
            radial-gradient(1200px 600px at 10% -10%, rgba(139, 92, 246, 0.22), transparent 60%),
            radial-gradient(900px 600px at 110% 10%, rgba(34, 211, 238, 0.18), transparent 60%),
            linear-gradient(180deg, #0b1020 0%, #0b1020 60%, #0a0f1e 100%);
        color: var(--mf-text);
    }

    section[data-testid="stSidebar"] > div {
        background: rgba(10, 15, 30, 0.75);
        backdrop-filter: blur(14px);
        border-right: 1px solid var(--mf-border);
    }

    /* Hero */
    .mf-hero {
        padding: 1.6rem 1.8rem;
        border-radius: 18px;
        background: var(--mf-surface);
        border: 1px solid var(--mf-border);
        backdrop-filter: blur(16px);
        margin-bottom: 1.25rem;
    }
    .mf-hero h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.25rem 0;
        background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 50%, #67e8f9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .mf-hero p {
        margin: 0;
        color: var(--mf-muted);
        font-size: 0.95rem;
    }

    /* KPI cards */
    .mf-kpi {
        padding: 1.1rem 1.3rem;
        border-radius: 16px;
        background: var(--mf-surface);
        border: 1px solid var(--mf-border);
        backdrop-filter: blur(12px);
        height: 100%;
        transition: transform 0.18s ease, border-color 0.18s ease;
    }
    .mf-kpi:hover {
        transform: translateY(-2px);
        border-color: rgba(139, 92, 246, 0.5);
    }
    .mf-kpi .label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--mf-muted);
        margin-bottom: 0.35rem;
    }
    .mf-kpi .value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #ffffff;
    }
    .mf-kpi .sub {
        font-size: 0.8rem;
        color: var(--mf-muted);
        margin-top: 0.2rem;
    }

    /* Engine pill */
    .mf-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.4);
        font-size: 0.72rem;
        font-weight: 600;
        color: #e9d5ff;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .mf-pill.druid { background: rgba(34, 211, 238, 0.15); border-color: rgba(34, 211, 238, 0.4); color: #a5f3fc; }
    .mf-pill.trino { background: rgba(251, 191, 36, 0.12); border-color: rgba(251, 191, 36, 0.35); color: #fde68a; }
    .mf-pill.spark { background: rgba(249, 115, 22, 0.12); border-color: rgba(249, 115, 22, 0.35); color: #fed7aa; }

    /* Tabs polish */
    button[data-baseweb="tab"] {
        font-weight: 600;
        color: var(--mf-muted) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
    }
    div[data-baseweb="tab-highlight"] {
        background: linear-gradient(90deg, var(--mf-accent), var(--mf-accent-2)) !important;
        height: 3px !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"], .stFormSubmitButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #22d3ee 100%);
        color: #0b1020;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 0.55rem 1.1rem;
        box-shadow: 0 8px 24px -10px rgba(139, 92, 246, 0.6);
    }
    .stFormSubmitButton > button:hover { filter: brightness(1.08); }

    /* Inputs */
    input, textarea, select, .stTextInput > div > div > input {
        border-radius: 10px !important;
    }

    /* Hide default Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* Code block */
    .stCodeBlock {
        border-radius: 12px;
        border: 1px solid var(--mf-border);
    }
</style>
"""
st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def fetch_json_cached(method: str, url: str, payload_key: str | None = None) -> dict[str, Any]:
    """Cache GET calls for quickly re-rendering the UI."""
    response = requests.request(method=method, url=url, timeout=60)
    response.raise_for_status()
    return response.json()


def fetch_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call the API and return a JSON payload (no caching for POSTs)."""
    response = requests.request(method=method, url=url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def engine_pill(engine: str) -> str:
    cls = engine.lower() if engine else ""
    return f'<span class="mf-pill {cls}">{engine}</span>'


def fmt_number(value: Any) -> str:
    """Humanize large numbers for KPI cards."""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return str(value)
    abs_x = abs(x)
    if abs_x >= 1_000_000_000:
        return f"{x / 1_000_000_000:.2f}B"
    if abs_x >= 1_000_000:
        return f"{x / 1_000_000:.2f}M"
    if abs_x >= 1_000:
        return f"{x / 1_000:.1f}K"
    if abs_x >= 1 or x == 0:
        return f"{x:,.2f}" if x != int(x) else f"{int(x):,}"
    return f"{x:.4f}"


# --------------------------------------------------------------------------
# Sidebar: connection + navigation
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1.2rem;">
            <div style="width:38px;height:38px;border-radius:10px;
                background:linear-gradient(135deg,#8b5cf6 0%,#22d3ee 100%);
                display:flex;align-items:center;justify-content:center;
                font-size:20px;">🗽</div>
            <div>
                <div style="font-weight:700;font-size:1.05rem;color:#fff;">MetricForge</div>
                <div style="font-size:0.72rem;color:#9ca3af;letter-spacing:0.08em;
                    text-transform:uppercase;">NYC semantic layer</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    api_base_url = st.text_input("API Base URL", value=API_BASE_URL, key="api_base_url")

    health_col1, health_col2 = st.columns(2)
    api_ok = False
    try:
        health_payload = fetch_json_cached("GET", f"{api_base_url}/health")
        api_ok = health_payload.get("status") == "ok"
    except requests.RequestException:
        api_ok = False

    with health_col1:
        st.markdown(
            f"<div style='font-size:0.8rem;color:#9ca3af;'>API</div>"
            f"<div style='font-weight:600;color:{'#22d3ee' if api_ok else '#f87171'};'>"
            f"{'● online' if api_ok else '● offline'}</div>",
            unsafe_allow_html=True,
        )
    with health_col2:
        if st.button("Refresh catalog", use_container_width=True):
            fetch_json_cached.clear()
            st.rerun()


# --------------------------------------------------------------------------
# Load catalog
# --------------------------------------------------------------------------
metrics_payload: dict[str, Any] = {"metrics": []}
dimensions_payload: dict[str, Any] = {"dimensions": []}
engines_payload: dict[str, Any] = {
    "available_engines": ["spark", "trino", "druid"],
    "default_engine": "spark",
}
catalog_error: str | None = None

try:
    metrics_payload = fetch_json_cached("GET", f"{api_base_url}/metrics")
    dimensions_payload = fetch_json_cached("GET", f"{api_base_url}/dimensions")
    engines_payload = fetch_json_cached("GET", f"{api_base_url}/engines")
except requests.RequestException as exc:
    catalog_error = f"Unable to reach the API: {exc}"

metrics = metrics_payload.get("metrics", [])
dimensions = dimensions_payload.get("dimensions", [])
available_engines = engines_payload.get("available_engines", ["spark", "trino", "druid"])
default_engine = engines_payload.get("default_engine", "spark")


# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="mf-hero">
        <h1>MetricForge NYC</h1>
        <p>Mini semantic layer / metrics platform inspired by Airbnb Minerva — governed metrics served on Spark, Trino and Druid.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top-line KPIs (from catalog metadata, no live query)
kpi_cols = st.columns(4)
kpi_cols[0].markdown(
    f"<div class='mf-kpi'><div class='label'>Metrics</div>"
    f"<div class='value'>{len(metrics)}</div>"
    f"<div class='sub'>Governed definitions</div></div>",
    unsafe_allow_html=True,
)
kpi_cols[1].markdown(
    f"<div class='mf-kpi'><div class='label'>Dimensions</div>"
    f"<div class='value'>{len(dimensions)}</div>"
    f"<div class='sub'>Shared allowed list</div></div>",
    unsafe_allow_html=True,
)
kpi_cols[2].markdown(
    f"<div class='mf-kpi'><div class='label'>Engines</div>"
    f"<div class='value'>{len(available_engines)}</div>"
    f"<div class='sub'>{', '.join(available_engines)}</div></div>",
    unsafe_allow_html=True,
)
kpi_cols[3].markdown(
    f"<div class='mf-kpi'><div class='label'>Default engine</div>"
    f"<div class='value'>{default_engine}</div>"
    f"<div class='sub'>Configurable per request</div></div>",
    unsafe_allow_html=True,
)

if catalog_error:
    st.error(catalog_error)
    st.stop()


# --------------------------------------------------------------------------
# Sidebar: query builder
# --------------------------------------------------------------------------
metrics_by_name = {metric["name"]: metric for metric in metrics}
all_dimension_names = [dimension["name"] for dimension in dimensions]

if not metrics or not dimensions:
    st.info("The FastAPI service returned an empty catalog. Check the semantic layer mounts.")
    st.stop()

with st.sidebar:
    st.markdown("### Query")
    selected_metric = st.selectbox(
        "Metric",
        options=list(metrics_by_name),
        help="Governed metric defined in metrics.yml.",
    )
    metric_definition = metrics_by_name[selected_metric]
    allowed_dimensions = metric_definition.get("allowed_dimensions", all_dimension_names) or all_dimension_names

    selected_group_by = st.multiselect(
        "Group by",
        options=allowed_dimensions,
        default=[],
        help="Dimensions to slice the metric.",
    )

    selected_engine = st.radio(
        "Engine",
        options=available_engines,
        index=available_engines.index(default_engine) if default_engine in available_engines else 0,
        horizontal=True,
    )

    selected_time_grain = st.selectbox(
        "Time grain",
        options=["none", "day", "week", "month"],
        index=0,
    )
    date_cols = st.columns(2)
    with date_cols[0]:
        start_date = st.date_input("From", value=date(2026, 1, 1))
    with date_cols[1]:
        end_date = st.date_input("To", value=date(2026, 3, 1))

    with st.expander("Advanced", expanded=False):
        order_by_options = ["metric_date", selected_metric] + list(allowed_dimensions)
        seen: set[str] = set()
        order_by_unique: list[str] = []
        for option in order_by_options:
            if option and option not in seen:
                seen.add(option)
                order_by_unique.append(option)

        order_by_columns = st.multiselect(
            "Order by",
            options=order_by_unique,
            default=[selected_metric] if selected_metric in order_by_unique else [],
        )
        order_by_direction = st.radio(
            "Direction",
            options=["desc", "asc"],
            index=0,
            horizontal=True,
        )
        row_limit = st.number_input(
            "Row limit",
            min_value=1,
            max_value=10000,
            value=100,
            step=10,
        )
        execute_query_flag = st.checkbox("Execute query (run SQL)", value=True)

    submit = st.button("Run query", type="primary", use_container_width=True)


# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
explore_tab, catalog_tab = st.tabs(["Explore", "Catalog"])

with catalog_tab:
    st.markdown("#### Metric catalog")
    metrics_df = pd.DataFrame(metrics)
    if not metrics_df.empty:
        display_cols = [c for c in ["name", "label", "type", "owner", "description", "allowed_dimensions"] if c in metrics_df.columns]
        st.dataframe(
            metrics_df[display_cols] if display_cols else metrics_df,
            use_container_width=True,
            hide_index=True,
        )
    st.markdown("#### Dimensions")
    dims_df = pd.DataFrame(dimensions)
    if not dims_df.empty:
        dim_cols = [c for c in ["name", "label", "type", "column", "description"] if c in dims_df.columns]
        st.dataframe(
            dims_df[dim_cols] if dim_cols else dims_df,
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------------------------------
# Chart helpers
# --------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"
ACCENT_SEQUENCE = [
    "#8b5cf6", "#22d3ee", "#f472b6", "#fbbf24", "#34d399",
    "#60a5fa", "#f87171", "#a78bfa", "#2dd4bf", "#fb923c",
]


def _style_figure(fig: go.Figure) -> go.Figure:
    """Apply a consistent dark / glass look to plotly figures."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#e5e7eb", size=13),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            bgcolor="rgba(10,15,30,0.4)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#0b1020",
            bordercolor="#8b5cf6",
            font=dict(color="#fff", family="Inter"),
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    return fig


def build_auto_chart(df: pd.DataFrame, metric_col: str, group_cols: list[str]) -> go.Figure | None:
    """Pick the most meaningful chart given the query shape."""
    if df.empty or metric_col not in df.columns:
        return None

    has_time = "metric_date" in df.columns
    non_time_groups = [c for c in group_cols if c != "metric_date"]

    # 1. Time-series (with optional single categorical break-down)
    if has_time:
        working = df.copy()
        working["metric_date"] = pd.to_datetime(working["metric_date"], errors="coerce")
        color_col = non_time_groups[0] if len(non_time_groups) == 1 else None
        fig = px.line(
            working.sort_values("metric_date"),
            x="metric_date",
            y=metric_col,
            color=color_col,
            markers=True,
            color_discrete_sequence=ACCENT_SEQUENCE,
            title=None,
        )
        fig.update_traces(line=dict(width=3))
        return _style_figure(fig)

    # 2. Two categorical dimensions → heatmap
    if len(non_time_groups) == 2:
        dim_x, dim_y = non_time_groups
        pivot = df.pivot_table(index=dim_y, columns=dim_x, values=metric_col, aggfunc="sum").fillna(0)
        fig = px.imshow(
            pivot,
            aspect="auto",
            color_continuous_scale=[[0, "#0b1020"], [0.4, "#4c1d95"], [0.8, "#8b5cf6"], [1, "#22d3ee"]],
            labels=dict(color=metric_col),
        )
        return _style_figure(fig)

    # 3. Single categorical → ranking bar
    if len(non_time_groups) == 1:
        dim = non_time_groups[0]
        top = df.sort_values(metric_col, ascending=False).head(20)
        fig = px.bar(
            top,
            x=metric_col,
            y=dim,
            orientation="h",
            color=metric_col,
            color_continuous_scale=[[0, "#4c1d95"], [1, "#22d3ee"]],
        )
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        return _style_figure(fig)

    # 4. No group dimensions → simple gauge-style indicator
    value = df[metric_col].iloc[0] if not df.empty else 0
    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=float(value),
            number=dict(font=dict(size=64, color="#ffffff"), valueformat=",.2f"),
            domain=dict(x=[0, 1], y=[0, 1]),
        )
    )
    return _style_figure(fig)


def build_summary_stats(df: pd.DataFrame, metric_col: str) -> dict[str, float]:
    """Summary stats for KPI cards on top of the result table."""
    if metric_col not in df.columns or df.empty:
        return {}
    series = pd.to_numeric(df[metric_col], errors="coerce").dropna()
    if series.empty:
        return {}
    return {
        "total": float(series.sum()),
        "mean": float(series.mean()),
        "max": float(series.max()),
        "min": float(series.min()),
        "rows": int(len(df)),
    }


# --------------------------------------------------------------------------
# Explore tab
# --------------------------------------------------------------------------
with explore_tab:
    if not submit:
        st.markdown(
            """
            <div class='mf-kpi' style='text-align:center;padding:3rem 1.5rem;'>
                <div class='label'>Ready when you are</div>
                <div style='font-size:1.4rem;font-weight:600;margin-top:0.4rem;'>
                    Configure the query in the sidebar and press
                    <span style='color:#22d3ee;'>Run query</span>.
                </div>
                <div class='sub' style='margin-top:0.6rem;'>
                    The chart type is auto-selected from the query shape — time-series, ranking bar or heatmap.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        payload: dict[str, Any] = {
            "metric": selected_metric,
            "group_by": selected_group_by,
            "time_grain": None if selected_time_grain == "none" else selected_time_grain,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "filters": {},
            "execute": execute_query_flag,
            "engine": selected_engine,
            "limit": int(row_limit),
        }
        if order_by_columns:
            payload["order_by"] = [
                {"column": column, "direction": order_by_direction}
                for column in order_by_columns
            ]

        with st.spinner("Running query…"):
            try:
                result = fetch_json("POST", f"{api_base_url}/query", payload=payload)
            except requests.HTTPError as exc:
                error_body = exc.response.text if exc.response is not None else str(exc)
                st.error(error_body)
                st.stop()
            except requests.RequestException as exc:
                st.error(f"API request failed: {exc}")
                st.stop()

        returned_engine = result.get("engine", selected_engine)
        sql_text = result.get("sql", "")
        data = result.get("data", [])

        # Header strip
        strip_cols = st.columns([2, 1, 1, 1])
        with strip_cols[0]:
            st.markdown(
                f"<div style='font-size:0.8rem;color:#9ca3af;text-transform:uppercase;"
                f"letter-spacing:0.08em;'>Metric</div>"
                f"<div style='font-size:1.35rem;font-weight:700;'>{selected_metric}</div>",
                unsafe_allow_html=True,
            )
        with strip_cols[1]:
            st.markdown(
                f"<div style='font-size:0.8rem;color:#9ca3af;text-transform:uppercase;"
                f"letter-spacing:0.08em;'>Engine</div>"
                f"<div style='margin-top:0.3rem;'>{engine_pill(returned_engine)}</div>",
                unsafe_allow_html=True,
            )
        with strip_cols[2]:
            grain_label = selected_time_grain if selected_time_grain != "none" else "—"
            st.markdown(
                f"<div style='font-size:0.8rem;color:#9ca3af;text-transform:uppercase;"
                f"letter-spacing:0.08em;'>Grain</div>"
                f"<div style='font-size:1.15rem;font-weight:600;'>{grain_label}</div>",
                unsafe_allow_html=True,
            )
        with strip_cols[3]:
            st.markdown(
                f"<div style='font-size:0.8rem;color:#9ca3af;text-transform:uppercase;"
                f"letter-spacing:0.08em;'>Rows</div>"
                f"<div style='font-size:1.15rem;font-weight:600;'>{len(data)}</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        if not execute_query_flag:
            st.info("SQL generated without execution. Toggle `Execute query` in the sidebar to run it.")
            st.markdown("#### Generated SQL")
            st.code(sql_text, language="sql")
        else:
            df = pd.DataFrame(data)
            if df.empty:
                st.warning("The query returned no rows for the selected window.")
            else:
                stats = build_summary_stats(df, selected_metric)
                if stats:
                    stat_cols = st.columns(4)
                    stat_cols[0].markdown(
                        f"<div class='mf-kpi'><div class='label'>Total</div>"
                        f"<div class='value'>{fmt_number(stats['total'])}</div>"
                        f"<div class='sub'>Σ {selected_metric}</div></div>",
                        unsafe_allow_html=True,
                    )
                    stat_cols[1].markdown(
                        f"<div class='mf-kpi'><div class='label'>Average</div>"
                        f"<div class='value'>{fmt_number(stats['mean'])}</div>"
                        f"<div class='sub'>Mean across {stats['rows']} rows</div></div>",
                        unsafe_allow_html=True,
                    )
                    stat_cols[2].markdown(
                        f"<div class='mf-kpi'><div class='label'>Max</div>"
                        f"<div class='value'>{fmt_number(stats['max'])}</div>"
                        f"<div class='sub'>Top bucket</div></div>",
                        unsafe_allow_html=True,
                    )
                    stat_cols[3].markdown(
                        f"<div class='mf-kpi'><div class='label'>Min</div>"
                        f"<div class='value'>{fmt_number(stats['min'])}</div>"
                        f"<div class='sub'>Bottom bucket</div></div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("#### Visualisation")
                chart = build_auto_chart(df, selected_metric, selected_group_by)
                if chart is not None:
                    st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("No chart available for this query shape — inspect the table below.")

                data_col, sql_col = st.columns([1.3, 1])
                with data_col:
                    st.markdown("#### Data")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    csv_bytes = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download CSV",
                        data=csv_bytes,
                        file_name=f"{selected_metric}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with sql_col:
                    st.markdown("#### Generated SQL")
                    st.code(sql_text, language="sql")

"""Streamlit dashboard for MetricForge NYC semantic metrics."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import requests
import streamlit as st

API_BASE_URL = os.getenv("METRICFORGE_API_URL", "http://localhost:8000")


def fetch_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call the API and return a JSON payload."""
    response = requests.request(method=method, url=url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="MetricForge NYC", layout="wide")
st.title("MetricForge NYC")
st.caption("Mini semantic layer / metrics platform inspired by Airbnb Minerva.")

api_base_url = st.text_input("API Base URL", value=API_BASE_URL)

metrics_payload: dict[str, Any] = {"metrics": []}
dimensions_payload: dict[str, Any] = {"dimensions": []}
engines_payload: dict[str, Any] = {
    "available_engines": ["spark", "trino", "druid"],
    "default_engine": "spark",
}
catalog_error: str | None = None

try:
    metrics_payload = fetch_json("GET", f"{api_base_url}/metrics")
    dimensions_payload = fetch_json("GET", f"{api_base_url}/dimensions")
    engines_payload = fetch_json("GET", f"{api_base_url}/engines")
except requests.RequestException as exc:
    catalog_error = f"Unable to reach the API: {exc}"

metrics = metrics_payload.get("metrics", [])
dimensions = dimensions_payload.get("dimensions", [])
available_engines = engines_payload.get("available_engines", ["spark", "trino", "druid"])
default_engine = engines_payload.get("default_engine", "spark")

st.subheader("Metric Catalog")
if catalog_error:
    st.error(catalog_error)
else:
    st.dataframe(metrics, use_container_width=True)

st.subheader("Query Builder")
if not metrics or not dimensions:
    st.info("Start the FastAPI service to load the metric catalog.")
else:
    metrics_by_name = {metric["name"]: metric for metric in metrics}
    all_dimension_names = [dimension["name"] for dimension in dimensions]

    with st.form("query_builder"):
        selected_metric = st.selectbox("Metric", options=list(metrics_by_name))
        metric_definition = metrics_by_name[selected_metric]
        allowed_dimensions = metric_definition.get("allowed_dimensions", all_dimension_names)

        selected_group_by = st.multiselect(
            "Group By",
            options=allowed_dimensions,
            default=[],
        )
        selected_engine = st.selectbox(
            "Execution Engine",
            options=available_engines,
            index=available_engines.index(default_engine) if default_engine in available_engines else 0,
        )
        selected_time_grain = st.selectbox(
            "Time Grain",
            options=["none", "day", "week", "month"],
            index=0,
        )
        start_date = st.date_input("Start Date", value=date(2024, 1, 1))
        end_date = st.date_input("End Date", value=date(2024, 2, 1))
        execute_query_flag = st.checkbox("Execute Query", value=False)
        submit = st.form_submit_button("Run Query")

    st.subheader("Results")
    if submit:
        payload = {
            "metric": selected_metric,
            "group_by": selected_group_by,
            "time_grain": None if selected_time_grain == "none" else selected_time_grain,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "filters": {},
            "execute": execute_query_flag,
            "engine": selected_engine,
        }
        try:
            result = fetch_json("POST", f"{api_base_url}/query", payload=payload)
            st.write(f"Engine: `{result.get('engine', selected_engine)}`")
            st.code(result["sql"], language="sql")
            if execute_query_flag:
                st.dataframe(result.get("data", []), use_container_width=True)
            else:
                st.info("SQL generated without execution.")
        except requests.HTTPError as exc:
            error_body = exc.response.text if exc.response is not None else str(exc)
            st.error(error_body)
        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")

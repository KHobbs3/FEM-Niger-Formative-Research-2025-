"""Phone Pulse — Respondents overview page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import load_pp_respondents_profile

FEM_ORANGE = "#C1693A"
FEM_BROWN  = "#8B5E45"
FEM_NAVY   = "#2E3F52"
FEM_STEEL  = "#5A6E7F"
FEM_TAUPE  = "#7A7068"
GROUP_COLORS = {"Using FP": FEM_NAVY, "Not using FP": FEM_ORANGE, "All": FEM_TAUPE}

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _load() -> pd.DataFrame:
    return load_pp_respondents_profile()


def _hbar(df: pd.DataFrame, title: str, color: str = FEM_NAVY) -> go.Figure:
    df = df.sort_values("pct")
    fig = go.Figure(go.Bar(
        x=df["pct"], y=df["category"], orientation="h",
        marker_color=color, text=df["pct"].map(lambda v: f"{v:.0f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        **_CHART,
        title=title, xaxis_title="% of respondents", xaxis_range=[0, 110],
        height=max(200, 50 * len(df) + 80),
        margin=dict(l=10, r=30, t=40, b=10),
    )
    fig.update_yaxes(tickfont=dict(size=12))
    return fig


def render() -> None:
    df = _load()

    total_row = df[df["variable"] == "_total"]
    n_total = int(total_row["count"].iloc[0]) if not total_row.empty else "—"

    st.markdown(f"### Phone Pulse Survey — Respondents")
    st.metric("Total respondents (quality-filtered)", n_total)
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        gender = df[df["variable"] == "gender"]
        if not gender.empty:
            fig = _hbar(gender, "Gender", FEM_BROWN)
            st.plotly_chart(fig, use_container_width=True)

        fp = df[df["variable"] == "fp_use"]
        if not fp.empty:
            fig = _hbar(fp, "Current FP use (fpbeh_fpnow)", FEM_NAVY)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        radio = df[df["variable"] == "radio"]
        if not radio.empty:
            fig = _hbar(radio, "Radio listenership", FEM_STEEL)
            st.plotly_chart(fig, use_container_width=True)

        pc = df[df["variable"] == "preg_chance"]
        if not pc.empty:
            fig = _hbar(pc, "Perceived pregnancy chance (fpbeh_pregchance)", FEM_ORANGE)
            st.plotly_chart(fig, use_container_width=True)

    # Village table (suppressed if n < 5)
    village = df[df["variable"] == "village"].copy()
    if not village.empty:
        st.markdown("#### Distribution by village")
        st.caption("Villages with fewer than 5 respondents are suppressed for privacy.")
        village_disp = village[["category", "count", "pct"]].rename(
            columns={"category": "Village", "count": "N", "pct": "%"}
        ).sort_values("N", ascending=False).reset_index(drop=True)
        st.dataframe(village_disp, use_container_width=True, hide_index=True)

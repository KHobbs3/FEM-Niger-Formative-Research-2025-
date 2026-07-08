"""Phone Pulse — Radio listenership page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import (
    load_pp_radio_any,
    load_pp_radio_uptake,
    load_pp_radio_days,
    load_pp_radio_hours,
    load_pp_radio_stations,
)

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"
FEM_BROWN  = "#8B5E45"
FEM_STEEL  = "#5A6E7F"
GROUP_COLORS = {"Using FP": FEM_NAVY, "Not using FP": FEM_ORANGE, "All": FEM_TAUPE}
GROUP_ORDER  = ["Using FP", "Not using FP", "All"]

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _grouped_hbar(df: pd.DataFrame, title: str,
                  xmax: float = 100, caption: str = "") -> None:
    fig = go.Figure()
    n_cats = df["category"].nunique()
    for grp in GROUP_ORDER:
        sub = df[df["group"] == grp].sort_values("pct")
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["pct"], y=sub["category"], orientation="h",
            name=grp, marker_color=GROUP_COLORS[grp],
            text=sub["pct"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
        ))
    fig.update_layout(
        **_CHART,
        title=title, barmode="group",
        xaxis_title="% of respondents",
        xaxis_range=[0, xmax + 15],
        height=max(250, 35 * n_cats * len(GROUP_ORDER) + 100),
        margin=dict(l=10, r=30, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
    if caption:
        st.caption(caption)


def render() -> None:
    st.markdown("### Phone Pulse — Radio Listenership")
    st.caption(
        "Results broken down by FP use status. "
        "Base for station / hours / days charts: radio listeners only."
    )
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Listenership", "FP content heard", "Listening days",
        "Daily hours", "Stations"
    ])

    with tab1:
        df = load_pp_radio_any()
        _grouped_hbar(df, "Radio listenership",
                      caption="Base: all respondents.")

    with tab2:
        df = load_pp_radio_uptake()
        _grouped_hbar(df, "Heard FP content on radio",
                      caption="Base: all respondents.")

    with tab3:
        df = load_pp_radio_days()
        _grouped_hbar(df, "Days of the week listeners tune in",
                      caption="Base: radio listeners only.")

    with tab4:
        df = load_pp_radio_hours()
        # Vertical bar for ordered buckets
        fig = go.Figure()
        hour_order = ["<1 hr", "1 hr", "2 hrs", "3 hrs", "4 hrs", "5–6 hrs", "7+ hrs"]
        for grp in GROUP_ORDER:
            sub = df[df["group"] == grp].copy()
            sub["_ord"] = sub["category"].map({v: i for i, v in enumerate(hour_order)})
            sub = sub.sort_values("_ord")
            if sub.empty:
                continue
            fig.add_trace(go.Bar(
                x=sub["category"], y=sub["pct"],
                name=grp, marker_color=GROUP_COLORS[grp],
                text=sub["pct"].map(lambda v: f"{v:.0f}%"),
                textposition="outside",
            ))
        fig.update_layout(
            **_CHART,
            title="Daily listening hours (among radio listeners)",
            barmode="group", yaxis_title="% of listeners",
            yaxis_range=[0, 80],
            height=380,
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Base: radio listeners only.")

    with tab5:
        df = load_pp_radio_stations()
        _grouped_hbar(df, "Station listenership (among radio listeners)",
                      caption="Base: radio listeners only. Placebo station is a control stimulus.")

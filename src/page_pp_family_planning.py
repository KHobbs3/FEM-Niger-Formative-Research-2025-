"""Phone Pulse — Family Planning behaviour page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import (
    load_pp_fp_awareness,
    load_pp_fp_method_used,
    load_pp_fp_whynot,
    load_pp_fp_preg_chance,
)

FEM_ORANGE = "#C1693A"
FEM_BROWN  = "#8B5E45"
FEM_NAVY   = "#2E3F52"
FEM_STEEL  = "#5A6E7F"
FEM_TAUPE  = "#7A7068"

SPLIT_OPTIONS = {
    "FP use status": {
        "split_by": "fp_use",
        "order":  ["Using FP", "Not using FP", "All"],
        "colors": {"Using FP": FEM_NAVY, "Not using FP": FEM_ORANGE, "All": FEM_TAUPE},
    },
    "Gender": {
        "split_by": "gender",
        "order":  ["Male", "Female", "All"],
        "colors": {"Male": FEM_STEEL, "Female": FEM_BROWN, "All": FEM_TAUPE},
    },
}

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _filter_split(df: pd.DataFrame, split_by: str) -> pd.DataFrame:
    if "split_by" not in df.columns:
        return df
    return df[df["split_by"] == split_by]


def _grouped_hbar(df: pd.DataFrame, title: str, group_order: list, group_colors: dict,
                  xmax: float = 100) -> go.Figure:
    """Horizontal bar chart with one trace per group."""
    fig = go.Figure()
    for grp in group_order:
        sub = df[df["group"] == grp].sort_values("pct")
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["pct"], y=sub["category"], orientation="h",
            name=grp, marker_color=group_colors[grp],
            text=sub["pct"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
        ))
    n_cats = df["category"].nunique()
    fig.update_layout(
        **_CHART,
        title=title, barmode="group",
        xaxis_title="% of respondents in group",
        xaxis_range=[0, xmax + 15],
        height=max(250, 35 * n_cats * 3 + 100),
        margin=dict(l=10, r=30, t=78, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
    )
    return fig


def render() -> None:
    st.markdown("### Phone Pulse — Family Planning Behaviour")

    view = st.radio("View by", list(SPLIT_OPTIONS.keys()), horizontal=True, key="pp_fp_split")
    split = SPLIT_OPTIONS[view]
    split_by, order, colors = split["split_by"], split["order"], split["colors"]

    st.caption(f"Broken down by {view.lower()}.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Method awareness", "Methods used", "Reasons for non-use", "Pregnancy chance"
    ])

    with tab1:
        df = _filter_split(load_pp_fp_awareness(), split_by)
        if df.empty:
            st.info("No data available.")
        else:
            fig = _grouped_hbar(df, "Awareness of FP methods (% who have heard of each)", order, colors)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Base: all respondents in each group.")

    with tab2:
        df = load_pp_fp_method_used()
        if df.empty:
            st.info("No data — only applicable to current FP users.")
        else:
            df = df.sort_values("pct", ascending=True)
            fig = go.Figure(go.Bar(
                x=df["pct"], y=df["category"], orientation="h",
                marker_color=FEM_NAVY,
                text=df["pct"].map(lambda v: f"{v:.0f}%"),
                textposition="outside",
            ))
            fig.update_layout(
                **_CHART,
                title="Methods currently used (among FP users)",
                xaxis_title="% of FP users",
                xaxis_range=[0, 115],
                height=max(250, 35 * len(df) + 80),
                margin=dict(l=10, r=30, t=50, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Base: respondents currently using FP (fpbeh_fpnow = 1). "
                "Not sliceable by view above — this export is FP-users-only."
            )

    with tab3:
        df = _filter_split(load_pp_fp_whynot(), split_by)
        if df.empty:
            st.info("No data available.")
        else:
            fig = _grouped_hbar(df, "Reasons for not using FP (% citing each reason)", order, colors)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Base: all respondents in each group. "
                "Respondents may cite multiple reasons."
            )

    with tab4:
        df = _filter_split(load_pp_fp_preg_chance(), split_by)
        if df.empty:
            st.info("No data available.")
        else:
            # Order from most to least likely
            cat_order = ["Very likely", "Somewhat likely", "Neither", "Unlikely", "Very unlikely"]
            def _order(d, col="category"):
                d = d.copy()
                d["_ord"] = d[col].map({v: i for i, v in enumerate(cat_order)})
                return d.sort_values("_ord").drop(columns="_ord")

            fig = go.Figure()
            for grp in order:
                sub = _order(df[df["group"] == grp])
                if sub.empty:
                    continue
                fig.add_trace(go.Bar(
                    x=sub["category"], y=sub["pct"],
                    name=grp, marker_color=colors[grp],
                    text=sub["pct"].map(lambda v: f"{v:.0f}%"),
                    textposition="outside",
                ))
            fig.update_layout(
                **_CHART,
                title="Perceived likelihood of pregnancy (if not using FP)",
                barmode="group", yaxis_title="% of respondents",
                yaxis_range=[0, 80],
                height=405,
                margin=dict(l=10, r=10, t=78, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.15),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Scale: 1 = Very likely → 5 = Very unlikely (inverted on x-axis).")

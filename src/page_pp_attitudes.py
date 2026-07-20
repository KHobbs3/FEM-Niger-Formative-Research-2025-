"""Phone Pulse — Attitudes toward FP page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import load_pp_attitudes

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"
FEM_BROWN  = "#8B5E45"
FEM_STEEL  = "#5A6E7F"

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

SCALE_NOTE = (
    "Scale: 0 = Strongly disagree → 4 = Strongly agree. "
    "Higher scores indicate stronger agreement with the statement."
)


def _filter_split(df: pd.DataFrame, split_by: str) -> pd.DataFrame:
    if "split_by" not in df.columns:
        return df
    return df[df["split_by"] == split_by]


def _dot_chart(df: pd.DataFrame, title: str, group_order: list, group_colors: dict) -> go.Figure:
    """Lollipop-style dot chart: one row per attitude item, dots per group."""
    fig = go.Figure()
    for grp in group_order:
        sub = df[df["group"] == grp]
        fig.add_trace(go.Scatter(
            x=sub["mean"], y=sub["label"],
            mode="markers+text", name=grp,
            marker=dict(color=group_colors[grp], size=12),
            text=sub["mean"].map(lambda v: f"{v:.2f}" if pd.notna(v) else ""),
            textposition="middle right",
        ))
    fig.update_layout(
        **_CHART,
        title=title,
        xaxis=dict(title="Mean agreement score (0–4)", range=[-0.2, 5.5]),
        height=max(300, 50 * df["label"].nunique() + 120),
        margin=dict(l=10, r=10, t=78, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.15),
    )
    fig.add_vline(x=2, line_dash="dot", line_color="#aaa")   # neutral midpoint
    return fig


def render() -> None:
    try:
        df = load_pp_attitudes()
    except Exception:
        st.error("Attitude data not found. Re-run export_pp_app_data.py.")
        return

    st.markdown("### Phone Pulse — Attitudes toward Family Planning")

    view = st.radio("View by", list(SPLIT_OPTIONS.keys()), horizontal=True, key="pp_attitudes_split")
    split = SPLIT_OPTIONS[view]
    split_by, order, colors = split["split_by"], split["order"], split["colors"]
    df = _filter_split(df, split_by)

    st.caption(
        "Mean agreement scores on 8 attitude statements, rated 0–4 (0 = Strongly disagree, "
        f"4 = Strongly agree), broken down by {view.lower()}. Dashed line at 2 = neutral."
    )
    st.markdown("---")

    tab_self, tab_spouse, tab_commu = st.tabs(
        ["Own attitudes", "Perceived spouse attitudes", "Perceived community attitudes"]
    )

    for tab, perspective, label in [
        (tab_self,  "self",      "own"),
        (tab_spouse,"spouse",   "spouse's"),
        (tab_commu, "community","community's"),
    ]:
        with tab:
            sub = df[df["perspective"] == perspective].dropna(subset=["mean"])
            if sub.empty:
                st.info(f"No data available for {label} attitudes.")
                continue

            fig = _dot_chart(sub, f"Mean agreement — {label.capitalize()} attitudes", order, colors)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(SCALE_NOTE)

            # Summary table
            pivot = sub.pivot_table(
                index="label", columns="group", values="mean", aggfunc="first"
            ).reset_index()
            col_order = ["label"] + [g for g in order if g in pivot.columns]
            pivot = pivot[col_order]
            for g in order:
                if g in pivot.columns:
                    pivot[g] = pivot[g].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
            pivot = pivot.rename(columns={"label": "Statement"})
            st.dataframe(pivot, use_container_width=True, hide_index=True)

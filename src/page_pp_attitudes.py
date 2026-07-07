"""Phone Pulse — Attitudes toward FP page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"
GROUP_COLORS = {"Using FP": FEM_NAVY, "Not using FP": FEM_ORANGE, "All": FEM_TAUPE}
GROUP_ORDER  = ["Using FP", "Not using FP", "All"]

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

SCALE_NOTE = (
    "Scale: 0 = Strongly disagree → 4 = Strongly agree. "
    "Higher scores indicate stronger agreement with the statement."
)


def _dot_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Lollipop-style dot chart: one row per attitude item, dots per group."""
    fig = go.Figure()
    for grp in GROUP_ORDER:
        sub = df[df["group"] == grp]
        fig.add_trace(go.Scatter(
            x=sub["mean"], y=sub["label"],
            mode="markers+text", name=grp,
            marker=dict(color=GROUP_COLORS[grp], size=12),
            text=sub["mean"].map(lambda v: f"{v:.2f}" if pd.notna(v) else ""),
            textposition="middle right",
        ))
    fig.update_layout(
        **_CHART,
        title=title,
        xaxis=dict(title="Mean agreement score (0–4)", range=[-0.2, 5.5]),
        height=max(300, 50 * df["label"].nunique() + 120),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.add_vline(x=2, line_dash="dot", line_color="#aaa")   # neutral midpoint
    return fig


def render() -> None:
    try:
        df = pd.read_csv(DATA_DIR / "pp_attitudes.csv")
    except FileNotFoundError:
        st.error("Attitude data not found. Re-run export_pp_app_data.py.")
        return

    st.markdown("### Phone Pulse — Attitudes toward Family Planning")
    st.caption(
        "Mean agreement scores on 8 attitude statements, rated 0–4 (0 = Strongly disagree, "
        "4 = Strongly agree). Dashed line at 2 = neutral."
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

            fig = _dot_chart(sub, f"Mean agreement — {label.capitalize()} attitudes")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(SCALE_NOTE)

            # Summary table
            pivot = sub.pivot_table(
                index="label", columns="group", values="mean", aggfunc="first"
            ).reset_index()
            col_order = ["label"] + [g for g in GROUP_ORDER if g in pivot.columns]
            pivot = pivot[col_order]
            for g in GROUP_ORDER:
                if g in pivot.columns:
                    pivot[g] = pivot[g].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
            pivot = pivot.rename(columns={"label": "Statement"})
            st.dataframe(pivot, use_container_width=True, hide_index=True)

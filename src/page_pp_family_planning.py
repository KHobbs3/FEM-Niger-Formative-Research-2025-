"""Phone Pulse — Family Planning behaviour page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FEM_ORANGE = "#C1693A"
FEM_BROWN  = "#8B5E45"
FEM_NAVY   = "#2E3F52"
FEM_STEEL  = "#5A6E7F"
FEM_TAUPE  = "#7A7068"
GROUP_COLORS = {"Using FP": FEM_NAVY, "Not using FP": FEM_ORANGE, "All": FEM_TAUPE}
GROUP_ORDER  = ["Using FP", "Not using FP", "All"]

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _grouped_hbar(df: pd.DataFrame, title: str, xmax: float = 100) -> go.Figure:
    """Horizontal bar chart with one trace per group."""
    fig = go.Figure()
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
    n_cats = df["category"].nunique()
    fig.update_layout(
        **_CHART,
        title=title, barmode="group",
        xaxis_title="% of respondents in group",
        xaxis_range=[0, xmax + 15],
        height=max(250, 35 * n_cats * 3 + 100),
        margin=dict(l=10, r=30, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def render() -> None:
    st.markdown("### Phone Pulse — Family Planning Behaviour")
    st.caption(
        "Broken down by current FP use (Using FP = fpbeh_fpnow is 1; "
        "Not using FP = all other respondents)."
    )
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Method awareness", "Methods used", "Reasons for non-use", "Pregnancy chance"
    ])

    with tab1:
        df = pd.read_csv(DATA_DIR / "pp_fp_awareness.csv")
        if df.empty:
            st.info("No data available.")
        else:
            fig = _grouped_hbar(df, "Awareness of FP methods (% who have heard of each)")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Base: all respondents in each group.")

    with tab2:
        df = pd.read_csv(DATA_DIR / "pp_fp_method_used.csv")
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
            st.caption("Base: respondents currently using FP (fpbeh_fpnow = 1).")

    with tab3:
        df = pd.read_csv(DATA_DIR / "pp_fp_whynot.csv")
        if df.empty:
            st.info("No data available.")
        else:
            fig = _grouped_hbar(df, "Reasons for not using FP (% citing each reason)")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Base: all respondents in each group. "
                "Respondents may cite multiple reasons."
            )

    with tab4:
        df = pd.read_csv(DATA_DIR / "pp_fp_preg_chance.csv")
        if df.empty:
            st.info("No data available.")
        else:
            # Order from most to least likely
            order = ["Very likely", "Somewhat likely", "Neither", "Unlikely", "Very unlikely"]
            def _order(d, col="category"):
                d = d.copy()
                d["_ord"] = d[col].map({v: i for i, v in enumerate(order)})
                return d.sort_values("_ord").drop(columns="_ord")

            fig = go.Figure()
            for grp in GROUP_ORDER:
                sub = _order(df[df["group"] == grp])
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
                title="Perceived likelihood of pregnancy (if not using FP)",
                barmode="group", yaxis_title="% of respondents",
                yaxis_range=[0, 80],
                height=380,
                margin=dict(l=10, r=10, t=50, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Scale: 1 = Very likely → 5 = Very unlikely (inverted on x-axis).")

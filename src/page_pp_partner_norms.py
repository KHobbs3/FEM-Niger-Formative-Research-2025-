"""Phone Pulse — Partner dynamics & social norms page."""

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


def _grouped_hbar(df: pd.DataFrame, title: str, xmax: float = 100) -> go.Figure:
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
    return fig


def render() -> None:
    st.markdown("### Phone Pulse — Partner Dynamics & Social Norms")
    st.caption("Results broken down by current FP use status.")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["FP decision-making", "Social norms", "Discussion norms"])

    with tab1:
        df = pd.read_csv(DATA_DIR / "pp_partner_decision.csv")
        fig = _grouped_hbar(df, "Who decides about family planning? (partner_pressure)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "1 = Mainly respondent, 2 = Mainly spouse, 3 = Joint decision, "
            "4 = Other / not applicable."
        )

    with tab2:
        df = pd.read_csv(DATA_DIR / "pp_partner_norms.csv")
        if df.empty:
            st.info("No norm data available.")
        else:
            fig = go.Figure()
            for grp in GROUP_ORDER:
                sub = df[df["group"] == grp].dropna(subset=["mean"])
                if sub.empty:
                    continue
                fig.add_trace(go.Bar(
                    x=sub["mean"], y=sub["label"], orientation="h",
                    name=grp, marker_color=GROUP_COLORS[grp],
                    text=sub["mean"].map(lambda v: f"{v:.2f}"),
                    textposition="outside",
                ))
            fig.update_layout(
                **_CHART,
                title="Mean agreement with social norm statements (0–4 scale)",
                barmode="group",
                xaxis_title="Mean agreement (0 = Strongly disagree, 4 = Strongly agree)",
                xaxis_range=[0, 5],
                height=350,
                margin=dict(l=10, r=30, t=50, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            fig.add_vline(x=2, line_dash="dot", line_color="#aaa")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Statements rated 0–4 (0 = Strongly disagree, 4 = Strongly agree). "
                "Dashed line at 2 = neutral midpoint."
            )

    with tab3:
        df = pd.read_csv(DATA_DIR / "pp_partner_discuss.csv")
        fig = _grouped_hbar(
            df, 'Agreement: "Not acceptable to discuss FP with friends" (pressure_discuss)'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Scale: 0 = Strongly disagree, 1 = Disagree, 2 = Neither, "
            "3 = Agree, 4 = Strongly agree."
        )

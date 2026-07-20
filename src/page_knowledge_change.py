"""Phone Pulse — Contraceptive knowledge change (Baseline vs Follow-up)."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import load_knowledge_change

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
SIG_THRESHOLD = 0.05


def render() -> None:
    df = load_knowledge_change()

    overall = df[df["method"] == "__OVERALL__"]
    methods = df[df["method"] != "__OVERALL__"].sort_values("known_pulse_pct")

    st.markdown("### Phone Pulse — Contraceptive Knowledge Change")
    st.caption(
        "Awareness of specific contraceptive methods, Formative Research "
        "baseline vs. Phone Pulse follow-up, for respondents linked across "
        "both waves."
    )
    st.markdown("---")

    if not overall.empty:
        row = overall.iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Known at baseline", f"{row['known_baseline_pct']:.0f}%")
        col2.metric(
            "Known at follow-up", f"{row['known_pulse_pct']:.0f}%",
            delta=f"{row['known_pulse_pct'] - row['known_baseline_pct']:+.0f} pts",
        )
        col3.metric("Respondents linked", str(int(row["gained_awareness_n"]) +
                                               int(row["lost_awareness_n"])) + "+ w/ change")
        st.caption(row.get("direction", ""))
        st.markdown("---")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=methods["known_baseline_pct"], y=methods["method"], orientation="h",
        name="Baseline", marker_color=FEM_TAUPE,
        text=methods["known_baseline_pct"].map(lambda v: f"{v:.0f}%"),
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=methods["known_pulse_pct"], y=methods["method"], orientation="h",
        name="Follow-up", marker_color=FEM_NAVY,
        text=methods["known_pulse_pct"].map(lambda v: f"{v:.0f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        **_CHART,
        title="Method awareness: baseline vs. follow-up",
        barmode="group",
        xaxis_title="% of linked respondents aware of method",
        xaxis_range=[0, 115],
        height=max(300, 45 * len(methods) + 100),
        margin=dict(l=10, r=30, t=78, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    sig = methods[methods["mcnemar_p_value"] < SIG_THRESHOLD]
    if not sig.empty:
        st.caption(
            f"Statistically significant change (McNemar's exact test, p < "
            f"{SIG_THRESHOLD}): " + ", ".join(sig["method"].tolist())
        )

    st.markdown("#### Detail")
    st.dataframe(
        methods[["method", "known_baseline_pct", "known_pulse_pct",
                 "gained_awareness_n", "lost_awareness_n",
                 "mcnemar_p_value", "direction"]]
        .rename(columns={
            "method": "Method", "known_baseline_pct": "Baseline %",
            "known_pulse_pct": "Follow-up %", "gained_awareness_n": "Gained (n)",
            "lost_awareness_n": "Lost (n)", "mcnemar_p_value": "p-value",
            "direction": "Direction",
        })
        .sort_values("p-value")
        .reset_index(drop=True),
        use_container_width=True, hide_index=True,
    )

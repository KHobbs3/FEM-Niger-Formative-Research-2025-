"""Phone Pulse — Baseline vs Follow-up (formative <-> pulse linkage)."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import load_knowledge_change, load_fp_use_change

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
SIG_THRESHOLD = 0.05


def _pending(csv_name: str) -> None:
    st.info(
        f"Data pending: run `3_linkage/compare_fp_use.py`, upload `{csv_name}.csv` to "
        f"Drive with link sharing on, then paste its file ID into `data_loader.py`."
    )


def _render_method_awareness() -> None:
    df = load_knowledge_change()

    overall = df[df["method"] == "__OVERALL__"]
    methods = df[df["method"] != "__OVERALL__"].sort_values("known_pulse_pct")

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


def _render_fp_use() -> None:
    df = load_fp_use_change()
    if df is None:
        _pending("fp_use_change_summary")
        return
    if df.empty:
        st.info("No data available.")
        return

    st.caption(
        "Current FP use, Formative Research baseline vs. Phone Pulse follow-up, "
        "for respondents linked across both waves."
    )
    st.markdown("---")

    row = df.iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Using FP at baseline", f"{row['using_baseline_pct']:.1f}%")
    col2.metric(
        "Using FP at follow-up", f"{row['using_pulse_pct']:.1f}%",
        delta=f"{row['using_pulse_pct'] - row['using_baseline_pct']:+.1f} pts",
    )
    col3.metric(
        "Started using / Stopped",
        f"{int(row['started_using_n'])} / {int(row['stopped_using_n'])}",
    )

    p_value = row.get("mcnemar_p_value")
    direction = row.get("direction", "")
    if pd.notna(p_value):
        sig_note = (
            f"Statistically significant (McNemar's exact test, p = {p_value:.4f})"
            if p_value < SIG_THRESHOLD else
            f"Not statistically significant (McNemar's exact test, p = {p_value:.4f})"
        )
        st.caption(f"{direction.capitalize() if direction else ''} — {sig_note}".strip(" —"))

    fig = go.Figure(go.Bar(
        x=[row["using_baseline_pct"], row["using_pulse_pct"]],
        y=["Baseline", "Follow-up"],
        orientation="h",
        marker_color=[FEM_TAUPE, FEM_NAVY],
        text=[f"{row['using_baseline_pct']:.1f}%", f"{row['using_pulse_pct']:.1f}%"],
        textposition="outside",
    ))
    fig.update_layout(
        **_CHART,
        title=row.get("question", "Currently using FP"),
        xaxis_title="% of linked respondents",
        xaxis_range=[0, 115],
        height=260,
        margin=dict(l=10, r=30, t=78, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "\"Started using\" = not using FP at baseline, using at follow-up. "
        "\"Stopped\" = the reverse."
    )


def _render_limitations() -> None:
    with st.expander("Limitations & caveats"):
        st.markdown(
            "- **Measurement effect**: the baseline was an in-person interview and "
            "the follow-up a phone call; the change in mode/privacy could shift "
            "reported answers on its own, independent of any real change.\n"
            "- **Linkage / attrition selection**: only 471 of 968 formative "
            "respondents (92.5% of the 509 reachable Phone Pulse respondents) were "
            "successfully linked across waves. If reachable/re-interviewed "
            "respondents differ systematically from those lost to follow-up, this "
            "comparison isn't necessarily representative of the full baseline sample.\n"
            "- **Confounding variables**: seasonal patterns, supply/stockout "
            "changes, or other health programming active over the same period "
            "could also contribute to the change shown here."
        )


def render() -> None:
    st.markdown("### Phone Pulse — Baseline vs Follow-up")

    tab1, tab2 = st.tabs(["Method Awareness", "Current FP Use"])
    with tab1:
        _render_method_awareness()
        _render_limitations()
    with tab2:
        _render_fp_use()
        _render_limitations()

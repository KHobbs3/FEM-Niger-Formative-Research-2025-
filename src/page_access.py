import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY
from src.data_loader import (
    load_access_stockouts,
    load_access_stockout_responses,
    load_access_travel,
    load_access_affordability,
    load_access_composite,
)

FEM_PALETTE = [FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY]

SPLIT_MAP = {
    "User group": "use",
    "Gender":     "gender",
    "Age group":  "age_group",
}

_MISSING = (
    "Pre-aggregated data not found. "
    "Run `python pipeline/run_pipeline.py --pages access` to generate it."
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hbar(series, title, pct=True, key=None):
    if series is None or series.empty:
        return
    colors = (FEM_PALETTE * (len(series) // len(FEM_PALETTE) + 1))[:len(series)]
    text = [f"{v*100:.1f}%" if pct else f"{v:.1f}" for v in series.values]
    fig = go.Figure(go.Bar(
        y=series.index.astype(str),
        x=series.values,
        orientation="h",
        marker_color=colors,
        text=text,
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(
            tickformat=".0%" if pct else "",
            showgrid=False,
            range=[0, series.max() * 1.35] if len(series) else [0, 1],
        ),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=36, b=10),
        height=max(200, len(series) * 44 + 80),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def _get_metric(df_long, metric, split_col):
    if df_long is None or df_long.empty:
        return pd.Series(dtype=float)
    sub = df_long[(df_long["metric"] == metric) & (df_long["split"] == split_col)]
    return sub.set_index("group")["value"].dropna()


def _get_scalar(df_long, metric):
    if df_long is None or df_long.empty:
        return np.nan
    sub = df_long[
        (df_long["metric"] == metric) &
        (df_long["split"] == "all") &
        (df_long["group"] == "all")
    ]
    return sub["value"].iloc[0] if not sub.empty else np.nan


# ── Section renderers ─────────────────────────────────────────────────────────

def render_availability(df_stockouts, df_responses, split_col):
    st.subheader("1. Availability")
    st.caption(
        "Are contraceptives stocked when people seek them? "
        "Users and non-users were asked separate questions."
    )
    if df_stockouts is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Users & past users**")
        _hbar(_get_metric(df_stockouts, "stockout_users", split_col),
              "Stockout rate", key="avail_users")
        if df_responses is not None:
            sub = df_responses[df_responses["group"] == "users"]
            if not sub.empty:
                with st.expander("How did users respond to stockouts?"):
                    st.dataframe(sub[["response", "count"]].reset_index(drop=True),
                                 use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Non-users & future users**")
        _hbar(_get_metric(df_stockouts, "sought_contraceptives", split_col),
              "Sought contraceptives", key="avail_sought")
        _hbar(_get_metric(df_stockouts, "stockout_nonusers_sought", split_col),
              "Stockout rate (among those who sought)", key="avail_nonusers")
        if df_responses is not None:
            sub = df_responses[df_responses["group"] == "nonusers"]
            if not sub.empty:
                with st.expander("How did non-users respond to stockouts?"):
                    st.dataframe(sub[["response", "count"]].reset_index(drop=True),
                                 use_container_width=True, hide_index=True)


def render_accessibility(df_travel, split_col):
    st.subheader("2. Accessibility")
    st.caption("Travel time to facilities, willingness to travel, and the gap between them.")
    if df_travel is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns(2)
    with col1:
        _hbar(_get_metric(df_travel, "mean_travel_users", split_col),
              "Mean travel time — users (mins)", pct=False, key="travel_users")
    with col2:
        _hbar(_get_metric(df_travel, "mean_travel_nonusers", split_col),
              "Mean travel time — non-users (mins)", pct=False, key="travel_nonusers")

    st.markdown("**Travel time gap** — share of users travelling further than willing")
    overall = _get_scalar(df_travel, "travel_gap_rate_overall")
    if not np.isnan(overall):
        st.metric("Overall travel barrier rate (users)", f"{overall*100:.1f}%")
    _hbar(_get_metric(df_travel, "travel_gap_rate", split_col),
          f"Travel barrier rate by {split_col}", key="travel_gap")

    with st.expander("Transport modes"):
        c1, c2 = st.columns(2)
        for label, cobj, key in [("users", c1, "tm_u"), ("nonusers", c2, "tm_nu")]:
            sub = df_travel[
                (df_travel["metric"] == f"transport_mode_{label}") &
                (df_travel["split"] == "mode")
            ]
            if not sub.empty:
                with cobj:
                    _hbar(sub.set_index("group")["value"].dropna(),
                          f"Transport — {label}", key=key)


def render_affordability(df_afford, split_col):
    st.subheader("3. Affordability")
    st.caption(
        "Contraceptive costs for users/past users vs. "
        "expected visit cost for non-users/future users."
    )
    if df_afford is None:
        st.warning(_MISSING)
        return

    col1, col2 = st.columns(2)
    with col1:
        _hbar(_get_metric(df_afford, "mean_cost_users", split_col),
              "Mean contraceptive cost — users (CFA)", pct=False, key="cost_users")
    with col2:
        _hbar(_get_metric(df_afford, "mean_cost_nonusers", split_col),
              "Expected visit cost — non-users (CFA)", pct=False, key="cost_nonusers")

    overall_cost = _get_scalar(df_afford, "cost_barrier_overall")
    if not np.isnan(overall_cost):
        st.metric("Share of users who paid anything", f"{overall_cost*100:.1f}%")


def render_composite(df_composite):
    st.subheader("4. Composite supply indicator")
    st.caption("Share of respondents facing each supply-side barrier.")
    if df_composite is None:
        st.warning(_MISSING)
        return

    overall = (df_composite[df_composite["use_group"] == "all"]
               .set_index("barrier")["rate"].dropna())
    fig = go.Figure(go.Bar(
        x=overall.index,
        y=overall.values,
        marker_color=FEM_PALETTE[:len(overall)],
        text=[f"{v*100:.1f}%" for v in overall.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Composite supply barrier rates",
        yaxis=dict(tickformat=".0%", title="Proportion", showgrid=False,
                   range=[0, overall.max() * 1.3] if not overall.empty else [0, 1]),
        xaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=20),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key="composite")

    with st.expander("Barrier rates by user group"):
        breakdown = df_composite[df_composite["use_group"] != "all"].dropna(subset=["rate"])
        if not breakdown.empty:
            fig2 = px.bar(
                breakdown, x="barrier", y="rate", color="use_group", barmode="group",
                text=breakdown["rate"].apply(lambda v: f"{v*100:.1f}%"),
                color_discrete_sequence=FEM_PALETTE,
            )
            fig2.update_layout(
                yaxis=dict(tickformat=".0%", title="Proportion", showgrid=False),
                xaxis=dict(showgrid=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=340,
                legend_title="User group",
            )
            st.plotly_chart(fig2, use_container_width=True, key="composite_grp")


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Health Access Barriers")

    df_stockouts = load_access_stockouts()
    df_responses = load_access_stockout_responses()
    df_travel    = load_access_travel()
    df_afford    = load_access_affordability()
    df_composite = load_access_composite()

    split_by  = st.radio("Split all charts by", list(SPLIT_MAP.keys()), horizontal=True)
    split_col = SPLIT_MAP[split_by]

    st.divider()
    render_availability(df_stockouts, df_responses, split_col)
    st.divider()
    render_accessibility(df_travel, split_col)
    st.divider()
    render_affordability(df_afford, split_col)
    st.divider()
    render_composite(df_composite)

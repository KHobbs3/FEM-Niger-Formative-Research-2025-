import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.data_loader import (
    load_drivers_barriers, parse_subgroup_prevalence,
    parse_statements, get_priority_sort_key,
    USER_CATEGORY_LABELS, AGE_GROUPS, GENDERS
)
from src.fem_colours import PRIORITY_COLORS, FEM_PALETTE

def render_priority_badge(priority):
    color = PRIORITY_COLORS.get(str(priority).strip(), "#6b7280")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">{priority}</span>'

def build_prevalence_bar(row, split="user_category"):
    """Build a horizontal bar chart for a single driver/barrier row."""
    if split == "user_category":
        data = parse_subgroup_prevalence(row["Prevalence (All)"])
        labels = [USER_CATEGORY_LABELS.get(k, k) for k in data.keys()]
        values = list(data.values())
        colors = FEM_PALETTE
    elif split == "gender":
        data = parse_subgroup_prevalence(row["GENDER: Prevalence (All)"])
        labels = list(data.keys())
        values = list(data.values())
        colors = FEM_PALETTE
    elif split == "age":
        data = parse_subgroup_prevalence(row["AGE_GROUP: Prevalence (All)"])
        labels = list(data.keys())
        values = list(data.values())
        colors = FEM_PALETTE
    else:
        data = {}
        labels, values, colors = [], [], []

    if not values:
        return None

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors[:len(labels)],
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        margin=dict(l=0, r=60, t=4, b=4),
        height=max(80, len(labels) * 36),
        xaxis=dict(range=[0, max(values) * 1.35], showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=12),
    )
    return fig

def build_statement_chart(row, split="user_category"):
    """Build agreement % chart for the linked belief statement."""
    if split == "user_category":
        stmt, pcts = parse_statements(row["Statements"])
    elif split == "gender":
        stmt, pcts = parse_statements(row["GENDER: Statements"])
    elif split == "age":
        stmt, pcts = parse_statements(row["AGE_GROUP: Statements"])
    else:
        return None, None

    if not pcts:
        return stmt, None

    labels = list(pcts.keys())
    values = list(pcts.values())
    colors = FEM_PALETTE

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors[:len(labels)],
        text=[f"{v:.0f}%" for v in values],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        margin=dict(l=0, r=60, t=4, b=4),
        height=max(80, len(labels) * 36),
        xaxis=dict(range=[0, 115], showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=12),
    )
    return stmt, fig

def render(df_raw=None):
    st.header("Drivers & Barriers")

    if df_raw is None:
        df_raw = load_drivers_barriers()

    # --- Controls ---
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        db_type = st.radio("Show", ["Driver", "Barrier"], horizontal=True)
    with col2:
        split_by = st.radio("Split by", ["User category", "Gender", "Age group"], horizontal=True)
    with col3:
        priority_filter = st.multiselect(
            "Priority filter",
            ["Very high", "High", "Medium", "Low"],
            default=["Very high", "High"],
        )

    split_key = {"User category": "user_category", "Gender": "gender", "Age group": "age"}[split_by]

    # --- Filter data ---
    df = df_raw[df_raw["Driver/Barrier"].str.lower() == db_type.lower()].copy()
    if priority_filter:
        df = df[df["Priority"].isin(priority_filter)]
    df["_sort"] = df["Priority"].apply(get_priority_sort_key)
    df = df.sort_values("_sort", ascending=False).reset_index(drop=True)

    if df.empty:
        st.info("No data matches the current filters.")
        return

    st.caption(f"Showing {len(df)} {db_type.lower()} — sorted by priority")
    st.divider()

    # --- Render each row ---
    for _, row in df.iterrows():
        name = str(row["Name"])
        priority = str(row["Priority"]).strip()

        # Header row
        hcol1, hcol2 = st.columns([6, 1])
        with hcol1:
            st.markdown(f"**{name}**")
        with hcol2:
            st.markdown(render_priority_badge(priority), unsafe_allow_html=True)

        # Prevalence chart
        fig_prev = build_prevalence_bar(row, split_key)
        if fig_prev:
            st.markdown("*Prevalence — % of respondents who mentioned this*")
            st.plotly_chart(fig_prev, use_container_width=True, key=f"prev_{name[:40]}")

        # Statement agreement
        stmt, fig_stmt = build_statement_chart(row, split_key)
        if fig_stmt:
            stmt_text = stmt if stmt else "Related belief statement"
            st.markdown(f"*Agreement with: \"{stmt_text}\"*")
            st.plotly_chart(fig_stmt, use_container_width=True, key=f"stmt_{name[:40]}")

        st.divider()

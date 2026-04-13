"""
page_statements.py  —  improved version
Changes:
  • Higher-contrast colour scale.
  • Human-readable group column headers for "use" split.
  • Second view shows actual respondent count (n) and weighted count — not %,
    since the raw 'proportion' column may not be present in every pipeline run.
  • Column detection: tries common count column names, reports clearly if absent.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.data_loader import load_statements_heatmap
from src.fem_colours import FEM_ORANGE, FEM_BROWN

# ── Colour scale ──────────────────────────────────────────────────────────────
FEM_SCALE_HC = [
    [0.0,  "#f8f3ee"],
    [0.15, "#f0d5b8"],
    [0.35, "#d9935e"],
    [0.55, FEM_ORANGE],
    [0.75, FEM_BROWN],
    [1.0,  "#2E3F52"],
]

USE_GROUP_LABELS = {
    "user":        "Current user",
    "past_user":   "Past user",
    "future_user": "Future user",
    "non_user":    "Non-user",
    "all":         "All",
}

SPLIT_MAP = {
    "User category": "use",
    "Gender":        "gender",
    "Age group":     "age_group",
    "None":          "none",
}

_MISSING = (
    "Pre-aggregated data not found. "
    "Run `python pipeline/run_pipeline.py --pages statements` to generate it."
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rename_columns(pivot, split_key):
    if split_key == "use":
        pivot.columns = [USE_GROUP_LABELS.get(str(c), str(c)) for c in pivot.columns]
    return pivot


def _build_pivot(df_long, split_key, value_col="weighted_agreement"):
    if value_col not in df_long.columns:
        return pd.DataFrame()

    if split_key == "none":
        sub = df_long[(df_long["split"] == "none") & (df_long["group"] == "all")]
        pivot = sub.set_index("label")[[value_col]]
        pivot.columns = ["All respondents"]
        return pivot

    sub = df_long[df_long["split"] == split_key]
    pivot = sub.pivot_table(
        index="label", columns="group",
        values=value_col, aggfunc="first", fill_value=0,
    )
    return _rename_columns(pivot, split_key)


def _heatmap_fig(pivot, title, value_label):
    z = pivot.values * 100

    text_matrix = [
        [f"{v:.0f}%" if (v is not None and not np.isnan(float(v))) else "" for v in row]
        for row in z
    ]

    fig = px.imshow(
        z,
        labels=dict(x="Group", y="Statement", color=value_label),
        x=list(pivot.columns.astype(str)),
        y=list(pivot.index.astype(str)),
        color_continuous_scale=FEM_SCALE_HC,
        zmin=0, zmax=100,
        text_auto=False,
    )
    fig.update_traces(text=text_matrix, texttemplate="%{text}")
    fig.update_layout(
        title=title,
        height=max(500, len(pivot) * 28 + 120),
        coloraxis_colorbar=dict(title=value_label, ticksuffix="%", thickness=14),
        xaxis=dict(side="top", tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=11)),
        margin=dict(l=10, r=20, t=80, b=10),
    )
    return fig


def _build_counts_table(df_long, split_key):
    """
    Build a table of actual n and weighted n per statement per group.
    Returns None if neither count column is found.
    """
    n_col  = next((c for c in df_long.columns if c in ("n", "count", "n_respondents")), None)
    wn_col = next((c for c in df_long.columns if c in ("weighted_n", "n_weighted", "wn")), None)

    if n_col is None and wn_col is None:
        return None

    if split_key == "none":
        sub = df_long[(df_long["split"] == "none") & (df_long["group"] == "all")].copy()
        result = {"Statement": sub["label"].tolist()}
        if n_col:
            result["n (respondents)"] = [
                f"{int(v):,}" if pd.notna(v) else "" for v in sub[n_col]
            ]
        if wn_col:
            result["Weighted n"] = [
                f"{float(v):,.1f}" if pd.notna(v) else "" for v in sub[wn_col]
            ]
        return pd.DataFrame(result)

    sub = df_long[df_long["split"] == split_key].copy()
    groups = sorted(sub["group"].dropna().unique())
    labels = sub["label"].dropna().unique()

    rows = []
    for lbl in labels:
        row = {"Statement": lbl}
        for grp in groups:
            grp_name = USE_GROUP_LABELS.get(str(grp), str(grp)) if split_key == "use" else str(grp)
            cell = sub[(sub["label"] == lbl) & (sub["group"] == grp)]
            if n_col:
                val = cell[n_col].iloc[0] if not cell.empty and pd.notna(cell[n_col].iloc[0]) else ""
                row[f"{grp_name} — n"] = f"{int(val):,}" if val != "" else ""
            if wn_col:
                wval = cell[wn_col].iloc[0] if not cell.empty and pd.notna(cell[wn_col].iloc[0]) else ""
                row[f"{grp_name} — wtd n"] = f"{float(wval):,.1f}" if wval != "" else ""
        rows.append(row)

    return pd.DataFrame(rows)


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Statement Agreement")

    split_by = st.radio("Split data by", list(SPLIT_MAP.keys()), horizontal=True)
    split_key = SPLIT_MAP[split_by]

    df_long = load_statements_heatmap()
    if df_long is None or df_long.empty:
        st.warning(_MISSING)
        return

    # ── Weighted agreement heatmap ────────────────────────────────────────────
    pivot_w = _build_pivot(df_long, split_key, value_col="weighted_agreement")
    if pivot_w.empty:
        st.info("No data for this split.")
        return

    if split_key == "use":
        st.caption(
            "Columns show **user category**. "
            "Weighted agreement score (0–100 %). Darker = higher agreement."
        )
    else:
        st.caption("Weighted agreement score (0–100 %). Darker = higher agreement.")

    st.plotly_chart(
        _heatmap_fig(pivot_w, "Statement Agreement — weighted score", "Weighted agmt %"),
        use_container_width=True,
        key="heatmap_weighted",
    )

    # ── Respondent counts ─────────────────────────────────────────────────────
    with st.expander("View respondent counts (n and weighted n)"):
        counts_df = _build_counts_table(df_long, split_key)
        if counts_df is not None and not counts_df.empty:
            st.caption(
                "**n** = actual number of respondents who answered each statement. "
                "**Weighted n** = sum of survey weights (effective sample size)."
            )
            st.dataframe(counts_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                "Count columns (n / weighted_n) were not found in the aggregated dataset. "
                "Re-run the pipeline ensuring count columns are exported alongside "
                "weighted_agreement."
            )

    # ── Raw agreement scores table ────────────────────────────────────────────
    with st.expander("View weighted agreement scores (table)"):
        st.dataframe(pivot_w.style.format("{:.1%}"), use_container_width=True)

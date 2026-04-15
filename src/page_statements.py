"""
page_statements.py  —  improved version
Changes:
  • Higher-contrast colour scale.
  • Human-readable group column headers for "use" split.
  • Shows agree/disagree counts separately (not just total respondents).
  • Weighted agreement is normalized: (sum of weighted responses) / (total weighted n)
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
    "nonuser":     "Non-user",
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
    z = pivot.values
    
    # Clamp values to [0, 1] for display
    z_clamped = np.clip(z, 0, 1)

    text_matrix = [
        [f"{v:.0%}" if (v is not None and not np.isnan(float(v))) else "" for v in row]
        for row in z
    ]

    fig = px.imshow(
        z_clamped * 100,
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
    Build a table showing agree/disagree counts separately.
    """
    required_cols = ["agree_n", "agree_weighted_n", "disagree_n", "disagree_weighted_n"]
    if not all(c in df_long.columns for c in required_cols):
        return None

    if split_key == "none":
        sub = df_long[(df_long["split"] == "none") & (df_long["group"] == "all")].copy()
        result = {"Statement": sub["label"].tolist()}
        result["Agree — n"] = [f"{int(v):,}" if pd.notna(v) else "" for v in sub["agree_n"]]
        result["Agree — wtd n"] = [f"{float(v):,.1f}" if pd.notna(v) else "" for v in sub["agree_weighted_n"]]
        result["Disagree — n"] = [f"{int(v):,}" if pd.notna(v) else "" for v in sub["disagree_n"]]
        result["Disagree — wtd n"] = [f"{float(v):,.1f}" if pd.notna(v) else "" for v in sub["disagree_weighted_n"]]
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
            
            if not cell.empty:
                agree_n = cell["agree_n"].iloc[0]
                agree_wn = cell["agree_weighted_n"].iloc[0]
                disagree_n = cell["disagree_n"].iloc[0]
                disagree_wn = cell["disagree_weighted_n"].iloc[0]
                
                row[f"{grp_name} — Agree n"] = f"{int(agree_n):,}" if pd.notna(agree_n) else ""
                row[f"{grp_name} — Agree wtd"] = f"{float(agree_wn):,.1f}" if pd.notna(agree_wn) else ""
                row[f"{grp_name} — Disagree n"] = f"{int(disagree_n):,}" if pd.notna(disagree_n) else ""
                row[f"{grp_name} — Disagree wtd"] = f"{float(disagree_wn):,.1f}" if pd.notna(disagree_wn) else ""
        
        rows.append(row)

    return pd.DataFrame(rows)


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Statement Agreement")
    
    # Description at the top
    st.markdown("""
    ### Interpreting the heatmap and counts
    
    **Weighted Agreement Score (heatmap):**
    - The weighted agreement score was calculated as: (sum of weighted "Agree" responses − sum of weighted "Disagree" responses) / (total weighted respondents)
    - Range: −1.0 (all disagree) to +1.0 (all agree)
    - Displayed as: (score + 1) / 2 × 100, converting to 0–100 % scale
    - Darker colours indicate higher agreement; lighter colours indicate higher disagreement
    
    **Respondent Counts (table):**
    - **n** = actual number of respondents who answered
    - **Weighted n** = sum of survey weights (effective sample size, accounts for over/under-sampling)
    """)

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
            "Scale: 0–100 %. Darker = higher agreement. Lighter = higher disagreement."
        )
    else:
        st.caption("Scale: 0–100 %. Darker = higher agreement. Lighter = higher disagreement.")

    st.plotly_chart(
        _heatmap_fig(pivot_w, "Statement Agreement — weighted score", "Agreement %"),
        use_container_width=True,
        key="heatmap_weighted",
    )

    # ── Respondent counts ────────────────────────────────────────────────────
    with st.expander("View respondent counts (Agree vs Disagree)"):
        counts_df = _build_counts_table(df_long, split_key)
        if counts_df is not None and not counts_df.empty:
            st.caption(
                "**n** = actual number of respondents. "
                "**Weighted n** = sum of survey weights (effective sample size). "
                "Shown separately for Agree and Disagree responses."
            )
            st.dataframe(counts_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                "Count columns were not found in the aggregated dataset. "
                "Re-run the pipeline ensuring count columns are exported."
            )

    # ── Raw agreement scores table ────────────────────────────────────────────
    with st.expander("View weighted agreement scores (table)"):
        st.dataframe(pivot_w.style.format("{:.1%}"), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import load_statements_heatmap
from src.fem_colours import FEM_SCALE

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


def _build_pivot(df_long, split_key):
    """Return a pivot table ready for px.imshow."""
    if split_key == "none":
        sub = df_long[(df_long["split"] == "none") & (df_long["group"] == "all")]
        pivot = sub.set_index("label")[["weighted_agreement"]]
        pivot.columns = ["All"]
    else:
        sub = df_long[df_long["split"] == split_key]
        pivot = sub.pivot_table(
            index="label",
            columns="group",
            values="weighted_agreement",
            aggfunc="first",
            fill_value=0,
        )
    return pivot


def statement_heatmap(split_key):
    df_long = load_statements_heatmap()

    if df_long is None or df_long.empty:
        st.warning(_MISSING)
        return

    pivot = _build_pivot(df_long, split_key)
    if pivot.empty:
        st.info("No data for this split.")
        return

    fig = px.imshow(
        pivot.values,
        labels=dict(x="Group", y="Statement", color="Weighted Agreement"),
        x=list(pivot.columns.astype(str)),
        y=list(pivot.index.astype(str)),
        color_continuous_scale=FEM_SCALE,
    )
    fig.update_layout(
        title="Statement Agreement Heatmap",
        xaxis_title=split_key if split_key != "none" else "",
        yaxis_title="Statements",
        height=1400,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View processed data"):
        st.dataframe(pivot)


def render():
    st.title("Statement Agreement Heatmap")

    split_by = st.radio(
        "Split data by",
        list(SPLIT_MAP.keys()),
        horizontal=True,
    )
    statement_heatmap(SPLIT_MAP[split_by])

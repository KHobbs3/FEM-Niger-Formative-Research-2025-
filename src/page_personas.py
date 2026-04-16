import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY, FEM_PALETTE
from src.data_loader import (
    load_personas_centroids,
    load_personas_profile,
)

_MISSING = (
    "Pre-aggregated persona data not found. "
    "Run `python pipeline/run_pipeline.py --pages personas` to generate it."
)

PROFILE_VARS = ["gender", "age_group", "use", "occupation", "religion", "life_goals"]


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _strip_hausa(text: str) -> str:
    """Return only the English part of bilingual 'Hausa / English' labels.
    
    Handles both single labels and pipe-delimited multiple labels.
    Example: "Ingantacciyar Lafiyar Mutum / Good/Better Personal Health|..."
             → "Good/Better Personal Health|Always Having Enough Food For My Children"
    """
    if not text or pd.isna(text):
        return str(text).strip()
    
    text = str(text)
    
    # Handle pipe-delimited multiple options
    if "|" in text:
        parts = text.split("|")
        english_parts = [_strip_hausa(part) for part in parts]
        return "|".join(english_parts)
    
    # Handle single bilingual label (Hausa / English)
    if "/" in text:
        # Split on first "/" to separate Hausa from the English part
        split = text.split("/", 1)
        if len(split) == 2:
            english = split[1].strip()
            return english if english else text.strip()

    else:
        # Split on first "/" to separate Hausa from the English part
        split = text.split(" / ", 1)
        if len(split) == 2:
            english = split[1].strip()
            return english if english else text.strip()
    
    return text.strip().replace("|", "; ")


def _hbar(series, title, top_n=10, key=None):
    series = series.head(top_n)
    if series is None or series.empty:
        return
    colors = (FEM_PALETTE * (len(series) // len(FEM_PALETTE) + 1))[:len(series)]
    fig = go.Figure(go.Bar(
        y=series.index.astype(str),
        x=series.values,
        orientation="h",
        marker_color=colors,
        text=[f"{v*100:.1f}%" for v in series.values],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, showticklabels=False,
                   range=[0, series.max() * 1.35] if len(series) else [0, 1]),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=36, b=10),
        height=max(180, len(series) * 34 + 60),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── Section renderers ─────────────────────────────────────────────────────────

def render_centroid_table(df_centroids):
    st.subheader("Persona summary")
    st.caption(
        "Each row is a cluster centroid — the representative values for that persona. "
        "Count shows the number of respondents in each cluster."
    )

    display = df_centroids.copy()

    # Clean up table
    display.index.name = "Persona"
    display.drop(columns=["persona"], inplace=True, errors="ignore")
    display['life_goals'] = display['life_goals'].apply(_strip_hausa)
    
    # Format count columns
    for col in ["age", "count", "weighted_count"]:
        if col in display.columns and display[col].dtype in [int, float]:
            display[col] = display[col].apply(
                lambda v: f"{int(v):,}" if pd.notna(v) else ""
            )

    # Format display columns
    display.columns = [col.replace("_", " ").title() for col in display.columns]

    st.dataframe(display, use_container_width=True)


def render_persona_profiles(df_profile, n_personas):
    st.subheader("Persona deep-dive")
    st.caption("Select a persona to see the distribution of key variables within that cluster.")

    persona_id = st.selectbox(
        "Select persona",
        list(range(n_personas)),
        format_func=lambda x: f"Persona {x}",
        key="persona_select",
    )

    sub = df_profile[df_profile["persona"] == persona_id].copy()

    # Show count
    count_row = sub[sub["variable"] == "_count"]
    if not count_row.empty:
        n = count_row[count_row["value"] == "n"]["proportion"].values
        wn = count_row[count_row["value"] == "weighted_n"]["proportion"].values
        c1, c2 = st.columns(2)
        c1.metric("Respondents", f"{int(n[0]):,}" if len(n) else "N/A")
        c2.metric("Weighted N", f"{wn[0]:,.0f}" if len(wn) else "N/A")

    # Profile charts per variable
    profile_vars = [v for v in sub["variable"].unique() if not v.startswith("_")]
    cols = st.columns(2)
    for i, var in enumerate(profile_vars):
        var_sub = sub[sub["variable"] == var]
        if var_sub.empty:
            continue
        # If numeric (single "mean" row), show as metric
        if set(var_sub["value"].tolist()) == {"mean"}:
            val = var_sub["proportion"].iloc[0]
            cols[i % 2].metric(var.replace("_", " ").title(), f"{val:.1f}")
        else:
            s = var_sub.set_index("value")["proportion"].sort_values(ascending=False)
            with cols[i % 2]:
                _hbar(s, var.replace("_", " ").title(),
                      key=f"persona_{persona_id}_{var}")


def render_comparison(df_profile, n_personas):
    st.subheader("Persona comparison")
    st.caption("Compare the distribution of one variable across all personas.")

    profile_vars = [v for v in df_profile["variable"].unique() if not v.startswith("_")]
    selected_var = st.selectbox("Select variable", profile_vars,
                                format_func=lambda v: v.replace("_", " ").title(),
                                key="persona_compare_var")

    sub = df_profile[df_profile["variable"] == selected_var].copy()

    # Skip numeric mean rows in comparison
    if set(sub["value"].tolist()) == {"mean"}:
        st.info("Comparison chart not available for numeric variables.")
        return

    traces = []
    for i, pid in enumerate(range(n_personas)):
        pdata = sub[sub["persona"] == pid].set_index("value")["proportion"]
        traces.append(go.Bar(
            name=f"Persona {pid}",
            x=pdata.index.astype(str),
            y=pdata.values,
            marker_color=FEM_PALETTE[i % len(FEM_PALETTE)],
            text=[f"{v*100:.0f}%" for v in pdata.values],
            textposition="outside",
        ))

    if not traces:
        return

    fig = go.Figure(traces)
    fig.update_layout(
        barmode="group",
        yaxis=dict(tickformat=".0%", showgrid=False, title="% of persona"),
        xaxis=dict(showgrid=False, tickangle=-30),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=80, l=10, r=10),
        height=360,
        legend_title="Persona",
    )
    st.plotly_chart(fig, use_container_width=True, key="persona_compare")


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.header("Personas")
    st.caption("""We develop cluster-based respondent profiles (ie. archetypes) based on the profiles of formative research participants. 
    This approach is used in user-centred design and marketing to create representative "customer personas" that help teams empathise with their target audience and make informed design decisions.
    """)
    st.markdown("""
### Methodology
Personas were derived using **k-modes clustering**, a variant of k-means adapted for
categorical data. Unlike k-means, k-modes uses modes (most frequent values) rather than
means as cluster centres, and measures dissimilarity by the number of mismatching
categories between observations — making it well-suited to survey responses.

**Clustering variables:** age, gender, occupation, religion, and life goals.

**Configuration:** 3 clusters, initialised using the Cao method (which selects starting
centroids based on category frequency distributions to reduce sensitivity to random
starting points), with 5 independent runs to improve stability. Results are fully
reproducible (fixed random seed).

**Output:** Each persona represents the modal respondent within a cluster — the
combination of attribute values that best characterises that group. Cluster size (N and
weighted N) is shown for each persona. Individual-level data is not stored or displayed.
        """)
    st.markdown("")

    df_centroids = load_personas_centroids()
    df_profile   = load_personas_profile()

    if df_centroids is None or df_centroids.empty:
        st.warning(_MISSING)
        return

    n_personas = len(df_centroids)

    render_centroid_table(df_centroids)
    st.divider()

    if df_profile is not None and not df_profile.empty:
        tab1, tab2 = st.tabs(["Deep-dive", "Comparison"])
        with tab1:
            render_persona_profiles(df_profile, n_personas)
        with tab2:
            render_comparison(df_profile, n_personas)
    else:
        st.warning(
            "Persona profile data not found. "
            "Run `python pipeline/run_pipeline.py --pages personas` to generate it."
        )

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY, FEM_PALETTE
from src.data_loader import (
    load_personas_centroids,
    load_personas_profile,
    load_personas_centroids_by_gender,
    load_personas_profile_by_gender,
    load_personas_elbow,
    load_personas_centroids_by_fp_use,
    load_personas_profile_by_fp_use,
    load_personas_elbow_by_fp_use,
)

_MISSING = (
    "Pre-aggregated persona data not found. "
    "Run `python pipeline/run_pipeline.py --pages personas` to generate it."
)

PROFILE_VARS = ["gender", "age_group", "use", "occupation", "religion", "life_goals"]

GENDER_DISPLAY = {
    "Mace / Femme":   "Female (Mace / Femme)",
    "Namiji / Homme": "Male (Namiji / Homme)",
}
GENDER_COLORS = {
    "Mace / Femme":   FEM_ORANGE,
    "Namiji / Homme": FEM_NAVY,
}

# FP-use split: same binary Using FP / Not using FP definition used
# throughout the app (pipeline/config.py USER_GROUPS/NONUSER_GROUPS).
FP_USE_DISPLAY = {
    "Using FP":     "Using FP",
    "Not using FP": "Not using FP",
}
FP_USE_COLORS = {
    "Using FP":     FEM_NAVY,
    "Not using FP": FEM_ORANGE,
}

# split key -> (centroid_col, display_map, color_map, loaders)
SPLIT_CONFIG = {
    "Gender": {
        "group_col": "gender",
        "display": GENDER_DISPLAY,
        "colors": GENDER_COLORS,
        "load_centroids": load_personas_centroids_by_gender,
        "load_profile": load_personas_profile_by_gender,
        "load_elbow": load_personas_elbow,
    },
    "FP use status": {
        "group_col": "fp_use",
        "display": FP_USE_DISPLAY,
        "colors": FP_USE_COLORS,
        "load_centroids": load_personas_centroids_by_fp_use,
        "load_profile": load_personas_profile_by_fp_use,
        "load_elbow": load_personas_elbow_by_fp_use,
    },
}


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _strip_hausa(text: str) -> str:
    """Return only the English part of bilingual 'Hausa / English' labels."""
    if not text or pd.isna(text):
        return str(text).strip()
    text = str(text)
    if "|" in text:
        parts = text.split("|")
        return "|".join(_strip_hausa(p) for p in parts)
    if "/" in text:
        split = text.split("/", 1)
        if len(split) == 2:
            english = split[1].strip()
            return english if english else text.strip()
    else:
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


# ── Elbow plot ────────────────────────────────────────────────────────────────

def render_elbow_plot(df_elbow, group_col, display_map, colors_map, legend_title):
    st.subheader("Choosing the number of clusters")
    st.caption(
        "Each line shows the within-cluster cost (sum of dissimilarities) for "
        f"k = 1 – 6 clusters, computed separately per {legend_title.lower()}. "
        "The 'elbow' — where the curve flattens — indicates the optimal k."
    )

    groups = df_elbow[group_col].unique()
    fig = go.Figure()
    for g in groups:
        sub = df_elbow[df_elbow[group_col] == g].sort_values("k")
        color = colors_map.get(g, FEM_TAUPE)
        label = display_map.get(g, g)
        fig.add_trace(go.Scatter(
            x=sub["k"], y=sub["cost"],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=7),
        ))

    fig.update_layout(
        xaxis=dict(title="Number of clusters (k)", dtick=1, showgrid=False),
        yaxis=dict(title="Within-cluster cost", showgrid=True, gridcolor="#eeeeee"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(title=legend_title, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"elbow_plot_{group_col}")


# ── Section renderers ─────────────────────────────────────────────────────────

def render_centroid_table(df_centroids, group_col=None, group_label=None):
    key_suffix = group_label.replace(" ", "_").replace("/", "") if group_label else "overall"
    st.subheader("Persona summary")
    st.caption(
        "Each row is a cluster centroid — the representative values for that persona. "
        "Count shows the number of respondents in each cluster."
    )

    display = df_centroids.copy()
    drop_cols = ["persona", "Unnamed: 0"] + ([group_col] if group_col else [])
    display.drop(columns=drop_cols, inplace=True, errors="ignore")
    if "life_goals" in display.columns:
        display["life_goals"] = display["life_goals"].apply(_strip_hausa)

    for col in ["age", "count", "weighted_count"]:
        if col in display.columns and display[col].dtype in [int, float]:
            display[col] = display[col].apply(
                lambda v: f"{int(v):,}" if pd.notna(v) else ""
            )

    display.columns = [col.replace("_", " ").title() for col in display.columns]
    st.dataframe(display, use_container_width=True)


def render_persona_profiles(df_profile, n_personas, group_label=None):
    key_suffix = group_label.replace(" ", "_").replace("/", "") if group_label else "overall"
    st.subheader("Persona deep-dive")
    st.caption("Select a persona to see the distribution of key variables within that cluster.")

    persona_id = st.selectbox(
        "Select persona",
        list(range(n_personas)),
        format_func=lambda x: f"Persona {x}",
        key=f"persona_select_{key_suffix}",
    )

    sub = df_profile[df_profile["persona"] == persona_id].copy()

    count_row = sub[sub["variable"] == "_count"]
    if not count_row.empty:
        n = count_row[count_row["value"] == "n"]["proportion"].values
        wn = count_row[count_row["value"] == "weighted_n"]["proportion"].values
        c1, c2 = st.columns(2)
        c1.metric("Respondents", f"{int(n[0]):,}" if len(n) else "N/A")
        c2.metric("Weighted N", f"{wn[0]:,.0f}" if len(wn) else "N/A")

    profile_vars = [v for v in sub["variable"].unique() if not v.startswith("_")]
    cols = st.columns(2)
    for i, var in enumerate(profile_vars):
        var_sub = sub[sub["variable"] == var]
        if var_sub.empty:
            continue
        if set(var_sub["value"].tolist()) == {"mean"}:
            val = var_sub["proportion"].iloc[0]
            cols[i % 2].metric(var.replace("_", " ").title(), f"{val:.1f}")
        else:
            s = var_sub.set_index("value")["proportion"].sort_values(ascending=False)
            with cols[i % 2]:
                _hbar(s, var.replace("_", " ").title(),
                      key=f"persona_{key_suffix}_{persona_id}_{var}")


def render_comparison(df_profile, n_personas, group_label=None):
    key_suffix = group_label.replace(" ", "_").replace("/", "") if group_label else "overall"
    st.subheader("Persona comparison")
    st.caption("Compare the distribution of one variable across all personas.")

    profile_vars = [v for v in df_profile["variable"].unique() if not v.startswith("_")]
    selected_var = st.selectbox(
        "Select variable", profile_vars,
        format_func=lambda v: v.replace("_", " ").title(),
        key=f"persona_compare_var_{key_suffix}",
    )

    sub = df_profile[df_profile["variable"] == selected_var].copy()

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
    st.plotly_chart(fig, use_container_width=True, key=f"persona_compare_{key_suffix}")


def _render_persona_tab(df_centroids_g, df_profile_g, group_label, group_col):
    n_personas = df_centroids_g["persona"].nunique()
    render_centroid_table(df_centroids_g, group_col=group_col, group_label=group_label)
    st.divider()
    if df_profile_g is not None and not df_profile_g.empty:
        tab1, tab2 = st.tabs(["Deep-dive", "Comparison"])
        with tab1:
            render_persona_profiles(df_profile_g, n_personas, group_label=group_label)
        with tab2:
            render_comparison(df_profile_g, n_personas, group_label=group_label)
    else:
        st.warning("Persona profile data not found for this group.")


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.header("Personas")
    st.caption(
        "We develop cluster-based respondent profiles (i.e. archetypes) based on the "
        "profiles of formative research participants. This approach is used in "
        "user-centred design and marketing to create representative \"customer personas\" "
        "that help teams empathise with their target audience and make informed design decisions."
    )
    st.markdown("""
### Methodology
Personas were derived using **k-modes clustering**, a variant of k-means adapted for
categorical data. Unlike k-means, k-modes uses modes (most frequent values) rather than
means as cluster centres, and measures dissimilarity by the number of mismatching
categories between observations — making it well-suited to survey responses.

**Clustering is run separately within each group below** (gender, or FP-use status) so
that within-group variation drives the clusters rather than the split variable itself.

**Clustering variables:** age, occupation, religion, and life goals (plus gender, when
splitting by FP-use status instead of gender — see below).

**Configuration:** 3 clusters per group, initialised using the Cao method (which selects
starting centroids based on category frequency distributions to reduce sensitivity to
random starting points), with 5 independent runs to improve stability. Results are fully
reproducible (fixed random seed).

**Output:** Each persona represents the modal respondent within a cluster — the
combination of attribute values that best characterises that group. Cluster size (N and
weighted N) is shown for each persona. Individual-level data is not stored or displayed.
    """)
    st.markdown("")

    # ── Split selector ────────────────────────────────────────────────────────
    split_choice = st.radio(
        "View personas by", list(SPLIT_CONFIG.keys()), horizontal=True, key="personas_split_by",
    )
    cfg = SPLIT_CONFIG[split_choice]
    group_col, display_map, colors_map = cfg["group_col"], cfg["display"], cfg["colors"]
    if split_choice == "FP use status":
        st.caption(
            "\"Using FP\" = current_use/past_use per the formative baseline survey's `use` "
            "field; \"Not using FP\" = non-user/future-user. Same 3-clusters-per-group "
            "k-modes methodology as the Gender view above, just split on a different variable."
        )

    df_centroids_g = cfg["load_centroids"]()
    df_profile_g   = cfg["load_profile"]()
    df_elbow       = cfg["load_elbow"]()

    if df_centroids_g is None or df_centroids_g.empty:
        st.warning(_MISSING)
        return

    # ── Elbow plot ────────────────────────────────────────────────────────────
    if df_elbow is not None and not df_elbow.empty:
        with st.expander("Elbow plot — choosing number of clusters", expanded=False):
            render_elbow_plot(df_elbow, group_col, display_map, colors_map, split_choice)

    # ── Group tabs ────────────────────────────────────────────────────────────
    groups_in_data = df_centroids_g[group_col].unique().tolist()
    tab_labels = [display_map.get(g, g) for g in groups_in_data]
    tabs = st.tabs(tab_labels)

    for tab, group_label in zip(tabs, groups_in_data):
        with tab:
            c_sub = df_centroids_g[df_centroids_g[group_col] == group_label].copy()
            p_sub = (
                df_profile_g[df_profile_g[group_col] == group_label].copy()
                if df_profile_g is not None else None
            )
            _render_persona_tab(c_sub, p_sub, group_label, group_col)

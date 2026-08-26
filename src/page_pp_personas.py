"""Phone Pulse — Personas: FP users vs non-users.

Unlike the Formative Research "Personas" page (k-modes demographic clusters),
this is a direct two-group comparison: everyone currently using FP
(fpbeh_fpnow == 1) vs everyone not, across every question domain the Phone
Pulse app tracks (attitudes, access, media habits, social norms, knowledge,
non-use reasons). Source: 2_phone pulse/analysis/personas_users_vs_nonusers.py,
which pulls the "Using FP" / "Not using FP" rows out of every pp_*.csv this
app already loads and ranks every variable/category by the gap between the
two groups — the biggest gaps are what actually distinguish the personas.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import load_pp_personas_comparison

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"

_MISSING = (
    "Persona comparison data not found. Generate it with "
    "`cd \"2_phone pulse/analysis\" && python3 personas_users_vs_nonusers.py`, "
    "then copy `outputs/persona_comparison_full.csv` to "
    "`niger_app/data/pp_personas_comparison.csv`."
)


def _gap_chart(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    sub = df.reindex(df["gap"].abs().sort_values(ascending=False).index).head(top_n)
    sub = sub.sort_values("gap")
    colors = [FEM_NAVY if g > 0 else FEM_ORANGE for g in sub["gap"]]
    fig = go.Figure(go.Bar(
        x=sub["gap"], y=sub["item"], orientation="h",
        marker_color=colors,
        text=sub["gap"].map(lambda v: f"{v:+.1f}"),
        textposition="outside",
        cliponaxis=False,
    ))
    fig.add_vline(x=0, line_color="#999")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        title=f"Top {len(sub)} differences between FP users and non-users",
        xaxis_title="Gap (Using FP − Not using FP)",
        margin=dict(l=10, r=60, t=50, b=10),
        height=max(320, 30 * len(sub) + 100),
        showlegend=False,
    )
    return fig


def render() -> None:
    try:
        df = load_pp_personas_comparison()
    except Exception:
        df = None
    if df is None or df.empty:
        st.warning(_MISSING)
        return

    st.markdown("### Phone Pulse — Personas: FP users vs non-users")
    st.caption(
        "\"Using FP\" = fpbeh_fpnow == 1; \"Not using FP\" = everyone else, "
        "restricted to the Treatment analysis sample (FEM partner-station "
        "listeners who passed QA, n=414). Every variable/category tracked "
        "elsewhere in this app — attitudes, access barriers, media habits, "
        "social norms, knowledge, non-use reasons — is compared here and "
        "ranked by the size of the gap between the two groups."
    )
    st.info(
        "**Headline finding:** the two personas look similar on most items "
        "(attitudes, radio habits, social norms). Differences concentrate in "
        "a handful of access-to-services and knowledge items — which is close "
        "to definitional, since access questions are largely gated on having "
        "engaged with services in the first place — rather than a broad "
        "attitudinal divide."
    )
    st.markdown("---")

    fig = _gap_chart(df)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Navy = higher among FP users, orange = higher among non-users. "
        "`pct`-type items are percentage points; `mean`-type items (e.g. "
        "attitude scores) are on the item's own scale — see the table below."
    )

    st.markdown("#### Full comparison")
    search = st.text_input("Filter by keyword (question, category, or source page)", "")
    table = df.copy()
    if search:
        mask = table["item"].str.contains(search, case=False, na=False) | \
               table["source_file"].str.contains(search, case=False, na=False)
        table = table[mask]

    display = table.rename(columns={
        "source_file": "Question page", "type": "Type", "item": "Item",
        "value_using": "Using FP", "value_notusing": "Not using FP",
        "gap": "Gap", "n_using": "n (users)", "n_notusing": "n (non-users)",
    })
    display["Question page"] = display["Question page"].str.replace("pp_", "").str.replace(".csv", "")
    st.dataframe(
        display[["Question page", "Item", "Type", "Using FP", "Not using FP", "Gap",
                  "n (users)", "n (non-users)"]],
        use_container_width=True, hide_index=True,
    )
    st.caption(f"{len(display)} of {len(df)} variable/category comparisons shown, sorted by gap size.")

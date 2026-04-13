"""
page_drivers_barriers.py  —  improved version
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.data_loader import (
    load_drivers_barriers, parse_subgroup_prevalence,
    parse_statements, get_priority_sort_key,
    USER_CATEGORY_LABELS, AGE_GROUPS, GENDERS,
)
from src.fem_colours import PRIORITY_COLORS, FEM_PALETTE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_hausa(text: str) -> str:
    """Return only the English part of a bilingual 'Hausa / English' label."""
    if "/" in str(text):
        english = str(text).split("/", 1)[1].strip()
        return english if english else str(text).strip()
    return str(text).strip()


def render_priority_badge(priority):
    color = PRIORITY_COLORS.get(str(priority).strip(), "#6b7280")
    return (
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:12px;font-weight:600;">{priority}</span>'
    )


def _overall_prevalence(row):
    """Best-effort: return a single numeric overall prevalence (0-100) for a row."""
    for col in ["Overall prevalence", "Prevalence overall", "overall", "Overall"]:
        if col in row.index and pd.notna(row[col]):
            try:
                return float(str(row[col]).replace("%", "").strip())
            except ValueError:
                pass
    # fall back: average the user-category subgroup values
    data = parse_subgroup_prevalence(row.get("Prevalence (All)", ""))
    if data:
        return sum(data.values()) / len(data)
    return None


def build_overview_chart(df, db_type, split_key="user_category"):
    """
    Consolidated grouped horizontal bar chart showing ALL drivers/barriers.

    Each item gets one bar per subgroup (user category, gender, or age),
    matching the example image.  Items are sorted highest → lowest priority,
    then by the maximum prevalence across subgroups within each priority band.

    The legend shows subgroup names only — no "trace 0" or priority entries.
    """
    # ── Collect per-subgroup prevalence for every row ──────────────────────
    PREV_COL_MAP = {
        "user_category": "Prevalence (All)",
        "gender":        "GENDER: Prevalence (All)",
        "age":           "AGE_GROUP: Prevalence (All)",
    }
    prev_col = PREV_COL_MAP.get(split_key, "Prevalence (All)")

    records = []
    for _, row in df.iterrows():
        data = parse_subgroup_prevalence(row.get(prev_col, ""))
        if not data:
            # fallback: try the user_category column
            data = parse_subgroup_prevalence(row.get("Prevalence (All)", ""))
        if not data:
            # last resort: single bar from averaged value
            avg = _overall_prevalence(row)
            data = {"Overall": avg} if avg is not None else {}

        # Apply human-readable labels for user categories
        if split_key == "user_category":
            data = {USER_CATEGORY_LABELS.get(k, k): v for k, v in data.items()}

        name     = _strip_hausa(str(row["Name"]))
        priority = str(row["Priority"]).strip()
        max_prev = max(data.values()) if data else 0
        records.append({
            "name":     name,
            "priority": priority,
            "_sort":    get_priority_sort_key(priority),
            "max_prev": max_prev,
            "data":     data,
        })

    if not records:
        return go.Figure()

    # ── Sort: priority high→low, then prevalence high→low within band ──────
    plot_df = (
        pd.DataFrame(records)
        .sort_values(["_sort", "max_prev"], ascending=[False, False])
        .reset_index(drop=True)
    )

    # ── Collect all subgroup keys in a stable order ────────────────────────
    all_groups: list[str] = []
    for data in plot_df["data"]:
        for k in data:
            if k not in all_groups:
                all_groups.append(k)

    # Colours per subgroup — use the FEM palette; cycle if >5 groups
    group_colors = {g: FEM_PALETTE[i % len(FEM_PALETTE)] for i, g in enumerate(all_groups)}

    item_names = plot_df["name"].tolist()
    priority_of = dict(zip(plot_df["name"], plot_df["priority"]))

    # ── One trace per subgroup ─────────────────────────────────────────────
    traces = []
    for grp in all_groups:
        x_vals = [row_data.get(grp, None) for row_data in plot_df["data"]]
        text_vals = [
            f"{v:.1f}%" if v is not None else ""
            for v in x_vals
        ]
        traces.append(go.Bar(
            name=grp,
            y=item_names,
            x=x_vals,
            orientation="h",
            marker_color=group_colors[grp],
            text=text_vals,
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                + grp + ": %{x:.1f}%<br>"
                "Priority: %{customdata}<extra></extra>"
            ),
            customdata=[priority_of[n] for n in item_names],
        ))

    fig = go.Figure(traces)

    # ── Priority band dividers (subtle horizontal lines between bands) ─────
    # Find y-positions where priority changes
    priorities = plot_df["priority"].tolist()
    divider_positions = []
    for i in range(1, len(priorities)):
        if get_priority_sort_key(priorities[i]) != get_priority_sort_key(priorities[i - 1]):
            divider_positions.append(i - 0.5)

    shapes = [
        dict(
            type="line",
            x0=0, x1=1, xref="paper",
            y0=pos, y1=pos, yref="y",
            line=dict(color="#cccccc", width=1, dash="dot"),
        )
        for pos in divider_positions
    ]

    # ── Priority band annotations on the right margin ─────────────────────
    # Label the first item in each band
    annotations = []
    seen_priorities = set()
    for i, row in plot_df.iterrows():
        p = row["priority"]
        if p not in seen_priorities:
            seen_priorities.add(p)
            color = PRIORITY_COLORS.get(p, "#6b7280")
            annotations.append(dict(
                x=1.01, xref="paper",
                y=row["name"], yref="y",
                text=f"<b>{p}</b>",
                showarrow=False,
                xanchor="left",
                font=dict(color=color, size=11),
            ))

    max_x = max(
        (v for d in plot_df["data"] for v in d.values() if v is not None),
        default=10,
    )

    fig.update_layout(
        title=f"All {db_type}s — prevalence by {split_key.replace('_', ' ')}",
        barmode="group",
        xaxis=dict(
            title="% of respondents",
            showgrid=False,
            range=[0, max_x * 1.4],
        ),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=280, r=180, t=48, b=10),
        height=max(500, len(plot_df) * 52 + 100),
        legend=dict(
            title=split_key.replace("_", " ").title(),
            orientation="v",
            x=1.02, y=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        shapes=shapes,
        annotations=annotations,
        showlegend=True,
    )
    return fig


def build_prevalence_bar(row, split="user_category", show_counts=False):
    """
    Build prevalence bar chart for a single driver/barrier.
    If show_counts=True, plot raw n and weighted n side-by-side instead of %.
    """
    COUNT_COL_MAP = {
        "user_category": ("N (All)", "Weighted N (All)"),
        "gender":        ("GENDER: N (All)", "GENDER: Weighted N (All)"),
        "age":           ("AGE_GROUP: N (All)", "AGE_GROUP: Weighted N (All)"),
    }

    if split == "user_category":
        data = parse_subgroup_prevalence(row.get("Prevalence (All)", ""))
        labels = [USER_CATEGORY_LABELS.get(k, k) for k in data.keys()]
        n_col, wn_col = COUNT_COL_MAP["user_category"]
    elif split == "gender":
        data = parse_subgroup_prevalence(row.get("GENDER: Prevalence (All)", ""))
        labels = list(data.keys())
        n_col, wn_col = COUNT_COL_MAP["gender"]
    elif split == "age":
        data = parse_subgroup_prevalence(row.get("AGE_GROUP: Prevalence (All)", ""))
        labels = list(data.keys())
        n_col, wn_col = COUNT_COL_MAP["age"]
    else:
        data, labels = {}, []
        n_col, wn_col = None, None

    values = list(data.values())
    if not values:
        return None

    if show_counts:
        # Try to parse n and weighted_n from dedicated columns
        n_data    = parse_subgroup_prevalence(row.get(n_col, "")) if n_col else {}
        wn_data   = parse_subgroup_prevalence(row.get(wn_col, "")) if wn_col else {}

        # Fallback: derive n from prevalence × total if count columns absent
        traces = []
        if n_data:
            n_labels = [USER_CATEGORY_LABELS.get(k, k) for k in n_data] if split == "user_category" else list(n_data.keys())
            traces.append(go.Bar(
                name="Raw n",
                y=n_labels,
                x=list(n_data.values()),
                orientation="h",
                marker_color=FEM_PALETTE[0],
                text=[f"{int(v):,}" for v in n_data.values()],
                textposition="outside",
                cliponaxis=False,
            ))
        if wn_data:
            wn_labels = [USER_CATEGORY_LABELS.get(k, k) for k in wn_data] if split == "user_category" else list(wn_data.keys())
            traces.append(go.Bar(
                name="Weighted n",
                y=wn_labels,
                x=list(wn_data.values()),
                orientation="h",
                marker_color=FEM_PALETTE[2],
                text=[f"{v:,.1f}" for v in wn_data.values()],
                textposition="outside",
                cliponaxis=False,
            ))

        if not traces:
            # columns not in data — show a note
            return None

        fig = go.Figure(traces)
        max_x = max(
            max(n_data.values(), default=0),
            max(wn_data.values(), default=0),
        )
        fig.update_layout(
            barmode="group",
            margin=dict(l=0, r=80, t=4, b=4),
            height=max(100, len(labels) * 52 + 40),
            xaxis=dict(range=[0, max_x * 1.35], showgrid=False, title="Count"),
            yaxis=dict(showgrid=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.2),
            font=dict(size=12),
        )
        return fig

    # ── Default: prevalence % ─────────────────────────────────────────────────
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=FEM_PALETTE[:len(labels)],
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=0, r=60, t=4, b=4),
        height=max(80, len(labels) * 36),
        xaxis=dict(
            range=[0, max(values) * 1.35],
            showticklabels=False,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=12),
    )
    return fig


def build_statement_chart(row, split="user_category"):
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

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=FEM_PALETTE[:len(labels)],
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


# ── Main render ───────────────────────────────────────────────────────────────

def render(df_raw=None):
    st.header("Drivers & Barriers")

    if df_raw is None:
        df_raw = load_drivers_barriers()

    # ── Controls ──────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        db_type = st.radio("Show", ["Driver", "Barrier"], horizontal=True)
    with col2:
        split_by = st.radio(
            "Split by", ["User category", "Gender", "Age group"], horizontal=True
        )
    with col3:
        priority_filter = st.multiselect(
            "Priority filter",
            ["Very high", "High", "Medium", "Low"],
            default=["Very high", "High", "Medium", "Low"],
        )

    split_key = {
        "User category": "user_category",
        "Gender":        "gender",
        "Age group":     "age",
    }[split_by]

    # ── Filter ────────────────────────────────────────────────────────────────
    df = df_raw[df_raw["Driver/Barrier"].str.lower() == db_type.lower()].copy()
    if priority_filter:
        df = df[df["Priority"].isin(priority_filter)]
    df["_sort"] = df["Priority"].apply(get_priority_sort_key)
    df = df.sort_values("_sort", ascending=False).reset_index(drop=True)

    if df.empty:
        st.info("No data matches the current filters.")
        return

    # ── Overview chart ────────────────────────────────────────────────────────
    st.markdown("### Overview — all items at a glance")
    st.caption(
        "Bars coloured by priority level. "
        "Prevalence = % of respondents who mentioned this as a main driver/barrier."
    )
    st.plotly_chart(
        build_overview_chart(df, db_type, split_key=split_key),
        use_container_width=True,
        key="overview_chart",
    )

    st.divider()
    st.markdown(f"### Detail cards — {len(df)} main {db_type.lower()}(s) shown")

    dcol1, dcol2 = st.columns([3, 1])
    with dcol1:
        st.caption("Sorted by priority, then by prevalence. Click any item to expand.")
    with dcol2:
        show_counts = st.toggle(
            "Show counts (n)",
            value=False,
            help=(
                "Switch between % prevalence and actual respondent counts. "
                "Raw n = number of survey responses. "
                "Weighted n = effective sample size after applying survey weights. "
                "Large gaps between the two indicate unequal weighting."
            ),
        )

    # ── Detail cards as expanders ─────────────────────────────────────────────
    for card_idx, (_, row) in enumerate(df.iterrows()):
        name_raw = str(row["Name"])
        name     = _strip_hausa(name_raw)
        priority = str(row["Priority"]).strip()

        # Respondent count (if column present)
        n_label = ""
        for n_col in ["N", "n", "n_respondents", "Respondents"]:
            if n_col in row.index and pd.notna(row[n_col]):
                try:
                    n_label = f"  ·  n = {int(row[n_col]):,}"
                except (ValueError, TypeError):
                    pass
                break

        badge_color = PRIORITY_COLORS.get(priority, "#6b7280")
        expander_label = f"**{name}**  —  {priority}{n_label}"

        with st.expander(expander_label, expanded=False):
            st.markdown(
                f'<span style="background:{badge_color};color:white;padding:2px 10px;'
                f'border-radius:12px;font-size:12px;font-weight:600;">'
                f'{priority} priority — main {db_type.lower()}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            fig_prev = build_prevalence_bar(row, split_key, show_counts=show_counts)
            if fig_prev:
                label = ("*Respondent counts (raw n vs weighted n)*"
                         if show_counts else
                         "*Prevalence — % of respondents who mentioned this*")
                st.markdown(label)
                st.plotly_chart(
                    fig_prev, use_container_width=True,
                    key=f"prev_{card_idx}",
                )

            stmt, fig_stmt = build_statement_chart(row, split_key)
            if fig_stmt:
                stmt_text = stmt if stmt else "Related belief statement"
                st.markdown(f"*Agreement with: \"{stmt_text}\"*")
                st.plotly_chart(
                    fig_stmt, use_container_width=True,
                    key=f"stmt_{card_idx}",
                )

            if not fig_prev and not fig_stmt:
                st.info("No chart data available for this item.")

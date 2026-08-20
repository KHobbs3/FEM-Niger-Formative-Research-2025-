"""Phone Pulse — Radio listenership page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import (
    load_pp_radio_any,
    load_pp_radio_uptake,
    load_pp_radio_days,
    load_pp_radio_hours,
    load_pp_radio_stations,
    load_pp_radio_fp_stations,
)

FEM_ORANGE = "#C1693A"
FEM_NAVY   = "#2E3F52"
FEM_TAUPE  = "#7A7068"
FEM_BROWN  = "#8B5E45"
FEM_STEEL  = "#5A6E7F"

SPLIT_OPTIONS = {
    "FP use status": {
        "split_by": "fp_use",
        "order":  ["Using FP", "Not using FP", "All"],
        "colors": {"Using FP": FEM_NAVY, "Not using FP": FEM_ORANGE, "All": FEM_TAUPE},
    },
    "Gender": {
        "split_by": "gender",
        "order":  ["Male", "Female", "All"],
        "colors": {"Male": FEM_STEEL, "Female": FEM_BROWN, "All": FEM_TAUPE},
    },
    "Treatment / Comparison": {
        "split_by": "treatment_arm",
        "order":  ["Treatment", "Comparison", "All"],
        "colors": {"Treatment": FEM_NAVY, "Comparison": FEM_ORANGE, "All": FEM_TAUPE},
    },
}

_CHART = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")


def _filter_split(df: pd.DataFrame, split_by: str) -> pd.DataFrame:
    """Filter a df to one split dimension. Older/cached exports without a
    split_by column (pre-gender-slicing) are passed through unfiltered."""
    if "split_by" not in df.columns:
        return df
    return df[df["split_by"] == split_by]


def _grouped_hbar(df: pd.DataFrame, title: str, group_order: list, group_colors: dict,
                  xmax: float = 100, caption: str = "") -> None:
    fig = go.Figure()
    n_cats = df["category"].nunique()
    has_n = "n_assigned" in df.columns
    has_nr = "n_no_response" in df.columns
    for grp in group_order:
        sub = df[df["group"] == grp].sort_values("pct")
        if sub.empty:
            continue
        trace_kw = {}
        if has_n and has_nr:
            trace_kw["customdata"] = sub[["n_assigned", "n_no_response"]].to_numpy()
            trace_kw["hovertemplate"] = (
                "%{y}: %{x:.1f}%% (%{customdata[0]:.0f} assigned; "
                "%{customdata[1]:.0f} did not answer)<extra>%{fullData.name}</extra>"
            )
        elif has_n:
            trace_kw["customdata"] = sub[["n_assigned"]].to_numpy()
            trace_kw["hovertemplate"] = (
                "%{y}: %{x:.1f}%% (%{customdata[0]:.0f} assigned to this station)<extra>%{fullData.name}</extra>"
            )
        fig.add_trace(go.Bar(
            x=sub["pct"], y=sub["category"], orientation="h",
            name=grp, marker_color=group_colors[grp],
            text=sub["pct"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
            **trace_kw,
        ))
    fig.update_layout(
        **_CHART,
        title=title, barmode="group",
        xaxis_title="% of respondents",
        xaxis_range=[0, xmax + 15],
        height=max(250, 35 * n_cats * len(group_order) + 100),
        margin=dict(l=10, r=30, t=78, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
    if caption:
        st.caption(caption)


def _stations_composition_chart(
    df: pd.DataFrame,
    yes_label: str = "Listened (Yes)",
    no_label: str = "Did not listen (No)",
    no_response_label: str = "No response (left blank)",
    title: str = "What the denominator is made of: Yes / No / No response",
) -> None:
    """
    Stacked bar, one row per station: how the "%" denominator actually
    breaks down — Yes / No / No response (left blank) — in raw counts.
    Answers "is this 0% real or missing data?" directly in the chart
    instead of only on hover. Always shows the "All" group of whichever
    split is active (this is about denominator transparency, not a
    sub-group comparison). Reused for both the listenership chart and the
    per-station FP-content chart — hence the customizable labels.
    """
    if not {"n_assigned", "n_no_response"}.issubset(df.columns):
        return
    sub = df[df["group"] == "All"].copy()
    if sub.empty:
        return
    sub["n_no"] = sub["n_assigned"] - sub["count"] - sub["n_no_response"]
    sub = sub.sort_values("pct")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub["count"], y=sub["category"], orientation="h",
        name=yes_label, marker_color=FEM_NAVY,
    ))
    fig.add_trace(go.Bar(
        x=sub["n_no"], y=sub["category"], orientation="h",
        name=no_label, marker_color=FEM_TAUPE,
    ))
    fig.add_trace(go.Bar(
        x=sub["n_no_response"], y=sub["category"], orientation="h",
        name=no_response_label, marker_color=FEM_ORANGE,
    ))
    fig.update_layout(
        **_CHART,
        title=title,
        barmode="stack",
        xaxis_title="Number of respondents assigned to this station",
        height=max(300, 28 * sub["category"].nunique() + 120),
        margin=dict(l=10, r=30, t=78, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Same stations/order as the chart above, in raw counts instead of %. A "
        "station with a long orange (\"no response\") segment relative to its "
        "total bar means a chunk of its 0%/low% came from unanswered questions, "
        "not confirmed non-listenership — a long taupe (\"No\") segment means "
        "people were actually asked and said no."
    )


def render() -> None:
    st.markdown("### Phone Pulse — Radio Listenership")

    view = st.radio("View by", list(SPLIT_OPTIONS.keys()), horizontal=True, key="pp_radio_split")
    split = SPLIT_OPTIONS[view]
    split_by, order, colors = split["split_by"], split["order"], split["colors"]

    caption = f"Results broken down by {view.lower()}. Base for station / hours / days charts: radio listeners only."
    if view == "Treatment / Comparison":
        caption += (
            " Note: this view uses a DIFFERENT, larger population than the other two "
            "(all 509 QA-passed respondents, not just the 414 Treatment/FEM-station "
            "listeners) — Treatment = FEM partner station listener, Comparison = "
            "everyone else (see the Campaign Exposure page for the full definition)."
        )
    st.caption(caption)
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Listenership", "FP content heard", "Listening days",
        "Daily hours", "Stations", "FP Content by Station"
    ])

    with tab1:
        df = _filter_split(load_pp_radio_any(), split_by)
        _grouped_hbar(df, "Radio listenership", order, colors,
                      caption="Base: all respondents.")

    with tab2:
        df = _filter_split(load_pp_radio_uptake(), split_by)
        _grouped_hbar(df, "Heard FP content on radio", order, colors,
                      caption="Base: all respondents.")

    with tab3:
        df = _filter_split(load_pp_radio_days(), split_by)
        _grouped_hbar(df, "Days of the week listeners tune in", order, colors,
                      caption="Base: radio listeners only.")

    with tab4:
        df = _filter_split(load_pp_radio_hours(), split_by)
        # Vertical bar for ordered buckets
        fig = go.Figure()
        hour_order = ["<1 hr", "1 hr", "2 hrs", "3 hrs", "4 hrs", "5–6 hrs", "7+ hrs"]
        for grp in order:
            sub = df[df["group"] == grp].copy()
            sub["_ord"] = sub["category"].map({v: i for i, v in enumerate(hour_order)})
            sub = sub.sort_values("_ord")
            if sub.empty:
                continue
            fig.add_trace(go.Bar(
                x=sub["category"], y=sub["pct"],
                name=grp, marker_color=colors[grp],
                text=sub["pct"].map(lambda v: f"{v:.0f}%"),
                textposition="outside",
            ))
        fig.update_layout(
            **_CHART,
            title="Daily listening hours (among radio listeners)",
            barmode="group", yaxis_title="% of listeners",
            yaxis_range=[0, 80],
            height=405,
            margin=dict(l=10, r=10, t=78, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.15),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Base: radio listeners only.")

    with tab5:
        with st.expander("Survey question asked"):
            st.markdown(
                "> \"Let's now think in particular about **{station}**.\n>\n"
                "> Have you listened to **{station}** in the last month?\"\n\n"
                "Asked once per station the respondent is assigned to (`{station}` is "
                "filled in with that respondent's actual assigned station name each "
                "time — e.g. \"Radio Tarka\" or \"Haddin Kay Dakoro\"), yes/no.¹"
            )
            st.markdown(
                "**Only asked at all if the respondent said they listen to radio in "
                "general** (a prior yes/no question) — respondents who said they "
                "don't listen to radio at all never see this question for any "
                "station, and their answer is blank/\"no response\" for every "
                "station they're assigned to. That's a structural skip, not a data "
                "gap for that individual — but it does mean part of any station's "
                "\"no response\" count in the chart below is these non-radio-listeners, "
                "not people who listen to radio but skipped this one question."
            )
            st.caption(
                "Sources:  1. field `radio_partner_1_listen` (and the equivalent "
                "`radio_partner_N_listen` / `radio_partner_placebo_listen` for each "
                "station slot), `label`/`relevance` columns — `2_phone pulse/meta/"
                "Participants_Appels de Suivi.xlsx`, sheet `survey`; relevance "
                "condition on field `radio_any`."
            )

        df = _filter_split(load_pp_radio_stations(), split_by)
        title = "Station listenership (among respondents assigned to that station)"
        _grouped_hbar(
            df, title, order, colors,
            caption=(
                "Base for each station's % is respondents ASSIGNED to that station "
                "(it covers their settlement) — not all respondents, and not the same "
                "denominator per station. Hover a bar to see how many respondents that "
                "station was assigned to, and how many left the listening question "
                "blank (\"did not answer\") rather than answering \"No\" — a 0% with a "
                "high did-not-answer count isn't the same result as a 0% where everyone "
                "actually answered \"No\". A 100% on a station assigned to only 1-2 "
                "people isn't a strong result either. Placebo (non-partner control) "
                "stations are excluded here — see the Media page for per-respondent "
                "placebo detail."
            ),
        )
        st.markdown("#### Denominator detail")
        _stations_composition_chart(df)

    with tab6:
        with st.expander("Survey question asked"):
            st.markdown(
                "> \"How frequently have you heard these programs or ads in the "
                "last few months on **{station}**?\"\n\n"
                "Asked once per station the respondent is assigned to, same "
                "\"fill in the actual station name\" pattern as the Stations tab. "
                "Scale: Never / Once a month / Once a week / Several times a "
                "week / Every day / Several times a day.¹ This chart collapses "
                "that scale to \"heard at all\" (anything but \"Never\") vs. "
                "\"Never\" vs. no response — see the Media page for the full "
                "frequency breakdown among those who heard something."
            )
            st.markdown(
                "**Only asked if the respondent said they listen to that "
                "specific station** (verified in the exported data: this field "
                "is blank for every respondent who didn't report listening to "
                "that station) — so \"no response\" here is usually much larger "
                "than on the Stations tab. That's expected: it includes everyone "
                "assigned to the station who doesn't listen to it, not a data gap."
            )
            st.caption(
                "Sources:  1. field `uptake_fp_freq_radio_1` (and the equivalent "
                "`uptake_fp_freq_radio_N` / `uptake_fp_freq_radio_placebo` for "
                "each station slot), `label` column — `2_phone pulse/meta/"
                "Participants_Appels de Suivi.xlsx`, sheet `survey`."
            )

        df = _filter_split(load_pp_radio_fp_stations(), split_by)
        if df is None:
            st.info(
                "Data pending: run `export_pp_app_data.py`, upload "
                "`pp_radio_fp_stations.csv` to Drive, then paste its file ID "
                "into `data_loader.py`."
            )
        else:
            title = "Heard FP/MCH content by station (among respondents assigned to that station)"
            _grouped_hbar(
                df, title, order, colors,
                caption=(
                    "Base for each station's % is respondents ASSIGNED to that "
                    "station — same denominator convention as the Stations tab. "
                    "\"Heard\" = any frequency other than \"Never\". Hover a bar "
                    "for n_assigned and no-response counts."
                ),
            )
            st.markdown("#### Denominator detail")
            _stations_composition_chart(
                df,
                yes_label="Heard FP content",
                no_label="Never heard (explicit)",
                no_response_label="No response (incl. non-listeners of this station)",
                title="What the denominator is made of: Heard / Never / No response",
            )

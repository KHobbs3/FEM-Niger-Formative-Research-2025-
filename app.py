import streamlit as st
from streamlit_option_menu import option_menu

from src.page_drivers_barriers import render as render_drivers_barriers
from src.page_radio import render as render_radio
from src.page_personas import render as render_personas
from src.page_statements import render as render_agreement_characteristics
from src.page_access import render as render_access
from src.page_family_planning import render as render_family_planning
from src.page_personality_traits import render as render_personality_traits

# from src.page_stubs import (
    # render_personas,
    # render_agreement_characteristics,
    # render_family_planning,
    # render_personality_traits,
    # render_access,
# )

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FEM Survey Analysis — Niger (2025)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# FEM colour palette (warm terracotta -> taupe -> steel -> navy)
FEM_ORANGE  = "#C1693A"
FEM_BROWN   = "#8B5E45"
FEM_TAUPE   = "#7A7068"
FEM_STEEL   = "#5A6E7F"
FEM_NAVY    = "#2E3F52"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Top bar colour */
    [data-testid="stHeader"] {{ background: {FEM_STEEL}; }}

    /* Main title text — ensure black */
    h1, h2, h3 {{ color: {FEM_BROWN} !important; }}

    /* Nav menu tweaks */
    .nav-link {{ font-size: 13px !important; padding: 4px 8px !important; }}
    .nav-link-selected {{ background-color: {FEM_BROWN} !important; }}

    /* Tighten plotly chart margins */
    .js-plotly-plot {{ margin-bottom: -1rem; }}

    /* Divider colour */
    hr {{ border-color: #e5e7eb !important; margin: 0.6rem 0 !important; }}

    /* Priority badge alignment */
    .stMarkdown p {{ margin-bottom: 0.2rem; }}
</style>
""", unsafe_allow_html=True)

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='margin-bottom:0.2rem;color:{FEM_BROWN};'>FEM Survey Analysis - Niger (2025)</h2>",
    unsafe_allow_html=True,
)

# ── Navigation ────────────────────────────────────────────────────────────────
selected = option_menu(
    menu_title=None,
    options=[
        "Personas",
        "Drivers & Barriers",
        "Agreement & Characteristics",
        "Radio",
        "Family Planning",
        "Personality Traits",
        "Access & Supply",
    ],
    icons=[
        "people-fill",
        "speedometer2",
        "card-checklist",
        "speaker-fill",
        "house-heart-fill",
        "file-earmark-person-fill",
        "fa-syringe",
    ],
    menu_icon="cast",
    default_index=1,
    orientation="horizontal",
    styles={
        "container": {"background-color": FEM_TAUPE, "padding": "0", "margin": "0"},
        "icon":      {"color": FEM_ORANGE, "font-size": "14px"},
        "nav-link":  {"padding": "4px 10px", "--hover-color": FEM_STEEL},
        "nav-link-selected": {"background-color": FEM_NAVY},
    },
)

st.markdown("")  # breathing room

# ── Route to pages ────────────────────────────────────────────────────────────
if selected == "Personas":
    render_personas()

elif selected == "Drivers & Barriers":
    render_drivers_barriers()

elif selected == "Agreement & Characteristics":
    render_agreement_characteristics()

elif selected == "Radio":
    render_radio()

elif selected == "Family Planning":
    render_family_planning()

elif selected == "Personality Traits":
    render_personality_traits()

elif selected == "Access & Supply":
    render_access()

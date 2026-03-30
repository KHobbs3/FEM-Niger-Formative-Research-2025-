import streamlit as st

def _stub_card(title, description, fields):
    st.markdown(f"""
    <div style="background:#fafafa;border:1.5px dashed #d1d5db;border-radius:10px;padding:1.5rem;margin-bottom:1rem;">
        <p style="font-size:1rem;font-weight:600;color:#374151;margin:0 0 0.4rem;">{title} — pending data</p>
        <p style="color:#6b7280;margin:0 0 1rem;font-size:0.9rem;">{description}</p>
        <p style="color:#9ca3af;font-size:0.82rem;margin:0;"><strong>Expected data fields:</strong> {", ".join(fields)}</p>
    </div>
    """, unsafe_allow_html=True)


# def render_personas():
#     st.header("Personas")
#     st.caption("Cluster-based respondent profiles derived from survey data.")
    # _stub_card(
    #     "Persona profiles",
    #     "Once survey microdata is available, personas will be generated via k-prototypes clustering on age, gender, occupation, religion, and life goals.",
    #     ["Cluster ID", "Age (centroid)", "Gender", "Occupation", "Religion", "Life goals", "Count"]
    # )
    # _stub_card(
    #     "Persona characteristics table",
    #     "Summary of key traits per persona cluster.",
    #     ["Marriage duration", "Number of children", "Education", "Pregnancy status", "Household spending"]
    # )


def render_agreement_characteristics():
    st.header("Agreement & Characteristics")
    st.caption("Agreement with belief statements and respondent characteristics, with demographic splits.")

    # _stub_card(
    #     "Agreement with statements",
    #     "Heatmap/table of % agreement with each belief statement, filterable by gender, age, and user category.",
    #     ["Statement text", "% Agree (All)", "% Agree (Male)", "% Agree (Female)", "% Agree by age group"]
    # )
    # _stub_card(
    #     "Characteristics table",
    #     "Summary statistics of demographic and behavioural traits across the survey sample.",
    #     ["Trait name", "Most common value (mode)", "Mean (numeric traits)", "Split by gender / age / urban-rural"]
    # )


def render_family_planning():
    st.header("Family Planning")
    st.caption("Contraceptive awareness, preferences, and method-specific data.")

    _stub_card(
        "Method preferences",
        "Why respondents prefer traditional/religious vs. medical contraceptive methods.",
        ["Method type", "Reason", "% of respondents", "Split by user category"]
    )
    _stub_card(
        "Contraceptive awareness",
        "Awareness and use of specific contraceptive methods.",
        ["Method name", "% Aware", "% Ever used", "% Currently using"]
    )


def render_personality_traits():
    st.header("Personality Traits")
    st.caption("Role models, health belief formation, life goals, and influencers.")

    _stub_card(
        "Who do you look up to?",
        "Role models and trusted figures in health decisions.",
        ["Role model type", "% of respondents", "Split by gender / age"]
    )
    _stub_card(
        "How do you form health beliefs?",
        "Sources and processes through which respondents form health-related beliefs.",
        ["Belief formation source", "% of respondents"]
    )
    _stub_card(
        "Life goals",
        "Most and least wanted life goals.",
        ["Goal", "% Most wanted", "% Least wanted"]
    )


def render_supply():
    st.header("Supply")
    st.caption("Cost, location, availability, and health facility experience data.")

    _stub_card(
        "Costs",
        "Perceptions and realities of contraceptive costs among users and non-users.",
        ["Cost bracket", "% Users who paid", "% Non-users who expect to pay", "Too expensive? (Y/N %)"]
    )
    _stub_card(
        "Location & travel time",
        "Distance to health centres and where contraceptives are obtained.",
        ["Distance bracket (mins)", "% of respondents", "Location of last obtained method"]
    )
    _stub_card(
        "Health facility experience",
        "Quality of interactions with health workers, split by user category.",
        ["Experience category", "% Users", "% Non-users", "% Past users"]
    )
    _stub_card(
        "Availability",
        "Whether desired methods are available at local facilities.",
        ["Available? (Y/N)", "% Users", "% Non-users"]
    )

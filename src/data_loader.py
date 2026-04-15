import pandas as pd
import re
import streamlit as st
import os

# ── Raw data loader (only used by pages not yet on the pipeline) ──────────────

def load_raw_data(path="../table_analysis/data/2_cleaned/fem_survey_niger_mapped.csv"):
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    return df


# ── Pre-aggregated loaders (safe: no PII) ─────────────────────────────────────

DATA_DIR = "data"

def _load(file_id, **kwargs):
    # path = os.path.join(DATA_DIR, filename)
    # if not os.path.exists(path):
    #     return None
    return pd.read_csv("https://drive.google.com/uc?export=download&id="+file_id, **kwargs)


# @st.cache_data
def load_drivers_barriers():
    # df = pd.read_csv(path, low_memory=False)
    # df.columns = df.columns.str.strip()
    return _load("1xf4Gkm70WKMC0R_zN6SJZ9JSEqdZUMt9") #"1_sKBFc3b32PjHatgIaBY-SSyKlSjCTTQ") - november 2025 version


def load_statement_labels(path="data/statement_labels.csv"):
    # df = pd.read_csv(path, encoding="ISO-8859-1", low_memory=False)
    # df.columns = df.columns.str.strip()
    # df.dropna(axis=0, how="all", inplace=True)
    # return df
    return _load("1cVSOTJ6VA8FGVUmt8Xw3klBOEobdBqpN")


# ── Access page ───────────────────────────────────────────────────────────────

# @st.cache_data
def load_access_stockouts():
    return _load("1EBowX6uQpTx-fX45a8a-I1QO-qz4UwcR")

# @st.cache_data
def load_access_stockout_responses():
    return _load("1Le5TxvRVT2uQYe-fQQUZikUqduMng3hP", index_col=0)

# @st.cache_data
def load_access_travel():
    return _load("18jWrVGiGDfOw8AZNCNQs5bsuiH8z18Pr", index_col=0)

# @st.cache_data
def load_access_affordability():
    return _load("1ahsiIFxBX-ZjPZ_inL6YCu-Df-W0ClW2", index_col=0)
    # return _load("access_affordability.csv", index_col=0)

# @st.cache_data
def load_access_composite():
    return _load("1pcCZAUorv8coIqW2k_yjkQNXX8rpaSUR", index_col=0)


# ── Statements page ───────────────────────────────────────────────────────────

# @st.cache_data
def load_statements_heatmap():
    return _load("1ezpz_FqegwF1GAPrhtsjQARHI9xxEjT9")

# ── Radio page ──────────────────────────────────────────────────────
def clean_column_name(col):
    col = re.sub(r'^\d+_\d+_', '', col)
    col = re.sub(r'_+\d+$', '', col)
    col = col.replace('_', ' ').strip().title()
    return col

# @st.cache_data
def load_radio_by_station():
    df = _load("1MNO6t_yappsE5ZVp4l2jlZA7qvh1gs5i") #"1l2n9CJcenNTt7CUpf-krApXe9fDsi4r4") November 2025 version
    df.set_index(df.columns[0], inplace=True)
    return df

def load_radio_by_state():
    df = _load("1fMMjeFEEoM6EUgIPC4sNa5xcyi3lOakw")
    df.set_index(df.columns[0], inplace=True)
    return df

# ── Family planning page ──────────────────────────────────────────────────────

# @st.cache_data
def load_fp_funnel():
    return _load("1HfnLz7AaEBRVkWcX5sv8F9uUnmFveju-")

# @st.cache_data
def load_fp_timing():
    return _load("1Oa8g4iGf_IuJiMriVUSZTFILGkutG29c")

# @st.cache_data
def load_fp_methods():
    return _load("1qus99-nxSJVZSbX1x7yA7wCTJyRpCZPQ")

# @st.cache_data
def load_fp_reason_use():
    return _load("1KRrqi-N_tj3GoFAXD8pmns2GgXdxZzws")

# @st.cache_data
def load_fp_intent():
    return _load("1n4r4uPOmsqvMADJDncrvxvzpIFF0y48r")

# @st.cache_data
def load_fp_nonuse_reasons():
    return _load("1My0suLDCypo9G0xbHdMuaHrUocZJKMix")


# ── Personality page ──────────────────────────────────────────────────────────

# @st.cache_data
def load_personality_life_goals():
    return _load("13TCMkDQj1y2X2VrmHBPc_8p098EOI3KY")

# @st.cache_data
def load_personality_goals_achievable():
    return _load("1A5kkyQfiZX_m-e6FqNXMJn75uKDvHhh-")

# @st.cache_data
def load_personality_role_models():
    return _load("1o0zX7lLFPTtJ1yCexMQTFdxara5hawwJ", index_col=0)

# @st.cache_data
def load_personality_likeable_traits():
    return _load("1XjDJRro4Sof1LB_XIfYumwtQJ3QTTmSX")

# @st.cache_data
def load_personality_forming_beliefs():
    return _load("1cRzqqLNGC9PfG7KjGkYJPykDmWCFKxia")

# @st.cache_data
def load_personality_decision_confident():
    return _load("1g1P6ZpElSAzGO09_KGeAgkeenIA8lYYd")

# @st.cache_data
def load_personality_wellbeing():
    return _load("1qnlGPl5N2D0syOBQjSvGe9HAldGi-WfB")


# ── Personas page ─────────────────────────────────────────────────────────────

# @st.cache_data
def load_personas_centroids():
    return _load("1qCO4Oh7j4oiK3ZEf28SrxIqNt01CiBAC")

# @st.cache_data
def load_personas_profile():
    return _load("1gbbOIVYiPTV0TKRg2n568I7hlwvcleK4")


# ── Shared parsing helpers (used by drivers/barriers) ─────────────────────────

def parse_subgroup_prevalence(cell_str):
    result = {}
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return result
    for line in str(cell_str).split("\n"):
        line = line.strip()
        match = re.match(r"^(.+?):\s*([\d.]+)%", line)
        if match:
            result[match.group(1).strip()] = float(match.group(2))
    return result


def parse_statements(cell_str):
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return None, {}
    lines = [l.strip() for l in str(cell_str).split("\n") if l.strip()]
    statement = None
    percentages = {}
    for line in lines:
        match = re.match(r"^(.+?):\s*([\d.]+)%", line)
        if match:
            percentages[match.group(1).strip()] = float(match.group(2))
        elif statement is None and "%" not in line:
            statement = line
    return statement, percentages


PRIORITY_ORDER = {"Very high": 4, "High": 3, "Medium": 2, "Low": 1}

def get_priority_sort_key(p):
    return PRIORITY_ORDER.get(str(p).strip(), 0)

USER_CATEGORY_LABELS = {
    "user":        "Current user",
    "non_user":    "Non-user",
    "future_user": "Future user",
    "past_user":   "Past user",
}

AGE_GROUPS  = ["16-20", "21-30", "31-45"]
GENDERS     = ["Mace / Femme", "Namiji / Homme"]
URBAN_RURAL = ["Rurale", "Semi-urbaine", "Urbaine"]

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.data_loader import load_radio
import re
from src.fem_colours import FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY, FEM_SCALE

# @st.cache_data

# def load_radio_data(path="data/radio_summary.csv"):
#     try:
#         df = pd.read_csv(path, index_col=0)
#         df.columns = [clean_column_name(c) for c in df.columns]
#         return df
#     except FileNotFoundError:
#         return None

def parse_radio_cell(cell_str):
    result = {}
    if pd.isna(cell_str) or str(cell_str).strip() == "":
        return result
    text = str(cell_str)
    pattern = re.findall(r"([^\n%]+?)\s*\n\s*([\d.]+)%", text)
    for name, pct in pattern:
        name = name.strip()
        if re.search(r"ban sani|prefer not|nafi son", name, re.IGNORECASE):
            continue
        result[name] = float(pct)
    return result


def shorten_question(q):
    first = q.split("\n")[0].strip()
    if len(first) > 100:
        first = first[:100] + "..."
    return first

def render_heatmap(df, question, min_pct=5):
    row = df.loc[question]
    stations_by_loc = {loc: parse_radio_cell(row[loc]) for loc in row.index}

    all_stations = set()
    for d in stations_by_loc.values():
        all_stations.update(k for k, v in d.items() if v >= min_pct)
    all_stations = sorted(all_stations)

    if not all_stations:
        st.info("No stations meet the minimum reach threshold. Try lowering it.")
        return

    locations = list(stations_by_loc.keys())
    matrix = []
    text_matrix = []
    for st_name in all_stations:
        row_vals = [stations_by_loc[loc].get(st_name, None) for loc in locations]
        matrix.append(row_vals)
        text_matrix.append([f"{v:.0f}%" if v is not None else "" for v in row_vals])


    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=locations,
        y=all_stations,
        colorscale=FEM_SCALE,
        text=text_matrix,
        texttemplate="%{text}",
        showscale=True,
        hoverongaps=False,
        zmin=0,
        zmax=100,
        colorbar=dict(title="Reach %", thickness=12, len=0.8),
    ))
    fig.update_layout(
        height=max(320, len(all_stations) * 30 + 100),
        margin=dict(l=10, r=10, t=10, b=80),
        xaxis=dict(side="bottom", tickangle=-35, tickfont=dict(size=11)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

def render(df=None):
    st.header("Radio")
    df = load_radio()

    if df is None:
        df = load_radio_data()

    if df is None:
        st.info("No radio data file found. Upload your radio summary CSV below.")
        uploaded = st.file_uploader("Upload radio_summary.csv", type="csv")
        if uploaded:
            df = pd.read_csv(uploaded, index_col=0)
            df.columns = [clean_column_name(c) for c in df.columns]
            st.success("Data loaded.")
        else:
            return

    questions = df.index.tolist()
    short_labels = [shorten_question(q) for q in questions]
    label_to_full = dict(zip(short_labels, questions))

    col1, col2 = st.columns([4, 1])
    with col1:
        selected_label = st.selectbox("Select question", short_labels)
    with col2:
        min_pct = st.slider("Min reach %", min_value=0, max_value=30, value=5, step=1)

    selected_q = label_to_full[selected_label]
    st.caption(selected_q)
    render_heatmap(df, selected_q, min_pct)

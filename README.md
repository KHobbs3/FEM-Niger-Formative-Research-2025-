# FEM Survey Analysis — Niger (2025)

Streamlit dashboard for visualising FEM survey results from Niger.

## Project structure

```
<project_root>/
├── pipeline/          ← new (outside app, has PII access)
└── niger_app/         ← existing app (never touches PII)
    └── data/          ← pipeline writes CSVs here


niger_app/
├── app.py                          # Main entry point
├── requirements.txt
├── data/
│   ├── drivers_barriers.csv        # from table_analysis output
│   └── radio_summary.csv           # from table_analysis output
└── src/
    ├── data_loader.py              # Shared parsing utilities
    ├── page_drivers_barriers.py
    ├── page_radio.py               # requires user upload
    └── page_stubs.py               # TODO
```

## Pages status

| Page | Status | Data needed |
|------|--------|-------------|
| Drivers & Barriers |   Ready | `data/drivers_barriers.csv` |
| Radio | Ready (upload in app) | `data/radio_summary.csv` |
| Personas | Stub | Cluster/persona summary table |
| Agreement & Characteristics | Stub | Statement agreement + traits table |
| Family Planning | stub | Methods awareness/preference table |
| Personality Traits | Stub | Role models, life goals, influencers |
| Addressability | Stub | Cost, location, availability tables |

## Local setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run pipeline to process data
# From project root
python pipeline/run_pipeline.py

# 3. Run the app
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repository
2. Go to https://share.streamlit.io
3. Connect your repo, set main file to `app.py`
4. Deploy — no secrets needed for the current data setup

## Radio data format

`data/radio_summary.csv` should have:
- **Rows**: question text (e.g. "Which radio stations do you listen to most often?")
- **Columns**: location/community names
- **Cells**: multiline text like:
  ```
  Station Name
   XX.X%
  
  Another Station
   YY.Y%
  ```

This matches the format of the radio snippet you already have.

## Adding new pages

When data is ready for a stub page:
1. Create `src/page_PAGENAME.py` with a `render()` function
2. Replace the corresponding stub call in `app.py` with `render_PAGENAME()`
3. Add data file to `data/`

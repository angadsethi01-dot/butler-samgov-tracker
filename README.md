# Butler Aerospace SAM.gov Opportunity Tracker

This is a single Streamlit dashboard for finding active SAM.gov opportunities that Butler Aerospace & Defense could realistically care about as a prime, subcontractor, teaming partner, or business-development intelligence lead.

## Quick Start

```bash
cd butler_samgov_tracker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SAM_API_KEY="your-sam-key"
python refresh.py --mode daily --debug
streamlit run app.py
```

The website reads saved datasets. It does not call SAM.gov on every page load, filter change, or click.

## Manual Backfill

```bash
python refresh.py --mode backfill --backfill-days 30 --debug
```

Backfill is intentionally manual and should not run daily.

## Generated Data

The refresh process writes:

- `data/raw/latest_successful_raw_results.json`
- `data/processed/latest_successful_processed_results.csv`
- `data/processed/latest_successful_processed_results.parquet`
- `data/processed/partial_refresh_results.csv`
- `data/processed/partial_refresh_results.parquet`
- `data/processed/failed_queries.csv`
- `data/processed/refresh_log.csv`
- `data/processed/rejected_results.csv`
- `data/exports/main_results.xlsx`
- `data/exports/main_results.csv`
- `data/exports/rejected_results.csv`
- `data/exports/partial_refresh_results.csv`
- `data/exports/failed_queries.csv`
- `data/exports/refresh_log.csv`

The app keeps showing the last successful data when a refresh fails or is incomplete.


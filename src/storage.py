from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    MAIN_COLUMNS,
    PROCESSED_DIR,
    RAW_DIR,
    REJECTED_COLUMNS,
)
from src.exporter import create_exports


META_PATH = PROCESSED_DIR / "latest_refresh_meta.json"
MAIN_CSV = PROCESSED_DIR / "latest_successful_processed_results.csv"
MAIN_PARQUET = PROCESSED_DIR / "latest_successful_processed_results.parquet"
PARTIAL_CSV = PROCESSED_DIR / "partial_refresh_results.csv"
PARTIAL_PARQUET = PROCESSED_DIR / "partial_refresh_results.parquet"
REJECTED_CSV = PROCESSED_DIR / "rejected_results.csv"
FAILED_CSV = PROCESSED_DIR / "failed_queries.csv"
REFRESH_LOG_CSV = PROCESSED_DIR / "refresh_log.csv"
RAW_JSON = RAW_DIR / "latest_successful_raw_results.json"
PARTIAL_RAW_JSON = RAW_DIR / "partial_refresh_raw_results.json"


def ensure_dirs() -> None:
    for path in [PROCESSED_DIR, RAW_DIR, PROCESSED_DIR.parent / "exports", PROCESSED_DIR.parent / "logs"]:
        path.mkdir(parents=True, exist_ok=True)


def dedupe_by_notice_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Notice ID" not in df.columns:
        return df
    sort_cols = [col for col in ["Due Date", "Refresh Status"] if col in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols), na_position="last")
    return df.drop_duplicates(subset=["Notice ID"], keep="first")


def safe_to_parquet(df: pd.DataFrame, path: Path) -> None:
    try:
        df.to_parquet(path, index=False)
    except Exception:
        # CSV remains the guaranteed portable artifact when parquet engines are absent.
        pass


def load_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns or [])


def load_meta() -> dict[str, Any]:
    if META_PATH.exists():
        return json.loads(META_PATH.read_text())
    return {
        "refresh_status": "No successful refresh yet",
        "last_refresh_timestamp": "",
        "accepted_results": 0,
        "rejected_results": 0,
        "failed_queries": 0,
        "api_calls_made": 0,
        "capacity_used": "0/0",
        "search_sources_completed": [],
        "search_sources_skipped": [],
        "raw_results_pulled": 0,
    }


def load_display_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    meta = load_meta()
    status = meta.get("refresh_status", "")
    main_path = PARTIAL_CSV if str(status).startswith("Partial") and PARTIAL_CSV.exists() else MAIN_CSV
    return (
        load_csv(main_path, MAIN_COLUMNS),
        load_csv(REJECTED_CSV, REJECTED_COLUMNS),
        load_csv(FAILED_CSV),
        load_csv(REFRESH_LOG_CSV),
        meta,
    )


def should_overwrite_successful(
    accepted_count: int,
    raw_count: int,
    had_errors: bool,
    capacity_reached: bool,
    all_priority_completed: bool,
) -> bool:
    if accepted_count > 0:
        return True
    return raw_count == 0 and not had_errors and not capacity_reached and all_priority_completed


def save_refresh(
    raw_records: list[dict],
    processed_rows: list[dict],
    failed_queries: list[dict],
    status: str,
    api_calls_made: int,
    max_api_calls: int,
    completed_sources: list[str],
    skipped_sources: list[str],
    mode: str,
) -> dict[str, Any]:
    ensure_dirs()
    now = datetime.now().isoformat(timespec="seconds")
    processed_df = pd.DataFrame(processed_rows)
    accepted_df = processed_df[processed_df.get("Fit Category", pd.Series(dtype=str)).isin(["A", "B", "C"])].copy()
    rejected_df = processed_df[processed_df.get("Fit Category", pd.Series(dtype=str)).eq("D")].copy()
    accepted_df = accepted_df.reindex(columns=MAIN_COLUMNS)
    rejected_df = rejected_df.reindex(columns=REJECTED_COLUMNS)
    accepted_df = dedupe_by_notice_id(accepted_df)
    rejected_df = dedupe_by_notice_id(rejected_df)
    failed_df = pd.DataFrame(failed_queries)
    had_errors = bool(failed_queries)
    capacity_reached = "Capacity Reached" in status
    all_priority_completed = not skipped_sources and not had_errors

    previous_success = load_csv(MAIN_CSV, MAIN_COLUMNS)
    if status.startswith("Partial"):
        merged = dedupe_by_notice_id(pd.concat([accepted_df, previous_success], ignore_index=True))
        merged.to_csv(PARTIAL_CSV, index=False)
        safe_to_parquet(merged, PARTIAL_PARQUET)
        PARTIAL_RAW_JSON.write_text(json.dumps(raw_records, indent=2, default=str))
        display_df = merged
    elif should_overwrite_successful(
        accepted_count=len(accepted_df),
        raw_count=len(raw_records),
        had_errors=had_errors,
        capacity_reached=capacity_reached,
        all_priority_completed=all_priority_completed,
    ):
        accepted_df.to_csv(MAIN_CSV, index=False)
        safe_to_parquet(accepted_df, MAIN_PARQUET)
        RAW_JSON.write_text(json.dumps(raw_records, indent=2, default=str))
        display_df = accepted_df
    else:
        status = "Failed Refresh — Using Cache" if previous_success.empty else "No new successful refresh — Using Cache"
        display_df = previous_success

    rejected_df.to_csv(REJECTED_CSV, index=False)
    failed_df.to_csv(FAILED_CSV, index=False)

    log_entry = {
        "timestamp": now,
        "mode": mode,
        "refresh_status": status,
        "raw_results_pulled": len(raw_records),
        "accepted_results": len(accepted_df),
        "rejected_results": len(rejected_df),
        "failed_queries": len(failed_df),
        "skipped_queries": len(skipped_sources),
        "api_calls_made": api_calls_made,
        "capacity_used": f"{api_calls_made}/{max_api_calls}",
        "search_sources_completed": "; ".join(completed_sources),
        "search_sources_skipped": "; ".join(skipped_sources),
    }
    prior_log = load_csv(REFRESH_LOG_CSV)
    refresh_log = pd.concat([prior_log, pd.DataFrame([log_entry])], ignore_index=True)
    refresh_log.to_csv(REFRESH_LOG_CSV, index=False)

    meta = {
        "refresh_status": status,
        "last_refresh_timestamp": now,
        "raw_results_pulled": len(raw_records),
        "accepted_results": len(accepted_df),
        "rejected_results": len(rejected_df),
        "failed_queries": len(failed_df),
        "skipped_queries": len(skipped_sources),
        "api_calls_made": api_calls_made,
        "capacity_used": f"{api_calls_made}/{max_api_calls}",
        "search_sources_completed": completed_sources,
        "search_sources_skipped": skipped_sources,
        "mode": mode,
    }
    META_PATH.write_text(json.dumps(meta, indent=2))

    create_exports(
        main_df=display_df,
        rejected_df=rejected_df,
        failed_df=failed_df,
        refresh_log_df=refresh_log,
        partial_df=display_df if status.startswith("Partial") else accepted_df,
    )
    return meta

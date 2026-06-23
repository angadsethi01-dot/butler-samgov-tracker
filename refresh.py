from __future__ import annotations

import argparse
from datetime import date

from config import RefreshSettings
from src.attachment_reader import enrich_notices_with_attachment_text
from src.classifier import classify_notice
from src.sam_client import SamClient
from src.storage import save_refresh


def run_refresh(
    mode: str = "daily",
    backfill_days: int = 30,
    debug: bool = False,
    today: date | None = None,
    api_key: str | None = None,
) -> dict:
    settings = RefreshSettings()
    client = SamClient(api_key=api_key, settings=settings)
    plan = client.build_query_plan(mode=mode, backfill_days=backfill_days, today=today)
    refresh_result = client.run_refresh(plan)
    enrich_notices_with_attachment_text(
        refresh_result.raw_records,
        api_key=client.api_key,
        settings=settings,
        session=client.session,
    )
    rows = [
        classify_notice(
            notice,
            search_source=notice.get("_search_source", ""),
            refresh_status=refresh_result.status,
            today=today,
        )
        for notice in refresh_result.raw_records
    ]
    meta = save_refresh(
        raw_records=refresh_result.raw_records,
        processed_rows=rows,
        failed_queries=refresh_result.failed_queries,
        status=refresh_result.status if mode == "daily" else refresh_result.status.replace("Refresh", "Backfill"),
        api_calls_made=refresh_result.api_calls_made,
        max_api_calls=settings.max_api_calls,
        completed_sources=refresh_result.completed_sources,
        skipped_sources=refresh_result.skipped_sources,
        mode=mode,
    )
    if debug:
        print(f"Refresh status: {meta['refresh_status']}")
        print(f"Raw records: {meta['raw_results_pulled']}")
        print(f"Accepted: {meta['accepted_results']}")
        print(f"Rejected: {meta['rejected_results']}")
        print(f"Failed queries: {meta['failed_queries']}")
        print(f"API calls: {meta['capacity_used']}")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Butler SAM.gov opportunity tracker data.")
    parser.add_argument("--mode", choices=["daily", "backfill"], default="daily")
    parser.add_argument("--backfill-days", type=int, default=30)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    run_refresh(mode=args.mode, backfill_days=args.backfill_days, debug=args.debug)


if __name__ == "__main__":
    main()

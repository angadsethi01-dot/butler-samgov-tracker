from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import requests

from config import (
    APPROVED_PSC_CODES,
    BROADER_KEYWORDS,
    HIGH_PRIORITY_ORGS,
    HIGH_VALUE_KEYWORDS,
    INCLUDED_PTYPES,
    LIMIT,
    MEDIUM_PRIORITY_ORGS,
    PRIMARY_NAICS,
    RefreshSettings,
    SAM_API_KEY_ENV,
    SAM_ENDPOINT,
    SECONDARY_NAICS,
)

PLACEHOLDER_KEYS = {"paste_your_sam_key_here", "your_key_here", "your-sam-key", ""}


def sam_date(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def date_window(mode: str, backfill_days: int = 30, today: date | None = None) -> dict[str, str]:
    today = today or date.today()
    lookback = 7 if mode == "daily" else max(30, min(backfill_days, 90))
    return {
        "postedFrom": sam_date(today - timedelta(days=lookback)),
        "postedTo": sam_date(today),
        "rdlfrom": sam_date(today),
        "rdlto": sam_date(today + timedelta(days=90)),
        "status": "active",
        "limit": LIMIT,
    }


def redact_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: ("[REDACTED]" if key == "api_key" else value) for key, value in params.items()}


def query_signature(params: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    keys = [
        "postedFrom",
        "postedTo",
        "rdlfrom",
        "rdlto",
        "status",
        "ptype",
        "ncode",
        "ccode",
        "organizationCode",
        "title",
        "keyword",
        "offset",
    ]
    return tuple((key, str(params.get(key, ""))) for key in keys)


def invalid_api_key_reason(api_key: str | None) -> str:
    key = (api_key or "").strip()
    if key.lower() in PLACEHOLDER_KEYS:
        return "Missing API key" if not key else "Placeholder API key"
    return ""


@dataclass
class QueryPlanItem:
    priority: int
    source: str
    params: dict[str, Any]


@dataclass
class SamRefreshResult:
    raw_records: list[dict] = field(default_factory=list)
    failed_queries: list[dict] = field(default_factory=list)
    completed_sources: list[str] = field(default_factory=list)
    skipped_sources: list[str] = field(default_factory=list)
    api_calls_made: int = 0
    capacity_reached: bool = False
    partial: bool = False
    status: str = "Successful Refresh"


class SamClient:
    def __init__(
        self,
        api_key: str | None = None,
        settings: RefreshSettings | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv(SAM_API_KEY_ENV, "")
        self.settings = settings or RefreshSettings()
        self.session = session or requests.Session()
        self._seen_signatures: dict[tuple[tuple[str, str], ...], dict] = {}
        self._api_calls = 0

    def build_query_plan(self, mode: str = "daily", backfill_days: int = 30, today: date | None = None) -> list[QueryPlanItem]:
        base = date_window(mode, backfill_days=backfill_days, today=today)
        plan: list[QueryPlanItem] = []

        for ncode in PRIMARY_NAICS:
            plan.append(QueryPlanItem(1, f"Primary NAICS {ncode}", {**base, "ncode": ncode}))
        for ccode in APPROVED_PSC_CODES:
            plan.append(QueryPlanItem(2, f"PSC {ccode}", {**base, "ccode": ccode}))
        for org in HIGH_PRIORITY_ORGS:
            plan.append(QueryPlanItem(3, f"High-priority org {org}", {**base, "organizationCode": org}))
        for keyword in HIGH_VALUE_KEYWORDS:
            plan.append(QueryPlanItem(4, f"High-value keyword: {keyword}", {**base, "title": keyword}))
        for ncode in SECONDARY_NAICS:
            plan.append(QueryPlanItem(5, f"Secondary NAICS {ncode}", {**base, "ncode": ncode}))
        for org in MEDIUM_PRIORITY_ORGS:
            plan.append(QueryPlanItem(6, f"Medium-priority org {org}", {**base, "organizationCode": org}))
        for keyword in BROADER_KEYWORDS:
            plan.append(QueryPlanItem(6, f"Broader keyword: {keyword}", {**base, "title": keyword}))

        ptypes = ",".join(INCLUDED_PTYPES)
        for item in plan:
            item.params["ptype"] = ptypes
        return sorted(plan, key=lambda item: item.priority)

    def run_refresh(self, plan: list[QueryPlanItem]) -> SamRefreshResult:
        result = SamRefreshResult()
        api_key_error = invalid_api_key_reason(self.api_key)
        if api_key_error:
            result.status = "Failed Refresh — Using Cache"
            result.failed_queries.append(
                {
                    "error_type": api_key_error,
                    "query_parameters": {},
                    "http_status_code": "",
                    "retry_count": 0,
                    "cached_data_used": True,
                    "partial_results_preserved": False,
                }
            )
            return result

        for item in plan:
            if self._api_calls >= self.settings.max_api_calls:
                result.capacity_reached = True
                result.partial = True
                result.skipped_sources.append(item.source)
                continue
            try:
                records = self._fetch_query(item, result)
                for record in records:
                    record["_search_source"] = item.source
                result.raw_records.extend(records)
                result.completed_sources.append(item.source)
            except CapacityReached:
                result.capacity_reached = True
                result.partial = True
                result.skipped_sources.append(item.source)
            except Exception as exc:  # pragma: no cover - defensive path
                result.partial = True
                result.failed_queries.append(
                    {
                        "error_type": type(exc).__name__,
                        "query_parameters": redact_params(item.params),
                        "http_status_code": "",
                        "retry_count": self.settings.retry_attempts,
                        "cached_data_used": False,
                        "partial_results_preserved": bool(result.raw_records),
                    }
                )

        result.api_calls_made = self._api_calls
        if result.capacity_reached:
            result.status = "Partial Refresh — Capacity Reached"
        elif result.partial or result.failed_queries:
            result.status = "Partial Refresh"
        else:
            result.status = "Successful Refresh"
        return result

    def _fetch_query(self, item: QueryPlanItem, result: SamRefreshResult) -> list[dict]:
        records: list[dict] = []
        offset = 0
        total_records: int | None = None
        for page in range(self.settings.max_pages_per_query):
            params = {**item.params, "offset": offset, "api_key": self.api_key}
            signature = query_signature(params)
            if signature in self._seen_signatures:
                payload = self._seen_signatures[signature]
            else:
                if self._api_calls >= self.settings.max_api_calls:
                    raise CapacityReached
                payload = self._request(params, result)
                self._seen_signatures[signature] = payload
            page_records = payload.get("opportunitiesData") or payload.get("data") or []
            if not isinstance(page_records, list):
                raise ValueError("Malformed response: opportunitiesData is not a list")
            records.extend(page_records)
            total_records = int(payload.get("totalRecords") or len(records) or 0)
            if total_records <= LIMIT or len(records) >= total_records:
                break
            offset += LIMIT
        if total_records and len(records) < total_records:
            result.partial = True
            result.failed_queries.append(
                {
                    "error_type": "Pagination stopped early",
                    "query_parameters": redact_params(item.params),
                    "http_status_code": "",
                    "retry_count": 0,
                    "cached_data_used": False,
                    "partial_results_preserved": bool(records),
                }
            )
        return records

    def _request(self, params: dict[str, Any], result: SamRefreshResult) -> dict:
        last_error: Exception | None = None
        response_status = ""
        for attempt in range(self.settings.retry_attempts):
            try:
                self._api_calls += 1
                response = self.session.get(
                    SAM_ENDPOINT,
                    params=params,
                    timeout=self.settings.request_timeout_seconds,
                )
                response_status = str(response.status_code)
                if response.status_code in {401, 403}:
                    raise PermissionError("Authentication failure")
                if response.status_code == 429:
                    raise RateLimitError("Rate limit / too many requests")
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Malformed response")
                return payload
            except Exception as exc:
                last_error = exc
                if attempt < self.settings.retry_attempts - 1:
                    sleep_for = self.settings.backoff_seconds[min(attempt, len(self.settings.backoff_seconds) - 1)]
                    time.sleep(sleep_for)
        result.failed_queries.append(
            {
                "error_type": type(last_error).__name__ if last_error else "Unknown API error",
                "query_parameters": redact_params(params),
                "http_status_code": response_status,
                "retry_count": self.settings.retry_attempts,
                "cached_data_used": False,
                "partial_results_preserved": True,
            }
        )
        raise last_error or RuntimeError("SAM.gov request failed")


class CapacityReached(Exception):
    pass


class RateLimitError(Exception):
    pass

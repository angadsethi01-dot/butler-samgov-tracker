"""
Guard for the automated refresh workflow.

Reads the refresh metadata that refresh.py just wrote and decides whether the
pull actually returned data. If it pulled zero records (quota exhausted or the
request was throttled), we exit non-zero so the workflow STOPS before committing
— that keeps the last known-good data in the repo instead of wiping it to empty.
"""

import json
import sys
from pathlib import Path

META = Path("data/processed/latest_refresh_meta.json")

if not META.exists():
    print("::error::No refresh metadata was written — refresh.py did not complete.")
    sys.exit(1)

meta = json.loads(META.read_text())
pulled = int(meta.get("raw_results_pulled", 0) or 0)
accepted = int(meta.get("accepted_results", 0) or 0)
status = meta.get("refresh_status", "")

print(f"raw_pulled={pulled}  accepted={accepted}  status={status!r}")

if pulled == 0:
    print("::error::Refresh pulled 0 records (SAM.gov quota exhausted or throttled). "
          "NOT committing — keeping the last good data so the dashboard is not wiped.")
    sys.exit(1)

print(f"Refresh OK: {pulled} raw / {accepted} accepted. Proceeding to commit.")

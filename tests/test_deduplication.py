import pandas as pd

from src.storage import dedupe_by_notice_id


def test_deduplicate_by_notice_id():
    df = pd.DataFrame(
        [
            {"Notice ID": "same", "Opportunity Title": "Old", "Due Date": "2026-07-01"},
            {"Notice ID": "same", "Opportunity Title": "New", "Due Date": "2026-08-01"},
        ]
    )
    deduped = dedupe_by_notice_id(df)
    assert len(deduped) == 1
    assert deduped.iloc[0]["Opportunity Title"] == "New"


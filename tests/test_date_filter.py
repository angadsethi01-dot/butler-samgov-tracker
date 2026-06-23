from datetime import date, timedelta

from src.classifier import classify_notice


def test_expired_deadline_excluded():
    row = classify_notice(
        {
            "noticeId": "expired",
            "title": "Aircraft engineering support",
            "description": "Systems engineering and testing for aircraft.",
            "department": "Department of Defense",
            "type": "o",
            "naicsCode": "541330",
            "responseDeadLine": (date(2026, 6, 23) - timedelta(days=1)).isoformat(),
            "status": "active",
        },
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "D"
    assert row["Rejection Reason"] == "Expired response deadline"


def test_response_deadline_misspelling_supported():
    row = classify_notice(
        {
            "noticeId": "due",
            "title": "Aircraft engineering support",
            "description": "Systems engineering and testing for aircraft.",
            "department": "Department of Defense",
            "type": "o",
            "naicsCode": "541330",
            "reponseDeadLine": (date(2026, 6, 23) + timedelta(days=5)).isoformat(),
            "status": "active",
        },
        today=date(2026, 6, 23),
    )
    assert row["Days Until Due"] == 5


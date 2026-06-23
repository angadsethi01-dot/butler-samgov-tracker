from datetime import date, timedelta

from src.classifier import classify_notice


def notice(**overrides):
    due = (date(2026, 6, 23) + timedelta(days=30)).isoformat()
    base = {
        "noticeId": "n1",
        "title": "Aircraft systems engineering support for NAVAIR",
        "description": "Systems engineering, testing, technical publications, support equipment, and repair engineering.",
        "department": "Department of Navy",
        "office": "NAVAIR",
        "type": "o",
        "naicsCode": "541330",
        "classificationCode": "R425",
        "responseDeadLine": due,
        "status": "active",
    }
    base.update(overrides)
    return base


def test_strong_aircraft_engineering_is_a():
    row = classify_notice(notice(), today=date(2026, 6, 23))
    assert row["Fit Category"] == "A"
    assert row["Status"] == "Accepted"


def test_seaport_navy_engineering_downgrades_to_c_not_d():
    row = classify_notice(
        notice(description="Task order under SeaPort-NxG for NAVAIR systems engineering and test support."),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "C"
    assert row["SeaPort / Vehicle Required"] == "Yes — SeaPort-NxG"
    assert row["Recommended Next Step"] == "Find SeaPort prime / teaming partner"


def test_t7a_hoteling_rejected():
    row = classify_notice(
        notice(title="T-7A Conference Hoteling", description="Conference hoteling, travel, food and meeting space."),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "D"
    assert "Hard reject" in row["Rejection Reason"]


def test_secondary_generic_it_rejected():
    row = classify_notice(
        notice(title="Generic web portal support", description="Commodity software and web hosting.", naicsCode="541512"),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "D"


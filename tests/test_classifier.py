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


def test_pure_hardware_manufacture_downgraded_to_c():
    # Strong manufacturing/aerospace score but the scope is pure build-to-print fabrication
    # with no design or engineering work -> Butler does not manufacture hardware -> downgrade to C.
    row = classify_notice(
        notice(
            title="CNC machining and composites fabrication of airframe components",
            description=(
                "Build to print. Manufacture and deliver airframe parts in accordance with "
                "Government-provided specifications. Off-the-shelf hardware where applicable."
            ),
            naicsCode="336413",
            classificationCode="1560",
        ),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "C"
    assert row["Status"] == "Accepted"
    assert "hardware supply/manufacturing" in row["Why It Fits Butler"].lower()


def test_redesign_hardware_stays_strong_fit():
    # Designing/redesigning hardware is squarely Butler's lane -> must remain a strong (A) fit.
    row = classify_notice(
        notice(
            title="Redesign of airframe structural bracket",
            description=(
                "Systems engineering and design analysis to redesign aircraft structural hardware "
                "and deliver an updated technical data package."
            ),
            naicsCode="541330",
        ),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "A"
    assert "hardware supply/manufacturing" not in row["Why It Fits Butler"].lower()


def test_design_and_manufacture_stays_strong_fit():
    # When design/engineering work is present alongside manufacturing language, the design
    # content keeps it a strong fit -> the supply downgrade must NOT fire.
    row = classify_notice(
        notice(
            title="Design and manufacture of aircraft test fixtures",
            description=(
                "Systems engineering, design, and redesign of aircraft tooling, including "
                "manufacture of the resulting test fixtures."
            ),
            naicsCode="541330",
        ),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "A"
    assert "hardware supply/manufacturing" not in row["Why It Fits Butler"].lower()


def test_new_manufacture_with_boilerplate_engineering_downgraded():
    # Real-world miss: a DLA "new manufacture" spares buy whose text contains procurement
    # boilerplate ("nonrecurring engineering costs", "supplier qualification"). Those words must
    # NOT shield it from the downgrade -- the deliverable is a manufactured part, so it is C.
    row = classify_notice(
        notice(
            title="CASE, COMBUSTION CHAMBER NSN 2840012620495 PN 9529M99G09",
            description=(
                "Sources sought for new manufacture of the item. Entails procurement/manufacture of "
                "component parts, inspection, testing, packaging, and shipping. Nonrecurring "
                "engineering costs may apply for supplier qualification."
            ),
            naicsCode="336412",
            classificationCode="2840",
            type="r",
        ),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "C"
    assert "hardware supply/manufacturing" in row["Why It Fits Butler"].lower()


def test_part_supply_with_engineering_drawing_reference_downgraded():
    # A bare part-supply buy that merely references a Government "engineering drawing" must still
    # be downgraded -- referencing a drawing is not doing design work.
    row = classify_notice(
        notice(
            title="F-16 RUDDER, AIRCRAFT",
            description="2 each of NSN: 1560-01-077-1314. Cadmium finish per engineering drawing.",
            naicsCode="336413",
            classificationCode="1560",
        ),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "C"


def test_keyword_matching_respects_word_boundaries():
    # Keywords must match as whole tokens, not as substrings buried in unrelated words --
    # "cadmium" must not count as CAD work, "chamber" must not count as MBE. This is what
    # previously inflated pure parts buys so non-Butler work looked like a match.
    from src.classifier import has_term

    assert not has_term("cad", "cadmium plating per drawing")
    assert not has_term("mbe", "combustion chamber housing")
    assert not has_term("road", "engineering roadmap for the railroad")
    # genuine whole-word (and simple plural) uses still match
    assert has_term("cad", "cad and plm modeling tools")
    assert has_term("mbe", "mbe and digital thread")
    assert has_term("uav", "uavs and uas platforms")


def test_low_value_hardware_supply_not_promoted():
    # A pure supply buy that is otherwise below threshold stays D -- the downgrade only caps
    # A/B items at C, it never promotes junk up to C.
    row = classify_notice(
        notice(
            title="Procurement of commercial off-the-shelf bolts",
            description="Supply of bolts. National stock number listed. Quantity of 5000.",
            naicsCode="332722",
            classificationCode="5305",
            department="General Services Administration",
            office="GSA",
        ),
        today=date(2026, 6, 23),
    )
    assert row["Fit Category"] == "D"


from src.stage_classifier import classify_stage


def test_sources_sought_from_ptype():
    assert classify_stage({"type": "r", "title": "Aircraft support"}) == "Sources Sought / RFI"


def test_rfp_from_combined_synopsis():
    assert classify_stage({"type": "k", "title": "Combined synopsis solicitation"}) == "RFP / Solicitation"


def test_rfp_from_full_sam_type_text():
    assert classify_stage({"type": "solicitation", "title": "Aircraft support"}) == "RFP / Solicitation"


def test_sources_sought_from_full_sam_type_text():
    assert classify_stage({"type": "sources_sought", "title": "Aircraft support"}) == "Sources Sought / RFI"

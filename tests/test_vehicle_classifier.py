from src.vehicle_classifier import detect_vehicle


def test_seaport_detection_fields():
    result = detect_vehicle("SeaPort-NxG contract holders only for engineering support")
    assert result["SeaPort / Vehicle Required"] == "Yes — SeaPort-NxG"
    assert result["Prime Feasibility"] == "Subcontract only"
    assert result["has_vehicle_blocker"] is True


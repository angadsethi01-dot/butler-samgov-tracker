from config import APPROVED_NAICS, PRIMARY_NAICS, SECONDARY_NAICS
from src.sam_client import SamClient


def test_query_plan_uses_only_approved_naics():
    plan = SamClient(api_key="x").build_query_plan()
    naics = {item.params["ncode"] for item in plan if "ncode" in item.params}
    assert naics == set(APPROVED_NAICS)
    assert set(PRIMARY_NAICS).issubset(naics)
    assert set(SECONDARY_NAICS).issubset(naics)


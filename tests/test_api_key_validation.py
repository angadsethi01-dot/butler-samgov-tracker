from src.sam_client import QueryPlanItem, SamClient


def test_placeholder_key_fails_fast_without_api_calls():
    client = SamClient(api_key="paste_your_sam_key_here")
    result = client.run_refresh([QueryPlanItem(1, "q", {"status": "active"})])
    assert result.status == "Failed Refresh — Using Cache"
    assert result.api_calls_made == 0
    assert result.failed_queries[0]["error_type"] == "Placeholder API key"

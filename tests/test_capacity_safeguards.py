from src.sam_client import QueryPlanItem, SamClient
from config import RefreshSettings


class FakeResponse:
    status_code = 200

    def __init__(self, idx):
        self.idx = idx

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "totalRecords": 1,
            "opportunitiesData": [
                {
                    "noticeId": f"n{self.idx}",
                    "title": "Aircraft engineering support",
                    "description": "Systems engineering for aircraft.",
                }
            ],
        }


class FakeSession:
    def __init__(self):
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse(self.calls)


def test_capacity_reached_preserves_partial_results():
    client = SamClient(api_key="key", settings=RefreshSettings(max_api_calls=2, retry_attempts=1), session=FakeSession())
    plan = [QueryPlanItem(1, f"q{i}", {"status": "active", "limit": 1000, "title": f"aircraft {i}"}) for i in range(5)]
    result = client.run_refresh(plan)
    assert result.status == "Partial Refresh — Capacity Reached"
    assert len(result.raw_records) == 2
    assert result.skipped_sources

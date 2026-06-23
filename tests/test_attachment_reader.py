from config import RefreshSettings
from src.attachment_reader import enrich_notices_with_attachment_text, extract_attachment_links
from src.classifier import classify_notice


class FakeResponse:
    status_code = 200
    headers = {"content-type": "text/plain"}
    content = b"Sources Sought for NAVAIR systems engineering, support equipment, and test planning."

    def raise_for_status(self):
        return None


class FakeSession:
    def get(self, *args, **kwargs):
        return FakeResponse()


def test_extract_attachment_links_skips_self_search_link():
    notice = {
        "resourceLinks": [
            "https://api.sam.gov/prod/opportunities/v2/search?noticeid=abc&limit=1",
            "https://sam.gov/api/prod/opps/v3/opportunities/resources/files/file-id/download",
        ]
    }
    assert extract_attachment_links(notice) == [
        "https://sam.gov/api/prod/opps/v3/opportunities/resources/files/file-id/download"
    ]


def test_attachment_text_updates_stage_and_fit():
    notice = {
        "noticeId": "att1",
        "title": "Technical support",
        "type": "",
        "department": "Department of Navy",
        "naicsCode": "541330",
        "responseDeadLine": "2026-07-10",
        "status": "active",
        "resourceLinks": ["https://sam.gov/api/prod/opps/v3/opportunities/resources/files/file-id/download"],
    }
    enrich_notices_with_attachment_text(
        [notice],
        api_key="key",
        settings=RefreshSettings(max_attachments_per_notice=1),
        session=FakeSession(),
    )
    row = classify_notice(notice, today=__import__("datetime").date(2026, 6, 23))
    assert row["Opportunity Stage"] == "Sources Sought / RFI"
    assert "attachment text read" in row["Data Confidence"].lower()

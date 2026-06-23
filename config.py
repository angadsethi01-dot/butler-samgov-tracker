from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"

SAM_ENDPOINT = "https://api.sam.gov/opportunities/v2/search"
SAM_API_KEY_ENV = "SAM_API_KEY"

MAX_API_CALLS_PER_REFRESH = 50
MAX_PAGES_PER_QUERY = 5
REQUEST_TIMEOUT_SECONDS = 30
RETRY_ATTEMPTS = 3
BACKOFF_SECONDS = [2, 5, 10]
USE_CACHE_ON_FAILURE = True
LIMIT = 1000
ENABLE_ATTACHMENT_TEXT_EXTRACTION = True
MAX_ATTACHMENTS_PER_NOTICE = 3
MAX_ATTACHMENT_BYTES = 2_000_000
MAX_ATTACHMENT_TEXT_CHARS = 20_000
ATTACHMENT_TIMEOUT_SECONDS = 20

PRIMARY_NAICS = {
    "541330": "Engineering Services",
    "541715": "R&D in Physical, Engineering, and Life Sciences",
    "336411": "Aircraft Manufacturing",
    "336412": "Aircraft Engine and Engine Parts Manufacturing",
    "336413": "Other Aircraft Parts and Auxiliary Equipment Manufacturing",
    "336414": "Guided Missile and Space Vehicle Manufacturing",
    "336415": "Guided Missile and Space Vehicle Propulsion Unit Manufacturing",
    "336419": "Other Guided Missile and Space Vehicle Parts Manufacturing",
    "541380": "Testing Laboratories and Services",
}

SECONDARY_NAICS = {
    "541512": "Computer Systems Design Services",
    "541511": "Custom Computer Programming Services",
    "541519": "Other Computer Related Services",
    "541614": "Logistics Consulting Services",
    "541690": "Other Scientific and Technical Consulting Services",
}

APPROVED_NAICS = {**PRIMARY_NAICS, **SECONDARY_NAICS}

PTYPE_MAP = {
    "r": "Sources Sought",
    "p": "Pre-Solicitation",
    "o": "Solicitation",
    "k": "Combined Synopsis/Solicitation",
    "s": "Special Notice",
    "u": "Justification / J&A",
}

EXCLUDED_PTYPES = {"a", "g"}
INCLUDED_PTYPES = tuple(PTYPE_MAP.keys())

# Conservative, A&D-leaning PSC/classification searches. These supplement NAICS
# and still pass through the Butler-fit classifier before display.
APPROVED_PSC_CODES = [
    "A",
    "AC",
    "AD",
    "AR",
    "H",
    "J",
    "K",
    "L",
    "R425",
    "R706",
    "R707",
    "R408",
    "1510",
    "1520",
    "1560",
    "1610",
    "1620",
    "1630",
    "1680",
    "1710",
    "1730",
    "1740",
    "1810",
    "1820",
    "1830",
    "1840",
]

HIGH_PRIORITY_ORGS = {
    "097": "Department of Defense",
    "1700": "Department of Navy",
    "2100": "Department of Army",
    "5700": "Department of Air Force",
    "FP2501": "U.S. Space Force",
    "97AS": "Defense Logistics Agency",
    "97AE": "DARPA",
    "97JC": "Missile Defense Agency",
    "9771": "Defense Microelectronics Activity",
}

MEDIUM_PRIORITY_ORGS = {
    "080": "NASA",
    "070": "Department of Homeland Security",
    "089": "Department of Energy",
    "97DL": "Defense Intelligence Agency",
}

HIGH_VALUE_KEYWORDS = [
    "aircraft engineering",
    "aerospace engineering",
    "systems engineering aircraft",
    "NAVAIR engineering support",
    "technical publications aircraft",
    "repair engineering",
    "support equipment engineering",
    "manufacturing engineering aircraft",
    "test fixture",
    "logistics support analysis",
    "maintenance planning",
    "provisioning",
    "digital engineering defense",
    "MBSE aerospace",
    "missile engineering",
    "space vehicle engineering",
]

BROADER_KEYWORDS = [
    "engineering technical support",
    "in-service engineering",
    "configuration management defense",
    "quality engineering",
    "tooling fixtures",
    "program management engineering",
]

MAIN_COLUMNS = [
    "Status",
    "Fit Category",
    "Fit Score",
    "Opportunity Stage",
    "Opportunity Title",
    "Agency",
    "Office",
    "Notice Type",
    "Notice ID",
    "Solicitation Number",
    "Due Date",
    "Days Until Due",
    "NAICS",
    "PSC",
    "Set-Aside",
    "Place of Performance",
    "Contract Value / Ceiling",
    "Contract Value Source Text",
    "Why It Fits Butler",
    "Feasibility Concern",
    "Recommended Next Step",
    "SeaPort / Vehicle Required",
    "Eligibility Status",
    "Eligibility Requirement",
    "Prime Feasibility",
    "Subcontract / Teaming Path",
    "Eligibility Notes",
    "SAM.gov Link",
    "Attachment Links",
    "Contact Name",
    "Contact Email",
    "Search Source",
    "Refresh Status",
    "Data Confidence",
]

REJECTED_COLUMNS = MAIN_COLUMNS + [
    "Rejection Reason",
    "Raw Notice Type",
    "Matched Negative Keywords",
    "Capacity / Logging Notes",
]


@dataclass(frozen=True)
class RefreshSettings:
    max_api_calls: int = MAX_API_CALLS_PER_REFRESH
    max_pages_per_query: int = MAX_PAGES_PER_QUERY
    request_timeout_seconds: int = REQUEST_TIMEOUT_SECONDS
    retry_attempts: int = RETRY_ATTEMPTS
    backoff_seconds: tuple[int, ...] = tuple(BACKOFF_SECONDS)
    use_cache_on_failure: bool = USE_CACHE_ON_FAILURE
    enable_attachment_text_extraction: bool = ENABLE_ATTACHMENT_TEXT_EXTRACTION
    max_attachments_per_notice: int = MAX_ATTACHMENTS_PER_NOTICE
    max_attachment_bytes: int = MAX_ATTACHMENT_BYTES
    max_attachment_text_chars: int = MAX_ATTACHMENT_TEXT_CHARS
    attachment_timeout_seconds: int = ATTACHMENT_TIMEOUT_SECONDS

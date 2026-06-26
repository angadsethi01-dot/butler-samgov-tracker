from __future__ import annotations

from datetime import date, datetime
from typing import Any

from config import APPROVED_NAICS, MAIN_COLUMNS, SECONDARY_NAICS
from src.stage_classifier import classify_stage, notice_type_label
from src.value_extractor import extract_contract_value
from src.vehicle_classifier import detect_vehicle


POSITIVE_GROUPS = [
    (5, ["aircraft", "aerospace", "aviation", "airframe", "propulsion", "avionics", "defense aircraft", "space vehicle", "missile", "uav", "uas"]),
    (5, ["engineering support", "systems engineering", "product development", "in-service engineering", "testing", "certification", "system safety"]),
    (4, ["manufacturing engineering", "tooling", "cad", "plm", "quality", "process planning", "bom", "fmea", "composites", "cnc"]),
    (4, ["aftermarket", "technical publication", "technical manual", "repair engineering", "provisioning", "logistics support analysis", "maintenance planning", "support equipment"]),
    (3, ["technical staffing", "staff augmentation", "engineering services"]),
    (3, ["department of defense", "dod", "navy", "air force", "army", "space force", "nasa", "navair", "nawc", "navsea", "nswc", "nuwc", "navsup", "navwar", "dla aviation", "aflcmc", "darpa", "missile defense agency"]),
    (2, ["digital engineering", "mbse", "mbe", "digital manufacturing", "digital thread", "embedded systems", "ai/ml", "iot", "cloud", "cybersecurity"]),
]

NEGATIVE_GROUPS = [
    (-7, ["hoteling", "conference", "catering", "food", "travel"]),
    (-7, ["landscaping", "janitorial", "basic facilities", "forest", "grassland"]),
    (-6, ["roads", "bridges", "dams", "civil construction", "utility master plan", "civil a&e", "civil architecture"]),
    (-5, ["web hosting", "data subscription", "commodity software", "microfiche", "digitization"]),
    (-5, ["advertising", "demographic research", "survey research", "medical statistical", "medical research"]),
]

HARD_REJECT = [
    "hoteling",
    "conference space",
    "travel",
    "food",
    "catering",
    "janitorial",
    "landscaping",
    "grassland",
    "forest work",
    "road",
    "bridge",
    "dam",
    "civil infrastructure",
    "utility master planning",
    "civil architecture",
    "environmental remediation",
    "medical research",
    "statistical research",
    "demographic research",
    "advertising",
    "marketing",
    "web hosting",
    "commodity software",
    "data subscription",
    "microfiche",
    "digitization",
    "office supplies",
    "furniture",
    "moving services",
]

# Butler does not supply or manufacture physical hardware. Notices whose deliverable is
# the production/supply of hardware (build-to-print, fabrication, parts supply, COTS, etc.)
# are outside Butler's capabilities UNLESS they also involve designing or redesigning the
# hardware. These two lists let the classifier tell the difference from the notice text.
MANUFACTURE_SUPPLY_TERMS = [
    "build to print",
    "build-to-print",
    "manufacture to print",
    "manufactured to print",
    "manufacture per",
    "manufacture in accordance",
    "manufacture and deliver",
    "manufacture and supply",
    "manufacture and delivery",
    "fabricate and deliver",
    "fabrication and delivery",
    "produce and deliver",
    "production and delivery",
    "manufacture of",
    "manufacturing of",
    "fabrication of",
    "production of",
    "furnish and deliver",
    "furnish and install",
    "supply of",
    "supplies of",
    "procurement of",
    "purchase of",
    "acquisition of",
    "spare parts",
    "replacement parts",
    "repair parts",
    "spares",
    "off-the-shelf",
    "commercial off-the-shelf",
    "commercial-off-the-shelf",
    "cots",
    "national stock number",
    "nsn",
    "hardware procurement",
    "parts procurement",
    "material procurement",
    "quantity of",
]

# Design/engineering/sustainment "work" verbs. If any of these are present, the notice
# involves designing, redesigning, or otherwise engineering/supporting the hardware, which
# is exactly Butler's lane — so it must NOT be treated as a pure supply/manufacturing buy.
ENGINEERING_WORK_TERMS = [
    "design",
    "redesign",
    "re-design",
    "reverse engineering",
    "reverse-engineering",
    "engineering",
    "develop",
    "development",
    "r&d",
    "research and development",
    "modification",
    "retrofit",
    "upgrade",
    "overhaul",
    "repair",
    "maintenance",
    "sustainment",
    "technical publication",
    "technical manual",
    "provisioning",
    "logistics support analysis",
    "maintenance planning",
    "support equipment",
    "test and evaluation",
    "system safety",
    "prototype",
    "prototyping",
    "integration",
    "installation",
    "analysis",
    "study",
    "studies",
    "program management",
    "program support",
    "technical support",
    "certification",
    "qualification",
    "configuration management",
]

NAVY_RELEVANCE = [
    "navair",
    "nawcad",
    "nawcwd",
    "navsea",
    "nswc",
    "nuwc",
    "navsup",
    "navwar",
    "onr",
    "military sealift command",
    "marine corps systems command",
    "fleet readiness",
    "aircraft sustainment",
    "shipboard systems",
    "combat systems",
    "support equipment",
    "technical manuals",
    "provisioning",
    "maintenance planning",
    "test and evaluation",
    "systems engineering",
    "software engineering",
    "in-service engineering",
    "logistics support analysis",
    "configuration management",
    "engineering technical support",
]

SECONDARY_CONNECTIONS = [
    "aerospace",
    "defense",
    "engineering",
    "manufacturing systems",
    "technical support",
    "embedded systems",
    "plm",
    "mbse",
    "digital engineering",
    "navy systems",
    "aircraft",
    "missiles",
    "space vehicles",
    "support equipment",
    "testing",
    "logistics support",
]


def _first(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


def parse_sam_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(text[: len(datetime.now().strftime(fmt))], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def response_deadline(notice: dict) -> date | None:
    return parse_sam_date(
        _first(
            notice.get("responseDeadLine"),
            notice.get("reponseDeadLine"),
            notice.get("responseDeadline"),
        )
    )


def combined_text(notice: dict) -> str:
    fields = [
        "title",
        "description",
        "fullParentPathName",
        "department",
        "subTier",
        "office",
        "naicsCode",
        "classificationCode",
        "typeOfSetAsideDescription",
        "solicitationNumber",
        "_attachment_text",
    ]
    return " ".join(str(notice.get(field) or "") for field in fields).lower()


def _score(text: str) -> tuple[int, list[str], list[str]]:
    score = 0
    positives: list[str] = []
    negatives: list[str] = []
    for points, terms in POSITIVE_GROUPS:
        matched = [term for term in terms if term in text]
        if matched:
            score += points
            positives.extend(matched[:3])
    for points, terms in NEGATIVE_GROUPS:
        matched = [term for term in terms if term in text]
        if matched:
            score += points
            negatives.extend(matched[:3])
    return score, list(dict.fromkeys(positives)), list(dict.fromkeys(negatives))


def _attachments(notice: dict) -> str:
    links: list[str] = []
    for key in ("resourceLinks", "links"):
        value = notice.get(key)
        if isinstance(value, list):
            links.extend(str(item) for item in value)
    return "\n".join(links)


def _contact(notice: dict) -> tuple[str, str]:
    contacts = notice.get("pointOfContact") or notice.get("pointOfContacts") or []
    if isinstance(contacts, list) and contacts:
        first = contacts[0] or {}
        return _first(first.get("fullName"), first.get("name")), _first(first.get("email"))
    return _first(notice.get("contactName")), _first(notice.get("contactEmail"))


def _place(notice: dict) -> str:
    pop = notice.get("placeOfPerformance") or {}
    if isinstance(pop, dict):
        parts = [
            pop.get("city", {}).get("name") if isinstance(pop.get("city"), dict) else pop.get("city"),
            pop.get("state", {}).get("name") if isinstance(pop.get("state"), dict) else pop.get("state"),
            pop.get("country", {}).get("name") if isinstance(pop.get("country"), dict) else pop.get("country"),
        ]
        return ", ".join(str(part) for part in parts if part)
    return str(pop or "")


def _sam_link(notice: dict) -> str:
    direct = _first(notice.get("uiLink"), notice.get("url"))
    if direct:
        return direct
    notice_id = _first(notice.get("noticeId"))
    return f"https://sam.gov/opp/{notice_id}/view" if notice_id else ""


def classify_notice(
    notice: dict,
    search_source: str = "",
    refresh_status: str = "Successful Refresh",
    today: date | None = None,
) -> dict:
    today = today or date.today()
    text = combined_text(notice)
    title = _first(notice.get("title"))
    agency = _first(notice.get("department"), notice.get("fullParentPathName"), notice.get("agency"))
    office = _first(notice.get("office"), notice.get("subTier"), notice.get("organizationName"))
    naics = _first(notice.get("naicsCode"), notice.get("naics"))
    psc = _first(notice.get("classificationCode"), notice.get("psc"))
    ptype = _first(notice.get("type"), notice.get("ptype")).lower()
    status = _first(notice.get("active"), notice.get("status"))
    set_aside = _first(notice.get("typeOfSetAsideDescription"), notice.get("setAside"))
    due = response_deadline(notice)
    days_until_due = (due - today).days if due else ""
    stage = classify_stage(notice)
    notice_type = notice_type_label(ptype, _first(notice.get("noticeType"), notice.get("typeDescription")))
    vehicle = detect_vehicle(text, agency=agency, set_aside=set_aside)
    score, positives, negatives = _score(text)

    if vehicle["has_low_feasibility"]:
        score -= 5
    if set_aside and "small" in set_aside.lower():
        score -= 3
    if isinstance(days_until_due, int) and days_until_due < 5:
        score -= 3
    if not positives:
        score -= 2

    expired = isinstance(days_until_due, int) and days_until_due < 0
    inactive = str(status).lower() in {"inactive", "archived", "cancelled", "canceled", "deleted"}
    excluded_type = ptype in {"a", "g"}
    hard_reject_terms = [term for term in HARD_REJECT if term in text]
    secondary_generic = naics in SECONDARY_NAICS and not any(term in text for term in SECONDARY_CONNECTIONS)
    navy_relevant = any(term in text for term in NAVY_RELEVANCE)
    seaport_relevant = "seaport" in text and navy_relevant
    manufacture_supply_terms = [term for term in MANUFACTURE_SUPPLY_TERMS if term in text]
    has_engineering_work = any(term in text for term in ENGINEERING_WORK_TERMS)
    hardware_supply_no_design = bool(manufacture_supply_terms) and not has_engineering_work

    if expired:
        fit = "D"
        rejection = "Expired response deadline"
    elif inactive:
        fit = "D"
        rejection = "Inactive, archived, cancelled, or deleted"
    elif excluded_type:
        fit = "D"
        rejection = "Excluded notice type"
    elif hard_reject_terms:
        fit = "D"
        rejection = f"Hard reject: {', '.join(hard_reject_terms[:5])}"
    elif secondary_generic:
        fit = "D"
        rejection = "Secondary NAICS without clear aerospace, defense, engineering, or sustainment connection"
    elif seaport_relevant:
        fit = "C"
        rejection = ""
    elif score >= 10 and not vehicle["has_prime_blocker"]:
        fit = "A"
        rejection = ""
    elif score >= 6 and not vehicle["has_vehicle_blocker"]:
        fit = "B"
        rejection = ""
    elif score >= 3 and vehicle["has_prime_blocker"]:
        fit = "C"
        rejection = ""
    elif navy_relevant and vehicle["has_vehicle_blocker"]:
        fit = "C"
        rejection = ""
    else:
        fit = "D"
        rejection = "Below Butler-fit threshold"

    if fit in {"A", "B"} and vehicle["has_vehicle_blocker"]:
        fit = "C"

    # Butler designs/redesigns hardware but does not supply or manufacture it. A strong-fit
    # notice whose scope is purely hardware supply/manufacture (with no design or engineering
    # work) is downgraded to C — kept visible as a subcontract / competitive-intelligence lead
    # rather than presented as a prime engineering fit.
    if fit in {"A", "B"} and hardware_supply_no_design:
        fit = "C"

    if fit == "A":
        why = "Direct match to Butler aerospace/defense engineering or sustainment capabilities."
    elif fit == "B":
        why = "Possible Butler fit through broader defense engineering, logistics, testing, or program support."
    elif fit == "C":
        why = "Relevant Butler intelligence or subcontract lead, but prime feasibility is limited."
    else:
        why = "Not a Butler-fit opportunity under the current conservative filter."

    if positives:
        why = f"{why} Matched: {', '.join(positives[:8])}."
    if notice.get("_attachment_text"):
        why = f"{why} Attachment text was included in the screen."

    if fit == "C" and hardware_supply_no_design:
        why = (
            f"{why} Scope reads as hardware supply/manufacturing with no clear design, "
            f"redesign, or engineering work (matched: {', '.join(manufacture_supply_terms[:5])}), "
            "so it is tracked as a subcontract/competitive-intelligence lead rather than a prime fit."
        )
        if not vehicle["Feasibility Concern"]:
            vehicle["Feasibility Concern"] = (
                "Hardware supply/manufacturing scope with no design or engineering work"
            )

    if fit == "C" and vehicle["Recommended Next Step"] == "Add to tracker":
        vehicle["Recommended Next Step"] = "Possible subcontract lead"
    if fit == "D":
        vehicle["Recommended Next Step"] = "Ignore"

    value, value_source = extract_contract_value(text)
    contact_name, contact_email = _contact(notice)
    row = {
        "Status": "Accepted" if fit in {"A", "B", "C"} else "Rejected",
        "Fit Category": fit,
        "Fit Score": score,
        "Opportunity Stage": stage,
        "Opportunity Title": title,
        "Agency": agency,
        "Office": office,
        "Notice Type": notice_type,
        "Notice ID": _first(notice.get("noticeId")),
        "Solicitation Number": _first(notice.get("solicitationNumber")),
        "Due Date": due.isoformat() if due else "",
        "Days Until Due": days_until_due,
        "NAICS": naics,
        "PSC": psc,
        "Set-Aside": set_aside,
        "Place of Performance": _place(notice),
        "Contract Value / Ceiling": value,
        "Contract Value Source Text": value_source,
        "Why It Fits Butler": why,
        "Feasibility Concern": vehicle["Feasibility Concern"],
        "Recommended Next Step": vehicle["Recommended Next Step"],
        "SeaPort / Vehicle Required": vehicle["SeaPort / Vehicle Required"],
        "Eligibility Status": vehicle["Eligibility Status"],
        "Eligibility Requirement": vehicle["Eligibility Requirement"],
        "Prime Feasibility": vehicle["Prime Feasibility"],
        "Subcontract / Teaming Path": vehicle["Subcontract / Teaming Path"],
        "Eligibility Notes": vehicle["Eligibility Notes"],
        "SAM.gov Link": _sam_link(notice),
        "Attachment Links": _attachments(notice),
        "Contact Name": contact_name,
        "Contact Email": contact_email,
        "Search Source": search_source,
        "Refresh Status": refresh_status,
        "Data Confidence": "High — attachment text read" if notice.get("_attachment_text") else ("High" if naics in APPROVED_NAICS or positives else "Medium"),
        "Rejection Reason": rejection,
        "Raw Notice Type": ptype,
        "Matched Negative Keywords": ", ".join(negatives),
        "Capacity / Logging Notes": _first(notice.get("_attachment_parse_notes")),
    }
    for column in MAIN_COLUMNS:
        row.setdefault(column, "")
    return row

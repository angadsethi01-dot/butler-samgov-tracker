from __future__ import annotations

from config import PTYPE_MAP


TYPE_TEXT_MAP = {
    "sources_sought": "Sources Sought",
    "sources sought": "Sources Sought",
    "source sought": "Sources Sought",
    "solicitation": "Solicitation",
    "combined synopsis/solicitation": "Combined Synopsis/Solicitation",
    "combined synopsis solicitation": "Combined Synopsis/Solicitation",
    "presolicitation": "Pre-Solicitation",
    "pre-solicitation": "Pre-Solicitation",
    "special_notice": "Special Notice",
    "special notice": "Special Notice",
    "justification": "Justification / J&A",
    "justification and approval": "Justification / J&A",
}


def notice_type_label(ptype: str | None, type_text: str | None = None) -> str:
    code = (ptype or "").strip().lower()
    if code in PTYPE_MAP:
        return PTYPE_MAP[code]
    normalized = code.replace("-", " ").replace("_", " ")
    for token, label in TYPE_TEXT_MAP.items():
        if token.replace("_", " ") in normalized:
            return label
    fallback = (type_text or "").strip()
    normalized_fallback = fallback.lower().replace("-", " ").replace("_", " ")
    for token, label in TYPE_TEXT_MAP.items():
        if token.replace("_", " ") in normalized_fallback:
            return label
    return fallback or "Unknown"


def classify_stage(notice: dict) -> str:
    ptype = (notice.get("type") or notice.get("ptype") or "").strip().lower()
    title = (notice.get("title") or "").lower()
    description = (notice.get("description") or "").lower()
    attachment_text = (notice.get("_attachment_text") or "").lower()
    type_text = (
        notice.get("typeOfSetAsideDescription")
        or notice.get("noticeType")
        or notice.get("typeDescription")
        or ""
    ).lower()
    normalized_ptype = ptype.replace("-", " ").replace("_", " ")
    text = f"{title} {type_text} {normalized_ptype} {description} {attachment_text[:5000]}"

    if ptype == "r" or any(
        token in text
        for token in [
            "sources sought",
            "source sought",
            "request for information",
            "rfi",
            "market research",
            "capability statement",
            "interested vendor",
        ]
    ):
        return "Sources Sought / RFI"
    if ptype in {"o", "k"} or any(
        token in text
        for token in [
            "solicitation",
            "combined synopsis",
            "request for proposal",
            "rfp",
            "request for quote",
            "rfq",
        ]
    ):
        return "RFP / Solicitation"
    if ptype == "p":
        return "Pre-Solicitation"
    if any(token in text for token in ["presolicitation", "pre solicitation", "pre-solicitation"]):
        return "Pre-Solicitation"
    if ptype == "u" or any(token in text for token in ["justification", "j&a", "sole source"]):
        return "Low-Feasibility / J&A"
    if ptype == "s" or "special notice" in text:
        return "Special Notice"
    return "Other"


def is_rfp(stage: str) -> bool:
    return stage in {"RFP / Solicitation"}


def is_sources_sought(stage: str) -> bool:
    return stage == "Sources Sought / RFI"

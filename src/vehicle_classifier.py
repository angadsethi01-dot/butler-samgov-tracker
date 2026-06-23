from __future__ import annotations

import re


SEAPORT_PATTERNS = [
    r"seaport[-\s]?nxg",
    r"seaport\s+next\s+generation",
    r"seaport\s+portal",
    r"seaport\s+mac",
    r"seaport\s+idiq",
    r"seaport\s+contract\s+holders",
    r"current\s+seaport\s+holders",
    r"existing\s+seaport\s+holders",
]

IDIQ_PATTERNS = [
    r"existing\s+idiq\s+holders",
    r"idiq\s+holders\s+only",
    r"current\s+mac\s+holders",
    r"offerors\s+must\s+hold",
    r"contract\s+holders\s+only",
    r"task\s+order\s+under",
]

SOLE_SOURCE_PATTERNS = [
    r"sole\s+source",
    r"intent\s+to\s+sole\s+source",
    r"justification\s+and\s+approval",
    r"\bj&a\b",
    r"brand[-\s]?name\s+only",
    r"oem[-\s]?only",
    r"original\s+equipment\s+manufacturer",
]

SET_ASIDE_PATTERNS = [
    r"\b8\(a\)\b",
    r"sdvosb",
    r"wosb",
    r"hubzone",
    r"edwosb",
    r"small\s+business\s+set[-\s]?aside",
    r"veteran[-\s]?owned",
    r"indian\s+economic\s+enterprise",
]


def _matches(patterns: list[str], text: str) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            found.append(match.group(0))
    return found


def detect_vehicle(text: str, agency: str = "", set_aside: str = "") -> dict:
    haystack = " ".join([text or "", agency or "", set_aside or ""])
    seaport = _matches(SEAPORT_PATTERNS, haystack)
    idiq = _matches(IDIQ_PATTERNS, haystack)
    sole = _matches(SOLE_SOURCE_PATTERNS, haystack)
    set_aside_matches = _matches(SET_ASIDE_PATTERNS, haystack)

    if seaport:
        vehicle_required = "Yes — SeaPort-NxG"
        eligibility_status = "Teaming/Subcontract Needed"
        eligibility_requirement = "Requires current SeaPort-NxG MAC/IDIQ contract holder status."
        prime_feasibility = "Subcontract only"
        next_step = "Find SeaPort prime / teaming partner"
        teaming_path = "Identify current SeaPort-NxG prime holders and assess teaming path."
    elif idiq:
        vehicle_required = "Other IDIQ / contract vehicle"
        eligibility_status = "Teaming/Subcontract Needed"
        eligibility_requirement = "Requires existing IDIQ/task-order contract holder status."
        prime_feasibility = "Subcontract only"
        next_step = "Possible subcontract lead"
        teaming_path = "Track incumbent and likely bidders for subcontracting outreach."
    else:
        vehicle_required = "No obvious vehicle restriction"
        eligibility_status = "Not Applicable"
        eligibility_requirement = "No special eligibility found in SAM.gov fields."
        prime_feasibility = "Prime feasible"
        next_step = "Add to tracker"
        teaming_path = "Monitor as a direct pursuit unless attachments indicate otherwise."

    if set_aside_matches and not seaport and not idiq:
        eligibility_status = "Unknown — check Butler contract vehicles"
        eligibility_requirement = "Requires small-business set-aside eligibility."
        prime_feasibility = "Prime uncertain"
        next_step = "Check set-aside"
        teaming_path = "Check whether Butler can qualify directly or should team with an eligible prime."

    if sole:
        if prime_feasibility == "Prime feasible":
            prime_feasibility = "Prime unlikely"
        next_step = "Check OEM restriction" if any("oem" in s.lower() for s in sole) else "Check incumbent"

    concern_parts = []
    if seaport:
        concern_parts.append("SeaPort-NxG restriction detected")
    if idiq:
        concern_parts.append("Existing contract vehicle restriction detected")
    if sole:
        concern_parts.append("Sole-source/OEM/brand-name restriction detected")
    if set_aside_matches:
        concern_parts.append("Set-aside eligibility may limit prime feasibility")

    detected = seaport + idiq + sole + set_aside_matches
    return {
        "SeaPort / Vehicle Required": vehicle_required,
        "Eligibility Status": eligibility_status,
        "Eligibility Requirement": eligibility_requirement,
        "Prime Feasibility": prime_feasibility,
        "Subcontract / Teaming Path": teaming_path,
        "Eligibility Notes": "; ".join(dict.fromkeys(detected)) or "None detected",
        "Recommended Next Step": next_step,
        "Feasibility Concern": "; ".join(concern_parts) or "None identified",
        "has_prime_blocker": bool(seaport or idiq or sole or set_aside_matches),
        "has_vehicle_blocker": bool(seaport or idiq),
        "has_low_feasibility": bool(seaport or idiq or sole),
        "matched_restrictions": detected,
    }


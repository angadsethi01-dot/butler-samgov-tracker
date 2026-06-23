from __future__ import annotations

import re


VALUE_CONTEXT = re.compile(
    r"((?:ceiling|award|amount|not[-\s]?to[-\s]?exceed|nte|total\s+value|budget|estimated\s+value)"
    r"[^.\n]{0,120}?\$[0-9][0-9,]*(?:\.[0-9]{2})?)",
    flags=re.IGNORECASE,
)

MONEY = re.compile(r"\$[0-9][0-9,]*(?:\.[0-9]{2})?")


def extract_contract_value(text: str) -> tuple[str, str]:
    if not text:
        return "Not stated", ""
    match = VALUE_CONTEXT.search(text)
    if not match:
        return "Not stated", ""
    source = match.group(1).strip()
    money = MONEY.search(source)
    return (money.group(0) if money else "Not stated", source)


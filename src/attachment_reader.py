from __future__ import annotations

import html
import io
import re
import zipfile
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from config import RefreshSettings


def extract_attachment_links(notice: dict) -> list[str]:
    links: list[str] = []
    for key in ("resourceLinks", "links", "attachments"):
        value = notice.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str):
                links.append(item)
            elif isinstance(item, dict):
                href = item.get("href") or item.get("url") or item.get("downloadUrl")
                if href:
                    links.append(str(href))
    return [link for link in dict.fromkeys(links) if _looks_like_attachment(link)]


def enrich_notices_with_attachment_text(
    notices: list[dict],
    api_key: str,
    settings: RefreshSettings,
    session: requests.Session | None = None,
) -> None:
    if not settings.enable_attachment_text_extraction:
        return
    session = session or requests.Session()
    for notice in notices:
        links = extract_attachment_links(notice)
        if not links:
            notice["_attachment_parse_notes"] = "No downloadable attachment links found."
            continue
        chunks: list[str] = []
        notes: list[str] = []
        for link in links[: settings.max_attachments_per_notice]:
            text, note = read_attachment_text(link, api_key, settings, session)
            if text:
                chunks.append(text)
            notes.append(note)
        joined = "\n\n".join(chunks).strip()
        notice["_attachment_text"] = joined[: settings.max_attachment_text_chars]
        notice["_attachment_parse_notes"] = "; ".join(notes)


def read_attachment_text(
    url: str,
    api_key: str,
    settings: RefreshSettings,
    session: requests.Session,
) -> tuple[str, str]:
    safe_url = _with_api_key(url, api_key)
    try:
        response = session.get(safe_url, timeout=settings.attachment_timeout_seconds, stream=True)
        if response.status_code in {401, 403}:
            return "", "Attachment auth failed"
        if response.status_code == 429:
            return "", "Attachment rate-limited"
        response.raise_for_status()
        content_type = (response.headers.get("content-type") or "").lower()
        content = response.content[: settings.max_attachment_bytes + 1]
        if len(content) > settings.max_attachment_bytes:
            return "", "Attachment skipped: too large"
        text = _decode_content(content, content_type, url)
        if not text:
            return "", "Attachment skipped: unsupported or empty"
        return text[: settings.max_attachment_text_chars], "Attachment text read"
    except Exception as exc:
        return "", f"Attachment read failed: {type(exc).__name__}"


def _looks_like_attachment(link: str) -> bool:
    lower = link.lower()
    if "opportunities/v2/search" in lower:
        return False
    return any(
        token in lower
        for token in [
            "/resources/files/",
            "/download",
            ".pdf",
            ".txt",
            ".html",
            ".htm",
            ".docx",
            ".csv",
            ".xml",
            ".json",
        ]
    )


def _with_api_key(url: str, api_key: str) -> str:
    if not api_key:
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query.setdefault("api_key", api_key)
    return urlunparse(parsed._replace(query=urlencode(query)))


def _decode_content(content: bytes, content_type: str, url: str) -> str:
    lower = url.lower()
    if "pdf" in content_type or lower.endswith(".pdf"):
        return _read_pdf(content)
    if "wordprocessingml" in content_type or lower.endswith(".docx"):
        return _read_docx(content)
    if "html" in content_type or lower.endswith((".html", ".htm")):
        return _strip_html(content.decode("utf-8", errors="ignore"))
    if any(token in content_type for token in ["text", "json", "xml", "csv"]) or lower.endswith((".txt", ".csv", ".xml", ".json")):
        return content.decode("utf-8", errors="ignore")
    sample = content[:500].decode("utf-8", errors="ignore")
    if len(sample.strip()) > 100:
        return content.decode("utf-8", errors="ignore")
    return ""


def _read_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages[:20])


def _read_docx(content: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception:
        return ""
    text = re.sub(r"<[^>]+>", " ", xml)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _strip_html(text: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()

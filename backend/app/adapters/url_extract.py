from __future__ import annotations

from dataclasses import dataclass

import httpx
import trafilatura

MIN_TEXT_CHARS = 200


@dataclass
class ExtractResult:
    ok: bool
    title: str = ""
    text: str = ""
    error_code: str | None = None


def fetch_html(url: str) -> tuple[int, str]:
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=15.0,
        headers={"User-Agent": "KaoWoYiXia/0.1"},
    )
    return response.status_code, response.text


def extract_public_url(url: str) -> ExtractResult:
    try:
        status, html = fetch_html(url)
    except httpx.HTTPError:
        return ExtractResult(ok=False, error_code="URL_FETCH_FAILED")

    if status in {401, 403}:
        return ExtractResult(ok=False, error_code="URL_LOGIN_WALL")
    if status >= 400:
        return ExtractResult(ok=False, error_code="URL_FETCH_FAILED")

    text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    metadata = trafilatura.extract_metadata(html)
    title = (metadata.title if metadata and metadata.title else "") or _first_heading(html)
    compact = " ".join(text.split())

    lower_html = html.lower()
    looks_like_login = "type=\"password\"" in lower_html or "type='password'" in lower_html
    if looks_like_login and len(compact) < MIN_TEXT_CHARS:
        return ExtractResult(ok=False, error_code="URL_LOGIN_WALL")
    if len(compact) < MIN_TEXT_CHARS:
        return ExtractResult(ok=False, error_code="URL_TOO_SHORT")
    return ExtractResult(ok=True, title=title or "未命名网页", text=compact)


def _first_heading(html: str) -> str:
    start = html.lower().find("<h1")
    if start < 0:
        return ""
    start = html.find(">", start)
    end = html.lower().find("</h1>", start)
    if start < 0 or end < 0:
        return ""
    return html[start + 1 : end].strip()

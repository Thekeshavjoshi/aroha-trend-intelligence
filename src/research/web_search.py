import os
import re
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from tavily import TavilyClient

from src.research.source_image import extract_source_image


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError(
        "TAVILY_API_KEY is missing from .env"
    )


# =========================================================
# TAVILY CLIENT
# =========================================================

client = TavilyClient(
    api_key=api_key
)


# =========================================================
# EVIDENCE CLEANING
# =========================================================

DEFAULT_MAX_CONTENT_CHARS = 3000


def _normalize_text(text: str) -> str:
    """Collapse repeated whitespace without changing the meaning."""
    return re.sub(r"\s+", " ", text).strip()


def _normalize_url(url: str) -> str:
    """Normalize a URL enough to detect obvious duplicate results."""
    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())
        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                parts.path.rstrip("/"),
                parts.query,
                "",
            )
        )
    except ValueError:
        return url.strip().lower().rstrip("/")


def _compact_content(content: str, max_chars: int) -> str:
    """Keep evidence bounded so large pages cannot consume the pipeline context."""
    content = _normalize_text(content)

    if len(content) <= max_chars:
        return content

    # Keep a complete character boundary and clearly mark truncation.
    return content[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."


# =========================================================
# WEB RESEARCH
# =========================================================

def search_web(
    query: str,
    max_results: int = 5,
    max_content_chars: int = DEFAULT_MAX_CONTENT_CHARS,
):
    """
    Search the web using Tavily and return compact research evidence.

    The research layer deliberately keeps only information required by
    downstream AROHA stages: title, URL, and bounded content.

    Cleaning performed here:
    - removes invalid/empty results
    - normalizes whitespace
    - removes duplicate URLs
    - removes duplicate content
    - bounds content length to reduce downstream token usage
    - preserves the original source URL for traceability
    """

    if not query or not query.strip():
        return []

    if max_results < 1:
        return []

    if max_content_chars < 200:
        raise ValueError("max_content_chars must be at least 200")

    response = client.search(
        query=query.strip(),
        search_depth="basic",
        max_results=max_results,
    )

    raw_results = response.get(
        "results",
        [],
    )

    cleaned_results = []
    seen_urls = set()
    seen_content = set()

    for result in raw_results:
        if not isinstance(result, dict):
            continue

        title = _normalize_text(
            str(result.get("title", ""))
        )

        url = str(
            result.get("url", "")
        ).strip()

        content = _compact_content(
            str(result.get("content", "")),
            max_content_chars,
        )

        if not title and not content:
            continue

        normalized_url = _normalize_url(url)
        normalized_content = content.lower()

        # Prefer URL-based deduplication. Content deduplication catches
        # duplicate/syndicated snippets when the URLs differ.
        if normalized_url and normalized_url in seen_urls:
            continue

        if normalized_content and normalized_content in seen_content:
            continue

        if normalized_url:
            seen_urls.add(normalized_url)

        if normalized_content:
            seen_content.add(normalized_content)

        source_image_url = ""

        if url:
            # Best-effort only: a source image must never break research.
            source_image_url = extract_source_image(url)

        cleaned_results.append({
            "title": title,
            "url": url,
            "content": content,
            "source_image_url": source_image_url,
        })

    return cleaned_results

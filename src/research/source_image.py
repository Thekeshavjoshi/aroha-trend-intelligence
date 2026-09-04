"""Extract a representative reference image from a source webpage."""

import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import requests


REQUEST_TIMEOUT = 8
MAX_HTML_CHARS = 1_500_000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0 Safari/537.36 AROHA/1.0"
)


class _ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta_images = []
        self.link_images = []
        self.img_sources = []
        self.jsonld_blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = {str(k).lower(): str(v).strip() for k, v in attrs if v is not None}

        if tag.lower() == "meta":
            prop = attrs.get("property", "").lower()
            name = attrs.get("name", "").lower()
            content = attrs.get("content", "").strip()

            if content and (
                prop in {"og:image", "og:image:url", "og:image:secure_url"}
                or name in {"twitter:image", "twitter:image:src"}
            ):
                self.meta_images.append(content)

        elif tag.lower() == "link":
            rel = attrs.get("rel", "").lower()
            href = attrs.get("href", "").strip()
            if href and "image_src" in rel:
                self.link_images.append(href)

        elif tag.lower() == "img":
            for key in ("src", "data-src", "data-lazy-src", "data-original"):
                value = attrs.get(key, "").strip()
                if value:
                    self.img_sources.append(value)
                    break

    def handle_data(self, data):
        # JSON-LD is handled separately from the parser to keep this class simple.
        return None


def _valid_http_url(value: str) -> bool:
    try:
        parts = urlsplit(value)
        return parts.scheme in {"http", "https"} and bool(parts.netloc)
    except ValueError:
        return False


def _extract_jsonld_images(html: str) -> list[str]:
    images = []

    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        raw = match.group(1).strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        def walk(value):
            if isinstance(value, dict):
                image = value.get("image")
                if isinstance(image, str):
                    images.append(image)
                elif isinstance(image, dict):
                    for key in ("url", "contentUrl"):
                        if isinstance(image.get(key), str):
                            images.append(image[key])
                elif isinstance(image, list):
                    for item in image:
                        if isinstance(item, str):
                            images.append(item)
                        elif isinstance(item, dict):
                            for key in ("url", "contentUrl"):
                                if isinstance(item.get(key), str):
                                    images.append(item[key])

                for child in value.values():
                    if isinstance(child, (dict, list)):
                        walk(child)

            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(data)

    return images


def extract_source_image(url: str) -> str:
    """Return the best representative image URL found on a source webpage.

    Priority:
      1. Open Graph image
      2. Twitter card image
      3. JSON-LD image
      4. image_src link
      5. first usable image element

    Failures intentionally return an empty string so image extraction never
    interrupts AROHA's research/intelligence pipeline.
    """

    if not _valid_http_url(url):
        return ""

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return ""

        page_url = response.url or url
        page_html = response.text[:MAX_HTML_CHARS]

        parser = _ImageParser()
        parser.feed(page_html)

        candidates = []
        candidates.extend(parser.meta_images)
        candidates.extend(_extract_jsonld_images(page_html))
        candidates.extend(parser.link_images)
        candidates.extend(parser.img_sources)

        seen = set()
        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate or candidate.startswith("data:"):
                continue

            absolute = urljoin(page_url, candidate)
            if not _valid_http_url(absolute):
                continue

            normalized = absolute.split("#", 1)[0]
            if normalized in seen:
                continue
            seen.add(normalized)

            return normalized

    except Exception:
        return ""

    return ""

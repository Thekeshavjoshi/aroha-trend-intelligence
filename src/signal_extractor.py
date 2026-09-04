import json
import re

from src.llm.client import generate_response


# =========================================================
# CONFIGURATION
# =========================================================

MAX_CONTENT_CHARS = 7000


# =========================================================
# HELPERS
# =========================================================

def _clean_text(value) -> str:
    """Convert a value to clean text."""
    if value is None:
        return ""

    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _extract_json(response: str):
    """
    Safely extract a JSON object from an LLM response.

    Handles responses where the model accidentally wraps JSON
    inside markdown code fences or adds small amounts of text.
    """

    if not response:
        return None

    response = response.strip()

    # -----------------------------------------------------
    # 1. Direct JSON
    # -----------------------------------------------------
    try:
        parsed = json.loads(response)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    # -----------------------------------------------------
    # 2. Remove markdown code fences
    # -----------------------------------------------------
    cleaned = re.sub(
        r"```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE
    )

    cleaned = cleaned.replace("```", "").strip()

    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    # -----------------------------------------------------
    # 3. Find first JSON object
    # -----------------------------------------------------
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = cleaned[start:end + 1]

        try:
            parsed = json.loads(candidate)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

    return None


def _normalize_list(value) -> list:
    """Ensure a field is always returned as a list."""

    if value is None:
        return []

    if isinstance(value, list):
        return [
            _clean_text(item)
            for item in value
            if _clean_text(item)
        ]

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return []

        return [value]

    return []


def _normalize_score(value) -> int:
    """Normalize LLM-generated scores to integers between 0 and 10."""

    try:
        score = int(float(value))
    except (TypeError, ValueError):
        return 0

    return max(0, min(10, score))


def _normalize_signal(signal: dict, title: str, url: str, source_image_url: str = "") -> dict:
    """
    Normalize the model output into AROHA's canonical signal schema.
    """

    return {
        # -------------------------------------------------
        # Core intelligence
        # -------------------------------------------------
        "observation": _clean_text(
            signal.get("observation")
        ),

        "signal": _clean_text(
            signal.get("signal")
        ),

        "signal_type": _clean_text(
            signal.get("signal_type")
        ),

        # -------------------------------------------------
        # Behavioral / consumer intelligence
        # -------------------------------------------------
        "behavior_change": _clean_text(
            signal.get("behavior_change")
        ),

        "consumer_need": _clean_text(
            signal.get("consumer_need")
        ),

        "emerging_preference": _clean_text(
            signal.get("emerging_preference")
        ),

        # -------------------------------------------------
        # Supporting evidence
        # -------------------------------------------------
        "evidence": _clean_text(
            signal.get("evidence")
        ),

        "evidence_strength": _normalize_score(
            signal.get("evidence_strength")
        ),

        # -------------------------------------------------
        # Trend potential
        # -------------------------------------------------
        "novelty": _normalize_score(
            signal.get("novelty")
        ),

        "momentum": _normalize_score(
            signal.get("momentum")
        ),

        # -------------------------------------------------
        # Supporting concepts
        # -------------------------------------------------
        "recurring_concepts": _normalize_list(
            signal.get("recurring_concepts")
        ),

        "popularity_indicators": _normalize_list(
            signal.get("popularity_indicators")
        ),

        # -------------------------------------------------
        # Source
        # -------------------------------------------------
        "source_title": title,
        "source_url": url,
        "source_image_url": _clean_text(source_image_url),
    }


def _is_valid_signal(signal: dict) -> bool:
    """
    Validate whether the extracted object contains enough
    intelligence to enter the downstream trend pipeline.
    """

    required_fields = [
        signal.get("observation"),
        signal.get("signal"),
        signal.get("evidence"),
    ]

    # At minimum, the model must provide these three.
    return all(
        isinstance(value, str) and value.strip()
        for value in required_fields
    )


# =========================================================
# MAIN SIGNAL EXTRACTION
# =========================================================

def extract_signals(search_result: dict) -> dict:
    """
    Extract a structured intelligence signal from one web result.

    The goal is NOT to summarize the article.

    The goal is to identify a meaningful change, behavior,
    preference, need, or emerging pattern that can later
    contribute to trend detection.
    """

    title = _clean_text(
        search_result.get("title", "")
    )

    content = _clean_text(
        search_result.get("content", "")
    )

    url = _clean_text(
        search_result.get("url", "")
    )

    source_image_url = _clean_text(
        search_result.get("source_image_url", "")
    )

    # -----------------------------------------------------
    # Protect token usage
    # -----------------------------------------------------

    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS]

    # -----------------------------------------------------
    # LLM prompt
    # -----------------------------------------------------

    prompt = f"""
You are AROHA's signal intelligence analyst.

Your job is to extract ONE high-quality emerging signal
from the provided web research result.

IMPORTANT:

Do NOT simply summarize the article.

Do NOT describe the article's writing style.

Do NOT invent statistics, popularity, market growth,
consumer behavior, or facts that are not supported.

Instead, identify a meaningful change or emerging pattern
that could contribute to a larger trend.

Think in this direction:

OBSERVATION
What does the source actually show?

        ↓

SIGNAL
What meaningful change or emerging pattern can be inferred
directly from that observation?

        ↓

BEHAVIOR / PREFERENCE
What are people, consumers, brands, or markets doing or
preferring differently?

        ↓

TREND POTENTIAL
Could this signal become part of a broader trend?

SOURCE TITLE:
{title}

SOURCE URL:
{url}

SOURCE CONTENT:
{content}


Return ONLY valid JSON.

Use exactly this structure:

{{
    "observation": "",
    "signal": "",
    "signal_type": "",
    "behavior_change": "",
    "consumer_need": "",
    "emerging_preference": "",
    "evidence": "",
    "evidence_strength": 0,
    "novelty": 0,
    "momentum": 0,
    "recurring_concepts": [],
    "popularity_indicators": []
}}


FIELD DEFINITIONS:

observation:
A concise factual observation directly supported by
the source.

signal:
The meaningful emerging signal represented by the
observation.

signal_type:
Choose ONE:
- behavior
- consumer_preference
- product
- design
- technology
- culture
- market
- lifestyle
- sustainability
- other

behavior_change:
Describe what appears to be changing in behavior,
usage, purchasing, design practice, or preference.

If the source does not support a behavior change,
return null.

consumer_need:
Identify the underlying consumer/user need only when
supported by the source.

Do not invent a psychological motivation.

emerging_preference:
Describe a new or increasingly visible preference
supported by the source.

evidence:
Give ONE concise piece of evidence from the source
supporting the signal.

Do not quote long passages.

evidence_strength:
Rate the strength of the available evidence:

0 = extremely weak
2 = weak
4 = moderate
6 = good
8 = strong
10 = very strong

Only use a high score when the source provides clear
support.

novelty:
How new or emerging does this signal appear based on
the source?

0 = established/common
10 = highly emerging/new

Do not assume novelty simply because something sounds
interesting.

momentum:
How strongly does the source indicate current adoption,
attention, repetition, or movement?

0 = no momentum evidence
10 = very strong momentum evidence

Do not create momentum if the source does not support it.

recurring_concepts:
Return 2-5 concise concepts explicitly present in the
source that could later be compared with signals from
other sources.

popularity_indicators:
Return only explicit indicators such as:
- rising searches
- increased adoption
- repeated mentions
- growing demand
- expanding market presence
- increasing engagement

If none are supported, return [].


CRITICAL RULES:

1. Use ONLY the provided source.
2. Never fabricate facts.
3. Never turn a generic article topic into a trend.
4. Separate observation from interpretation.
5. Keep every field concise.
6. Return ONE signal only.
7. Return null when evidence is unavailable.
8. Return valid JSON only.
"""

    # -----------------------------------------------------
    # LLM call
    # -----------------------------------------------------

    response = generate_response(prompt)

    # -----------------------------------------------------
    # Parse response
    # -----------------------------------------------------

    signal = _extract_json(response)

    if signal is None:

        return {
            "valid": False,
            "error": "LLM returned invalid JSON",
            "source_title": title,
            "source_url": url,
        }

    # -----------------------------------------------------
    # Normalize
    # -----------------------------------------------------

    normalized_signal = _normalize_signal(
        signal,
        title,
        url,
        source_image_url
    )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    if not _is_valid_signal(normalized_signal):

        return {
            "valid": False,
            "error": "Extracted signal failed validation",
            "source_title": title,
            "source_url": url,
        }

    # -----------------------------------------------------
    # Mark successful extraction
    # -----------------------------------------------------

    normalized_signal["valid"] = True

    return normalized_signal
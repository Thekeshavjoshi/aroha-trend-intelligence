import json
import re
from collections import defaultdict

from src.llm.client import generate_response


# =========================================================
# CONFIGURATION
# =========================================================

MAX_SIGNALS = 20
MAX_TRENDS = 5

MIN_CONFIDENCE = 4

MIN_MULTI_SIGNAL_COUNT = 2

MIN_HIGH_EVIDENCE_SCORE = 7
MIN_MEDIUM_EVIDENCE_SCORE = 5

# Maximum number of signals sent to the clustering LLM.
# Keeping this controlled helps with Groq TPM limits.
MAX_CLUSTER_SIGNALS = 20

# Maximum number of clusters sent into trend generation.
MAX_CLUSTERS = 8


# =========================================================
# TEXT / JSON HELPERS
# =========================================================

def _clean_text(value) -> str:
    """Normalize text."""

    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def _normalize_score(value) -> int:
    """Convert a model score to an integer from 0-10."""

    try:
        score = int(float(value))
    except (TypeError, ValueError):
        return 0

    return max(0, min(10, score))


def _normalize_list(value) -> list:
    """Ensure a value is returned as a clean list."""

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

        if value:
            return [value]

    return []


# =========================================================
# JSON EXTRACTION
# =========================================================

def _extract_json(response: str):

    if not response:
        return None

    response = response.strip()

    # -----------------------------------------------------
    # Direct JSON
    # -----------------------------------------------------

    try:

        parsed = json.loads(response)

        if isinstance(parsed, dict):
            return parsed

        if isinstance(parsed, list):
            return {"trends": parsed}

    except json.JSONDecodeError:
        pass

    # -----------------------------------------------------
    # Remove markdown fences
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

        if isinstance(parsed, list):
            return {"trends": parsed}

    except json.JSONDecodeError:
        pass

    # -----------------------------------------------------
    # Extract JSON object
    # -----------------------------------------------------

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end > start:

        candidate = cleaned[start:end + 1]

        try:

            parsed = json.loads(candidate)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

    # -----------------------------------------------------
    # Extract JSON array
    # -----------------------------------------------------

    start = cleaned.find("[")
    end = cleaned.rfind("]")

    if start != -1 and end > start:

        candidate = cleaned[start:end + 1]

        try:

            parsed = json.loads(candidate)

            if isinstance(parsed, list):
                return {"trends": parsed}

        except json.JSONDecodeError:
            pass

    return None


# =========================================================
# SIGNAL PREPARATION
# =========================================================

def _prepare_signals(signals: list[dict]) -> list[dict]:
    """
    Prepare compact structured signals for trend reasoning.
    """

    prepared = []

    for index, signal in enumerate(
        signals[:MAX_SIGNALS]
    ):

        if not isinstance(signal, dict):
            continue

        if signal.get("valid") is False:
            continue

        signal_text = _clean_text(
            signal.get("signal")
        )

        observation = _clean_text(
            signal.get("observation")
        )

        evidence = _clean_text(
            signal.get("evidence")
        )

        if not signal_text or not evidence:
            continue

        prepared.append(
            {
                "signal_id": index + 1,

                "signal": signal_text,

                "observation": observation,

                "signal_type": _clean_text(
                    signal.get("signal_type")
                ),

                "behavior_change": _clean_text(
                    signal.get("behavior_change")
                ),

                "consumer_need": _clean_text(
                    signal.get("consumer_need")
                ),

                "emerging_preference": _clean_text(
                    signal.get("emerging_preference")
                ),

                "evidence": evidence,

                "evidence_strength": _normalize_score(
                    signal.get("evidence_strength")
                ),

                "novelty": _normalize_score(
                    signal.get("novelty")
                ),

                "momentum": _normalize_score(
                    signal.get("momentum")
                ),

                "recurring_concepts": _normalize_list(
                    signal.get("recurring_concepts")
                ),

                "popularity_indicators": _normalize_list(
                    signal.get("popularity_indicators")
                ),

                "source_title": _clean_text(
                    signal.get("source_title")
                ),

                "source_url": _clean_text(
                    signal.get("source_url")
                ),
            }
        )

    return prepared


# =========================================================
# SIGNAL ID RESOLUTION
# =========================================================

def _resolve_signal_ids(
    raw_ids,
    signals: list[dict]
) -> list[int]:

    if not isinstance(raw_ids, list):
        return []

    valid_ids = []

    for value in raw_ids:

        try:
            signal_id = int(value)
        except (TypeError, ValueError):
            continue

        if 1 <= signal_id <= len(signals):

            if signal_id not in valid_ids:
                valid_ids.append(signal_id)

    return valid_ids


# =========================================================
# EVIDENCE BUILDING
# =========================================================

def _build_evidence(
    signal_ids: list[int],
    signals: list[dict]
) -> list[str]:

    evidence = []

    for signal_id in signal_ids:

        signal = signals[signal_id - 1]

        text = _clean_text(
            signal.get("evidence")
        )

        if not text:
            continue

        source = _clean_text(
            signal.get("source_title")
        )

        if source:

            evidence.append(
                f"{text} [{source}]"
            )

        else:

            evidence.append(text)

    return evidence


# =========================================================
# SOURCE BUILDING
# =========================================================

def _build_sources(
    signal_ids: list[int],
    signals: list[dict]
) -> list[str]:

    sources = []

    for signal_id in signal_ids:

        signal = signals[signal_id - 1]

        url = _clean_text(
            signal.get("source_url")
        )

        if url and url not in sources:
            sources.append(url)

    return sources


# =========================================================
# EVIDENCE QUALITY
# =========================================================

def _calculate_evidence_quality(
    signal_ids: list[int],
    signals: list[dict]
) -> dict:
    """
    Calculate evidence quality for a trend.
    """

    if not signal_ids:

        return {
            "quality": "low",
            "score": 0,
            "basis": [],
        }

    supporting = [
        signals[signal_id - 1]
        for signal_id in signal_ids
        if 1 <= signal_id <= len(signals)
    ]

    if not supporting:

        return {
            "quality": "low",
            "score": 0,
            "basis": [],
        }

    evidence_scores = [
        _normalize_score(
            signal.get("evidence_strength")
        )
        for signal in supporting
    ]

    momentum_scores = [
        _normalize_score(
            signal.get("momentum")
        )
        for signal in supporting
    ]

    max_evidence = max(evidence_scores)

    avg_evidence = (
        sum(evidence_scores)
        / len(evidence_scores)
    )

    max_momentum = max(momentum_scores)

    basis = []

    # -----------------------------------------------------
    # Independent sources
    # -----------------------------------------------------

    unique_sources = set(
        _clean_text(
            signal.get("source_url")
        )
        for signal in supporting
        if _clean_text(
            signal.get("source_url")
        )
    )

    if len(unique_sources) >= 2:

        basis.append(
            "cross-source convergence"
        )

    # -----------------------------------------------------
    # Popularity / quantitative evidence
    # -----------------------------------------------------

    quantitative_patterns = [
        "%",
        "increased",
        "increase",
        "grew",
        "growth",
        "rose",
        "rising",
        "tripled",
        "doubled",
        "more than",
        "searches",
        "adoption",
        "sales",
        "demand",
        "engagement",
    ]

    has_quantitative_evidence = False

    for signal in supporting:

        evidence = _clean_text(
            signal.get("evidence")
        ).lower()

        indicators = [
            item.lower()
            for item in signal.get(
                "popularity_indicators",
                []
            )
        ]

        if any(
            pattern in evidence
            for pattern in quantitative_patterns
        ):

            has_quantitative_evidence = True

        if any(
            any(
                pattern in indicator
                for pattern in quantitative_patterns
            )
            for indicator in indicators
        ):

            has_quantitative_evidence = True

    if has_quantitative_evidence:

        basis.append(
            "quantitative or popularity evidence"
        )

    # -----------------------------------------------------
    # Behavioral evidence
    # -----------------------------------------------------

    behavioral_language = [
        "consumers are",
        "consumers increasingly",
        "homeowners are",
        "designers are",
        "people are",
        "moving away",
        "shifting toward",
        "increasingly selecting",
        "increasingly using",
        "adopting",
        "adoption",
        "preference",
        "choosing",
        "selecting",
    ]

    has_behavioral_evidence = False

    for signal in supporting:

        behavior = _clean_text(
            signal.get("behavior_change")
        ).lower()

        if any(
            phrase in behavior
            for phrase in behavioral_language
        ):

            has_behavioral_evidence = True
            break

    if has_behavioral_evidence:

        basis.append(
            "behavioral or preference shift"
        )

    # -----------------------------------------------------
    # Momentum
    # -----------------------------------------------------

    if max_momentum >= 7:

        basis.append(
            "strong momentum"
        )

    # -----------------------------------------------------
    # Quality score
    # -----------------------------------------------------

    score = (
        avg_evidence * 0.45
        + max_evidence * 0.25
        + max_momentum * 0.15
        + min(len(unique_sources), 3) * 0.5
        + min(len(basis), 4) * 0.5
    )

    # -----------------------------------------------------
    # Classification
    # -----------------------------------------------------

    if (
        has_quantitative_evidence
        and max_evidence >= 7
    ):

        quality = "high"

    elif (
        len(supporting) >= 2
        and len(unique_sources) >= 2
        and avg_evidence >= MIN_MEDIUM_EVIDENCE_SCORE
    ):

        quality = "high"

    elif (
        max_evidence >= 7
        or (
            len(supporting) >= 2
            and avg_evidence >= MIN_MEDIUM_EVIDENCE_SCORE
        )
        or (
            max_momentum >= 7
            and len(unique_sources) >= 1
        )
    ):

        quality = "medium"

    else:

        quality = "low"

    return {
        "quality": quality,
        "score": round(score, 2),
        "basis": basis,
    }


# =========================================================
# TREND PROMOTION
# =========================================================

def _should_promote_trend(
    signal_ids: list[int],
    signals: list[dict]
) -> tuple[bool, dict]:

    quality = _calculate_evidence_quality(
        signal_ids,
        signals
    )

    supporting_count = len(signal_ids)

    # -----------------------------------------------------
    # HIGH QUALITY
    # -----------------------------------------------------

    if quality["quality"] == "high":

        return True, quality

    # -----------------------------------------------------
    # MULTI-SIGNAL MEDIUM QUALITY
    # -----------------------------------------------------

    if (
        quality["quality"] == "medium"
        and supporting_count >= 2
    ):

        return True, quality

    # -----------------------------------------------------
    # SINGLE SIGNAL EMERGING TREND
    # -----------------------------------------------------

    if supporting_count == 1:

        signal = signals[
            signal_ids[0] - 1
        ]

        evidence_strength = _normalize_score(
            signal.get("evidence_strength")
        )

        momentum = _normalize_score(
            signal.get("momentum")
        )

        novelty = _normalize_score(
            signal.get("novelty")
        )

        popularity = _normalize_list(
            signal.get(
                "popularity_indicators"
            )
        )

        popularity_count = len(popularity)

        # Strong evidence + meaningful momentum
        if (
            evidence_strength >= 7
            and momentum >= 6
        ):

            return True, quality

        # Strong evidence + popularity
        if (
            evidence_strength >= 6
            and popularity_count >= 1
        ):

            return True, quality

        # High novelty + popularity
        if (
            novelty >= 8
            and popularity_count >= 2
            and evidence_strength >= 5
        ):

            return True, quality

        # Strong momentum + reasonable evidence
        if (
            momentum >= 7
            and evidence_strength >= 5
        ):

            return True, quality

    return False, quality


# =========================================================
# STAGE 1 — SIGNAL CLUSTERING
# =========================================================

def _cluster_signals(
    prepared_signals: list[dict]
) -> list[dict]:
    """
    Discover relationships between signals.

    The model does NOT generate trend names here.

    It only determines whether signals represent:
        - same underlying shift
        - related but distinct
        - independent emerging trend
        - weak/noise

    This separation makes trend detection more reliable.
    """

    if not prepared_signals:
        return []

    blocks = []

    for signal in prepared_signals[
        :MAX_CLUSTER_SIGNALS
    ]:

        concepts = ", ".join(
            signal["recurring_concepts"]
        )

        blocks.append(
            f"""
SIGNAL {signal["signal_id"]}

Signal:
{signal["signal"]}

Behavior:
{signal["behavior_change"]}

Consumer need:
{signal["consumer_need"]}

Preference:
{signal["emerging_preference"]}

Type:
{signal["signal_type"]}

Concepts:
{concepts}

Evidence:
{signal["evidence"]}

Evidence strength:
{signal["evidence_strength"]}/10

Novelty:
{signal["novelty"]}/10

Momentum:
{signal["momentum"]}/10
"""
        )

    signal_text = "\n".join(blocks)

    prompt = f"""
You are AROHA's signal relationship engine.

Your task is NOT to generate trends.

Your task is to discover the underlying relationships between
research signals.

=========================================================
SIGNALS
=========================================================

{signal_text}

=========================================================
CORE PRINCIPLE
=========================================================

Two signals belong to the SAME cluster only when they describe
the SAME underlying change in:

- consumer behavior
- consumer preference
- design aesthetic
- product adoption
- technology adoption
- lifestyle behavior
- market movement

Do NOT group signals merely because they share the same industry.

For example:

Signal A:
warm textures in minimalist homes

Signal B:
natural materials in minimalist homes

Signal C:
texture replacing decorative accessories

These likely represent one underlying shift.

But:

Signal D:
large-format groutless porcelain

may represent a different product/material trend.

=========================================================
RELATIONSHIP TYPES
=========================================================

Use one of:

"same_underlying_shift"

"related_but_distinct"

"independent"

"weak"

=========================================================
IMPORTANT
=========================================================

Every signal must appear in exactly one cluster.

A cluster can contain one signal.

A single-signal cluster is valid when the signal represents
a potentially meaningful emerging trend.

Do NOT force unrelated signals together.

Do NOT discard a signal merely because another signal looks
more important.

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Format:

{{
    "clusters": [
        {{
            "signal_ids": [1, 4, 5],
            "relationship": "same_underlying_shift",
            "pattern": "short description of the shared underlying shift"
        }},
        {{
            "signal_ids": [2],
            "relationship": "independent",
            "pattern": "short description of the independent shift"
        }}
    ]
}}

Rules:

1. Every signal ID must be represented.
2. Never invent signal IDs.
3. Never place the same signal ID in multiple clusters.
4. Do not create trend names.
5. Keep pattern descriptions concise.
6. Prefer meaningful clusters over keyword matching.
7. Return JSON only.
"""

    try:

        response = generate_response(
            prompt
        )

    except Exception as exc:

        print(
            f"[Trend Clustering Error] {exc}"
        )

        return []

    parsed = _extract_json(
        response
    )

    if not parsed:
        return []

    raw_clusters = parsed.get(
        "clusters",
        []
    )

    if not isinstance(
        raw_clusters,
        list
    ):

        return []

    clusters = []

    used_ids = set()

    for raw_cluster in raw_clusters:

        if not isinstance(
            raw_cluster,
            dict
        ):

            continue

        signal_ids = _resolve_signal_ids(
            raw_cluster.get(
                "signal_ids",
                []
            ),
            prepared_signals
        )

        if not signal_ids:
            continue

        # -------------------------------------------------
        # Prevent duplicate signal assignment
        # -------------------------------------------------

        clean_ids = []

        for signal_id in signal_ids:

            if signal_id not in used_ids:

                clean_ids.append(
                    signal_id
                )

                used_ids.add(
                    signal_id
                )

        if not clean_ids:
            continue

        relationship = _clean_text(
            raw_cluster.get(
                "relationship"
            )
        )

        if relationship not in {
            "same_underlying_shift",
            "related_but_distinct",
            "independent",
            "weak",
        }:

            relationship = (
                "independent"
            )

        pattern = _clean_text(
            raw_cluster.get(
                "pattern"
            )
        )

        clusters.append(
            {
                "signal_ids": clean_ids,
                "relationship": relationship,
                "pattern": pattern,
            }
        )

    # -----------------------------------------------------
    # Deterministic recovery
    #
    # If the LLM forgot a signal, create an independent
    # cluster instead of silently losing it.
    # -----------------------------------------------------

    for signal in prepared_signals:

        signal_id = signal[
            "signal_id"
        ]

        if signal_id not in used_ids:

            clusters.append(
                {
                    "signal_ids": [
                        signal_id
                    ],
                    "relationship": "independent",
                    "pattern": signal[
                        "signal"
                    ],
                }
            )

    return clusters[:MAX_CLUSTERS]


# =========================================================
# STAGE 2 — TREND GENERATION
# =========================================================

def _generate_trends_from_clusters(
    clusters: list[dict],
    prepared_signals: list[dict]
) -> list[dict]:
    """
    Convert validated signal clusters into named trends.

    The LLM generates the trend intelligence, while the
    Python layer validates signal ownership and provides
    deterministic recovery if the LLM returns unusable JSON.
    """

    if not clusters:
        return []

    cluster_blocks = []

    for index, cluster in enumerate(
        clusters,
        start=1
    ):

        signal_ids = cluster["signal_ids"]

        signal_details = []

        for signal_id in signal_ids:

            if not (
                1 <= signal_id <= len(prepared_signals)
            ):
                continue

            signal = prepared_signals[
                signal_id - 1
            ]

            signal_details.append(
                f"""
SIGNAL {signal_id}

Signal:
{signal["signal"]}

Observation:
{signal["observation"]}

Behavior:
{signal["behavior_change"]}

Consumer need:
{signal["consumer_need"]}

Emerging preference:
{signal["emerging_preference"]}

Signal type:
{signal["signal_type"]}

Evidence:
{signal["evidence"]}

Evidence strength:
{signal["evidence_strength"]}/10

Novelty:
{signal["novelty"]}/10

Momentum:
{signal["momentum"]}/10

Recurring concepts:
{", ".join(signal["recurring_concepts"])}

Popularity indicators:
{", ".join(signal["popularity_indicators"])}

Source:
{signal["source_title"]}
"""
            )

        cluster_blocks.append(
            f"""
=========================================================
CLUSTER {index}
=========================================================

Relationship:
{cluster["relationship"]}

Pattern:
{cluster["pattern"]}

SIGNAL IDS IN THIS CLUSTER:
{signal_ids}

SIGNAL DETAILS:

{"".join(signal_details)}
"""
        )

    clusters_text = "\n".join(
        cluster_blocks
    )

    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are AROHA's senior trend intelligence engine.

You are given VALIDATED signal clusters from web research.

Your task is to convert meaningful clusters into
evidence-backed trends.

Do NOT perform clustering again.

Do NOT merge clusters.

Do NOT invent evidence.

Do NOT invent statistics.

Use ONLY the supplied signals.

=========================================================
VALIDATED CLUSTERS
=========================================================

{clusters_text}

=========================================================
CORE RULE
=========================================================

Each meaningful cluster should normally produce ONE trend.

For example:

Cluster:
Signals [1,4,5]

Pattern:
Expansion of brand-run resale and take-back programs making
second-hand fashion a mainstream growth engine.

Possible trend:

"Mainstream Circular Resale"

The trend must be supported by signals [1,4,5].

=========================================================
SINGLE-SIGNAL CLUSTERS
=========================================================

A single-signal cluster CAN produce a trend.

For example:

Signal [2]

Evidence strength: 8/10
Momentum: 7/10
Novelty: 7/10

This is strong enough to represent an emerging trend.

Therefore DO NOT discard a single-signal cluster merely
because it contains one signal.

=========================================================
WEAK CLUSTERS
=========================================================

A "weak" cluster should normally be rejected unless its
signal contains unusually strong evidence.

=========================================================
TREND DESCRIPTION
=========================================================

Explain:

1. What is changing?
2. How is it changing?
3. What does this look like in practice?

Use ONLY supplied evidence.

=========================================================
WHY IT MATTERS
=========================================================

Explain strategic significance based ONLY on supplied
signals.

Possible areas:

- consumer demand
- product opportunities
- market implications
- business implications
- design implications

Do not speculate beyond the evidence.

=========================================================
TREND TYPE
=========================================================

Choose exactly one:

behavior
consumer
design
product
technology
culture
lifestyle
market
sustainability
hybrid

=========================================================
SCORES
=========================================================

confidence: 0-10

momentum: 0-10

novelty: 0-10

Scores must reflect the supplied signals.

=========================================================
SIGNAL OWNERSHIP
=========================================================

THIS IS EXTREMELY IMPORTANT.

Every trend MUST contain supporting_signal_ids.

Those IDs MUST come from the SAME cluster that produced
the trend.

For example:

Cluster signals:
[1,4,5]

Valid:

"supporting_signal_ids": [1,4,5]

Invalid:

"supporting_signal_ids": [1,2,5]

because signal 2 belongs to another cluster.

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "trends": [
        {{
            "trend": "short meaningful trend name",
            "description": "what is changing and how it is appearing",
            "why_it_matters": "strategic significance",
            "trend_type": "market",
            "supporting_signal_ids": [1,4,5],
            "confidence": 8,
            "momentum": 8,
            "novelty": 7
        }}
    ]
}}

=========================================================
FINAL RULES
=========================================================

1. Do not create more than {MAX_TRENDS} trends.

2. Do not create a trend merely because a cluster exists.

3. However, DO NOT unnecessarily reject strong single-signal
   emerging trends.

4. Do not merge clusters.

5. Do not invent facts.

6. Do not invent statistics.

7. Every trend MUST have supporting_signal_ids.

8. Every supporting signal ID MUST belong to its cluster.

9. Return JSON only.

10. Prefer 2–4 meaningful trends when evidence supports them.

=========================================================
"""

    try:

        response = generate_response(
            prompt
        )

    except Exception as exc:

        print(
            f"[Trend Generation Error] {exc}"
        )

        return []

    # =====================================================
    # DEBUG — VERY IMPORTANT
    # =====================================================

    print(
        "\n[AROHA] RAW TREND GENERATION RESPONSE"
    )

    print(
        response
    )

    # =====================================================
    # PARSE
    # =====================================================

    parsed = _extract_json(
        response
    )

    if not parsed:

        print(
            "[AROHA] Trend generation returned "
            "invalid JSON."
        )

        return []

    raw_trends = parsed.get(
        "trends",
        []
    )

    if not isinstance(
        raw_trends,
        list
    ):

        print(
            "[AROHA] 'trends' field is not a list."
        )

        return []

    # =====================================================
    # VALIDATE CLUSTER OWNERSHIP
    # =====================================================

    validated_trends = []

    for raw_trend in raw_trends:

        if not isinstance(
            raw_trend,
            dict
        ):
            continue

        trend_name = _clean_text(
            raw_trend.get("trend")
        )

        signal_ids = _resolve_signal_ids(
            raw_trend.get(
                "supporting_signal_ids",
                []
            ),
            prepared_signals
        )

        if not trend_name:
            continue

        if not signal_ids:
            print(
                f"[AROHA] Rejected trend '{trend_name}': "
                "no supporting signal IDs."
            )

            continue

        # -------------------------------------------------
        # Find owning cluster
        # -------------------------------------------------

        owning_cluster = None

        for cluster in clusters:

            cluster_ids = set(
                cluster["signal_ids"]
            )

            if set(signal_ids).issubset(
                cluster_ids
            ):

                owning_cluster = cluster
                break

        if owning_cluster is None:

            print(
                f"[AROHA] Rejected trend '{trend_name}': "
                f"signal IDs {signal_ids} do not belong "
                f"to one cluster."
            )

            continue

        # -------------------------------------------------
        # Keep validated trend
        # -------------------------------------------------

        validated_trends.append(
            raw_trend
        )

    print(
        f"[AROHA] Validated generated trends: "
        f"{len(validated_trends)}"
    )

    return validated_trends


# =========================================================
# COVERAGE CHECK
# =========================================================

def _calculate_signal_coverage(
    trends: list[dict],
    signal_count: int
) -> dict:
    """
    Determine how many research signals were represented
    by generated trends.
    """

    used = set()

    for trend in trends:

        for signal_id in trend.get(
            "supporting_signal_ids",
            []
        ):

            try:

                signal_id = int(
                    signal_id
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            if (
                1 <= signal_id <= signal_count
            ):

                used.add(
                    signal_id
                )

    all_ids = set(
        range(
            1,
            signal_count + 1
        )
    )

    unused = sorted(
        all_ids - used
    )

    return {
        "used_signal_ids": sorted(
            used
        ),
        "unused_signal_ids": unused,
        "coverage": (
            len(used) / signal_count
            if signal_count
            else 0
        ),
    }


# =========================================================
# TREND FINALIZATION
# =========================================================

def _finalize_trends(
    raw_trends: list[dict],
    prepared_signals: list[dict]
) -> list[dict]:

    final_trends = []

    seen_trends = set()

    for raw_trend in raw_trends:

        if not isinstance(
            raw_trend,
            dict
        ):

            continue

        trend_name = _clean_text(
            raw_trend.get(
                "trend"
            )
        )

        description = _clean_text(
            raw_trend.get(
                "description"
            )
        )

        why_it_matters = _clean_text(
            raw_trend.get(
                "why_it_matters"
            )
        )

        if not trend_name or not description:
            continue

        # -------------------------------------------------
        # Resolve signal IDs
        # -------------------------------------------------

        signal_ids = _resolve_signal_ids(
            raw_trend.get(
                "supporting_signal_ids",
                []
            ),
            prepared_signals
        )

        if not signal_ids:
            continue

        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        evidence = _build_evidence(
            signal_ids,
            prepared_signals
        )

        if not evidence:
            continue

        # -------------------------------------------------
        # Sources
        # -------------------------------------------------

        supporting_sources = _build_sources(
            signal_ids,
            prepared_signals
        )

        if not supporting_sources:
            continue

        # -------------------------------------------------
        # Evidence gate
        # -------------------------------------------------

        should_promote, evidence_quality = (
            _should_promote_trend(
                signal_ids,
                prepared_signals
            )
        )

        if not should_promote:

            print(
                f"[AROHA] Trend rejected: "
                f"'{trend_name}' | "
                f"signals={signal_ids} | "
                f"quality={evidence_quality['quality']} | "
                f"score={evidence_quality['score']}"
            )    

            continue

        # -------------------------------------------------
        # Scores
        # -------------------------------------------------

        confidence = _normalize_score(
            raw_trend.get(
                "confidence"
            )
        )

        momentum = _normalize_score(
            raw_trend.get(
                "momentum"
            )
        )

        novelty = _normalize_score(
            raw_trend.get(
                "novelty"
            )
        )

        if confidence < MIN_CONFIDENCE:
            continue

        # -------------------------------------------------
        # Duplicate protection
        # -------------------------------------------------

        trend_key = re.sub(
            r"[^a-z0-9]+",
            " ",
            trend_name.lower()
        ).strip()

        if trend_key in seen_trends:
            continue

        seen_trends.add(
            trend_key
        )

        # -------------------------------------------------
        # Final object
        # -------------------------------------------------

        final_trends.append(
            {
                "trend": trend_name,

                "description": description,

                "supporting_sources":
                    supporting_sources,

                "supporting_signal_count":
                    len(signal_ids),

                "supporting_signal_ids":
                    signal_ids,

                "supporting_signals": [
                    prepared_signals[
                        i - 1
                    ]["signal"]
                    for i in signal_ids
                ],

                "evidence":
                    evidence,

                "evidence_quality":
                    evidence_quality[
                        "quality"
                    ],

                "evidence_quality_score":
                    evidence_quality[
                        "score"
                    ],

                "evidence_basis":
                    evidence_quality[
                        "basis"
                    ],

                "confidence":
                    confidence,

                "momentum":
                    momentum,

                "novelty":
                    novelty,

                "trend_type":
                    _clean_text(
                        raw_trend.get(
                            "trend_type"
                        )
                    ),

                "why_it_matters":
                    why_it_matters,

                "valid":
                    True,
            }
        )

    return final_trends


# =========================================================
# TREND RANKING
# =========================================================

def _rank_trends(
    trends: list[dict]
) -> list[dict]:
    """
    Rank trends while balancing:

    - evidence
    - confidence
    - momentum
    - novelty
    - signal convergence
    """

    def trend_score(
        trend
    ):

        signal_count = min(
            trend.get(
                "supporting_signal_count",
                0
            ),
            5
        )

        confidence = trend.get(
            "confidence",
            0
        )

        momentum = trend.get(
            "momentum",
            0
        )

        novelty = trend.get(
            "novelty",
            0
        )

        evidence_quality_score = (
            trend.get(
                "evidence_quality_score",
                0
            )
        )

        # Multiple signals matter,
        # but should not completely dominate
        # strong emerging single-signal trends.

        convergence_bonus = min(
            signal_count - 1,
            3
        ) * 1.5

        return (
            confidence * 1.5
            + momentum * 1.2
            + novelty * 0.7
            + evidence_quality_score * 0.7
            + convergence_bonus
        )

    trends.sort(
        key=trend_score,
        reverse=True
    )

    return trends[:MAX_TRENDS]


# =========================================================
# MAIN TREND DETECTION
# =========================================================

def detect_trends(
    signals: list[dict]
) -> list[dict]:
    """
    AROHA trend detection pipeline.

    Signals
       ↓
    Signal preparation
       ↓
    Stage 1: relationship clustering
       ↓
    Stage 2: trend generation
       ↓
    Evidence validation
       ↓
    Coverage validation
       ↓
    Ranking
       ↓
    Final trends
    """

    # =====================================================
    # PREPARE SIGNALS
    # =====================================================

    prepared_signals = _prepare_signals(
        signals
    )

    if not prepared_signals:
        return []

    print(
        "\n[AROHA] Trend detection started."
    )

    print(
        f"[AROHA] Signals available: "
        f"{len(prepared_signals)}"
    )

    # =====================================================
    # STAGE 1
    # =====================================================

    print(
        "[AROHA] Stage 1: discovering "
        "signal relationships..."
    )

    clusters = _cluster_signals(
        prepared_signals
    )

    if not clusters:

        print(
            "[AROHA] No signal clusters found."
        )

        return []

    # =====================================================
    # DEBUG CLUSTERS
    # =====================================================

    print(
        "\n[AROHA] DISCOVERED SIGNAL CLUSTERS"
    )

    for index, cluster in enumerate(
        clusters,
        start=1
    ):

        print(
            f"\nCluster {index}"
        )

        print(
            f"Relationship: "
            f"{cluster['relationship']}"
        )

        print(
            f"Signals: "
            f"{cluster['signal_ids']}"
        )

        print(
            f"Pattern: "
            f"{cluster['pattern']}"
        )

    # =====================================================
    # STAGE 2
    # =====================================================

    print(
        "\n[AROHA] Stage 2: generating "
        "trends from clusters..."
    )

    raw_trends = (
        _generate_trends_from_clusters(
            clusters,
            prepared_signals
        )
    )

    print(
        f"\n[AROHA] Raw trends generated: "
        f"{len(raw_trends)}"
    )

    if not raw_trends:

        print(
            "[AROHA] No trends generated."
        )

        return []

    # =====================================================
    # FINALIZE
    # =====================================================

    final_trends = _finalize_trends(
        raw_trends,
        prepared_signals
    )

    # =====================================================
    # COVERAGE
    # =====================================================

    coverage = _calculate_signal_coverage(
        final_trends,
        len(prepared_signals)
    )

    print(
        "\n[AROHA] SIGNAL COVERAGE"
    )

    print(
        f"Used signals: "
        f"{coverage['used_signal_ids']}"
    )

    print(
        f"Unused signals: "
        f"{coverage['unused_signal_ids']}"
    )

    print(
        f"Coverage: "
        f"{coverage['coverage'] * 100:.1f}%"
    )

    # =====================================================
    # RANK
    # =====================================================

    final_trends = _rank_trends(
        final_trends
    )

    print(
        f"\n[AROHA] Final trends: "
        f"{len(final_trends)}"
    )

    return final_trends
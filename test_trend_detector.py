from src.research.web_search import search_web
from src.analysis.signal_analyzer import extract_signals_from_results
from src.analysis.trend_detector import detect_trends

import pprint


query = "emerging interior design trends 2026"


# =========================================================
# STEP 1: SEARCH THE WEB
# =========================================================

results = search_web(
    query,
    max_results=5
)


# =========================================================
# STEP 2: EXTRACT SIGNALS
# =========================================================

signals = extract_signals_from_results(results)

print("\n")
print("=" * 70)
print("EXTRACTED SIGNALS")
print("=" * 70)

import pprint
pprint.pp(signals)


# =========================================================
# STEP 3: DETECT TRENDS
# =========================================================

trends = detect_trends(signals)


# =========================================================
# DEBUG — SHOW COMPLETE RAW TREND OBJECTS
# =========================================================

print("\n")
print("=" * 70)
print("RAW TREND OBJECTS")
print("=" * 70)

pprint.pp(trends)


# =========================================================
# HUMAN-READABLE OUTPUT
# =========================================================

print("\n")
print("=" * 70)
print("AROHA AI — DETECTED TRENDS")
print("=" * 70)


for i, trend in enumerate(trends, start=1):

    print(f"\nTREND {i}")
    print("-" * 70)

    print("Trend:")
    print(trend.get("trend"))

    print("\nDescription:")
    print(trend.get("description"))

    print("\nTrend Type:")
    print(trend.get("trend_type"))

    print("\nSupporting Signal IDs:")
    print(trend.get("supporting_signal_ids"))

    print("\nSupporting Signals:")
    for signal in trend.get("supporting_signals", []):
        print(f"  - {signal}")

    print("\nSupporting Sources:")
    for source in trend.get("supporting_sources", []):
        print(f"  - {source}")

    print("\nSupporting Signal Count:")
    print(trend.get("supporting_signal_count"))

    print("\nEvidence:")
    for evidence in trend.get("evidence", []):
        print(f"  - {evidence}")

    print("\nEvidence Quality:")
    print(trend.get("evidence_quality"))

    print("\nEvidence Quality Score:")
    print(trend.get("evidence_quality_score"))

    print("\nEvidence Basis:")
    for basis in trend.get("evidence_basis", []):
        print(f"  - {basis}")

    print("\nConfidence:")
    print(trend.get("confidence"))

    print("\nMomentum:")
    print(trend.get("momentum"))

    print("\nNovelty:")
    print(trend.get("novelty"))

    print("\nWhy It Matters:")
    print(trend.get("why_it_matters"))


from src.research.web_search import search_web
from src.analysis.signal_analyzer import extract_signals_from_results
from src.analysis.trend_detector import detect_trends
from src.analysis.opportunity_scorer import score_opportunities
from src.analysis.creative_generator import generate_creative_directions


query = "current trends in minimalist home decor"


# 1. Search the web
results = search_web(
    query,
    max_results=5
)


# 2. Extract signals
signals = extract_signals_from_results(results)


# 3. Detect trends
trends = detect_trends(signals)


# 4. Score opportunities
opportunities = score_opportunities(trends)


# 5. Generate creative directions
directions = generate_creative_directions(opportunities)


print("\n")
print("=" * 70)
print("AROHA AI — CREATIVE DIRECTIONS")
print("=" * 70)


for i, direction in enumerate(directions, start=1):

    print(f"\nDIRECTION {i}")
    print("-" * 70)

    print("Name:")
    print(direction.get("name"))

    print("\nConcept:")
    print(direction.get("concept"))

    print("\nCreative Direction:")
    print(direction.get("creative_direction"))

    print("\nTarget Audience:")
    print(direction.get("target_audience"))

    print("\nRationale:")
    print(direction.get("rationale"))

    print("\nSupporting Trend:")
    print(direction.get("supporting_trend"))

    print("\nSupporting Evidence:")

    for evidence in direction.get("supporting_evidence", []):
        print(f"  - {evidence}")
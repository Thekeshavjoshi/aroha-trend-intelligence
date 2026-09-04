from src.research.web_search import search_web
from src.analysis.signal_analyzer import extract_signals_from_results
from src.analysis.trend_detector import detect_trends
from src.analysis.opportunity_scorer import score_opportunities


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


print("\n")
print("=" * 70)
print("AROHA AI — OPPORTUNITY ANALYSIS")
print("=" * 70)


for i, opportunity in enumerate(opportunities, start=1):

    print(f"\nOPPORTUNITY {i}")
    print("-" * 70)

    print("Trend:")
    print(opportunity.get("trend"))

    print("\nEvidence Strength:")
    print(f"{opportunity.get('evidence_strength')}/10")

    print("\nGrowth Signal:")
    print(f"{opportunity.get('growth_signal')}/10")

    print("\nCreative Potential:")
    print(f"{opportunity.get('creative_potential')}/10")

    print("\nCommercial Potential:")
    print(f"{opportunity.get('commercial_potential')}/10")

    print("\nOverall Opportunity Score:")
    print(f"{opportunity.get('overall_score')}/10")

    print("\nReasoning:")
    print(opportunity.get("reasoning"))

    print("\nOpportunity:")
    print(opportunity.get("opportunity"))
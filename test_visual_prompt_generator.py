from src.research.web_search import search_web
from src.analysis.signal_analyzer import extract_signals_from_results
from src.analysis.trend_detector import detect_trends
from src.analysis.opportunity_scorer import score_opportunities
from src.analysis.creative_generator import generate_creative_directions
from src.visualization.visual_prompt_generator import generate_visual_prompts


query = "current trends in minimalist home decor"


# 1. Web research
results = search_web(
    query,
    max_results=5
)


# 2. Signal extraction
signals = extract_signals_from_results(results)


# 3. Trend detection
trends = detect_trends(signals)


# 4. Opportunity scoring
opportunities = score_opportunities(trends)


# 5. Creative directions
directions = generate_creative_directions(opportunities)


# 6. Generate visual prompts
visual_prompts = generate_visual_prompts(directions)


print("\n")
print("=" * 70)
print("AROHA AI — VISUAL CONCEPT PROMPTS")
print("=" * 70)


for i, item in enumerate(visual_prompts, start=1):

    print(f"\nVISUAL CONCEPT {i}")
    print("-" * 70)

    print("Name:")
    print(item.get("name"))

    print("\nVisual Prompt:")
    print(item.get("visual_prompt"))

    print("\nVisual Rationale:")
    print(item.get("visual_rationale"))
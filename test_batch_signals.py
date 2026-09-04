from src.research.web_search import search_web
from src.analysis.signal_analyzer import extract_signals_from_results


query = "current trends in minimalist home decor"

results = search_web(
    query,
    max_results=5
)

signals = extract_signals_from_results(results)


for i, signal in enumerate(signals, start=1):

    print(f"\n{'=' * 60}")
    print(f"SIGNAL {i}")
    print(f"{'=' * 60}")

    print(signal)
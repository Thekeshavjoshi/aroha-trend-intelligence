from src.research.web_search import search_web
from src.signal_extractor import extract_signals


query = "current trends in minimalist home decor"

results = search_web(query, max_results=1)

signal = extract_signals(results[0])

print("\nExtracted Signal:")
print(signal)
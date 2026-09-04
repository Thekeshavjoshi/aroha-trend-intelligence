from src.research.web_search import search_web


query = "current trends in minimalist home decor"

results = search_web(query)


for i, result in enumerate(results, start=1):
    print(f"\n--- Result {i} ---")
    print("Title:", result.get("title"))
    print("URL:", result.get("url"))
    print("Content:", result.get("content", "")[:500])
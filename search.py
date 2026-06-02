from tavily import TavilyClient
import os

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

SEARCH_QUERIES = [
    "Van Gogh style art for sale original painting",
    "Van Gogh inspired artwork buy swirling brushstrokes",
    "impasto Van Gogh aesthetic print for sale",
]

def search_art_listings() -> list[dict]:
    """Search for Van Gogh style art listings via Tavily."""
    results = []
    for query in SEARCH_QUERIES:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_images=True,
        )
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("content", ""),
                "image_url": r.get("image", ""),
                "source": r.get("url", ""),
            })
    return results

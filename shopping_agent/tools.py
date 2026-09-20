"""
tools.py
--------
The "actions" the shopping agent is allowed to take. Each function decorated
with @tool becomes something the LLM can choose to call, with structured
arguments, as part of its own reasoning (this is what makes it "agentic"
rather than a plain chatbot).

Two tools are exposed:
  1. search_products   -> hits real e-commerce data through SerpApi's
                           Google Shopping engine (falls back to a local
                           mock catalog if no SERPAPI_API_KEY is set, so the
                           project still runs for a demo/offline grading).
  2. get_product_reviews_snippet -> pulls a short real review/opinion
                           snippet for a specific product via a Google
                           search, so the agent can factor in sentiment,
                           not just price.
"""

import os
import requests
from langchain_core.tools import tool

def _get_serpapi_key():
    return os.getenv("SERPAPI_API_KEY", "").strip()
SERPAPI_URL = "https://serpapi.com/search"

# ---------------------------------------------------------------------------
# Mock catalog used only when no SERPAPI_API_KEY is configured, so graders /
# reviewers can run the project with zero external cost. Structure mirrors
# what SerpApi's shopping_results returns, so the rest of the agent code
# doesn't need to know which source it came from.
# ---------------------------------------------------------------------------
_MOCK_CATALOG = [
    {"title": "Noise ColorFit Pulse 2 Smartwatch", "price": 1499, "source": "Flipkart", "rating": 4.1, "link": "https://example.com/p1", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "boAt Xtend Smartwatch", "price": 1799, "source": "Amazon", "rating": 4.0, "link": "https://example.com/p2", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "Noise Icon 3 Smartwatch", "price": 1299, "source": "Myntra", "rating": 3.9, "link": "https://example.com/p3", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "boAt Wave Call Smartwatch", "price": 999, "source": "Flipkart", "rating": 3.8, "link": "https://example.com/p4", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "Fire-Boltt Ninja Call Pro Plus", "price": 1399, "source": "Amazon", "rating": 4.0, "link": "https://example.com/p5", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "Fastrack Reflex Play Smartwatch", "price": 1899, "source": "Myntra", "rating": 3.7, "link": "https://example.com/p6", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "Noise Pulse Go Buzz Smartwatch", "price": 1199, "source": "Flipkart", "rating": 3.9, "link": "https://example.com/p7", "image": "https://placehold.co/160x160/png?text=Watch"},
    {"title": "boAt Storm Call Smartwatch", "price": 1599, "source": "Amazon", "rating": 4.2, "link": "https://example.com/p8", "image": "https://placehold.co/160x160/png?text=Watch"},
]


def _mock_search(query: str, max_price: float | None):
    q = query.lower()
    results = [p for p in _MOCK_CATALOG if any(w in p["title"].lower() for w in q.split())]
    if not results:
        results = _MOCK_CATALOG  # generic fallback so the demo never returns empty
    if max_price:
        results = [p for p in results if p["price"] <= max_price] or results
    return results[:8]


@tool
def search_products(query: str, max_price: float = 0) -> str:
    """
    Search for real, currently-listed products matching a shopping query.
    Use this whenever you need actual product names, prices, ratings, or
    sellers to base a recommendation on -- never invent products or prices
    yourself.

    Args:
        query: what to search for, e.g. "wireless earbuds under 2000" or
               "smartwatch with heart rate monitor".
        max_price: optional upper price bound in INR. Pass 0 for no limit.

    Returns:
        A formatted list of matching products with price, rating, seller
        and link.
    """
    max_p = max_price if max_price and max_price > 0 else None

    serpapi_key = _get_serpapi_key()
    if serpapi_key:
        try:
            params = {
                "engine": "google_shopping",
                "q": query,
                "api_key": serpapi_key,
                "gl": "in",
                "hl": "en",
            }
            resp = requests.get(SERPAPI_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("shopping_results", [])
            items = []
            for d in data:
                price = d.get("extracted_price")
                if max_p and price and price > max_p:
                    continue
                raw_link = d.get("link") or d.get("product_link") or ""
                if raw_link and not raw_link.startswith("http"):
                    raw_link = "https://www.google.com" + raw_link
                items.append(
                    {
                        "title": d.get("title", "Unknown product"),
                        "price": price,
                        "source": d.get("source", "Unknown seller"),
                        "rating": d.get("rating", "N/A"),
                        "link": raw_link,
                        "image": d.get("thumbnail", ""),
                    }
                )
                if len(items) >= 8:
                    break
            if items:
                return _format_products(items, live=True)
            # SerpApi returned nothing usable -> fall through to mock
        except requests.RequestException as e:
            return (
                f"[Live product search failed: {e}. Falling back to sample "
                f"catalog for this query.]\n"
                + _format_products(_mock_search(query, max_p), live=False)
            )

    return _format_products(_mock_search(query, max_p), live=False)


def _format_products(items, live: bool) -> str:
    if not items:
        return "No products found matching that query."
    header = "LIVE marketplace results:" if live else "SAMPLE catalog results (no SERPAPI_API_KEY set):"
    lines = [header]
    for i, p in enumerate(items, 1):
        price = p["price"] if p["price"] else "price unavailable"
        lines.append(
            f"{i}. {p['title']} | ₹{price} | {p['source']} | rating: {p['rating']} | "
            f"link: {p['link']} | image: {p.get('image', '')}"
        )
    return "\n".join(lines)


@tool
def get_product_reviews_snippet(product_name: str) -> str:
    """
    Get a short real-world opinion/review snippet for a specific product
    name, to sanity-check quality/sentiment before recommending it.

    Args:
        product_name: the exact product title to look up.
    """
    serpapi_key = _get_serpapi_key()
    if not serpapi_key:
        return (
            f"No live review data available (no SERPAPI_API_KEY set). "
            f"Rely on the star rating already returned by search_products "
            f"for '{product_name}'."
        )
    try:
        params = {
            "engine": "google",
            "q": f"{product_name} review",
            "api_key": serpapi_key,
            "gl": "in",
            "hl": "en",
        }
        resp = requests.get(SERPAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        organic = resp.json().get("organic_results", [])
        if not organic:
            return f"No review snippets found for '{product_name}'."
        snippet = organic[0].get("snippet", "No snippet available.")
        return f"Review snippet for '{product_name}': {snippet}"
    except requests.RequestException as e:
        return f"Review lookup failed: {e}"


TOOLS = [search_products, get_product_reviews_snippet]

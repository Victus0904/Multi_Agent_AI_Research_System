"""Web search (Tavily) and scraping (requests + BeautifulSoup) tools used by the agents."""

from __future__ import annotations

import os
from functools import lru_cache

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

USER_AGENT = "Mozilla/5.0 (compatible; ResearchAssistant/1.0)"


@lru_cache(maxsize=1)
def get_tavily_client():
    """Create the Tavily client on first use so importing this module never needs a key."""
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set. Add it to your .env file (see .env.example).")
    return TavilyClient(api_key)


def format_search_results(results: dict) -> str:
    """Format a Tavily response as readable Title / URL / Snippet blocks."""
    out = []

    for r in results.get("results", []):
        out.append(
            f"Title: {r.get('title', 'Untitled')}\n"
            f"URL: {r.get('url', 'No URL')}\n"
            f"Snippet: {r.get('content', '')[:160]}"
        )
    return "\n----\n".join(out) if out else "No search results found."


def search_web_direct(query: str, max_results: int = 3) -> tuple[str, list[str]]:
    """Search the web and return ``(formatted_results, urls)``."""
    results = get_tavily_client().search(query, max_results=max_results)
    urls = [
        r.get("url")
        for r in results.get("results", [])
        if r.get("url")
    ]
    return format_search_results(results), urls


def scrape_url_direct(url: str, max_chars: int = 700) -> str:
    """Fetch ``url`` and return up to ``max_chars`` of visible text (errors are returned as text)."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())  # collapse whitespace
        return text[:max_chars] if text else "No readable text found on the page."
    except requests.RequestException as e:
        return f"Error scraping URL: {e}"


@tool
def web_search(query: str) -> str:
    """Searches the recent and reliable information on the web.
    Returns Titles, URLs and snippets"""
    formatted, _ = search_web_direct(query)
    return formatted


@tool
def scrape_url(url: str) -> str:
    """Scrapes and returns clean text content from a given URL for deeper reading"""
    return scrape_url_direct(url)

from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))


def format_search_results(results: dict) -> str:
    out = []

    for r in results.get("results", []):
        out .append(
            f"Title: {r.get('title', 'Untitled')}\n"
            f"URL: {r.get('url', 'No URL')}\n"
            f"Snippet: {r.get('content', '')[:160]}"
        )
    return "\n----\n".join(out) if out else "No search results found."


def search_web_direct(query: str, max_results: int = 3) -> tuple[str, list[str]]:
    results = tavily.search(query, max_results=max_results, page=1, sort_by="relevance")
    urls = [
        r.get("url")
        for r in results.get("results", [])
        if r.get("url")
    ]
    return format_search_results(results), urls


def scrape_url_direct(url: str, max_chars: int = 700) -> str:
    try:
        resp = requests.get(url, timeout = 8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip = True)
        return text[:max_chars] if text else "No readable text found on the page."
    except Exception as e:
        return f"Error scraping URL: {str(e)}"


@tool
def web_search(query: str) -> str:
    """Searches the recent and reliable information on the web.
    Returns Titles, URLs and snippets"""
    formatted, _ = search_web_direct(query)
    return formatted


@tool
def scrape_url(url: str)-> str:
    """Scrapes and returns clean text content from a given URL for deeper reading"""
    return scrape_url_direct(url)

from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Searches the recent and reliable information on the web.
    Returns Titles, URLs and snippets"""
    results = tavily.search(query, max_results=5, page=1, sort_by="relevance")

    out = []

    for r in results['results']:
        out .append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}"
        )
    return "\n----\n".join(out)


@tool
def scrape_url(url: str)-> str:
    """Scrapes and returns clean text content from a given URL for deeper reading"""
    try:
        resp = requests.get(url, timeout = 8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
            return soup.get_text(separator=" ", strip = True)[:3000]
    except Exception as e:
        return f"Error scraping URL: {str(e)}"
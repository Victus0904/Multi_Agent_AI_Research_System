"""Offline tests: no API keys or network access needed."""

import sys
import threading
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools  # noqa: E402
import web_app  # noqa: E402


def test_format_search_results():
    text = tools.format_search_results(
        {"results": [{"title": "A", "url": "https://a.example", "content": "x" * 500}]}
    )
    assert "Title: A" in text and "URL: https://a.example" in text
    assert len(text.split("Snippet: ")[1]) == 160
    assert tools.format_search_results({}) == "No search results found."


def test_missing_tavily_key_raises_clear_error(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    tools.get_tavily_client.cache_clear()
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        tools.search_web_direct("anything")


def test_scrape_strips_scripts(monkeypatch):
    class Resp:
        text = "<html><script>bad()</script><nav>menu</nav><p>Hello   world</p></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(tools.requests, "get", lambda *a, **k: Resp())
    assert tools.scrape_url_direct("https://example.com") == "Hello world"


def test_scrape_reports_http_errors(monkeypatch):
    def boom(*a, **k):
        raise tools.requests.ConnectionError("offline")

    monkeypatch.setattr(tools.requests, "get", boom)
    assert tools.scrape_url_direct("https://example.com").startswith("Error scraping URL")


def test_render_page_escapes_html():
    page = web_app.render_page(topic="<script>x</script>", state={"report": "<b>r</b>"}).decode()
    assert "<script>x</script>" not in page
    assert "&lt;b&gt;r&lt;/b&gt;" in page


def test_pipeline_limit_text():
    pytest.importorskip("langchain_mistralai")
    import os

    os.environ.setdefault("MISTRAL_API_KEY", "dummy")
    from pipeline import limit_text

    assert limit_text("short", 10) == "short"
    assert limit_text("one two three four", 9).startswith("one two")
    assert limit_text(None, 5) == ""


@pytest.fixture
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), web_app.ResearchHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_web_get_and_empty_post(server):
    assert b"Research Pipeline" in urllib.request.urlopen(server + "/").read()
    data = urllib.parse.urlencode({"topic": "  "}).encode()
    body = urllib.request.urlopen(server + "/research", data=data).read()
    assert b"Please enter a research topic." in body

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from pipeline import run_research_pipeline_low_call


HOST = "127.0.0.1"
PORT = 8000


def escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def render_page(
    *,
    topic: str = "",
    state: dict | None = None,
    error: str | None = None,
    is_loading_hint: bool = False,
) -> bytes:
    report = state or {}
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research Pipeline</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #20242a;
      --muted: #606975;
      --line: #d9dee7;
      --accent: #1f6f5b;
      --accent-strong: #155344;
      --danger: #9f2d20;
      --soft: #eef4f2;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}

    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }}

    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 18px;
    }}

    h1 {{
      margin: 0;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: 0;
    }}

    .subtitle {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}

    form {{
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      padding: 14px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-bottom: 16px;
    }}

    input {{
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      color: var(--text);
      font-size: 15px;
    }}

    button {{
      min-height: 42px;
      border: 0;
      border-radius: 6px;
      padding: 0 16px;
      background: var(--accent);
      color: white;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
    }}

    button:hover {{
      background: var(--accent-strong);
    }}

    .voice-button {{
      width: 42px;
      padding: 0;
      background: var(--soft);
      color: var(--accent-strong);
      border: 1px solid var(--line);
      font-size: 18px;
    }}

    .voice-button:hover,
    .voice-button.listening {{
      background: #d9ebe5;
    }}

    .form-note {{
      grid-column: 1 / -1;
      min-height: 18px;
      color: var(--muted);
      font-size: 13px;
    }}

    .option-row {{
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 14px;
    }}

    .option-row input {{
      width: 16px;
      min-height: 16px;
    }}

    .status,
    .error {{
      padding: 12px 14px;
      border-radius: 8px;
      margin-bottom: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      color: var(--muted);
    }}

    .error {{
      color: var(--danger);
      border-color: #e2aaa4;
      background: #fff7f6;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}

    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
    }}

    section.full {{
      grid-column: 1 / -1;
    }}

    h2 {{
      margin: 0;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      font-size: 16px;
      letter-spacing: 0;
    }}

    pre {{
      margin: 0;
      padding: 14px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
      max-height: 520px;
      overflow: auto;
    }}

    @media (max-width: 760px) {{
      header,
      form {{
        display: block;
      }}

      button {{
        width: 100%;
        margin-top: 10px;
      }}

      .voice-button {{
        width: 100%;
      }}

      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Research Pipeline</h1>
        <p class="subtitle">Search, scrape, write, and critique a research report.</p>
      </div>
    </header>

    <form method="post" action="/research" id="research-form">
      <input id="topic-input" name="topic" value="{escape(topic)}" placeholder="Enter a research topic" required>
      <button class="voice-button" id="voice-button" type="button" title="Voice input" aria-label="Voice input">&#127908;</button>
      <button type="submit">Run Research</button>
      <label class="option-row">
        <input type="checkbox" name="skip_critic" value="1" checked>
        Skip critic to save Mistral quota
      </label>
      <div class="form-note" id="voice-status"></div>
    </form>

    {render_message(error, is_loading_hint)}
    {render_results(report)}
  </main>
  <script>
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const voiceButton = document.getElementById("voice-button");
    const topicInput = document.getElementById("topic-input");
    const voiceStatus = document.getElementById("voice-status");

    if (!SpeechRecognition) {{
      voiceButton.disabled = true;
      voiceButton.title = "Voice input is not supported in this browser";
      voiceStatus.textContent = "Voice input works best in Chrome or Edge.";
    }} else {{
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      voiceButton.addEventListener("click", () => {{
        voiceStatus.textContent = "Listening...";
        voiceButton.classList.add("listening");
        recognition.start();
      }});

      recognition.addEventListener("result", (event) => {{
        const transcript = event.results[0][0].transcript;
        topicInput.value = transcript;
        voiceStatus.textContent = "Voice topic captured. Review it, then run research.";
      }});

      recognition.addEventListener("error", (event) => {{
        voiceStatus.textContent = `Voice input failed: ${{event.error}}`;
      }});

      recognition.addEventListener("end", () => {{
        voiceButton.classList.remove("listening");
      }});
    }}
  </script>
</body>
</html>"""
    return body.encode("utf-8")


def render_message(error: str | None, is_loading_hint: bool) -> str:
    if error:
        return f'<div class="error">{escape(error)}</div>'
    if is_loading_hint:
        return '<div class="status">The pipeline is running. This page will update when the report is ready.</div>'
    return ""


def render_results(state: dict) -> str:
    if not state:
        return ""

    return f"""
    <div class="grid">
      <section>
        <h2>Search Results</h2>
        <pre>{escape(state.get("search_results"))}</pre>
      </section>
      <section>
        <h2>Scraped Content</h2>
        <pre>{escape(state.get("scraped_content"))}</pre>
      </section>
      <section class="full">
        <h2>Final Report</h2>
        <pre>{escape(state.get("report"))}</pre>
      </section>
      <section class="full">
        <h2>Critic Feedback</h2>
        <pre>{escape(state.get("feedback"))}</pre>
      </section>
    </div>"""


class ResearchHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/", "/research"}:
            self.send_error(404, "Not found")
            return

        self.send_html(render_page())

    def do_POST(self) -> None:
        if self.path != "/research":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(raw_body)
        topic = form.get("topic", [""])[0].strip()
        include_critic = form.get("skip_critic", ["0"])[0] != "1"

        if not topic:
            self.send_html(render_page(error="Please enter a research topic."))
            return

        try:
            state = run_research_pipeline_low_call(topic, include_critic=include_critic)
        except Exception as e:
            self.send_html(render_page(topic=topic, error=f"Pipeline failed: {e}"))
            return

        self.send_html(render_page(topic=topic, state=state))

    def send_html(self, content: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ResearchHandler)
    print(f"Web interface running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    server.serve_forever()


if __name__ == "__main__":
    main()

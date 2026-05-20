# Multi_Agent_AI_Research_System

A lightweight research assistant that takes a topic, searches the web, scrapes source content, writes a structured report, and optionally critiques the result. The project supports both a command-line workflow and a local web interface with browser-based voice input.

## Features

- 4-stage research workflow: Tavily web search, BeautifulSoup scraping, Mistral report writing, and optional critic feedback.
- Local web interface built with Python's standard `http.server`, requiring no Flask/FastAPI dependency.
- Browser voice input for entering research topics in supported browsers such as Chrome and Edge.
- Low-quota web mode that uses direct Python search/scraping and only 1 Mistral call by default.
- CLI voice input on Windows using built-in PowerShell speech recognition.

## Project Structure

```text
.
|-- agents.py      # Mistral LLM setup, LangChain agents, writer chain, critic chain
|-- pipeline.py    # CLI pipeline, voice input, full agent pipeline, low-call pipeline
|-- tools.py       # Tavily search and BeautifulSoup scraping tools/helpers
|-- web_app.py     # Local browser interface
|-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.10+
- Tavily API key
- Mistral API key

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=your_tavily_api_key
MISTRAL_API_KEY=your_mistral_api_key
```

The `.env` file is ignored by git so API keys are not committed.

## Run the Web Interface

```powershell
python web_app.py
```

Then open:

```text
http://127.0.0.1:8000
```

In the website:

- Enter a topic manually or use the microphone button.
- Keep `Skip critic to save Mistral quota` checked to use only 1 Mistral call.
- Uncheck it to also generate critic feedback.

## Run the CLI Pipeline

```powershell
python pipeline.py
```

You can type a topic directly or enter `v` / `voice` to use voice input on Windows.

## API Usage Notes

The project includes two execution paths:

- `run_research_pipeline`: full LangChain agent pipeline with search agent, reader agent, writer, and critic.
- `run_research_pipeline_low_call`: quota-friendly path used by the web app. It performs Tavily search and scraping directly in Python, then calls Mistral only for report writing by default.

If you hit a Mistral `429 rate limit exceeded` error, wait for quota reset or keep critic generation disabled in the web interface.

## Tech Stack

- Python
- LangChain
- Mistral AI
- Tavily Search
- BeautifulSoup
- Requests
- Python `http.server`
- Browser Web Speech API

## GitHub

Repository: [Multi_Agent_AI_Research_System](https://github.com/Victus0904/Multi_Agent_AI_Research_System)

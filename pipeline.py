from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
from tools import scrape_url_direct, search_web_direct
import platform
import subprocess


def limit_text(text: str, max_chars: int) -> str:
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "\n...[trimmed to reduce token usage]"


def listen_for_topic(timeout_seconds: int = 8) -> str | None:
    if platform.system() != "Windows":
        print("Voice input is only supported on Windows in this project.")
        return None

    script = f"""
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()
$recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$result = $recognizer.Recognize([TimeSpan]::FromSeconds({timeout_seconds}))
if ($result -ne $null) {{
    $result.Text
}}
$recognizer.Dispose()
"""

    try:
        print(f"Listening for up to {timeout_seconds} seconds...")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 5,
        )
    except (subprocess.SubprocessError, OSError) as e:
        print(f"Voice input failed: {e}")
        return None

    if result.returncode != 0:
        error = result.stderr.strip() or "Speech recognition failed."
        print(f"Voice input failed: {error}")
        return None

    topic = result.stdout.strip()
    return topic or None


def get_research_topic() -> str:
    choice = input("Enter topic to research, or type 'v' for voice input: ").strip()

    if choice.lower() not in {"v", "voice"}:
        return choice

    topic = listen_for_topic()
    if not topic:
        return input("Voice input did not detect a topic. Type topic to research: ").strip()

    print(f"Detected topic: {topic}")
    confirm = input("Use this topic? [Y/n]: ").strip().lower()
    if confirm in {"n", "no"}:
        return input("Type topic to research: ").strip()

    return topic

def run_research_pipeline(topic: str) -> dict:
    state = {}

    # Search agent working
    print("\n" + "="*50)
    print("Step 1 : Search agent is running")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find 3 recent reliable sources about: {topic}")]
    })

    state["search_results"] = limit_text(search_result["messages"][-1].content, 1200)
    print("\n search result ",state['search_results'])

    # Step 2 : Reader agent

    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
                      f"Based on the following search results about '{topic}', "
                      f"pick one relevant URL and scrape it. Keep the answer concise.\n\n"
                      f"Search Results:\n{limit_text(state['search_results'], 500)}"
                      )]
    })

    state["scraped_content"] = limit_text(reader_result["messages"][-1].content, 1000)
    print("\nscraped content: \n", state['scraped_content'])

    #Step 3 - writer chain

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS:\n{limit_text(state['search_results'], 900)}\n\n"
        f"SCRAPED CONTENT:\n{limit_text(state['scraped_content'], 900)}"
    )

    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print("\n Final Report\n",state['report'])

    #critic report

    print("\n"+" ="*50)
    print("Step 4 - critic is reviewing the report ")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report": limit_text(state['report'], 1800),
        "research": limit_text(research_combined, 1200)
    })

    print("\n critic report \n", state['feedback'])

    return state


def run_research_pipeline_low_call(topic: str, include_critic: bool = True) -> dict:
    state = {}

    print("\n" + "="*50)
    print("Step 1 : Direct Tavily search is running")
    print("="*50)

    search_results, urls = search_web_direct(topic, max_results=3)
    state["search_results"] = limit_text(search_results, 900)
    print("\n search result ", state["search_results"])

    print("\n"+" ="*50)
    print("step 2 - Direct scraper is reading the top source ...")
    print("="*50)

    if urls:
        scraped_content = scrape_url_direct(urls[0], max_chars=600)
    else:
        scraped_content = "No URL found to scrape."

    state["scraped_content"] = limit_text(scraped_content, 700)
    print("\nscraped content: \n", state["scraped_content"])

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting a concise report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS:\n{limit_text(state['search_results'], 700)}\n\n"
        f"SCRAPED CONTENT:\n{limit_text(state['scraped_content'], 600)}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    print("\n Final Report\n", state["report"])

    if include_critic:
        print("\n"+" ="*50)
        print("Step 4 - critic is reviewing the report ")
        print("="*50)

        state["feedback"] = critic_chain.invoke({
            "report": limit_text(state["report"], 1200),
            "research": limit_text(research_combined, 900)
        })
    else:
        state["feedback"] = "Critic skipped to reduce Mistral API usage."

    print("\n critic report \n", state["feedback"])

    return state


if"__main__" == __name__:
    topic = get_research_topic()
    run_research_pipeline(topic)

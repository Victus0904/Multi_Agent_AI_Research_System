from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import scrape_url, web_search
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatMistralAI(model="mistral-large-latest", temperature=0.2, max_tokens=700)

# First Agent
def build_search_agent():
    return create_agent(
        model = llm,
        tools= [web_search],
        system_prompt="Use the web_search tool once. Return only the 3 most relevant sources with title, URL, and a short snippet.",
    )

# Second Agent
def build_reader_agent():
    return create_agent(
        model = llm,
        tools= [scrape_url],
        system_prompt="Use scrape_url once on the best URL. Return a concise factual summary and the source URL.",
    )

# Writer Chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write concise, factual reports."),
    ("human", """Write a concise research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (3 brief points)
- Conclusion
- Sources (list all URLs found in the research)

Keep the full report under 450 words."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

# Critic chain

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be brief, honest, and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Research used to write the report:
{research}

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...

Areas to Improve:
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()

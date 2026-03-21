# backend/app/agents/research_agent.py

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, SystemMessage
from app.config.settings import settings
from app.logger.logger import logger
from app.utils.helpers import truncate_text


# ── Tools ──────────────────────────────────────────────────────────────────
search_tool = TavilySearch(
    max_results=5,
    api_key=settings.TAVILY_API_KEY,
)

# ── LLM ───────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.3,          # lower temp → more factual research output
)

# ── System prompt ──────────────────────────────────────────────────────────
RESEARCH_SYSTEM_PROMPT = """You are an expert research assistant.
Your job is to:
1. Analyse the user's query carefully.
2. Use the web search results provided to you.
3. Synthesise a clear, factual, well-structured answer.
4. Always cite which search result supports each key point.
5. Be concise — no padding, no repetition.

Format your response as:
### Research Summary
<your synthesised answer here>

### Sources Used
<bullet list of URLs you relied on>
"""


# ── Main function ──────────────────────────────────────────────────────────
def run_research_agent(query: str) -> dict:
    """
    Research Agent entry point.

    Steps:
        1. Run Tavily web search for the query.
        2. Format search results into a context block.
        3. Ask Groq LLaMA to synthesise a clean answer.

    Args:
        query : The user's research question.

    Returns:
        dict with keys:
            - query          : original query
            - search_results : raw list from Tavily
            - summary        : LLM-synthesised answer string
    """

    logger.info(f"[research_agent] Starting research for: '{query}'")

    # ── Step 1: Web search ─────────────────────────────────────────────────
    try:
        search_results: list[dict] = search_tool.invoke(query)
        logger.info(f"[research_agent] Got {len(search_results)} results.")
    except Exception as e:
        logger.error(f"[research_agent] Search error: {e}")
        raise

    # ── Step 2: Format results as readable context ─────────────────────────
    context_block = _format_results(search_results)

    # ── Step 3: LLM synthesis ──────────────────────────────────────────────
    messages = [
        SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Query: {query}\n\n"
            f"Web Search Results:\n{context_block}\n\n"
            "Now write your research summary."
        )),
    ]

    try:
        response = llm.invoke(messages)
        summary: str = response.content
        logger.info("[research_agent] Summary generated successfully.")
    except Exception as e:
        logger.error(f"[research_agent] LLM error: {e}")
        raise

    return {
        "query":          query,
        "search_results": search_results,
        "summary":        summary,
    }


# ── Helper ─────────────────────────────────────────────────────────────────
def _format_results(results: list[dict]) -> str:
    """
    Convert Tavily result dicts into a numbered, readable string block
    that fits neatly into the LLM prompt.

    Each result dict from Tavily has keys: url, content, title, score.
    """
    lines = []
    for i, r in enumerate(results, start=1):
        title   = r.get("title",   "No title")
        url     = r.get("url",     "No URL")
        content = r.get("content", "").strip()

        lines.append(
            f"[{i}] {title}\n"
            f"     URL: {url}\n"
            f"     Snippet: {truncate_text(content, max_chars=400)}"
        )
    return "\n\n".join(lines)
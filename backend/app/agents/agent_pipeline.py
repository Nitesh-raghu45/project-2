# backend/app/agents/agent_pipeline.py

from app.agents.research_agent import run_research_agent
from app.agents.critic_agent import run_critic_agent
from app.logger.logger import logger

MAX_RETRIES = 2   # re-research if critic gives FAIL (up to 2 times)


def run_agent_pipeline(query: str) -> dict:
    """
    Full Research → Critic pipeline.

    Flow:
        1. Research Agent  → produces a summary from web search.
        2. Critic Agent    → scores the summary.
        3. If FAIL + retries left → refine query and retry from step 1.
        4. Return final combined result.

    Args:
        query : user's research question

    Returns:
        dict with keys:
            - query          : original query
            - summary        : final research summary
            - critique       : critic's full evaluation dict
            - passed         : bool
            - attempts       : how many research attempts were made
    """

    attempt       = 0
    critic_result = None

    while attempt < MAX_RETRIES:
        attempt += 1
        logger.info(f"[pipeline] Attempt {attempt}/{MAX_RETRIES} for: '{query}'")

        # ── Step 1: Research ───────────────────────────────────────────────
        research_result = run_research_agent(query)

        # ── Step 2: Critic review ──────────────────────────────────────────
        critic_result = run_critic_agent(research_result)

        if critic_result["passed"]:
            logger.info(f"[pipeline] PASSED on attempt {attempt}. ✅")
            break

        logger.warning(
            f"[pipeline] FAILED (score={critic_result['critique'].get('overall_score')}) "
            f"— retrying with refined query..."
        )

        # ── Step 3: Refine query using critic feedback ─────────────────────
        feedback = critic_result["critique"].get("feedback", "")
        query    = f"{query}. Focus especially on: {feedback}"

    return {
        "query":    critic_result["query"],
        "summary":  critic_result["summary"],
        "critique": critic_result["critique"],
        "passed":   critic_result["passed"],
        "attempts": attempt,
    }
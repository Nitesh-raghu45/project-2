# Nodes here
# backend/app/chatbot/nodes.py

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage
from app.chatbot.state import ChatState
from app.config.settings import settings
from app.logger.logger import logger

# ── LLM (shared across nodes) ─────────────────────────────────────────────
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.7,
)

# ── Constants ─────────────────────────────────────────────────────────────
SUMMARY_THRESHOLD = 10   # summarise after this many messages in history


# ── Node 1: chat_node ─────────────────────────────────────────────────────
def chat_node(state: ChatState) -> dict:
    """
    Core chat node.
    - Prepends the running summary (if any) as a SystemMessage so the LLM
      retains long-term context even after old messages are pruned.
    - Calls Groq LLaMA and returns the AI reply.
    """

    logger.info(f"[chat_node] session={state['session_id']} | "
                f"messages={len(state['messages'])}")

    messages_to_send = []

    # Inject summary as system context when available
    if state.get("summary"):
        messages_to_send.append(
            SystemMessage(content=(
                "You are a helpful AI assistant. "
                f"Summary of earlier conversation:\n{state['summary']}"
            ))
        )
    else:
        messages_to_send.append(
            SystemMessage(content="You are a helpful AI assistant.")
        )

    messages_to_send.extend(state["messages"])

    try:
        response: AIMessage = llm.invoke(messages_to_send)
        logger.info(f"[chat_node] LLM responded successfully.")
    except Exception as e:
        logger.error(f"[chat_node] LLM error: {e}")
        raise

    return {"messages": [response]}


# ── Node 2: summarize_node ────────────────────────────────────────────────
def summarize_node(state: ChatState) -> dict:
    """
    Summarization node — triggered when message count exceeds SUMMARY_THRESHOLD.
    - Builds a compact summary of ALL current messages.
    - Removes all but the last 4 messages from state to keep context lean.
    - Persists the new summary back into state.
    """

    logger.info(f"[summarize_node] Summarising conversation for "
                f"session={state['session_id']}")

    existing_summary = state.get("summary", "")

    if existing_summary:
        prompt = (
            f"Previous summary:\n{existing_summary}\n\n"
            "Extend this summary with the new messages below. "
            "Be concise and preserve key facts.\n\nNew messages:"
        )
    else:
        prompt = (
            "Summarise the following conversation concisely, "
            "preserving key facts and context:\n\nMessages:"
        )

    summary_messages = state["messages"] + [HumanMessage(content=prompt)]

    try:
        response = llm.invoke(summary_messages)
        new_summary: str = response.content
        logger.info("[summarize_node] Summary generated.")
    except Exception as e:
        logger.error(f"[summarize_node] Summarisation error: {e}")
        raise

    # Keep only the last 4 messages; mark the rest for deletion
    messages_to_delete = [
        RemoveMessage(id=m.id)
        for m in state["messages"][:-4]
    ]

    return {
        "summary": new_summary,
        "messages": messages_to_delete,
    }


# ── Routing function ──────────────────────────────────────────────────────
def should_summarize(state: ChatState) -> str:
    """
    Conditional edge function.
    Returns 'summarize' when history is long enough; otherwise 'end'.
    """
    if len(state["messages"]) >= SUMMARY_THRESHOLD:
        logger.info("[routing] Threshold reached → triggering summarize_node.")
        return "summarize"
    return "end"
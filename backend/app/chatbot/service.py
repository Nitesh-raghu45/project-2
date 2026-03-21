# backend/app/chatbot/service.py

from langchain_core.messages import HumanMessage
from app.chatbot.graph import chatbot
from app.logger.logger import logger
from typing import Iterator


def _make_config(thread_id: str) -> dict:
    """
    Build the LangGraph config dict.
    SqliteSaver uses thread_id to load/save the correct conversation.
    """
    return {
        "configurable": {"thread_id": thread_id},
        "run_name": "chat_turn",
    }


# ── Standard invoke (returns full string) ─────────────────────────────────
def get_chat_response(message: str, thread_id: str) -> str:
    """
    Invoke the chatbot graph for one turn.
    SqliteSaver automatically:
      - loads this thread's full history before chat_node runs
      - saves the updated state (including AI reply) after chat_node completes
    No manual DB calls needed.

    Args:
        message   : User's latest message.
        thread_id : Unique conversation ID (uuid string).

    Returns:
        AI response as a plain string.
    """
    logger.info(f"[service] invoke | thread={thread_id}")

    config = _make_config(thread_id)

    try:
        result = chatbot.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )
    except Exception as e:
        logger.error(f"[service] invoke error: {e}")
        raise

    ai_reply: str = result["messages"][-1].content
    logger.info(f"[service] reply ready | thread={thread_id}")
    return ai_reply


# ── Streaming invoke (yields token chunks) ────────────────────────────────
def stream_chat_response(message: str, thread_id: str) -> Iterator[str]:
    """
    Stream the chatbot response token-by-token using stream_mode='messages'.
    Yields each content chunk as it arrives from Groq — identical to
    Streamlit's st.write_stream() pattern in your working code.

    Usage in FastAPI (SSE):
        for chunk in stream_chat_response(msg, thread_id):
            yield f"data: {chunk}\\n\\n"
    """
    logger.info(f"[service] stream | thread={thread_id}")

    config = _make_config(thread_id)

    try:
        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode="messages",
        ):
            if message_chunk.content:
                yield message_chunk.content
    except Exception as e:
        logger.error(f"[service] stream error: {e}")
        raise

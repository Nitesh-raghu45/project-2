# backend/app/chatbot/service.py

from langchain_core.messages import HumanMessage
from app.chatbot.graph import chatbot_graph
from app.database.sqlite_db import save_message, get_session_messages
from app.logger.logger import logger


def get_chat_response(message: str, session_id: str) -> str:
    """
    Public entry point for the chatbot.

    Steps:
        1. Load previous messages for this session from SQLite.
        2. Run the LangGraph graph with the full history + new message.
        3. Persist the new Human + AI messages back to SQLite.
        4. Return the AI reply string.

    Args:
        message    : The user's latest message.
        session_id : Unique session identifier (uuid string).

    Returns:
        AI response as a plain string.
    """

    logger.info(f"[service] New message | session={session_id}")

    # ── 1. Load history from DB ───────────────────────────────────────────
    history = get_session_messages(session_id)   # list[BaseMessage]

    # ── 2. Append the new user message ───────────────────────────────────
    history.append(HumanMessage(content=message))

    # ── 3. Invoke the graph ───────────────────────────────────────────────
    initial_state = {
        "messages": history,
        "summary": "",          # graph will update this if summarisation runs
        "session_id": session_id,
    }

    try:
        result = chatbot_graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"[service] Graph error: {e}")
        raise

    # ── 4. Extract AI reply ───────────────────────────────────────────────
    ai_reply: str = result["messages"][-1].content

    # ── 5. Persist both turns to SQLite ──────────────────────────────────
    save_message(session_id=session_id, role="user",      content=message)
    save_message(session_id=session_id, role="assistant", content=ai_reply)

    logger.info(f"[service] Reply saved | session={session_id}")

    return ai_reply
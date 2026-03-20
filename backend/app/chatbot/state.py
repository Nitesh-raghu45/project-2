# backend/app/chatbot/state.py

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    """
    Shared state that flows through every node in the graph.

    Fields:
        messages  : Full conversation history (HumanMessage / AIMessage).
                    `add_messages` reducer appends instead of replacing.
        summary   : Running summary injected as context when history is long.
        session_id: Unique ID linking this graph run to a SQLite session row.
    """

    messages: Annotated[list, add_messages]
    summary: str
    session_id: str
# LangGraph logic here
# backend/app/chatbot/graph.py

from langgraph.graph import StateGraph, END
from app.chatbot.nodes import chat_node, summarize_node, should_summarize
from app.chatbot.state import ChatState


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph chatbot graph.

    Graph Flow:
        [START] → chat_node → should_summarize? → summarize_node → [END]
                                                 ↘ (no)          → [END]
    """

    graph = StateGraph(ChatState)

    # ── Nodes ──────────────────────────────────────────────────────────────
    graph.add_node("chat", chat_node)
    graph.add_node("summarize", summarize_node)

    # ── Edges ──────────────────────────────────────────────────────────────
    graph.set_entry_point("chat")

    graph.add_conditional_edges(
        "chat",
        should_summarize,          # routing function
        {
            "summarize": "summarize",
            "end": END,
        },
    )

    graph.add_edge("summarize", END)

    return graph.compile()


# Compiled graph (singleton — import this everywhere)
chatbot_graph = build_graph()
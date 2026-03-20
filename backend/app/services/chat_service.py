# backend/app/services/chat_service.py

from app.chatbot.service import get_chat_response


def chat_response(message: str, session_id: str) -> str:
    return get_chat_response(message, session_id)
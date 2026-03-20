# backend/app/config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "AI Chatbot with RAG"
    VERSION: str      = "1.0.0"

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str   = os.getenv("GROQ_MODEL", "llama3-8b-8192")

    # Summarisation
    SUMMARY_THRESHOLD: int = 10     # messages before summary kicks in


settings = Settings()
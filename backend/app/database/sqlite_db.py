# backend/app/database/sqlite_db.py

import sqlite3
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.logger.logger import logger

DB_PATH = "chat.db"


# ── Connection ─────────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # access columns by name
    return conn


# ── Schema Init ────────────────────────────────────────────────────────────
def init_db() -> None:
    """
    Create tables if they don't exist.
    Call this once at application startup (see main.py lifespan).
    """
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT PRIMARY KEY,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                summary     TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                role        TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content     TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );
        """)
        logger.info("[db] Tables initialised.")


# ── Session helpers ────────────────────────────────────────────────────────
def create_session(session_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id) VALUES (?)",
            (session_id,),
        )
    logger.info(f"[db] Session created: {session_id}")


def update_summary(session_id: str, summary: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET summary = ? WHERE session_id = ?",
            (summary, session_id),
        )


def get_summary(session_id: str) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT summary FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return row["summary"] if row else ""


# ── Message helpers ────────────────────────────────────────────────────────
def save_message(session_id: str, role: str, content: str) -> None:
    """Persist a single turn to the messages table."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_session_messages(session_id: str) -> list[BaseMessage]:
    """
    Load all messages for a session and return them as LangChain message objects.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()

    history: list[BaseMessage] = []
    for row in rows:
        if row["role"] == "user":
            history.append(HumanMessage(content=row["content"]))
        else:
            history.append(AIMessage(content=row["content"]))

    return history
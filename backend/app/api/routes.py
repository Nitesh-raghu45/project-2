# backend/app/api/routes.py

from fastapi import APIRouter, HTTPException
from app.api.schemas import (
    ChatRequest, ChatResponse,
    RAGRequest, RAGResponse,
    ResearchRequest, ResearchResponse,
)
from app.services.chat_service import chat_response
from app.services.rag_service import rag_response
from app.agents.agent_pipeline import run_agent_pipeline
from app.database.sqlite_db import create_session
from app.logger.logger import logger

router = APIRouter()


# ── Chat endpoint ──────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest):
    try:
        create_session(data.session_id)
        reply = chat_response(data.message, data.session_id)
        return ChatResponse(response=reply, session_id=data.session_id)
    except Exception as e:
        logger.error(f"[routes] /chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── RAG endpoint ───────────────────────────────────────────────────────────
@router.post("/rag", response_model=RAGResponse)
def rag(data: RAGRequest):
    try:
        create_session(data.session_id)
        reply = rag_response(data.query, data.session_id)
        return RAGResponse(response=reply, session_id=data.session_id)
    except Exception as e:
        logger.error(f"[routes] /rag error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Research + Critic endpoint ─────────────────────────────────────────────
@router.post("/research", response_model=ResearchResponse)
def research(data: ResearchRequest):
    """
    Runs the full Research Agent → Critic Agent pipeline.
    Returns the summary + quality critique + pass/fail verdict.
    """
    try:
        result = run_agent_pipeline(data.query)
        return ResearchResponse(**result)
    except Exception as e:
        logger.error(f"[routes] /research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
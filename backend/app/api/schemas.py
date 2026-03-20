# backend/app/api/schemas.py

from pydantic import BaseModel, Field
import uuid


class ChatRequest(BaseModel):
    message: str    = Field(..., min_length=1, description="User message")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                            description="Unique session ID (UUID)")


class ChatResponse(BaseModel):
    response:   str
    session_id: str


class RAGRequest(BaseModel):
    query:      str = Field(..., min_length=1)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class RAGResponse(BaseModel):
    response:   str
    session_id: str


# ── Research / Critic schemas ──────────────────────────────────────────────
class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Research question")


class CritiqueScores(BaseModel):
    accuracy:     int
    completeness: int
    clarity:      int
    source_usage: int


class CritiqueDetail(BaseModel):
    scores:        CritiqueScores
    overall_score: float
    verdict:       str
    strengths:     list[str]
    weaknesses:    list[str]
    feedback:      str


class ResearchResponse(BaseModel):
    query:    str
    summary:  str
    critique: CritiqueDetail
    passed:   bool
    attempts: int
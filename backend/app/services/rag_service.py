# backend/app/services/rag_service.py

from app.rag.rag_service import get_rag_response, stream_rag_response, ingest_file
from typing import Iterator


def rag_response(query: str) -> dict:
    return get_rag_response(query)


def rag_stream_response(query: str) -> Iterator[str]:
    return stream_rag_response(query)


def rag_ingest(file_path: str) -> dict:
    return ingest_file(file_path)

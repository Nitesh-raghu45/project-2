# RAG ingestion logic
# backend/app/rag/ingest.py

import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from app.config.settings import settings
from app.logger.logger import logger


# ── Embeddings model (runs locally, no API key needed) ────────────────────
embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
)

# ── Text splitter ─────────────────────────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)

# ── Supported loaders by extension ────────────────────────────────────────
LOADERS = {
    ".pdf":  PyPDFLoader,
    ".txt":  TextLoader,
    ".docx": Docx2txtLoader,
}


def load_documents(file_path: str):
    """Load a file using the correct loader based on its extension."""
    ext = os.path.splitext(file_path)[-1].lower()
    loader_cls = LOADERS.get(ext)

    if not loader_cls:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(LOADERS)}")

    logger.info(f"[ingest] Loading file: {file_path} (type={ext})")
    loader = loader_cls(file_path)
    return loader.load()


def ingest_document(file_path: str) -> int:
    """
    Full ingestion pipeline for a single document:
        1. Load file → raw documents
        2. Split into chunks
        3. Embed chunks
        4. Add to FAISS vectorstore (creates or updates)

    Args:
        file_path : absolute or relative path to the document

    Returns:
        Number of chunks ingested
    """
    # ── Step 1: Load ───────────────────────────────────────────────────────
    docs = load_documents(file_path)
    logger.info(f"[ingest] Loaded {len(docs)} pages/sections.")

    # ── Step 2: Chunk ──────────────────────────────────────────────────────
    chunks = splitter.split_documents(docs)
    logger.info(f"[ingest] Split into {len(chunks)} chunks.")

    # ── Step 3 & 4: Embed + store ──────────────────────────────────────────
    if os.path.exists(settings.FAISS_INDEX_PATH):
        # Load existing index and add new chunks
        logger.info("[ingest] Updating existing FAISS index...")
        vectorstore = FAISS.load_local(
            settings.FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        vectorstore.add_documents(chunks)
    else:
        # Create fresh index
        logger.info("[ingest] Creating new FAISS index...")
        vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore.save_local(settings.FAISS_INDEX_PATH)
    logger.info(f"[ingest] FAISS index saved → {settings.FAISS_INDEX_PATH}")

    return len(chunks)
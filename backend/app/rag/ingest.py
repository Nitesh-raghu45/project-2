# backend/app/rag/ingest.py

import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from app.config.settings import settings
from app.logger.logger import logger


LOADERS = {
    ".pdf":  PyPDFLoader,
    ".txt":  TextLoader,
    ".docx": Docx2txtLoader,
}

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
)


def _get_pinecone_index():
    """Connect to Pinecone and return the index — creates it if it doesn't exist."""
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    existing = [i.name for i in pc.list_indexes()]
    if settings.PINECONE_INDEX_NAME not in existing:
        logger.info(f"[ingest] Creating Pinecone index: {settings.PINECONE_INDEX_NAME}")
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=384,           # all-MiniLM-L6-v2 output dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(settings.PINECONE_INDEX_NAME)


def ingest_document(file_path: str) -> int:
    """
    Full ingestion pipeline:
        1. Load file
        2. Split into chunks
        3. Embed with HuggingFace (local, free)
        4. Upsert into Pinecone (cloud vector store)

    Returns number of chunks ingested.
    """
    ext = os.path.splitext(file_path)[-1].lower()
    loader_cls = LOADERS.get(ext)
    if not loader_cls:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(LOADERS)}")

    logger.info(f"[ingest] Loading: {file_path}")
    docs   = loader_cls(file_path).load()
    chunks = splitter.split_documents(docs)
    logger.info(f"[ingest] {len(chunks)} chunks created.")

    index = _get_pinecone_index()

    # Build vectors for Pinecone upsert
    vectors = []
    for i, chunk in enumerate(chunks):
        vector = embeddings.embed_query(chunk.page_content)
        vectors.append({
            "id":       f"{os.path.basename(file_path)}-{i}",
            "values":   vector,
            "metadata": {
                "text":   chunk.page_content,
                "source": file_path,
                "page":   str(chunk.metadata.get("page", "")),
            },
        })

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i:i+batch_size])

    logger.info(f"[ingest] Upserted {len(vectors)} vectors to Pinecone.")
    return len(chunks)

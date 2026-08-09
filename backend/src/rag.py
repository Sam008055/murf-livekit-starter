import logging
import os
import sqlite3

import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger("rag")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "agri_rag.db")


def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def search_knowledge_base(query: str, top_k: int = 2) -> str:
    """
    Search agricultural knowledge base (PDFs on crops, schemes, soil, pest management, KCC, PM-Kisan, etc.)
    using hybrid vector + text similarity.
    """
    if not os.path.exists(SQLITE_PATH):
        return "Agricultural knowledge base is initializing. Please ask general guidance for now."

    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT doc_name, page_num, content, embedding FROM chunks")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "Knowledge base contains no indexed documents yet."

    # Try embedding query
    query_vec = None
    if ai_client:
        try:
            res = ai_client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=query,
                config={"output_dimensionality": 768},
            )
            query_vec = np.array(res.embeddings[0].values, dtype=np.float32)
        except Exception as e:
            logger.warning(f"RAG embedding query fallback to text match: {e}")

    scored_chunks = []
    query_keywords = set(query.lower().split())

    for doc_name, page_num, content, emb_bytes in rows:
        sim = 0.0
        if query_vec is not None and emb_bytes is not None:
            emb_vec = np.frombuffer(emb_bytes, dtype=np.float32)
            sim = cosine_similarity(query_vec, emb_vec)

        # Keyword relevance boost
        content_lower = content.lower()
        match_count = sum(
            1 for kw in query_keywords if kw in content_lower and len(kw) > 3
        )
        keyword_score = match_count * 0.15

        total_score = sim + keyword_score
        scored_chunks.append((total_score, doc_name, page_num, content))

    # Sort descending by score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored_chunks[:top_k]

    results = []
    for score, doc_name, page_num, content in top_matches:
        if score > 0.05:
            clean_doc = doc_name.replace(".pdf", "").replace("_", " ")
            chunk_content = content.strip()
            if len(chunk_content) > 700:
                chunk_content = chunk_content[:700] + "..."
            results.append(f"[{clean_doc} - Page {page_num}]\n{chunk_content}")

    if not results:
        return "No specific agricultural guidelines found in document knowledge base for this exact phrase."

    return "\n\n---\n\n".join(results)

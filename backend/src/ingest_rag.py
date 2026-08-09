import glob
import logging
import os
import sqlite3
import time

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pypdf import PdfReader

# Suppress pypdf logs
logging.getLogger("pypdf").setLevel(logging.ERROR)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "agri_rag.db")


def init_sqlite_db():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT,
            page_num INTEGER,
            content TEXT,
            embedding BLOB
        )
    """)
    conn.commit()
    conn.close()


def semantic_chunk(text, max_chunk_size=750, overlap=120):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    curr = ""
    for p in paragraphs:
        if len(curr) + len(p) > max_chunk_size and len(curr) > 100:
            chunks.append(curr.strip())
            words = curr.split()
            overlap_text = " ".join(words[-20:]) if len(words) > 20 else curr
            curr = overlap_text + " " + p
        else:
            curr = (curr + "\n\n" + p).strip() if curr else p
    if len(curr) > 40:
        chunks.append(curr.strip())
    return chunks


def get_embedding_with_retry(text, retries=5):
    for attempt in range(retries):
        try:
            res = ai_client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=text,
                config={"output_dimensionality": 768},
            )
            return res.embeddings[0].values
        except errors.ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 3
                print(
                    f"    Rate limit hit. Waiting {wait_time}s before retry (attempt {attempt + 1}/{retries})..."
                )
                time.sleep(wait_time)
            else:
                raise e
        except Exception:
            time.sleep(2)
    return None


def process_pdfs():
    init_sqlite_db()
    pdf_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "pdfs")
    )
    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))

    print(f"Found {len(pdf_files)} agricultural PDFs in {pdf_dir}")

    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()

    total_chunks_inserted = 0
    for pdf_path in pdf_files:
        doc_name = os.path.basename(pdf_path)
        print(f"\nProcessing {doc_name}...")

        # Check if doc already processed
        cur.execute("SELECT COUNT(*) FROM chunks WHERE doc_name = ?", (doc_name,))
        if cur.fetchone()[0] > 0:
            print(f"  Doc {doc_name} already ingested, skipping.")
            continue

        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if not text.strip():
                continue

            chunks = semantic_chunk(text)
            for chunk_str in chunks:
                if len(chunk_str.strip()) < 30:
                    continue

                try:
                    emb = get_embedding_with_retry(chunk_str)
                    emb_bytes = (
                        np.array(emb, dtype=np.float32).tobytes() if emb else None
                    )

                    cur.execute(
                        "INSERT INTO chunks (doc_name, page_num, content, embedding) VALUES (?, ?, ?, ?)",
                        (doc_name, i + 1, chunk_str, emb_bytes),
                    )
                    total_chunks_inserted += 1
                    time.sleep(1.0)  # Respect rate limits
                except Exception as e:
                    print(f"  Error chunk {doc_name} p.{i + 1}: {e}")
            conn.commit()
            print(f"  Saved page {i + 1}/{len(reader.pages)}")

    conn.commit()
    conn.close()
    print("\nIngestion complete! Successfully stored chunks in agri_rag.db")


if __name__ == "__main__":
    process_pdfs()

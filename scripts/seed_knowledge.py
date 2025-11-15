# scripts/seed_and_ingest.py
import sys, os, traceback, time
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BASE_DIR)

from app.scraper.fetcher import simple_fetch, extract_text_from_html, is_allowed
from app.ingest.chunker import basic_chunk_text
from app.embeddings.embedder import embed_texts
from app.db.mongo import db
from app.core.config import settings
import datetime
import numpy as np

SEED_URLS = [
    "https://www.geeksforgeeks.org/binary-search/",
    "https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/",
    "https://www.geeksforgeeks.org/depth-first-search-or-dfs-for-a-graph/",
    "https://www.geeksforgeeks.org/stack-data-structure/",
    "https://www.geeksforgeeks.org/queue-data-structure/",
    "https://www.geeksforgeeks.org/merge-sort/",
    "https://www.geeksforgeeks.org/quick-sort-algorithm/",
]

def seed_and_ingest(urls=SEED_URLS, max_pages=None):
    inserted_total = 0
    for i, url in enumerate(urls):
        if max_pages and i >= max_pages:
            break
        try:
            if not is_allowed(url):
                print(f"Skipping (not allowed domain): {url}")
                continue
            print(f"Fetching: {url}")
            html = simple_fetch(url)
            if not html:
                print(f"Fetch failed or returned empty for {url}")
                continue
            text = extract_text_from_html(html)
            if not text or len(text.strip()) < 200:
                print("Fetched text too short, skipping.")
                continue
            chunks = basic_chunk_text(text, max_chars=1200, overlap=300)
            if not chunks:
                print("No chunks created, skipping.")
                continue
            embs, normed = embed_texts(chunks)
            for idx, chunk in enumerate(chunks):
                doc = {
                    "source": "seed",
                    "url": url,
                    "title": url.split("/")[-1] or url,
                    "text": chunk,
                    "lang": "en",
                    "tags": [],
                    "created_at": datetime.datetime.utcnow(),
                    "ingested_from_url": url
                }
                res = db.knowledge_documents.insert_one(doc)
                doc_id_str = str(res.inserted_id)
                emb_doc = {
                    "doc_id": doc_id_str,
                    "embedding": embs[idx].astype("float32").tolist(),
                    "normed_embedding": normed[idx].astype("float32").tolist(),
                    "vector_model": settings.EMBEDDING_MODEL,
                    "created_at": datetime.datetime.utcnow()
                }
                db.embeddings.insert_one(emb_doc)
                inserted_total += 1
            print(f"Inserted {len(chunks)} chunks from {url}")
            time.sleep(1.0)
        except Exception as e:
            print("Error on URL:", url, "->", e)
            traceback.print_exc()
    print("SEED COMPLETE. Total inserted chunk docs:", inserted_total)
    return inserted_total

if __name__ == "__main__":
    seed_and_ingest()

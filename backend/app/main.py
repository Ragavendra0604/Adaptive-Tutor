# backend/app/main.py
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bson.objectid import ObjectId
from bson.errors import InvalidId
import datetime
import traceback
from fastapi.middleware.cors import CORSMiddleware 
import httpx

import os, sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.db.mongo import db
from app.retriever.retriever import top_k_documents, get_index
from app.rag.rag_engine import answer_query
from app.api.v1 import admin
from app.tasks.scheduler import start_scheduler
from app.core.config import settings
from app.scraper.fetcher import simple_fetch, extract_text_from_html, is_allowed
from app.ingest.ingester import ingest_document

from app.api.v1.practice import router as practice_router
from app.api.v1.stream import router as stream_router
from app.api.v1.answers import router as answers_router

app = FastAPI(title="Adaptive DSA Tutor API")

app.include_router(admin.router)
app.include_router(practice_router)
app.include_router(stream_router)
app.include_router(answers_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_id: str
    query: str
    session_id: str | None = None

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

SEED_URLS = [
    "https://www.geeksforgeeks.org/binary-search/",
    "https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/",
    "https://www.geeksforgeeks.org/depth-first-search-or-dfs-for-a-graph/",
    "https://www.geeksforgeeks.org/stack-data-structure/",
    "https://www.geeksforgeeks.org/queue-data-structure/",
    "https://www.geeksforgeeks.org/merge-sort/",
    "https://www.geeksforgeeks.org/quick-sort-algorithm/"
]

# Health Check
@app.get("/")
def read_root():
    return {"status": "active", "service": "Adaptive Tutor Backend"}
    
# Keep-Alive Loop
async def run_keep_alive():
    # Pings the backend every 10 minutes (600 seconds) 
    url = "https://adaptive-tutor.onrender.com/" 
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                print(f"Keeping alive: Pinging {url}...")
                await client.get(url)
            except Exception as e:
                print(f"Keep-alive ping failed: {e}")
            
            # Sleep for 10 minutes (Render sleeps after 15 mins)
            await asyncio.sleep(600)

@app.on_event("startup")
async def startup_event():
    # 1. Start Scheduler
    start_scheduler()
    
    # 2. Initialize & Rebuild Brain (FAISS)
    try:
        idx = get_index()
        
        # Try loading from disk first
        try:
            idx.load()
        except Exception:
            pass # It's okay if file doesn't exist yet on Render

        # CHECK: Is the brain empty?
        if not idx.index or idx.index.ntotal == 0:
            print("Index is empty (Render cold start). Rebuilding from MongoDB...")
            # This pulls the 60 docs from your image and puts them into RAM
            count = idx.build_from_db() 
            print(f"Brain rebuilt! Loaded {count} documents.")
        else:
            print(f"Index loaded from disk. Total documents: {idx.index.ntotal}")
            
    except Exception as e:
        print("Warning: Failed to load FAISS index:", e)
        traceback.print_exc()
        
    # 3. Start Keep-Alive (to prevent sleeping)
    asyncio.create_task(run_keep_alive())

def get_docs(query_text):
    # 1) attempt retrieval from DB
    docs = top_k_documents(query_text, k=5)
    if docs and len(docs) >= 1:
        return docs

    # 2) fallback scraping — try each seed but do not crash on first failure
    any_ingested = False
    for url in SEED_URLS:
        if not is_allowed(url):
            print(f"[get_docs] skipped not allowed domain: {url}")
            continue
        try:
            raw = simple_fetch(url)
            if not raw:
                print(f"[get_docs] fetch failed or returned no content for: {url}")
                continue
            text = extract_text_from_html(raw)
            if not text or len(text.strip()) < 100:
                print(f"[get_docs] extracted text too short for: {url}")
                continue
            ingest_document(url=url, title=url, raw_text=text, source="seed")
            any_ingested = True
        except Exception as e:
            print(f"[get_docs] unexpected error while fetching/ingesting {url}: {e}")
            traceback.print_exc()
            continue

    # 3) if we ingested anything, refresh index and re-run retrieval
    if any_ingested:
        try:
            idx = get_index()
            # If index is empty, build from DB. If non-empty, ingest already added vectors
            if idx.index is None or getattr(idx.index, "ntotal", 0) == 0:
                idx.build_from_db()
            else:
                # safe to call load to ensure doc_ids in memory if index was saved earlier
                try:
                    idx.load()
                except Exception:
                    pass
        except Exception as e:
            print("[get_docs] warning: failed to reload index in memory:", e)

        # rerun retrieval
        docs = top_k_documents(query_text, k=5)

    # 4) final decision
    if not docs:
        raise HTTPException(status_code=404, detail="No relevant documents found, and fallback scraping failed.")
    return docs
    
# accept both /v1/query and /v1/query/
@app.post("/v1/query")
@app.post("/v1/query/")
async def query_endpoint(req: QueryRequest):
    # Validate session_id if provided
    try:
        session_id = ObjectId(req.session_id) if req.session_id else None
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    # Retrieve documents
    docs = get_docs(req.query)

    # Generate answer
    try:
        answer = answer_query(req.query, docs)
    except Exception as e:
        # failed LLM; don't crash — return helpful error
        print("LLM generation failed:", e)
        raise HTTPException(status_code=500, detail="Failed to generate answer at the moment.")

    # Log chat
    try:
        chat_rec = {
            "user_id": req.user_id,
            "session_id": req.session_id,
            "messages": [
                {"role": "user", "text": req.query},
                {"role": "assistant", "text": answer}
            ],
            "metadata": {"retrieved_docs": [d["doc"]["url"] for d in docs]},
            "created_at": datetime.datetime.utcnow()
        }
        db.chats.insert_one(chat_rec)
    except Exception:
        # logging should not break the response
        print("Warning: failed to log chat")

    return QueryResponse(answer=answer, sources=[d["doc"]["url"] for d in docs])

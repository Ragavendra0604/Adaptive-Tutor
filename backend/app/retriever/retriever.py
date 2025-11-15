# backend/app/retriever/retriever.py
from ..embeddings.embedder import embed_texts
from .faiss_index import FaissIndex
from ..db.mongo import db
import numpy as np
from ..core.config import settings
from bson.objectid import ObjectId

# module-level singleton
_INDEX_SINGLETON = None

def get_index():
    global _INDEX_SINGLETON
    if _INDEX_SINGLETON is None:
        _INDEX_SINGLETON = FaissIndex(settings.EMBEDDING_DIM)
        try:
            _INDEX_SINGLETON.load()
        except Exception:
            pass
    return _INDEX_SINGLETON

def top_k_documents(query: str, k=5):
    embs, normed = embed_texts([query])
    index = get_index()
    # if index empty, build from DB (safe)
    if index is None or getattr(index.index, "ntotal", 0) == 0:
        index.build_from_db()
    if getattr(index.index, "ntotal", 0) == 0:
        return []

    res = index.search(normed, top_k=k)
    docs = []
    for r in res:
        doc_id_str = r.get("doc_id")
        if not doc_id_str:
            continue
        # try to fetch knowledge_documents by converting doc_id_str to ObjectId if possible
        try:
            doc = db.knowledge_documents.find_one({"_id": ObjectId(doc_id_str)})
        except Exception:
            # fallback: try using string field
            doc = db.knowledge_documents.find_one({"_id": doc_id_str})
        if doc:
            docs.append({"doc": doc, "score": r.get("score")})
    return docs

# scripts/rebuild_index.py
import os, sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BASE_DIR)

import numpy as np
from app.core.config import settings
from app.db.mongo import db
from app.retriever.faiss_index import FaissIndex
import traceback

def safe_array(obj):
    try:
        if obj is None:
            return None
        if isinstance(obj, list):
            return np.array(obj, dtype="float32")
        if hasattr(obj, "tolist"):
            return np.array(obj, dtype="float32")
        if isinstance(obj, str):
            import ast
            parsed = ast.literal_eval(obj)
            return np.array(parsed, dtype="float32")
        return np.array(obj, dtype="float32")
    except Exception as e:
        print("Failed to parse embedding:", e)
        return None

def ensure_normed(emb):
    norm = np.linalg.norm(emb)
    if norm == 0:
        return emb
    return emb / norm

def build_index_from_db():
    dim = settings.EMBEDDING_DIM
    faiss_idx = FaissIndex(dim)
    vectors = []
    doc_ids = []
    cursor = db.embeddings.find({})
    count = 0
    bad = 0
    for e in cursor:
        count += 1
        emb_raw = e.get("normed_embedding") or e.get("embedding")
        arr = safe_array(emb_raw)
        if arr is None:
            bad += 1
            print(f"Skipping doc {e.get('_id')} — cannot parse embedding")
            continue
        if e.get("normed_embedding") is None:
            if arr.ndim != 1:
                arr = arr.reshape(-1)
            arr = ensure_normed(arr.astype("float32"))
            try:
                db.embeddings.update_one({"_id": e["_id"]}, {"$set": {"normed_embedding": arr.tolist()}})
            except Exception as upd_e:
                print("Warning: failed to update normed_embedding in db:", upd_e)
        else:
            if arr.ndim != 1:
                arr = arr.reshape(-1)
            arr = ensure_normed(arr.astype("float32"))
        if arr.shape[0] != dim:
            print(f"Skipping doc {e.get('_id')} — dim mismatch {arr.shape[0]} != expected {dim}")
            bad += 1
            continue
        vectors.append(arr)
        doc_id = e.get("doc_id") or e.get("docId") or e.get("doc_id_str") or e.get("_id")
        doc_ids.append(str(doc_id))
    print(f"Total embedding docs scanned: {count}, usable: {len(vectors)}, skipped/bad: {bad}")

    if len(vectors) == 0:
        print("No usable vectors to build index.")
        return

    mat = np.vstack(vectors).astype("float32")
    import faiss
    faiss_idx.index = faiss.IndexFlatIP(dim)
    faiss_idx.index.add(mat)
    faiss_idx.doc_ids = doc_ids
    faiss_idx.save()
    print("Built faiss index with ntotal:", faiss_idx.index.ntotal)

if __name__ == "__main__":
    try:
        build_index_from_db()
    except Exception as e:
        print("Exception during rebuild:", e)
        traceback.print_exc()

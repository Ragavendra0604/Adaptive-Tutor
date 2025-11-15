# backend/app/retriever/faiss_index.py
import faiss
import numpy as np
import os
from ..core.config import settings
from ..db.mongo import db

# Ensure index dir exists
idx_dir = os.path.dirname(settings.FAISS_INDEX_PATH)
if idx_dir:
    os.makedirs(idx_dir, exist_ok=True)

class FaissIndex:
    """
    Lightweight FAISS wrapper.
    - stores index in settings.FAISS_INDEX_PATH + .idx
    - stores doc_id list in .meta file (one id per line)
    """

    def __init__(self, dim: int):
        self.dim = dim
        # create a fresh index in memory; may be replaced by load()
        self.index = faiss.IndexFlatIP(self.dim)
        self.doc_ids = []
        # if files exist, don't auto-load here (call load explicitly)
        # but keep index initialized

    def add_single(self, normed_vector: np.ndarray, doc_id: str):
        vec = normed_vector.reshape(1, -1).astype("float32")
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dim)
            self.doc_ids = []
        self.index.add(vec)
        self.doc_ids.append(doc_id)
        # persist index & meta
        try:
            self.save()
        except Exception as e:
            print("[faiss] warning: failed to save index after add_single:", e)

    def build_from_db(self, limit=None):
        print("Building FAISS index from MongoDB")
        self.index = faiss.IndexFlatIP(self.dim)
        self.doc_ids = []
        cursor = db.embeddings.find({}, {"normed_embedding": 1, "doc_id": 1})
        if limit:
            cursor = cursor.limit(limit)
        vecs = []
        for e in cursor:
            vec = e.get("normed_embedding") or e.get("embedding")
            if not vec:
                continue
            try:
                arr = np.array(vec, dtype="float32")
                # ensure 1D
                arr = arr.reshape(-1)
                # normalize for cosine (IndexFlatIP expects normalized vectors)
                norm = np.linalg.norm(arr)
                if norm != 0:
                    arr = arr / norm
                vecs.append(arr)
                self.doc_ids.append(str(e.get("doc_id") or e.get("_id")))
            except Exception as ex:
                print("[faiss] skipped embedding due to parse error:", ex)
                continue

        if len(vecs) == 0:
            print("[faiss] no vectors found to build index.")
            return

        mat = np.vstack(vecs).astype("float32")
        self.index.add(mat)
        self.save()

    def save(self):
        # write index and meta
        faiss.write_index(self.index, settings.FAISS_INDEX_PATH + ".idx")
        with open(settings.FAISS_INDEX_PATH + ".meta", "w", encoding="utf-8") as f:
            f.write("\n".join(self.doc_ids))

    def load(self):
        idx_path = settings.FAISS_INDEX_PATH + ".idx"
        meta_path = settings.FAISS_INDEX_PATH + ".meta"
        if not os.path.exists(idx_path) or not os.path.exists(meta_path):
            # nothing to load
            return
        try:
            self.index = faiss.read_index(idx_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                self.doc_ids = [l.strip() for l in f if l.strip()]
        except Exception as e:
            print("[faiss] Failed to load index:", e)

    def search(self, normed_vectors: np.ndarray, top_k=5):
        if self.index is None or getattr(self.index, "ntotal", 0) == 0:
            return []
        D, I = self.index.search(normed_vectors, top_k)
        results = []
        for dist_list, idx_list in zip(D, I):
            for dist, idx in zip(dist_list, idx_list):
                if idx < 0 or idx >= len(self.doc_ids):
                    continue
                results.append({"doc_id": self.doc_ids[idx], "score": float(dist)})
        return results

# backend/app/ingest/ingester.py
from ..db.mongo import db
from ..embeddings.embedder import embed_texts
from ..ingest.chunker import basic_chunk_text
from ..core.config import settings
import datetime
import numpy as np
from ..retriever.faiss_index import FaissIndex

def ingest_document(url: str, title: str, raw_text: str, source: str = "manual"):
    """
    Ingest a single document's text: chunk, embed, store docs+embeddings and add to FAISS.
    Returns list of inserted doc_id strings.
    """
    chunks = basic_chunk_text(raw_text)
    if not chunks:
        return []

    embs, normed = embed_texts(chunks)

    # Load single FaissIndex instance in this process for incremental adds
    faiss_idx = FaissIndex(settings.EMBEDDING_DIM)
    try:
        faiss_idx.load()
    except Exception:
        # load may fail if index files don't exist; add_single will create internally if needed
        pass

    inserted_ids = []
    for i, chunk in enumerate(chunks):
        doc = {
            "source": source,
            "url": url,
            "title": title,
            "text": chunk,
            "tags": [],
            "created_at": datetime.datetime.utcnow()
        }
        res = db.knowledge_documents.insert_one(doc)
        doc_id_str = str(res.inserted_id)

        emb_doc = {
            "doc_id": doc_id_str,
            "embedding": embs[i].astype("float32").tolist(),
            "normed_embedding": normed[i].astype("float32").tolist(),
            "vector_model": settings.EMBEDDING_MODEL,
            "created_at": datetime.datetime.utcnow()
        }
        db.embeddings.insert_one(emb_doc)

        # Add to FAISS once
        try:
            faiss_idx.add_single(np.array(normed[i], dtype="float32"), doc_id_str)
        except Exception as e:
            # swallow errors — index can be rebuilt later
            print(f"[ingest] warning: faiss add_single failed for {doc_id_str}: {e}")

        inserted_ids.append(doc_id_str)

    return inserted_ids

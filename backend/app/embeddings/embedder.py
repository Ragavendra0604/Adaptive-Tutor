from sentence_transformers import SentenceTransformer
import numpy as np
from ..core.config import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed_texts(texts:list):
    """
    texts: list[str]
    returns: np.ndarray of shape (len(texts), dim)
    """
    model = get_model()
    embs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    # optional L2-norm for cosine similarity
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms==0] = 1.0
    normed = embs / norms
    return embs.astype("float32"), normed.astype("float32")

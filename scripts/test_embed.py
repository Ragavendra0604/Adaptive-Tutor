# scripts/test_embed_shape.py
import sys, os
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.insert(0, BACKEND_DIR)
from app.embeddings.embedder import embed_texts
from app.core.config import settings
a, n = embed_texts(["hello world"])
print("EMBEDDING_DIM config:", settings.EMBEDDING_DIM)
print("emb shape:", a.shape)
print("normed shape:", n.shape)
print("first 5 values:", a[0][:5])

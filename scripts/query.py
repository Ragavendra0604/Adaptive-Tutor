# scripts/query_test.py
import sys, os
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.insert(0, BACKEND_DIR)
from app.retriever.retriever import top_k_documents
q = "binary search"
docs = top_k_documents(q, k=5)
print("Found docs:", len(docs))
for d in docs:
    print("score:", d.get("score"))
    print("url:", d["doc"].get("url"))
    print("snippet:", d["doc"].get("text","")[:200].replace("\n"," "))
    print("-"*60)

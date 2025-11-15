# scripts/verify_db.py
import sys, os
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.insert(0, BACKEND_DIR)
from app.db.mongo import db
from bson import ObjectId
import json
import pprint

def show_counts():
    print("knowledge_documents count:", db.knowledge_documents.count_documents({}))
    print("embeddings count:", db.embeddings.count_documents({}))
    print("question_bank count:", db.question_bank.count_documents({}))
    print("chats count:", db.chats.count_documents({}))

def print_sample(n=3):
    print("\n--- sample knowledge docs ---")
    for d in db.knowledge_documents.find({}).limit(n):
        print("id:", str(d["_id"]))
        print("url:", d.get("url"))
        print("text snippet:", d.get("text","")[:200].replace("\n"," "))
        print("-"*40)
    print("\n--- sample embeddings docs ---")
    for e in db.embeddings.find({}).limit(n):
        print("id:", str(e["_id"]))
        print("doc_id:", e.get("doc_id"))
        emb = e.get("embedding")
        print("embedding len:", len(emb) if emb else None)
        norm = e.get("normed_embedding")
        print("normed len:", len(norm) if norm else None)
        print("-"*40)

if __name__ == "__main__":
    show_counts()
    print_sample()

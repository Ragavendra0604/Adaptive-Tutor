# backend/app/api/v1/practice.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.adaptive.adaptive import get_mastery
from app.db.mongo import db
from datetime import datetime
from typing import Optional
from bson.objectid import ObjectId

router = APIRouter(prefix="/v1")

class PracticeRequest(BaseModel):
    user_id: str
    concept: str
    n: int = 3

class UserCreate(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None


@router.post("/user")
def create_user(u: UserCreate):
    doc = {
        "user_id": u.user_id,
        "name": u.name,
        "email": u.email,
        "created_at": datetime.utcnow(),
        "mastery": {}
    }
    db.users.update_one({"user_id": u.user_id}, {"$set": doc}, upsert=True)
    return {"status": "ok"}

@router.get("/concepts")
def get_unique_concepts():
    """
    Returns a list of all unique concepts available in the question bank.
    Useful for populating dropdowns on the frontend.
    """
    concepts = db.question_bank.distinct("concept")
    return {"concepts": sorted(concepts)}

@router.get("/user/{user_id}")
def get_user(user_id: str):
    user = db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user or {}


@router.post("/practice")
def get_practice(req: PracticeRequest):
    """
    FULL metadata returned:
    - qid
    - question
    - difficulty
    - type
    - testcases
    - language_id
    """

    mastery = get_mastery(req.user_id, req.concept)
    strength = mastery.get("strength", 0.0)

    if strength < 0.3:
        levels = ["beginner", "beginner", "intermediate"]
    elif strength < 0.6:
        levels = ["intermediate", "intermediate", "advanced"]
    else:
        levels = ["advanced", "intermediate", "advanced"]

    results = []
    seen_qids = set()

    for lvl in levels[:req.n]:
        pipeline = [
            {"$match": {"concept": req.concept, "difficulty": lvl}},
            {"$sample": {"size": 1}}
        ]

        docs = list(db.question_bank.aggregate(pipeline))
        qdoc = docs[0] if docs else None

        if not qdoc:
            # fallback find
            qdoc = db.question_bank.find_one({"concept": req.concept, "difficulty": lvl})

        if not qdoc:
            continue

        qid = str(qdoc["_id"])
        if qid in seen_qids:
            continue

        seen_qids.add(qid)

        results.append({
            "qid": qid,
            "difficulty": lvl,
            "question": qdoc.get("question"),
            "type": qdoc.get("type", "short_answer"),
            "testcases": qdoc.get("testcases", []),
            "language_id": qdoc.get("language_id", 71)
        })

    return {"questions": results, "mastery": mastery}

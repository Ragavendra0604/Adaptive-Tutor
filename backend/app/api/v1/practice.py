# backend/app/api/v1/practice.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.adaptive.adaptive import get_mastery
from app.db.mongo import db
from datetime import datetime
from typing import Optional
from bson.objectid import ObjectId, InvalidId

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
    doc = {"user_id": u.user_id, "name": u.name, "email": u.email, "created_at": datetime.utcnow(), "mastery": {}}
    db.users.update_one({"user_id": u.user_id}, {"$set": doc}, upsert=True)
    return {"status": "ok"}

@router.get("/user/{user_id}")
def get_user(user_id: str):
    user = db.users.find_one({"user_id": user_id}, {"_id":0})
    return user or {}

@router.post("/practice")
def get_practice(req: PracticeRequest):
    """
    Returns up to n practice questions for the given user+concept.
    Selection rules:
      - decide difficulty bucket(s) from mastery strength
      - sample one question per bucket using Mongo $sample
      - ensure returned qids are unique (no duplicates)
    """
    try:
        mastery = get_mastery(req.user_id, req.concept)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load mastery: {e}")

    # choose difficulty list based on mastery strength
    s = mastery.get("strength", 0.0) if mastery else 0.0
    if s < 0.3:
        levels = ["beginner", "beginner", "intermediate"]
    elif s < 0.6:
        levels = ["intermediate", "intermediate", "advanced"]
    else:
        levels = ["advanced", "intermediate", "advanced"]

    questions = []
    seen_qids = set()

    try:
        # For each desired level, attempt to sample one question without returning duplicates.
        for lvl in levels[:req.n]:
            # First try random sampling pipeline (fast)
            pipeline = [
                {"$match": {"concept": req.concept, "difficulty": lvl}},
                {"$sample": {"size": 1}}
            ]
            res = list(db.question_bank.aggregate(pipeline))
            qdoc = None
            if res:
                qdoc = res[0]
                qid = str(qdoc.get("_id"))
                if qid in seen_qids:
                    qdoc = None  # fallthrough to non-sample fetch
            if qdoc is None:
                # try to find any non-seen question of that difficulty
                excluded = []
                for x in seen_qids:
                    try:
                        excluded.append(ObjectId(x))
                    except Exception:
                        pass
                q = db.question_bank.find_one({"concept": req.concept, "difficulty": lvl, "_id": {"$nin": excluded}})
                if q:
                    qdoc = q

            if qdoc:
                qid = str(qdoc.get("_id"))
                if qid in seen_qids:
                    continue
                seen_qids.add(qid)
                questions.append({"qid": qid, "difficulty": lvl, "question": qdoc.get("question")})
            # else: nothing found for this level -> skip quietly

        return {"questions": questions, "mastery": mastery}
    except Exception as e:
        # log server-side for debugging and return clean error to client
        import traceback
        tb = traceback.format_exc()
        print("[practice] Internal error:", tb)
        raise HTTPException(status_code=500, detail="Internal server error while selecting practice questions.")

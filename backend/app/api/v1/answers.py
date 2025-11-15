# backend/app/api/v1/answers.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.mongo import db
from app.adaptive.adaptive import schedule_next, get_mastery
import difflib
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId
from app.code.judge_client import submit_code_to_judge, poll_submission

router = APIRouter(prefix="/v1")

class SubmitAnswerRequest(BaseModel):
    user_id: str
    concept: str
    qid: str
    answer: str = ""
    language_id: Optional[int] = None
    source_code: Optional[str] = None

class SubmitAnswerResponse(BaseModel):
    qid: str
    score: float
    quality: int
    mastery: dict
    details: Optional[Dict[str, Any]] = None

@router.post("/submit_answer", response_model=SubmitAnswerResponse)
def submit_answer(req: SubmitAnswerRequest):
    # fetch question by _id (try ObjectId then string)
    try:
        qdoc = db.question_bank.find_one({"_id": ObjectId(req.qid)})
    except Exception:
        qdoc = db.question_bank.find_one({"_id": req.qid})

    if not qdoc:
        raise HTTPException(status_code=404, detail="Question not found")

    qtype = qdoc.get("type", "short_answer")
    expected = qdoc.get("expected_answer") or qdoc.get("answer") or ""
    quality = 0
    score = 0.0
    details = {}

    if qtype in ("short_answer", "essay"):
        if not expected:
            quality = 3
            score = 0.5
        else:
            seq = difflib.SequenceMatcher(a=expected.lower(), b=req.answer.lower())
            ratio = seq.ratio()
            score = float(ratio)
            if ratio > 0.9:
                quality = 5
            elif ratio > 0.75:
                quality = 4
            elif ratio > 0.5:
                quality = 3
            elif ratio > 0.3:
                quality = 2
            else:
                quality = 1
        details["expected"] = expected
        details["similarity"] = score

    elif qtype == "mcq":
        correct = qdoc.get("correct_option")
        if req.answer.strip().lower() == str(correct).strip().lower():
            quality = 5
            score = 1.0
        else:
            quality = 1
            score = 0.0
        details["correct_option"] = correct

    elif qtype == "code":
        # require source_code and testcases
        testcases = qdoc.get("testcases", [])
        if not req.source_code:
            raise HTTPException(status_code=400, detail="Missing source_code for code question")
        if not testcases:
            # If no testcases present, we can't evaluate — mark partial
            quality = 3
            score = 0.5
            details["note"] = "No testcases available for this coding question"
        else:
            # Run each testcase using Judge0
            passed = 0
            total = 0
            testcase_results = []
            language_id = req.language_id or qdoc.get("language_id") or 71  # default python3 mapping
            for tc in testcases:
                total += 1
                stdin = tc.get("stdin", "")
                expected_out = tc.get("expected", "").strip()
                try:
                    token = submit_code_to_judge(req.source_code, language_id, stdin)
                    res = poll_submission(token, wait_seconds=0.5, timeout=20)
                    stdout = (res.get("stdout") or "") if isinstance(res, dict) else ""
                    # trim and compare ignoring trailing newlines/spaces
                    passed_tc = stdout.strip() == expected_out
                    if passed_tc:
                        passed += 1
                    testcase_results.append({"stdin": stdin, "expected": expected_out, "stdout": stdout, "passed": passed_tc, "raw": res})
                except Exception as e:
                    testcase_results.append({"stdin": stdin, "expected": expected_out, "error": str(e)})
            # compute pass ratio
            score = passed / total if total > 0 else 0.0
            details["testcases"] = testcase_results
            # map to quality
            if score == 1.0:
                quality = 5
            elif score >= 0.75:
                quality = 4
            elif score >= 0.5:
                quality = 3
            elif score > 0:
                quality = 2
            else:
                quality = 1
    else:
        quality = 3
        score = 0.5
        details["note"] = "Unknown question type; treated as partial"

    # update mastery
    res = schedule_next(req.user_id, req.concept, quality)

    # store answer log
    try:
        db.answer_logs.insert_one({
            "user_id": req.user_id,
            "concept": req.concept,
            "qid": req.qid,
            "answer": req.answer,
            "source_code": req.source_code,
            "quality": quality,
            "score": score,
            "details": details,
            "created_at": __import__("datetime").datetime.utcnow()
        })
    except Exception:
        pass

    return SubmitAnswerResponse(qid=req.qid, score=score, quality=quality, mastery=res["mastery"], details=details)

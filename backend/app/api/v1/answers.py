# backend/app/api/v1/answers.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.mongo import db
from app.adaptive.adaptive import schedule_next
from app.code.judge_client import submit_code_to_judge, poll_submission
from app.openrouter.client import chat_completion, is_configured as openrouter_configured
from app.rubrics.prompts import SHORT_ANSWER_RUBRIC, CODE_RUBRIC_PROMPT
from bson.objectid import ObjectId
import difflib, json, traceback
from typing import Optional, Dict, Any

router = APIRouter(prefix="/v1")

class SubmitAnswerRequest(BaseModel):
    user_id: str
    concept: str
    qid: str
    answer: Optional[str] = ""
    language_id: Optional[int] = None
    source_code: Optional[str] = None

class SubmitAnswerResponse(BaseModel):
    qid: str
    score: float
    quality: int
    mastery: dict
    details: Optional[Dict[str, Any]] = None

def _simple_text_eval(expected: str, answer: str):
    # fallback diff-based
    if not expected:
        return {"score": 0.5, "quality": 3, "feedback": "No canonical answer available; manual review recommended."}
    seq = difflib.SequenceMatcher(a=expected.lower(), b=(answer or "").lower())
    ratio = seq.ratio()
    # map to quality
    if ratio > 0.9:
        q = 5
    elif ratio > 0.75:
        q = 4
    elif ratio > 0.5:
        q = 3
    elif ratio > 0.3:
        q = 2
    else:
        q = 1
    return {"score": float(ratio), "quality": q, "feedback": "Auto-evaluated by heuristic; consider manual review."}

@router.post("/submit_answer", response_model=SubmitAnswerResponse)
def submit_answer(req: SubmitAnswerRequest):
    # fetch question
    try:
        qdoc = db.question_bank.find_one({"_id": ObjectId(req.qid)})
    except Exception:
        qdoc = db.question_bank.find_one({"_id": req.qid})

    if not qdoc:
        raise HTTPException(status_code=404, detail="Question not found")

    qtype = qdoc.get("type", "short_answer")
    expected = qdoc.get("expected_answer") or qdoc.get("answer") or ""

    details = {}
    score = 0.0
    quality = 0

    try:
        # =================================================
        # 1. SHORT / ESSAY EVALUATION via LLM
        # =================================================
        if qtype in ("short_answer", "essay"):
            if openrouter_configured():
                prompt = SHORT_ANSWER_RUBRIC.format(expected=expected, answer=req.answer or "")
                res = chat_completion(prompt, system=None, max_tokens=300, temperature=0.0)
                if res.get("success"):
                    content = res.get("content") or ""
                    try:
                        # try direct parse
                        parsed = json.loads(content.strip())
                    except Exception:
                        # try to find first JSON object in text
                        import re
                        m = re.search(r"\{.*\}", content, flags=re.S)
                        if m:
                            parsed = json.loads(m.group(0))
                        else:
                            # If JSON parse fails, degrade gracefully
                            parsed = {}
                    
                    score = float(parsed.get("score", 0.0))
                    quality = int(parsed.get("quality", 3))
                    details["feedback"] = parsed.get("feedback", "")
                    details["raw_llm"] = res.get("raw")
                else:
                    # fall back
                    fb = _simple_text_eval(expected, req.answer or "")
                    score = fb["score"]; quality = fb["quality"]; details["feedback"] = fb["feedback"]
            else:
                fb = _simple_text_eval(expected, req.answer or "")
                score = fb["score"]; quality = fb["quality"]; details["feedback"] = fb["feedback"]

        # =================================================
        # 2. MCQ EVALUATION
        # =================================================
        elif qtype == "mcq":
            correct = qdoc.get("correct_option")
            if str(req.answer).strip().lower() == str(correct).strip().lower():
                score = 1.0; quality = 5
            else:
                score = 0.0; quality = 1
            details["correct_option"] = correct

        # =================================================
        # 3. CODE EVALUATION (FIXED LOOP LOGIC)
        # =================================================
        elif qtype == "code":
            testcases = qdoc.get("testcases", [])
            if not req.source_code:
                raise HTTPException(status_code=400, detail="source_code is required for code questions")

            if not testcases:
                score = 0.5; quality = 3
                details["note"] = "No testcases to evaluate; consider manual review."
            else:
                # --- RUN EVERY TEST CASE ---
                passed_count = 0
                testcase_results = []
                last_jres = {} # Keep the last raw result for LLM context

                for tc in testcases:
                    input_data = tc.get("stdin", "")
                    expected_out = tc.get("expected", "").strip()

                    try:
                        # Submit specific input for this test case
                        token = submit_code_to_judge(
                            req.source_code, 
                            req.language_id or qdoc.get("language_id") or 71,
                            stdin=input_data
                        )
                        # Poll for result
                        jres = poll_submission(token, wait_seconds=0.5, timeout=10)
                        last_jres = jres

                        # Check Output
                        actual_out = (jres.get("stdout") or "").strip()
                        
                        # Compare (exact match after stripping whitespace)
                        is_correct = (actual_out == expected_out)
                        if is_correct:
                            passed_count += 1
                        
                        testcase_results.append({
                            "stdin": input_data,
                            "expected": expected_out,
                            "stdout": actual_out,
                            "stderr": jres.get("stderr"),
                            "compile_output": jres.get("compile_output"),
                            "passed": is_correct
                        })
                    except Exception as e:
                        print(f"Test case failed: {e}")
                        testcase_results.append({
                            "stdin": input_data,
                            "error": str(e),
                            "passed": False
                        })

                # Compute Score based on execution
                total = len(testcases)
                score = (passed_count / total) if total > 0 else 0.0
                
                details["testcases"] = testcase_results
                details["judge_raw"] = last_jres

                # --- LLM QUALITY GRADING (Optional) ---
                if openrouter_configured():
                    try:
                        testcases_str = json.dumps(testcases, default=str, ensure_ascii=False)
                        judge0_str = json.dumps(last_jres, default=str, ensure_ascii=False)
                        
                        prompt = CODE_RUBRIC_PROMPT.format(
                            source_code=req.source_code, 
                            testcases=testcases_str, 
                            judge0_raw=judge0_str
                        )
                        
                        res = chat_completion(prompt, system=None, max_tokens=400, temperature=0.0)
                        if res.get("success"):
                            content = res.get("content") or ""
                            try:
                                parsed = json.loads(content.strip())
                            except Exception:
                                import re
                                m = re.search(r"\{.*\}", content, flags=re.S)
                                parsed = json.loads(m.group(0)) if m else {}

                            # Use LLM's opinion on quality/style
                            llm_quality = parsed.get("quality")
                            if llm_quality is not None:
                                quality = int(llm_quality)
                            else:
                                quality = 3 # default
                            
                            details["llm_feedback"] = parsed.get("feedback")
                            details["llm_suggestion"] = parsed.get("suggestion")
                    except Exception as e:
                        print(f"LLM Grading Error: {e}")
                        # Don't fail the request if LLM fails, just keep the Test Score
                        pass
                else:
                    # If no LLM, estimate quality based on score
                    quality = 5 if score == 1.0 else (3 if score > 0 else 1)

        else:
            score = 0.5; quality = 3
            details["note"] = "Unknown question type"

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

    # Ensure defaults
    score = float(score or 0.0)
    quality = int(quality or 3)

    # Update mastery via schedule_next (SM-2 style)
    try:
        res = schedule_next(req.user_id, req.concept, quality)
    except Exception:
        res = {"mastery": {}}

    # log answer
    try:
        db.answer_logs.insert_one({
            "user_id": req.user_id,
            "concept": req.concept,
            "qid": req.qid,
            "answer": req.answer,
            "source_code": req.source_code,
            "score": score,
            "quality": quality,
            "details": details,
            "created_at": __import__("datetime").datetime.utcnow()
        })
    except Exception:
        pass

    return SubmitAnswerResponse(qid=req.qid, score=score, quality=quality, mastery=res.get("mastery", {}), details=details)
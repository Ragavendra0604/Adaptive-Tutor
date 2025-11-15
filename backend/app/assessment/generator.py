# simple generator using question_bank; fallback to LLM to create Qs
from ..db.mongo import db

def get_questions_for_concept(concept, levels=["beginner","intermediate","advanced"], n_per_level=1):
    qs=[]
    for level in levels:
        cur = db.question_bank.find({"concept":concept, "difficulty":level}).limit(n_per_level)
        for q in cur:
            qs.append({"difficulty": level, "question": q["question"], "answer": q.get("answer")})
    return qs

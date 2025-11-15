def simple_evaluate(user_answers: list, gold_answers: list):
    # Naive exact-match / partial-match scoring
    score=0
    details=[]
    for ua, ga in zip(user_answers, gold_answers):
        correct = False
        if isinstance(ga, str):
            correct = ua.strip().lower() == ga.strip().lower()
        elif isinstance(ga, list):
            correct = ua.strip().lower() in [x.strip().lower() for x in ga]
        details.append({"user":ua, "gold":ga, "correct": correct})
        if correct: score += 1
    return {"score": score, "total": len(gold_answers), "details": details}

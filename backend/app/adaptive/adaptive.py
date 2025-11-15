# backend/app/adaptive/adaptive.py
from datetime import datetime, timedelta
from app.db.mongo import db
import math

def get_mastery(user_id, concept):
    user = db.users.find_one({"user_id": user_id}, {"mastery."+concept:1})
    if not user or "mastery" not in user or concept not in user["mastery"]:
        # initialize
        return {"strength": 0.0, "easiness": 2.5, "interval": 1, "reviews": 0, "last_practiced": None}
    return user["mastery"][concept]

def schedule_next(user_id, concept, quality):
    """
    quality: 0..5 (SM-2 style)
    Update mastery and compute next review date
    """
    s = get_mastery(user_id, concept)
    e = s.get("easiness", 2.5)
    interval = s.get("interval", 1)
    reviews = s.get("reviews", 0)

    if quality < 3:
        # failed: reset interval
        interval = 1
        reviews = 0
    else:
        if reviews == 0:
            interval = 1
        elif reviews == 1:
            interval = 6
        else:
            interval = round(interval * e)
        reviews += 1

    # update easiness
    e = max(1.3, e + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # update strength between 0..1 as a function of quality and reviews
    strength = min(1.0, (quality / 5.0) * (0.5 + min(reviews,10)/20.0))

    data = {
        "strength": strength,
        "easiness": e,
        "interval": interval,
        "reviews": reviews,
        "last_practiced": datetime.utcnow()
    }
    db.users.update_one({"user_id": user_id}, {"$set": {f"mastery.{concept}": data}}, upsert=True)
    next_due = datetime.utcnow() + timedelta(days=interval)
    return {"next_due": next_due, "mastery": data}

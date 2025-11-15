# scripts/simulate_practice_session.py
"""
Simulate a user practice session end-to-end via API (no UI).
- Creates user
- Requests practice for a concept
- Submits simulated answers (some correct, some partial)
Run: python scripts/simulate_practice_session.py
"""
import requests, os, json, time

BASE = os.environ.get("BACKEND_BASE","http://127.0.0.1:8000")
user_id = "sim_user"

def create_user():
    r = requests.post(f"{BASE}/v1/user", json={"user_id": user_id, "name": "Sim User"})
    r.raise_for_status()
    print("User created/ensured")

def get_practice(concept="binary_search", n=3):
    r = requests.post(f"{BASE}/v1/practice", json={"user_id": user_id, "concept": concept, "n": n})
    r.raise_for_status()
    return r.json()

def submit_short_answer(qid, answer):
    r = requests.post(f"{BASE}/v1/submit_answer", json={"user_id": user_id, "concept":"binary_search", "qid": qid, "answer": answer})
    r.raise_for_status()
    return r.json()

def submit_code(qid, source_code, language_id=71):
    r = requests.post(f"{BASE}/v1/submit_answer", json={"user_id": user_id, "concept":"binary_search", "qid": qid, "source_code": source_code, "language_id": language_id})
    r.raise_for_status()
    return r.json()

def simulate():
    create_user()
    print("Requesting practice questions...")
    p = get_practice("binary_search", 5)
    print(json.dumps(p, indent=2))
    questions = p.get("questions", [])
    for q in questions:
        print("\n--- QUESTION ---")
        print(q["question"])
        qid = q["qid"]
        # fetch full qdoc to decide how to answer (call DB via API not available; we will attempt naive)
        # For code questions: if the question contains 'binary search', respond with a simple binary search implementation
        if "binary search" in q["question"].lower() and q.get("difficulty","").lower() == "beginner":
            # simple python implementation reading input like: n\narr\ntarget\n
            src = (
                "import sys\n"
                "data = sys.stdin.read().strip().split()\n"
                "if not data:\n    print(-1)\nelse:\n"
                "    n = int(data[0])\n"
                "    arr = list(map(int, data[1:1+n]))\n"
                "    target = int(data[1+n])\n"
                "    lo, hi = 0, n-1\n"
                "    ans = -1\n"
                "    while lo<=hi:\n"
                "        mid = (lo+hi)//2\n"
                "        if arr[mid]==target:\n"
                "            ans = mid; break\n"
                "        elif arr[mid] < target:\n"
                "            lo = mid+1\n"
                "        else:\n"
                "            hi = mid-1\n"
                "    print(ans)\n"
            )
            try:
                res = submit_code(qid, src, language_id=71)
                print("CODE RESULT:", json.dumps(res, indent=2))
            except Exception as e:
                print("Code submit failed:", e)
        else:
            # short answer simulation: produce a simple correct-ish text
            ans_text = "It picks the middle and halves the search space until found."
            try:
                res = submit_short_answer(qid, ans_text)
                print("ANSWER RESULT:", res)
            except Exception as e:
                print("Submit failed:", e)
        time.sleep(0.5)

if __name__ == "__main__":
    simulate()

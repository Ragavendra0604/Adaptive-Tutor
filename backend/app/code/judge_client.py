# backend/app/code/judge_client.py
import requests
import os
import time

from app.core.config import settings

JUDGE0_URL = getattr(settings, "JUDGE0_URL", None) or os.environ.get("JUDGE0_URL")

def submit_code_to_judge(source_code: str, language_id: int, stdin: str = "") -> str:
    """
    Submits code to Judge0 and returns the token.
    """
    url = f"{JUDGE0_URL}/submissions?base64_encoded=false&wait=false"
    payload = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("token")

def poll_submission(token: str, wait_seconds: float = 0.5, timeout: float = 30.0) -> dict:
    """
    Polls Judge0 for submission result until a final state or timeout.
    """
    start = time.time()
    url = f"{JUDGE0_URL}/submissions/{token}?base64_encoded=false"
    while True:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", {})
        description = status.get("description", "").lower()
        if description not in ("in queue", "processing", ""):
            return data
        if time.time() - start > timeout:
            return {"error": "timeout", "status": status}
        time.sleep(wait_seconds)

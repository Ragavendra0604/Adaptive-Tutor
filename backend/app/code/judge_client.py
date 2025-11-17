import time
import requests
import base64
import os
from app.core.config import settings

# Default to public API if not set, but self-hosted is recommended for production
JUDGE0_URL = getattr(settings, "JUDGE0_API_URL", "https://judge0-ce.p.rapidapi.com")
JUDGE0_KEY = getattr(settings, "JUDGE0_API_KEY", None)
JUDGE0_HOST = getattr(settings, "JUDGE0_API_HOST", "judge0-ce.p.rapidapi.com")

def _get_headers():
    headers = {
        "Content-Type": "application/json",
    }
    # If using RapidAPI (the public default):
    if "rapidapi" in JUDGE0_URL:
        if JUDGE0_KEY:
            headers["X-RapidAPI-Key"] = JUDGE0_KEY
            headers["X-RapidAPI-Host"] = JUDGE0_HOST
    return headers

def _encode_base64(text: str) -> str:
    if not text:
        return ""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def _decode_base64(b64text: str) -> str:
    if not b64text:
        return ""
    try:
        return base64.b64decode(b64text).decode("utf-8")
    except Exception:
        return b64text  # Return raw if decode fails

def submit_code_to_judge(source_code: str, language_id: int, stdin: str = "") -> str:
    """
    Submits code to Judge0 and returns the 'token' to track the submission.
    Uses base64_encoded=true to preserve formatting/indentation.
    """
    url = f"{JUDGE0_URL}/submissions?base64_encoded=true&wait=false"
    
    payload = {
        "source_code": _encode_base64(source_code),
        "language_id": language_id,
        "stdin": _encode_base64(stdin),
    }

    try:
        response = requests.post(url, json=payload, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("token")
    except requests.RequestException as e:
        print(f"[Judge0] Submit failed: {e} | Response: {response.text if 'response' in locals() else ''}")
        raise RuntimeError(f"Judge0 submission failed: {str(e)}")

def poll_submission(token: str, wait_seconds: float = 0.5, timeout: int = 10) -> dict:
    """
    Polls the submission status until it is finished (status_id >= 3) or timeout occurs.
    Decodes the output from Base64 before returning.
    """
    url = f"{JUDGE0_URL}/submissions/{token}?base64_encoded=true"
    start_time = time.time()

    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError("Judge0 submission timed out.")

        try:
            response = requests.get(url, headers=_get_headers(), timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Judge0 Status IDs: 1=In Queue, 2=Processing, >=3=Finished
            status_id = data.get("status", {}).get("id", 1)

            if status_id >= 3:
                # Finished. Decode results.
                result = {
                    "status": data.get("status"), # {id, description}
                    "stdout": _decode_base64(data.get("stdout")),
                    "stderr": _decode_base64(data.get("stderr")),
                    "compile_output": _decode_base64(data.get("compile_output")),
                    "time": data.get("time"),
                    "memory": data.get("memory"),
                    "token": token
                }
                return result
            
            # Still processing, wait and retry
            time.sleep(wait_seconds)

        except requests.RequestException as e:
            print(f"[Judge0] Poll failed: {e}")
            # Don't crash immediately on network blip, just retry unless timeout
            time.sleep(wait_seconds)
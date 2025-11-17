# backend/app/openrouter/client.py
"""
Tiny OpenRouter HTTP client wrapper.
Uses the OpenRouter chat completions endpoint (OpenAI-compatible shape).
"""

import os
import time
import requests
from typing import Optional, Dict, Any

from app.core.config import settings

OPENROUTER_API_URL = getattr(settings, "OPENROUTER_API_URL", None) or os.environ.get("OPENROUTER_API_URL")
OPENROUTER_API_KEY = getattr(settings, "OPENROUTER_API_KEY", None) or os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = getattr(settings, "OPENROUTER_MODEL", None) or os.environ.get("OPENROUTER_MODEL")

DEFAULT_TIMEOUT = 30

def is_configured() -> bool:
    return bool(OPENROUTER_API_KEY)

def chat_completion(prompt: str, system: Optional[str] = None, max_tokens: int = 512,
                    temperature: float = 0.0, retries: int = 2, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Call OpenRouter chat completion and return parsed result dict with keys:
      - success (bool)
      - content (assistant text) OR error (text)
      - raw (raw response JSON if available)
    """
    if not is_configured():
        return {"success": False, "error": "OPENROUTER_API_KEY not set"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    backoff = 1.0
    for attempt in range(1, retries + 2):
        try:
            resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=timeout)
            # try parse json
            try:
                data = resp.json()
            except Exception:
                data = None
            if resp.status_code == 200:
                # robustly extract assistant content
                try:
                    # OpenAI-style chat
                    content = data["choices"][0]["message"]["content"]
                except Exception:
                    # fallback to older style
                    try:
                        content = data["choices"][0].get("text")
                    except Exception:
                        content = None
                return {"success": True, "content": content, "raw": data}
            else:
                # client error: don't retry on 400-series except 429
                if resp.status_code == 429 and attempt <= retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                # try to extract message
                err = None
                if isinstance(data, dict):
                    err = data.get("error") or data
                else:
                    err = resp.text
                return {"success": False, "error": f"OpenRouter {resp.status_code}: {err}", "raw": data}
        except requests.exceptions.RequestException as e:
            if attempt <= retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Exceeded retries"}

# backend/app/rag/rag_engine.py
"""
RAG engine using OpenRouter API (https://openrouter.ai).
- If OPENROUTER_API_KEY is set, this will call the OpenRouter chat completions endpoint.
- If no key or the call fails, a deterministic local summarizer will be returned (so server doesn't 500).
"""

import os
import time
import json
import textwrap
from typing import Any
from .prompt_templates import EXPLAIN_PROMPT

# requests for HTTP calls
import requests

# config helper (your existing settings module)
from ..core.config import settings

def build_excerpts(docs):
    snippets = []
    for i, d in enumerate(docs[:3]):
        src = d["doc"].get("url", "unknown")
        txt = d["doc"].get("text", "")
        snippet = txt.replace("\n", " ").strip()[:1000] 
        snippets.append(f"--- SOURCE {i+1}: {src} ---\n{snippet}")
    return "\n\n".join(snippets)

def _local_summarize(user_query: str, docs):
    excerpts = build_excerpts(docs)
    lines = []
    lines.append(f"Query: {user_query}")
    lines.append("")
    lines.append("Short explanation (from retrieved content):")
    for d in docs[:3]:
        txt = d["doc"].get("text", "").replace("\n", " ").strip()
        sents = txt.split(".")
        first = sents[0].strip() if len(sents) > 0 else ""
        second = sents[1].strip() if len(sents) > 1 else ""
        sample = ". ".join([sent for sent in (first, second) if sent])
        if sample:
            lines.append(f"- {sample.strip()}. (source: {d['doc'].get('url','')})")
    lines.append("")
    lines.append("Real-world analogy:")
    lines.append("- Think of this like a phone book: pick the middle and cut the search space in half (binary search).")
    lines.append("")
    lines.append("Practice problems (one per level):")
    lines.append("Beginner: Given [1,3,5,7], find index of 5 using binary search.")
    lines.append("Intermediate: How to adapt binary search for rotated sorted arrays?")
    lines.append("Advanced: Explain why binary search runs in O(log n) and consider worst-case edge cases.")
    lines.append("")
    lines.append("Sources used:")
    for d in docs[:3]:
        lines.append(f"- {d['doc'].get('url','')}")
    return "\n".join(lines)

# OpenRouter HTTP call wrapper
def _call_openrouter(prompt: str, model: str, key: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
    """
    Sends a chat completion request to OpenRouter.
    Retries a few times on transient errors.
    Returns the assistant text on success; raises Exception on hard failure.
    """
    api_url = getattr(settings, "OPENROUTER_API_URL", None) or os.environ.get("OPENROUTER_API_URL") or "https://api.openrouter.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    # Build payload compatible with OpenAI chat completions style (OpenRouter is compatible)
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    # simple retry loop for transient server/network failures
    retries = 3
    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
            # try to parse JSON even on non-200 so we can show meaningful errors
            try:
                data = resp.json()
            except Exception:
                resp.raise_for_status()
                data = None

            if resp.status_code == 200:
                # typical OpenRouter shape mirrors OpenAI: data['choices'][0]['message']['content']
                if data:
                    # robustly extract text from common shapes
                    try:
                        # OpenAI-style chat
                        text = data["choices"][0]["message"]["content"]
                        return text
                    except Exception:
                        # try older/text field
                        try:
                            text = data["choices"][0].get("text")
                            if text:
                                return text
                        except Exception:
                            pass
                # fallback: return raw text form
                return json.dumps(data)
            elif 500 <= resp.status_code < 600:
                # server error, retry
                if attempt < retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    raise Exception(f"OpenRouter server error {resp.status_code}: {resp.text}")
            else:
                # client error (e.g., 401) — don't retry
                err_msg = data.get("error") if isinstance(data, dict) else resp.text
                raise Exception(f"OpenRouter returned {resp.status_code}: {err_msg}")
        except requests.exceptions.RequestException as e:
            # network issue — retry
            if attempt < retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise

def answer_query(user_query: str, docs):
    """
    Main RAG interface:
    - If OPENROUTER_API_KEY present, attempt to call OpenRouter (configurable model).
    - If call fails or no key, fall back to deterministic summarizer.
    """
    if not docs:
        return "No knowledge available to answer this query."

    # build prompt text using your template
    try:
        prompt = EXPLAIN_PROMPT.format(user_query=user_query, excerpts=build_excerpts(docs))
    except Exception:
        prompt = f"{user_query}\n\n{build_excerpts(docs)}"

    # read key and model from settings or env
    key = getattr(settings, "OPENROUTER_API_KEY", None) or os.environ.get("OPENROUTER_API_KEY")
    model = getattr(settings, "OPENROUTER_MODEL", None) or os.environ.get("OPENROUTER_MODEL") or "gpt-4o-mini"  # default placeholder

    if key:
        try:
            text = _call_openrouter(prompt=prompt, model=model, key=key, max_tokens=1000, temperature=0.1)
            return text
        except Exception as e:
            print("[rag_engine][openrouter] call failed:", e)
            # fall through to local summarizer

    # fallback deterministic summary (prevents 500s)
    return _local_summarize(user_query, docs)

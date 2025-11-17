# scripts/seed_and_ingest.py
import sys
import os
import traceback
import time
import random
import json
import csv
import datetime
import datetime
import numpy as np
from urllib.parse import urlparse, urlunparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BASE_DIR)

from app.scraper.fetcher import simple_fetch, extract_text_from_html, is_allowed
from app.ingest.chunker import basic_chunk_text
from app.embeddings.embedder import embed_texts
from app.db.mongo import db
from app.core.config import settings

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SEED_URLS = [
    # initially feeded knowledge
    "https://www.geeksforgeeks.org/binary-search/",
    "https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/",
    "https://www.geeksforgeeks.org/depth-first-search-or-dfs-for-a-graph/",
    "https://www.geeksforgeeks.org/stack-data-structure/",
    "https://www.geeksforgeeks.org/queue-data-structure/",
    "https://www.geeksforgeeks.org/merge-sort/",
    "https://www.geeksforgeeks.org/quick-sort-algorithm/",

    # Searching + Sorting
    "https://www.geeksforgeeks.org/linear-search/",
    "https://www.geeksforgeeks.org/insertion-sort/",
    "https://www.geeksforgeeks.org/selection-sort/",
    "https://www.geeksforgeeks.org/heap-sort/",
    "https://www.geeksforgeeks.org/counting-sort/",
    "https://www.geeksforgeeks.org/radix-sort/",
    "https://www.geeksforgeeks.org/bucket-sort-2/",

    # Trees
    "https://www.geeksforgeeks.org/binary-tree-data-structure/",
    "https://www.geeksforgeeks.org/binary-search-tree-data-structure/",
    "https://www.geeksforgeeks.org/avl-tree-set-1-insertion/",
    "https://www.geeksforgeeks.org/red-black-tree-set-1-introduction-2/",
    "https://www.geeksforgeeks.org/segment-tree-set-1-sum-of-given-range/",
    "https://www.geeksforgeeks.org/fenwick-tree-range-sum-queries/",
    "https://www.geeksforgeeks.org/trie-insert-and-search/",
    "https://www.geeksforgeeks.org/heap-data-structure/",

    # Graph Algorithms
    "https://www.geeksforgeeks.org/dijkstras-shortest-path-algorithm-greedy-algo-7/",
    "https://www.geeksforgeeks.org/bellman-ford-algorithm-dp-23/",
    "https://www.geeksforgeeks.org/floyd-warshall-algorithm-dp-16/",
    "https://www.geeksforgeeks.org/kruskals-minimum-spanning-tree-algorithm-greedy-algo-2/",
    "https://www.geeksforgeeks.org/prims-minimum-spanning-tree-mst-greedy-algo-5/",
    "https://www.geeksforgeeks.org/topological-sorting/",
    "https://www.geeksforgeeks.org/detect-cycle-in-a-directed-graph-using-colors/",
    "https://www.geeksforgeeks.org/detect-cycle-undirected-graph-using-dfs/",

    # DP (Dynamic Programming)
    "https://www.geeksforgeeks.org/dynamic-programming/",
    "https://www.geeksforgeeks.org/0-1-knapsack-problem-dp-10/",
    "https://www.geeksforgeeks.org/longest-increasing-subsequence-dp-3/",
    "https://www.geeksforgeeks.org/longest-common-subsequence-dp-4/",
    "https://www.geeksforgeeks.org/coin-change-dp-7/",
    "https://www.geeksforgeeks.org/edit-distance-dp-5/",
    "https://www.geeksforgeeks.org/egg-dropping-puzzle-dp-11/",
    "https://www.geeksforgeeks.org/matrix-chain-multiplication-dp-8/",

    # Linked Lists
    "https://www.geeksforgeeks.org/data-structures/linked-list/",
    "https://www.geeksforgeeks.org/reverse-a-linked-list/",
    "https://www.geeksforgeeks.org/doubly-linked-list/",
    "https://www.geeksforgeeks.org/circular-linked-list/",

    # Hashing
    "https://www.geeksforgeeks.org/hashing-data-structure/",
    "https://www.geeksforgeeks.org/hashing-set-1-introduction/",
    "https://www.geeksforgeeks.org/implementation-of-hashing-with-chaining/",

    # Greedy
    "https://www.geeksforgeeks.org/greedy-algorithms/",
    "https://www.geeksforgeeks.org/activity-selection-problem-greedy-algo-1/",
    "https://www.geeksforgeeks.org/huffman-coding-greedy-algo-3/",
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
FAIL_CSV = os.path.join(OUTPUT_DIR, "failures.csv")
JSONL_FILE = os.path.join(OUTPUT_DIR, "results.jsonl")

MAX_ATTEMPTS = int(os.getenv("SEED_MAX_ATTEMPTS", "4"))
INITIAL_BACKOFF = float(os.getenv("SEED_BACKOFF_INITIAL", "1.0"))
TIMEOUT = int(os.getenv("SEED_REQ_TIMEOUT", "20"))
MIN_SLEEP = float(os.getenv("SEED_MIN_SLEEP", "0.8"))
MAX_SLEEP = float(os.getenv("SEED_MAX_SLEEP", "1.6"))

PROXY = os.getenv("SEED_PROXY", None)
PROXIES = {"http": PROXY, "https": PROXY} if PROXY else None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def make_requests_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    # robust adapter with retries for idempotent requests
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504),
                    allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]))
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

def swap_www_variant(url):
    p = urlparse(url)
    host = p.netloc
    if host.startswith("www."):
        return urlunparse(p._replace(netloc=host[len("www."):]))
    else:
        return urlunparse(p._replace(netloc="www." + host))

def write_failure(url, err_msg):
    with open(FAIL_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.utcnow().isoformat(), url, err_msg])

def append_jsonl(record):
    with open(JSONL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")

# robust fetch that wraps your simple_fetch but adds retries + fallback to requests
def robust_fetch(url):
    last_err = None
    # attempt using your simple_fetch first (to keep site-specific logic / headers)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            html = simple_fetch(url)
            if html:
                return html
            last_err = f"simple_fetch returned empty (attempt {attempt})"
        except Exception as e:
            last_err = f"simple_fetch exception (attempt {attempt}): {e}"
        # exponential backoff before next attempt
        backoff = INITIAL_BACKOFF * (2 ** (attempt - 1))
        time.sleep(backoff)

    # if simple_fetch failed repeatedly, try non-www/www fallback variants
    try:
        alt = swap_www_variant(url)
        if alt != url:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    html = simple_fetch(alt)
                    if html:
                        return html
                    last_err = f"simple_fetch(alt) returned empty (attempt {attempt})"
                except Exception as e:
                    last_err = f"simple_fetch(alt) exception (attempt {attempt}): {e}"
                time.sleep(INITIAL_BACKOFF * (2 ** (attempt - 1)))
    except Exception:
        # ignore swapping errors
        pass

    # final fallback: use requests (with retries configured)
    session = make_requests_session()
    try_urls = [url]
    # also try swapped host as second option
    try:
        swapped = swap_www_variant(url)
        if swapped not in try_urls:
            try_urls.append(swapped)
    except Exception:
        pass

    for try_url in try_urls:
        try:
            resp = session.get(try_url, timeout=TIMEOUT, proxies=PROXIES)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_err = f"requests fallback failed for {try_url}: {e}"

    # all attempts failed -> return None and log error externally
    write_failure(url, last_err)
    return None

def seed_and_ingest(urls=SEED_URLS, max_pages=None):
    inserted_total = 0
    for i, url in enumerate(urls):
        if max_pages and i >= max_pages:
            break
        try:
            if not is_allowed(url):
                print(f"Skipping (not allowed domain): {url}")
                continue

            print(f"Fetching: {url}")
            html = robust_fetch(url)
            if not html:
                print(f"Fetch failed or returned empty for {url}")
                continue

            text = extract_text_from_html(html)
            if not text or len(text.strip()) < 200:
                print("Fetched text too short, skipping.")
                write_failure(url, "extracted text too short or empty")
                continue

            chunks = basic_chunk_text(text, max_chars=1200, overlap=300)
            if not chunks:
                print("No chunks created, skipping.")
                write_failure(url, "no chunks created")
                continue

            # embeddings
            embs, normed = embed_texts(chunks)

            # guard: ensure embedding length matches chunks
            if len(embs) != len(chunks) or len(normed) != len(chunks):
                # optional: attempt re-embedding single chunks or skip
                print(f"Embedding length mismatch for {url}: chunks={len(chunks)} embs={len(embs)}")
                write_failure(url, f"embed length mismatch: chunks={len(chunks)} embs={len(embs)}")
                continue

            for idx, chunk in enumerate(chunks):
                doc = {
                    "source": "seed",
                    "url": url,
                    "title": (url.split("/")[-1] or url),
                    "text": chunk,
                    "lang": "en",
                    "tags": [],
                    "created_at": datetime.datetime.utcnow(),
                    "ingested_from_url": url
                }
                res = db.knowledge_documents.insert_one(doc)
                doc_id_str = str(res.inserted_id)
                emb_doc = {
                    "doc_id": doc_id_str,
                    "embedding": embs[idx].astype("float32").tolist(),
                    "normed_embedding": normed[idx].astype("float32").tolist(),
                    "vector_model": settings.EMBEDDING_MODEL,
                    "created_at": datetime.datetime.utcnow()
                }
                db.embeddings.insert_one(emb_doc)
                inserted_total += 1

            record = {"url": url, "inserted_chunks": len(chunks), "time": datetime.datetime.utcnow().isoformat()}
            append_jsonl(record)

            print(f"Inserted {len(chunks)} chunks from {url}")
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        except Exception as e:
            print("Error on URL:", url, "->", e)
            traceback.print_exc()
            write_failure(url, str(e))
    print("SEED COMPLETE. Total inserted chunk docs:", inserted_total)
    return inserted_total


if __name__ == "__main__":
    seed_and_ingest()

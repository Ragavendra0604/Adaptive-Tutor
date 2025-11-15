# backend/app/scraper/fetcher.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    "geeksforgeeks.org",
    "leetcode.com",
    "github.com",
    "tutorialspoint.com"
]

def simple_fetch(url, timeout=10, allow_redirects=True):
    """
    Safe fetcher: returns response.text on success, or None on failure.
    Does NOT propagate HTTPError to the caller.
    """
    headers = {"User-Agent": "AdaptiveTutorBot/1.0 (+email@example.com)"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=allow_redirects)
        r.raise_for_status()
        return r.text
    except requests.exceptions.HTTPError as he:
        print(f"[fetcher] HTTP error for {url}: {he} (status: {getattr(he.response, 'status_code', 'N/A')})")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[fetcher] Request failed for {url}: {e}")
        return None

def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    main = soup.find("main")
    if main:
        text = main.get_text(separator="\n")
    else:
        article = soup.find("article")
        text = article.get_text(separator="\n") if article else soup.get_text(separator="\n")
    return text

def is_allowed(url):
    domain = urlparse(url).netloc
    for ad in ALLOWED_DOMAINS:
        if ad in domain:
            return True
    return False

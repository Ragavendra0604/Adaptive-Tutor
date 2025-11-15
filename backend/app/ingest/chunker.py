import re
from typing import List

# simple paragraph-based chunker + sentence join
def basic_chunk_text(text:str, max_chars=1000, overlap=200) -> List[str]:
    # clean
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_chars:
        return [text]
    chunks=[]
    start=0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # extend end to nearest sentence end
        seg = text[start:end]
        if end < len(text):
            # find last period
            last_dot = seg.rfind('.')
            if last_dot != -1 and last_dot > int(len(seg)*0.5):
                end = start + last_dot + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = max(end - overlap, end)
    return chunks

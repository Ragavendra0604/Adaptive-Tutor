# backend/app/api/v1/stream.py  (updated chunk dedupe)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import AsyncGenerator
import asyncio
from app.rag.rag_engine import answer_query
from app.retriever.retriever import top_k_documents

router = APIRouter(prefix="/v1")

async def _stream_text_chunks(text: str, chunk_size: int = 120) -> AsyncGenerator[str, None]:
    """
    Yield reasonably-sized chunks of text to simulate streaming tokens.
    Collapse consecutive duplicate chunks before yielding.
    """
    start = 0
    length = len(text)
    prev = None
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        start = end
        # collapse identical consecutive chunks (trim whitespace for comparison)
        if prev is not None and chunk.strip() == prev.strip():
            continue
        prev = chunk
        yield chunk
        await asyncio.sleep(0.02)

@router.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    try:
        data = await ws.receive_json()
        user_query = data.get("query")
        user_id = data.get("user_id", "anonymous")

        docs = top_k_documents(user_query, k=5)
        if not docs:
            await ws.send_json({"type":"error","message":"No knowledge found for this query."})
            await ws.close()
            return

        answer_text = answer_query(user_query, docs)

        async for chunk in _stream_text_chunks(answer_text):
            await ws.send_json({"type":"token","text": chunk})
        await ws.send_json({"type":"done"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_json({"type":"error","message": "Server error while streaming response."})
        try:
            await ws.close()
        except Exception:
            pass

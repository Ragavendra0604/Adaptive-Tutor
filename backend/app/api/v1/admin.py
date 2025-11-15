from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.retriever.faiss_index import FaissIndex
from app.core.config import settings
from app.db.mongo import db
import datetime

router = APIRouter(prefix="/admin")

from app.retriever.retriever import get_index as _get_index

@router.post("/reindex")
async def trigger_reindex(background_tasks: BackgroundTasks):
    """
    Trigger a background reindex. This returns immediately and runs rebuild in background.
    """
    def _reindex_job():
        idx = _get_index()
        idx.build_from_db()
    background_tasks.add_task(_reindex_job)
    return {"status": "reindexing started", "started_at": datetime.datetime.utcnow().isoformat()}

@router.get("/index/status")
async def index_status():
    idx = _get_index()
    return {"ntotal": getattr(idx.index, "ntotal", 0), "dim": idx.dim}

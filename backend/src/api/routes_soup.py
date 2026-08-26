import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import asyncpg

from src.db.connection import get_pool

router = APIRouter(prefix="/soup", tags=["Soup Integration"])

@router.get("/export-dataset")
async def export_dataset(pool: asyncpg.Pool = Depends(get_pool)):
    """
    Exports all chat history into a ShareGPT-formatted JSONL file.
    This file can be directly used by the `Soup` CLI to fine-tune local models:
    `soup train --config soup.yaml` (with the dataset pointing to this output).
    """
    # Fetch all messages ordered by session and time
    rows = await pool.fetch("SELECT session_id, role, content FROM messages ORDER BY session_id, created_at")
    
    sessions = {}
    for r in rows:
        sid = r["session_id"]
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append({"role": r["role"], "content": r["content"]})
        
    def generate():
        for sid, msgs in sessions.items():
            # Only export conversations that have at least one back-and-forth
            if len(msgs) > 1:
                yield json.dumps({"messages": msgs}) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=soup_dataset.jsonl"}
    )

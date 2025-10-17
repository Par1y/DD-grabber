from fastapi import FastAPI, Request, HTTPException
import json
import os
import threading
import asyncio
from datetime import datetime, timezone

app = FastAPI()
_lock = threading.Lock()
OUT_FILE = os.path.join(os.path.dirname(__file__), "collected_items.jsonl")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/items")
async def receive_item(request: Request):
    """接收任意 JSON 项，按 JSON Lines (UTF-8) 格式追加到 gen/collected_items.jsonl。

    请求体应该是一个 JSON 对象（item）。响应为 {"status": "ok"} 或错误信息。
    """
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析 JSON: {e}")

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "item": data
    }

    line = json.dumps(record, ensure_ascii=False)
    try:
        # write file in threadpool to avoid blocking the event loop
        def _append_line(l):
            with _lock:
                with open(OUT_FILE, "a", encoding="utf-8") as f:
                    f.write(l + "\n")

        await asyncio.to_thread(_append_line, line)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入文件失败: {e}")

    return {"status": "ok"}


@app.post("/items/")
async def receive_item_slash(request: Request):
    """Alias route accepting trailing slash to avoid client path mismatches."""
    return await receive_item(request)

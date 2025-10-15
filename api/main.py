from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
from lru_cache.core import LRUCache

app = FastAPI(title="LRU Cache API (memory)")

CACHE_CAPACITY = 256
cache = LRUCache(CACHE_CAPACITY)

class PutPayload(BaseModel):
    value: Any

@app.get("/cache/{key}")
def get_value(key: str):
    try:
        return {"key": key, "value": cache.get(key)}
    except KeyError:
        raise HTTPException(status_code=404, detail="Key not found")

@app.put("/cache/{key}")
def put_value(key: str, payload: PutPayload):
    cache.put(key, payload.value)
    return {"status": "ok", "key": key}
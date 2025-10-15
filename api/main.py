# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Any
# from lru_cache.core import LRUCache

# app = FastAPI(title="LRU Cache API (memory)")

# CACHE_CAPACITY = 256
# cache = LRUCache(CACHE_CAPACITY)

# class PutPayload(BaseModel):
#     value: Any

# @app.get("/cache/{key}")
# def get_value(key: str):
#     try:
#         return {"key": key, "value": cache.get(key)}
#     except KeyError:
#         raise HTTPException(status_code=404, detail="Key not found")

# @app.put("/cache/{key}")
# def put_value(key: str, payload: PutPayload):
#     cache.put(key, payload.value)
#     return {"status": "ok", "key": key}


from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Optional
from lru_cache.core import LRUCache
import os

# Optional Redis
try:
    import redis  # type: ignore
except Exception:
    redis = None

app = FastAPI(title="LRU Cache API")

# Config via env
CACHE_CAPACITY = int(os.getenv("CACHE_CAPACITY", "256"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Memory LRU
cache = LRUCache(CACHE_CAPACITY)

class PutPayload(BaseModel):
    value: Any

class RedisLRU:
    """Approximate LRU using Redis HASH + LIST for recency."""
    def __init__(self, client: "redis.Redis", namespace: str = "lru", maxsize: int = 256):
        self.r = client
        self.ns = namespace
        self.maxsize = maxsize
        self.hkey = f"{namespace}:data"
        self.lkey = f"{namespace}:recency"

    def get(self, key: str) -> Any:
        if self.r.hexists(self.hkey, key):
            # bump to MRU
            self.r.lrem(self.lkey, 0, key)
            self.r.lpush(self.lkey, key)
            raw = self.r.hget(self.hkey, key)
            import json
            return json.loads(raw)
        raise KeyError(key)

    def put(self, key: str, value: Any) -> None:
        import json
        self.r.hset(self.hkey, key, json.dumps(value))
        self.r.lrem(self.lkey, 0, key)
        self.r.lpush(self.lkey, key)
        # trim to capacity
        while self.r.llen(self.lkey) > self.maxsize:
            lru_key = self.r.rpop(self.lkey)
            if lru_key:
                self.r.hdel(self.hkey, lru_key)

redis_cache: Optional[RedisLRU] = None

@app.on_event("startup")
def _connect_redis_if_available() -> None:
    global redis_cache
    if redis is None:
        return
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        redis_cache = RedisLRU(client, namespace="lru", maxsize=CACHE_CAPACITY)
    except Exception:
        redis_cache = None

@app.get("/cache/{key}")
def get_value(
    key: str,
    backend: str = Query("memory", enum=["memory", "redis"])
):
    if backend == "redis":
        if redis_cache is None:
            raise HTTPException(503, detail="Redis backend unavailable")
        try:
            return {"key": key, "value": redis_cache.get(key)}
        except KeyError:
            raise HTTPException(404, detail="Key not found")
    # memory
    try:
        return {"key": key, "value": cache.get(key)}
    except KeyError:
        raise HTTPException(404, detail="Key not found")

@app.put("/cache/{key}")
def put_value(
    key: str,
    payload: PutPayload,
    backend: str = Query("memory", enum=["memory", "redis"])
):
    if backend == "redis":
        if redis_cache is None:
            raise HTTPException(503, detail="Redis backend unavailable")
        redis_cache.put(key, payload.value)
        return {"status": "ok", "backend": "redis", "key": key}
    cache.put(key, payload.value)
    return {"status": "ok", "backend": "memory", "key": key}

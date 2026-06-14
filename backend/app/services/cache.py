import json
import time
from threading import Lock

from app.core.config import get_settings

settings = get_settings()
_memory: dict[str, tuple[float, str]] = {}
_lock = Lock()
_redis = None

if settings.redis_url:
    try:
        from redis import Redis

        _redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=1)
        _redis.ping()
    except Exception:
        _redis = None


def get_json(key: str):
    if _redis:
        value = _redis.get(key)
        return json.loads(value) if value else None
    with _lock:
        item = _memory.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at <= time.time():
            _memory.pop(key, None)
            return None
        return json.loads(value)


def set_json(key: str, value, ttl_seconds: int = 900):
    encoded = json.dumps(value, ensure_ascii=False)
    if _redis:
        _redis.setex(key, ttl_seconds, encoded)
        return
    with _lock:
        _memory[key] = (time.time() + ttl_seconds, encoded)


def increment(key: str, ttl_seconds: int = 60) -> int:
    if _redis:
        count = int(_redis.incr(key))
        if count == 1:
            _redis.expire(key, ttl_seconds)
        return count
    now = time.time()
    with _lock:
        item = _memory.get(key)
        count = 0
        if item and item[0] > now:
            count = int(item[1])
        count += 1
        _memory[key] = (now + ttl_seconds, str(count))
        return count

from __future__ import annotations
import time
from app.settings import get_settings

class AzureRedisCache:
    """Azure Cache for Redis seam for idempotency keys, rate limits, and hot session reads.

    In production use REDIS_URL/REDIS_PASSWORD or Managed Identity-enabled Redis Enterprise if available.
    The local project keeps this isolated so Redis is not required for review.
    """
    def __init__(self) -> None:
        try:
            import redis
        except ModuleNotFoundError as exc:
            raise RuntimeError("Redis dependency is not installed. Install redis or use local DB-backed idempotency.") from exc
        s = get_settings()
        if not s.redis_url:
            raise RuntimeError("REDIS_URL is required to use Azure Redis")
        self.client = redis.Redis.from_url(s.redis_url, password=s.redis_password, decode_responses=True)

    def set_idempotency_key(self, key: str, ttl_seconds: int = 600) -> bool:
        return bool(self.client.set(f"idem:{key}", str(time.time()), nx=True, ex=ttl_seconds))

    def increment_rate_limit(self, key: str, window_seconds: int = 60) -> int:
        redis_key = f"rate:{key}:{int(time.time() // window_seconds)}"
        value = self.client.incr(redis_key)
        if value == 1:
            self.client.expire(redis_key, window_seconds)
        return int(value)

    def put_hot_session(self, conversation_id: str, payload_json: str, ttl_seconds: int = 3600) -> None:
        self.client.set(f"session:{conversation_id}", payload_json, ex=ttl_seconds)

    def get_hot_session(self, conversation_id: str) -> str | None:
        return self.client.get(f"session:{conversation_id}")

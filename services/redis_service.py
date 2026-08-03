"""Redis service for refresh token rotation, revocation tracking, and rate limiting."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.config import get_settings

try:
    import redis as redis_lib
except ImportError:  # pragma: no cover
    redis_lib = None  # type: ignore


class RedisAuthStore:
    """Redis-backed storage for authentication state and refresh token identifiers."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._in_memory_store: dict[str, Any] = {}
        self._redis_client = None

        if self.settings.app_environment != "test" and redis_lib is not None:
            try:
                self._redis_client = redis_lib.from_url(
                    self.settings.redis_url,
                    decode_responses=True,
                )
            except Exception:  # pragma: no cover
                self._redis_client = None

    def store_refresh_token(
        self,
        jti: str,
        user_id: UUID,
        tenant_id: UUID,
        ttl_seconds: int,
    ) -> None:
        """Store a refresh token JTI with tenant/user metadata and expiry."""
        key = f"refresh_token:{jti}"
        data = json.dumps({"user_id": str(user_id), "tenant_id": str(tenant_id)})

        if self._redis_client:
            try:
                self._redis_client.setex(key, ttl_seconds, data)
                return
            except Exception:  # pragma: no cover
                pass

        self._in_memory_store[key] = data

    def is_refresh_token_valid(self, jti: str) -> bool:
        """Check if refresh token JTI exists in store and is not revoked."""
        key = f"refresh_token:{jti}"
        if self._redis_client:
            try:
                return bool(self._redis_client.exists(key))
            except Exception:  # pragma: no cover
                pass

        return key in self._in_memory_store

    def revoke_refresh_token(self, jti: str) -> None:
        """Revoke a refresh token JTI atomically."""
        key = f"refresh_token:{jti}"
        if self._redis_client:
            try:
                self._redis_client.delete(key)
                return
            except Exception:  # pragma: no cover
                pass

        self._in_memory_store.pop(key, None)

    def check_rate_limit(
        self,
        key_identifier: str,
        max_attempts: int = 5,
        window_seconds: int = 300,
    ) -> bool:
        """Return True if rate limit is respected, False if limit exceeded."""
        key = f"rate_limit:{key_identifier}"
        if self._redis_client:
            try:
                attempts = self._redis_client.incr(key)
                if attempts == 1:
                    self._redis_client.expire(key, window_seconds)
                return attempts <= max_attempts
            except Exception:  # pragma: no cover
                pass

        count = self._in_memory_store.get(key, 0) + 1
        self._in_memory_store[key] = count
        return count <= max_attempts


_auth_store_instance: RedisAuthStore | None = None


def get_redis_auth_store() -> RedisAuthStore:
    """Return singleton instance of RedisAuthStore."""
    global _auth_store_instance
    if _auth_store_instance is None:
        _auth_store_instance = RedisAuthStore()
    return _auth_store_instance

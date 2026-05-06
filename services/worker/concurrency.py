"""Redis-backed concurrency controls for automation worker tasks."""

from __future__ import annotations

import logging

import redis
from redis.exceptions import WatchError


logger = logging.getLogger(__name__)


class AutomationConcurrencyLimiter:
    """Enforce global and per-user in-flight automation session limits."""

    _GLOBAL_KEY = "artemis:automation:active:global"

    def __init__(
        self,
        *,
        redis_url: str,
        global_limit: int,
        per_user_limit: int,
        ttl_seconds: int,
    ) -> None:
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.global_limit = max(0, int(global_limit))
        self.per_user_limit = max(0, int(per_user_limit))
        self.ttl_seconds = max(60, int(ttl_seconds))

    def acquire(self, user_id: str) -> tuple[bool, str | None]:
        """Try to reserve capacity for this task run."""
        acquired_global = False

        if self.global_limit > 0:
            if not self._try_increment(self._GLOBAL_KEY, self.global_limit):
                return False, (
                    "automation concurrency limit reached: "
                    f"global active sessions already at max={self.global_limit}"
                )
            acquired_global = True

        if self.per_user_limit > 0:
            user_key = self._user_key(user_id)
            if not self._try_increment(user_key, self.per_user_limit):
                if acquired_global:
                    self._decrement(self._GLOBAL_KEY)
                return False, (
                    "automation concurrency limit reached: "
                    f"user {user_id} already has max in-flight sessions={self.per_user_limit}"
                )

        return True, None

    def release(self, user_id: str) -> None:
        """Release previously acquired capacity."""
        if self.per_user_limit > 0:
            self._decrement(self._user_key(user_id))
        if self.global_limit > 0:
            self._decrement(self._GLOBAL_KEY)

    def _user_key(self, user_id: str) -> str:
        return f"artemis:automation:active:user:{user_id}"

    def _try_increment(self, key: str, limit: int) -> bool:
        for _ in range(5):
            with self.client.pipeline() as pipe:
                try:
                    pipe.watch(key)
                    raw_value = pipe.get(key)
                    current = int(raw_value or 0)
                    if current >= limit:
                        pipe.unwatch()
                        return False

                    pipe.multi()
                    pipe.incr(key, 1)
                    pipe.expire(key, self.ttl_seconds)
                    pipe.execute()
                    return True
                except WatchError:
                    continue
                except Exception:  # noqa: BLE001
                    logger.exception("[WorkerConcurrency] Failed to increment key=%s", key)
                    return False

        logger.warning("[WorkerConcurrency] Could not acquire key=%s after retries", key)
        return False

    def _decrement(self, key: str) -> None:
        try:
            current = self.client.decr(key, 1)
            if current <= 0:
                self.client.delete(key)
        except Exception:  # noqa: BLE001
            logger.exception("[WorkerConcurrency] Failed to decrement key=%s", key)

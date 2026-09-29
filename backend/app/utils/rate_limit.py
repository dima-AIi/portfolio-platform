import time
from collections import defaultdict, deque

from fastapi import Request

from app.utils.errors import AppError

_buckets: dict[str, deque[float]] = defaultdict(deque)

# Upper bound on tracked keys so an attacker rotating IPs cannot grow memory
# without limit. The oldest idle buckets are dropped first — the whole store is
# never wiped, otherwise one burst of traffic would reset every other limit.
_MAX_TRACKED_KEYS = 10000
# A bucket that has been idle for this long holds no meaningful window data.
_IDLE_EVICTION_SECONDS = 3600


def reset_rate_limits() -> None:
    _buckets.clear()


def _evict_idle(now: float) -> None:
    if len(_buckets) <= _MAX_TRACKED_KEYS:
        return
    for key in [
        key
        for key, bucket in _buckets.items()
        if not bucket or now - bucket[-1] > _IDLE_EVICTION_SECONDS
    ]:
        del _buckets[key]
    if len(_buckets) > _MAX_TRACKED_KEYS:
        # Still oversized: drop the least recently active keys.
        ordered = sorted(_buckets.items(), key=lambda item: item[1][-1] if item[1] else 0.0)
        for key, _ in ordered[: len(_buckets) - _MAX_TRACKED_KEYS]:
            del _buckets[key]


def _client_ip(request: Request) -> str:
    """Resolve the client IP for rate-limit bucketing.

    Behind a proxy (Render, nginx) the socket peer is the proxy itself, so the
    forwarded header is the only usable signal. A client can put whatever it
    likes in its own `X-Forwarded-For`, and the trusted proxy *appends* the real
    address to it, so the right-most entry is the one the proxy observed. Using
    the left-most entry (client-controlled) let anyone reset the login limiter at
    will by rotating a header, which defeats the whole brute-force defence.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        candidates = [part.strip() for part in forwarded.split(",") if part.strip()]
        if candidates:
            return candidates[-1]
    return request.client.host if request.client else "unknown"


def rate_limit(max_requests: int, window_seconds: int):
    """Sliding-window in-memory limiter keyed by client IP + path."""

    def dependency(request: Request) -> None:
        now = time.monotonic()
        _evict_idle(now)
        key = f"{_client_ip(request)}:{request.url.path}"
        bucket = _buckets[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= max_requests:
            raise AppError(
                "RATE_LIMITED",
                "Слишком много попыток. Подождите минуту и попробуйте снова.",
                429,
            )
        bucket.append(now)

    return dependency

"""
Rate Limiter Middleware

Redis-backed sliding-window rate limiter to protect API endpoints
from abuse. Supports per-user and per-IP rate limiting.
"""
import time
from functools import wraps
from typing import Optional

from flask import request, current_app, g


class RateLimiter:
    """
    Sliding-window rate limiter backed by Redis.

    Usage:
        limiter = RateLimiter()

        # In your Flask app factory:
        limiter.init_app(app)

        # As a decorator on endpoints:
        @app.route("/api/auth/login", methods=["POST"])
        @limiter.limit(max_requests=5, window_seconds=60)
        def login():
            ...
    """

    def __init__(self):
        self._redis = None
        self._enabled = True

    def init_app(self, app):
        """
        Initialize the rate limiter with a Flask app.

        Reads the Redis connection from ``app.redis`` set up in the app factory.
        """
        self._redis = getattr(app, "redis", None)
        self._enabled = app.config.get("RATE_LIMITING_ENABLED", True)

        # Register after-request handler to include rate limit headers
        @app.after_request
        def inject_rate_limit_headers(response):
            if hasattr(g, "rate_limit_info"):
                info = g.rate_limit_info
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(info["reset"])
            return response

    def _get_identifier(self) -> str:
        """
        Determine the identity of the current requester.

        Uses the authenticated user ID if available, otherwise falls back
        to the client IP address.
        """
        from flask_jwt_extended import get_jwt_identity

        try:
            identity = get_jwt_identity()
            if identity:
                return f"user:{identity}"
        except Exception:
            pass

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.remote_addr or "unknown"
        return f"ip:{ip}"

    def _check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> dict:
        """
        Check whether the request is within the rate limit.

        Uses a Redis sorted set with timestamps as scores to implement
        a sliding window.

        Returns:
            dict with 'allowed', 'limit', 'remaining', 'reset' keys.
        """
        now = time.time()
        window_start = now - window_seconds

        pipe = self._redis.pipeline()
        # Remove entries outside the current window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count remaining entries
        pipe.zcard(key)
        # Add the current request
        pipe.zadd(key, {f"{now}:{id(request)}": now})
        # Set key expiry so Redis cleans up automatically
        pipe.expire(key, window_seconds + 1)
        results = pipe.execute()

        current_count = results[1]  # zcard result before adding current
        allowed = current_count < max_requests
        remaining = max(0, max_requests - current_count - 1) if allowed else 0
        reset_at = int(now + window_seconds)

        if not allowed:
            # Remove the entry we just added since the request is rejected
            self._redis.zrem(key, f"{now}:{id(request)}")
            remaining = 0

        return {
            "allowed": allowed,
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_at,
        }

    def limit(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        key_prefix: Optional[str] = None,
        error_message: str = "Too many requests. Please try again later.",
    ):
        """
        Decorator to apply rate limiting to an endpoint.

        Args:
            max_requests: Maximum number of requests allowed in the window.
            window_seconds: Length of the sliding window in seconds.
            key_prefix: Optional custom prefix for the Redis key.
            error_message: Message returned when rate limit is exceeded.
        """
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                if not self._enabled or not self._redis:
                    return fn(*args, **kwargs)

                identifier = self._get_identifier()
                prefix = key_prefix or f"rl:{request.endpoint}"
                redis_key = f"{prefix}:{identifier}"

                info = self._check_rate_limit(redis_key, max_requests, window_seconds)
                g.rate_limit_info = info

                if not info["allowed"]:
                    return {
                        "error": "Rate limit exceeded",
                        "message": error_message,
                        "retry_after": info["reset"] - int(time.time()),
                    }, 429

                return fn(*args, **kwargs)
            return wrapper
        return decorator


# Singleton instance for use across the application
rate_limiter = RateLimiter()

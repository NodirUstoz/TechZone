"""
Request Logger Middleware

Logs incoming API requests and response times for monitoring and debugging.
"""
import time
import logging
from typing import Optional

from flask import Flask, request, g


logger = logging.getLogger("techzone.requests")


class RequestLogger:
    """
    Middleware that logs request details, response status, and duration.

    Attaches to Flask before_request and after_request hooks.

    Usage:
        request_logger = RequestLogger()
        request_logger.init_app(app)
    """

    # Paths to skip logging (health checks, static assets, etc.)
    SKIP_PATHS = frozenset({"/health", "/healthz", "/favicon.ico"})

    # Slow request threshold in milliseconds
    SLOW_REQUEST_THRESHOLD_MS = 1000

    def __init__(self):
        self._app: Optional[Flask] = None

    def init_app(self, app: Flask) -> None:
        """Register request logging hooks with the Flask app."""
        self._app = app

        if not app.config.get("REQUEST_LOGGING_ENABLED", True):
            return

        app.before_request(self._before_request)
        app.after_request(self._after_request)

    @staticmethod
    def _before_request() -> None:
        """Record the request start time."""
        g.request_start_time = time.time()

    def _after_request(self, response):
        """Log request details after the response is generated."""
        # Skip excluded paths
        if request.path in self.SKIP_PATHS:
            return response

        # Calculate duration
        start_time = getattr(g, "request_start_time", None)
        if start_time is None:
            duration_ms = 0.0
        else:
            duration_ms = (time.time() - start_time) * 1000

        # Determine the user identifier
        user_id = self._get_user_id()

        # Build the log line
        log_data = {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "ip": request.remote_addr,
            "user_agent": request.user_agent.string[:200] if request.user_agent else None,
            "user_id": user_id,
        }

        # Include query params for GET requests
        if request.method == "GET" and request.args:
            log_data["query_params"] = dict(request.args)

        # Choose log level based on status and duration
        if response.status_code >= 500:
            logger.error("%(method)s %(path)s %(status)d [%(duration_ms).1fms]", log_data)
        elif response.status_code >= 400:
            logger.warning("%(method)s %(path)s %(status)d [%(duration_ms).1fms]", log_data)
        elif duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "SLOW REQUEST %(method)s %(path)s %(status)d [%(duration_ms).1fms]",
                log_data,
            )
        else:
            logger.info("%(method)s %(path)s %(status)d [%(duration_ms).1fms]", log_data)

        # Add server-timing header for debugging
        response.headers["Server-Timing"] = f"total;dur={duration_ms:.1f}"

        return response

    @staticmethod
    def _get_user_id() -> Optional[int]:
        """Attempt to extract the current user ID from the JWT."""
        try:
            from flask_jwt_extended import get_jwt_identity
            return get_jwt_identity()
        except Exception:
            return None


# Singleton instance
request_logger = RequestLogger()

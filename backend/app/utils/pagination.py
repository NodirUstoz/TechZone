"""
Pagination Utilities
"""
from flask import request, current_app


def paginate_query(query, serialize_fn, default_per_page: int = None, max_per_page: int = None) -> dict:
    """
    Paginate a SQLAlchemy query and return a standardized response dict.

    Args:
        query: SQLAlchemy BaseQuery to paginate.
        serialize_fn: Callable that converts each row to a dict.
        default_per_page: Items per page (falls back to app config).
        max_per_page: Maximum allowed items per page (falls back to app config).

    Returns:
        Dict with 'items', 'page', 'per_page', 'total', 'pages', 'has_next', 'has_prev'.
    """
    if default_per_page is None:
        default_per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    if max_per_page is None:
        max_per_page = current_app.config.get("MAX_PAGE_SIZE", 100)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", default_per_page, type=int)

    # Clamp values
    page = max(1, page)
    per_page = max(1, min(per_page, max_per_page))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": [serialize_fn(item) for item in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


def cursor_paginate(query, cursor_field, serialize_fn, per_page: int = 20) -> dict:
    """
    Cursor-based pagination for large datasets.

    Args:
        query: Base SQLAlchemy query.
        cursor_field: The column to use as cursor (must be sortable and unique).
        serialize_fn: Serializer function.
        per_page: Number of items per page.

    Returns:
        Dict with 'items', 'next_cursor', 'has_more'.
    """
    cursor = request.args.get("cursor", type=int)
    per_page = min(request.args.get("per_page", per_page, type=int), 100)

    if cursor:
        query = query.filter(cursor_field > cursor)

    query = query.order_by(cursor_field.asc()).limit(per_page + 1)
    items = query.all()

    has_more = len(items) > per_page
    if has_more:
        items = items[:per_page]

    next_cursor = getattr(items[-1], cursor_field.key) if items else None

    return {
        "items": [serialize_fn(item) for item in items],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }

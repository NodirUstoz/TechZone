"""
Custom Decorators
"""
from functools import wraps
from flask_jwt_extended import current_user


def admin_required(fn):
    """
    Decorator that ensures the current JWT-authenticated user has admin role.
    Must be used after @jwt_required().

    Usage:
        @jwt_required()
        @admin_required
        def my_admin_endpoint():
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user or not current_user.is_admin:
            return {"error": "Admin privileges required."}, 403
        return fn(*args, **kwargs)
    return wrapper


def verified_email_required(fn):
    """
    Decorator that ensures the current user has a verified email address.
    Must be used after @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user or not current_user.email_verified:
            return {"error": "Email verification required."}, 403
        return fn(*args, **kwargs)
    return wrapper


def active_user_required(fn):
    """
    Decorator that ensures the current user account is active.
    Must be used after @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user or not current_user.is_active:
            return {"error": "Account is deactivated."}, 403
        return fn(*args, **kwargs)
    return wrapper
